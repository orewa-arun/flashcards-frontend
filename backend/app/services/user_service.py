"""User service for managing user data and authentication using PostgreSQL."""

from datetime import datetime, timezone
from typing import Optional
import asyncpg
import logging

from app.repositories.user_repository import UserRepository
from app.models.user import User, UserCreate, UserSummary

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user operations using PostgreSQL."""
    
    def __init__(self, pool: asyncpg.Pool):
        """
        Initialize service with PostgreSQL connection pool.
        
        Args:
            pool: AsyncPG connection pool
        """
        self.pool = pool
        self.repository = UserRepository(pool)
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Get user by Firebase UID.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user_dict = await self.repository.get_user_by_firebase_uid(firebase_uid)
            if user_dict:
                return User(**user_dict)
            return None
        except Exception as e:
            logger.error(f"Error fetching user by Firebase UID {firebase_uid}: {e}")
            raise
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created User object
        """
        try:
            user_dict = await self.repository.create_user(
                firebase_uid=user_data.firebase_uid,
                email=user_data.email,
                name=user_data.name,
                picture=user_data.picture,
                email_verified=user_data.email_verified
            )
            
            logger.info(f"Created new user with Firebase UID: {user_data.firebase_uid}")
            return User(**user_dict)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def update_last_active(self, firebase_uid: str) -> bool:
        """
        Update user's last active timestamp.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            return await self.repository.update_last_active(firebase_uid)
        except Exception as e:
            logger.error(f"Error updating last active for user {firebase_uid}: {e}")
            return False
    
    async def get_or_create_user(
        self,
        firebase_uid: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: bool = False
    ) -> User:
        """
        Get existing user or create new one if doesn't exist.
        
        Args:
            firebase_uid: Firebase UID
            email: User's email
            name: User's display name
            picture: User's profile picture URL
            email_verified: Whether email is verified
            
        Returns:
            User object (existing or newly created)
        """
        try:
            # Try to get existing user
            user = await self.get_user_by_firebase_uid(firebase_uid)
            
            if user:
                # Update last active timestamp
                await self.update_last_active(firebase_uid)
                
                # Check if we need to update user info
                needs_update = False
                if email and user.email != email:
                    needs_update = True
                if name and user.name != name:
                    needs_update = True
                if picture and user.picture != picture:
                    needs_update = True
                if email_verified != user.email_verified:
                    needs_update = True
                
                if needs_update:
                    updated_dict = await self.repository.update_user(
                        firebase_uid=firebase_uid,
                        email=email if email and user.email != email else None,
                        name=name if name and user.name != name else None,
                        picture=picture if picture and user.picture != picture else None,
                        email_verified=email_verified if email_verified != user.email_verified else None
                    )
                    if updated_dict:
                        logger.info(f"Updated user info for Firebase UID: {firebase_uid}")
                        return User(**updated_dict)
                
                return user
            else:
                # Create new user
                user_data = UserCreate(
                    firebase_uid=firebase_uid,
                    email=email,
                    name=name,
                    picture=picture,
                    email_verified=email_verified
                )
                return await self.create_user(user_data)
                
        except Exception as e:
            logger.error(f"Error in get_or_create_user for Firebase UID {firebase_uid}: {e}")
            raise
    
    async def increment_decks_studied(self, firebase_uid: str) -> bool:
        """
        Increment the total decks studied counter for a user.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            return await self.repository.increment_stats(firebase_uid, decks_studied=1)
        except Exception as e:
            logger.error(f"Error incrementing decks studied for user {firebase_uid}: {e}")
            return False
    
    async def increment_quiz_attempts(self, firebase_uid: str) -> bool:
        """
        Increment the total quiz attempts counter for a user.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            return await self.repository.increment_stats(firebase_uid, quiz_attempts=1)
        except Exception as e:
            logger.error(f"Error incrementing quiz attempts for user {firebase_uid}: {e}")
            return False
    
    async def get_user_summary(self, firebase_uid: str) -> Optional[UserSummary]:
        """
        Get user summary for API responses.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            UserSummary object if user found, None otherwise
        """
        try:
            user = await self.get_user_by_firebase_uid(firebase_uid)
            if user:
                return UserSummary(
                    firebase_uid=user.firebase_uid,
                    email=user.email,
                    name=user.name,
                    picture=user.picture,
                    total_decks_studied=user.total_decks_studied,
                    total_quiz_attempts=user.total_quiz_attempts,
                    created_at=user.created_at,
                    last_active=user.last_active
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user summary for Firebase UID {firebase_uid}: {e}")
            raise


async def get_user_service() -> UserService:
    """Get user service instance with PostgreSQL pool."""
    from app.db.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    return UserService(pool)
