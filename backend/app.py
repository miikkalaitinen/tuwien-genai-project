# filter out stupid pydantic warning crying about deprications in packages
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

import shutil
import uuid
import hashlib
from pathlib import Path
from typing import List, Literal, Dict, Any, Optional
import os

from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# PDF processing modules
from src.integration import process_single_paper, build_paper_graph
from src.utils import find_similar_papers, get_papers_by_ids
from src.components.pdf_ingestion import PDFIngestor
from src.components.chunking import SemanticChunker
import logging
from src.utils import job_store

# Log stuff
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

class PaperItem(BaseModel):
    id: str
    name: str

class GraphRequest(BaseModel):
    mode: Literal["student", "researcher"] = "student"
    papers: Optional[List[PaperItem]] = None

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
    if not os.getenv("GOOGLE_API_KEY") or "your-key-here" in os.getenv("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY is missing! Using HuggingFace fallback for embeddings, (SLOW!)")

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
    
    graph_mode = user_type if user_type in ["student", "researcher"] else "student"
    
    try:
        job_store[job_id]["status"] = "processing"
        total_files = len(files_info)
        
        for i, info in enumerate(files_info):
            file_path = Path(info["path"])
            original_name = info["original_name"]
            
            job_store[job_id]["progress"] = int((i / total_files) * 80)
            job_store[job_id]["current_file"] = original_name
            
            try:
                filename = file_path.name
                collection_name = f"paper_embeddings_{graph_mode}"
                existing_papers = get_papers_by_ids([filename], collection_name=collection_name)
                
                if existing_papers:
                    logger.info(f"Paper {original_name} ({filename}) already exists in DB ({graph_mode}). Skipping processing.")
                    existing = existing_papers[0]
                    processed_files.append({
                        "filename": filename,
                        "original_filename": original_name,
                        "file_path": str(file_path),
                        "sections": {},
                        "extraction_success": True,
                        "metadata": existing["metadata"]
                    })
                    continue

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
                
                result = process_single_paper(paper_data, store_embedding=True, mode=graph_mode)
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

def regenerate_graph_task(job_id: str, request: GraphRequest):
    """
    Background worker function to regenerate graph from existing papers.
    """
    mode = request.mode
    requested_papers = request.papers
    
    logger.info(f"Job {job_id}: Regenerating graph in mode: {mode}")
    
    try:
        job_store[job_id]["status"] = "processing"
        job_store[job_id]["progress"] = 10
        job_store[job_id]["current_file"] = "Fetching papers..."

        from src.utils import get_all_papers, get_papers_by_ids
        
        collection_name = f"paper_embeddings_{mode}"
        
        if requested_papers:
            # Extract IDs from request objects
            paper_ids = [p.id for p in requested_papers]
            db_papers = get_papers_by_ids(paper_ids, collection_name=collection_name)
        else:
            db_papers = get_all_papers(collection_name=collection_name)
        
        processed_papers = []
        found_ids = set()

        for p in db_papers:
            found_ids.add(p["id"])
            processed_papers.append({
                "filename": p["id"],
                "original_filename": p["metadata"].get("original_filename"),
                "metadata": {
                    "methodology": p["metadata"].get("methodology"),
                    "key_result": p["metadata"].get("key_result"),
                    "core_theory": p["metadata"].get("core_theory"),
                },
                "file_path": p["metadata"].get("file_path", ""),
                "extraction_success": True 
            })

        # Check for missing papers and process them
        if requested_papers:
            # Identify which requested papers were not found in DB
            missing_papers = [p for p in requested_papers if p.id not in found_ids]
            
            if missing_papers:
                total_missing = len(missing_papers)
                logger.info(f"Found {total_missing} papers missing from {mode} DB. Processing from disk...")
                
                for i, missing_paper in enumerate(missing_papers):
                    job_store[job_id]["progress"] = 10 + int((i / total_missing) * 40)
                    job_store[job_id]["current_file"] = f"Processing {missing_paper.name}..."
                    
                    file_path = UPLOAD_DIR / missing_paper.id
                    if not file_path.exists():
                        logger.warning(f"Paper {missing_paper.id} not found on disk. Skipping.")
                        continue
                    
                    try:
                        # Use provided name from request
                        original_name = missing_paper.name
                        
                        ingestor = PDFIngestor(str(file_path))
                        full_markdown = ingestor.extract_clean_text()
                        
                        chunker = SemanticChunker()
                        sections = chunker.split_by_section(full_markdown)
                        
                        paper_data = {
                            "filename": missing_paper.id,
                            "original_filename": original_name,
                            "metadata": {
                                "file_path": str(file_path),
                                "original_filename": original_name
                            },
                            "sections": sections
                        }
                        
                        result = process_single_paper(paper_data, store_embedding=True, mode=mode)
                        if result["extraction_success"]:
                            processed_papers.append(result)

                    except Exception as e:
                        logger.error(f"Failed to process missing paper {missing_paper.name}: {e}")

        job_store[job_id]["progress"] = 50
        job_store[job_id]["current_file"] = "Building Graph..."

        graph_data = build_paper_graph(
            processed_papers=processed_papers, 
            mode=mode,
            confidence_threshold=0.6,
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

@app.post("/graph")
async def make_graph(request: GraphRequest, background_tasks: BackgroundTasks):
    """
    Initiates asynchronous graph regeneration.
    Returns a job_id immediately. Use /batch-status/{job_id} to check progress.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received graph regeneration request. Job ID: {job_id}")

    job_store[job_id] = {
        "status": "queued",
        "progress": 0,
        "current_file": "Initializing...",
        "created_at": str(uuid.uuid1())
    }
    
    background_tasks.add_task(regenerate_graph_task, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Graph regeneration started."
    }