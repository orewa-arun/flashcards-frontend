"""
FastAPI server for Image-RAG pipeline.
Provides endpoints for PDF ingestion, image/text search, AND vector indexing.

ENHANCED: Now includes /index endpoint for receiving content from main backend.
This allows the RAG backend to handle both indexing and chat with the same Qdrant store.
"""
import os
import logging
import hashlib
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import shutil
import json

from ..db.vector_store import VectorStore
from ..ingestion.loader import IngestionPipeline
from ..ingestion.api_embedder import APIEmbedder
from ..retrieval.query import ImageRetriever
from ..chatbot.chain import ConversationManager
from ..utils.config import Config

# Set logging level from config
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Image-RAG Pipeline", version="1.0.0")

# Configure CORS - allow main backend and frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # Main backend
        "https://flashcards-frontend-production.up.railway.app",  # Railway main backend
        "https://www.exammate.ai",  # Production frontend
        "*",  # Allow all for internal service-to-service calls
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGE_DIR = os.path.join(DATA_DIR, "images")
PDF_DIR = os.path.join(DATA_DIR, "pdfs")

# Ensure base data directories exist (Qdrant path is handled inside VectorStore)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

# Initialize components (lazy loading)
_vector_store = None
_embedder = None
_ingestion_pipeline = None
_retriever = None
_conversation_managers = {}  # Store conversation managers per course


def get_vector_store():
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        # Let VectorStore resolve QDRANT_PATH consistently, so that a
        # relative path like "data/embeddings" works the same for both
        # the main backend and this chat server.
        _vector_store = VectorStore()
    return _vector_store


def get_embedder():
    """Get or create embedder instance using API-based embeddings."""
    global _embedder
    if _embedder is None:
        _embedder = APIEmbedder()
    return _embedder


def get_ingestion_pipeline():
    """Get or create ingestion pipeline instance."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = IngestionPipeline(
            image_output_dir=IMAGE_DIR,
            vector_store=get_vector_store(),
            embedder=get_embedder(),
            chunk_size=Config.CHUNK_SIZE
        )
    return _ingestion_pipeline


def get_retriever():
    """Get or create retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = ImageRetriever(
            vector_store=get_vector_store(),
            embedder=get_embedder()
        )
    return _retriever


def extract_lecture_id_from_session(session_id: str, course_id: str) -> str:
    """
    Extract lecture_id from session_id.
    Session format: {user_uid}_{course_id}_{lecture_id}
    
    Args:
        session_id: Session identifier
        course_id: Course identifier
        
    Returns:
        Lecture identifier, or "unknown" if parsing fails
    """
    try:
        # NOTE ON FORMAT AND UNDERSCORES
        # ------------------------------
        # Session IDs are generated as:
        #     {user_uid}_{course_id}_{lecture_id}
        # where *course_id itself may contain underscores* (e.g. MAPP_F_MKT404_EN_2025).
        #
        # Relying on splitting and matching the full course_id fails in that case.
        # Instead, we treat the **last segment** as the lecture_id, which matches
        # how the frontend constructs the session_id.
        parts = session_id.split("_")
        if len(parts) < 2:
            logger.warning(
                f"Could not parse lecture_id from session '{session_id}', using 'unknown'"
            )
            return "unknown"
        
        lecture_id = parts[-1]
        logger.debug(
            f"Extracted lecture_id '{lecture_id}' from session '{session_id}' "
            f"for course '{course_id}'"
        )
        return lecture_id
    except Exception as e:
        logger.error(f"Error extracting lecture_id from session '{session_id}': {e}")
        return "unknown"


def get_conversation_manager(course_id: str, lecture_id: str) -> ConversationManager:
    """
    Get or create conversation manager for a course and lecture.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        
    Returns:
        ConversationManager instance for the course/lecture
    """
    global _conversation_managers
    
    # Use course_id + lecture_id as key for the manager
    manager_key = f"{course_id}_{lecture_id}"
    
    if manager_key not in _conversation_managers:
        logger.info(f"Creating conversation manager for {course_id}/{lecture_id}")
        _conversation_managers[manager_key] = ConversationManager(
            course_id=course_id,
            lecture_id=lecture_id,
            vector_store=get_vector_store(),
            embedder=get_embedder(),
            llm_model=os.getenv("LLM_MODEL", "gemini-1.5-flash-001"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.5")),
            top_k=int(os.getenv("CHAT_TOP_K", "5")),
            max_history_messages=int(os.getenv("CHAT_MAX_HISTORY", "6")),  # Updated to 6 (PILLAR 2)
            max_token_limit=int(os.getenv("CHAT_TOKEN_LIMIT", "1500"))  # Updated to 1500 (PILLAR 2)
        )
    
    return _conversation_managers[manager_key]


# Request/Response models
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class IngestResponse(BaseModel):
    success: bool
    message: str
    pdf_path: str
    course_id: str
    text_chunks: int
    images: int
    total_items: int


class SearchResponse(BaseModel):
    query: str
    course_id: str
    results: list


class IndexRequest(BaseModel):
    """Request model for indexing content from main backend."""
    lecture_id: int
    course_code: str
    lecture_title: Optional[str] = None
    flashcards: Optional[Dict[str, Any]] = None
    consolidated_analysis: Optional[Dict[str, Any]] = None


class IndexResponse(BaseModel):
    """Response model for indexing operations."""
    success: bool
    message: str
    lecture_id: int
    indexed_count: int = 0
    semantic_chunks: int = 0
    flashcards: int = 0


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Image-RAG Pipeline",
        "version": "1.0.0"
    }


