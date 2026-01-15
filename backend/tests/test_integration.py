# backend/tests/test_integration.py
"""
Integration Test for analysis pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.components import (
    PDFIngestor,
    SemanticChunker,
    extract_paper_metadata,
    synthesize_relationship,
)


def test_full_pipeline():
    """Test completo: 2 PDFs → extracción → comparación."""
    
    print("=" * 60)
    print("🧪 Integration Test: Full Analysis Pipeline")
    print("=" * 60)
    
    # Find available PDFs
    data_dir = Path(__file__).parent.parent / "data"
    pdfs = list(data_dir.glob("*.pdf"))
    
    if len(pdfs) < 2:
        print(f"❌ Need at least 2 PDFs in {data_dir}")
        print(f"   Found: {len(pdfs)}")
        return
    
    pdf_a = pdfs[0]
    pdf_b = pdfs[1]
    
    print(f"\n📄 Paper A: {pdf_a.name}")
    print(f"📄 Paper B: {pdf_b.name}")
    
    print("\n" + "=" * 60)
    print("📥 STEP 1: Processing PDF")
    print("=" * 60)
    
    chunker = SemanticChunker()
    
    print(f"\n🔄 Processing: {pdf_a.name}...")
    try:
        ingestor_a = PDFIngestor(str(pdf_a))
        markdown_a = ingestor_a.extract_clean_text()
        chunks_a = chunker.split_by_section(markdown_a)
        print(f"   ✅ Sections extracted: {list(chunks_a.keys())}")
    except Exception as e:
        print(f"   ❌ Error processing Paper A: {e}")
        return
    
    print(f"\n🔄 Processing: {pdf_b.name}...")
    try:
        ingestor_b = PDFIngestor(str(pdf_b))
        markdown_b = ingestor_b.extract_clean_text()
        chunks_b = chunker.split_by_section(markdown_b)
        print(f"   ✅ Sections extracted: {list(chunks_b.keys())}")
    except Exception as e:
        print(f"   ❌ Error processing Paper B: {e}")
        return

    print("\n" + "=" * 60)
    print("🧠 STEP 2: Extracting Metadata")
    print("=" * 60)
    
    def prepare_text_for_llm(chunks: dict) -> str:
        """Combine most relevant sections for analysis."""
        sections = ["abstract", "methodology", "results", "introduction"]
        text_parts = []
        for section in sections:
            if section in chunks and chunks[section].strip():
                content = chunks[section][:2000]
                text_parts.append(f"[{section.upper()}]\n{content}")
        return "\n\n".join(text_parts) if text_parts else str(chunks)
    
    text_a = prepare_text_for_llm(chunks_a)
    text_b = prepare_text_for_llm(chunks_b)
    
    print(f"\n🔍 Extracting metadata from Paper A...")
    try:
        meta_a = extract_paper_metadata(text_a)
        print(f"   ✅ Methodology: {meta_a.methodology[:80]}...")
        print(f"   ✅ Key Result: {meta_a.key_result[:80]}...")
        print(f"   ✅ Core Theory: {meta_a.core_theory[:80]}...")
    except Exception as e:
        print(f"   ❌ Error extracting metadata A: {e}")
        return
    
    print(f"\n🔍 Extracting metadata from Paper B...")
    try:
        meta_b = extract_paper_metadata(text_b)
        print(f"   ✅ Methodology: {meta_b.methodology[:80]}...")
        print(f"   ✅ Key Result: {meta_b.key_result[:80]}...")
        print(f"   ✅ Core Theory: {meta_b.core_theory[:80]}...")
    except Exception as e:
        print(f"   ❌ Error extracting metadata B: {e}")
        return
    
    # =========================================================================
    # STEP 3: Synthesize Relationship
    # =========================================================================
    print("\n" + "=" * 60)
    print("🔗 STEP 3: Analyzing Relationship")
    print("=" * 60)
    
    for mode in ["researcher", "student"]:
        print(f"\n🎯 Mode: {mode.upper()}")
        try:
            result = synthesize_relationship(meta_a, meta_b, mode=mode)
            print(f"   📊 Relation: {result.relation_type}")
            print(f"   📈 Confidence: {result.confidence:.0%}")
            print(f"   💬 Explanation: {result.explanation}")
        except Exception as e:
            print(f"   ❌ Error in synthesis ({mode}): {e}")
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_full_pipeline()
