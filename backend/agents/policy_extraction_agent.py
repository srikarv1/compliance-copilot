from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict, List

class PolicyExtractionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
    
    def extract_policies(self, context: str, query: str) -> Dict:
        """Extract relevant policies and regulations from context"""
        system_prompt = """You are a compliance expert specializing in banking regulations.
        Your task is to extract specific policies, regulations, and rules from regulatory documents.
        Be precise and cite specific regulation numbers and sections."""
        
        user_prompt = f"""Given the following regulatory context and query, extract:
        1. Specific regulations that apply
        2. Policy requirements
        3. Compliance thresholds
        4. Regulatory citations
        
        Query: {query}
        
        Context:
        {context}
        
        Format your response as JSON with:
        - regulations: list of applicable regulations
        - policies: list of policy requirements
        - thresholds: any numerical thresholds mentioned
        - citations: specific regulation citations"""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Extract content from AIMessage
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "extracted_policies": content,
            "agent": "PolicyExtractionAgent",
            "status": "completed"
        }

