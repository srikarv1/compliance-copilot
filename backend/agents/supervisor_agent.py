from langgraph.graph import StateGraph, END
from typing import Dict, List, TypedDict, Annotated
import operator

class AgentState(TypedDict):
    query: str
    transaction_data: Dict
    retrieved_context: str
    extracted_policies: str
    risk_assessment: str
    verification: str
    final_report: str
    agent_history: Annotated[List[str], operator.add]
    current_agent: str
    retry_count: int
    max_retries: int
    hallucination_detected: bool

class SupervisorAgent:
    def __init__(self, retriever, policy_extractor, risk_classifier, hallucination_guard, report_generator):
        self.retriever = retriever
        self.policy_extractor = policy_extractor
        self.risk_classifier = risk_classifier
        self.hallucination_guard = hallucination_guard
        self.report_generator = report_generator
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow orchestrating 5 specialized agents"""
        workflow = StateGraph(AgentState)

        # Add nodes for each agent
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_node("policy_extractor", self._policy_extractor_node)
        workflow.add_node("risk_classifier", self._risk_classifier_node)
        workflow.add_node("hallucination_guard", self._hallucination_guard_node)
        workflow.add_node("report_generator", self._report_generator_node)

        # Set entry point
        workflow.set_entry_point("retriever")

        # Add edges: sequential pipeline
        workflow.add_edge("retriever", "policy_extractor")
        workflow.add_edge("policy_extractor", "risk_classifier")
        workflow.add_edge("risk_classifier", "hallucination_guard")

        # CONDITIONAL EDGE: Route based on hallucination detection
        workflow.add_conditional_edges(
            "hallucination_guard",
            self._should_retry_or_finalize,
            {
                "retry": "retriever",           # Loop back to retriever
                "finalize": "report_generator"   # Continue to report generation
            }
        )

        workflow.add_edge("report_generator", END)

        return workflow.compile()

    def _retriever_node(self, state: AgentState) -> AgentState:
        """Retriever agent node"""
        result = self.retriever.retrieve_relevant_context(
            state["query"],
            state.get("transaction_data", {})
        )
        state["retrieved_context"] = result["context"]
        state["agent_history"].append("RetrieverAgent: Retrieved relevant documents")
        return state

    def _policy_extractor_node(self, state: AgentState) -> AgentState:
        """Policy extraction agent node"""
        result = self.policy_extractor.extract_policies(
            state["retrieved_context"],
            state["query"]
        )
        state["extracted_policies"] = result["extracted_policies"]
        state["agent_history"].append("PolicyExtractionAgent: Extracted policies")
        return state

    def _risk_classifier_node(self, state: AgentState) -> AgentState:
        """Risk classification agent node"""
        result = self.risk_classifier.classify_risk(
            state["retrieved_context"],
            state["extracted_policies"],
            state.get("transaction_data", {})
        )
        state["risk_assessment"] = result["risk_assessment"]
        state["agent_history"].append("RiskClassificationAgent: Classified risk")
        return state

    def _hallucination_guard_node(self, state: AgentState) -> AgentState:
        """Hallucination guard agent node"""
        # Get source documents from retriever
        docs = self.retriever.vector_store.search(state["query"], k=5)

        claims = f"{state['extracted_policies']}\n{state['risk_assessment']}"
        result = self.hallucination_guard.verify_facts(
            claims,
            docs,
            state["retrieved_context"]
        )
        state["verification"] = result["verification"]
        state["agent_history"].append("HallucinationGuardAgent: Verified facts")
        return state

    def _should_retry_or_finalize(self, state: AgentState) -> str:
        """
        Conditional routing logic: decide whether to retry (loop back to retriever)
        or proceed to report generation.

        Returns: "retry" or "finalize"
        """
        verification = state["verification"]
        retry_count = state["retry_count"]
        max_retries = state["max_retries"]

        # Check if max retries reached - ALWAYS go to finalize
        if retry_count >= max_retries:
            state["agent_history"].append(
                f"⚠️ Max retries ({max_retries}) reached. Proceeding to report generation."
            )
            return "finalize"

        # Check if hallucination was detected
        # Look for keywords that indicate unsupported/unverified claims
        hallucination_keywords = [
            "unsupported",
            "not supported",
            "no evidence",
            "cannot verify",
            "unverified",
            "confidence: 0",
            "confidence: low"
        ]

        has_hallucination = any(
            keyword.lower() in verification.lower()
            for keyword in hallucination_keywords
        )

        if has_hallucination and retry_count < max_retries:
            # LOOP BACK: Increment retry count and go back to retriever
            state["retry_count"] += 1
            state["hallucination_detected"] = True
            state["agent_history"].append(
                f"🔄 Hallucination detected. Retrying (attempt {state['retry_count']}/{max_retries})..."
            )
            return "retry"
        else:
            # PROCEED: No hallucination or max retries reached
            state["agent_history"].append("✅ Verification passed. Proceeding to report generation.")
            return "finalize"

    def _report_generator_node(self, state: AgentState) -> AgentState:
        """Report generation agent node"""
        result = self.report_generator.generate_report(
            state["query"],
            state["extracted_policies"],
            state["risk_assessment"],
            state["verification"]
        )
        state["final_report"] = result["final_report"]
        state["agent_history"].append("ReportGenerationAgent: Generated final compliance report")
        return state

    def process(self, query: str, transaction_data: Dict = None) -> Dict:
        """Process a compliance query through the multi-agent workflow"""
        initial_state = {
            "query": query,
            "transaction_data": transaction_data or {},
            "retrieved_context": "",
            "extracted_policies": "",
            "risk_assessment": "",
            "verification": "",
            "final_report": "",
            "agent_history": [],
            "current_agent": "supervisor",
            "retry_count": 0,
            "max_retries": 2,  # Allow up to 2 retries (3 total attempts)
            "hallucination_detected": False
        }

        result = self.workflow.invoke(initial_state)
        return result
