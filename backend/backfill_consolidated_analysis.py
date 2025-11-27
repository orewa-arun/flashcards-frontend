"""
Backfill script to generate consolidated_structured_analysis for existing lectures.

This script finds all lectures that have structured_analysis but no consolidated_structured_analysis,
runs the consolidation process on them, and saves the results to the database.

Usage:
    python backfill_consolidated_analysis.py [--dry-run] [--lecture-id ID]
    
Options:
    --dry-run: Show what would be processed without actually updating the database
    --lecture-id ID: Process only a specific lecture ID
"""

import asyncio
import json
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.postgres import init_postgres_db, get_postgres_pool, close_postgres_db
from app.repositories.content_repository import ContentRepository
from app.content_generation.analyzers.content_consolidator import ContentConsolidator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def find_lectures_needing_consolidation(
    repository: ContentRepository,
    lecture_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Find lectures that have structured_analysis but no consolidated_structured_analysis.
    
    Args:
        repository: Content repository
        lecture_id: Optional specific lecture ID to process
        
    Returns:
        List of lecture dicts that need consolidation
    """
    if lecture_id:
        lecture = await repository.get_lecture_by_id(lecture_id)
        if not lecture:
            logger.warning(f"Lecture {lecture_id} not found")
            return []
        
        # Check if it needs consolidation
        if lecture.get("structured_analysis") and not lecture.get("consolidated_structured_analysis"):
            structured_analysis = lecture.get("structured_analysis")
            if isinstance(structured_analysis, str):
                try:
                    structured_analysis = json.loads(structured_analysis)
                except json.JSONDecodeError:
                    logger.warning(f"Lecture {lecture_id} has invalid structured_analysis JSON")
                    return []
            
            raw_slides = structured_analysis.get("raw_slide_analyses", [])
            if raw_slides:
                return [lecture]
            else:
                logger.warning(f"Lecture {lecture_id} has structured_analysis but no raw_slide_analyses")
                return []
        
        return []
    
    # Find all lectures with structured_analysis but no consolidated_structured_analysis
    all_lectures = await repository.list_lectures()
    lectures_to_process = []
    
    for lecture in all_lectures:
        # Skip if already has consolidated_structured_analysis
        if lecture.get("consolidated_structured_analysis"):
            continue
        
        # Check if has structured_analysis
        structured_analysis = lecture.get("structured_analysis")
        if not structured_analysis:
            continue
        
        # Parse JSON if needed
        if isinstance(structured_analysis, str):
            try:
                structured_analysis = json.loads(structured_analysis)
            except json.JSONDecodeError:
                logger.warning(f"Lecture {lecture['id']} has invalid structured_analysis JSON")
                continue
        
        # Check if has raw_slide_analyses
        raw_slides = structured_analysis.get("raw_slide_analyses", [])
        if raw_slides:
            lectures_to_process.append(lecture)
    
    return lectures_to_process


async def consolidate_lecture(
    repository: ContentRepository,
    lecture: Dict[str, Any],
    dry_run: bool = False
) -> bool:
    """
    Consolidate a single lecture and save to database.
    
    Args:
        repository: Content repository
        lecture: Lecture dict
        dry_run: If True, don't actually save to database
        
    Returns:
        True if successful, False otherwise
    """
    lecture_id = lecture["id"]
    lecture_title = lecture.get("lecture_title", "Unknown Lecture")
    
    try:
        # Extract structured_analysis
        structured_analysis = lecture.get("structured_analysis")
        if isinstance(structured_analysis, str):
            structured_analysis = json.loads(structured_analysis)
        
        raw_slide_analyses = structured_analysis.get("raw_slide_analyses", [])
        
        if not raw_slide_analyses:
            logger.warning(f"Lecture {lecture_id} has no raw_slide_analyses, skipping")
            return False
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing Lecture {lecture_id}: {lecture_title}")
        logger.info(f"Course: {lecture.get('course_code', 'Unknown')}")
        logger.info(f"Total Slides: {len(raw_slide_analyses)}")
        logger.info(f"{'='*70}")
        
        # Apply consolidation
        consolidator = ContentConsolidator(
            topic_similarity_threshold=0.5,
            min_educational_value=0.3,
            consolidate_by_title=True
        )
        
        logger.info("Running consolidation...")
        result = consolidator.consolidate(
            raw_slide_analyses=raw_slide_analyses,
            lecture_title=lecture_title
        )
        
        # Prepare consolidated data (same format as in structured_analysis.py)
        consolidated_analysis = {
            "lecture_info": {
                "id": lecture_id,
                "course_code": lecture["course_code"],
                "lecture_title": lecture_title,
                "analysis_status": lecture.get("analysis_status", "completed")
            },
            "consolidation_stats": {
                "original_slides": result.get("total_original_slides", 0),
                "educational_slides": result.get("educational_slides_count", 0),
                "filtered_slides": result.get("filtered_slides_count", 0),
                "topics_created": result.get("topic_count", 0),
                "semantic_chunks": len(result.get("semantic_chunks", [])),
                "summary": result.get("consolidation_summary", "")
            },
            "topics": result.get("topics", []),
            "semantic_chunks": result.get("semantic_chunks", []),
            "full_result": result
        }
        
        # Log statistics
        logger.info(f"✅ Consolidation complete:")
        logger.info(f"   Original slides: {result.get('total_original_slides', 0)}")
        logger.info(f"   Educational slides: {result.get('educational_slides_count', 0)}")
        logger.info(f"   Filtered slides: {result.get('filtered_slides_count', 0)}")
        logger.info(f"   Topics created: {result.get('topic_count', 0)}")
        logger.info(f"   Semantic chunks: {len(result.get('semantic_chunks', []))}")
        
        # Save to database (unless dry run)
        if dry_run:
            logger.info(f"🔍 DRY RUN: Would save consolidated_analysis for lecture {lecture_id}")
            return True
        
        logger.info(f"💾 Saving to database...")
        success = await repository.update_lecture_content(
            lecture_id=lecture_id,
            content_field="consolidated_structured_analysis",
            content_data=consolidated_analysis
        )
        
        if success:
            logger.info(f"✅ Successfully saved consolidated_analysis for lecture {lecture_id}")
            return True
        else:
            logger.error(f"❌ Failed to save consolidated_analysis for lecture {lecture_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error processing lecture {lecture_id}: {str(e)}", exc_info=True)
        return False


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Backfill consolidated_structured_analysis for existing lectures"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually updating the database"
    )
    parser.add_argument(
        "--lecture-id",
        type=int,
        help="Process only a specific lecture ID"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_postgres_db()
        pool = await get_postgres_pool()
        
        # Create repository
        repository = ContentRepository(pool)
        
        # Find lectures needing consolidation
        logger.info("Searching for lectures needing consolidation...")
        lectures = await find_lectures_needing_consolidation(
            repository,
            lecture_id=args.lecture_id
        )
        
        if not lectures:
            logger.info("✅ No lectures found that need consolidation.")
            logger.info("   All lectures either:")
            logger.info("   - Already have consolidated_structured_analysis, or")
            logger.info("   - Don't have structured_analysis with raw_slide_analyses")
            return
        
        logger.info(f"\n📊 Found {len(lectures)} lecture(s) needing consolidation")
        
        if args.dry_run:
            logger.info("\n🔍 DRY RUN MODE - No changes will be made to the database\n")
        
        # Process each lecture
        successful = 0
        failed = 0
        
        for idx, lecture in enumerate(lectures, 1):
            logger.info(f"\n[{idx}/{len(lectures)}] Processing lecture {lecture['id']}...")
            
            success = await consolidate_lecture(
                repository=repository,
                lecture=lecture,
                dry_run=args.dry_run
            )
            
            if success:
                successful += 1
            else:
                failed += 1
        
        # Summary
        logger.info(f"\n{'='*70}")
        logger.info("SUMMARY")
        logger.info(f"{'='*70}")
        logger.info(f"Total lectures processed: {len(lectures)}")
        logger.info(f"✅ Successful: {successful}")
        logger.info(f"❌ Failed: {failed}")
        
        if args.dry_run:
            logger.info(f"\n🔍 This was a DRY RUN - no changes were made to the database")
            logger.info(f"   Run without --dry-run to actually update the database")
        else:
            logger.info(f"\n✅ Backfill complete!")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Close database connection
        try:
            await close_postgres_db()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())

