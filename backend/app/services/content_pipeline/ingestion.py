"""Ingestion service for uploading PDFs to R2 and creating database records."""

import logging
import boto3
from typing import List, Dict, Any
from botocore.exceptions import ClientError

from app.config import settings
from app.repositories.content_repository import ContentRepository

logger = logging.getLogger(__name__)


class IngestionService:
    """Service for handling course and lecture ingestion."""
    
    def __init__(self, repository: ContentRepository):
        """
        Initialize ingestion service.
        
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
    
    def upload_pdf_to_r2(
        self,
        file_content: bytes,
        course_code: str,
        filename: str
    ) -> str:
        """
        Upload a PDF file to Cloudflare R2.
        
        Args:
            file_content: PDF file content as bytes
            course_code: Course identifier
            filename: Original filename
            
        Returns:
            str: R2 path where the file was uploaded
        """
        try:
            # Sanitize filename (replace spaces with underscores)
            safe_filename = filename.replace(" ", "_")
            
            # Construct R2 path
            r2_path = f"docs/course_slides_pdf/{course_code}/{safe_filename}"
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=r2_path,
                Body=file_content,
                ContentType='application/pdf'
            )
            
            logger.info(f"Uploaded PDF to R2: {r2_path}")
            return r2_path
            
        except ClientError as e:
            logger.error(f"Failed to upload PDF to R2: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading PDF: {str(e)}")
            raise
    
    async def ingest_course_with_lectures(
        self,
        course_metadata: Dict[str, Any],
        pdf_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Complete ingestion workflow: create course and upload all lectures.
        
        Args:
            course_metadata: Dict with course_code, course_name, instructor, etc.
            pdf_files: List of dicts with 'filename' and 'content' keys
            
        Returns:
            Dict with course_id and list of lecture_ids
        """
        try:
            course_code = course_metadata['course_code']
            
            # Check if course exists
            existing_course = await self.repository.get_course_by_code(course_code)
            
            if existing_course:
                # Update existing course
                course = await self.repository.update_course(
                    course_code=course_code,
                    course_name=course_metadata['course_name'],
                    instructor=course_metadata.get('instructor'),
                    additional_info=course_metadata.get('additional_info'),
                    reference_textbooks=course_metadata.get('reference_textbooks', [])
                )
                logger.info(f"Updated existing course: {course_code}")
            else:
                # Create new course
                course = await self.repository.create_course(
                    course_code=course_code,
                    course_name=course_metadata['course_name'],
                    instructor=course_metadata.get('instructor'),
                    additional_info=course_metadata.get('additional_info'),
                    reference_textbooks=course_metadata.get('reference_textbooks', [])
                )
                logger.info(f"Created new course: {course_code}")
            
            # Process each PDF
            lecture_ids = []
            for pdf_file in pdf_files:
                # Upload to R2
                r2_path = self.upload_pdf_to_r2(
                    file_content=pdf_file['content'],
                    course_code=course_code,
                    filename=pdf_file['filename']
                )
                
                # Create lecture record
                lecture = await self.repository.create_lecture(
                    course_code=course_code,
                    lecture_title=pdf_file['filename'],
                    r2_pdf_path=r2_path
                )
                
                lecture_ids.append(lecture['id'])
            
            logger.info(
                f"Successfully ingested course {course_code} with {len(lecture_ids)} lectures"
            )
            
            return {
                "course_id": course['id'],
                "course_code": course['course_code'],
                "lecture_ids": lecture_ids
            }
            
        except Exception as e:
            logger.error(f"Error in ingestion workflow: {str(e)}")
            raise


# Create singleton instance function
def create_ingestion_service(repository: ContentRepository) -> IngestionService:
    """
    Factory function to create ingestion service.
    
    Args:
        repository: Content repository
        
    Returns:
        IngestionService instance
    """
    return IngestionService(repository)
