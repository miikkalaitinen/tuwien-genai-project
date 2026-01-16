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
    "system": """
You are a Senior Technical Reviewer for a top-tier scientific journal. 
Your goal is to critically analyze research papers to identify:
1. Methodological flaws or conflicts.
2. Direct contradictions in results compared to prior work.
3. Incremental theoretical extensions.
4. Specific gaps in the current state-of-the-art.

You do not care about high-level summaries. You care about the "how" (methodology) and the exact "what" (quantitative results).
You must remain objective and skeptical. Never invent connections that are not explicitly supported by the text.
""",

    "extraction": """
Analyze the provided text sections of the research paper (Abstract, Methodology, Results, Discussion).
Extract the following critical metadata into a strictly valid JSON object.

Input Text:
{paper_text}

Instructions:
1. Identify the specific **Methodology** used (e.g., "Transformer architecture," "Double-blind randomized control trial").
2. Extract the **Key Quantitative Result** (e.g., "Achieved 95% accuracy," "p-value < 0.05").
3. Identify the **Main Claim** or hypothesis.
4. List any explicitly stated **Limitations**.

Output Format (JSON only):
{{
    "methodology_type": "string",
    "key_result_quantitative": "string",
    "main_claim": "string",
    "limitations": "string"
}}
""",

    "synthesis": """
You are provided with the extracted metadata and key sections from two different research papers: Paper A and Paper B.
Your task is to determine the precise academic relationship between them based *only* on the provided evidence.

Paper A Metadata:
{paper_a_data}

Paper B Metadata:
{paper_b_data}

Determine which of the following relationships best describes how Paper B relates to Paper A:
- "Contradicts results of": Paper B presents evidence that refutes Paper A's claim.
- "Uses same methodology as": Paper B applies the exact same method (e.g., specific algorithm or lab protocol) as Paper A.
- "Extends theory of": Paper B builds directly upon the theoretical framework established in Paper A.
- "None": No significant critical relationship found.

**Constraint**: You must provide a "reasoning_trace" citing specific differences in methodology or results before selecting the relationship.

Output Format (JSON only):
{{
    "reasoning_trace": "Compare Method A vs Method B and Result A vs Result B...",
    "relationship_type": "Contradicts results of | Uses same methodology as | Extends theory of | None",
    "confidence_score": 0.0 to 1.0
}}
"""
}
