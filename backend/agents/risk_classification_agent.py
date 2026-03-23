from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict, List, Optional


class RiskClassificationAgent:
    def __init__(self, vector_store=None):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.vector_store = vector_store
        self._risk_factors = []
        self._violations = []
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self) -> list:
        """Build tools for risk classification"""

        class ThresholdCheckInput(BaseModel):
            amount: str = Field(description="Transaction amount to check (e.g., '$50,000', '100000')")
            regulation: str = Field(description="The regulation or rule to check against (e.g., 'BSA CTR filing', 'wire transfer reporting')")
            threshold: str = Field(description="The known regulatory threshold (e.g., '$10,000', '3 business days')")

        class RiskFactorInput(BaseModel):
            factor_name: str = Field(description="Name of the risk factor (e.g., 'high_value_transaction', 'cross_border', 'pep_involvement')")
            severity: str = Field(description="Severity: 'low', 'medium', 'high', or 'critical'")
            evidence: str = Field(description="Evidence or reasoning for this risk factor assessment")

        class ViolationSearchInput(BaseModel):
            transaction_type: str = Field(description="Type of transaction (e.g., 'wire_transfer', 'cash_deposit', 'account_opening')")
            regulation_area: str = Field(description="Area of regulation (e.g., 'AML', 'KYC', 'sanctions', 'reporting')")

        risk_factors = self._risk_factors
        violations = self._violations

        def check_threshold_violation(amount: str, regulation: str, threshold: str) -> str:
            """Check if a transaction amount violates a specific regulatory threshold. Compares the amount against known limits and determines if reporting or other action is required."""
            prompt = f"""Analyze this threshold check:

Transaction amount: {amount}
Regulation: {regulation}
Regulatory threshold: {threshold}

Determine:
1. Does the amount exceed the threshold? (YES/NO)
2. Is this a violation or just a reporting trigger?
3. What specific action is required (e.g., file CTR, file SAR, enhanced due diligence)?
4. Are there structuring concerns (amount just below threshold)?

Provide a clear assessment."""

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            if "yes" in content.lower()[:100] or "exceed" in content.lower()[:200]:
                violations.append({
                    "type": "threshold_violation",
                    "regulation": regulation,
                    "amount": amount,
                    "threshold": threshold,
                    "details": content[:300]
                })

            return content

        def assess_risk_factor(factor_name: str, severity: str, evidence: str) -> str:
            """Record and assess a specific risk factor. Use this to build up a comprehensive risk profile by evaluating individual risk dimensions one at a time."""
            factor = {
                "factor": factor_name,
                "severity": severity,
                "evidence": evidence
            }
            risk_factors.append(factor)

            severity_scores = {"low": 10, "medium": 30, "high": 60, "critical": 90}
            score = severity_scores.get(severity.lower(), 30)

            return f"Risk factor recorded: {factor_name} (severity: {severity}, score contribution: {score}/100)\nEvidence: {evidence}\nTotal risk factors assessed so far: {len(risk_factors)}"

        def search_violation_patterns(transaction_type: str, regulation_area: str) -> str:
            """Search the regulatory knowledge base for known violation patterns and enforcement actions related to a transaction type and regulation area."""
            if not self.vector_store:
                return f"Using built-in knowledge for {regulation_area} violations related to {transaction_type}."
            query = f"{regulation_area} violations enforcement {transaction_type}"
            docs = self.vector_store.search(query, k=3)
            if not docs:
                return f"No specific violation patterns found for {transaction_type} under {regulation_area}."
            results = []
            for doc in docs:
                results.append(doc.page_content[:400])
            return f"Violation patterns for {transaction_type} ({regulation_area}):\n\n" + "\n\n---\n\n".join(results)

        return [
            StructuredTool.from_function(
                func=check_threshold_violation,
                name="check_threshold_violation",
                description="Check if a transaction amount violates a specific regulatory threshold. Use for comparing amounts against known limits.",
                args_schema=ThresholdCheckInput
            ),
            StructuredTool.from_function(
                func=assess_risk_factor,
                name="assess_risk_factor",
                description="Record and assess a specific risk factor. Call this for each risk dimension (e.g., transaction size, geography, customer type, product type).",
                args_schema=RiskFactorInput
            ),
            StructuredTool.from_function(
                func=search_violation_patterns,
                name="search_violation_patterns",
                description="Search for known violation patterns and enforcement actions related to a transaction type and regulation area.",
                args_schema=ViolationSearchInput
            ),
        ]

    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Risk Classification Agent specializing in banking compliance risk assessment.

Your job is to systematically assess compliance risk by evaluating individual risk factors and checking for violations.

Strategy:
1. First, search for known violation patterns relevant to the transaction type
2. Check specific regulatory thresholds (e.g., $10,000 CTR threshold, $3,000 funds transfer rule)
3. Assess each risk factor individually using assess_risk_factor:
   - Transaction size risk
   - Geographic/jurisdictional risk
   - Customer type risk
   - Product/channel risk
   - Pattern/behavior risk (structuring, rapid movement, etc.)
4. After assessing all factors, provide a final risk classification

Risk levels:
- LOW (0-25): Routine transaction, no concerns
- MEDIUM (26-50): Some risk factors present, standard monitoring
- HIGH (51-75): Multiple risk factors, enhanced due diligence required
- CRITICAL (76-100): Likely violation, immediate action required"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            max_iterations=10,
            handle_parsing_errors=True
        )

    def classify_risk(self, context: str, policies: str, transaction_data: Dict = None) -> Dict:
        """Run the risk classification agent"""
        self._risk_factors = []
        self._violations = []

        transaction_info = ""
        if transaction_data:
            parts = []
            if transaction_data.get("type"):
                parts.append(f"Type: {transaction_data['type']}")
            if transaction_data.get("amount"):
                parts.append(f"Amount: {transaction_data['amount']}")
            if transaction_data.get("region"):
                parts.append(f"Region: {transaction_data['region']}")
            if transaction_data.get("customer_type"):
                parts.append(f"Customer: {transaction_data['customer_type']}")
            transaction_info = "\n".join(parts)

        input_text = f"""Assess the compliance risk for this transaction:

Transaction Details:
{transaction_info if transaction_info else "No specific transaction data provided."}

Applicable Policies and Regulations:
{policies[:3000]}

Regulatory Context:
{context[:2000]}

Systematically evaluate all risk factors, check relevant thresholds, and provide a final risk classification."""

        result = self.agent_executor.invoke({"input": input_text})

        return {
            "risk_assessment": result["output"],
            "risk_factors": self._risk_factors,
            "violations": self._violations,
            "agent": "RiskClassificationAgent",
            "status": "completed"
        }
