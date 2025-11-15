from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from typing import Dict

class RiskClassificationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
    
    def classify_risk(self, context: str, policies: str, transaction_data: Dict = None) -> Dict:
        """Classify risk level and identify violations"""
        system_prompt = """You are a risk assessment expert for banking compliance.
        Classify risk levels as: LOW, MEDIUM, HIGH, CRITICAL.
        Identify specific violations and their severity."""
        
        transaction_info = ""
        if transaction_data:
            transaction_info = f"""
            Transaction Details:
            - Type: {transaction_data.get('type', 'N/A')}
            - Amount: {transaction_data.get('amount', 'N/A')}
            - Region: {transaction_data.get('region', 'N/A')}
            - Customer: {transaction_data.get('customer_type', 'N/A')}
            """
        
        user_prompt = f"""Analyze the following for compliance risk:
        
        {transaction_info}
        
        Policies and Regulations:
        {policies}
        
        Context:
        {context}
        
        Provide:
        1. Risk Level (LOW/MEDIUM/HIGH/CRITICAL)
        2. Violations identified (if any)
        3. Risk score (0-100)
        4. Reasoning
        
        Format as JSON with keys: risk_level, violations, risk_score, reasoning"""
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Extract content from AIMessage
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "risk_assessment": content,
            "agent": "RiskClassificationAgent",
            "status": "completed"
        }

