"""

Bridges the PDF ingestion pipeline with the AI engine.
Takes processed_papers.json output and feeds it to extraction/synthesis functions.

Usage:
    from src.integration import process_papers_for_graph, build_paper_graph
    
    # Process all papers from JSON
    metadata_list = process_papers_for_graph("processed_papers.json")
    
    # Build relationship graph
    graph = build_paper_graph(metadata_list, mode="student")
"""

import json
import logging
from pathlib import Path
from typing import Any, Literal

from src.components.connection_engine import extract_paper_metadata, synthesize_relationship
from src.utils import PaperMetadata, RelationshipResult, store_paper_embedding, find_similar_papers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_processed_papers(json_path: str | Path) -> list[dict[str, Any]]:
    """
    Load papers from the processed_papers.json file.
    
    Args:
        json_path: Path to the processed_papers.json file
        
    Returns:
        List of paper dictionaries with filename, metadata, and sections
        
    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed papers file not found: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        papers = json.load(f)
    
    logger.info(f"Loaded {len(papers)} papers from {path}")
    return papers


def prepare_paper_text(paper: dict[str, Any], sections_to_use: list[str] | None = None) -> str:
    """
    Prepare paper text for metadata extraction by combining relevant sections.
    
    Args:
        paper: Paper dictionary from processed_papers.json
        sections_to_use: List of section names to include. 
                        Defaults to ["abstract", "methodology", "results", "introduction"]
    
    Returns:
        Combined text from selected sections
    """
    if sections_to_use is None:
        # Prioritize sections most useful for metadata extraction
        sections_to_use = ["abstract", "methodology", "results", "introduction"]
    
    sections = paper.get("sections", {})
    if not sections:
        return ""

    combined_parts = []
    
    for section_name in sections_to_use:
        content = sections.get(section_name, "")
        if content and content.strip():
            combined_parts.append(f"## {section_name.title()}\n{content}")
    
    if not combined_parts:
        # Fallback: use all available sections if specific ones weren't found
        logger.debug(f"No priority sections found for {paper.get('filename')}. Using all available sections.")
        for name, content in sections.items():
            if content and content.strip():
                combined_parts.append(f"## {name.title()}\n{content}")
    
    return "\n\n".join(combined_parts)


def process_single_paper(
    paper: dict[str, Any],
    store_embedding: bool = False,
    mode: Literal["student", "researcher"] = "student"
) -> dict[str, Any]:
    """
    Process a single paper: extract metadata and optionally store embedding.
    
    Args:
        paper: Paper dictionary from processed_papers.json
        store_embedding: Whether to store the paper in ChromaDB
        mode: Extraction mode ("student" or "researcher")
        
    Returns:
        Dictionary with paper info and extracted metadata:
        {
            "filename": str,
            "file_path": str,
            "metadata": PaperMetadata dict,
            "sections": dict,
            "extraction_success": bool
        }
    """
    filename = paper.get("filename", "Unknown")
    
    # Check for previous pipeline errors
    if paper.get("status") == "error":
        logger.warning(f"Skipping {filename}: Previous step failed ({paper.get('error_msg', 'unknown error')})")
        return {
            "filename": filename,
            "file_path": "",
            "sections": {},
            "extraction_success": False,
            "metadata": None,
            "error": "ingestion_failed"
        }

    logger.info(f"Processing paper: {filename} in {mode} mode")
    
    # Prepare text for extraction - limit to ~4000 chars to stay within Groq free tier (6000 tokens)
    paper_text = prepare_paper_text(paper)
    MAX_TEXT_LENGTH = 4000  # Roughly 1000 tokens
    if len(paper_text) > MAX_TEXT_LENGTH:
        paper_text = paper_text[:MAX_TEXT_LENGTH] + "\n\n[Text truncated for processing...]"
        logger.debug(f"Truncated text from {len(prepare_paper_text(paper))} to {MAX_TEXT_LENGTH} chars")
    
    result = {
        "filename": filename,
        "original_filename": paper.get("original_filename"),
        "file_path": paper.get("metadata", {}).get("file_path", ""),
        "sections": paper.get("sections", {}),
        "extraction_success": False,
        "metadata": None
    }
    
    if not paper_text.strip():
        logger.warning(f"No usable text found for paper: {filename}")
        return result
    
    try:
        # Call extraction function
        extracted = extract_paper_metadata(paper_text, mode=mode)
        
        if extracted:
            result["metadata"] = extracted.model_dump() if hasattr(extracted, "model_dump") else extracted
            result["extraction_success"] = True
            logger.info(f"Successfully extracted metadata for: {filename}")
            
            # Optionally store in vector database
            if store_embedding:
                try:
                    # Prepare metadata for storage (include original filename)
                    storage_metadata = result["metadata"].copy()
                    if paper.get("original_filename"):
                        storage_metadata["original_filename"] = paper.get("original_filename")
                    
                    # Store in mode-specific collection
                    collection_name = f"paper_embeddings_{mode}"
                    store_paper_embedding(
                        paper_id=filename,
                        paper_text=paper_text[:4000],  # Limit text length for embedding
                        metadata=storage_metadata,
                        collection_name=collection_name
                    )
                    logger.info(f"Stored embedding for: {filename} in '{collection_name}'")
                except Exception as e:
                    logger.warning(f"Failed to store embedding for {filename}: {e}")
        else:
            logger.warning(f"Extraction returned empty result for: {filename}")
            
    except Exception as e:
        logger.error(f"Failed to extract metadata for {filename}: {e}")
    
    return result


def process_papers_for_graph(
    json_path: str | Path,
    store_embeddings: bool = False,
    limit: int | None = None,
    mode: Literal["student", "researcher"] = "student"
) -> list[dict[str, Any]]:
    """
    Process all papers from processed_papers.json for graph building.
    
    Args:
        json_path: Path to processed_papers.json
        store_embeddings: Whether to store papers in ChromaDB
        limit: Optional limit on number of papers to process
        mode: "student" or "researcher"
        
    Returns:
        List of processed paper dictionaries with extracted metadata
    """
    papers = load_processed_papers(json_path)
    
    if limit:
        papers = papers[:limit]
    
    processed = []
    for paper in papers:
        result = process_single_paper(paper, store_embedding=store_embeddings, mode=mode)
        processed.append(result)
    
    successful = sum(1 for p in processed if p["extraction_success"])
    logger.info(f"Processed {len(processed)} papers, {successful} successful extractions")
    
    return processed


def synthesize_paper_relationship(
    paper_a: dict[str, Any],
    paper_b: dict[str, Any],
    mode: Literal["student", "researcher"] = "student"
) -> dict[str, Any] | None:
    """
    Synthesize the relationship between two papers.
    
    Args:
        paper_a: First paper with extracted metadata
        paper_b: Second paper with extracted metadata
        mode: "student" or "researcher" mode
        
    Returns:
        Relationship dictionary or None if synthesis fails:
        {
            "source": str,  # paper_a filename
            "target": str,  # paper_b filename
            "relation_type": "Supports" | "Contradicts" | "Extends",
            "confidence": float,
            "explanation": str
        }
    """
    # Check both papers have metadata
    meta_a = paper_a.get("metadata")
    meta_b = paper_b.get("metadata")
    
    if not meta_a or not meta_b:
        logger.warning("Cannot synthesize relationship: missing metadata")
        return None
    
    try:
        # Call synthesis function
        relationship = synthesize_relationship(meta_a, meta_b, mode=mode)
        
        if relationship:
            return {
                "source": paper_a.get("filename", "Unknown"),
                "target": paper_b.get("filename", "Unknown"),
                "relation_type": relationship.relation_type if hasattr(relationship, "relation_type") else relationship.get("relation_type"),
                "confidence": relationship.confidence if hasattr(relationship, "confidence") else relationship.get("confidence"),
                "explanation": relationship.explanation if hasattr(relationship, "explanation") else relationship.get("explanation", "")
            }
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
    
    return None


def build_paper_graph(
    processed_papers: list[dict[str, Any]],
    mode: Literal["student", "researcher"] = "student",
    confidence_threshold: float = 0.5,
    use_similar_papers: bool = False
) -> dict[str, Any]:
    """
    Build a graph of paper relationships.
    
    Args:
        processed_papers: List of papers with extracted metadata
        mode: "student" or "researcher" mode
        confidence_threshold: Minimum confidence to include an edge
        use_similar_papers: If True, only compare similar papers via ChromaDB
        
    Returns:
        Graph dictionary suitable for React Flow visualization:
        {
            "nodes": [{"id": str, "data": {...}}],
            "edges": [{"source": str, "target": str, "data": {...}}]
        }
    """
    # Filter papers with successful extraction
    valid_papers = [p for p in processed_papers if p["extraction_success"]]
    
    if len(valid_papers) < 2:
        logger.warning("Need at least 2 papers with metadata to build graph")
        return {"nodes": [], "edges": []}
    
    # Build nodes
    nodes = []
    for paper in valid_papers:
        # Use original filename for display label if available
        label = paper.get("original_filename") or paper["filename"].replace(".pdf", "")

        nodes.append({
            "id": paper["filename"],
            "data": {
                "label": label,
                "metadata": paper["metadata"],
                "file_path": paper["file_path"]
            }
        })
    
    # Build edges by comparing paper pairs
    edges = []
    
    if use_similar_papers:
        # Use ChromaDB to find similar papers (more efficient for large datasets)
        collection_name = f"paper_embeddings_{mode}"
        for paper in valid_papers:
            try:
                # Use paper text (from metadata or section) for query, or filename as fallback
                # Ideally we should use the abstract
                query_text = paper.get("metadata", {}).get("key_result", "") or paper["filename"]
                
                similar = find_similar_papers(
                    query_text=query_text,
                    n_results=5,
                    collection_name=collection_name
                )
                # Compare only with similar papers
                for sim_item in similar:
                    sim_id = sim_item.get("id")
                    sim_paper = next((p for p in valid_papers if p["filename"] == sim_id), None)
                    if sim_paper and sim_paper["filename"] != paper["filename"]:
                        rel = synthesize_paper_relationship(paper, sim_paper, mode=mode)
                        if rel and rel["confidence"] >= confidence_threshold:
                            edges.append({
                                "id": f"{rel['source']}->{rel['target']}",
                                "source": rel["source"],
                                "target": rel["target"],
                                "data": {
                                    "relation_type": rel["relation_type"],
                                    "confidence": rel["confidence"],
                                    "explanation": rel["explanation"]
                                }
                            })
            except Exception as e:
                logger.warning(f"Similar paper search failed for {paper['filename']}: {e}")
    else:
        # Compare all pairs (O(n²) - use for small datasets)
        for i, paper_a in enumerate(valid_papers):
            for paper_b in valid_papers[i+1:]:
                rel = synthesize_paper_relationship(paper_a, paper_b, mode=mode)
                if rel and rel["confidence"] >= confidence_threshold:
                    edges.append({
                        "id": f"{rel['source']}->{rel['target']}",
                        "source": rel["source"],
                        "target": rel["target"],
                        "data": {
                            "relation_type": rel["relation_type"],
                            "confidence": rel["confidence"],
                            "explanation": rel["explanation"]
                        }
                    })
    
    logger.info(f"Built graph with {len(nodes)} nodes and {len(edges)} edges")
    return {"nodes": nodes, "edges": edges}


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration: Process papers and build relationship graph")
    parser.add_argument(
        "--input", "-i",
        default="processed_papers.json",
        help="Path to processed_papers.json file"
    )
    parser.add_argument(
        "--output", "-o",
        default="paper_graph.json",
        help="Output path for the graph JSON"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["student", "researcher"],
        default="student",
        help="Relationship synthesis mode (default: student)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of papers to process"
    )
    parser.add_argument(
        "--confidence", "-c",
        type=float,
        default=0.5,
        help="Minimum confidence threshold for edges (default: 0.5)"
    )
    parser.add_argument(
        "--store-embeddings",
        action="store_true",
        help="Store paper embeddings in ChromaDB"
    )
    
    args = parser.parse_args()
    
    print(f"🔗 Integration Pipeline")
    print(f"   Input:  {args.input}")
    print(f"   Mode:   {args.mode} (for relationship synthesis)")
    print(f"   Limit:  {args.limit or 'all papers'}")
    
    # Process papers (extraction uses specified mode prompts)
    processed = process_papers_for_graph(
        json_path=args.input,
        store_embeddings=args.store_embeddings,
        limit=args.limit,
        mode=args.mode
    )
    
    # Build graph
    graph = build_paper_graph(
        processed_papers=processed,
        mode=args.mode,
        confidence_threshold=args.confidence
    )
    
    # Save graph
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    
    print(f"\n✅ Graph saved to: {output_path}")
    print(f"   Nodes: {len(graph['nodes'])}")
    print(f"   Edges: {len(graph['edges'])}")
