from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict, List


class HallucinationGuardAgent:
    def __init__(self, vector_store=None):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.0  # Zero temperature for deterministic fact-checking
        )
        self.vector_store = vector_store
        self._verification_log = []
        self._flagged_claims = []
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self) -> list:
        """Build tools for hallucination detection"""

        class VerifyClaimInput(BaseModel):
            claim: str = Field(description="The specific claim to verify (e.g., 'BSA requires CTR filing for transactions over $10,000')")
            source_text: str = Field(description="The source document text to verify the claim against")

        class SearchEvidenceInput(BaseModel):
            claim: str = Field(description="The claim to find evidence for in the document store")

        class FlagClaimInput(BaseModel):
            claim: str = Field(description="The unsupported claim to flag")
            reason: str = Field(description="Why this claim is flagged (e.g., 'no source document mentions this threshold', 'regulation number does not match')")
            severity: str = Field(description="Severity of the issue: 'minor' (wording imprecise), 'major' (claim not in sources), 'critical' (contradicts sources)")

        verification_log = self._verification_log
        flagged = self._flagged_claims

        def verify_claim_against_source(claim: str, source_text: str) -> str:
            """Verify a specific claim against source document text. Returns whether the claim is SUPPORTED, PARTIALLY SUPPORTED, or UNSUPPORTED with explanation."""
            prompt = f"""You are a strict fact-checker. Verify this claim against the source text.

CLAIM: {claim}

SOURCE TEXT:
{source_text[:2000]}

Rules:
- SUPPORTED: The claim is directly stated or clearly implied by the source
- PARTIALLY SUPPORTED: The source mentions related concepts but the specific claim has details not in the source
- UNSUPPORTED: The source does not contain information supporting this claim
- CONTRADICTED: The source explicitly contradicts this claim

Return your verdict as: VERDICT: [SUPPORTED/PARTIALLY SUPPORTED/UNSUPPORTED/CONTRADICTED]
Then explain your reasoning with specific quotes from the source."""

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            verdict = "unknown"
            for v in ["SUPPORTED", "PARTIALLY SUPPORTED", "UNSUPPORTED", "CONTRADICTED"]:
                if v in content.upper():
                    verdict = v
                    break

            verification_log.append({
                "claim": claim[:200],
                "verdict": verdict,
                "details": content[:500]
            })

            return content

        def search_for_evidence(claim: str) -> str:
            """Search the regulatory document store for evidence supporting or refuting a claim. Use this when the provided source text doesn't cover the claim."""
            if not self.vector_store:
                return "No vector store available. Cannot search for additional evidence."
            docs = self.vector_store.search(claim, k=3)
            if not docs:
                return f"No evidence found in document store for: {claim}"
            results = []
            for i, doc in enumerate(docs):
                source = doc.metadata.get("filename", "unknown")
                results.append(f"[Evidence {i+1}] ({source}):\n{doc.page_content[:500]}")
            return "\n\n".join(results)

        def flag_unsupported_claim(claim: str, reason: str, severity: str) -> str:
            """Flag a claim that cannot be verified or is contradicted by sources. This adds it to the verification report as a warning."""
            entry = {
                "claim": claim,
                "reason": reason,
                "severity": severity
            }
            flagged.append(entry)
            return f"⚠️ FLAGGED ({severity}): \"{claim[:100]}...\"\nReason: {reason}\nTotal flagged claims: {len(flagged)}"

        return [
            StructuredTool.from_function(
                func=verify_claim_against_source,
                name="verify_claim_against_source",
                description="Verify a specific claim against source document text. Returns SUPPORTED, PARTIALLY SUPPORTED, UNSUPPORTED, or CONTRADICTED.",
                args_schema=VerifyClaimInput
            ),
            StructuredTool.from_function(
                func=search_for_evidence,
                name="search_for_evidence",
                description="Search the document store for evidence supporting or refuting a claim. Use when source text doesn't cover the claim.",
                args_schema=SearchEvidenceInput
            ),
            StructuredTool.from_function(
                func=flag_unsupported_claim,
                name="flag_unsupported_claim",
                description="Flag an unsupported or contradicted claim with severity level. Adds it to the verification report as a warning.",
                args_schema=FlagClaimInput
            ),
        ]

    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Hallucination Guard Agent. Your job is to verify that all claims in compliance reports are supported by source documents.

This is critical — in regulatory compliance, a fabricated regulation or incorrect threshold could lead to legal liability.

Strategy:
1. Break the input into individual verifiable claims (regulation names, thresholds, requirements, risk assessments)
2. For each significant claim, verify it against the provided source text using verify_claim_against_source
3. If a claim isn't covered by the provided sources, use search_for_evidence to look for supporting documents
4. Flag any claim that is UNSUPPORTED or CONTRADICTED using flag_unsupported_claim
5. Pay special attention to: specific regulation numbers, dollar thresholds, time limits, and named requirements

Be thorough but practical — verify the most important claims first (regulation citations, thresholds, violation assessments)."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            max_iterations=12,
            handle_parsing_errors=True
        )

    def verify_facts(self, claims: str, source_documents: List, context: str) -> Dict:
        """Run the hallucination guard agent"""
        self._verification_log = []
        self._flagged_claims = []

        sources_text = "\n\n".join([
            f"Source {i+1} ({doc.metadata.get('filename', 'unknown')}):\n{doc.page_content[:600]}"
            for i, doc in enumerate(source_documents[:5])
        ])

        input_text = f"""Verify the following compliance analysis claims against the source documents.

CLAIMS TO VERIFY:
{claims[:4000]}

SOURCE DOCUMENTS:
{sources_text}

ADDITIONAL CONTEXT:
{context[:1500]}

Systematically verify each significant claim. Flag anything unsupported."""

        result = self.agent_executor.invoke({"input": input_text})

        return {
            "verification": result["output"],
            "verification_log": self._verification_log,
            "flagged_claims": self._flagged_claims,
            "agent": "HallucinationGuardAgent",
            "status": "completed"
        }
