from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from vector_store import VectorStoreManager
from config import Config
from typing import List, Dict

class RetrieverAgent:
    def __init__(self, vector_store: VectorStoreManager):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.vector_store = vector_store
    
    def retrieve_relevant_context(self, query: str, transaction_data: Dict = None) -> Dict:
        """Retrieve relevant regulatory and policy documents"""
        # Enhanced query construction
        enhanced_query = self._enhance_query(query, transaction_data)
        
        # Retrieve relevant documents
        docs = self.vector_store.search(enhanced_query, k=10)
        
        # Filter and rank by relevance
        relevant_docs = self._filter_relevant(docs, query)
        
        return {
            "query": query,
            "relevant_documents": relevant_docs,
            "document_count": len(relevant_docs),
            "context": "\n\n".join([doc.page_content for doc in relevant_docs])
        }
    
    def _enhance_query(self, query: str, transaction_data: Dict = None) -> str:
        """Enhance query with transaction context"""
        if transaction_data:
            context = f"Transaction type: {transaction_data.get('type', 'N/A')}, "
            context += f"Amount: {transaction_data.get('amount', 'N/A')}, "
            context += f"Region: {transaction_data.get('region', 'N/A')}"
            return f"{query}. Context: {context}"
        return query
    
    def _filter_relevant(self, docs: List, query: str) -> List:
        """Filter documents by relevance using LLM"""
        if not docs:
            return []
        
        prompt = f"""Given the query: "{query}"
        
Review these documents and return only the most relevant ones (max 5).
Documents:
{chr(10).join([f"{i+1}. {doc.page_content[:200]}..." for i, doc in enumerate(docs)])}

Return only the numbers of relevant documents, comma-separated:"""
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        # Extract content from AIMessage
        content = response.content if hasattr(response, 'content') else str(response)
        selected_indices = self._parse_indices(content)
        
        return [docs[i-1] for i in selected_indices if 1 <= i <= len(docs)]
    
    def _parse_indices(self, response: str) -> List[int]:
        """Parse document indices from LLM response"""
        try:
            indices = [int(x.strip()) for x in response.split(',')]
            return indices[:5]  # Limit to 5
        except:
            return list(range(1, min(6, len(response.split(',')) + 1)))

