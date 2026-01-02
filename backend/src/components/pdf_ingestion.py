"""
Module: PDF Ingestion (LlamaParse Edition)
Responsibility: Send PDFs to LlamaCloud to get structured Markdown.
Owner: Jaime (Data Pipeline Engineer)

This module provides a robust PDF-to-Markdown conversion pipeline using
the LlamaParse API. It handles document extraction with proper error
handling and logging for production use.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from llama_parse import LlamaParse

# Configure module-level logger
logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_env_path)


class PDFIngestionError(Exception):
    """Custom exception for PDF ingestion failures."""
    pass


class PDFIngestor:
    """
    Handles PDF ingestion using the LlamaParse cloud API.
    
    This class provides a clean interface for converting PDF documents
    into structured Markdown format, preserving document hierarchy
    and formatting for downstream semantic chunking.
    
    Attributes:
        file_path: Absolute path to the PDF file to process.
        parser: Configured LlamaParse instance.
    
    Example:
        >>> ingestor = PDFIngestor("/path/to/paper.pdf")
        >>> markdown = ingestor.extract_clean_text()
        >>> metadata = ingestor.get_metadata()
    """
    
    def __init__(self, file_path: str, verbose: bool = False) -> None:
        """
        Initialize the PDF ingestor with a file path.
        
        Args:
            file_path: Absolute path to the PDF file.
            verbose: Enable verbose logging from LlamaParse API.
        
        Raises:
            FileNotFoundError: If the specified PDF file does not exist.
            ValueError: If the file is not a PDF.
        """
        self.file_path = Path(file_path)
        
        # Validate file exists and is a PDF
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if self.file_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF, got: {self.file_path.suffix}")
        
        # Configure LlamaParse with markdown output
        # result_type="markdown" preserves document structure for chunking
        self.parser = LlamaParse(
            result_type="markdown",
            verbose=verbose,
            language="en"
        )
        
        logger.debug(f"Initialized PDFIngestor for: {self.file_path.name}")

    def extract_clean_text(self) -> str:
        """
        Convert PDF to Markdown using LlamaParse API.
        
        Sends the PDF to LlamaCloud for processing and returns
        the extracted content as a single Markdown string with
        preserved structure (headers, tables, lists).
        
        Returns:
            Full Markdown representation of the PDF content.
        
        Raises:
            PDFIngestionError: If extraction fails for any reason.
        """
        logger.info(f"Extracting text from: {self.file_path.name}")
        
        try:
            # LlamaParse returns a list of documents (usually 1 per file)
            documents = self.parser.load_data(str(self.file_path))
            
            if not documents:
                raise PDFIngestionError(f"No content extracted from: {self.file_path.name}")
            
            # Combine all pages into one markdown string
            full_markdown = "\n\n".join([doc.text for doc in documents])
            
            logger.info(
                f"Successfully extracted {len(full_markdown):,} characters "
                f"from {self.file_path.name}"
            )
            
            return full_markdown
            
        except PDFIngestionError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract {self.file_path.name}: {e}")
            raise PDFIngestionError(f"Extraction failed: {e}") from e

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the processed PDF.
        
        Returns:
            Dictionary containing:
                - source: Parser used (always "LlamaParse")
                - file: Original filename
                - file_path: Full path to the file
                - file_size_kb: File size in kilobytes
        """
        file_size_kb = self.file_path.stat().st_size / 1024
        
        return {
            "source": "LlamaParse",
            "file": self.file_path.name,
            "file_path": str(self.file_path),
            "file_size_kb": round(file_size_kb, 2)
        }