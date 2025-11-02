"""User service for managing user data and authentication."""

from datetime import datetime, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
import logging

from ..models.user import User, UserCreate, UserSummary
from ..database import get_database

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing user operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.users
    
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Get user by Firebase UID.
        
        Args:
            firebase_uid: Firebase UID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user_doc = await self.collection.find_one({"firebase_uid": firebase_uid})
            if user_doc:
                return User(**user_doc)
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
            
        Raises:
            DuplicateKeyError: If user with Firebase UID already exists
        """
        try:
            user = User(
                firebase_uid=user_data.firebase_uid,
                email=user_data.email,
                name=user_data.name,
                picture=user_data.picture,
                email_verified=user_data.email_verified,
                created_at=datetime.now(timezone.utc),
                last_active=datetime.now(timezone.utc)
            )
            
            # Convert to dict for MongoDB insertion
            user_dict = user.model_dump(by_alias=True, exclude={"id"})
            
            # Insert into database
            result = await self.collection.insert_one(user_dict)
            user.id = result.inserted_id
            
            logger.info(f"Created new user with Firebase UID: {user_data.firebase_uid}")
            return user
            
        except DuplicateKeyError:
            logger.warning(f"Attempted to create duplicate user with Firebase UID: {user_data.firebase_uid}")
            raise
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
            result = await self.collection.update_one(
                {"firebase_uid": firebase_uid},
                {"$set": {"last_active": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating last active for user {firebase_uid}: {e}")
            return False
    
    async def get_or_create_user(self, firebase_uid: str, email: Optional[str] = None, 
                                name: Optional[str] = None, picture: Optional[str] = None,
                                email_verified: bool = False) -> User:
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
                
                # Update user info if provided and different
                update_fields = {}
                if email and user.email != email:
                    update_fields["email"] = email
                if name and user.name != name:
                    update_fields["name"] = name
                if picture and user.picture != picture:
                    update_fields["picture"] = picture
                if email_verified != user.email_verified:
                    update_fields["email_verified"] = email_verified
                
                if update_fields:
                    await self.collection.update_one(
                        {"firebase_uid": firebase_uid},
                        {"$set": update_fields}
                    )
                    logger.info(f"Updated user info for Firebase UID: {firebase_uid}")
                
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
            result = await self.collection.update_one(
                {"firebase_uid": firebase_uid},
                {
                    "$inc": {"total_decks_studied": 1},
                    "$set": {"last_active": datetime.now(timezone.utc)}
                }
            )
            return result.modified_count > 0
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
            result = await self.collection.update_one(
                {"firebase_uid": firebase_uid},
                {
                    "$inc": {"total_quiz_attempts": 1},
                    "$set": {"last_active": datetime.now(timezone.utc)}
                }
            )
            return result.modified_count > 0
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

# Dependency to get user service
async def get_user_service() -> UserService:
    """Get user service instance."""
    db = await get_database()
    return UserService(db)
