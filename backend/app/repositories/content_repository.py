"""
Content repository - Plain SQL queries for course and lecture data access.
Provides a clean abstraction layer over the database.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncpg

logger = logging.getLogger(__name__)


class ContentRepository:
    """Repository for content-related database operations using plain SQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Course Operations ====================
    
    async def create_course(
        self,
        course_code: str,
        course_name: str,
        instructor: Optional[str] = None,
        additional_info: Optional[str] = None,
        reference_textbooks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new course.
        
        Returns:
            Dict with course data including generated ID
        """
        query = """
            INSERT INTO courses (
                course_code, course_name, instructor, 
                additional_info, reference_textbooks, 
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
            RETURNING id, course_code, course_name, instructor, 
                      additional_info, reference_textbooks, 
                      created_at, updated_at
        """
        
        now = datetime.utcnow()
        # Convert list to JSON string for JSONB column
        textbooks_json = json.dumps(reference_textbooks or [])
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                course_code,
                course_name,
                instructor,
                additional_info,
                textbooks_json,
                now,
                now
            )
            return dict(row)
    
    async def update_course(
        self,
        course_code: str,
        course_name: str,
        instructor: Optional[str] = None,
        additional_info: Optional[str] = None,
        reference_textbooks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update an existing course."""
        query = """
            UPDATE courses
            SET course_name = $2,
                instructor = $3,
                additional_info = $4,
                reference_textbooks = $5::jsonb,
                updated_at = $6
            WHERE course_code = $1
            RETURNING id, course_code, course_name, instructor,
                      additional_info, reference_textbooks,
                      created_at, updated_at
        """
        
        now = datetime.utcnow()
        # Convert list to JSON string for JSONB column
        textbooks_json = json.dumps(reference_textbooks or [])
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                course_code,
                course_name,
                instructor,
                additional_info,
                textbooks_json,
                now
            )
            return dict(row) if row else None
    
    async def get_course_by_code(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get course by course_code."""
        query = """
            SELECT id, course_code, course_name, instructor,
                   additional_info, reference_textbooks, course_repository_link,
                   repository_created_by, created_at, updated_at
            FROM courses
            WHERE course_code = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, course_code)
            return dict(row) if row else None
    
    async def list_courses(self, college: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all courses with lecture counts.
        
        Args:
            college: Optional college filter. If provided, only returns courses for that college.
        """
        base_query = """
            SELECT c.id, c.course_code, c.course_name, c.instructor,
                   c.additional_info, c.reference_textbooks, c.course_repository_link,
                   c.repository_created_by, c.college, c.created_at, c.updated_at,
                   COUNT(l.id) FILTER (WHERE l.is_deleted IS NULL OR l.is_deleted = FALSE) as lecture_count
            FROM courses c
            LEFT JOIN lectures l ON c.course_code = l.course_code
        """
        
        group_by = """
            GROUP BY c.id, c.course_code, c.course_name, c.instructor,
                     c.additional_info, c.reference_textbooks, c.course_repository_link,
                     c.repository_created_by, c.college, c.created_at, c.updated_at
            ORDER BY c.created_at DESC
        """
        
        async with self.pool.acquire() as conn:
            if college:
                # Filter by college
                query = base_query + " WHERE c.college = $1 " + group_by
                rows = await conn.fetch(query, college)
            else:
                # Return all courses
                query = base_query + group_by
                rows = await conn.fetch(query)
            
            return [dict(row) for row in rows]
    
    async def update_course_repository(
        self,
        course_code: str,
        repository_link: str,
        updated_by_name: str,
        updated_by_uid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update the course repository link and log the change to history.
        
        Uses a transaction to ensure both the course update and history
        insertion succeed or fail together.
        
        Args:
            course_code: Course code to update
            repository_link: The drive/repository link
            updated_by_name: Display name of the user who made the update
            updated_by_uid: Firebase UID of the user (for audit trail)
            
        Returns:
            Updated course dict or None if course not found
        """
        update_course_query = """
            UPDATE courses
            SET course_repository_link = $2,
                repository_created_by = $3,
                updated_at = $4
            WHERE course_code = $1
            RETURNING id, course_code, course_name, instructor,
                      additional_info, reference_textbooks, course_repository_link,
                      repository_created_by, created_at, updated_at
        """
        
        insert_history_query = """
            INSERT INTO course_repository_history (
                course_code, repository_link, updated_by_name, updated_by_uid, updated_at
            )
            VALUES ($1, $2, $3, $4, $5)
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            # Use a transaction to ensure both operations succeed or fail together
            async with conn.transaction():
                # Update the course with the new repository link
                row = await conn.fetchrow(
                    update_course_query, 
                    course_code, 
                    repository_link, 
                    updated_by_name, 
                    now
                )
                
                if row:
                    # Log the change to history
                    await conn.execute(
                        insert_history_query,
                        course_code,
                        repository_link,
                        updated_by_name,
                        updated_by_uid,
                        now
                    )
                    return dict(row)
                
                return None
    
    # ==================== Lecture Operations ====================
    
    async def create_lecture(
        self,
        course_code: str,
        lecture_title: str,
        r2_pdf_path: str
    ) -> Dict[str, Any]:
        """
        Create a new lecture with pending statuses.
        
        Returns:
            Dict with lecture data including generated ID
        """
        query = """
            INSERT INTO lectures (
                course_code, lecture_title, r2_pdf_path,
                analysis_status, flashcard_status, quiz_status, qdrant_status,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, 'pending', 'pending', 'pending', 'pending', $4, $5)
            RETURNING id, course_code, lecture_title, r2_pdf_path,
                      structured_analysis, consolidated_structured_analysis,
                      flashcards, quizzes,
                      analysis_status, flashcard_status, quiz_status, qdrant_status,
                      error_log, created_at, updated_at
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                course_code,
                lecture_title,
                r2_pdf_path,
                now,
                now
            )
            return dict(row)
    
    async def get_lecture_by_id(self, lecture_id: int) -> Optional[Dict[str, Any]]:
        """Get lecture by ID."""
        query = """
            SELECT id, course_code, lecture_title, r2_pdf_path,
                   structured_analysis, consolidated_structured_analysis,
                   flashcards, quizzes,
                   analysis_status, flashcard_status, quiz_status, qdrant_status,
                   error_log, created_at, updated_at
            FROM lectures
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id)
            return dict(row) if row else None
    
    async def list_lectures(
        self,
        course_code: Optional[str] = None,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List lectures, optionally filtered by course_code.
        
        Args:
            course_code: Optional course code to filter by
            include_deleted: Whether to include soft-deleted lectures (default: False)
        """
        if course_code:
            if include_deleted:
                query = """
                    SELECT id, course_code, lecture_title, r2_pdf_path,
                           structured_analysis, consolidated_structured_analysis,
                           flashcards, quizzes,
                           analysis_status, flashcard_status, quiz_status, qdrant_status,
                           error_log, is_deleted, created_at, updated_at
                    FROM lectures
                    WHERE course_code = $1
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT id, course_code, lecture_title, r2_pdf_path,
                           structured_analysis, consolidated_structured_analysis,
                           flashcards, quizzes,
                           analysis_status, flashcard_status, quiz_status, qdrant_status,
                           error_log, is_deleted, created_at, updated_at
                    FROM lectures
                    WHERE course_code = $1
                      AND (is_deleted IS NULL OR is_deleted = FALSE)
                    ORDER BY created_at DESC
                """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, course_code)
        else:
            if include_deleted:
                query = """
                    SELECT id, course_code, lecture_title, r2_pdf_path,
                           structured_analysis, consolidated_structured_analysis,
                           flashcards, quizzes,
                           analysis_status, flashcard_status, quiz_status, qdrant_status,
                           error_log, is_deleted, created_at, updated_at
                    FROM lectures
                    ORDER BY created_at DESC
                """
            else:
                query = """
                    SELECT id, course_code, lecture_title, r2_pdf_path,
                           structured_analysis, consolidated_structured_analysis,
                           flashcards, quizzes,
                           analysis_status, flashcard_status, quiz_status, qdrant_status,
                           error_log, is_deleted, created_at, updated_at
                    FROM lectures
                    WHERE is_deleted IS NULL OR is_deleted = FALSE
                    ORDER BY created_at DESC
                """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
        
        return [dict(row) for row in rows]
    
    # ==================== Status Update Operations ====================
    
    async def update_lecture_status(
        self,
        lecture_id: int,
        status_field: str,
        status_value: str
    ) -> bool:
        """
        Update a specific status field for a lecture.
        
        Args:
            lecture_id: Lecture ID
            status_field: One of: analysis_status, flashcard_status, quiz_status, qdrant_status
            status_value: One of: pending, in_progress, completed, failed
            
        Returns:
            True if updated, False if lecture not found
        """
        # Validate status field
        valid_fields = ['analysis_status', 'flashcard_status', 'quiz_status', 'qdrant_status']
        if status_field not in valid_fields:
            raise ValueError(f"Invalid status field: {status_field}")
        
        query = f"""
            UPDATE lectures
            SET {status_field} = $2,
                updated_at = $3
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, status_value, now)
            return row is not None
    
    async def update_lecture_content(
        self,
        lecture_id: int,
        content_field: str,
        content_data: Dict[str, Any]
    ) -> bool:
        """
        Update a content field (structured_analysis, flashcards, or quizzes).
        
        Args:
            lecture_id: Lecture ID
            content_field: One of: structured_analysis, flashcards, quizzes
            content_data: JSON data to store
            
        Returns:
            True if updated, False if lecture not found
        """
        valid_fields = ['structured_analysis', 'consolidated_structured_analysis', 'flashcards', 'quizzes']
        if content_field not in valid_fields:
            raise ValueError(f"Invalid content field: {content_field}")
        
        query = f"""
            UPDATE lectures
            SET {content_field} = $2::jsonb,
                updated_at = $3
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        # Convert dict to JSON string for JSONB column
        content_json = json.dumps(content_data)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, content_json, now)
            return row is not None
    
    async def update_lecture_error(
        self,
        lecture_id: int,
        error_key: str,
        error_data: Dict[str, Any]
    ) -> bool:
        """
        Update or add an error in the error_log.
        
        Args:
            lecture_id: Lecture ID
            error_key: Error key (e.g., 'analysis_error', 'flashcard_error')
            error_data: Error details dict
            
        Returns:
            True if updated
        """
        query = """
            UPDATE lectures
            SET error_log = COALESCE(error_log, '{}'::jsonb) || $2::jsonb,
                updated_at = $3
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        # Convert dict to JSON string before inserting into JSONB
        error_json = json.dumps({error_key: error_data})
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, error_json, now)
            return row is not None
    
    async def clear_lecture_error(
        self,
        lecture_id: int,
        error_key: str
    ) -> bool:
        """
        Clear a specific error from error_log.
        
        Args:
            lecture_id: Lecture ID
            error_key: Error key to remove
            
        Returns:
            True if updated
        """
        query = """
            UPDATE lectures
            SET error_log = error_log - $2,
                updated_at = $3
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, error_key, now)
            return row is not None
    
    # ==================== Query Operations ====================
    
    async def get_lectures_by_status(
        self,
        status_field: str,
        status_value: str
    ) -> List[Dict[str, Any]]:
        """
        Get all lectures with a specific status.
        
        Args:
            status_field: Status field to filter on
            status_value: Status value to match
            
        Returns:
            List of lecture dicts
        """
        valid_fields = ['analysis_status', 'flashcard_status', 'quiz_status', 'qdrant_status']
        if status_field not in valid_fields:
            raise ValueError(f"Invalid status field: {status_field}")
        
        query = f"""
            SELECT id, course_code, lecture_title, r2_pdf_path,
                   structured_analysis, consolidated_structured_analysis,
                   flashcards, quizzes,
                   analysis_status, flashcard_status, quiz_status, qdrant_status,
                   error_log, created_at, updated_at
            FROM lectures
            WHERE {status_field} = $1
              AND (is_deleted IS NULL OR is_deleted = FALSE)
            ORDER BY created_at ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, status_value)
            return [dict(row) for row in rows]
    
    # ==================== Delete Operations ====================
    
    async def mark_lecture_deleted(self, lecture_id: int) -> bool:
        """
        Soft delete a lecture by setting is_deleted = TRUE.
        
        Args:
            lecture_id: ID of the lecture to delete
            
        Returns:
            True if deleted, False if lecture not found
        """
        query = """
            UPDATE lectures
            SET is_deleted = TRUE,
                updated_at = $2
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, now)
            return row is not None
    
    async def restore_lecture(self, lecture_id: int) -> bool:
        """
        Restore a soft-deleted lecture by setting is_deleted = FALSE.
        
        Args:
            lecture_id: ID of the lecture to restore
            
        Returns:
            True if restored, False if lecture not found
        """
        query = """
            UPDATE lectures
            SET is_deleted = FALSE,
                updated_at = $2
            WHERE id = $1
            RETURNING id
        """
        
        now = datetime.utcnow()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, lecture_id, now)
            return row is not None

