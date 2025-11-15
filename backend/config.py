import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    PORT = int(os.getenv("PORT", 8000))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Model configurations
    EMBEDDING_MODEL = "text-embedding-3-small"
    LLM_MODEL = "gpt-4-turbo-preview"
    TEMPERATURE = 0.1

