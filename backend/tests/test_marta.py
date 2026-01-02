# backend/tests/test_marta.py
"""
Unit Test: Marta's Connection Engine

Tests extract_paper_metadata() and synthesize_relationship() with mock data.
"""

from dotenv import load_dotenv
from src.components.connection_engine import extract_paper_metadata, synthesize_relationship

load_dotenv()


def test_connection_engine():
    print("🧪 UNIT TEST: Connection Engine")
    print("=" * 50)
    
    # Mock paper data (simulates Jaime's pipeline output)
    paper_a_text = """
    Title: Deep Learning in Medicine
    Abstract: We propose a new Transformer model called MedBERT to diagnose cancer.
    Methodology: We trained on 50,000 X-ray images using PyTorch.
    Results: We achieved 95% accuracy, beating previous CNN models.
    """
    
    paper_b_text = """
    Title: Limitations of Transformers
    Abstract: We analyze the energy consumption of large models.
    Methodology: We measured GPU usage of MedBERT and other models.
    Results: MedBERT consumes 500% more energy than CNNs for only 1% gain in accuracy.
    """

    # Test 1: Extract metadata
    print("\n🔍 Test 1: Extracting metadata from Paper A...")
    try:
        meta_a = extract_paper_metadata(paper_a_text)
        print(f"   ✅ Methodology: {meta_a.methodology[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    print("\n🔍 Test 2: Extracting metadata from Paper B...")
    meta_b = extract_paper_metadata(paper_b_text)

    # Test 2: Synthesize relationship
    print("\n🤝 Test 3: Finding relationship (Researcher mode)...")
    try:
        result = synthesize_relationship(meta_a, meta_b, mode="researcher")
        print("-" * 50)
        print(f"TYPE: {result.relation_type}")
        print(f"CONFIDENCE: {result.confidence}")
        print(f"EXPLANATION: {result.explanation}")
        print("-" * 50)
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Unit test completed")


if __name__ == "__main__":
    test_connection_engine()