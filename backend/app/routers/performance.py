import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ..database import get_database
from ..firebase_auth import get_current_user
from ..models.readiness_v2 import UserFlashcardPerformance
from ..services.flashcard_performance_service import FlashcardPerformanceService

router = APIRouter()

def _serialize_datetime(obj):
    """Helper to serialize datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# Helper function to load flashcard content
def _load_flashcard_content(course_id: str, lecture_id: str) -> Dict[str, Any]:
    """Loads the cognitive flashcards file for a given course and lecture."""
    base_path = Path(__file__).parent.parent.parent / "courses"
    file_path = base_path / course_id / "cognitive_flashcards" / lecture_id / f"{lecture_id}_cognitive_flashcards_only.json"
    
    if not file_path.exists():
        return {}
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Create a dictionary for quick lookup by flashcard_id
        return {flashcard['flashcard_id']: flashcard for flashcard in data.get('flashcards', [])}

@router.get("/weak-flashcards", response_model=List[Dict[str, Any]])
async def get_weak_flashcards_with_content(
    user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Retrieves all weak flashcard performance documents for the current user,
    enriched with the actual flashcard content.
    """
    try:
        user_id = user["uid"]
        flashcard_perf_service = FlashcardPerformanceService(db)
        
        weak_flashcards_perf = await flashcard_perf_service.get_weak_flashcards_for_user(user_id)
        
        enriched_flashcards = []
        
        # Cache loaded flashcard content to avoid redundant file I/O
        flashcard_content_cache = {}

        for perf_doc in weak_flashcards_perf:
            # Convert Pydantic model to dictionary for JSON serialization
            # mode='json' ensures datetime objects are serialized to ISO strings
            perf_doc_dict = perf_doc.model_dump(mode='json')
            course_id = perf_doc_dict.get("course_id")
            lecture_id = perf_doc_dict.get("lecture_id")
            flashcard_id = perf_doc_dict.get("flashcard_id")

            if not all([course_id, lecture_id, flashcard_id]):
                continue

            cache_key = f"{course_id}_{lecture_id}"
            if cache_key not in flashcard_content_cache:
                flashcard_content_cache[cache_key] = _load_flashcard_content(course_id, lecture_id)

            lecture_flashcards = flashcard_content_cache[cache_key]
            
            content = lecture_flashcards.get(flashcard_id)
            
            if content:
                # Merge flashcard content first, then add performance data
                # This ensures flashcard fields (like 'question') are not overwritten
                enriched_doc = {
                    **content,  # Flashcard content (question, answers, diagrams, etc.)
                    # Add performance-specific fields
                    "performance_by_level": perf_doc_dict.get("performance_by_level"),
                    "recent_attempts": perf_doc_dict.get("recent_attempts"),
                    "coverage_score": perf_doc_dict.get("coverage_score"),
                    "accuracy_score": perf_doc_dict.get("accuracy_score"),
                    "momentum_score": perf_doc_dict.get("momentum_score"),
                    "is_weak": perf_doc_dict.get("is_weak"),
                    "last_updated": perf_doc_dict.get("last_updated"),
                }
                enriched_flashcards.append(enriched_doc)
            else:
                # If content not found, still include performance data with a flag
                enriched_doc = {
                    **perf_doc_dict,
                    "is_missing_data": True,
                    "question": "[Missing Data] Flashcard content not found.",
                    "answers": [],
                }
                enriched_flashcards.append(enriched_doc)

        return enriched_flashcards
    except Exception as e:
        print(f"Error fetching weak flashcards for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching weak flashcards.")
