"""API endpoints for user profiles and course enrollment."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_database
from app.firebase_auth import get_current_user
from app.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("")
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Get current user's profile with enrolled courses.
    
    Returns:
        User profile with enrolled_courses list
    """
    try:
        user_id = current_user['uid']
        profile_service = UserProfileService(db)
        
        enrolled_courses = await profile_service.get_enrolled_courses(user_id)
        
        return {
            "user_id": user_id,
            "enrolled_courses": enrolled_courses
        }
    
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.post("/enroll/{course_id}")
async def enroll_in_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Enroll current user in a course.
    
    Args:
        course_id: Course identifier to enroll in
        
    Returns:
        Success message with updated enrolled courses list
    """
    try:
        user_id = current_user['uid']
        profile_service = UserProfileService(db)
        
        # Check if already enrolled
        is_enrolled = await profile_service.is_enrolled(user_id, course_id)
        if is_enrolled:
            enrolled_courses = await profile_service.get_enrolled_courses(user_id)
            return {
                "success": True,
                "message": f"Already enrolled in {course_id}",
                "enrolled_courses": enrolled_courses
            }
        
        # Enroll the user
        success = await profile_service.enroll_course(user_id, course_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to enroll in course"
            )
        
        enrolled_courses = await profile_service.get_enrolled_courses(user_id)
        
        logger.info(f"✅ User {user_id} enrolled in course {course_id}")
        
        return {
            "success": True,
            "message": f"Successfully enrolled in {course_id}",
            "enrolled_courses": enrolled_courses
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling in course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll: {str(e)}"
        )


@router.delete("/enroll/{course_id}")
async def unenroll_from_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Unenroll current user from a course.
    
    Args:
        course_id: Course identifier to unenroll from
        
    Returns:
        Success message with updated enrolled courses list
    """
    try:
        user_id = current_user['uid']
        profile_service = UserProfileService(db)
        
        success = await profile_service.unenroll_course(user_id, course_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unenroll from course"
            )
        
        enrolled_courses = await profile_service.get_enrolled_courses(user_id)
        
        logger.info(f"User {user_id} unenrolled from course {course_id}")
        
        return {
            "success": True,
            "message": f"Successfully unenrolled from {course_id}",
            "enrolled_courses": enrolled_courses
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unenrolling from course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unenroll: {str(e)}"
        )


@router.get("/enrollment/{course_id}")
async def check_enrollment_status(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Check if current user is enrolled in a specific course.
    
    Args:
        course_id: Course identifier to check
        
    Returns:
        Enrollment status
    """
    try:
        user_id = current_user['uid']
        profile_service = UserProfileService(db)
        
        is_enrolled = await profile_service.is_enrolled(user_id, course_id)
        
        return {
            "course_id": course_id,
            "is_enrolled": is_enrolled
        }
    
    except Exception as e:
        logger.error(f"Error checking enrollment status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check enrollment: {str(e)}"
        )

