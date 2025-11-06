"""
Main entry point for PDF Slide Processor.

This module orchestrates the entire slide processing pipeline:
- Renders PDF slides as images
- Analyzes slides using Gemini Vision
- Extracts and structures content for flashcard generation

Usage:
    python -m pdf_slide_processor.main [course_id] [pdf_name]
    
    If course_id is not provided, all courses will be processed.
    If pdf_name is provided (without .pdf extension), only that lecture will be processed.
    
    Example:
        python -m pdf_slide_processor.main MS5150 SI_lec_1
        python -m pdf_slide_processor.main MS5260

Output:
    - courses/[COURSE_ID]/slide_images/ (rendered slide images)
    - courses/[COURSE_ID]/slide_analysis/ (extracted content and JSON)
"""

import os
import sys
from pathlib import Path

from config import Config
from .renderer import SlideRenderer
from .analyzer import GeminiVisionAnalyzer
from .extractor import InformationExtractor
from .utils import load_courses, get_course_by_id


def process_course(course: dict, target_pdf_name: str = None) -> None:
    """
    Process slides for a given course.

    If target_pdf_name is provided, only that lecture PDF is processed.
    
    Args:
        course: Course dictionary with metadata and slides list
        target_pdf_name: (Optional) The stem of the PDF file to process (e.g., "SI_lec_1").
    """
    course_id = course['course_id']
    course_name = course['course_name']
    
    print(f"\n{'='*80}")
    print(f"📚 Processing Course: {course_name} ({course_id})")
    print(f"{'='*80}")
    
    # Create course-based directory structure
    course_base_dir = f"./courses/{course_id}"
    slide_images_dir = f"{course_base_dir}/slide_images"
    analysis_output_dir = f"{course_base_dir}/slide_analysis"
    
    os.makedirs(slide_images_dir, exist_ok=True)
    os.makedirs(analysis_output_dir, exist_ok=True)
    
    # Display course information
    print(f"\n📖 Course Information:")
    print(f"  • Name: {course_name}")
    print(f"  • Code: {course.get('course_code', 'N/A')}")
    if course.get('reference_textbooks'):
        print(f"  • Reference Textbooks:")
        for textbook in course['reference_textbooks']:
            print(f"    - {textbook}")
    
    # Process each slide deck in the course
    slides_to_process = course.get('lecture_slides', [])
    if not slides_to_process:
        print(f"⚠️  No slides configured for this course")
        return

    # If a specific lecture PDF is targeted, filter the list
    if target_pdf_name:
        slides_to_process = [
            s for s in slides_to_process if Path(s['pdf_path']).stem == target_pdf_name
        ]
        if not slides_to_process:
            print(f"⚠️  PDF name '{target_pdf_name}' not found in course '{course_id}'.")
            # Log available lectures by PDF name
            print("   Available PDF names are:")
            for s in course.get('lecture_slides', []):
                print(f"     - {Path(s['pdf_path']).stem}")
        return
    
    print(f"\n📊 Slides to process: {len(slides_to_process)}")
    
    all_analyzed_slides = []
    
    for slide_deck in slides_to_process:
        pdf_path = slide_deck['pdf_path']
        lecture_name = slide_deck.get('lecture_name', Path(pdf_path).stem)
        
        if not os.path.exists(pdf_path):
            print(f"⚠️  Warning: PDF not found: {pdf_path}")
            continue
        
        print(f"\n{'─'*70}")
        print(f"📄 Processing: {lecture_name}")
        print(f"   Path: {pdf_path}")
        print(f"{'─'*70}")
        
        try:
            # Step 1: Render slides as images
            pdf_name = Path(pdf_path).stem
            lecture_images_dir = f"{slide_images_dir}/{pdf_name}"
            renderer = SlideRenderer(output_dir=lecture_images_dir)
            slides = renderer.render_pdf_to_images(pdf_path)
            
            # Step 2: Analyze slides with Gemini Vision (with course context)
            course_context = {
                'course_name': course_name,
                'course_code': course.get('course_code'),
                'course_description': course.get('course_description'),
                'reference_textbooks': course.get('reference_textbooks', []),
                'lecture_name': lecture_name
            }
            
            analyzer = GeminiVisionAnalyzer(
                api_key=Config.GEMINI_API_KEY,
                model=Config.GEMINI_MODEL,
                course_context=course_context
            )
            
            # Use batching to reduce API costs: 5 slides per call, 10s delay between batches
            analyzed_slides = analyzer.analyze_all_slides(slides, delay_seconds=10, slides_per_batch=5)
            all_analyzed_slides.extend(analyzed_slides)
            
            # Save structured JSON for this lecture
            json_path = os.path.join(analysis_output_dir, f"{pdf_name}_structured_analysis.json")
            InformationExtractor.save_structured_json(analyzed_slides, json_path)
            
            print(f"\n✅ Completed: {lecture_name}")
            print(f"  • Slides analyzed: {len(analyzed_slides)}")
            print(f"  • Structured JSON: {json_path}")
            
        except Exception as e:
            print(f"❌ Error processing {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary for the entire course
    print(f"\n{'='*80}")
    print(f"✅ COURSE COMPLETE: {course_name}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"  • Total slides analyzed: {len(all_analyzed_slides)}")
    print(f"  • Output directory: {course_base_dir}/")
    print(f"  • Slide images: {slide_images_dir}/")
    print(f"  • Analysis files: {analysis_output_dir}/")
    print(f"\n💡 Next step: Use the analysis files for flashcard generation!")


def main():
    """Main execution function."""
    
    print("🚀 Course-Based Intelligent Slide Analyzer with Gemini Vision\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        return
    
    # Load courses from the new location
    courses = load_courses()
    if not courses:
        return
    
    print(f"📚 Loaded {len(courses)} course(s) from courses_resources/courses.json")
    
    # Check for command-line arguments
    target_course_id = sys.argv[1] if len(sys.argv) > 1 else None
    target_pdf_name = sys.argv[2] if len(sys.argv) > 2 else None

    if target_course_id:
        print(f"🎯 Target course: {target_course_id}")
    if target_pdf_name:
        print(f"🎯 Target lecture PDF: {target_pdf_name}")
    
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
        
        process_course(course, target_pdf_name)
    else:
        # Process all courses
        print(f"\n🔄 Processing all courses...\n")
        for i, course in enumerate(courses, 1):
            print(f"\n{'#'*80}")
            print(f"# Course {i}/{len(courses)}")
            print(f"{'#'*80}")
            process_course(course)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL COURSES COMPLETE!")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()

