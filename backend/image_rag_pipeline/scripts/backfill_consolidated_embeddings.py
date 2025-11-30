#!/usr/bin/env python3
"""
Backfill script for indexing consolidated semantic chunks into Qdrant.

This script finds all lectures with consolidated_structured_analysis
and indexes their semantic chunks (and optionally flashcards) into Qdrant.

Usage:
    # Backfill all lectures with consolidated analysis
    python backfill_consolidated_embeddings.py
    
    # Backfill a specific lecture
    python backfill_consolidated_embeddings.py --lecture-id 5
    
    # Backfill a specific course
    python backfill_consolidated_embeddings.py --course-code MS5031
    
    # Dry run (don't actually index)
    python backfill_consolidated_embeddings.py --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncpg
from dotenv import load_dotenv

from app.ingestion.loader import IngestionPipeline
from app.ingestion.embedder import Embedder
from app.db.vector_store import VectorStore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_db_pool() -> asyncpg.Pool:
    """Create database connection pool."""
    db_url = os.getenv("POSTGRES_URL", "")
    if not db_url:
        raise RuntimeError("POSTGRES_URL environment variable not set")
    
    # Convert SQLAlchemy URL format to asyncpg format
    db_url = db_url.replace("+asyncpg", "")
    
    return await asyncpg.create_pool(
        db_url,
        min_size=2,
        max_size=10,
        command_timeout=60
    )


async def find_lectures_with_consolidated_analysis(
    pool: asyncpg.Pool,
    course_code: Optional[str] = None,
    lecture_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Find all lectures that have consolidated_structured_analysis.
    
    Args:
        pool: Database connection pool
        course_code: Optional course code to filter by
        lecture_id: Optional specific lecture ID
        
    Returns:
        List of lecture dictionaries
    """
    async with pool.acquire() as conn:
        if lecture_id:
            query = """
                SELECT id, course_code, lecture_title,
                       consolidated_structured_analysis,
                       flashcards, qdrant_status
                FROM lectures
                WHERE id = $1
                  AND consolidated_structured_analysis IS NOT NULL
            """
            rows = await conn.fetch(query, lecture_id)
        elif course_code:
            query = """
                SELECT id, course_code, lecture_title,
                       consolidated_structured_analysis,
                       flashcards, qdrant_status
                FROM lectures
                WHERE course_code = $1
                  AND consolidated_structured_analysis IS NOT NULL
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY id
            """
            rows = await conn.fetch(query, course_code)
        else:
            query = """
                SELECT id, course_code, lecture_title,
                       consolidated_structured_analysis,
                       flashcards, qdrant_status
                FROM lectures
                WHERE consolidated_structured_analysis IS NOT NULL
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY course_code, id
            """
            rows = await conn.fetch(query)
        
        return [dict(row) for row in rows]


async def update_lecture_qdrant_status(
    pool: asyncpg.Pool,
    lecture_id: int,
    status: str
) -> None:
    """Update the qdrant_status for a lecture."""
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE lectures SET qdrant_status = $1 WHERE id = $2",
            status, lecture_id
        )


