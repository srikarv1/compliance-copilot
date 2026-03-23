from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
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
        self._collected_docs = []
        self.tools = self._build_tools()
        self.agent_executor = self._build_agent()

    def _build_tools(self) -> list:
        """Build tools the retriever agent can use"""

        class SearchInput(BaseModel):
            query: str = Field(description="The search query to find relevant regulatory documents")
            k: int = Field(default=5, description="Number of documents to retrieve (1-20)")

        class ScoredSearchInput(BaseModel):
            query: str = Field(description="The search query")
            k: int = Field(default=5, description="Number of documents to retrieve")
            min_score: float = Field(default=0.0, description="Minimum similarity score threshold (0-1). Documents below this score are filtered out")

        class RefineQueryInput(BaseModel):
            original_query: str = Field(description="The original search query")
            context: str = Field(description="Additional context to refine the query (e.g., transaction type, region, regulation area)")

        vs = self.vector_store
        collected = self._collected_docs

        def vector_search(query: str, k: int = 5) -> str:
            """Search the regulatory document vector store for relevant documents. Returns document content and metadata."""
            docs = vs.search(query, k=k)
            if not docs:
                return "No documents found for this query."
            collected.extend(docs)
            results = []
            for i, doc in enumerate(docs):
                source = doc.metadata.get("filename", "unknown")
                results.append(f"[Doc {i+1}] (source: {source})\n{doc.page_content[:600]}")
            return "\n\n---\n\n".join(results)

        def scored_search(query: str, k: int = 5, min_score: float = 0.0) -> str:
            """Search with similarity scores to assess retrieval quality. Use this to judge if results are relevant enough or if you need to refine your query."""
            results = vs.search_with_score(query, k=k)
            if not results:
                return "No documents found."
            output = []
            for i, (doc, score) in enumerate(results):
                if score >= min_score:
                    collected.append(doc)
                    source = doc.metadata.get("filename", "unknown")
                    output.append(f"[Doc {i+1}] Score: {score:.4f} (source: {source})\n{doc.page_content[:600]}")
            if not output:
                return f"No documents met the minimum score threshold of {min_score}."
            return "\n\n---\n\n".join(output)

        def refine_query(original_query: str, context: str) -> str:
            """Rewrite a search query to improve retrieval results. Use this when initial search results are poor or too broad."""
            refine_prompt = f"""Rewrite this regulatory document search query to be more specific and effective.

Original query: {original_query}
Additional context: {context}

Return ONLY the refined query string, nothing else."""
            response = self.llm.invoke(refine_prompt)
            return f"Refined query: {response.content}"

        return [
            StructuredTool.from_function(
                func=vector_search,
                name="vector_search",
                description="Search the regulatory document vector store for relevant documents. Returns document content and metadata.",
                args_schema=SearchInput
            ),
            StructuredTool.from_function(
                func=scored_search,
                name="scored_search",
                description="Search with similarity scores to assess retrieval quality. Use this to judge if results are relevant enough or if you need to refine your query.",
                args_schema=ScoredSearchInput
            ),
            StructuredTool.from_function(
                func=refine_query,
                name="refine_query",
                description="Rewrite a search query to improve retrieval results. Use when initial results are poor or too broad.",
                args_schema=RefineQueryInput
            ),
        ]

    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent with tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Retrieval Agent specializing in finding relevant regulatory and compliance documents.

Your job is to find the most relevant regulatory documents for a given compliance query.

Strategy:
1. Start with a scored_search to assess the quality of results for the initial query
2. If scores are low or results seem off-topic, use refine_query to improve the search
3. Try different search angles — search for the regulation name, the transaction type, the jurisdiction
4. Aim to collect 3-7 highly relevant documents covering different aspects of the query
5. Stop when you have sufficient coverage of the regulatory landscape for the query

Always explain your reasoning about why results are or aren't relevant."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            max_iterations=6,
            handle_parsing_errors=True
        )

    def retrieve_relevant_context(self, query: str, transaction_data: Dict = None) -> Dict:
        """Run the retriever agent to find relevant documents"""
        self._collected_docs = []

        # Build input with transaction context
        input_text = f"Find regulatory documents relevant to this compliance query: {query}"
        if transaction_data:
            tx_details = []
            if transaction_data.get("type"):
                tx_details.append(f"Transaction type: {transaction_data['type']}")
            if transaction_data.get("amount"):
                tx_details.append(f"Amount: {transaction_data['amount']}")
            if transaction_data.get("region"):
                tx_details.append(f"Region/Jurisdiction: {transaction_data['region']}")
            if transaction_data.get("customer_type"):
                tx_details.append(f"Customer type: {transaction_data['customer_type']}")
            if tx_details:
                input_text += f"\n\nTransaction context:\n" + "\n".join(tx_details)

        self.agent_executor.invoke({"input": input_text})

        # Deduplicate collected docs by content
        seen = set()
        unique_docs = []
        for doc in self._collected_docs:
            content_hash = hash(doc.page_content[:200])
            if content_hash not in seen:
                seen.add(content_hash)
                unique_docs.append(doc)

        return {
            "query": query,
            "relevant_documents": unique_docs,
            "document_count": len(unique_docs),
            "context": "\n\n".join([doc.page_content for doc in unique_docs])
        }
