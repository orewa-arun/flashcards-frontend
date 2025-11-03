#!/usr/bin/env python3
"""
Quiz Generator Entry Point

Generates multi-level quiz questions from existing cognitive flashcards.

Usage:
    python generate_quizzes.py [course_id] [lecture_name]
    
    If course_id is not provided, all courses will be processed.
    If lecture_name is provided, only that specific lecture will be processed.
    
    Examples:
        python generate_quizzes.py MS5130
        python generate_quizzes.py MS5130 OR_lec_1
        python generate_quizzes.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from cognitive_flashcard_generator.utils import load_courses, get_course_by_id
from cognitive_flashcard_generator.main import process_course_quizzes


def main():
    """Main execution function for quiz generation."""
    
    print("🎯 Multi-Level Quiz Generator\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        return
    
    # Load courses
    courses = load_courses()
    if not courses:
        return
    
    print(f"📚 Loaded {len(courses)} course(s) from courses.json")
    
    # Check for command-line arguments
    target_course_id = None
    lecture_name = None
    
    if len(sys.argv) > 1:
        target_course_id = sys.argv[1]
        print(f"🎯 Target course: {target_course_id}")
    
    if len(sys.argv) > 2:
        lecture_name = sys.argv[2]
        print(f"🎯 Target lecture: {lecture_name}")
    
    # Process courses
    if target_course_id:
        # Process only the specified course
        course = get_course_by_id(target_course_id, courses)
        if not course:
            print(f"❌ Error: Course '{target_course_id}' not found in courses.json")
            print(f"\nAvailable courses:")
            for c in courses:
                print(f"  • {c['course_id']}: {c['course_name']}")
            return
        
        process_course_quizzes(course, lecture_name)
    else:
        # Process all courses (lecture_name is ignored when processing all courses)
        if lecture_name:
            print(f"⚠️  Note: lecture_name '{lecture_name}' ignored when processing all courses")
            print(f"   Please specify a course_id to use lecture_name")
        
        print(f"\n🔄 Processing all courses...\n")
        for i, course in enumerate(courses, 1):
            print(f"\n{'#'*80}")
            print(f"# Course {i}/{len(courses)}")
            print(f"{'#'*80}")
            process_course_quizzes(course)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL QUIZZES COMPLETE!")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()

