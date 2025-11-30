"""
Flashcard ID utility module.

Provides functions for generating stable, unique flashcard IDs.

ID Format: {course_code}_L{lecture_id}_FC{index:03d}
Examples: MS5260_L3_FC001, MS5260_L3_FC002, ...

This format is:
- Stable: doesn't change if lecture title is renamed
- Unique: globally unique across all lectures
- Compact: safe characters, no spaces
- Human-readable: can identify course and lecture at a glance
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def generate_flashcard_id(course_code: str, lecture_id: int, index: int) -> str:
    """
    Generate a stable, unique flashcard ID.
    
    Args:
        course_code: Course code (e.g., "MS5260")
        lecture_id: Database primary key of the lecture
        index: 1-based index of the flashcard within the lecture
        
    Returns:
        Flashcard ID in format: {course_code}_L{lecture_id}_FC{index:03d}
        
    Example:
        >>> generate_flashcard_id("MS5260", 3, 1)
        'MS5260_L3_FC001'
        >>> generate_flashcard_id("MS5260", 3, 15)
        'MS5260_L3_FC015'
    """
    # Sanitize course_code (remove spaces, uppercase)
    safe_course_code = course_code.strip().upper().replace(" ", "_")
    
    return f"{safe_course_code}_L{lecture_id}_FC{index:03d}"


def tag_flashcards_with_ids(
    flashcards_data: Dict[str, Any],
    course_code: str,
    lecture_id: int,
    overwrite_existing: bool = False
) -> Dict[str, Any]:
    """
    Tag all flashcards in a flashcards_data dict with unique IDs.
    
    This function is idempotent by default - it won't overwrite existing IDs
    unless explicitly told to.
    
    Args:
        flashcards_data: Dict containing "flashcards" list
        course_code: Course code for ID generation
        lecture_id: Lecture database ID for ID generation
        overwrite_existing: If True, regenerate IDs even if they exist
        
    Returns:
        Updated flashcards_data with flashcard_id set on each flashcard
        
    Example:
        >>> data = {"flashcards": [{"question": "Q1"}, {"question": "Q2"}]}
        >>> result = tag_flashcards_with_ids(data, "MS5260", 3)
        >>> result["flashcards"][0]["flashcard_id"]
        'MS5260_L3_FC001'
    """
    if not flashcards_data:
        logger.warning("tag_flashcards_with_ids called with empty flashcards_data")
        return flashcards_data
    
    flashcards = flashcards_data.get("flashcards", [])
    
    if not flashcards:
        logger.warning("No flashcards found in flashcards_data")
        return flashcards_data
    
    tagged_count = 0
    skipped_count = 0
    
    for index, flashcard in enumerate(flashcards, start=1):
        existing_id = flashcard.get("flashcard_id")
        
        if existing_id and not overwrite_existing:
            skipped_count += 1
            continue
        
        new_id = generate_flashcard_id(course_code, lecture_id, index)
        flashcard["flashcard_id"] = new_id
        tagged_count += 1
    
    logger.info(
        f"Flashcard ID tagging complete: "
        f"tagged={tagged_count}, skipped={skipped_count}, total={len(flashcards)}"
    )
    
    return flashcards_data


def validate_flashcard_ids(flashcards_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all flashcards have IDs and report any issues.
    
    Args:
        flashcards_data: Dict containing "flashcards" list
        
    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "total": int,
            "with_id": int,
            "without_id": int,
            "missing_indices": List[int]
        }
    """
    flashcards = flashcards_data.get("flashcards", [])
    
    with_id = 0
    without_id = 0
    missing_indices = []
    
    for index, flashcard in enumerate(flashcards, start=1):
        if flashcard.get("flashcard_id"):
            with_id += 1
        else:
            without_id += 1
            missing_indices.append(index)
    
    return {
        "valid": without_id == 0,
        "total": len(flashcards),
        "with_id": with_id,
        "without_id": without_id,
        "missing_indices": missing_indices[:10]  # First 10 only
    }