@app.post("/ingest-pdf/{course_id}", response_model=IngestResponse)
async def ingest_pdf(
    course_id: str,
    file: UploadFile = File(...),
    lecture_name: Optional[str] = None,
    lecture_number: Optional[str] = None
):
    """
    Ingest a PDF file for a specific course.
    
    Args:
        course_id: Course identifier
        file: PDF file to upload
        lecture_name: Optional lecture name
        lecture_number: Optional lecture number
        
    Returns:
        Ingestion statistics
    """
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded PDF
        pdf_path = os.path.join(PDF_DIR, f"{course_id}_{file.filename}")
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Saved PDF to {pdf_path}")
        
        # Prepare metadata
        metadata = {
            "course_id": course_id
        }
        if lecture_name:
            metadata["lecture_name"] = lecture_name
        if lecture_number:
            metadata["lecture_number"] = lecture_number
        
        # Run ingestion pipeline
        pipeline = get_ingestion_pipeline()
        result = pipeline.ingest_pdf(
            pdf_path=pdf_path,
            course_id=course_id,
            pdf_metadata=metadata
        )
        
        return IngestResponse(
            success=True,
            message="PDF ingested successfully",
            **result
        )
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-image/{course_id}", response_model=SearchResponse)
async def search_image(course_id: str, request: SearchRequest):
    """
    Search for images using text query.
    
    Args:
        course_id: Course identifier
        request: Search request with query and top_k
        
    Returns:
        Search results with image metadata
    """
    try:
        retriever = get_retriever()
        results = retriever.query_text_to_image(
            query=request.query,
            course_id=course_id,
            top_k=request.top_k
        )
        return SearchResponse(**results)
    
    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-text/{course_id}", response_model=SearchResponse)
async def search_text(course_id: str, request: SearchRequest):
    """
    Search for text chunks using text query.
    
    Args:
        course_id: Course identifier
        request: Search request with query and top_k
        
    Returns:
        Search results with text chunks
    """
    try:
        retriever = get_retriever()
        results = retriever.query_text_to_text(
            query=request.query,
            course_id=course_id,
            top_k=request.top_k
        )
        return SearchResponse(**results)
    
    except Exception as e:
        logger.error(f"Text search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/images/{filename}")
async def get_image(filename: str):
    """
    Serve an image file.
    
    Args:
        filename: Image filename
        
    Returns:
        Image file
    """
    image_path = os.path.join(IMAGE_DIR, filename)
    
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(image_path)


# ============================================================================
# Indexing Endpoints (called by main backend)
# ============================================================================

