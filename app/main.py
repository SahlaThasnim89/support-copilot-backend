from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import rag,ingest
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Support Copilot API",
    description="RAG-based support agent that suggests replies using past tickets",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rag.router, tags=["RAG"])
app.include_router(ingest.router, tags=["INGEST"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Support Copilot API is running"}
 
 
@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}