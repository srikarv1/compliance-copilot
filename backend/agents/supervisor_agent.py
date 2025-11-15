from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
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

class SupervisorAgent:
    def __init__(self, retriever, policy_extractor, risk_classifier, hallucination_guard):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.retriever = retriever
        self.policy_extractor = policy_extractor
        self.risk_classifier = risk_classifier
        self.hallucination_guard = hallucination_guard
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_node("policy_extractor", self._policy_extractor_node)
        workflow.add_node("risk_classifier", self._risk_classifier_node)
        workflow.add_node("hallucination_guard", self._hallucination_guard_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("retriever")
        
        # Add edges
        workflow.add_edge("retriever", "policy_extractor")
        workflow.add_edge("policy_extractor", "risk_classifier")
        workflow.add_edge("risk_classifier", "hallucination_guard")
        workflow.add_edge("hallucination_guard", "finalize")
        workflow.add_edge("finalize", END)
        
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
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize and generate comprehensive report"""
        system_prompt = """You are a compliance officer generating a final compliance report.
        Synthesize all agent findings into a comprehensive, actionable report."""
        
        user_prompt = f"""Generate a final compliance report based on:
        
        Query: {state['query']}
        
        Policies Extracted:
        {state['extracted_policies']}
        
        Risk Assessment:
        {state['risk_assessment']}
        
        Verification:
        {state['verification']}
        
        Create a comprehensive report with:
        1. Executive Summary
        2. Applicable Regulations
        3. Risk Assessment
        4. Violations (if any)
        5. Remediation Steps
        6. Recommendations
        
        Format as a professional compliance report."""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Extract content from AIMessage
        content = response.content if hasattr(response, 'content') else str(response)
        state["final_report"] = content
        state["agent_history"].append("SupervisorAgent: Generated final report")
        return state
    
    def process(self, query: str, transaction_data: Dict = None) -> Dict:
        """Process a compliance query through the workflow"""
        initial_state = {
            "query": query,
            "transaction_data": transaction_data or {},
            "retrieved_context": "",
            "extracted_policies": "",
            "risk_assessment": "",
            "verification": "",
            "final_report": "",
            "agent_history": [],
            "current_agent": "supervisor"
        }
        
        result = self.workflow.invoke(initial_state)
        return result

