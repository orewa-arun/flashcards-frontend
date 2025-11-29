"""
Utility for loading lecture metadata from consolidated analysis in the database.
This provides the foundational context for the AI Tutor chatbot.

ENHANCED: Now fetches from PostgreSQL lectures table, prioritizing consolidated_structured_analysis.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncpg

logger = logging.getLogger(__name__)

# Database connection pool (will be initialized on first use)
_db_pool: Optional[asyncpg.Pool] = None


async def _get_db_pool() -> asyncpg.Pool:
    """
    Get or create a database connection pool.
    
    Uses the same connection string as the main app.
    """
    global _db_pool
    
    if _db_pool is None:
        # Get database URL from environment
        db_url = os.getenv("POSTGRES_URL", "")
        if not db_url:
            raise RuntimeError("POSTGRES_URL environment variable not set")
        
        # Convert SQLAlchemy URL format to asyncpg format
        db_url = db_url.replace("+asyncpg", "")
        
        _db_pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=5,
            command_timeout=30
        )
        logger.info("Created database connection pool for lecture metadata")
    
    return _db_pool


async def load_lecture_metadata_from_db(
    course_code: str,
    lecture_id: str
) -> Optional[Dict[str, Any]]:
    """
    Load lecture metadata from the database.
    
    Prioritizes consolidated_structured_analysis, falls back to structured_analysis.
    
    Args:
        course_code: Course code (e.g., "MS5260")
        lecture_id: Lecture ID (can be numeric or string like "MIS_lec_1-3")
        
    Returns:
        Dictionary with lecture metadata or None if not found
    """
    try:
        pool = await _get_db_pool()
        
        async with pool.acquire() as conn:
            # Try to find lecture by ID (numeric) or by title pattern
            if lecture_id.isdigit():
                query = """
                    SELECT id, course_code, lecture_title,
                           consolidated_structured_analysis,
                           structured_analysis
                    FROM lectures
                    WHERE course_code = $1 AND id = $2
                """
                row = await conn.fetchrow(query, course_code, int(lecture_id))
            else:
                # Search by lecture title pattern (legacy support)
                query = """
                    SELECT id, course_code, lecture_title,
                           consolidated_structured_analysis,
                           structured_analysis
                    FROM lectures
                    WHERE course_code = $1 
                      AND (lecture_title ILIKE $2 OR lecture_title ILIKE $3)
                    LIMIT 1
                """
                row = await conn.fetchrow(
                    query, 
                    course_code, 
                    f"%{lecture_id}%",
                    lecture_id.replace("_", " ").replace("-", " ")
                )
            
            if not row:
                logger.warning(f"Lecture not found in DB: {course_code}/{lecture_id}")
                return None
            
            # Prioritize consolidated_structured_analysis
            consolidated = row.get("consolidated_structured_analysis")
            structured = row.get("structured_analysis")
            
            if consolidated:
                logger.info(f"Using consolidated_structured_analysis for {course_code}/{lecture_id}")
                return _parse_consolidated_metadata(consolidated, row)
            elif structured:
                logger.info(f"Falling back to structured_analysis for {course_code}/{lecture_id}")
                return _parse_structured_metadata(structured, row)
            else:
                logger.warning(f"No analysis data found for lecture {course_code}/{lecture_id}")
                return None
                
    except Exception as e:
        logger.error(f"Error loading lecture metadata from DB: {e}")
        return None


def _parse_consolidated_metadata(
    consolidated: Dict[str, Any],
    row: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse consolidated_structured_analysis into metadata format.
    
    Extracts:
    - topics: Ordered list of topics (the "roadmap")
    - lecture_summary: From consolidation_stats.summary
    - key_concepts: Aggregated from all topics
    """
    # Handle JSON string if needed
    if isinstance(consolidated, str):
        consolidated = json.loads(consolidated)
    
    # Extract topics (the roadmap)
    topics = consolidated.get("topics", [])
    topic_names = [t.get("name", "") for t in topics if t.get("name")]
    
    # Extract consolidation summary
    stats = consolidated.get("consolidation_stats", {})
    summary = stats.get("summary", "")
    
    # If no summary, build one from lecture info
    if not summary:
        lecture_info = consolidated.get("lecture_info", {})
        summary = f"This lecture covers: {', '.join(topic_names[:5])}" if topic_names else ""
    
    # Aggregate key concepts from all topics
    all_key_concepts = []
    for topic in topics:
        concepts = topic.get("key_concepts", [])
        all_key_concepts.extend(concepts)
    
    # Deduplicate while preserving order
    seen = set()
    unique_concepts = []
    for concept in all_key_concepts:
        if concept.lower() not in seen:
            seen.add(concept.lower())
            unique_concepts.append(concept)
    
    return {
        "lecture_summary": summary,
        "key_concepts": unique_concepts[:15],  # Limit to top 15
        "topics": topic_names,  # The roadmap
        "topics_detailed": topics,  # Full topic objects for rich context
        "total_slides": stats.get("original_slides", 0),
        "semantic_chunks_count": stats.get("semantic_chunks", 0),
        "source": "consolidated_structured_analysis",
        "lecture_id": row.get("id"),
        "lecture_title": row.get("lecture_title", "")
    }