def index_lecture(
    pipeline: IngestionPipeline,
    lecture: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Index a single lecture's consolidated content.
    
    Args:
        pipeline: Ingestion pipeline instance
        lecture: Lecture dictionary from database
        
    Returns:
        Indexing result dictionary
    """
    lecture_id = lecture["id"]
    course_code = lecture["course_code"]
    lecture_title = lecture.get("lecture_title", f"Lecture {lecture_id}")
    
    # Parse consolidated analysis
    consolidated = lecture.get("consolidated_structured_analysis")
    if isinstance(consolidated, str):
        consolidated = json.loads(consolidated)
    
    # Parse flashcards
    flashcards = lecture.get("flashcards")
    if isinstance(flashcards, str):
        flashcards = json.loads(flashcards)
    
    lecture_metadata = {
        "lecture_id": str(lecture_id),
        "lecture_title": lecture_title
    }
    
    # Use the full ingestion method
    result = pipeline.ingest_lecture_full(
        consolidated_analysis=consolidated,
        flashcards=flashcards,
        course_id=course_code,
        lecture_id=lecture_id,
        lecture_metadata=lecture_metadata,
        include_flashcards=True
    )
    
    return result


async def main():
    parser = argparse.ArgumentParser(
        description="Backfill consolidated semantic chunks into Qdrant"
    )
    parser.add_argument(
        "--lecture-id",
        type=int,
        help="Specific lecture ID to backfill"
    )
    parser.add_argument(
        "--course-code",
        type=str,
        help="Specific course code to backfill"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually index, just show what would be done"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-index even if qdrant_status is already 'completed'"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("CONSOLIDATED CONTENT BACKFILL")
    logger.info("=" * 70)
    
    # Initialize database connection
    logger.info("Connecting to database...")
    pool = await get_db_pool()
    
    try:
        # Find lectures to process
        logger.info("Finding lectures with consolidated analysis...")
        lectures = await find_lectures_with_consolidated_analysis(
            pool,
            course_code=args.course_code,
            lecture_id=args.lecture_id
        )
        
        if not lectures:
            logger.info("No lectures found with consolidated_structured_analysis")
            return
        
        logger.info(f"Found {len(lectures)} lectures to process")
        
        # Filter out already-indexed lectures unless --force
        if not args.force:
            lectures = [
                l for l in lectures 
                if l.get("qdrant_status") != "completed"
            ]
            logger.info(f"After filtering completed: {len(lectures)} lectures to index")
        
        if not lectures:
            logger.info("All lectures already indexed. Use --force to re-index.")
            return
        
        if args.dry_run:
            logger.info("\n[DRY RUN] Would index the following lectures:")
            for lecture in lectures:
                consolidated = lecture.get("consolidated_structured_analysis", {})
                if isinstance(consolidated, str):
                    consolidated = json.loads(consolidated)
                chunk_count = len(consolidated.get("semantic_chunks", []))
                logger.info(
                    f"  - Lecture {lecture['id']}: {lecture['lecture_title']} "
                    f"({lecture['course_code']}) - {chunk_count} chunks"
                )
            return
        
        # Initialize ingestion pipeline
        logger.info("Initializing ingestion pipeline...")
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        
        vector_store = VectorStore(host=qdrant_host, port=qdrant_port)
        embedder = Embedder()
        
        image_dir = os.getenv("IMAGE_OUTPUT_DIR", "/tmp/rag_images")
        os.makedirs(image_dir, exist_ok=True)
        
        pipeline = IngestionPipeline(
            image_output_dir=image_dir,
            vector_store=vector_store,
            embedder=embedder
        )
        
        # Process each lecture
        total_chunks = 0
        total_flashcards = 0
        success_count = 0
        error_count = 0
        
        for i, lecture in enumerate(lectures, 1):
            lecture_id = lecture["id"]
            lecture_title = lecture.get("lecture_title", f"Lecture {lecture_id}")
            course_code = lecture["course_code"]
            
            logger.info(f"\n[{i}/{len(lectures)}] Processing: {lecture_title} ({course_code})")
            
            try:
                # Update status to in_progress
                await update_lecture_qdrant_status(pool, lecture_id, "in_progress")
                
                # Index the lecture
                result = index_lecture(pipeline, lecture)
                
                chunks = result.get("semantic_chunks", 0)
                flashcards = result.get("flashcards", 0)
                
                total_chunks += chunks
                total_flashcards += flashcards
                success_count += 1
                
                # Update status to completed
                await update_lecture_qdrant_status(pool, lecture_id, "completed")
                
                logger.info(f"  ✅ Indexed {chunks} chunks + {flashcards} flashcards")
                
            except Exception as e:
                error_count += 1
                logger.error(f"  ❌ Error: {str(e)}")
                
                # Update status to failed
                await update_lecture_qdrant_status(pool, lecture_id, "failed")
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Lectures processed: {success_count}/{len(lectures)}")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Total semantic chunks indexed: {total_chunks}")
        logger.info(f"Total flashcards indexed: {total_flashcards}")
        
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())


