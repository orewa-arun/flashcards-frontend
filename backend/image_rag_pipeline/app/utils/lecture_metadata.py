"""
Utility for loading lecture metadata from structured analysis JSON files.
This provides the foundational context for the AI Tutor chatbot.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def load_lecture_metadata(course_id: str, lecture_id: str) -> Dict[str, any]:
    """
    Load lecture summary and key concepts from the structured analysis JSON.
    
    Args:
        course_id: Course identifier (e.g., "MS5260")
        lecture_id: Lecture identifier (e.g., "MIS_lec_1-3")
        
    Returns:
        Dictionary with 'lecture_summary' and 'key_concepts', or fallback values
    """
    # Construct the path to the structured analysis JSON
    # Path pattern: courses/{course_id}/slide_analysis/{lecture_id}_structured_analysis.json
    base_path = Path(__file__).parent.parent.parent.parent.parent  # Navigate to project root
    json_path = base_path / "courses" / course_id / "slide_analysis" / f"{lecture_id}_structured_analysis.json"
    
    logger.info(f"Loading lecture metadata from: {json_path}")
    
    try:
        if not json_path.exists():
            logger.warning(f"Structured analysis file not found: {json_path}")
            return _get_fallback_metadata(course_id, lecture_id)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract lecture_summary and key_concepts if they exist
        lecture_summary = data.get('lecture_summary')
        key_concepts = data.get('key_concepts', [])
        
        if not lecture_summary:
            logger.warning(f"No lecture_summary found in {json_path}, using fallback")
            return _get_fallback_metadata(course_id, lecture_id)
        
        logger.info(f"Loaded metadata: {len(key_concepts)} key concepts identified")
        
        return {
            'lecture_summary': lecture_summary,
            'key_concepts': key_concepts,
            'total_slides': data.get('total_slides', 0)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {json_path}: {e}")
        return _get_fallback_metadata(course_id, lecture_id)
    except Exception as e:
        logger.error(f"Error loading lecture metadata: {e}")
        return _get_fallback_metadata(course_id, lecture_id)


def _get_fallback_metadata(course_id: str, lecture_id: str) -> Dict[str, any]:
    """
    Generate fallback metadata when the structured analysis doesn't exist or lacks metadata.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        
    Returns:
        Dictionary with basic fallback values
    """
    return {
        'lecture_summary': f"This is lecture '{lecture_id}' from course '{course_id}'.",
        'key_concepts': ["Course content"],
        'total_slides': 0,
        'is_fallback': True
    }


def create_foundational_context(
    course_id: str, 
    lecture_id: str,
    metadata: Optional[Dict[str, any]] = None
) -> str:
    """
    Create the "Foundational Context" string that will be pinned to every AI response.
    This is the "mission statement" for the chatbot.
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        metadata: Pre-loaded metadata (if None, will load from file)
        
    Returns:
        A formatted string containing the foundational context
    """
    if metadata is None:
        metadata = load_lecture_metadata(course_id, lecture_id)
    
    lecture_summary = metadata.get('lecture_summary', 'This lecture')
    key_concepts = metadata.get('key_concepts', [])
    
    # Build the foundational context
    context_parts = [
        "=== YOUR ROLE ===",
        "You are an expert AI Tutor helping a student master university-level concepts.",
        "Your teaching style is inspired by Richard Feynman and Walter Lewin:",
        "- Break down complex ideas into simple, intuitive explanations",
        "- Use real-world analogies and vivid examples",
        "- Build understanding step-by-step, from fundamentals to advanced topics",
        "- Make learning engaging and memorable",
        "",
        "=== THIS LECTURE ===",
        lecture_summary,
        "",
    ]
    
    if key_concepts and len(key_concepts) > 0:
        context_parts.append("=== KEY CONCEPTS TO COVER ===")
        for i, concept in enumerate(key_concepts, 1):
            context_parts.append(f"{i}. {concept}")
        context_parts.append("")
    
    context_parts.extend([
        "=== YOUR TASK ===",
        "Help the student understand these concepts deeply, one at a time.",
        "When they ask vague questions like 'next concept' or 'tell me more',",
        "use the key concepts list above to guide them logically through the material.",
        "Always stay on topic and grounded in the lecture content."
    ])
    
    return "\n".join(context_parts)


