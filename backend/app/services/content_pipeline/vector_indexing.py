"""Vector indexing service for Qdrant.

ENHANCED: Now indexes consolidated semantic chunks for better AI tutor context.
"""

import logging
import traceback
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.repositories.content_repository import ContentRepository

# Import the image_rag_pipeline components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'image_rag_pipeline'))

from image_rag_pipeline.app.ingestion.loader import IngestionPipeline
from image_rag_pipeline.app.ingestion.embedder import Embedder
from image_rag_pipeline.app.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


class VectorIndexingService:
    """
    Service for indexing lecture content into Qdrant vector database.
    
    ENHANCED: Now indexes:
    1. Consolidated semantic chunks (rich narrative content for teaching)
    2. Flashcards (specific Q&A pairs for fact retrieval)
    """
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self._embedder: Optional[Embedder] = None
        self._vector_store: Optional[VectorStore] = None
        self._pipeline: Optional[IngestionPipeline] = None
    
    def _get_embedder(self) -> Embedder:
        """Lazy initialization of embedder."""
        if self._embedder is None:
            self._embedder = Embedder()
        return self._embedder
    
    def _get_vector_store(self) -> VectorStore:
        """Lazy initialization of vector store."""
        if self._vector_store is None:
            # Let VectorStore resolve QDRANT_PATH consistently so that a
            # relative path like "data/embeddings" works regardless of
            # the current working directory of the backend service.
            self._vector_store = VectorStore()
        return self._vector_store
    
    def _get_pipeline(self) -> IngestionPipeline:
        """Lazy initialization of ingestion pipeline."""
        if self._pipeline is None:
            # Image output directory (not used for text-only ingestion)
            image_dir = os.getenv("IMAGE_OUTPUT_DIR", "/tmp/rag_images")
            os.makedirs(image_dir, exist_ok=True)
            
            self._pipeline = IngestionPipeline(
                image_output_dir=image_dir,
                vector_store=self._get_vector_store(),
                embedder=self._get_embedder()
            )
        return self._pipeline
    
    async def index_to_qdrant(
        self,
        flashcards: Dict[str, Any],
        lecture_id: int,
        course_code: str,
        consolidated_analysis: Optional[Dict[str, Any]] = None,
        lecture_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index lecture content into Qdrant.
        
        ENHANCED: Now indexes both consolidated chunks and flashcards.
        
        Args:
            flashcards: Flashcards JSON
            lecture_id: ID of the lecture
            course_code: Course code for organization
            consolidated_analysis: Optional consolidated_structured_analysis
            lecture_title: Optional lecture title for metadata
            
        Returns:
            Dict: Indexing result with count of indexed items
        """
        logger.info(f"Indexing content to Qdrant for lecture {lecture_id} (course: {course_code})")
        
        pipeline = self._get_pipeline()
        lecture_metadata = {
            "lecture_id": str(lecture_id),
            "lecture_title": lecture_title or f"Lecture {lecture_id}"
        }
        
        total_indexed = 0
        semantic_chunks_count = 0
        flashcards_count = 0
        
        # 1. Index consolidated semantic chunks (if available)
        if consolidated_analysis:
            # Parse if it's a string
            if isinstance(consolidated_analysis, str):
                consolidated_analysis = json.loads(consolidated_analysis)
            
            logger.info(f"Indexing consolidated semantic chunks for lecture {lecture_id}...")
            consolidated_result = pipeline.ingest_consolidated_content(
                consolidated_analysis=consolidated_analysis,
                course_id=course_code,
                lecture_id=lecture_id,
                lecture_metadata=lecture_metadata
            )
            semantic_chunks_count = consolidated_result.get("semantic_chunks", 0)
            total_indexed += semantic_chunks_count
            logger.info(f"Indexed {semantic_chunks_count} semantic chunks")
        else:
            logger.warning(f"No consolidated_analysis found for lecture {lecture_id}, skipping semantic chunks")
        
        # 2. Index flashcards
        if flashcards:
            # Parse if it's a string
            if isinstance(flashcards, str):
                flashcards = json.loads(flashcards)
            
            flashcard_items = flashcards.get("flashcards", [])
            if flashcard_items:
                logger.info(f"Indexing {len(flashcard_items)} flashcards for lecture {lecture_id}...")
                flashcards_count = pipeline._ingest_flashcards_from_dict(
                    flashcards=flashcard_items,
                    course_id=course_code,
                    lecture_id=lecture_id,
                    lecture_metadata=lecture_metadata
                )
                total_indexed += flashcards_count
                logger.info(f"Indexed {flashcards_count} flashcards")
        else:
            logger.warning(f"No flashcards found for lecture {lecture_id}")
        
        result = {
            "indexed_count": total_indexed,
            "semantic_chunks": semantic_chunks_count,
            "flashcards": flashcards_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Indexing complete for lecture {lecture_id}: {result}")
        return result
    
    async def index_content(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Index lecture content to Qdrant.
        
        ENHANCED: Now indexes consolidated semantic chunks alongside flashcards.
        
        Args:
            lecture_id: ID of the lecture to process
            
        Returns:
            Dict: Result with success status and data
        """
        try:
            # Fetch lecture from database
            lecture = await self.repository.get_lecture_by_id(lecture_id)
            
            if not lecture:
                raise ValueError(f"Lecture with ID {lecture_id} not found")
            
            # Check prerequisites - we need at least flashcards or consolidated analysis
            has_flashcards = lecture.get("flashcard_status") == "completed" and lecture.get("flashcards")
            has_consolidated = lecture.get("consolidated_structured_analysis") is not None
            
            if not has_flashcards and not has_consolidated:
                raise ValueError(
                    f"Cannot index content: need either flashcards (status: {lecture.get('flashcard_status')}) "
                    f"or consolidated_structured_analysis"
                )
            
            if lecture["qdrant_status"] == "completed":
                logger.info(f"Lecture {lecture_id} already indexed to Qdrant")
                return {
                    "success": True,
                    "message": "Content already indexed",
                    "lecture_id": lecture_id
                }
            
            # Update status to in_progress
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="qdrant_status",
                status_value="in_progress"
            )
            
            # Index to Qdrant (both consolidated and flashcards)
            indexing_result = await self.index_to_qdrant(
                flashcards=lecture.get("flashcards"),
                lecture_id=lecture_id,
                course_code=lecture["course_code"],
                consolidated_analysis=lecture.get("consolidated_structured_analysis"),
                lecture_title=lecture.get("lecture_title")
            )
            
            # Update lecture status
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="qdrant_status",
                status_value="completed"
            )
            
            # Clear any previous errors
            await self.repository.clear_lecture_error(
                lecture_id=lecture_id,
                error_key="qdrant_error"
            )
            
            logger.info(f"Successfully indexed lecture {lecture_id} to Qdrant")
            return {
                "success": True,
                "message": "Content indexing completed",
                "lecture_id": lecture_id,
                "indexed_count": indexing_result.get("indexed_count", 0),
                "semantic_chunks": indexing_result.get("semantic_chunks", 0),
                "flashcards": indexing_result.get("flashcards", 0)
            }
            
        except Exception as e:
            logger.error(f"Error indexing content for lecture {lecture_id}: {str(e)}")
            
            # Update lecture with error
            try:
                await self.repository.update_lecture_status(
                    lecture_id=lecture_id,
                    status_field="qdrant_status",
                    status_value="failed"
                )
                
                error_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.repository.update_lecture_error(
                    lecture_id=lecture_id,
                    error_key="qdrant_error",
                    error_data=error_data
                )
            except Exception as commit_error:
                logger.error(f"Failed to update error status: {str(commit_error)}")
            
            return {
                "success": False,
                "message": f"Failed to index content: {str(e)}",
                "lecture_id": lecture_id
            }
