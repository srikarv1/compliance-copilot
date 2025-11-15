from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict, List

class HallucinationGuardAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.0  # Lower temperature for fact-checking
        )
    
    def verify_facts(self, claims: str, source_documents: List, context: str) -> Dict:
        """Verify claims against source documents to prevent hallucinations"""
        system_prompt = """You are a fact-checker for compliance reports.
        Your job is to verify that all claims are supported by the source documents.
        Flag any unsupported claims or potential hallucinations."""
        
        sources_text = "\n\n".join([
            f"Source {i+1}:\n{doc.page_content[:500]}" 
            for i, doc in enumerate(source_documents[:5])
        ])
        
        user_prompt = f"""Verify the following claims against the source documents:
        
        Claims to verify:
        {claims}
        
        Source Documents:
        {sources_text}
        
        Additional Context:
        {context}
        
        For each claim, determine:
        1. Is it supported by sources? (YES/NO/PARTIAL)
        2. Confidence level (0-100)
        3. Source citations
        4. Any unsupported claims
        
        Format as JSON with: verified_claims, confidence, citations, warnings"""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Extract content from AIMessage
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "verification": content,
            "agent": "HallucinationGuardAgent",
            "status": "completed"
        }

