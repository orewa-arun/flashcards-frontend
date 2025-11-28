"""API endpoints for course exam timetables using PostgreSQL."""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.postgres import get_postgres_pool
from app.firebase_auth import get_current_user
from app.services.timetable_service import TimetableService
from app.services.user_profile_service import UserProfileService
from app.services.readiness_v2_service import ReadinessV2Service
from app.models.readiness_v2 import UserExamReadiness

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/timetables", tags=["timetables"])


@router.get("/my-schedule")
async def get_my_aggregated_schedule(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated exam schedule for all courses the user is enrolled in.
    
    This endpoint:
    1. Fetches the user's enrolled courses
    2. Gets timetables for all those courses
    3. Aggregates all exams into a single list
    4. Converts all dates to IST
    5. Sorts chronologically
    
    Returns:
        Aggregated schedule with exams from all enrolled courses
    """
    try:
        user_id = current_user['uid']
        
        pool = await get_postgres_pool()
        profile_service = UserProfileService(pool)
        timetable_service = TimetableService(pool)
        
        # Get user's enrolled courses
        enrolled_courses = await profile_service.get_enrolled_courses(user_id)
        
        if not enrolled_courses:
            return {
                "enrolled_courses": [],
                "exams": [],
                "message": "Not enrolled in any courses"
            }
        
        # Fetch timetables for all enrolled courses
        all_exams = []
        
        for course_id in enrolled_courses:
            timetable = await timetable_service.get_timetable(course_id)
            
            if timetable and timetable.get('exams'):
                # Add course_id to each exam for display purposes
                for exam in timetable['exams']:
                    exam['course_id'] = course_id
                    all_exams.append(exam)
        
        # Sort exams chronologically by date_ist
        if all_exams:
            try:
                all_exams.sort(key=lambda x: x.get('date_ist', ''))
            except Exception as e:
                logger.warning(f"Could not sort exams: {e}")
        
        logger.info(f"Aggregated schedule for user {user_id}: {len(all_exams)} exams from {len(enrolled_courses)} courses")
        
        return {
            "enrolled_courses": enrolled_courses,
            "exams": all_exams,
            "total_exams": len(all_exams)
        }
    
    except Exception as e:
        logger.error(f"Error fetching aggregated schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch schedule: {str(e)}"
        )


@router.get("/{course_id}")
async def get_course_timetable(
    course_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get exam timetable for a course.
    
    All dates are returned in IST format for display.
    
    Args:
        course_id: Course identifier (e.g., "MS5031")
        current_user: Authenticated user from Firebase
        
    Returns:
        Timetable document with exams and last update info
    """
    try:
        pool = await get_postgres_pool()
        timetable_service = TimetableService(pool)
        
        timetable = await timetable_service.get_timetable(course_id)
        
        if not timetable:
            # Return empty timetable structure if none exists
            return {
                "course_id": course_id,
                "exams": [],
                "last_updated_by": None
            }
        
        return timetable
    
    except Exception as e:
        logger.error(f"Error fetching timetable for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch timetable: {str(e)}"
        )


@router.put("/{course_id}")
async def update_course_timetable(
    course_id: str,
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update exam timetable for a course.
    
    Frontend sends dates in IST format, backend converts to UTC for storage.
    
    Args:
        course_id: Course identifier
        request: Dictionary with 'exams' list containing exam data
        current_user: Authenticated user from Firebase
        
    Returns:
        Success message with updated timetable
    """
    try:
        user_id = current_user['uid']
        user_name = current_user.get('name') or current_user.get('email', 'Unknown User')
        
        # Extract exams from request
        exams = request.get('exams', [])
        
        if not isinstance(exams, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'exams' must be a list"
            )
        
        pool = await get_postgres_pool()
        timetable_service = TimetableService(pool)
        
        success = await timetable_service.update_timetable(
            course_id=course_id,
            exams=exams,
            user_id=user_id,
            user_name=user_name
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update timetable"
            )
        
        # Fetch and return the updated timetable
        updated_timetable = await timetable_service.get_timetable(course_id)
        
        logger.info(f"Timetable updated for course {course_id} by {user_name}")
        
        return {
            "success": True,
            "message": "Timetable updated successfully",
            "timetable": updated_timetable
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating timetable for course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update timetable: {str(e)}"
        )


@router.delete("/{course_id}/exams/{exam_id}")
async def delete_exam_entry(
    course_id: str,
    exam_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete a specific exam entry from a course timetable.
    
    Args:
        course_id: Course identifier
        exam_id: Exam identifier to delete
        current_user: Authenticated user from Firebase
        
    Returns:
        Success message
    """
    try:
        pool = await get_postgres_pool()
        timetable_service = TimetableService(pool)
        
        success = await timetable_service.delete_exam(course_id, exam_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exam {exam_id} not found in course {course_id}"
            )
        
        logger.info(f"Deleted exam {exam_id} from course {course_id}")
        
        return {
            "success": True,
            "message": "Exam deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exam {exam_id} from course {course_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exam: {str(e)}"
        )


@router.get("/{course_id}/exams/{exam_id}/readiness")
async def get_exam_readiness(
    course_id: str,
    exam_id: str,
    current_user: dict = Depends(get_current_user)
) -> UserExamReadiness:
    """
    Get Exam Readiness Score (The Trinity Engine V2).
    
    This endpoint returns the pre-calculated exam readiness score with
    flashcard-level performance tracking. If the score doesn't exist or
    is stale, it triggers an on-demand calculation.
    
    Args:
        course_id: Course identifier (e.g., "MS5031")
        exam_id: Exam identifier from the timetable
        current_user: Authenticated user from Firebase
        
    Returns:
        UserExamReadiness with Trinity breakdown and weak flashcards
    """
    try:
        user_id = current_user['uid']
        
        pool = await get_postgres_pool()
        
        # Initialize the readiness service
        readiness_service = ReadinessV2Service(pool)
        
        # Try to get cached readiness score
        readiness = await readiness_service.get_exam_readiness(user_id, exam_id)
        
        # If not found or stale (older than 5 minutes), recalculate
        if readiness is None:
            logger.info(f"No cached readiness found for user {user_id}, exam {exam_id}. Calculating...")
            readiness = await readiness_service.calculate_and_persist_exam_readiness(
                user_id=user_id,
                course_id=course_id,
                exam_id=exam_id
            )
        else:
            from datetime import datetime, timezone, timedelta
            # Ensure readiness.last_calculated is timezone-aware UTC
            if readiness.last_calculated.tzinfo is None:
                readiness.last_calculated = readiness.last_calculated.replace(tzinfo=timezone.utc)
            
            age = datetime.now(timezone.utc) - readiness.last_calculated
            if age > timedelta(minutes=5):
                logger.info(f"Cached readiness is stale ({age.total_seconds():.0f}s old). Recalculating...")
                readiness = await readiness_service.calculate_and_persist_exam_readiness(
                    user_id=user_id,
                    course_id=course_id,
                    exam_id=exam_id
                )
        
        logger.info(f"Returning readiness for user {user_id}, exam {exam_id}: {readiness.overall_readiness_score:.1f}%")
        
        return readiness
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exam readiness: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exam readiness: {str(e)}"
        )
