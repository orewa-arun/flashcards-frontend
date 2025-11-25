"""Orchestrator service for content pipeline - high-level facade."""

import logging
from typing import Dict, Any

from app.repositories.content_repository import ContentRepository
from app.services.content_pipeline.ingestion import IngestionService
from app.services.content_pipeline.structured_analysis import StructuredAnalysisService
from app.services.content_pipeline.flashcard_generation import FlashcardGenerationService
from app.services.content_pipeline.quiz_generation import QuizGenerationService
from app.services.content_pipeline.vector_indexing import VectorIndexingService

logger = logging.getLogger(__name__)


class ContentPipelineOrchestrator:
    """
    High-level orchestrator for content pipeline operations.
    Provides a unified interface for triggering pipeline actions.
    """
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize orchestrator with repository and service dependencies.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self.ingestion = IngestionService(repository)
        self.analysis = StructuredAnalysisService(repository)
        self.flashcards = FlashcardGenerationService(repository)
        self.quizzes = QuizGenerationService(repository)
        self.indexing = VectorIndexingService(repository)
    
    async def run_ingestion(
        self,
        course_metadata: Dict[str, Any],
        pdf_files: list
    ) -> Dict[str, Any]:
        """
        Run the ingestion workflow.
        
        Args:
            course_metadata: Course metadata dict
            pdf_files: List of PDF files to upload
            
        Returns:
            Dict: Result with course_id and lecture_ids
        """
        logger.info(f"Running ingestion for course: {course_metadata.get('course_code')}")
        return await self.ingestion.ingest_course_with_lectures(
            course_metadata=course_metadata,
            pdf_files=pdf_files
        )
    
    async def run_analysis(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Run structured analysis for a lecture.
        
        Args:
            lecture_id: Lecture ID to process
            
        Returns:
            Dict: Result with success status
        """
        logger.info(f"Running structured analysis for lecture: {lecture_id}")
        return await self.analysis.generate_structured_analysis(lecture_id=lecture_id)
    
    async def run_flashcard_generation(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Run flashcard generation for a lecture.
        
        Args:
            lecture_id: Lecture ID to process
            
        Returns:
            Dict: Result with success status
        """
        logger.info(f"Running flashcard generation for lecture: {lecture_id}")
        return await self.flashcards.generate_flashcards(lecture_id=lecture_id)
    
    async def run_quiz_generation(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Run quiz generation for a lecture.
        
        Args:
            lecture_id: Lecture ID to process
            
        Returns:
            Dict: Result with success status
        """
        logger.info(f"Running quiz generation for lecture: {lecture_id}")
        return await self.quizzes.generate_quizzes(lecture_id=lecture_id)
    
    async def run_indexing(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Run vector indexing for a lecture.
        
        Args:
            lecture_id: Lecture ID to process
            
        Returns:
            Dict: Result with success status
        """
        logger.info(f"Running vector indexing for lecture: {lecture_id}")
        return await self.indexing.index_content(lecture_id=lecture_id)
    
    async def get_action_handler(self, action: str):
        """
        Get the appropriate handler for an action.
        
        Args:
            action: Action name (analyze, flashcards, quiz, index)
            
        Returns:
            Callable: Handler function
        """
        handlers = {
            "analyze": self.run_analysis,
            "flashcards": self.run_flashcard_generation,
            "quiz": self.run_quiz_generation,
            "index": self.run_indexing
        }
        
        handler = handlers.get(action)
        if not handler:
            raise ValueError(f"Unknown action: {action}")
        
        return handler


def create_orchestrator(repository: ContentRepository) -> ContentPipelineOrchestrator:
    """
    Factory function to create orchestrator.
    
    Args:
        repository: Content repository
        
    Returns:
        ContentPipelineOrchestrator instance
    """
    return ContentPipelineOrchestrator(repository)
