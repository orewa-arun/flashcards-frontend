"""API endpoints for content management and pipeline operations."""

import logging
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.db.postgres import get_postgres_pool
from app.repositories.content_repository import ContentRepository
from app.repositories.user_repository import UserRepository
from app.services.content_pipeline.orchestrator import create_orchestrator
from app.firebase_auth import get_current_user, verify_firebase_token
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["content"])


# Pydantic models for requests/responses
class IngestionResponse(BaseModel):
    """Response model for ingestion."""
    success: bool
    message: str
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    lecture_ids: Optional[List[int]] = None


class ActionResponse(BaseModel):
    """Response model for pipeline actions."""
    success: bool
    message: str
    lecture_id: int


class LectureStatus(BaseModel):
    """Lecture status model."""
    id: int
    course_code: str
    lecture_title: str
    r2_pdf_path: str
    analysis_status: str
    flashcard_status: str
    quiz_status: str
    qdrant_status: str
    topics: List[str] = []
    error_log: Optional[dict] = None
    created_at: str
    updated_at: str


class CourseDetail(BaseModel):
    """Course detail model."""
    id: int
    course_code: str
    course_name: str
    instructor: Optional[str] = None
    additional_info: Optional[str] = None
    reference_textbooks: Optional[List[str]] = None
    course_repository_link: Optional[str] = None
    repository_created_by: Optional[str] = None
    college: Optional[str] = None
    lecture_count: int = 0
    created_at: str
    updated_at: str


class UpdateRepositoryRequest(BaseModel):
    """Request model for updating course repository."""
    link: str
    # Optional fallback: used if token doesn't contain display name
    user_name: Optional[str] = None


async def get_repository():
    """Dependency to get repository instance."""
    pool = await get_postgres_pool()
    return ContentRepository(pool)


async def get_user_repository():
    """Dependency to get user repository instance."""
    pool = await get_postgres_pool()
    return UserRepository(pool)


# Optional authentication - returns None if no token provided
security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.
    Returns user data if valid token provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        return await verify_firebase_token(credentials)
    except Exception:
        return None


def is_global_admin(email: Optional[str]) -> bool:
    """Check if user email is in global admin list."""
    if not email:
        return False
    return email.lower() in settings.GLOBAL_ADMIN_EMAILS


def extract_topics_from_analysis(structured_analysis: Any) -> List[str]:
    """
    Extract topics from structured_analysis JSONB field.
    
    Tries multiple sources: 'topics', 'key_concepts', 'sections'.
    """
    if not structured_analysis:
        return []
    
    # Handle if it's a string (JSON)
    if isinstance(structured_analysis, str):
        try:
            structured_analysis = json.loads(structured_analysis)
        except json.JSONDecodeError:
            return []
    
    if not isinstance(structured_analysis, dict):
        return []
    
    # Try 'topics' first
    topics = structured_analysis.get("topics")
    if topics and isinstance(topics, list):
        return [str(t) for t in topics if t]
    
    # Try 'key_concepts' as fallback
    key_concepts = structured_analysis.get("key_concepts")
    if key_concepts and isinstance(key_concepts, list):
        return [str(c) for c in key_concepts if c]
    
    # Try 'sections' as last resort (extract section titles)
    sections = structured_analysis.get("sections")
    if sections and isinstance(sections, list):
        return [s.get("title", str(s)) if isinstance(s, dict) else str(s) for s in sections if s]
    
    return []


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_content(
    course_code: str = Form(...),
    course_name: str = Form(...),
    instructor: Optional[str] = Form(None),
    additional_info: Optional[str] = Form(None),
    reference_textbooks: Optional[str] = Form(None),  # JSON string
    pdf_files: List[UploadFile] = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ContentRepository = Depends(get_repository)
):
    """
    Ingest course metadata and lecture PDFs.
    
    Creates course record and uploads PDFs to R2, creating lecture records.
    All lecture statuses are initialized to 'pending'.
    """
    try:
        # Parse reference_textbooks if provided
        textbooks = []
        if reference_textbooks:
            import json
            try:
                textbooks = json.loads(reference_textbooks)
            except json.JSONDecodeError:
                textbooks = [reference_textbooks]
        
        # Prepare course metadata
        course_metadata = {
            "course_code": course_code,
            "course_name": course_name,
            "instructor": instructor,
            "additional_info": additional_info,
            "reference_textbooks": textbooks
        }
        
        # Prepare PDF files
        pdf_data = []
        for pdf_file in pdf_files:
            content = await pdf_file.read()
            pdf_data.append({
                "filename": pdf_file.filename,
                "content": content
            })
        
        # Create orchestrator and run ingestion
        orchestrator = create_orchestrator(repository)
        result = await orchestrator.run_ingestion(
            course_metadata=course_metadata,
            pdf_files=pdf_data
        )
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {len(pdf_data)} lectures",
            course_id=result["course_id"],
            course_code=result["course_code"],
            lecture_ids=result["lecture_ids"]
        )
        
    except Exception as e:
        logger.error(f"Error in ingestion endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{action}/{lecture_id}", response_model=ActionResponse)
