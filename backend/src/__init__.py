"""
Research Paper Navigator - Backend Source Package

This package contains the core components for the llm pipeline, PDF ingestion,
semantic chunking, and connection engine for building a knowledge graph:

- components/: PDF ingestion, semantic chunking, connection engine
- prompts/: LLM prompt templates for Student and Researcher modes
- utils.py: LLM client, ChromaDB, Pydantic schemas, RAG functions
- integration.py: Bridge between PDF pipeline and AI connection engine
- batch_processor.py: CLI utility for batch processing

Usage:
    from src.components import PDFIngestor, SemanticChunker
    from src.components import extract_paper_metadata, synthesize_relationship
    from src.utils import store_paper_embedding, find_similar_papers
    from src.integration import process_papers_for_graph, build_paper_graph
"""

__version__ = "1.0.0"

