"""Authentication and user management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ..firebase_auth import get_current_user
from ..services.user_service import get_user_service, UserService
from ..models.user import UserSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/me", response_model=UserSummary)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current authenticated user information.
    
    Returns:
        UserSummary: Current user's profile and statistics
    """
    try:
        # Get or create user in database
        user = await user_service.get_or_create_user(
            firebase_uid=current_user["uid"],
            email=current_user.get("email"),
            name=current_user.get("name"),
            picture=current_user.get("picture"),
            email_verified=current_user.get("email_verified", False)
        )
        
        # Return user summary
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
        
    except Exception as e:
        logger.error(f"Error getting current user info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
        )

@router.post("/verify")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verify authentication token and return basic user info.
    
    Returns:
        Dict: Basic user information from Firebase token
    """
    return {
        "uid": current_user["uid"],
        "email": current_user.get("email"),
        "name": current_user.get("name"),
        "email_verified": current_user.get("email_verified", False),
        "message": "Token is valid"
    }

@router.delete("/user")
async def delete_user_data(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete all user data (GDPR compliance).
    Note: This only deletes data from our database, not from Firebase Auth.
    
    Returns:
        Dict: Confirmation message
    """
    try:
        firebase_uid = current_user["uid"]
        
        # Delete user from database
        result = await user_service.collection.delete_one({"firebase_uid": firebase_uid})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted user data for Firebase UID: {firebase_uid}")
            return {"message": "User data deleted successfully"}
        else:
            return {"message": "No user data found to delete"}
            
    except Exception as e:
        logger.error(f"Error deleting user data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user data"
        )
