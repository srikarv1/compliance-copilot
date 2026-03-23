from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict


class PolicyExtractionAgent:
    def __init__(self, vector_store=None):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.vector_store = vector_store
        self._extracted_data = {
            "regulations": [],
            "policies": [],
            "thresholds": [],
            "citations": []
        }
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self) -> list:
        """Build tools for policy extraction"""

        class ExtractRegulationsInput(BaseModel):
            context: str = Field(description="The regulatory document text to extract regulations from")
            regulation_type: str = Field(description="Type of regulation to look for: 'AML', 'KYC', 'BSA', 'GDPR', 'SOX', 'FATF', or 'general'")

        class CrossReferenceInput(BaseModel):
            regulation_name: str = Field(description="The name or ID of a regulation to cross-reference (e.g., 'BSA Section 5318', 'FATF Recommendation 16')")

        class ExtractThresholdsInput(BaseModel):
            context: str = Field(description="Text to extract numerical thresholds and limits from")

        extracted = self._extracted_data

        def extract_regulations(context: str, regulation_type: str) -> str:
            """Extract specific regulations of a given type from regulatory text. Identifies regulation names, section numbers, and requirements."""
            prompt = f"""Extract all {regulation_type} regulations from this text. For each regulation found, provide:
- Regulation name and number
- Key requirements
- Applicable entities/transactions

Text:
{context[:3000]}

Return a structured list of regulations found. If none found for this type, say "No {regulation_type} regulations found in this context." """

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            extracted["regulations"].append({"type": regulation_type, "findings": content})
            return content

        def cross_reference_regulation(regulation_name: str) -> str:
            """Search the vector store for additional context about a specific regulation. Use this to find related rules, amendments, or enforcement guidance."""
            if not self.vector_store:
                return f"No vector store available. Using extracted context only for {regulation_name}."
            docs = self.vector_store.search(regulation_name, k=3)
            if not docs:
                return f"No additional documents found for {regulation_name}."
            results = []
            for i, doc in enumerate(docs):
                source = doc.metadata.get("filename", "unknown")
                results.append(f"[{source}]: {doc.page_content[:400]}")
            extracted["citations"].extend([
                {"regulation": regulation_name, "source": doc.metadata.get("filename", "unknown")}
                for doc in docs
            ])
            return f"Cross-reference results for {regulation_name}:\n\n" + "\n\n".join(results)

        def extract_thresholds(context: str) -> str:
            """Extract numerical thresholds, limits, and deadlines from regulatory text. Identifies dollar amounts, time limits, percentage requirements, etc."""
            prompt = f"""Extract ALL numerical thresholds, limits, and deadlines from this regulatory text:

{context[:3000]}

For each threshold found, provide:
- The specific number/amount
- What it applies to
- The regulation it comes from
- Consequences of exceeding it

If no thresholds found, say "No numerical thresholds found." """

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            extracted["thresholds"].append(content)
            return content

        return [
            StructuredTool.from_function(
                func=extract_regulations,
                name="extract_regulations",
                description="Extract specific regulations of a given type (AML, KYC, BSA, etc.) from regulatory text.",
                args_schema=ExtractRegulationsInput
            ),
            StructuredTool.from_function(
                func=cross_reference_regulation,
                name="cross_reference_regulation",
                description="Search the document store for additional context about a specific regulation. Use to find related rules or enforcement guidance.",
                args_schema=CrossReferenceInput
            ),
            StructuredTool.from_function(
                func=extract_thresholds,
                name="extract_thresholds",
                description="Extract numerical thresholds, dollar limits, time deadlines, and percentage requirements from regulatory text.",
                args_schema=ExtractThresholdsInput
            ),
        ]

    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Policy Extraction Agent specializing in banking and financial compliance.

Your job is to thoroughly extract all applicable policies, regulations, and compliance requirements from regulatory documents.

Strategy:
1. First, extract regulations by type — start with the most likely types based on the query (e.g., AML for money laundering, KYC for customer verification)
2. Extract numerical thresholds — these are critical for compliance (e.g., $10,000 CTR threshold)
3. Cross-reference key regulations in the document store to find related rules or amendments
4. Be thorough — missing a regulation is worse than including a marginal one

Always cite specific regulation sections and numbers when possible."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            max_iterations=8,
            handle_parsing_errors=True
        )

    def extract_policies(self, context: str, query: str) -> Dict:
        """Run the policy extraction agent"""
        self._extracted_data = {
            "regulations": [],
            "policies": [],
            "thresholds": [],
            "citations": []
        }

        input_text = f"""Extract all applicable policies and regulations from the following context.

Compliance query: {query}

Regulatory context:
{context[:4000]}

Identify: applicable regulations (by type), specific policy requirements, numerical thresholds, and provide citations."""

        result = self.agent_executor.invoke({"input": input_text})

        return {
            "extracted_policies": result["output"],
            "structured_data": self._extracted_data,
            "agent": "PolicyExtractionAgent",
            "status": "completed"
        }
