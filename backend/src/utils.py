"""
Module: Utilities
Owner: Marta (AI Backend Architect)

Provides:
- LLM client via LlamaIndex (Groq primary, Gemini fallback)
- ChromaDB persistent vector store for embeddings
- Pydantic schemas for strict JSON output
- Retry logic for rate limit handling
- RAG functions for storing and retrieving papers

Usage:
    from src.utils import get_llm, PaperMetadata, RelationshipResult
    from src.utils import store_paper_embedding, find_similar_papers
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LlamaIndex imports
from llama_index.core import Settings
from llama_index.core.llms import LLM

# ChromaDB imports
import chromadb
from chromadb.config import Settings as ChromaSettings

# Load environment variables
load_dotenv()

# =============================================================================
# Path Constants
# =============================================================================
BACKEND_ROOT = Path(__file__).parent.parent
DATA_DIR = BACKEND_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR = BACKEND_ROOT / "chroma_db"
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)


job_store: Dict[str, Dict[str, Any]] = {}

# =============================================================================
# Pydantic Schemas for Strict JSON Output
# =============================================================================

class PaperMetadata(BaseModel):
    """Schema for extracted paper metadata with defaults for robustness."""
    methodology: str = Field(
        default="Not specified", 
        description="The main research methodology used (e.g., 'experimental study', 'meta-analysis', 'simulation')"
    )
    key_result: str = Field(
        default="Not specified", 
        description="The primary finding or contribution of the paper"
    )
    core_theory: str = Field(
        default="Not specified", 
        description="The underlying theoretical framework or hypothesis"
    )
    
    @classmethod
    def from_dict(cls, data: dict) -> "PaperMetadata":
        """Create from dict, handling None values."""
        return cls(
            methodology=data.get("methodology") or "Not specified",
            key_result=data.get("key_result") or "Not specified",
            core_theory=data.get("core_theory") or "Not specified",
        )


class RelationshipResult(BaseModel):
    """Strict schema for paper relationship synthesis."""
    relation_type: Literal["Contradicts", "Supports", "Extends"] = Field(
        ..., 
        description="The type of relationship between the two papers"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0, 
        le=1.0, 
        description="Confidence score of the relationship (0.0 to 1.0)"
    )
    explanation: str = Field(
        default="No explanation provided", 
        description="Brief explanation justifying the relationship type"
    )


# =============================================================================
# Retry Configuration for Rate Limits
# =============================================================================

T = TypeVar('T')

def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    job_id: Optional[str] = None
) -> T:
    """
    Execute a function with exponential backoff retry on rate limit errors.
    
    Args:
        func: The function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        
    Returns:
        The result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit error (429)
            if "429" in str(e) or "quota" in error_str or "rate" in error_str:
                last_exception = e
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    print(f"⏳ Rate limit hit, waiting {delay:.1f}s before retry ({attempt + 1}/{max_retries})...")
                    if job_id:
                        job_store[job_id]["status"] = "ratelimit"
                    time.sleep(delay)
                    continue
            # If not a rate limit error, raise immediately
            raise e
    
    raise last_exception  # type: ignore


# =============================================================================
# LLM Client Configuration (Groq - Free tier with generous limits)
# =============================================================================

def get_groq_llm() -> LLM:
    """
    Configure and return a Groq LLM client with Llama 3.
    
    Groq offers generous free tier limits (30 req/min).
    
    Returns:
        LLM: Configured LLM instance
        
    Raises:
        ValueError: If GROQ_API_KEY is not set
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Get your free key at https://console.groq.com/keys"
        )
    
    from llama_index.llms.groq import Groq
    
    llm = Groq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.1,
    )
    
    Settings.llm = llm
    return llm


def get_gemini_llm_fallback() -> LLM:
    """
    Fallback to Gemini if Groq is not available.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found for fallback.")
    
    from llama_index.llms.gemini import Gemini
    
    llm = Gemini(
        model="models/gemini-2.0-flash-lite",
        api_key=api_key,
        temperature=0.1,
    )
    
    Settings.llm = llm
    return llm


def get_embedding_model():
    """
    Get embedding model. Tries Gemini first, falls back to HuggingFace local.
    """
    # Try Gemini first
    api_key = os.getenv("GOOGLE_API_KEY")
    print("Embedding API Key:", "Set" if api_key else "Not Set")

    if api_key:
        try:
            from llama_index.embeddings.gemini import GeminiEmbedding
            embedding = GeminiEmbedding(
                model_name="models/embedding-001",
                api_key=api_key,
            )
            Settings.embed_model = embedding
            return embedding
        except Exception:
            pass
    
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    local_path = "/app/local_models/all-MiniLM-L6-v2"

    embedding = HuggingFaceEmbedding(model_name=local_path)
    # if os.path.exists(local_model_path):
    #     embedding = HuggingFaceEmbedding(model_name=local_model_path)
    # else:
    #     logging.warning(
    #         "Local model not found at './local_models/all-MiniLM-L6-v2'. "
    #         "Falling back to online model (this may be slow)."
    #     )
    #     embedding = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    Settings.embed_model = embedding
    return embedding


