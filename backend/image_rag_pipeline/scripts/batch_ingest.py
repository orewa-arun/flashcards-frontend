"""
Batch ingestion script for processing all courses from courses.json.
"""
import json
import os
import sys
import logging
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ingestion.loader import IngestionPipeline
from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder
from app.utils.config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)


def ingest_all_courses(
    courses_json_path: Optional[str] = None,
    course_id: Optional[str] = None,
    lecture_number: Optional[str] = None
):
    """
    Ingest courses from courses.json.
    
    Args:
        courses_json_path: Path to courses.json (defaults to project root)
        course_id: Optional course ID to filter (if None, processes all courses)
        lecture_number: Optional lecture number to filter (if None, processes all lectures)
                       Only used if course_id is also provided
    """
    # Default path to courses.json
    if courses_json_path is None:
        script_dir = os.path.dirname(__file__)
        courses_json_path = os.path.join(
            script_dir, 
            "..", "..", "..", 
            "courses_resources", 
            "courses.json"
        )
    
    courses_json_path = os.path.abspath(courses_json_path)
    
    if not os.path.exists(courses_json_path):
        logger.error(f"courses.json not found at: {courses_json_path}")
        return
    
    logger.info(f"Loading courses from: {courses_json_path}")
    
    # Initialize components
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    data_dir = os.path.join(base_dir, "data")
    
    # Initialize vector store using Config
    if Config.QDRANT_PATH and not Config.QDRANT_PATH.startswith("http"):
        # Use local path
        vector_db_path = Config.QDRANT_PATH if os.path.isabs(Config.QDRANT_PATH) else os.path.join(base_dir, Config.QDRANT_PATH)
        vector_store = VectorStore(path=vector_db_path)
    else:
        # Use remote server
        vector_store = VectorStore(host=Config.QDRANT_HOST, port=Config.QDRANT_PORT)
    logger.info("Vector store initialized")
    
    embedder = Embedder(
        model_name=Config.CLIP_MODEL,
        pretrained=Config.CLIP_PRETRAINED
    )
    logger.info("Embedder initialized")
    
    pipeline = IngestionPipeline(
        image_output_dir=os.path.join(data_dir, "images"),
        vector_store=vector_store,
        embedder=embedder,
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    logger.info("Ingestion pipeline initialized")
    
    # Load courses
    with open(courses_json_path) as f:
        courses = json.load(f)
    
    logger.info(f"Found {len(courses)} courses")
    
    # Filter courses if course_id is provided
    if course_id:
        courses = [c for c in courses if c.get("course_id") == course_id]
        if not courses:
            logger.error(f"Course ID '{course_id}' not found in courses.json")
            return
        logger.info(f"Filtered to course: {course_id}")
    
    # Track statistics
    total_processed = 0
    total_failed = 0
    total_skipped = 0
    
    # Ingest each course
    for course in courses:
        current_course_id = course["course_id"]
        course_name = course["course_name"]
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing course: {current_course_id} - {course_name}")
        logger.info(f"{'='*60}")
        
        # Filter lectures if lecture_number is provided
        lectures = course.get("lecture_slides", [])
        if lecture_number:
            # Match exact or check if lecture_number is within a range (e.g., "1" matches "1-3")
            def matches_lecture(lecture_num: str, search_num: str) -> bool:
                if lecture_num == search_num:
                    return True
                # Check if search_num is within a range (e.g., "1-3" contains "1", "2", or "3")
                if "-" in lecture_num:
                    try:
                        start, end = map(int, lecture_num.split("-"))
                        search_int = int(search_num)
                        return start <= search_int <= end
                    except ValueError:
                        return False
                # Check if lecture_num starts with search_num (e.g., "1" matches "1-3")
                return lecture_num.startswith(search_num + "-") or lecture_num.startswith(search_num + ",")
            
            filtered_lectures = [
                l for l in lectures 
                if matches_lecture(l.get("lecture_number", ""), lecture_number)
            ]
            
            if not filtered_lectures:
                # Show available lecture numbers for helpful error message
                available = [l.get("lecture_number", "Unknown") for l in lectures]
                logger.warning(
                    f"Lecture number '{lecture_number}' not found in course {current_course_id}. "
                    f"Available lecture numbers: {', '.join(available)}"
                )
                total_skipped += 1
                continue
            
            lectures = filtered_lectures
            logger.info(f"Filtered to lecture number: {lecture_number} (matched {len(lectures)} lecture(s))")
        
        for lecture in lectures:
            pdf_path = lecture.get("pdf_path")
            
            if not pdf_path:
                logger.warning(f"  No PDF path for lecture: {lecture.get('lecture_name')}")
                total_skipped += 1
                continue
            
            # Convert to absolute path if relative
            if not os.path.isabs(pdf_path):
                # Path is relative to project root
                project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
                pdf_path = os.path.join(project_root, pdf_path)
            
            pdf_path = os.path.abspath(pdf_path)
            
            # Determine if we should process the PDF
            pdf_exists = os.path.exists(pdf_path)
            has_pdf_flag = lecture.get("hasPDF", True)
            
            should_process_pdf = pdf_exists and has_pdf_flag
            
            if not pdf_exists:
                logger.warning(f"  PDF file missing: {pdf_path}")
            
            if not has_pdf_flag:
                logger.info(f"  Lecture marked as hasPDF=false: {lecture.get('lecture_name')}")

            metadata = {
                "course_id": current_course_id,
                "course_name": course_name,
                "lecture_name": lecture.get("lecture_name", "Unknown"),
                "lecture_number": lecture.get("lecture_number", "Unknown"),
                "topics": lecture.get("topics", [])
            }
            
            # Try to find corresponding flashcard JSON file
            pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
            
            # Look for JSON in multiple possible locations
            json_paths_to_try = [
                # Primary: courses/ directory
                os.path.join(
                    project_root,
                    "courses",
                    current_course_id,
                    "cognitive_flashcards",
                    pdf_basename,
                    f"{pdf_basename}_cognitive_flashcards_only.json"
                ),
                # Fallback: backend/courses/ directory
                os.path.join(
                    project_root,
                    "backend",
                    "courses",
                    current_course_id,
                    "cognitive_flashcards",
                    pdf_basename,
                    f"{pdf_basename}_cognitive_flashcards_only.json"
                )
            ]
            
            json_path = None
            for path in json_paths_to_try:
                if os.path.exists(path):
                    json_path = path
                    break
            
            # If neither PDF nor JSON exists, skip
            if not should_process_pdf and not json_path:
                logger.warning(f"  Skipping: No PDF (or hasPDF=false) and no flashcard JSON found for {lecture.get('lecture_name')}")
                total_skipped += 1
                continue

            try:
                logger.info(f"\n  Processing: {lecture['lecture_name']}")
                
                # Use hybrid ingestion if JSON exists
                if json_path:
                    logger.info(f"  Using hybrid ingestion (PDF + JSON)")
                    if should_process_pdf:
                        logger.info(f"    - Images from: {os.path.basename(pdf_path)}")
                    else:
                        logger.info(f"    - Skipping PDF images (hasPDF=false or file missing)")
                    logger.info(f"    - Text from: {os.path.basename(json_path)}")
                    
                    result = pipeline.ingest_lecture_hybrid(
                        pdf_path=pdf_path,
                        json_path=json_path,
                        course_id=current_course_id,
                        lecture_metadata=metadata,
                        skip_images=not should_process_pdf
                    )
                    logger.info(f"  ✓ Success: {result['total_items']} items "
                              f"({result['flashcard_blocks']} flashcard blocks, {result['images']} images)")
                # Otherwise fallback to PDF-only if valid
                elif should_process_pdf:
                    logger.info(f"  Using PDF-only ingestion (no flashcard JSON found)")
                    result = pipeline.ingest_pdf(pdf_path, current_course_id, metadata)
                    logger.info(f"  ✓ Success: {result['total_items']} items "
                              f"({result['text_chunks']} chunks, {result['images']} images)")
                else:
                    # This case should be caught by the check above, but just in case
                    logger.warning("  Skipping: conditions not met for ingestion")
                    total_skipped += 1
                    continue
                
                total_processed += 1
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                total_failed += 1
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("INGESTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total lectures processed: {total_processed}")
    logger.info(f"Total failed: {total_failed}")
    logger.info(f"Total skipped: {total_skipped}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch ingest courses from courses.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all courses and lectures
  python scripts/batch_ingest.py
  
  # Process all lectures for a specific course
  python scripts/batch_ingest.py --course-id MS5260
  
  # Process a specific lecture from a specific course
  python scripts/batch_ingest.py --course-id MS5260 --lecture-number 4
        """
    )
    parser.add_argument(
        "--courses-json",
        type=str,
        default=None,
        help="Path to courses.json file (defaults to project root)"
    )
    parser.add_argument(
        "--course-id",
        type=str,
        default=None,
        help="Optional course ID to filter (e.g., MS5260). If provided, only processes this course."
    )
    parser.add_argument(
        "--lecture-number",
        type=str,
        default=None,
        help="Optional lecture number to filter (e.g., '4' or '1-3'). "
             "Only used if --course-id is also provided. If provided, only processes this lecture."
    )
    
    args = parser.parse_args()
    ingest_all_courses(
        courses_json_path=args.courses_json,
        course_id=args.course_id,
        lecture_number=args.lecture_number
    )

