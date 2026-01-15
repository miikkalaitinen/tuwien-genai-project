"""
Module: Researcher Mode Prompts

TODO for Aarne:
- Design System Prompts for Researcher perspective
- Focus on: methodology conflicts, research gaps, state-of-the-art
- Output relations: "Contradicts", "Uses same methodology as", "Extends theory of"
- Test with Golden Set of 3-5 papers with known relationships

Available sections from chunking pipeline:
- abstract, introduction, methodology, results, discussion, references
"""

from typing import Dict

RESEARCHER_PROMPTS: Dict[str, str] = {
    "system": "",
    "extraction": "",
    "synthesis": "",
}
