"""
Module: Semantic Chunking (Waterfall/Sticky Logic Edition)
Responsibility: Split Markdown text into broad academic categories.

Logic (Waterfall/Sticky):
1. Detect explicit section starts via keyword matching (e.g., "Methodology").
2. If a generic header appears (e.g., "A. Compression"), APPEND it to the 
   CURRENT section - do not reset to 'other' just because the header lacks keywords.
3. Only transition to a new section when a strong keyword is detected.

"""

import logging
import re
from typing import Dict, List, Tuple

# Configure module-level logger
logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Splits academic paper Markdown into semantic sections.
    
    Uses a "waterfall" or "sticky" logic where once a section category
    is detected (e.g., Methodology), all subsequent content remains in
    that category until a new explicit section keyword is found.
    
    This approach prevents technical subsections (like "A. Overview" or
    "B. Implementation Details") from being incorrectly classified as
    'other' when they clearly belong to the parent section.
    
    Attributes:
        target_sections: Mapping of section categories to their trigger keywords.
        section_priority: Ordered list for resolving ambiguous headers.
    
    Example:
        >>> chunker = SemanticChunker()
        >>> sections = chunker.split_by_section(markdown_text)
        >>> print(sections.keys())
        dict_keys(['abstract', 'introduction', 'methodology', 'results', 'discussion', 'references', 'other'])
    """
    
    # Section transition keywords ordered by typical paper structure
    # This ordering helps resolve ambiguous headers
    SECTION_ORDER: List[str] = [
        "abstract",
        "introduction", 
        "methodology",
        "results",
        "discussion",
        "references"
    ]
    
    def __init__(self) -> None:
        """Initialize the chunker with section keyword mappings."""
        
        # Keyword mapping: category -> list of trigger words
        # These are matched case-insensitively against header text
        #
        # IMPORTANT: "evaluation", "experiment", "performance" are placed in 
        # results to ensure proper separation from methodology.
        # The order of checking matters - results keywords are checked with
        # higher priority than methodology keywords.
        self.target_sections: Dict[str, List[str]] = {
            "abstract": [
                "abstract", 
                "summary"
            ],
            "introduction": [
                "introduction", 
                "motivation", 
                "background", 
                "related work", 
                "problem statement",
                "overview"  # Only at document start
            ],
            # Results/Evaluation keywords - checked BEFORE methodology
            # to catch "Evaluation" sections that might otherwise stick to methodology
            "results": [
                "result",
                "evaluation",      # CRITICAL: Must be in results, not methodology
                "experiment",      # CRITICAL: Experiments = Results
                "performance",
                "analysis",
                "ablation",
                "numerical",
                "comparison",
                "benchmark",
                "testing",
                "validation results",
                "empirical"
            ],
            # Methodology keywords
            "methodology": [
                "methodology",
                "method",
                "approach", 
                "system",
                "architecture",
                "design",
                "proposed",
                "implementation",
                "model",
                "framework",
                "setup",           # Can be ambiguous - context matters
                "algorithm",
                "technique",
                "pipeline"
            ],
            "discussion": [
                "discussion",
                "conclusion",
                "future work",
                "concluding",
                "limitation",
                "threat"           # "Threats to validity"
            ],
            "references": [
                "reference",
                "bibliography",
                "works cited"
            ]
        }
        
        logger.debug("SemanticChunker initialized with waterfall logic")

    def _classify_header(self, header_text: str, current_category: str) -> str:
        """
        Determine the section category for a header.
        
        Uses priority-based matching where results/evaluation keywords
        are checked before methodology to prevent evaluation sections
        from being absorbed into methodology.
        
        Args:
            header_text: The header text to classify (will be lowercased).
            current_category: The current active category (for sticky logic).
        
        Returns:
            The detected category, or current_category if no keywords match.
        """
        title_lower = header_text.lower()
        
        # Priority order: Check results BEFORE methodology to catch "Evaluation"
        # This prevents the common edge case where "Evaluation" gets merged into methodology
        priority_order = [
            "references",    # Check first - clear boundary
            "discussion",    # Check before results
            "results",       # CHECK BEFORE METHODOLOGY - critical for evaluation
            "abstract",      
            "introduction",
            "methodology",   # Check last among content sections
        ]
        
        for category in priority_order:
            keywords = self.target_sections.get(category, [])
            if any(keyword in title_lower for keyword in keywords):
                logger.debug(f"Header '{header_text}' matched category: {category}")
                return category
        
        # No match - stick to current category (waterfall logic)
        return current_category

    def split_by_section(self, text: str) -> Dict[str, str]:
        """
        Split Markdown text into semantic sections using waterfall logic.
        
        The algorithm:
        1. Extract any pre-header content as abstract
        2. Parse all Markdown headers (# through ######)
        3. For each header, check if it triggers a new section
        4. If no trigger found, content stays in current section (sticky)
        5. Append header + content to the active section
        
        Args:
            text: Full Markdown text of the academic paper.
        
        Returns:
            Dictionary mapping section names to their content.
            Keys: abstract, introduction, methodology, results, 
                  discussion, references, other
        """
        # Initialize all section containers
        sections: Dict[str, str] = {key: "" for key in self.target_sections.keys()}
        sections["other"] = ""
        
        # Regex: Capture ANY level of Markdown header (#, ##, ###...)
        # Groups: (1) hash marks, (2) header title, followed by content until next header
        header_pattern = r'\n(#{1,6})\s+(.*?)\n'
        chunks = re.split(header_pattern, text)
        
        # --- 1. Handle Pre-Header Content (Usually Abstract) ---
        if chunks and len(chunks[0].strip()) > 0:
            preamble = chunks[0].strip()
            # Substantial pre-header text is typically the abstract
            if len(preamble) > 50:
                sections["abstract"] += preamble
                logger.debug(f"Captured preamble as abstract: {len(preamble)} chars")
        
        # --- 2. Initialize Waterfall State ---
        # Default starting category - generic early headers go here
        current_category: str = "introduction"
        
        # Track section transitions for logging
        transitions: List[Tuple[str, str]] = []
        
        # --- 3. Process Headers and Content ---
        # Chunks come in triplets: (hash_marks, title, content)
        for i in range(1, len(chunks), 3):
            if i + 2 >= len(chunks):
                break
            
            header_hashes: str = chunks[i]      # e.g., "##"
            header_title: str = chunks[i + 1]   # e.g., "A. Compression Flow"
            content: str = chunks[i + 2]        # Content after header
            
            # Classify this header
            new_category = self._classify_header(header_title, current_category)
            
            # Log transitions for debugging
            if new_category != current_category:
                transitions.append((header_title, new_category))
                logger.debug(f"Section transition: {current_category} -> {new_category} at '{header_title}'")
                current_category = new_category
            
            # Handle edge case: still in abstract when generic header appears
            if current_category == "abstract" and not any(
                kw in header_title.lower() for kw in self.target_sections["abstract"]
            ):
                current_category = "introduction"
            
            # Append full block (header + content) to active section
            full_block = f"\n{header_hashes} {header_title}\n{content}"
            sections[current_category] += full_block
        
        # Log summary
        non_empty = {k: len(v) for k, v in sections.items() if v.strip()}
        logger.info(f"Chunking complete. Sections: {non_empty}")
        
        return sections
    
    def get_section_summary(self, sections: Dict[str, str]) -> Dict[str, int]:
        """
        Get character counts for each section.
        
        Useful for quality checks and debugging.
        
        Args:
            sections: Dictionary from split_by_section()
        
        Returns:
            Dictionary mapping section names to character counts.
        """
        return {name: len(content) for name, content in sections.items()}