def _parse_structured_metadata(
    structured: Dict[str, Any],
    row: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse structured_analysis into metadata format (fallback).
    """
    if isinstance(structured, str):
        structured = json.loads(structured)
    
    return {
        "lecture_summary": structured.get("lecture_summary", ""),
        "key_concepts": structured.get("key_concepts", []),
        "topics": [],  # No roadmap in old format
        "topics_detailed": [],
        "total_slides": structured.get("total_slides", 0),
        "source": "structured_analysis",
        "lecture_id": row.get("id"),
        "lecture_title": row.get("lecture_title", "")
    }


def load_lecture_metadata(course_id: str, lecture_id: str) -> Dict[str, Any]:
    """
    Load lecture summary and key concepts from the database or file system.
    
    ENHANCED: Now tries database first (consolidated_structured_analysis),
    then falls back to file-based structured_analysis.json.
    
    Args:
        course_id: Course identifier (e.g., "MS5260")
        lecture_id: Lecture identifier (e.g., "MIS_lec_1-3" or numeric ID)
        
    Returns:
        Dictionary with 'lecture_summary', 'key_concepts', 'topics', etc.
    """
    import asyncio
    
    # Try to load from database first
    try:
        # Check if we're in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, need to create a task
            # This is tricky - we'll use a sync approach instead
            logger.info(f"Async context detected, using sync DB fetch for {course_id}/{lecture_id}")
        except RuntimeError:
            # No running loop, we can create one
            pass
        
        # Use sync approach with new event loop
        db_metadata = asyncio.get_event_loop().run_until_complete(
            load_lecture_metadata_from_db(course_id, lecture_id)
        )
        
        if db_metadata:
            logger.info(f"Loaded metadata from DB ({db_metadata.get('source', 'unknown')}) for {course_id}/{lecture_id}")
            return db_metadata
            
    except Exception as e:
        logger.warning(f"Could not load from DB, falling back to file: {e}")
    
    # Fallback to file-based loading (legacy)
    return _load_lecture_metadata_from_file(course_id, lecture_id)


def _load_lecture_metadata_from_file(course_id: str, lecture_id: str) -> Dict[str, Any]:
    """
    Legacy file-based metadata loading.
    
    Reads from: courses/{course_id}/slide_analysis/{lecture_id}_structured_analysis.json
    """
    # Construct the path to the structured analysis JSON
    base_path = Path(__file__).parent.parent.parent.parent.parent  # Navigate to project root
    json_path = base_path / "courses" / course_id / "slide_analysis" / f"{lecture_id}_structured_analysis.json"
    
    logger.info(f"Loading lecture metadata from file: {json_path}")
    
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
        
        logger.info(f"Loaded metadata from file: {len(key_concepts)} key concepts identified")
        
        return {
            'lecture_summary': lecture_summary,
            'key_concepts': key_concepts,
            'topics': [],  # No roadmap in file-based format
            'topics_detailed': [],
            'total_slides': data.get('total_slides', 0),
            'source': 'file'
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {json_path}: {e}")
        return _get_fallback_metadata(course_id, lecture_id)
    except Exception as e:
        logger.error(f"Error loading lecture metadata from file: {e}")
        return _get_fallback_metadata(course_id, lecture_id)


def _get_fallback_metadata(course_id: str, lecture_id: str) -> Dict[str, Any]:
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
        'topics': [],
        'topics_detailed': [],
        'total_slides': 0,
        'is_fallback': True,
        'source': 'fallback'
    }


def create_foundational_context(
    course_id: str, 
    lecture_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create the "Foundational Context" string that will be pinned to every AI response.
    This is the "mission statement" for the chatbot.
    
    ENHANCED: Now includes:
    - Lecture Roadmap (topics from consolidated analysis)
    - Socratic/Feynman teaching style guidance
    - Handoff to Adaptive Quiz Mode
    
    Args:
        course_id: Course identifier
        lecture_id: Lecture identifier
        metadata: Pre-loaded metadata (if None, will load from file/DB)
        
    Returns:
        A formatted string containing the foundational context
    """
    if metadata is None:
        metadata = load_lecture_metadata(course_id, lecture_id)
    
    lecture_summary = metadata.get('lecture_summary', 'This lecture')
    key_concepts = metadata.get('key_concepts', [])
    topics = metadata.get('topics', [])
    lecture_title = metadata.get('lecture_title', lecture_id)
    
    # Build the foundational context with enhanced teaching style
    context_parts = [
        "=== YOUR ROLE ===",
        "You are an expert AI Tutor—warm, empathetic, and adaptive.",
        "You combine the best teaching styles:",
        "",
        "**Socratic Method**: Guide students through questions. Don't just dump information.",
        "  - Ask 'What do you think?' before revealing answers",
        "  - Use 'Why might that be?' to encourage reasoning",
        "  - But if a student is stuck, pivot gracefully to direct explanation",
        "",
        "**Feynman Technique**: Explain simply, as if to a bright 12-year-old.",
        "  - Use everyday analogies and vivid examples",
        "  - Avoid jargon; when you must use it, define it immediately",
        "  - Build from first principles",
        "",
        "**Human Touch**: Be natural, not robotic.",
        "  - Read the room—if they're frustrated, be encouraging",
        "  - Celebrate small wins: 'Exactly!' 'You've got it!'",
        "  - Use light humor when appropriate",
        "  - Improvise minimally when it helps understanding",
        "",
        "=== THIS LECTURE ===",
        f"**{lecture_title}**",
        "",
        lecture_summary,
        "",
    ]
    
    # Add the Roadmap (topics) if available
    if topics and len(topics) > 0:
        context_parts.append("=== LECTURE ROADMAP ===")
        context_parts.append("This is the logical flow of topics in this lecture:")
        for i, topic in enumerate(topics, 1):
            context_parts.append(f"  {i}. {topic}")
        context_parts.append("")
        context_parts.append("Use this roadmap to guide the conversation if the student is exploring.")
        context_parts.append("When finishing a topic, naturally bridge to the next one.")
        context_parts.append("")
    
    # Add key concepts if available
    if key_concepts and len(key_concepts) > 0:
        context_parts.append("=== KEY CONCEPTS ===")
        for i, concept in enumerate(key_concepts[:10], 1):  # Limit to 10
            context_parts.append(f"  {i}. {concept}")
        context_parts.append("")
    
    context_parts.extend([
        "=== YOUR TASK ===",
        "Help the student understand these concepts deeply.",
        "",
        "When they ask vague questions like 'next concept' or 'tell me more',",
        "use the Roadmap above to guide them logically through the material.",
        "",
        "Always stay grounded in the lecture content. If asked about something",
        "not in the materials, gently redirect: 'That's a great question, but",
        "let's focus on what's in this lecture first.'",
        "",
        "=== HANDOFF ===",
        "When the student has understood the core concepts of this lecture,",
        "encourage them to test their knowledge:",
        "",
        "'You've got a solid grasp of these concepts! Ready to put them to the test?",
        "Try the **Adaptive Quiz Mode** to see how exam-ready you are.'",
    ])
    
    return "\n".join(context_parts)


# Async version for use in async contexts
async def load_lecture_metadata_async(course_id: str, lecture_id: str) -> Dict[str, Any]:
    """
    Async version of load_lecture_metadata.
    
    Use this when calling from an async function.
    """
    # Try database first
    db_metadata = await load_lecture_metadata_from_db(course_id, lecture_id)
    
    if db_metadata:
        logger.info(f"Loaded metadata from DB ({db_metadata.get('source', 'unknown')}) for {course_id}/{lecture_id}")
        return db_metadata
    
    # Fallback to file
    return _load_lecture_metadata_from_file(course_id, lecture_id)
