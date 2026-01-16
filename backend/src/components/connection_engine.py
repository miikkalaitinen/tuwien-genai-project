"""
Module: Connection Engine

Provides:
- extract_paper_metadata(): Extract structured metadata from paper text using LLM
- synthesize_relationship(): Compare two papers and determine their relationship

Uses Pydantic models for strict JSON output validation.
Supports Student and Researcher modes with different system prompts.
"""

import json
from typing import Literal

from pydantic import ValidationError

# Import utilities and schemas
from src.utils import (
    get_llm,
    PaperMetadata,
    RelationshipResult,
    retry_with_backoff,
)

# Import prompts
from src.prompts.student_prompts import STUDENT_PROMPTS
from src.prompts.researcher_prompts import RESEARCHER_PROMPTS


# =============================================================================
# Fallback Prompts
# =============================================================================

_FALLBACK_EXTRACTION_PROMPT = """You are an expert academic researcher analyzing scientific papers.
Extract the following information from the paper text and return ONLY valid JSON:

{
    "methodology": "The main research methodology used",
    "key_result": "The primary finding or contribution",
    "core_theory": "The underlying theoretical framework"
}

Be concise but precise. Each field should be 1-2 sentences maximum."""

_FALLBACK_STUDENT_SYSTEM_PROMPT = """You are a helpful academic assistant explaining research to students.
Focus on:
- Clear, accessible explanations
- How concepts build on each other
- Foundational relationships between papers
Use simple language and avoid jargon when possible."""

_FALLBACK_RESEARCHER_SYSTEM_PROMPT = """You are an expert research analyst for academic scholars.
Focus on:
- Methodological comparisons and conflicts
- Research gaps and extensions
- State-of-the-art positioning
Provide technical, nuanced analysis."""

_FALLBACK_SYNTHESIS_PROMPT = """Compare these two research papers and determine their relationship.

Paper A:
- Methodology: {methodology_a}
- Key Result: {key_result_a}
- Core Theory: {core_theory_a}

Paper B:
- Methodology: {methodology_b}
- Key Result: {key_result_b}
- Core Theory: {core_theory_b}

Determine if Paper B:
- "Contradicts" Paper A (conflicting results or opposing theories)
- "Supports" Paper A (confirms findings or validates approach)
- "Extends" Paper A (builds upon, improves, or generalizes)

Return ONLY valid JSON:
{{
    "relation_type": "Contradicts" | "Supports" | "Extends",
    "confidence": 0.0 to 1.0,
    "explanation": "Brief justification"
}}"""


# =============================================================================
# Helper Functions
# =============================================================================

def _get_prompt(prompt_dict: dict, key: str, fallback: str) -> str:
    """Get prompt from dict, using fallback if empty."""
    prompt = prompt_dict.get(key, "")
    return prompt if prompt.strip() else fallback


def _parse_json_from_response(response_text: str) -> dict:
    """
    Extract and parse JSON from LLM response.
    
    Handles cases where the LLM wraps JSON in markdown code blocks.
    """
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()
    
    return json.loads(text)


# =============================================================================
# Main Functions
# =============================================================================

def extract_paper_metadata(paper_text: str, mode: Literal["student", "researcher"] = "student") -> PaperMetadata:
    """
    Extract structured metadata from paper text using LLM.
    
    Extracts:
    - methodology: The research approach used
    - key_result: The main finding or contribution
    - core_theory: The underlying theoretical framework
    
    Args:
        paper_text: Full text or relevant sections of a research paper
        mode: Extraction mode ("student" or "researcher") linked to specific prompt sets
    
    Returns:
        PaperMetadata: Validated Pydantic model with extracted fields
        
    Raises:
        ValidationError: If LLM output doesn't match expected schema
        json.JSONDecodeError: If LLM output is not valid JSON
    """
    llm = get_llm()
    
    # Select prompts based on mode
    if mode == "student":
        prompts = STUDENT_PROMPTS
        fallback_prompt = _FALLBACK_EXTRACTION_PROMPT
    else:
        prompts = RESEARCHER_PROMPTS
        fallback_prompt = _FALLBACK_EXTRACTION_PROMPT

    # Get extraction prompt
    extraction_prompt = _get_prompt(
        prompts,
        "extraction",
        fallback_prompt
    )
    
    # Construct the full prompt
    full_prompt = f"""{extraction_prompt}\n\nPaper text:\n\"\"\"{paper_text}\n\"\"\"\n\nReturn ONLY the JSON object, no other text."""
    
    # Call the LLM with retry for rate limits
    def _call_llm():
        return llm.complete(full_prompt)
    
    response = retry_with_backoff(_call_llm)
    response_text = str(response)
    
    # Parse and validate the response (handling None values)
    parsed_data = _parse_json_from_response(response_text)
    metadata = PaperMetadata.from_dict(parsed_data)
    
    return metadata


