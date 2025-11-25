"""Vector indexing service for Qdrant."""

import logging
import traceback
from typing import Dict, Any
from datetime import datetime

from app.repositories.content_repository import ContentRepository

logger = logging.getLogger(__name__)


class VectorIndexingService:
    """Service for indexing flashcards into Qdrant vector database."""
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        # TODO: Initialize Qdrant client from config
    
    async def index_to_qdrant(
        self,
        flashcards: Dict[str, Any],
        lecture_id: int,
        course_code: str
    ) -> Dict[str, Any]:
        """
        Index flashcards into Qdrant.
        
        Args:
            flashcards: Flashcards JSON
            lecture_id: ID of the lecture
            course_code: Course code for organization
            
        Returns:
            Dict: Indexing result with count of indexed items
        """
        # TODO: Implement actual Qdrant indexing
        logger.info(f"Indexing flashcards to Qdrant for lecture {lecture_id}")
        
        # Placeholder implementation
        result = {
            "indexed_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Indexed flashcards for lecture {lecture_id}")
        return result
    
    async def index_content(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Index lecture content to Qdrant.
        
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
            
            # Check prerequisites
            if lecture["flashcard_status"] != "completed":
                raise ValueError(
                    f"Cannot index content: flashcard_status is "
                    f"'{lecture['flashcard_status']}', must be 'completed'"
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
            
            # Index to Qdrant
            indexing_result = await self.index_to_qdrant(
                flashcards=lecture["flashcards"],
                lecture_id=lecture_id,
                course_code=lecture["course_code"]
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
                "indexed_count": indexing_result.get("indexed_count", 0)
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
