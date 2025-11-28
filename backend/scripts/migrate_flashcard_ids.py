#!/usr/bin/env python3
"""
Migration script to add flashcard IDs to existing flashcards in the database.

This script:
1. Fetches all lectures with completed flashcards
2. Tags each flashcard with a stable ID: {course_code}_L{lecture_id}_FC{index:03d}
3. Saves the updated flashcards back to the database

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/migrate_flashcard_ids.py

Options:
    --dry-run    Show what would be updated without making changes
    --lecture-id ID    Only process a specific lecture
"""

import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.postgres import init_postgres_db, get_postgres_pool, close_postgres_db
from app.repositories.content_repository import ContentRepository
from app.content_generation.utils.flashcard_id import tag_flashcards_with_ids, validate_flashcard_ids

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def migrate_lecture_flashcard_ids(
    repository: ContentRepository,
    lecture: dict,
    dry_run: bool = False
) -> dict:
    """
    Migrate flashcard IDs for a single lecture.
    
    Args:
        repository: Content repository
        lecture: Lecture dict from database
        dry_run: If True, don't save changes
        
    Returns:
        Dict with migration results
    """
    lecture_id = lecture["id"]
    course_code = lecture["course_code"]
    lecture_title = lecture["lecture_title"]
    
    result = {
        "lecture_id": lecture_id,
        "course_code": course_code,
        "lecture_title": lecture_title,
        "status": "skipped",
        "flashcards_total": 0,
        "flashcards_tagged": 0,
        "flashcards_already_had_id": 0
    }
    
    # Get flashcards data
    flashcards_data = lecture.get("flashcards")
    
    if not flashcards_data:
        result["status"] = "no_flashcards"
        return result
    
    # Parse if JSON string
    if isinstance(flashcards_data, str):
        try:
            flashcards_data = json.loads(flashcards_data)
        except json.JSONDecodeError:
            result["status"] = "invalid_json"
            return result
    
    flashcards = flashcards_data.get("flashcards", [])
    result["flashcards_total"] = len(flashcards)
    
    if not flashcards:
        result["status"] = "empty_flashcards"
        return result
    
    # Validate current state
    validation = validate_flashcard_ids(flashcards_data)
    result["flashcards_already_had_id"] = validation["with_id"]
    
    if validation["valid"]:
        result["status"] = "already_complete"
        logger.info(f"  ✓ Lecture {lecture_id}: All {len(flashcards)} flashcards already have IDs")
        return result
    
    # Tag flashcards with IDs
    logger.info(
        f"  → Lecture {lecture_id} ({lecture_title}): "
        f"Tagging {validation['without_id']}/{len(flashcards)} flashcards"
    )
    
    updated_flashcards_data = tag_flashcards_with_ids(
        flashcards_data=flashcards_data,
        course_code=course_code,
        lecture_id=lecture_id,
        overwrite_existing=False  # Don't overwrite existing IDs
    )
    
    result["flashcards_tagged"] = validation["without_id"]
    
    # Save if not dry run
    if not dry_run:
        await repository.update_lecture_content(
            lecture_id=lecture_id,
            content_field="flashcards",
            content_data=updated_flashcards_data
        )
        result["status"] = "updated"
        logger.info(f"  ✓ Lecture {lecture_id}: Saved {result['flashcards_tagged']} new IDs")
    else:
        result["status"] = "would_update"
        logger.info(f"  [DRY RUN] Lecture {lecture_id}: Would tag {result['flashcards_tagged']} flashcards")
        
        # Show sample IDs
        sample_flashcards = updated_flashcards_data.get("flashcards", [])[:3]
        for fc in sample_flashcards:
            logger.info(f"    Sample ID: {fc.get('flashcard_id')}")
    
    return result


async def run_migration(dry_run: bool = False, lecture_id: int = None):
    """
    Run the flashcard ID migration.
    
    Args:
        dry_run: If True, don't save changes
        lecture_id: If provided, only process this lecture
    """
    logger.info("=" * 60)
    logger.info("Flashcard ID Migration Script")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("MODE: Dry run (no changes will be saved)")
    else:
        logger.info("MODE: Live run (changes will be saved)")
    
    # Initialize database connection (create global pool)
    await init_postgres_db()
    pool = await get_postgres_pool()
    repository = ContentRepository(pool)
    
    # Fetch lectures
    if lecture_id:
        logger.info(f"\nFetching lecture {lecture_id}...")
        lecture = await repository.get_lecture_by_id(lecture_id)
        if not lecture:
            logger.error(f"Lecture {lecture_id} not found")
            return
        lectures = [lecture]
    else:
        logger.info("\nFetching all lectures with completed flashcards...")
        lectures = await repository.get_lectures_by_status(
            status_field="flashcard_status",
            status_value="completed"
        )
    
    logger.info(f"Found {len(lectures)} lecture(s) to process\n")
    
    # Process each lecture
    results = []
    for lecture in lectures:
        result = await migrate_lecture_flashcard_ids(
            repository=repository,
            lecture=lecture,
            dry_run=dry_run
        )
        results.append(result)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 60)
    
    updated = sum(1 for r in results if r["status"] in ("updated", "would_update"))
    already_complete = sum(1 for r in results if r["status"] == "already_complete")
    skipped = sum(1 for r in results if r["status"] in ("skipped", "no_flashcards", "empty_flashcards"))
    errors = sum(1 for r in results if r["status"] == "invalid_json")
    
    total_tagged = sum(r["flashcards_tagged"] for r in results)
    total_flashcards = sum(r["flashcards_total"] for r in results)
    
    logger.info(f"Lectures processed: {len(results)}")
    logger.info(f"  - Updated/Would update: {updated}")
    logger.info(f"  - Already complete: {already_complete}")
    logger.info(f"  - Skipped (no flashcards): {skipped}")
    logger.info(f"  - Errors: {errors}")
    logger.info(f"\nFlashcards:")
    logger.info(f"  - Total: {total_flashcards}")
    logger.info(f"  - Newly tagged: {total_tagged}")
    
    if dry_run and updated > 0:
        logger.info("\n⚠️  This was a dry run. Run without --dry-run to apply changes.")
    
    # Close pool
    await close_postgres_db()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate flashcard IDs for existing flashcards in the database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--lecture-id",
        type=int,
        help="Only process a specific lecture ID"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_migration(
        dry_run=args.dry_run,
        lecture_id=args.lecture_id
    ))


if __name__ == "__main__":
    main()

