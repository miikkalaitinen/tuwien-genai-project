"""
Research Paper Navigator - Backend Source Package

This package contains the core components for the Research Paper Navigator:
- components/: PDF ingestion, semantic chunking, connection engine
- prompts/: LLM prompt templates for Student and Researcher modes
- batch_processor.py: CLI utility for batch processing

Usage:
    from src.components import PDFIngestor, SemanticChunker
    from src.batch_processor import BatchProcessor
"""

__version__ = "1.0.0"
