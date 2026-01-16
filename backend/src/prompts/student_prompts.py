"""
Module: Student Mode Prompts

TODO for Aarne:
- Design System Prompts for Student perspective
- Focus on: hierarchical relationships, foundational concepts
- Output relations: "Defines X", "Introduction to Y", "Example of Z"
- Test with Golden Set of 3-5 papers with known relationships

Available sections from chunking pipeline:
- abstract, introduction, methodology, results, discussion, references
"""

from typing import Dict

STUDENT_PROMPTS = {
    "system": """You are an expert Academic Tutor. Your goal is to help a student with basic field knowledge connect complex ideas.
    You do NOT give generic study advice. You explain the *logic* of how papers relate.
    
    Your focus is "Conceptual Bridging":
    1. Connect Abstract to Concrete (How does Theory A look in Practice B?).
    2. Connect General to Specific (How does Broad Concept A apply to Specific Problem B?).
    3. Connect Complexity to Simplicity (How does B make A easier to grasp?).

    Your output must ALWAYS be valid, flat JSON matching the requested schema.""",

    "extraction": """Analyze the paper text below. 
    Extract the educational content into the following strictly named JSON fields.

    Input Text:
    {paper_text}

    Instructions for mapping Student content to required keys:
    - In "methodology": Describe the **Practical Application** or **Context**. (e.g., "Used in autonomous driving systems").
    - In "key_result": Write the **"Bottom Line" Summary**. What is the core insight without the math?
    - In "core_theory": List the **Key Concepts** discussed (e.g., "Neural Networks", "Game Theory").

    Return ONLY valid JSON:
    {{
        "methodology": "Context/Application...",
        "key_result": "The core insight is...",
        "core_theory": "Key concepts: [Concept A, Concept B]..."
    }}""",

    "synthesis": """Compare the educational content of these two papers to explain their logical connection.

    Paper A:
    - Context (Methodology): {methodology_a}
    - Insight (Key Result): {key_result_a}
    - Concepts (Core Theory): {core_theory_a}

    Paper B:
    - Context (Methodology): {methodology_b}
    - Insight (Key Result): {key_result_b}
    - Concepts (Core Theory): {core_theory_b}

    Determine the relationship using these specific bridging rules:
    - "Supports": Paper B explains the *background* or *foundational definition* of a concept used in Paper A.
    - "Extends": Paper B takes the *theory* from Paper A and demonstrates it in a *specific real-world scenario*.
    - "Contradicts": Paper B clarifies a *nuance* or *exception* to the rule established in Paper A.

    **CRITICAL**: The 'explanation' must be a "Conceptual Bridge".
    BAD: "Paper B is a study guide for A."
    BAD: "Paper B extends A."
    GOOD: "Paper B takes the 'Optimization' theory from Paper A and applies it to 'Traffic Control', showing how the math works in real cities."

    Return ONLY valid JSON:
    {{
        "relation_type": "Contradicts" | "Supports" | "Extends",
        "confidence": 0.0 to 1.0,
        "explanation": "Explain the connection: [Concept in A] -> [Transformation] -> [Result in B]."
    }}"""
}