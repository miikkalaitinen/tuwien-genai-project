"""
Script: Inspect Extraction
Responsibility: Debug tool to inspect extracted sections from a specific paper.

This utility helps verify that the semantic chunking is working correctly
by displaying the methodology section (or any section) for a specific paper.

Usage:
    python inspect_extraction.py <partial_filename>
    python inspect_extraction.py HyperDrive
    python inspect_extraction.py --section results FOOL
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_JSON = Path("backend/processed_papers.json")
PREVIEW_CHARS = 500


def find_paper(
    data: list, 
    partial_name: str
) -> Optional[Dict[str, Any]]:
    """
    Find a paper by partial filename match.
    
    Args:
        data: List of paper dictionaries from processed_papers.json
        partial_name: Substring to match against filenames
    
    Returns:
        Matching paper dictionary, or None if not found.
    """
    partial_lower = partial_name.lower()
    
    for paper in data:
        if partial_lower in paper.get('filename', '').lower():
            return paper
    
    return None


def display_section(
    paper: Dict[str, Any],
    section_name: str = "methodology",
    preview_chars: int = PREVIEW_CHARS
) -> None:
    """
    Display a specific section from a paper.
    
    Args:
        paper: Paper dictionary with sections
        section_name: Name of section to display
        preview_chars: Number of characters for preview (start and end)
    """
    filename = paper.get('filename', 'Unknown')
    sections = paper.get('sections', {})
    
    print(f"\n📄 PAPER: {filename}")
    print("=" * 60)
    
    # Get the requested section
    content = sections.get(section_name, '')
    
    if not content or len(content.strip()) < 50:
        print(f"⚠️  WARNING: Section '{section_name}' is EMPTY or too short")
        print(f"\n   Available sections with content:")
        for name, text in sections.items():
            char_count = len(text)
            if char_count > 50:
                print(f"   ✅ {name}: {char_count:,} characters")
            elif char_count > 0:
                print(f"   ⚠️  {name}: {char_count} characters (minimal)")
        return
    
    # Display section info
    print(f"✅ SECTION: {section_name.upper()} ({len(content):,} characters)")
    print("-" * 60)
    
    if len(content) <= preview_chars * 2:
        # Content is small enough to show fully
        print(content)
    else:
        # Show start and end with ellipsis
        print("--- START ---")
        print(content[:preview_chars])
        print(f"\n... [{len(content) - preview_chars*2:,} characters omitted] ...\n")
        print("--- END ---")
        print(content[-preview_chars:])
    
    print("-" * 60)
    
    # Show section sizes summary
    print("\n📊 SECTION SIZES:")
    section_sizes = paper.get('section_sizes', {})
    if section_sizes:
        for name, size in sorted(section_sizes.items(), key=lambda x: -x[1]):
            if size > 0:
                bar = "█" * min(int(size / 1000), 40)
                print(f"   {name:15} {size:6,} chars  {bar}")
    else:
        # Calculate from sections if not present
        for name, text in sorted(sections.items(), key=lambda x: -len(x[1])):
            if len(text) > 0:
                bar = "█" * min(int(len(text) / 1000), 40)
                print(f"   {name:15} {len(text):6,} chars  {bar}")


def inspect_paper(
    partial_name: str,
    section: str = "methodology",
    json_path: Path = DEFAULT_JSON
) -> int:
    """
    Main inspection function.
    
    Args:
        partial_name: Substring to match against filenames
        section: Section to display
        json_path: Path to processed_papers.json
    
    Returns:
        Exit code (0 success, 1 error)
    """
    if not json_path.exists():
        logger.error(f"❌ File not found: {json_path}")
        logger.info("   Run batch_processor.py first to generate processed data.")
        return 1

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    paper = find_paper(data, partial_name)
    
    if not paper:
        logger.error(f"❌ No paper found matching: '{partial_name}'")
        logger.info("\n   Available papers:")
        for p in data:
            logger.info(f"   - {p.get('filename')}")
        return 1
    
    if paper.get('status') != 'success':
        logger.error(f"❌ Paper processing failed: {paper.get('error_msg')}")
        return 1
    
    display_section(paper, section)
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Inspect extracted sections from processed papers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python inspect_extraction.py HyperDrive
    python inspect_extraction.py --section results FOOL
    python inspect_extraction.py --section abstract "Federated Learning"
        """
    )
    
    parser.add_argument(
        "paper_name",
        type=str,
        help="Partial filename to search for (case-insensitive)"
    )
    
    parser.add_argument(
        "--section", "-s",
        type=str,
        default="methodology",
        choices=["abstract", "introduction", "methodology", "results", "discussion", "references", "other"],
        help="Section to display (default: methodology)"
    )
    
    parser.add_argument(
        "--json", "-j",
        type=str,
        default=str(DEFAULT_JSON),
        help=f"Path to processed_papers.json (default: {DEFAULT_JSON})"
    )
    
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Show full section content (no truncation)"
    )
    
    return parser


def main() -> int:
    """CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Adjust preview length if --full flag is set
    global PREVIEW_CHARS
    if args.full:
        PREVIEW_CHARS = 1_000_000  # Effectively unlimited
    
    return inspect_paper(
        partial_name=args.paper_name,
        section=args.section,
        json_path=Path(args.json)
    )


if __name__ == "__main__":
    sys.exit(main())