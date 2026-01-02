"""
Module: Utilities
Owner: Marta (AI Backend Architect)

TODO for Marta:
- Add API key management (OpenAI, LlamaCloud)
- Configure LlamaIndex and ChromaDB
- Add helper functions for the connection_engine
- Define JSON output schemas for frontend

The PDF ingestion pipeline is ready to use:
    from src.components import PDFIngestor, SemanticChunker
"""

from pathlib import Path

# Path constants
BACKEND_ROOT = Path(__file__).parent.parent
DATA_DIR = BACKEND_ROOT / "data"
