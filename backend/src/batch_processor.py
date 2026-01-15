"""
Batch Processor CLI

This is a CLI utility for batch processing research papers. It:
1. Ingests PDFs from a data directory using LlamaParse
2. Applies semantic chunking to extract sections
3. Saves structured JSON output
4. Optionally saves raw Markdown for debugging

Usage:
    python -m src.batch_processor                    # Process all PDFs
    python -m src.batch_processor --filter "FOOL"    # Filter by filename
    python -m src.batch_processor --no-debug         # Skip debug markdown
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.components.pdf_ingestion import PDFIngestor, PDFIngestionError
from src.components.chunking import SemanticChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Processes multiple PDFs through the ingestion and chunking pipeline.
    
    Handles batch operations with proper error recovery, ensuring that
    a single failed PDF doesn't stop the entire batch.
    
    Attributes:
        data_dir: Directory containing input PDFs.
        output_file: Path for the output JSON file.
        debug_dir: Optional directory for saving raw Markdown files.
        chunker: SemanticChunker instance for section extraction.
    
    Example:
        >>> processor = BatchProcessor(
        ...     data_dir=Path("./data"),
        ...     output_file=Path("./processed.json")
        ... )
        >>> processor.run()
    """
    
    def __init__(
        self,
        data_dir: Path,
        output_file: Path,
        debug_dir: Optional[Path] = None,
        save_debug: bool = True
    ) -> None:
        """
        Initialize the batch processor.
        
        Args:
            data_dir: Directory containing PDF files to process.
            output_file: Path where the JSON output will be saved.
            debug_dir: Directory for debug Markdown files. Defaults to data_dir/../debug_markdowns
            save_debug: Whether to save raw Markdown files for debugging.
        """
        self.data_dir = Path(data_dir)
        self.output_file = Path(output_file)
        self.save_debug = save_debug
        
        # Default debug directory
        if debug_dir is None:
            self.debug_dir = self.data_dir.parent / "debug_markdowns"
        else:
            self.debug_dir = Path(debug_dir)
        
        # Create debug directory if needed
        if self.save_debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunker = SemanticChunker()
        
        logger.info(f"BatchProcessor initialized")
        logger.info(f"  Data dir:    {self.data_dir}")
        logger.info(f"  Output file: {self.output_file}")
        if self.save_debug:
            logger.info(f"  Debug dir:   {self.debug_dir}")

    def _get_pdf_files(self, filter_pattern: Optional[str] = None) -> List[Path]:
        """
        Get list of PDF files to process.
        
        Args:
            filter_pattern: Optional case-insensitive substring to filter filenames.
        
        Returns:
            List of Path objects for PDFs to process.
        """
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        all_pdfs = list(self.data_dir.glob("*.pdf")) + list(self.data_dir.glob("*.PDF"))
        
        if filter_pattern:
            pattern_lower = filter_pattern.lower()
            filtered = [p for p in all_pdfs if pattern_lower in p.name.lower()]
            logger.info(f"Filter '{filter_pattern}': {len(filtered)}/{len(all_pdfs)} files match")
            return filtered
        
        return all_pdfs

    def _process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a single PDF through the pipeline.
        
        Args:
            pdf_path: Path to the PDF file.
        
        Returns:
            Dictionary with processing results or error information.
        """
        try:
            logger.info(f"Processing: {pdf_path.name}")
            
            # 1. Ingest (Convert PDF to Markdown via LlamaParse)
            ingestor = PDFIngestor(str(pdf_path), verbose=False)
            full_markdown = ingestor.extract_clean_text()
            
            # 2. Save debug Markdown if enabled
            if self.save_debug:
                debug_path = self.debug_dir / f"{pdf_path.name}.md"
                debug_path.write_text(full_markdown, encoding="utf-8")
                logger.debug(f"Saved debug Markdown: {debug_path}")
            
            # 3. Chunk (Semantic sectioning)
            sections = self.chunker.split_by_section(full_markdown)
            section_summary = self.chunker.get_section_summary(sections)
            
            # 4. Build result object
            return {
                "filename": pdf_path.name,
                "metadata": ingestor.get_metadata(),
                "sections": sections,
                "section_sizes": section_summary,
                "status": "success"
            }
            
        except PDFIngestionError as e:
            logger.error(f"Ingestion failed for {pdf_path.name}: {e}")
            return {
                "filename": pdf_path.name,
                "status": "error",
                "error_type": "ingestion",
                "error_msg": str(e)
            }
        except Exception as e:
            logger.exception(f"Unexpected error processing {pdf_path.name}")
            return {
                "filename": pdf_path.name,
                "status": "error",
                "error_type": "unknown",
                "error_msg": str(e)
            }

    def run(self, filter_pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Execute batch processing on all matching PDFs.
        
        Args:
            filter_pattern: Optional substring to filter filenames.
        
        Returns:
            List of result dictionaries for all processed files.
        """
        pdf_files = self._get_pdf_files(filter_pattern)
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return []
        
        logger.info(f"Starting batch processing: {len(pdf_files)} files")
        
        results: List[Dict[str, Any]] = []
        success_count = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"[{i}/{len(pdf_files)}] {pdf_path.name}")
            result = self._process_single_pdf(pdf_path)
            results.append(result)
            
            if result["status"] == "success":
                success_count += 1
        
        # Save results
        self._save_results(results)
        
        # Log summary
        logger.info("=" * 50)
        logger.info(f"Batch complete: {success_count}/{len(pdf_files)} successful")
        
        return results

    def _save_results(self, data: List[Dict[str, Any]]) -> None:
        """
        Save processing results to JSON file.
        
        Args:
            data: List of result dictionaries.
        """
        try:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {self.output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Batch process research papers through the ingestion pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.batch_processor
    python -m src.batch_processor --filter "HyperDrive"
    python -m src.batch_processor --no-debug --verbose
        """
    )
    
    parser.add_argument(
        "--filter", "-f",
        type=str,
        default=None,
        help="Filter PDFs by filename substring (case-insensitive)"
    )
    
    parser.add_argument(
        "--data-dir", "-d",
        type=str,
        default="data",
        help="Directory containing PDF files (default: data)"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="processed_papers.json",
        help="Output JSON file path (default: processed_papers.json)"
    )
    
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Skip saving debug Markdown files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    
    return parser


def main() -> int:
    """
    CLI entry point for batch processing.
    
    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Resolve paths relative to backend directory
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / args.data_dir
    output_file = backend_dir / args.output
    debug_dir = backend_dir / "debug_markdowns"
    
    try:
        processor = BatchProcessor(
            data_dir=data_dir,
            output_file=output_file,
            debug_dir=debug_dir,
            save_debug=not args.no_debug
        )
        
        results = processor.run(filter_pattern=args.filter)
        
        # Return error code if any files failed
        failed = sum(1 for r in results if r["status"] != "success")
        return 1 if failed > 0 else 0
        
    except Exception as e:
        logger.exception(f"Batch processing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())