"""
Script to fetch a lecture from database, apply consolidation, and save output.

Usage:
    python test_consolidation_from_db.py [lecture_id]
    
If lecture_id is not provided, it will pick the first available lecture with analysis.
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.postgres import init_postgres_db, get_postgres_pool, close_postgres_db
from app.repositories.content_repository import ContentRepository
from app.content_generation.analyzers.content_consolidator import ContentConsolidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_lecture_with_analysis(
    repository: ContentRepository,
    lecture_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Find a lecture with structured_analysis containing raw_slide_analyses.
    
    Args:
        repository: Content repository
        lecture_id: Optional specific lecture ID to fetch
        
    Returns:
        Lecture dict or None
    """
    if lecture_id:
        lecture = await repository.get_lecture_by_id(lecture_id)
        if lecture and lecture.get("structured_analysis"):
            structured_analysis = lecture["structured_analysis"]
            if isinstance(structured_analysis, str):
                structured_analysis = json.loads(structured_analysis)
            
            raw_slides = structured_analysis.get("raw_slide_analyses", [])
            if raw_slides:
                logger.info(f"Found lecture {lecture_id} with {len(raw_slides)} slides")
                return lecture
        return None
    
    # Find first lecture with analysis
    lectures = await repository.list_lectures()
    
    for lecture in lectures:
        structured_analysis = lecture.get("structured_analysis")
        if not structured_analysis:
            continue
        
        if isinstance(structured_analysis, str):
            structured_analysis = json.loads(structured_analysis)
        
        raw_slides = structured_analysis.get("raw_slide_analyses", [])
        if raw_slides:
            logger.info(f"Found lecture {lecture['id']} ({lecture['lecture_title']}) with {len(raw_slides)} slides")
            return lecture
    
    return None


async def main():
    """Main execution function."""
    # Parse lecture_id from command line
    lecture_id = None
    if len(sys.argv) > 1:
        try:
            lecture_id = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid lecture_id: {sys.argv[1]}")
            return
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_postgres_db()
        pool = await get_postgres_pool()
        
        # Create repository
        repository = ContentRepository(pool)
        
        # Find lecture with analysis
        logger.info("Searching for lecture with slide analyses...")
        lecture = await find_lecture_with_analysis(repository, lecture_id)
        
        if not lecture:
            logger.error("No lecture found with structured_analysis containing raw_slide_analyses")
            logger.info("Make sure you have at least one lecture with analysis_status='completed'")
            return
        
        # Extract structured_analysis
        structured_analysis = lecture.get("structured_analysis")
        if isinstance(structured_analysis, str):
            structured_analysis = json.loads(structured_analysis)
        
        raw_slide_analyses = structured_analysis.get("raw_slide_analyses", [])
        lecture_title = lecture.get("lecture_title", "Unknown Lecture")
        
        logger.info(f"\n{'='*70}")
        logger.info(f"PROCESSING LECTURE: {lecture_title}")
        logger.info(f"Lecture ID: {lecture['id']}")
        logger.info(f"Course Code: {lecture['course_code']}")
        logger.info(f"Total Slides: {len(raw_slide_analyses)}")
        logger.info(f"{'='*70}\n")
        
        # Apply consolidation
        consolidator = ContentConsolidator(
            topic_similarity_threshold=0.5,
            min_educational_value=0.3,
            consolidate_by_title=True
        )
        
        logger.info("Applying consolidation...")
        result = consolidator.consolidate(
            raw_slide_analyses=raw_slide_analyses,
            lecture_title=lecture_title
        )
        
        # Prepare output
        output_data = {
            "lecture_info": {
                "id": lecture["id"],
                "course_code": lecture["course_code"],
                "lecture_title": lecture_title,
                "analysis_status": lecture.get("analysis_status"),
            },
            "consolidation_stats": {
                "original_slides": result["total_original_slides"],
                "educational_slides": result["educational_slides_count"],
                "filtered_slides": result["filtered_slides_count"],
                "topics_created": result["topic_count"],
                "semantic_chunks": len(result["semantic_chunks"]),
                "summary": result["consolidation_summary"]
            },
            "topics": result["topics"],
            "semantic_chunks": result["semantic_chunks"],
            "full_result": result
        }
        
        # Save to temp folder
        temp_dir = Path(__file__).parent.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Create filename
        safe_title = "".join(c for c in lecture_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]
        output_file = temp_dir / f"consolidation_lecture_{lecture['id']}_{safe_title}.json"
        
        # Write JSON output
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n{'='*70}")
        logger.info("CONSOLIDATION COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"\n📊 STATISTICS:")
        logger.info(f"   Original slides: {result['total_original_slides']}")
        logger.info(f"   Educational slides: {result['educational_slides_count']}")
        logger.info(f"   Filtered (non-educational): {result['filtered_slides_count']}")
        logger.info(f"   Consolidated topics: {result['topic_count']}")
        logger.info(f"   Semantic chunks: {len(result['semantic_chunks'])}")
        
        logger.info(f"\n📝 SUMMARY: {result['consolidation_summary']}")
        
        logger.info(f"\n💾 OUTPUT SAVED TO:")
        logger.info(f"   {output_file}")
        
        # Also create a human-readable summary
        summary_file = temp_dir / f"consolidation_summary_lecture_{lecture['id']}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"CONSOLIDATION SUMMARY\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"Lecture: {lecture_title}\n")
            f.write(f"Lecture ID: {lecture['id']}\n")
            f.write(f"Course Code: {lecture['course_code']}\n\n")
            
            f.write(f"STATISTICS:\n")
            f.write(f"  Original slides: {result['total_original_slides']}\n")
            f.write(f"  Educational slides: {result['educational_slides_count']}\n")
            f.write(f"  Filtered (non-educational): {result['filtered_slides_count']}\n")
            f.write(f"  Consolidated topics: {result['topic_count']}\n")
            f.write(f"  Semantic chunks: {len(result['semantic_chunks'])}\n\n")
            
            f.write(f"SUMMARY: {result['consolidation_summary']}\n\n")
            
            f.write(f"TOPICS:\n")
            f.write(f"{'-'*70}\n")
            for i, topic in enumerate(result['topics'], 1):
                f.write(f"\n{i}. {topic['name'].upper()}\n")
                f.write(f"   Slides: {topic['slides']}\n")
                f.write(f"   Educational Value: {topic['educational_value']:.2f}\n")
                f.write(f"   Key Concepts: {', '.join(topic['key_concepts'][:5])}\n")
                if topic['definitions']:
                    f.write(f"   Definitions: {len(topic['definitions'])}\n")
                if topic['examples']:
                    f.write(f"   Examples: {len(topic['examples'])}\n")
                if topic['diagrams']:
                    f.write(f"   Diagrams: {len(topic['diagrams'])}\n")
            
            f.write(f"\n\nSEMANTIC CHUNKS:\n")
            f.write(f"{'-'*70}\n")
            for i, chunk in enumerate(result['semantic_chunks'], 1):
                f.write(f"\nChunk {i}:\n")
                f.write(f"   Topics: {', '.join(chunk['topics'])}\n")
                f.write(f"   Key Concepts: {', '.join(chunk['key_concepts'][:5])}\n")
                f.write(f"   Content Size: {len(chunk['content'])} chars\n")
                f.write(f"   Educational Value: {chunk['educational_value']:.2f}\n")
                f.write(f"   Preview:\n{chunk['content'][:500]}...\n")
        
        logger.info(f"   {summary_file}")
        logger.info(f"\n✅ Done!\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
    finally:
        # Close database connection
        try:
            await close_postgres_db()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())