def synthesize_relationship(
    paper_a_metadata: PaperMetadata | dict,
    paper_b_metadata: PaperMetadata | dict,
    mode: Literal["student", "researcher"] = "researcher"
) -> RelationshipResult:
    """
    Compare two papers and determine their relationship.
    
    Analyzes the metadata of two papers and classifies their relationship
    as one of: "Contradicts", "Supports", or "Extends".
    
    Uses different system prompts based on the mode:
    - Student mode: Focus on foundational/hierarchical relationships
    - Researcher mode: Focus on methodological conflicts and extensions
    
    Args:
        paper_a_metadata: Metadata of the first paper (PaperMetadata or dict)
        paper_b_metadata: Metadata of the second paper (PaperMetadata or dict)
        mode: Either "student" or "researcher" for different analysis styles
        
    Returns:
        RelationshipResult: Validated result with relation_type, confidence, explanation
        
    Raises:
        ValidationError: If LLM output doesn't match expected schema
        json.JSONDecodeError: If LLM output is not valid JSON
    """
    llm = get_llm()
    
    # Convert to dict if PaperMetadata instance
    if isinstance(paper_a_metadata, PaperMetadata):
        paper_a_dict = paper_a_metadata.model_dump()
    else:
        paper_a_dict = paper_a_metadata
        
    if isinstance(paper_b_metadata, PaperMetadata):
        paper_b_dict = paper_b_metadata.model_dump()
    else:
        paper_b_dict = paper_b_metadata
    
    # Select prompts based on mode
    if mode == "student":
        prompts = STUDENT_PROMPTS
        fallback_system = _FALLBACK_STUDENT_SYSTEM_PROMPT
    else:
        prompts = RESEARCHER_PROMPTS
        fallback_system = _FALLBACK_RESEARCHER_SYSTEM_PROMPT
    
    # Get system prompt
    system_prompt = _get_prompt(prompts, "system", fallback_system)
    
    # Get synthesis prompt
    synthesis_prompt = _get_prompt(
        prompts,
        "synthesis",
        _FALLBACK_SYNTHESIS_PROMPT
    )
    
    # Format the synthesis prompt with paper data
    formatted_synthesis = synthesis_prompt.format(
        methodology_a=paper_a_dict.get("methodology", "Unknown"),
        key_result_a=paper_a_dict.get("key_result", "Unknown"),
        core_theory_a=paper_a_dict.get("core_theory", "Unknown"),
        methodology_b=paper_b_dict.get("methodology", "Unknown"),
        key_result_b=paper_b_dict.get("key_result", "Unknown"),
        core_theory_b=paper_b_dict.get("core_theory", "Unknown"),
    )
    
    # Construct the full prompt with system context
    full_prompt = f"""{system_prompt}

{formatted_synthesis}

Return ONLY the JSON object, no other text."""
    
    def _call_llm():
        return llm.complete(full_prompt)
    
    response = retry_with_backoff(_call_llm, 5, 5, 60)
    response_text = str(response)
    
    # Parse and validate the response
    parsed_data = _parse_json_from_response(response_text)
    result = RelationshipResult(**parsed_data)
    
    return result


# =============================================================================
# Batch Processing Helpers
# =============================================================================

def extract_metadata_safe(paper_text: str, mode: Literal["student", "researcher"] = "student") -> PaperMetadata | None:
    """
    Safe wrapper for extract_paper_metadata that returns None on failure.
    
    Useful for batch processing where some papers might fail.
    """
    try:
        return extract_paper_metadata(paper_text, mode=mode)
    except (ValidationError, json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to extract metadata: {e}")
        return None


def synthesize_relationship_safe(
    paper_a_metadata: PaperMetadata | dict,
    paper_b_metadata: PaperMetadata | dict,
    mode: Literal["student", "researcher"] = "researcher"
) -> RelationshipResult | None:
    """
    Safe wrapper for synthesize_relationship that returns None on failure.
    
    Useful for batch processing where some comparisons might fail.
    """
    try:
        return synthesize_relationship(paper_a_metadata, paper_b_metadata, mode)
    except (ValidationError, json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to synthesize relationship: {e}")
        return None
