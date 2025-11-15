from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from config import Config
import os
from typing import List
from langchain_core.documents import Document

class VectorStoreManager:
    def __init__(self):
        # Use environment variable for API key (recommended for newer langchain-openai)
        # Ensure OPENAI_API_KEY is set in environment
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Initialize or load existing vector store"""
        # Ensure directory exists
        os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=Config.CHROMA_PERSIST_DIRECTORY,
            embedding_function=self.embeddings
        )
    
    def ingest_pdf(self, file_path: str, metadata: dict = None) -> List[str]:
        """Ingest a PDF file into the vector store"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if metadata:
                for doc in documents:
                    doc.metadata.update(metadata)
            
            texts = self.text_splitter.split_documents(documents)
            
            # add_documents returns a list of IDs
            ids = self.vector_store.add_documents(texts)
            
            # Handle case where add_documents might return None
            if ids is None:
                # Generate IDs based on document count
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            return ids if isinstance(ids, list) else []
        except Exception as e:
            error_msg = str(e)
            # Check for OpenAI quota/billing errors
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower() or "429" in error_msg:
                raise Exception(
                    f"OpenAI API quota exceeded. Please check your billing and plan details at https://platform.openai.com/account/billing. "
                    f"Error: {error_msg}"
                )
            raise Exception(f"Error ingesting PDF {file_path}: {error_msg}")
    
    def search(self, query: str, k: int = 5) -> List[Document]:
        """Search for relevant documents"""
        return self.vector_store.similarity_search(query, k=k)
    
    def search_with_score(self, query: str, k: int = 5):
        """Search with similarity scores"""
        return self.vector_store.similarity_search_with_score(query, k=k)