async def trigger_action(
    action: str,
    lecture_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ContentRepository = Depends(get_repository)
):
    """
    Trigger a specific pipeline action for a lecture.
    
    Actions: analyze, flashcards, quiz, index
    """
    try:
        # Validate action
        valid_actions = ["analyze", "flashcards", "quiz", "index"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        
        # Create orchestrator and get handler
        orchestrator = create_orchestrator(repository)
        handler = await orchestrator.get_action_handler(action)
        result = await handler(lecture_id=lecture_id)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return ActionResponse(
            success=True,
            message=result["message"],
            lecture_id=lecture_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in action endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ProcessResponse(BaseModel):
    """Response model for process (full pipeline) action."""
    success: bool
    message: str
    lecture_id: int


async def _run_full_pipeline_task(lecture_id: int, repository: ContentRepository):
    """
    Background task to run the full pipeline.
    
    This runs asynchronously after the HTTP response is sent.
    """
    try:
        orchestrator = create_orchestrator(repository)
        result = await orchestrator.run_full_pipeline(lecture_id=lecture_id)
        
        if result["success"]:
            logger.info(f"Background pipeline completed for lecture {lecture_id}")
        else:
            logger.warning(
                f"Background pipeline failed for lecture {lecture_id} at step '{result['failed_step']}': {result['error']}"
            )
    except Exception as e:
        logger.error(f"Background pipeline exception for lecture {lecture_id}: {str(e)}")


@router.post("/process/{lecture_id}", response_model=ProcessResponse)
async def process_lecture(
    lecture_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ContentRepository = Depends(get_repository)
):
    """
    Run the full content pipeline for a lecture in the background.
    
    This triggers all steps (Analysis → Flashcards → Quiz → Indexing) sequentially.
    The request returns immediately; processing continues in the background.
    
    If any step fails, the pipeline stops and logs the error to the lecture record.
    """
    try:
        # Verify lecture exists
        lecture = await repository.get_lecture_by_id(lecture_id)
        if not lecture:
            raise HTTPException(status_code=404, detail=f"Lecture {lecture_id} not found")
        
        # Schedule the pipeline to run in background
        background_tasks.add_task(_run_full_pipeline_task, lecture_id, repository)
        
        logger.info(f"Started background pipeline for lecture {lecture_id}")
        
        return ProcessResponse(
            success=True,
            message="Pipeline started. Processing will continue in the background.",
            lecture_id=lecture_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting pipeline for lecture {lecture_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/courses", response_model=List[CourseDetail])
async def list_courses(
    repository: ContentRepository = Depends(get_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)
):
    """
    List courses with lecture counts.
    
    Filtering logic:
    - Global admins (email in GLOBAL_ADMIN_EMAILS): See all courses
    - Authenticated users: See courses for their college
    - Unauthenticated users: See all courses (public access)
    """
    try:
        college_filter = None
        
        # If user is authenticated, check if they need filtering
        if current_user:
            user_email = current_user.get("email", "")
            
            # Global admins see all courses
            if not is_global_admin(user_email):
                # Get user's college from DB
                user_data = await user_repo.get_user_by_firebase_uid(current_user.get("uid", ""))
                if user_data and user_data.get("college"):
                    college_filter = user_data["college"]
                    logger.info(f"Filtering courses for college: {college_filter}")
        
        courses = await repository.list_courses(college=college_filter)
        
        result = []
        for course in courses:
            # Parse reference_textbooks if it's a JSON string
            textbooks = course.get("reference_textbooks")
            if isinstance(textbooks, str):
                try:
                    textbooks = json.loads(textbooks) if textbooks else []
                except json.JSONDecodeError:
                    textbooks = []
            elif textbooks is None:
                textbooks = []
            
            result.append(
                CourseDetail(
                    id=course["id"],
                    course_code=course["course_code"],
                    course_name=course["course_name"],
                    instructor=course.get("instructor"),
                    additional_info=course.get("additional_info"),
                    reference_textbooks=textbooks,
                    course_repository_link=course.get("course_repository_link"),
                    repository_created_by=course.get("repository_created_by"),
                    college=course.get("college"),
                    lecture_count=course.get("lecture_count", 0),
                    created_at=course["created_at"].isoformat(),
                    updated_at=course["updated_at"].isoformat()
                )
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/courses/{course_code}/repository")
async def update_course_repository(
    course_code: str,
    request: UpdateRepositoryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ContentRepository = Depends(get_repository)
):
    """
    Update the course repository link.
    
    This allows authenticated community members to add or update the shared 
    drive link for a course. The user's identity is extracted from the 
    authentication token for secure attribution and audit logging.
    """
    try:
        # Validate the link is not empty
        if not request.link or not request.link.strip():
            raise HTTPException(status_code=400, detail="Repository link cannot be empty")
        
        # Get user info from authenticated token
        user_uid = current_user.get('uid')
        # Use name from token, fallback to request user_name, then email prefix
        user_name = current_user.get('name') or request.user_name or current_user.get('email', '').split('@')[0] or 'Anonymous'
        
        # Update the repository (also logs to history table)
        updated_course = await repository.update_course_repository(
            course_code=course_code,
            repository_link=request.link.strip(),
            updated_by_name=user_name,
            updated_by_uid=user_uid
        )
        
        if not updated_course:
            raise HTTPException(status_code=404, detail=f"Course {course_code} not found")
        
        return {
            "success": True,
            "message": "Repository link updated successfully",
            "course_repository_link": updated_course.get("course_repository_link"),
            "repository_created_by": updated_course.get("repository_created_by")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating course repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lectures", response_model=List[LectureStatus])
async def list_lectures(
    course_code: Optional[str] = None,
    repository: ContentRepository = Depends(get_repository)
):
    """
    List lectures with status information.
    
    Optionally filter by course_code.
    """
    try:
        lectures = await repository.list_lectures(course_code=course_code)
        
        result = []
        for lecture in lectures:
            # Parse error_log if it's a JSON string
            error_log = lecture.get("error_log")
            if isinstance(error_log, str):
                try:
                    error_log = json.loads(error_log) if error_log else None
                except json.JSONDecodeError:
                    error_log = None
            
            # Extract topics from structured_analysis
            topics = extract_topics_from_analysis(lecture.get("structured_analysis"))
            
            result.append(
                LectureStatus(
                    id=lecture["id"],
                    course_code=lecture["course_code"],
                    lecture_title=lecture["lecture_title"],
                    r2_pdf_path=lecture["r2_pdf_path"],
                    analysis_status=lecture["analysis_status"],
                    flashcard_status=lecture["flashcard_status"],
                    quiz_status=lecture["quiz_status"],
                    qdrant_status=lecture["qdrant_status"],
                    topics=topics,
                    error_log=error_log,
                    created_at=lecture["created_at"].isoformat(),
                    updated_at=lecture["updated_at"].isoformat()
                )
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing lectures: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lectures/{lecture_id}", response_model=LectureStatus)
async def get_lecture(
    lecture_id: int,
    repository: ContentRepository = Depends(get_repository)
):
    """Get detailed information about a specific lecture."""
    try:
        lecture = await repository.get_lecture_by_id(lecture_id)
        
        if not lecture:
            raise HTTPException(status_code=404, detail=f"Lecture {lecture_id} not found")
        
        # Parse error_log if it's a JSON string
        error_log = lecture.get("error_log")
        if isinstance(error_log, str):
            try:
                error_log = json.loads(error_log) if error_log else None
            except json.JSONDecodeError:
                error_log = None
        
        # Extract topics from structured_analysis
        topics = extract_topics_from_analysis(lecture.get("structured_analysis"))
        
        return LectureStatus(
            id=lecture["id"],
            course_code=lecture["course_code"],
            lecture_title=lecture["lecture_title"],
            r2_pdf_path=lecture["r2_pdf_path"],
            analysis_status=lecture["analysis_status"],
            flashcard_status=lecture["flashcard_status"],
            quiz_status=lecture["quiz_status"],
            qdrant_status=lecture["qdrant_status"],
            topics=topics,
            error_log=error_log,
            created_at=lecture["created_at"].isoformat(),
            updated_at=lecture["updated_at"].isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lecture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    success: bool
    message: str
    lecture_id: int


@router.get("/lectures/{lecture_id}/flashcards")
async def get_lecture_flashcards(
    lecture_id: int,
    repository: ContentRepository = Depends(get_repository)
):
    """
    Get full flashcards JSON for a specific lecture.
    
    Returns the exact JSON structure stored in the lectures.flashcards column,
    which is what the frontend StudyDeck expects.
    """
    try:
        lecture = await repository.get_lecture_by_id(lecture_id)
        
        if not lecture:
            raise HTTPException(status_code=404, detail=f"Lecture {lecture_id} not found")
        
        flashcards_data = lecture.get("flashcards")
        if not flashcards_data:
            raise HTTPException(
                status_code=404,
                detail=f"Flashcards not found for lecture {lecture_id}. Please run flashcard generation."
            )
        
        # Handle JSON string stored in DB
        if isinstance(flashcards_data, str):
            try:
                flashcards_data = json.loads(flashcards_data)
            except json.JSONDecodeError:
                logger.error(f"Invalid flashcards JSON for lecture {lecture_id}")
                raise HTTPException(
                    status_code=500,
                    detail="Stored flashcards data is corrupted or invalid JSON"
                )
        
        if not isinstance(flashcards_data, dict):
            logger.error(f"Unexpected flashcards data type for lecture {lecture_id}: {type(flashcards_data)}")
            raise HTTPException(
                status_code=500,
                detail="Stored flashcards data has unexpected format"
            )
        
        return flashcards_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flashcards for lecture {lecture_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch flashcards for lecture {lecture_id}: {str(e)}"
        )


@router.delete("/lectures/{lecture_id}", response_model=DeleteResponse)
async def delete_lecture(
    lecture_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repository: ContentRepository = Depends(get_repository)
):
    """
    Soft delete a lecture by marking it as deleted.
    
    The lecture will no longer appear in lists but remains in the database
    and can be restored if needed.
    """
    try:
        # First check if lecture exists
        lecture = await repository.get_lecture_by_id(lecture_id)
        if not lecture:
            raise HTTPException(status_code=404, detail=f"Lecture {lecture_id} not found")
        
        # Mark as deleted
        success = await repository.mark_lecture_deleted(lecture_id)
        
        if success:
            logger.info(f"Lecture {lecture_id} marked as deleted")
            return DeleteResponse(
                success=True,
                message=f"Lecture '{lecture['lecture_title']}' has been deleted",
                lecture_id=lecture_id
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete lecture")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lecture {lecture_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
