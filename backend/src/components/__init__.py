"""
Components Package

Core processing components for the Research Paper Navigator.

Exports:
    PDFIngestor: Handles PDF-to-Markdown conversion via LlamaParse
    PDFIngestionError: Custom exception for ingestion failures
    SemanticChunker: Splits Markdown into academic sections
    extract_paper_metadata: Extract structured metadata from paper text
    synthesize_relationship: Compare two papers and determine relationship
"""

from src.components.pdf_ingestion import PDFIngestor, PDFIngestionError
from src.components.chunking import SemanticChunker
from src.components.connection_engine import (
    extract_paper_metadata,
    synthesize_relationship,
    extract_metadata_safe,
    synthesize_relationship_safe,
)

__all__ = [
    "PDFIngestor",
    "PDFIngestionError", 
    "SemanticChunker",
    "extract_paper_metadata",
    "synthesize_relationship",
    "extract_metadata_safe",
    "synthesize_relationship_safe",
]

