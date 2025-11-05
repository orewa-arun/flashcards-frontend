"""Service layer for user profiles and course enrollment."""

import logging
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for managing user profiles and course enrollment."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.user_profiles
    
    async def initialize_indexes(self):
        """Create indexes for efficient querying."""
        await self.collection.create_index("user_id", unique=True)
        logger.info("User profile indexes created")
    
    async def get_profile(self, user_id: str) -> Optional[dict]:
        """
        Get user profile with enrolled courses.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Profile document or None if not found
        """
        profile = await self.collection.find_one({"user_id": user_id})
        return profile
    
    async def get_enrolled_courses(self, user_id: str) -> List[str]:
        """
        Get list of course IDs the user is enrolled in.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            List of course IDs
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return []
        return profile.get('enrolled_courses', [])
    
    async def enroll_course(self, user_id: str, course_id: str) -> bool:
        """
        Enroll user in a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier to enroll in
            
        Returns:
            True if successful
        """
        try:
            result = await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$addToSet": {"enrolled_courses": course_id}  # $addToSet prevents duplicates
                },
                upsert=True
            )
            
            logger.info(f"✅ User {user_id} enrolled in course {course_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error enrolling user {user_id} in course {course_id}: {e}")
            return False
    
    async def unenroll_course(self, user_id: str, course_id: str) -> bool:
        """
        Unenroll user from a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier to unenroll from
            
        Returns:
            True if successful
        """
        try:
            result = await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$pull": {"enrolled_courses": course_id}
                }
            )
            
            logger.info(f"User {user_id} unenrolled from course {course_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error unenrolling user {user_id} from course {course_id}: {e}")
            return False
    
    async def is_enrolled(self, user_id: str, course_id: str) -> bool:
        """
        Check if user is enrolled in a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier
            
        Returns:
            True if enrolled, False otherwise
        """
        enrolled_courses = await self.get_enrolled_courses(user_id)
        return course_id in enrolled_courses

