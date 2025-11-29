"""Vector indexing service for Qdrant.

ENHANCED: Now indexes consolidated semantic chunks for better AI tutor context.
Uses API-based embeddings (Google Generative AI) for lightweight production deployment.
"""

import logging
import traceback
import os
import json
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from app.repositories.content_repository import ContentRepository
from app.services.content_pipeline.api_embedder import APIEmbedder

# Lazy imports for heavy dependencies - only imported when actually needed
if TYPE_CHECKING:
    from image_rag_pipeline.app.db.vector_store import VectorStore

logger = logging.getLogger(__name__)


def _get_vector_store():
    """
    Lazy import and initialization of VectorStore.
    This avoids importing torch at module load time.
    """
    # Add image_rag_pipeline to path
    import sys
    pipeline_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'image_rag_pipeline')
    if pipeline_path not in sys.path:
        sys.path.insert(0, pipeline_path)
    
    from image_rag_pipeline.app.db.vector_store import VectorStore
    return VectorStore()


class VectorIndexingService:
    """
    Service for indexing lecture content into Qdrant vector database.
    
    ENHANCED: Now indexes:
    1. Consolidated semantic chunks (rich narrative content for teaching)
    2. Flashcards (specific Q&A pairs for fact retrieval)
    
    Uses API-based embeddings (Google Generative AI) for lightweight deployment.
    """
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self._embedder: Optional[APIEmbedder] = None
        self._vector_store = None
    
    def _get_embedder(self) -> APIEmbedder:
        """Lazy initialization of API-based embedder."""
        if self._embedder is None:
            self._embedder = APIEmbedder()
        return self._embedder
    
    def _get_vector_store(self):
        """Lazy initialization of vector store."""
        if self._vector_store is None:
            self._vector_store = _get_vector_store()
        return self._vector_store
    
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
        Uses API-based embeddings for lightweight deployment.
        
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
        
        embedder = self._get_embedder()
        vector_store = self._get_vector_store()
        
        # Ensure collection exists (create_collection adds "course_" prefix internally)
        embedding_dim = embedder.get_embedding_dim()
        vector_store.create_collection(course_code, vector_size=embedding_dim)
        
        lecture_metadata = {
            "lecture_id": str(lecture_id),
            "lecture_title": lecture_title or f"Lecture {lecture_id}"
        }
        
        total_indexed = 0
        semantic_chunks_count = 0
        flashcards_count = 0
        
        # 1. Index consolidated semantic chunks (if available)
        if consolidated_analysis:
            if isinstance(consolidated_analysis, str):
                consolidated_analysis = json.loads(consolidated_analysis)
            
            logger.info(f"Indexing consolidated semantic chunks for lecture {lecture_id}...")
            semantic_chunks_count = self._ingest_consolidated_content(
                vector_store=vector_store,
                embedder=embedder,
                consolidated_analysis=consolidated_analysis,
                course_code=course_code,
                lecture_id=lecture_id,
                lecture_metadata=lecture_metadata
            )
            total_indexed += semantic_chunks_count
            logger.info(f"Indexed {semantic_chunks_count} semantic chunks")
        else:
            logger.warning(f"No consolidated_analysis found for lecture {lecture_id}, skipping semantic chunks")
        
        # 2. Index flashcards
        if flashcards:
            if isinstance(flashcards, str):
                flashcards = json.loads(flashcards)
            
            flashcard_items = flashcards.get("flashcards", [])
            if flashcard_items:
                logger.info(f"Indexing {len(flashcard_items)} flashcards for lecture {lecture_id}...")
                flashcards_count = self._ingest_flashcards(
                    vector_store=vector_store,
                    embedder=embedder,
                    flashcards=flashcard_items,
                    course_code=course_code,
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
    
    def _ingest_consolidated_content(
        self,
        vector_store,
        embedder: APIEmbedder,
        consolidated_analysis: Dict[str, Any],
        course_code: str,
        lecture_id: int,
        lecture_metadata: Dict[str, Any]
    ) -> int:
        """
        Ingest consolidated semantic chunks into the vector store.
        
        Args:
            vector_store: VectorStore instance
            embedder: APIEmbedder instance
            consolidated_analysis: The consolidated_structured_analysis JSON
            course_code: Course identifier
            lecture_id: Lecture ID
            lecture_metadata: Additional metadata
            
        Returns:
            Number of chunks indexed
        """
        import hashlib
        
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
            chunk_topics = chunk.get("topics", topic_names[:3])  # Use chunk-specific or first 3 overall
            
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
        
        # Insert into vector store (use course_code without prefix - insert_embeddings adds it)
        vector_store.insert_embeddings(
            course_id=course_code,
            embeddings=embeddings,
            metadata=metadata_list,
            ids=ids
        )
        
        return len(texts_to_embed)
    
    def _ingest_flashcards(
        self,
        vector_store,
        embedder: APIEmbedder,
        flashcards: list,
        course_code: str,
        lecture_id: int,
        lecture_metadata: Dict[str, Any]
    ) -> int:
        """
        Ingest flashcards into the vector store.
        
        Args:
            vector_store: VectorStore instance
            embedder: APIEmbedder instance
            flashcards: List of flashcard dicts
            course_code: Course identifier
            lecture_id: Lecture ID
            lecture_metadata: Additional metadata
            
        Returns:
            Number of flashcards indexed
        """
        import hashlib
        
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
        
        # Insert into vector store (use course_code without prefix - insert_embeddings adds it)
        vector_store.insert_embeddings(
            course_id=course_code,
            embeddings=embeddings,
            metadata=metadata_list,
            ids=ids
        )
        
        return len(texts_to_embed)
    
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
