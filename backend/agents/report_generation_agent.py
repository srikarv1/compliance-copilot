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


class ReportGenerationAgent:
    def __init__(self, vector_store=None):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.vector_store = vector_store
        self._report_sections = {}
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self) -> list:
        """Build tools for report generation"""

        class CompileSectionInput(BaseModel):
            section_name: str = Field(description="Report section: 'executive_summary', 'applicable_regulations', 'risk_assessment', 'violations', 'remediation_steps', or 'recommendations'")
            content: str = Field(description="The content/data to compile into this section")

        class LookupCitationInput(BaseModel):
            regulation_reference: str = Field(description="The regulation to look up for proper citation (e.g., '31 CFR 1010.311', 'BSA Section 5318')")

        class AssembleReportInput(BaseModel):
            include_sections: str = Field(description="Comma-separated list of section names to include in the final report")

        sections = self._report_sections

        def compile_section(section_name: str, content: str) -> str:
            """Compile a specific section of the compliance report. The agent should call this for each section, providing the relevant data. The tool formats it professionally."""
            section_prompts = {
                "executive_summary": "Write a concise executive summary (3-5 sentences) of the compliance analysis findings.",
                "applicable_regulations": "List all applicable regulations with their full citations and key requirements.",
                "risk_assessment": "Summarize the risk assessment with the risk level, score, and key risk factors.",
                "violations": "Detail any identified violations with specific regulation references and evidence.",
                "remediation_steps": "Provide specific, actionable remediation steps ordered by priority.",
                "recommendations": "Provide forward-looking compliance recommendations."
            }

            instruction = section_prompts.get(
                section_name,
                f"Write the {section_name} section of a compliance report."
            )

            prompt = f"""{instruction}

Based on this data:
{content[:2500]}

Format professionally with clear structure. Use bullet points where appropriate."""

            response = self.llm.invoke(prompt)
            formatted = response.content if hasattr(response, 'content') else str(response)
            sections[section_name] = formatted
            return f"Section '{section_name}' compiled successfully.\n\nPreview:\n{formatted[:500]}..."

        def lookup_citation(regulation_reference: str) -> str:
            """Look up the full citation and context for a regulation reference. Use this to ensure citations in the report are accurate and complete."""
            if not self.vector_store:
                return f"Using standard citation format for {regulation_reference}."
            docs = self.vector_store.search(regulation_reference, k=2)
            if not docs:
                return f"No additional citation context found for {regulation_reference}. Use standard citation format."
            results = []
            for doc in docs:
                source = doc.metadata.get("filename", "unknown")
                results.append(f"[{source}]: {doc.page_content[:300]}")
            return f"Citation context for {regulation_reference}:\n" + "\n".join(results)

        def assemble_report(include_sections: str) -> str:
            """Assemble the final report from compiled sections. Call this after all individual sections have been compiled."""
            section_names = [s.strip() for s in include_sections.split(",")]

            section_titles = {
                "executive_summary": "Executive Summary",
                "applicable_regulations": "Applicable Regulations",
                "risk_assessment": "Risk Assessment",
                "violations": "Violations Identified",
                "remediation_steps": "Remediation Steps",
                "recommendations": "Recommendations"
            }

            report_parts = ["# Compliance Analysis Report\n"]
            for name in section_names:
                if name in sections:
                    title = section_titles.get(name, name.replace("_", " ").title())
                    report_parts.append(f"\n## {title}\n\n{sections[name]}")
                else:
                    report_parts.append(f"\n## {name.replace('_', ' ').title()}\n\n*Section not yet compiled.*")

            final = "\n".join(report_parts)
            sections["_final"] = final
            return final

        return [
            StructuredTool.from_function(
                func=compile_section,
                name="compile_section",
                description="Compile a specific section of the compliance report. Call this for each section (executive_summary, applicable_regulations, risk_assessment, violations, remediation_steps, recommendations).",
                args_schema=CompileSectionInput
            ),
            StructuredTool.from_function(
                func=lookup_citation,
                name="lookup_citation",
                description="Look up the full citation and context for a regulation reference to ensure accuracy.",
                args_schema=LookupCitationInput
            ),
            StructuredTool.from_function(
                func=assemble_report,
                name="assemble_report",
                description="Assemble the final report from all compiled sections. Call this LAST after all sections are compiled.",
                args_schema=AssembleReportInput
            ),
        ]

    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Report Generation Agent that produces professional compliance reports.

Your job is to synthesize findings from other agents into a structured, actionable compliance report.

Strategy:
1. Review all input data (policies, risk assessment, verification results)
2. Look up citations for key regulations mentioned to ensure accuracy
3. Compile each section individually using compile_section:
   - executive_summary: High-level findings (compile this LAST since it summarizes everything)
   - applicable_regulations: All relevant regulations with citations
   - risk_assessment: Risk level, score, and factors
   - violations: Any identified violations with evidence
   - remediation_steps: Specific actions to take
   - recommendations: Forward-looking compliance advice
4. Assemble the final report using assemble_report

Compile sections in this order: applicable_regulations → violations → risk_assessment → remediation_steps → recommendations → executive_summary. Then assemble."""),
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

    def generate_report(self, query: str, extracted_policies: str, risk_assessment: str, verification: str) -> Dict:
        """Run the report generation agent"""
        self._report_sections = {}

        input_text = f"""Generate a comprehensive compliance report based on these findings:

ORIGINAL QUERY: {query}

EXTRACTED POLICIES AND REGULATIONS:
{extracted_policies[:3000]}

RISK ASSESSMENT:
{risk_assessment[:2000]}

VERIFICATION RESULTS:
{verification[:2000]}

Build the report section by section, look up citations for accuracy, then assemble the final report."""

        result = self.agent_executor.invoke({"input": input_text})

        final_report = self._report_sections.get("_final", result["output"])

        return {
            "final_report": final_report,
            "sections": {k: v for k, v in self._report_sections.items() if not k.startswith("_")},
            "agent": "ReportGenerationAgent",
            "status": "completed"
        }
