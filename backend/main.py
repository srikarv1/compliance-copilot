from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import os
import tempfile
from config import Config
from vector_store import VectorStoreManager
from agents.retriever_agent import RetrieverAgent
from agents.policy_extraction_agent import PolicyExtractionAgent
from agents.risk_classification_agent import RiskClassificationAgent
from agents.hallucination_guard_agent import HallucinationGuardAgent
from agents.supervisor_agent import SupervisorAgent

# Ensure OPENAI_API_KEY is set in environment for langchain-openai
if Config.OPENAI_API_KEY and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY

app = FastAPI(title="Compliance Copilot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStoreManager()
retriever_agent = RetrieverAgent(vector_store)
policy_extractor = PolicyExtractionAgent()
risk_classifier = RiskClassificationAgent()
hallucination_guard = HallucinationGuardAgent()
supervisor = SupervisorAgent(
    retriever_agent,
    policy_extractor,
    risk_classifier,
    hallucination_guard
)

class ComplianceQuery(BaseModel):
    query: str
    transaction_data: Optional[Dict] = None

class ComplianceResponse(BaseModel):
    final_report: str
    risk_assessment: str
    extracted_policies: str
    verification: str
    agent_history: list

@app.get("/")
async def root():
    return {"message": "Compliance Copilot API", "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/compliance/analyze", response_model=ComplianceResponse)
async def analyze_compliance(query: ComplianceQuery):
    """Main endpoint for compliance analysis"""
    try:
        result = supervisor.process(
            query.query,
            query.transaction_data
        )
        return ComplianceResponse(
            final_report=result["final_report"],
            risk_assessment=result["risk_assessment"],
            extracted_policies=result["extracted_policies"],
            verification=result["verification"],
            agent_history=result["agent_history"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest regulatory documents"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Ingest into vector store
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type
        }
        ids = vector_store.ingest_pdf(tmp_path, metadata)
        
        # Clean up
        os.unlink(tmp_path)
        
        return {
            "message": "Document ingested successfully",
            "document_ids": ids if ids else [],
            "filename": file.filename
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/documents/search")
async def search_documents(query: str, k: int = 5):
    """Search documents in vector store"""
    try:
        docs = vector_store.search(query, k=k)
        return {
            "query": query,
            "results": [
                {
                    "content": doc.page_content[:500],
                    "metadata": doc.metadata
                }
                for doc in docs
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

