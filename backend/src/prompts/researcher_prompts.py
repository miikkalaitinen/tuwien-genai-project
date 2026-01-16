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

RESEARCHER_PROMPTS = {
    "system": """You are a Senior Technical Reviewer for a top-tier scientific journal.
    Your goal is to identifying methodological flaws, direct result contradictions, and specific theoretical gaps.
    You do not care about high-level summaries. You focus on the 'how' (methodology) and the exact 'what' (quantitative results).
    Your output must ALWAYS be valid, flat JSON matching the requested schema.""",

    "extraction": """Analyze the paper text below. 
    Extract the critical technical metadata into the following strictly named JSON fields (do not create new keys):

    Input Text:
    {paper_text}

    Instructions for mapping Researcher content to required keys:
    - In "methodology": Describe the specific **Algorithm/Protocol** used AND any stated **Limitations**.
    - In "key_result": State the **Key Quantitative Result** (e.g., 'p<0.05', '95% accuracy') and the Main Claim.
    - In "core_theory": Define the underlying **Mathematical Model** or Architectural Framework.

    Return ONLY valid JSON:
    {{
        "methodology": "Specific protocol and limitations...",
        "key_result": "Quantitative findings...",
        "core_theory": "Theoretical framework..."
    }}""",

    "synthesis": """Compare the technical evidence of these two papers to determine their rigorous academic relationship.

    Paper A:
    - Method/Limits (Methodology): {methodology_a}
    - Quant Results (Key Result): {key_result_a}
    - Framework (Core Theory): {core_theory_a}

    Paper B:
    - Method/Limits (Methodology): {methodology_b}
    - Quant Results (Key Result): {key_result_b}
    - Framework (Core Theory): {core_theory_b}

    Determine the relationship using these strict reviewer rules:
    - "Contradicts": If Paper B explicitly refutes Paper A's claim or reports significantly lower results on the same benchmark.
    - "Supports": If Paper B applies the **same methodology** to validate A, or reproduces A's results (Replication).
    - "Extends": If Paper B proposes a novel improvement, generalization, or theoretical expansion of A.

    Return ONLY valid JSON:
    {{
        "relation_type": "Contradicts" | "Supports" | "Extends",
        "confidence": 0.0 to 1.0,
        "explanation": "State the specific methodological delta or conflict (e.g., 'Paper B refutes A's results on dataset X')"
    }}"""
}