@app.post("/index", response_model=IndexResponse)
async def index_content(request: IndexRequest):
    """
    Index lecture content into Qdrant.
    
    This endpoint is called by the main backend to index content.
    By having the RAG backend handle indexing, both indexing and chat
    use the same Qdrant store.
    
    Args:
        request: IndexRequest with lecture content
        
    Returns:
        IndexResponse with indexing statistics
    """
    try:
        logger.info(f"Received index request for lecture {request.lecture_id} (course: {request.course_code})")
        
        embedder = get_embedder()
        vector_store = get_vector_store()
        
        # Ensure collection exists
        embedding_dim = embedder.get_embedding_dim()
        vector_store.create_collection(request.course_code, vector_size=embedding_dim)
        
        lecture_metadata = {
            "lecture_id": str(request.lecture_id),
            "lecture_title": request.lecture_title or f"Lecture {request.lecture_id}"
        }
        
        total_indexed = 0
        semantic_chunks_count = 0
        flashcards_count = 0
        
        # 1. Index consolidated semantic chunks (if available)
        if request.consolidated_analysis:
            logger.info(f"Indexing consolidated semantic chunks for lecture {request.lecture_id}...")
            semantic_chunks_count = _ingest_consolidated_content(
                vector_store=vector_store,
                embedder=embedder,
                consolidated_analysis=request.consolidated_analysis,
                course_code=request.course_code,
                lecture_id=request.lecture_id,
                lecture_metadata=lecture_metadata
            )
            total_indexed += semantic_chunks_count
            logger.info(f"Indexed {semantic_chunks_count} semantic chunks")
        
        # 2. Index flashcards
        if request.flashcards:
            flashcard_items = request.flashcards.get("flashcards", [])
            if flashcard_items:
                logger.info(f"Indexing {len(flashcard_items)} flashcards for lecture {request.lecture_id}...")
                flashcards_count = _ingest_flashcards(
                    vector_store=vector_store,
                    embedder=embedder,
                    flashcards=flashcard_items,
                    course_code=request.course_code,
                    lecture_id=request.lecture_id,
                    lecture_metadata=lecture_metadata
                )
                total_indexed += flashcards_count
                logger.info(f"Indexed {flashcards_count} flashcards")
        
        return IndexResponse(
            success=True,
            message="Content indexed successfully",
            lecture_id=request.lecture_id,
            indexed_count=total_indexed,
            semantic_chunks=semantic_chunks_count,
            flashcards=flashcards_count
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Indexing failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


def _ingest_consolidated_content(
    vector_store: VectorStore,
    embedder: APIEmbedder,
    consolidated_analysis: Dict[str, Any],
    course_code: str,
    lecture_id: int,
    lecture_metadata: Dict[str, Any]
) -> int:
    """
    Ingest consolidated semantic chunks into the vector store.
    """
    semantic_chunks = consolidated_analysis.get("semantic_chunks", [])
    if not semantic_chunks:
        logger.warning("No semantic_chunks found in consolidated_analysis")
        return 0
    
    # Extract topics for metadata
    topics = consolidated_analysis.get("topics", [])
    topic_names = [t.get("name", "") for t in topics if isinstance(t, dict)]
    
    texts_to_embed = []
    metadata_list = []
    ids = []
    
    for i, chunk in enumerate(semantic_chunks):
        chunk_text = chunk.get("text", "")
        if not chunk_text:
            continue
        
        # Generate deterministic ID
        chunk_id = f"consolidated_{course_code}_{lecture_id}_{i}"
        hash_obj = hashlib.sha256(chunk_id.encode('utf-8'))
        int_id = abs(int.from_bytes(hash_obj.digest()[:8], 'big'))
        
        # Build metadata
        chunk_topics = chunk.get("topics", topic_names[:3])
        
        metadata = {
            "text": chunk_text,
            "source": "consolidated_chunk",
            "course_id": course_code,
            "lecture_id": str(lecture_id),
            "lecture_title": lecture_metadata.get("lecture_title", ""),
            "chunk_index": i,
            "topics": chunk_topics,
            "educational_value": chunk.get("educational_value", 0.7),
            "has_definitions": chunk.get("has_definitions", False),
            "has_examples": chunk.get("has_examples", False),
        }
        
        texts_to_embed.append(chunk_text)
        metadata_list.append(metadata)
        ids.append(int_id)
    
    if not texts_to_embed:
        return 0
    
    # Generate embeddings
    embeddings = embedder.embed_text(texts_to_embed)
    
    # Insert into vector store
    vector_store.insert_embeddings(
        course_id=course_code,
        embeddings=embeddings,
        metadata=metadata_list,
        ids=ids
    )
    
    return len(texts_to_embed)


def _ingest_flashcards(
    vector_store: VectorStore,
    embedder: APIEmbedder,
    flashcards: list,
    course_code: str,
    lecture_id: int,
    lecture_metadata: Dict[str, Any]
) -> int:
    """
    Ingest flashcards into the vector store.
    """
    if not flashcards:
        return 0
    
    texts_to_embed = []
    metadata_list = []
    ids = []
    
    for i, fc in enumerate(flashcards):
        question = fc.get("question", "")
        answer = fc.get("answer", "")
        flashcard_id = fc.get("id", f"fc_{course_code}_{lecture_id}_{i}")
        
        if not question:
            continue
        
        # Combine Q&A for embedding
        combined_text = f"Question: {question}\nAnswer: {answer}"
        
        # Generate deterministic ID
        hash_obj = hashlib.sha256(flashcard_id.encode('utf-8'))
        int_id = abs(int.from_bytes(hash_obj.digest()[:8], 'big'))
        
        metadata = {
            "text": combined_text,
            "source": "flashcard",
            "flashcard_id": flashcard_id,
            "question": question,
            "answer": answer,
            "course_id": course_code,
            "lecture_id": str(lecture_id),
            "lecture_title": lecture_metadata.get("lecture_title", ""),
            "context": fc.get("context", ""),
            "difficulty": fc.get("difficulty", "medium"),
        }
        
        texts_to_embed.append(combined_text)
        metadata_list.append(metadata)
        ids.append(int_id)
    
    if not texts_to_embed:
        return 0
    
    # Generate embeddings
    embeddings = embedder.embed_text(texts_to_embed)
    
    # Insert into vector store
    vector_store.insert_embeddings(
        course_id=course_code,
        embeddings=embeddings,
        metadata=metadata_list,
        ids=ids
    )
    
    return len(texts_to_embed)


# ============================================================================
# Chat Endpoints
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    session_id: str


@app.post("/chat/{course_id}", response_model=ChatResponse)
async def chat(course_id: str, request: ChatRequest):
    """
    Chat with the course assistant using conversational RAG.
    
    The chatbot maintains conversation history per session and uses
    retrieved course materials to answer questions accurately.
    
    ENHANCED: Now extracts lecture_id from session_id to provide foundational context.
    
    Args:
        course_id: Course identifier (e.g., "MS5260")
        request: Chat request with message and session_id (format: uid_courseId_lectureId)
        
    Returns:
        Chat response with answer and session_id
        
    Example:
        POST /chat/MS5260
        {
            "message": "What is MIS?",
            "session_id": "user123_MS5260_MIS_lec_1-3"
        }
    """
    try:
        # Extract lecture_id from session_id (PILLAR 1: Foundational Context)
        lecture_id = extract_lecture_id_from_session(request.session_id, course_id)
        
        conversation_manager = get_conversation_manager(course_id, lecture_id)
        
        result = conversation_manager.chat(
            session_id=request.session_id,
            message=request.message
        )
        
        return ChatResponse(**result)
    
    except Exception as e:
        import traceback
        logger.error(f"Chat failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/{course_id}/stream")
async def stream_chat(course_id: str, request: ChatRequest):
    """
    Stream chat response from the AI Tutor.
    """
    try:
        lecture_id = extract_lecture_id_from_session(request.session_id, course_id)
        conversation_manager = get_conversation_manager(course_id, lecture_id)
        
        return StreamingResponse(
            conversation_manager.stream_chat(
                session_id=request.session_id,
                message=request.message
            ),
            media_type="text/plain"
        )
    except Exception as e:
        import traceback
        logger.error(f"Stream chat failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/{course_id}/clear")
async def clear_chat_session(course_id: str, session_id: str = "default"):
    """
    Clear the chat history for a session.
    
    Args:
        course_id: Course identifier
        session_id: Session identifier to clear (format: uid_courseId_lectureId)
        
    Returns:
        Success message
    """
    try:
        # Extract lecture_id from session_id
        lecture_id = extract_lecture_id_from_session(session_id, course_id)
        
        conversation_manager = get_conversation_manager(course_id, lecture_id)
        conversation_manager.clear_session(session_id)
        
        return {"status": "success", "message": f"Session {session_id} cleared"}
    
    except Exception as e:
        logger.error(f"Clear session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/{course_id}/history")
async def get_chat_history(course_id: str, session_id: str = "default"):
    """
    Get the chat history for a session.
    
    Args:
        course_id: Course identifier
        session_id: Session identifier (format: uid_courseId_lectureId)
        
    Returns:
        List of messages in the session
    """
    try:
        # Extract lecture_id from session_id
        lecture_id = extract_lecture_id_from_session(session_id, course_id)
        
        conversation_manager = get_conversation_manager(course_id, lecture_id)
        history = conversation_manager.get_session_history(session_id)
        
        return {"session_id": session_id, "history": history}
    
    except Exception as e:
        import traceback
        logger.error(f"Get history failed: {e}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Detailed health check with component status."""
    # Get QDRANT_PATH from environment or use default
    qdrant_path = os.getenv("QDRANT_PATH", "data/embeddings")
    
    return {
        "status": "healthy",
        "components": {
            "vector_store": _vector_store is not None,
            "embedder": _embedder is not None,
            "ingestion_pipeline": _ingestion_pipeline is not None,
            "retriever": _retriever is not None
        },
        "directories": {
            "images": os.path.exists(IMAGE_DIR),
            "pdfs": os.path.exists(PDF_DIR),
            "vector_db": os.path.exists(qdrant_path)
        },
        "rag_backend_url": RAG_BACKEND_URL if 'RAG_BACKEND_URL' in dir() else "N/A"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)

