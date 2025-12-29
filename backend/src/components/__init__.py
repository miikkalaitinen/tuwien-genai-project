"""
Components Package

Core processing components for the Research Paper Navigator.

Exports:
    PDFIngestor: Handles PDF-to-Markdown conversion via LlamaParse
    PDFIngestionError: Custom exception for ingestion failures
    SemanticChunker: Splits Markdown into academic sections
"""

from src.components.pdf_ingestion import PDFIngestor, PDFIngestionError
from src.components.chunking import SemanticChunker

__all__ = [
    "PDFIngestor",
    "PDFIngestionError", 
    "SemanticChunker",
]
