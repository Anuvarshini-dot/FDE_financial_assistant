"""
FastAPI backend for the Finance Policy Assistant.
Exposes endpoints for querying the RAG pipeline and managing the vector store.
"""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from document_processor import get_or_build_vector_store, build_vector_store
from rag_pipeline import build_rag_chain, query_rag

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set. Create backend/.env with your key.")

# Global state
vector_store = None
rag_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global vector_store, rag_chain
    print("Initializing vector store and RAG chain...")
    vector_store = get_or_build_vector_store(OPENAI_API_KEY)
    rag_chain = build_rag_chain(vector_store, OPENAI_API_KEY)
    print("Finance Policy Assistant is ready.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="Finance Policy Assistant API",
    description="RAG-powered assistant for enterprise finance policy queries",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    source: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


@app.get("/health")
def health():
    return {"status": "ok", "ready": rag_chain is not None}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized.")

    result = query_rag(rag_chain, request.question)
    return QueryResponse(
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result["sources"]],
    )


@app.post("/rebuild-index")
def rebuild_index():
    """Force-rebuild the FAISS vector index from scratch."""
    global vector_store, rag_chain
    vector_store = build_vector_store(OPENAI_API_KEY)
    rag_chain = build_rag_chain(vector_store, OPENAI_API_KEY)
    return {"status": "Index rebuilt successfully."}
