"""Structured analysis service using self-contained modules."""

import logging
import traceback
import boto3
from typing import Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError

from app.config import settings
from app.repositories.content_repository import ContentRepository
from app.content_generation.llm.client import create_llm_client
from app.content_generation.analyzers.pdf_extractor import PDFImageExtractor
from app.content_generation.analyzers.slide_analyzer import SlideAnalyzer
from app.content_generation.analyzers.content_condenser import ContentCondenser

logger = logging.getLogger(__name__)


class StructuredAnalysisService:
    """Service for generating structured analysis from lecture PDFs."""
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: Content repository for database access
        """
        self.repository = repository
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT_URL,
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            region_name='auto'
        )
        self.bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
        self.model_name = settings.MODEL_ANALYSIS
    
    def fetch_pdf_from_r2(self, r2_path: str) -> bytes:
        """
        Fetch PDF content from R2 bucket.
        
        Args:
            r2_path: Path to PDF in R2
            
        Returns:
            bytes: PDF content
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=r2_path
            )
            pdf_content = response['Body'].read()
            logger.info(f"Fetched PDF from R2: {r2_path}")
            return pdf_content
        except ClientError as e:
            logger.error(f"Failed to fetch PDF from R2: {str(e)}")
            raise
    
    async def generate_structured_analysis(
        self,
        lecture_id: int
    ) -> Dict[str, Any]:
        """
        Generate structured analysis for a lecture.
        
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
            if lecture["analysis_status"] == "completed":
                logger.info(f"Lecture {lecture_id} already has completed analysis")
                return {
                    "success": True,
                    "message": "Analysis already completed",
                    "lecture_id": lecture_id
                }
            
            # Update status to in_progress
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="analysis_status",
                status_value="in_progress"
            )
            
            # Fetch PDF from R2
            pdf_content = self.fetch_pdf_from_r2(lecture["r2_pdf_path"])
            
            # Get course context
            course = await self.repository.get_course_by_code(lecture["course_code"])
            course_context = {
                "course_name": course["course_name"],
                "instructor": course.get("instructor", ""),
                "reference_textbooks": course.get("reference_textbooks", [])
            }
            
            # Initialize LLM client for vision
            llm_client = create_llm_client(
                provider="gemini",
                model=self.model_name,
                api_key=settings.GEMINI_API_KEY
            )
            
            # Step 1: Extract images from PDF
            extractor = PDFImageExtractor()
            image_paths = extractor.extract_from_bytes(pdf_content)
            logger.info(f"Extracted {len(image_paths)} slides")
            
            # Step 2: Analyze slides using parallel batching
            analyzer = SlideAnalyzer(
                llm_client=llm_client,
                course_context=course_context,
                batch_size=settings.ANALYSIS_BATCH_SIZE,
                max_concurrency=settings.ANALYSIS_MAX_CONCURRENCY,
                batch_delay_ms=settings.ANALYSIS_BATCH_DELAY_MS
            )
            slide_analyses = await analyzer.analyze_slides_parallel(image_paths)
            
            # Step 3: Condense into structured content
            condenser = ContentCondenser(llm_client)
            structured_content = condenser.condense(
                slide_analyses=slide_analyses,
                lecture_title=lecture["lecture_title"],
                course_context=course_context
            )
            
            # Prepare final result
            structured_analysis = {
                "lecture_title": lecture["lecture_title"],
                "model_used": self.model_name,
                "total_slides": len(image_paths),
                "course_context": course_context,
                "structured_content": structured_content,
                "raw_slide_analyses": slide_analyses
            }
            
            # Update lecture with results
            await self.repository.update_lecture_content(
                lecture_id=lecture_id,
                content_field="structured_analysis",
                content_data=structured_analysis
            )
            
            await self.repository.update_lecture_status(
                lecture_id=lecture_id,
                status_field="analysis_status",
                status_value="completed"
            )
            
            # Clear any previous errors
            await self.repository.clear_lecture_error(
                lecture_id=lecture_id,
                error_key="analysis_error"
            )
            
            logger.info(f"Successfully completed structured analysis for lecture {lecture_id}")
            return {
                "success": True,
                "message": "Structured analysis completed",
                "lecture_id": lecture_id
            }
            
        except Exception as e:
            logger.error(f"Error generating structured analysis for lecture {lecture_id}: {str(e)}")
            
            # Update lecture with error
            try:
                await self.repository.update_lecture_status(
                    lecture_id=lecture_id,
                    status_field="analysis_status",
                    status_value="failed"
                )
                
                error_data = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.repository.update_lecture_error(
                    lecture_id=lecture_id,
                    error_key="analysis_error",
                    error_data=error_data
                )
            except Exception as commit_error:
                logger.error(f"Failed to update error status: {str(commit_error)}")
            
            return {
                "success": False,
                "message": f"Failed to generate structured analysis: {str(e)}",
                "lecture_id": lecture_id
            }
