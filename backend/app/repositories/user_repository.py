"""
User repository - PostgreSQL queries for user and profile data access.
Handles users table (Firebase users) and user_profiles table (course enrollment).
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncpg

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize repository with connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
    
    # ==================== Users Table Operations ====================
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by their Firebase UID.
        
        Args:
            firebase_uid: Firebase user ID
            
        Returns:
            User dict or None if not found
        """
        query = """
            SELECT 
                id, firebase_uid, email, name, picture, email_verified,
                total_decks_studied, total_quiz_attempts, created_at, last_active
            FROM users
            WHERE firebase_uid = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, firebase_uid)
            
            if not row:
                return None
            
            return dict(row)
    
    async def create_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            firebase_uid: Firebase user ID
            email: User's email
            name: User's display name
            picture: URL to profile picture
            email_verified: Whether email is verified
            
        Returns:
            Created user dict
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO users (
                firebase_uid, email, name, picture, email_verified,
                total_decks_studied, total_quiz_attempts, created_at, last_active
            )
            VALUES ($1, $2, $3, $4, $5, 0, 0, $6, $6)
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                firebase_uid, email, name, picture, email_verified, now
            )
            
            logger.info(f"Created user {firebase_uid}")
            return dict(row)
    
    async def get_or_create_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: bool = False
    ) -> Dict[str, Any]:
        """
        Get existing user or create new one.
        
        Args:
            firebase_uid: Firebase user ID
            email: User's email
            name: User's display name
            picture: URL to profile picture
            email_verified: Whether email is verified
            
        Returns:
            User dict
        """
        user = await self.get_user_by_firebase_uid(firebase_uid)
        
        if user:
            # Update last_active
            await self.update_last_active(firebase_uid)
            return user
        
        return await self.create_user(
            firebase_uid=firebase_uid,
            email=email,
            name=name,
            picture=picture,
            email_verified=email_verified
        )
    
    async def update_last_active(self, firebase_uid: str) -> bool:
        """
        Update user's last_active timestamp.
        
        Args:
            firebase_uid: Firebase user ID
            
        Returns:
            True if updated
        """
        now = datetime.now(timezone.utc)
        
        query = """
            UPDATE users
            SET last_active = $2
            WHERE firebase_uid = $1
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, firebase_uid, now)
            return row is not None
    
    async def update_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user fields.
        
        Args:
            firebase_uid: Firebase user ID
            email: New email (optional)
            name: New name (optional)
            picture: New picture URL (optional)
            email_verified: New verified status (optional)
            
        Returns:
            Updated user dict or None if not found
        """
        # Build dynamic update query
        updates = []
        params = [firebase_uid]
        param_idx = 2
        
        if email is not None:
            updates.append(f"email = ${param_idx}")
            params.append(email)
            param_idx += 1
        
        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1
        
        if picture is not None:
            updates.append(f"picture = ${param_idx}")
            params.append(picture)
            param_idx += 1
        
        if email_verified is not None:
            updates.append(f"email_verified = ${param_idx}")
            params.append(email_verified)
            param_idx += 1
        
        if not updates:
            return await self.get_user_by_firebase_uid(firebase_uid)
        
        updates.append(f"last_active = ${param_idx}")
        params.append(datetime.now(timezone.utc))
        
        query = f"""
            UPDATE users
            SET {', '.join(updates)}
            WHERE firebase_uid = $1
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            
            if not row:
                return None
            
            return dict(row)
    
    async def increment_stats(
        self,
        firebase_uid: str,
        decks_studied: int = 0,
        quiz_attempts: int = 0
    ) -> bool:
        """
        Increment user statistics.
        
        Args:
            firebase_uid: Firebase user ID
            decks_studied: Number of decks to add
            quiz_attempts: Number of quiz attempts to add
            
        Returns:
            True if updated
        """
        query = """
            UPDATE users
            SET 
                total_decks_studied = total_decks_studied + $2,
                total_quiz_attempts = total_quiz_attempts + $3,
                last_active = $4
            WHERE firebase_uid = $1
            RETURNING id
        """
        
        now = datetime.now(timezone.utc)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, firebase_uid, decks_studied, quiz_attempts, now)
            return row is not None
    
    # ==================== User Profiles Table Operations ====================
    
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile with enrolled courses.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Profile dict or None if not found
        """
        query = """
            SELECT id, user_id, enrolled_courses, preferences, created_at, updated_at
            FROM user_profiles
            WHERE user_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            if not row:
                return None
            
            result = dict(row)
            # Parse JSONB fields
            if isinstance(result.get("enrolled_courses"), str):
                result["enrolled_courses"] = json.loads(result["enrolled_courses"])
            if isinstance(result.get("preferences"), str):
                result["preferences"] = json.loads(result["preferences"])
            
            return result
    
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
        
        return profile.get("enrolled_courses", [])
    
    async def enroll_course(self, user_id: str, course_id: str) -> bool:
        """
        Enroll user in a course.
        
        Args:
            user_id: Firebase user ID
            course_id: Course identifier to enroll in
            
        Returns:
            True if successful
        """
        now = datetime.now(timezone.utc)
        
        # Use JSONB array append with deduplication
        query = """
            INSERT INTO user_profiles (user_id, enrolled_courses, created_at, updated_at)
            VALUES ($1, $2::jsonb, $3, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET
                enrolled_courses = (
                    SELECT jsonb_agg(DISTINCT elem)
                    FROM (
                        SELECT jsonb_array_elements(user_profiles.enrolled_courses) AS elem
                        UNION
                        SELECT $4::jsonb AS elem
                    ) sub
                ),
                updated_at = $3
            RETURNING id
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    user_id,
                    json.dumps([course_id]),
                    now,
                    json.dumps(course_id)
                )
                
                logger.info(f"User {user_id} enrolled in course {course_id}")
                return row is not None
        
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
        now = datetime.now(timezone.utc)
        
        # Remove course_id from JSONB array
        query = """
            UPDATE user_profiles
            SET 
                enrolled_courses = (
                    SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
                    FROM jsonb_array_elements(enrolled_courses) AS elem
                    WHERE elem != $2::jsonb
                ),
                updated_at = $3
            WHERE user_id = $1
            RETURNING id
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, json.dumps(course_id), now)
                
                logger.info(f"User {user_id} unenrolled from course {course_id}")
                return row is not None
        
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
    
    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences.
        
        Args:
            user_id: Firebase user ID
            preferences: Preferences dict to merge
            
        Returns:
            True if successful
        """
        now = datetime.now(timezone.utc)
        
        query = """
            INSERT INTO user_profiles (user_id, preferences, created_at, updated_at)
            VALUES ($1, $2::jsonb, $3, $3)
            ON CONFLICT (user_id)
            DO UPDATE SET
                preferences = user_profiles.preferences || $2::jsonb,
                updated_at = $3
            RETURNING id
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, user_id, json.dumps(preferences), now)
                return row is not None
        
        except Exception as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False


