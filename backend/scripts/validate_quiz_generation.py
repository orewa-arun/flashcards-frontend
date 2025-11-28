"""
Script to validate quiz generation for a lecture.

Checks that each flashcard has the expected number of questions (default: 2)
at each difficulty level (easy, medium, hard, boss).

Usage:
    python -m scripts.validate_quiz_generation --lecture-id 4
    python -m scripts.validate_quiz_generation --lecture-id 4 --expected-questions 2
"""

import argparse
import asyncio
import json
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Any, Set

from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.postgres import init_postgres_db, close_postgres_db, get_postgres_pool
from app.repositories.content_repository import ContentRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Level mapping
LEVEL_NAMES = {1: "easy", 2: "medium", 3: "hard", 4: "boss"}
LEVEL_NUMBERS = {"easy": 1, "medium": 2, "hard": 3, "boss": 4}


async def validate_quiz_generation(
    lecture_id: int,
    expected_questions_per_level: int = 2
) -> Dict[str, Any]:
    """
    Validate quiz generation for a lecture.
    
    Args:
        lecture_id: ID of the lecture to validate
        expected_questions_per_level: Expected number of questions per flashcard per level
        
    Returns:
        Dict with validation results
    """
    # Initialize database
    await init_postgres_db()
    pool = await get_postgres_pool()
    repository = ContentRepository(pool)
    
    try:
        # Fetch lecture
        logger.info(f"Fetching lecture {lecture_id}...")
        lecture = await repository.get_lecture_by_id(lecture_id)
        
        if not lecture:
            raise ValueError(f"Lecture with ID {lecture_id} not found")
        
        logger.info(f"Found lecture: {lecture['lecture_title']}")
        
        # Check quiz status
        quiz_status = lecture.get("quiz_status")
        if quiz_status != "completed":
            logger.warning(f"Quiz status is '{quiz_status}', not 'completed'. Results may be incomplete.")
        
        # Parse flashcards
        flashcards_data = lecture.get("flashcards")
        if not flashcards_data:
            raise ValueError("No flashcards found in lecture")
        
        if isinstance(flashcards_data, str):
            flashcards_data = json.loads(flashcards_data)
        
        flashcards_list = flashcards_data.get("flashcards", [])
        if not flashcards_list:
            raise ValueError("Flashcards list is empty")
        
        logger.info(f"Found {len(flashcards_list)} flashcards")
        
        # Extract flashcard IDs
        flashcard_ids: Set[str] = set()
        flashcard_id_to_index: Dict[str, int] = {}
        
        for idx, flashcard in enumerate(flashcards_list):
            flashcard_id = flashcard.get("flashcard_id")
            if flashcard_id:
                flashcard_ids.add(flashcard_id)
                flashcard_id_to_index[flashcard_id] = idx
            else:
                logger.warning(f"Flashcard at index {idx} has no flashcard_id")
        
        logger.info(f"Found {len(flashcard_ids)} flashcards with IDs")
        
        # Parse quizzes
        quizzes_data = lecture.get("quizzes")
        if not quizzes_data:
            raise ValueError("No quizzes found in lecture")
        
        if isinstance(quizzes_data, str):
            quizzes_data = json.loads(quizzes_data)
        
        levels_data = quizzes_data.get("levels", [])
        if not levels_data:
            raise ValueError("No quiz levels found")
        
        logger.info(f"Found {len(levels_data)} quiz levels")
        
        # Map questions to flashcards by level
        # Structure: {level_name: {flashcard_id: [questions]}}
        questions_by_level_and_flashcard: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Track all questions
        total_questions_by_level: Dict[str, int] = defaultdict(int)
        questions_without_source: List[Dict[str, Any]] = []
        questions_with_invalid_source: List[Dict[str, Any]] = []
        
        for level_data in levels_data:
            level_num = level_data.get("level")
            level_name = LEVEL_NAMES.get(level_num, f"level_{level_num}")
            questions = level_data.get("questions", [])
            
            total_questions_by_level[level_name] = len(questions)
            logger.info(f"Level {level_num} ({level_name}): {len(questions)} questions")
            
            for question in questions:
                source_flashcard_id = question.get("source_flashcard_id")
                
                if not source_flashcard_id:
                    questions_without_source.append({
                        "level": level_name,
                        "question_text": question.get("question_text", "N/A")[:50]
                    })
                elif source_flashcard_id not in flashcard_ids:
                    questions_with_invalid_source.append({
                        "level": level_name,
                        "source_flashcard_id": source_flashcard_id,
                        "question_text": question.get("question_text", "N/A")[:50]
                    })
                else:
                    questions_by_level_and_flashcard[level_name][source_flashcard_id].append(question)
        
        # Validate each flashcard
        validation_results: Dict[str, Dict[str, Any]] = {}
        shortfalls: List[Dict[str, Any]] = []
        
        for flashcard_id in sorted(flashcard_ids):
            flashcard_index = flashcard_id_to_index[flashcard_id]
            flashcard = flashcards_list[flashcard_index]
            
            result = {
                "flashcard_id": flashcard_id,
                "flashcard_index": flashcard_index,
                "question": flashcard.get("question", "N/A")[:50],
                "levels": {}
            }
            
            for level_name in ["easy", "medium", "hard", "boss"]:
                questions = questions_by_level_and_flashcard[level_name].get(flashcard_id, [])
                count = len(questions)
                expected = expected_questions_per_level
                
                result["levels"][level_name] = {
                    "count": count,
                    "expected": expected,
                    "status": "✓" if count == expected else "✗"
                }
                
                if count != expected:
                    shortfalls.append({
                        "flashcard_id": flashcard_id,
                        "flashcard_index": flashcard_index,
                        "level": level_name,
                        "count": count,
                        "expected": expected,
                        "shortfall": expected - count
                    })
            
            validation_results[flashcard_id] = result
        
        # Summary statistics
        total_flashcards = len(flashcard_ids)
        total_expected_questions = total_flashcards * 4 * expected_questions_per_level
        total_actual_questions = sum(total_questions_by_level.values())
        
        # Count flashcards with perfect coverage
        perfect_flashcards = sum(
            1 for result in validation_results.values()
            if all(
                result["levels"][level]["count"] == expected_questions_per_level
                for level in ["easy", "medium", "hard", "boss"]
            )
        )
        
        summary = {
            "lecture_id": lecture_id,
            "lecture_title": lecture["lecture_title"],
            "total_flashcards": total_flashcards,
            "expected_questions_per_flashcard_per_level": expected_questions_per_level,
            "total_expected_questions": total_expected_questions,
            "total_actual_questions": total_actual_questions,
            "questions_by_level": dict(total_questions_by_level),
            "perfect_flashcards": perfect_flashcards,
            "flashcards_with_shortfalls": len(shortfalls),
            "total_shortfalls": len(shortfalls),
            "questions_without_source": len(questions_without_source),
            "questions_with_invalid_source": len(questions_with_invalid_source)
        }
        
        return {
            "summary": summary,
            "validation_results": validation_results,
            "shortfalls": shortfalls,
            "questions_without_source": questions_without_source,
            "questions_with_invalid_source": questions_with_invalid_source
        }
        
    finally:
        await close_postgres_db()


