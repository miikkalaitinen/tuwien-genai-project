"""
Module: FastAPI Application (Main Entry Point)
Owner: Miikka (Frontend & Visualization Developer)

TODO for Miikka:
- Add file upload endpoints for PDF processing
- Integrate with connection_engine.py for relationship detection
- Add endpoints for graph data retrieval
- Implement Student/Researcher mode toggle

The PDF processing pipeline is ready:
    from src.components import PDFIngestor, SemanticChunker
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Research Paper Navigator API",
    version="0.1.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Research Paper Navigator API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
