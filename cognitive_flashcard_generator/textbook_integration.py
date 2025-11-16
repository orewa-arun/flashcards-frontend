"""
Textbook Integration Module

This module integrates the textbook enrichment pipeline with the existing
flashcard and quiz generation systems.

Usage:
    python textbook_integration.py --course MS5031 --lecture 2
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the enrichment and generation modules
from cognitive_flashcard_generator.textbook_enrichment import TextbookContentEnricher
from cognitive_flashcard_generator.generator import CognitiveFlashcardGenerator
from cognitive_flashcard_generator.quiz_generator import QuizGenerator


class TextbookToLearningMaterials:
    """
    End-to-end pipeline: Textbook topics → Enriched content → Flashcards & Quizzes
    """
    
    def __init__(
        self, 
        courses_json_path: str,
        enriched_content_dir: str = "enriched_content",
        output_base_dir: str = "courses"
    ):
        self.courses_json_path = courses_json_path
        self.enriched_content_dir = Path(enriched_content_dir)
        self.output_base_dir = Path(output_base_dir)
        
        # Initialize the enricher
        self.enricher = TextbookContentEnricher(
            courses_json_path=courses_json_path,
            output_dir=str(self.enriched_content_dir)
        )
        
        # Load courses data
        with open(courses_json_path, 'r') as f:
            self.courses_data = json.load(f)
    
    def get_course(self, course_id: str) -> Optional[Dict]:
        """Get course by ID."""
        for course in self.courses_data:
            if course['course_id'] == course_id:
                return course
        return None
    
    def generate_all_materials_for_lecture(
        self,
        course_id: str,
        lecture_number: str,
        skip_enrichment: bool = False
    ) -> Dict:
        """
        Complete pipeline: Enrich content → Generate flashcards → Generate quizzes
        
        Args:
            course_id: Course ID (e.g., "MS5031")
            lecture_number: Lecture number (e.g., "2")
            skip_enrichment: If True, use existing enriched content
            
        Returns:
            Dictionary with paths to generated materials
        """
        
        print(f"\n{'='*80}")
        print(f"TEXTBOOK-TO-LEARNING-MATERIALS PIPELINE")
        print(f"Course: {course_id} | Lecture: {lecture_number}")
        print(f"{'='*80}\n")
        
        # Step 1: Enrich content (or load existing)
        lecture_id = f"{course_id}_lecture_{lecture_number}"
        enriched_content_path = self.enriched_content_dir / course_id / f"{lecture_id}.txt"
        
        if not skip_enrichment or not enriched_content_path.exists():
            print("STEP 1: Content Enrichment")
            print("-" * 80)
            enriched_content = self.enricher.enrich_course(course_id)
            print(f"✓ Content enriched and saved\n")
        else:
            print("STEP 1: Loading existing enriched content")
            print("-" * 80)
            with open(enriched_content_path, 'r', encoding='utf-8') as f:
                enriched_content_text = f.read()
            print(f"✓ Loaded from {enriched_content_path}\n")
        
        # Step 2: Generate flashcards
        print("STEP 2: Flashcard Generation")
        print("-" * 80)
        
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Read enriched content
        with open(enriched_content_path, 'r', encoding='utf-8') as f:
            enriched_content_text = f.read()
        
        # Get course metadata
        course_name = course['course_name']
        course_code = course['course_code']
        textbook = course['reference_textbooks'][0] if course['reference_textbooks'] else ""
        
        # Get API key
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize flashcard generator
        flashcard_gen = CognitiveFlashcardGenerator(
            api_key=api_key,
            model="gemini-2.5-flash",
            course_name=course_name,
            textbook_reference=textbook
        )
        
        # Generate flashcards
        print("Generating flashcards from enriched content...")
        flashcards = flashcard_gen.generate_flashcards(
            content=enriched_content_text,
            source_name=f"{course_code} Lecture {lecture_number}"
        )
        
        # Save flashcards
        output_dir = self.output_base_dir / course_id / "cognitive_flashcards"
        output_dir.mkdir(parents=True, exist_ok=True)
        flashcards_path = output_dir / f"{course_code}_lec_{lecture_number}.json"
        
        with open(flashcards_path, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Flashcards saved to: {flashcards_path}\n")
        
        # Step 3: Generate quizzes (all levels)
        print("STEP 3: Quiz Generation (Levels 1-4)")
        print("-" * 80)
        
        # Initialize quiz generator
        quiz_gen = QuizGenerator(
            api_key=api_key,
            model="gemini-2.5-flash",
            course_name=course_name,
            textbook_reference=textbook
        )
        
        quiz_paths = {}
        for level in range(1, 5):
            print(f"\nGenerating Level {level} quiz...")
            
            # Generate quiz questions from flashcards
            quiz_questions = quiz_gen.generate_quiz_questions(
                flashcards_chunk=flashcards,
                level=level,
                chunk_info=f"Lecture {lecture_number}"
            )
            
            # Save quiz
            quiz_output_dir = self.output_base_dir / course_id / "quiz"
            quiz_output_dir.mkdir(parents=True, exist_ok=True)
            quiz_path = quiz_output_dir / f"{course_code}_lec_{lecture_number}_level_{level}.json"
            
            with open(quiz_path, 'w', encoding='utf-8') as f:
                json.dump(quiz_questions, f, indent=2, ensure_ascii=False)
            
            quiz_paths[f"level_{level}"] = str(quiz_path)
            print(f"✓ Level {level} quiz saved to: {quiz_path}")
        
        print()
        
        # Summary
        results = {
            "course_id": course_id,
            "lecture_number": lecture_number,
            "enriched_content_path": str(enriched_content_path),
            "flashcards_path": str(flashcards_path),
            "quiz_paths": quiz_paths
        }
        
        print("\n" + "="*80)
        print("PIPELINE COMPLETE!")
        print("="*80)
        print("\nGenerated Materials:")
        print(f"  📝 Enriched Content: {results['enriched_content_path']}")
        print(f"  🗂️  Flashcards: {results['flashcards_path']}")
        print(f"  📊 Quizzes:")
        for level, path in results['quiz_paths'].items():
            print(f"      - {level}: {path}")
        print()
        
        return results
    
    def generate_all_materials_for_course(
        self,
        course_id: str,
        skip_enrichment: bool = False
    ) -> Dict:
        """
        Generate all learning materials for an entire course.
        
        Args:
            course_id: Course ID (e.g., "MS5031")
            skip_enrichment: If True, use existing enriched content
            
        Returns:
            Dictionary mapping lecture numbers to their generated materials
        """
        
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        print(f"\n{'#'*80}")
        print(f"# FULL COURSE MATERIAL GENERATION")
        print(f"# {course['course_name']} ({course_id})")
        print(f"{'#'*80}\n")
        
        all_results = {}
        
        # Process each lecture that lacks a PDF
        for lecture in course.get('lecture_slides', []):
            if 'pdf_path' in lecture and lecture['pdf_path']:
                continue
            
            lecture_number = lecture.get('lecture_number', 'unknown')
            
            try:
                results = self.generate_all_materials_for_lecture(
                    course_id=course_id,
                    lecture_number=lecture_number,
                    skip_enrichment=skip_enrichment
                )
                all_results[lecture_number] = results
            except Exception as e:
                print(f"❌ Error processing lecture {lecture_number}: {e}")
                all_results[lecture_number] = {"error": str(e)}
        
        return all_results


def main():
    """Command-line interface for the textbook integration pipeline."""
    
    parser = argparse.ArgumentParser(
        description="Generate learning materials from textbook topics"
    )
    parser.add_argument(
        "--course",
        required=True,
        help="Course ID (e.g., MS5031)"
    )
    parser.add_argument(
        "--lecture",
        help="Specific lecture number (optional, processes all if not specified)"
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Use existing enriched content instead of regenerating"
    )
    parser.add_argument(
        "--courses-json",
        default="courses_resources/courses.json",
        help="Path to courses.json file"
    )
    
    args = parser.parse_args()
    
    # Initialize the pipeline
    pipeline = TextbookToLearningMaterials(
        courses_json_path=args.courses_json
    )
    
    # Execute based on arguments
    if args.lecture:
        # Single lecture
        results = pipeline.generate_all_materials_for_lecture(
            course_id=args.course,
            lecture_number=args.lecture,
            skip_enrichment=args.skip_enrichment
        )
    else:
        # Entire course
        results = pipeline.generate_all_materials_for_course(
            course_id=args.course,
            skip_enrichment=args.skip_enrichment
        )
    
    # Save results summary
    results_file = Path("enriched_content") / args.course / "generation_summary.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📋 Results summary saved to: {results_file}")


if __name__ == "__main__":
    main()

