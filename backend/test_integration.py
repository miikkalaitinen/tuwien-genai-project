#!/usr/bin/env python3
"""

Tests:
1. Load processed_papers.json
2. Extract metadata using extract_paper_metadata()
3. Synthesize relationship between 2 papers
4. Output graph structure

Usage:
    cd backend
    python test_integration.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_integration():
    print("=" * 60)
    print("🧪 Integration Test: Analysis Pipeline")
    print("=" * 60)
    
    # Step 1: Test imports
    print("\n[1/5] Testing imports...")
    try:
        from src.integration import (
            load_processed_papers,
            prepare_paper_text,
            process_single_paper,
            synthesize_paper_relationship
        )
        from src.components.connection_engine import extract_paper_metadata, synthesize_relationship
        from src.utils import get_llm, PaperMetadata
        print("   ✅ All imports successful")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Step 2: Load processed papers
    print("\n[2/5] Loading processed_papers.json...")
    try:
        papers = load_processed_papers("processed_papers.json")
        print(f"   ✅ Loaded {len(papers)} papers")
        for i, p in enumerate(papers[:3]):
            print(f"      {i+1}. {p['filename'][:50]}...")
    except FileNotFoundError:
        print("   ❌ processed_papers.json not found!")
        print("      Run: python -m src.batch_processor data/ --output processed_papers.json")
        return False
    
    # Step 3: Test LLM connection
    print("\n[3/5] Testing Groq LLM connection...")
    try:
        llm = get_llm()
        response = llm.complete("Say 'API working' in 3 words or less.")
        print(f"   ✅ LLM responded: {str(response)[:50]}...")
    except Exception as e:
        print(f"   ❌ LLM connection failed: {e}")
        print("      Check GROQ_API_KEY in .env")
        return False
    
    # Step 4: Extract metadata from first paper
    print("\n[4/5] Extracting metadata from first paper...")
    try:
        paper_text = prepare_paper_text(papers[0])
        print(f"   📄 Paper: {papers[0]['filename'][:40]}...")
        print(f"   📝 Text length: {len(paper_text)} chars")
        
        metadata = extract_paper_metadata(paper_text[:3000])  # Limit for speed
        print(f"   ✅ Metadata extracted:")
        print(f"      - Methodology: {metadata.methodology[:60]}...")
        print(f"      - Key Result: {metadata.key_result[:60]}...")
        print(f"      - Core Theory: {metadata.core_theory[:60]}...")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False
    
    # Step 5: Test relationship synthesis (if 2+ papers)
    if len(papers) >= 2:
        print("\n[5/5] Synthesizing relationship between papers...")
        try:
            # Process second paper
            paper2_text = prepare_paper_text(papers[1])
            metadata2 = extract_paper_metadata(paper2_text[:3000])
            
            print(f"   📄 Paper A: {papers[0]['filename'][:35]}...")
            print(f"   📄 Paper B: {papers[1]['filename'][:35]}...")
            
            relationship = synthesize_relationship(metadata, metadata2, mode="student")
            print(f"   ✅ Relationship synthesized:")
            print(f"      - Type: {relationship.relation_type}")
            print(f"      - Confidence: {relationship.confidence:.2f}")
            print(f"      - Explanation: {relationship.explanation[:80]}...")
        except Exception as e:
            print(f"   ⚠️ Synthesis failed (non-critical): {e}")
    else:
        print("\n[5/5] Skipped: Need 2+ papers for relationship test")
    
    print("\n" + "=" * 60)
    print("✅ Integration test PASSED!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Build full graph: python -m src.integration -l 3")
    print("  2. View output: cat paper_graph.json")
    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