# =============================================================================
# ChromaDB Configuration (Persistent Local Storage)
# =============================================================================

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Configure and return a persistent ChromaDB client.
    
    The database is stored locally in backend/chroma_db/ directory.
    
    Returns:
        chromadb.PersistentClient: Configured ChromaDB client instance
    """
    # Ensure the persist directory exists
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )
    
    return client


def get_or_create_collection(
    client: chromadb.PersistentClient,
    collection_name: str = "paper_embeddings"
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection for storing paper embeddings.
    
    Args:
        client: ChromaDB client instance
        collection_name: Name of the collection (default: "paper_embeddings")
        
    Returns:
        chromadb.Collection: The collection instance
    """
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Research paper embeddings for similarity search"}
    )
    
    return collection


# =============================================================================
# Singleton Instances (Lazy Initialization)
# =============================================================================

_llm_instance: Optional[LLM] = None
_embedding_instance: Optional[Any] = None
_chroma_client: Optional[Any] = None  # chromadb.PersistentClient


def get_llm() -> LLM:
    """
    Get singleton LLM instance. Uses Groq by default, Gemini as fallback.
    """
    global _llm_instance
    if _llm_instance is None:
        try:
            _llm_instance = get_groq_llm()
            print("✅ Using Groq (Llama 3.1)")
        except ValueError:
            try:
                _llm_instance = get_gemini_llm_fallback()
                print("✅ Using Gemini (fallback)")
            except ValueError as e:
                raise ValueError(
                    "No API key found. Configure at least one:\n"
                    "- GROQ_API_KEY (recommended, free at https://console.groq.com/keys)\n"
                    "- GOOGLE_API_KEY (backup)"
                ) from e
    return _llm_instance


def get_embedding() -> Any:
    """Get singleton embedding model instance."""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = get_embedding_model()
    return _embedding_instance


def get_vector_store() -> chromadb.PersistentClient:
    """Get singleton ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = get_chroma_client()
    return _chroma_client


# =============================================================================
# RAG Functions (Store & Retrieve Papers)
# =============================================================================

def store_paper_embedding(
    paper_id: str,
    paper_text: str,
    metadata: dict | None = None,
    collection_name: str = "paper_embeddings"
) -> None:
    """
    Store a paper's embedding in ChromaDB for similarity search.
    
    Args:
        paper_id: Unique identifier for the paper (e.g., filename)
        paper_text: The text content to embed (abstract + methodology recommended)
        metadata: Optional metadata dict (title, authors, etc.)
        collection_name: ChromaDB collection name
    """
    client = get_vector_store()
    collection = get_or_create_collection(client, collection_name)
    
    # Check if paper already exists
    existing = collection.get(ids=[paper_id])
    if existing and existing["ids"]:
        # Update existing
        collection.update(
            ids=[paper_id],
            documents=[paper_text],
            metadatas=[metadata or {}]
        )
    else:
        # Add new
        collection.add(
            ids=[paper_id],
            documents=[paper_text],
            metadatas=[metadata or {}]
        )


def find_similar_papers(
    query_text: str,
    n_results: int = 5,
    collection_name: str = "paper_embeddings"
) -> list[dict]:
    """
    Find papers similar to the query text using vector similarity.
    
    Args:
        query_text: Text to search for (e.g., a paper's abstract)
        n_results: Number of similar papers to return
        collection_name: ChromaDB collection name
        
    Returns:
        List of dicts with 'id', 'text', 'metadata', 'distance'
    """
    client = get_vector_store()
    collection = get_or_create_collection(client, collection_name)
    
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    papers = []
    if results and results["ids"] and results["ids"][0]:
        for i, paper_id in enumerate(results["ids"][0]):
            papers.append({
                "id": paper_id,
                "text": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0
            })
    
    return papers


def get_papers_by_ids(
    paper_ids: list[str],
    collection_name: str = "paper_embeddings"
) -> list[dict]:
    """
    Retrieve specific papers from ChromaDB by ID.
    
    Args:
        paper_ids: List of paper IDs to retrieve
        collection_name: ChromaDB collection name
        
    Returns:
        List of dicts with 'id', 'text', 'metadata'
    """
    if not paper_ids:
        return []
        
    client = get_vector_store()
    collection = get_or_create_collection(client, collection_name)
    
    # ChromaDB .get(ids=...) returns only matches
    results = collection.get(ids=paper_ids)
    
    papers = []
    if results and results["ids"]:
        for i, paper_id in enumerate(results["ids"]):
            papers.append({
                "id": paper_id,
                "text": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
            
    return papers


def get_all_papers(collection_name: str = "paper_embeddings") -> list[dict]:
    """
    Retrieve all stored papers from ChromaDB.
    
    Returns:
        List of dicts with 'id', 'text', 'metadata'
    """
    client = get_vector_store()
    collection = get_or_create_collection(client, collection_name)
    
    results = collection.get()
    
    papers = []
    if results and results["ids"]:
        for i, paper_id in enumerate(results["ids"]):
            papers.append({
                "id": paper_id,
                "text": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {}
            })
    
    return papers


def delete_paper(paper_id: str, collection_name: str = "paper_embeddings") -> bool:
    """
    Delete a paper from ChromaDB.
    
    Returns:
        True if deleted, False if not found
    """
    client = get_vector_store()
    collection = get_or_create_collection(client, collection_name)
    
    try:
        collection.delete(ids=[paper_id])
        return True
    except Exception:
        return False
