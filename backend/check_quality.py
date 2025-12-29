"""
Script: Quality Check
Responsibility: Audit the processed JSON to ensure critical sections 
(Methodology, Results) were successfully extracted from papers.

This script validates the output of batch_processor.py and provides
metrics useful for evaluating the chunking algorithm's effectiveness.

Usage:
    python check_quality.py                    # Check default file
    python check_quality.py path/to/data.json  # Check specific file
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


# Minimum character threshold to consider a section "present"
MIN_SECTION_CHARS = 50

# Minimum methodology detection rate for viable Researcher Mode
MIN_METHODOLOGY_RATE = 0.70


def check_quality(json_path: Path) -> Dict[str, Any]:
    """
    Analyze processed papers JSON for data quality.
    
    Args:
        json_path: Path to the processed_papers.json file.
    
    Returns:
        Dictionary with quality metrics.
    """
    if not json_path.exists():
        logger.error(f"File not found: {json_path}")
        return {"error": "file_not_found"}

    with open(json_path, 'r', encoding='utf-8') as f:
        data: List[Dict] = json.load(f)

    total = len(data)
    if total == 0:
        logger.warning("No papers found in JSON file")
        return {"error": "empty_file"}
    
    # Counters
    success_count = sum(1 for p in data if p.get('status') == 'success')
    has_abstract = 0
    has_methodology = 0
    has_results = 0
    
    # Track problem files
    missing_methodology: List[str] = []
    failed_files: List[Dict[str, str]] = []
    
    for paper in data:
        if paper.get('status') != 'success':
            failed_files.append({
                "filename": paper.get('filename', 'unknown'),
                "error": paper.get('error_msg', 'Unknown error')
            })
            continue
            
        sections = paper.get('sections', {})
        
        # Check sections (with minimum threshold to filter noise)
        if len(sections.get('abstract', '')) > MIN_SECTION_CHARS:
            has_abstract += 1
            
        if len(sections.get('methodology', '')) > MIN_SECTION_CHARS:
            has_methodology += 1
        else:
            missing_methodology.append(paper.get('filename', 'unknown'))
            
        if len(sections.get('results', '')) > MIN_SECTION_CHARS:
            has_results += 1

    # Calculate rates
    methodology_rate = has_methodology / total if total > 0 else 0
    
    # Build report
    report = {
        "total_papers": total,
        "successful": success_count,
        "failed": len(failed_files),
        "sections": {
            "abstract": {"count": has_abstract, "rate": has_abstract / total},
            "methodology": {"count": has_methodology, "rate": methodology_rate},
            "results": {"count": has_results, "rate": has_results / total}
        },
        "missing_methodology": missing_methodology,
        "failed_files": failed_files,
        "viable_for_researcher_mode": methodology_rate >= MIN_METHODOLOGY_RATE
    }
    
    return report


def print_report(report: Dict[str, Any]) -> None:
    """Print a formatted quality report to console."""
    
    if "error" in report:
        logger.error(f"Quality check failed: {report['error']}")
        return
    
    total = report["total_papers"]
    
    print("\n" + "=" * 60)
    print("📊 DATA QUALITY REPORT")
    print("=" * 60)
    
    print(f"\nTotal Papers Processed: {total}")
    print(f"Successfully Parsed:    {report['successful']}/{total}")
    print(f"Failed:                 {report['failed']}/{total}")
    
    print("\n" + "-" * 40)
    print("SECTION DETECTION")
    print("-" * 40)
    
    for section_name, stats in report["sections"].items():
        count = stats["count"]
        rate = stats["rate"] * 100
        status = "✅" if rate >= 70 else "⚠️" if rate >= 50 else "❌"
        print(f"{status} {section_name.capitalize():15} {count:3}/{total} ({rate:.1f}%)")
    
    # Report failed files
    if report["failed_files"]:
        print("\n" + "-" * 40)
        print("FAILED FILES")
        print("-" * 40)
        for f in report["failed_files"]:
            print(f"  ❌ {f['filename']}: {f['error']}")
    
    # Report missing methodology
    if report["missing_methodology"]:
        print("\n" + "-" * 40)
        print("MISSING METHODOLOGY")
        print("-" * 40)
        for filename in report["missing_methodology"]:
            print(f"  ⚠️  {filename}")
    
    # Final verdict
    print("\n" + "=" * 60)
    if report["viable_for_researcher_mode"]:
        print("🚀 SUCCESS: Data quality is high enough for Researcher Mode")
    else:
        print("🚨 WARNING: Methodology detection too low for Researcher Mode")
        print(f"   Current: {report['sections']['methodology']['rate']*100:.1f}%")
        print(f"   Required: {MIN_METHODOLOGY_RATE*100:.0f}%")
        print("   Consider improving keywords in chunking.py")
    print("=" * 60 + "\n")


def main() -> int:
    """CLI entry point."""
    # Get JSON path from argument or use default
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])
    else:
        json_path = Path(__file__).parent / "processed_papers.json"
    
    report = check_quality(json_path)
    print_report(report)
    
    # Return error code if quality is insufficient
    if report.get("viable_for_researcher_mode", False):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())