def print_validation_report(results: Dict[str, Any]):
    """Print a formatted validation report."""
    summary = results["summary"]
    shortfalls = results["shortfalls"]
    questions_without_source = results["questions_without_source"]
    questions_with_invalid_source = results["questions_with_invalid_source"]
    
    print("\n" + "=" * 80)
    print("QUIZ GENERATION VALIDATION REPORT")
    print("=" * 80)
    print(f"\nLecture ID: {summary['lecture_id']}")
    print(f"Lecture Title: {summary['lecture_title']}")
    print(f"\nTotal Flashcards: {summary['total_flashcards']}")
    print(f"Expected Questions per Flashcard per Level: {summary['expected_questions_per_flashcard_per_level']}")
    print(f"Total Expected Questions: {summary['total_expected_questions']}")
    print(f"Total Actual Questions: {summary['total_actual_questions']}")
    print(f"\nPerfect Flashcards: {summary['perfect_flashcards']}/{summary['total_flashcards']}")
    print(f"Flashcards with Shortfalls: {summary['flashcards_with_shortfalls']}")
    
    print("\n" + "-" * 80)
    print("QUESTIONS BY LEVEL")
    print("-" * 80)
    for level_name in ["easy", "medium", "hard", "boss"]:
        count = summary["questions_by_level"].get(level_name, 0)
        expected = summary["total_flashcards"] * summary["expected_questions_per_flashcard_per_level"]
        print(f"  {level_name.upper():8s}: {count:4d} / {expected:4d} expected")
    
    if questions_without_source:
        print("\n" + "-" * 80)
        print(f"⚠️  QUESTIONS WITHOUT SOURCE_FLASHCARD_ID: {len(questions_without_source)}")
        print("-" * 80)
        for q in questions_without_source[:10]:  # Show first 10
            print(f"  Level: {q['level']}, Question: {q['question_text']}...")
        if len(questions_without_source) > 10:
            print(f"  ... and {len(questions_without_source) - 10} more")
    
    if questions_with_invalid_source:
        print("\n" + "-" * 80)
        print(f"⚠️  QUESTIONS WITH INVALID SOURCE_FLASHCARD_ID: {len(questions_with_invalid_source)}")
        print("-" * 80)
        for q in questions_with_invalid_source[:10]:  # Show first 10
            print(f"  Level: {q['level']}, Source ID: {q['source_flashcard_id']}, Question: {q['question_text']}...")
        if len(questions_with_invalid_source) > 10:
            print(f"  ... and {len(questions_with_invalid_source) - 10} more")
    
    if shortfalls:
        print("\n" + "-" * 80)
        print(f"❌ SHORTFALLS DETECTED: {len(shortfalls)}")
        print("-" * 80)
        
        # Group by flashcard
        shortfalls_by_flashcard: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for shortfall in shortfalls:
            shortfalls_by_flashcard[shortfall["flashcard_id"]].append(shortfall)
        
        for flashcard_id, flashcard_shortfalls in sorted(shortfalls_by_flashcard.items()):
            first = flashcard_shortfalls[0]
            print(f"\n  Flashcard ID: {flashcard_id} (Index: {first['flashcard_index']})")
            for shortfall in flashcard_shortfalls:
                print(f"    Level {shortfall['level'].upper():8s}: {shortfall['count']}/{shortfall['expected']} questions (shortfall: {shortfall['shortfall']})")
    else:
        print("\n" + "-" * 80)
        print("✅ NO SHORTFALLS - ALL FLASHCARDS HAVE EXPECTED QUESTIONS")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    
    # Detailed per-flashcard breakdown
    print("\nDETAILED PER-FLASHCARD BREAKDOWN")
    print("=" * 80)
    validation_results = results["validation_results"]
    
    for flashcard_id, result in sorted(validation_results.items()):
        print(f"\nFlashcard ID: {flashcard_id} (Index: {result['flashcard_index']})")
        print(f"  Question: {result['question']}...")
        for level_name in ["easy", "medium", "hard", "boss"]:
            level_data = result["levels"][level_name]
            status = level_data["status"]
            print(f"  {status} {level_name.upper():8s}: {level_data['count']}/{level_data['expected']} questions")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate quiz generation for a lecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.validate_quiz_generation --lecture-id 4
  python -m scripts.validate_quiz_generation --lecture-id 4 --expected-questions 2
        """
    )
    
    parser.add_argument(
        "--lecture-id",
        type=int,
        default=4,
        help="Lecture ID to validate (default: 4)"
    )
    
    parser.add_argument(
        "--expected-questions",
        type=int,
        default=2,
        help="Expected number of questions per flashcard per level (default: 2)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting validation for lecture {args.lecture_id}...")
        results = await validate_quiz_generation(
            lecture_id=args.lecture_id,
            expected_questions_per_level=args.expected_questions
        )
        
        print_validation_report(results)
        
        # Exit with error code if there are shortfalls
        if results["shortfalls"]:
            logger.warning(f"Validation completed with {len(results['shortfalls'])} shortfalls")
            sys.exit(1)
        else:
            logger.info("Validation completed successfully - no shortfalls")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

