"""Service layer for user profiles and course enrollment using PostgreSQL."""

import logging
from typing import Optional, List
import asyncpg

from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for managing user profiles and course enrollment using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.repository = UserRepository(pool)
    
    async def get_profile(self, user_id: str) -> Optional[dict]:
        """
        Get user profile with enrolled courses.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Profile document or None if not found
        """
        return await self.repository.get_profile(user_id)
    
    async def get_enrolled_courses(self, user_id: str) -> List[str]:
        """
        Get list of course IDs the user is enrolled in.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            List of course IDs
        """
        return await self.repository.get_enrolled_courses(user_id)
    
    async def enroll_course(self, user_id: str, course_id: str) -> bool:
        """
        Enroll user in a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier to enroll in
            
        Returns:
            True if successful
        """
        success = await self.repository.enroll_course(user_id, course_id)
        
        if success:
            logger.info(f"User {user_id} enrolled in course {course_id}")
        
        return success
    
    async def unenroll_course(self, user_id: str, course_id: str) -> bool:
        """
        Unenroll user from a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier to unenroll from
            
        Returns:
            True if successful
        """
        success = await self.repository.unenroll_course(user_id, course_id)
        
        if success:
            logger.info(f"User {user_id} unenrolled from course {course_id}")
        
        return success
    
    async def is_enrolled(self, user_id: str, course_id: str) -> bool:
        """
        Check if user is enrolled in a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier
            
        Returns:
            True if enrolled, False otherwise
        """
        return await self.repository.is_enrolled(user_id, course_id)


async def get_user_profile_service() -> UserProfileService:
    """Get user profile service instance with PostgreSQL pool."""
    from app.db.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    return UserProfileService(pool)
