"""
Module: FastAPI Application (Main Entry Point)
Owner: Miikka (Frontend & Visualization Developer)

TODO for Miikka:
- Add file upload endpoints for PDF processing
- Integrate with connection_engine.py for relationship detection
- Add endpoints for graph data retrieval
- Implement Student/Researcher mode toggle

The PDF processing pipeline is ready.
"""

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import shutil
import uuid
import hashlib
from pathlib import Path
from typing import List, Literal, Dict, Any
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Jaime's and Marta's backend modules
from src.integration import process_single_paper, build_paper_graph, load_processed_papers
from src.utils import find_similar_papers
from src.components.pdf_ingestion import PDFIngestor
from src.components.chunking import SemanticChunker
import logging

# Log stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

job_store: Dict[str, Dict[str, Any]] = {}

app = FastAPI(
    title="Research Paper Navigator API",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Research Paper Navigator API...")
    if not os.getenv("LLAMA_CLOUD_API_KEY") or "your-key-here" in os.getenv("LLAMA_CLOUD_API_KEY"):
        logger.warning("LLAMA_CLOUD_API_KEY is missing! PDF processing will fail.")
    if not os.getenv("GROQ_API_KEY") or "your-key-here" in os.getenv("GROQ_API_KEY"):
        logger.warning("GROQ_API_KEY is missing! Using Gemini fallback for LLM tasks.")
        if not os.getenv("GOOGLE_API_KEY") or "your-key-here" in os.getenv("GOOGLE_API_KEY"):
            logger.warning("GOOGLE_API_KEY is also missing! LLM tasks will fail.")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_batch_task(job_id: str, files_info: List[Dict[str, Any]], user_type: str):
    """
    Background worker function to process PDFs.
    """
    logger.info(f"Job {job_id}: Started processing {len(files_info)} files")
    processed_files = []
    
    try:
        job_store[job_id]["status"] = "processing"
        total_files = len(files_info)
        
        for i, info in enumerate(files_info):
            file_path = Path(info["path"])
            original_name = info["original_name"]
            
            job_store[job_id]["progress"] = int((i / total_files) * 80)
            job_store[job_id]["current_file"] = original_name
            
            try:
                ingestor = PDFIngestor(str(file_path))
                full_markdown = ingestor.extract_clean_text()
                
                chunker = SemanticChunker()
                sections = chunker.split_by_section(full_markdown)
                
                paper_data = {
                    "filename": file_path.name,
                    "original_filename": original_name,
                    "metadata": {
                        "file_path": str(file_path),
                        "original_filename": original_name
                    },
                    "sections": sections
                }
                
                result = process_single_paper(paper_data, store_embedding=True)
                if result["extraction_success"]:
                    processed_files.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to process {original_name}: {e}")
                
        if not processed_files:
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["error"] = "No valid PDF files could be processed."
            return

        job_store[job_id]["progress"] = 90
        job_store[job_id]["current_file"] = "Building Graph..."
        
        graph_mode = user_type if user_type in ["student", "researcher"] else "student"
        
        graph_data = build_paper_graph(
            processed_papers=processed_files,
            mode=graph_mode,
            confidence_threshold=0.6 
        )
        
        job_store[job_id]["result"] = graph_data
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["progress"] = 100
        logger.info(f"Job {job_id}: Completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {e}")
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)

@app.get("/")
def root():
    return {"message": "Research Paper Navigator API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/process-batch")
async def process_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    mode: str = Form(...),
    user_type: str = Form(...)
):
    """
    Initiates asynchronous PDF processing.
    Returns a job_id immediately. Use /batch-status/{job_id} to check progress.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received PDF batch: {len(files)} files. Job ID: {job_id}")
    
    files_info = []
    
    for file in files:
        if not file.filename.endswith(".pdf"):
            continue
            
        # Compute hash of file content
        content = file.file.read()
        file_hash = hashlib.md5(content).hexdigest()
        file.file.seek(0)
        
        # Save file with hash as filename to avoid duplicates
        hash_filename = f"{file_hash}.pdf"
        file_path = UPLOAD_DIR / hash_filename
        
        if not file_path.exists():
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        files_info.append({
            "path": str(file_path),
            "original_name": file.filename
        })
    
    if not files_info:
        raise HTTPException(status_code=400, detail="No valid PDF files uploaded.")

    job_store[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_file": "Initializing...",
        "total_files": len(files_info),
        "created_at": str(uuid.uuid1())
    }
    
    # Start background task
    background_tasks.add_task(process_batch_task, job_id, files_info, user_type)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Batch processing started."
    }

@app.get("/batch-status/{job_id}")
def get_batch_status(job_id: str):
    """
    Check the status of a background processing job.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return job
    
@app.get("/graph")
def get_graph(mode: Literal["student", "researcher"] = "student"):
    """
    Regenerates the graph for the previously uploaded papers 
    using a different perspective.
    """
    logger.info(f"Regenerating graph in mode: {mode}")
    
    try:
        papers = load_processed_papers("processed_papers.json")
        
        graph_data = build_paper_graph(
            processed_papers=papers, 
            mode=mode,
            confidence_threshold=0.5
        )
        
        return graph_data
        
    except FileNotFoundError:
        return {"nodes": [], "edges": []}
    except Exception as e:
        logger.error(f"Mode switch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate graph")
    
@app.get("/search")
def search_papers(query: str, limit: int = 5):
    """
    Performs semantic search across the uploaded papers.
    """
    logger.info(f"Semantic searching for: {query}")
    
    try:
        results = find_similar_papers(query, n_results=limit)
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "paper_id": r["id"],
                "excerpt": r["text"][:200] + "...",
                "score": r["distance"]
            })
            
        return {"results": formatted_results}
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search engine error")