"""
Main entry point for Cognitive Flashcard Generator.

Usage:
    python -m cognitive_flashcard_generator.main [course_id]
    
    If course_id is not provided, all courses in courses.json will be processed.
    
    Example:
        python -m cognitive_flashcard_generator.main MS5260
        python -m cognitive_flashcard_generator.main
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from config import Config
from .generator import CognitiveFlashcardGenerator
from .renderer import DiagramRenderer
from .utils import load_courses, get_course_by_id


def save_flashcards_json(flashcards, metadata, output_path):
    """Save flashcards as JSON with metadata."""
    data = {
        'metadata': metadata,
        'flashcards': flashcards
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved JSON: {output_path}")


def process_course_flashcards(course: Dict[str, Any]) -> None:
    """
    Process flashcard generation for all lectures in a course.
    
    Args:
        course: Course dictionary with metadata and slides list
    """
    course_id = course['course_id']
    course_name = course['course_name']
    
    print(f"\n{'='*80}")
    print(f"📚 Generating Flashcards for: {course_name} ({course_id})")
    print(f"{'='*80}")
    
    # Get course metadata for context
    textbooks = course.get('reference_textbooks', [])
    textbook_reference = "; ".join(textbooks) if textbooks else "No reference textbooks specified"
    
    print(f"\n📖 Course Information:")
    print(f"  • Name: {course_name}")
    print(f"  • Code: {course.get('course_code', 'N/A')}")
    if textbooks:
        print(f"  • Reference Textbooks:")
        for textbook in textbooks:
            print(f"    - {textbook}")
    
    # Define input and output paths
    course_base_dir = Path(f"./courses/{course_id}")
    analysis_dir = course_base_dir / "slide_analysis"
    output_base = course_base_dir / "cognitive_flashcards"
    
    # Check if analysis directory exists
    if not analysis_dir.exists():
        print(f"⚠️  No slide analysis found for this course at: {analysis_dir}")
        print(f"   Please run: python -m pdf_slide_processor.main {course_id}")
        return
    
    # Find all master content files
    master_content_files = list(analysis_dir.glob("*_master_content.txt"))
    
    if not master_content_files:
        print(f"⚠️  No master content files found in {analysis_dir}")
        return
    
    print(f"\n📊 Found {len(master_content_files)} lecture(s) to process")
    
    # Create output base directory
    output_base.mkdir(exist_ok=True)
    
    # Check if Mermaid CLI is available
    has_mermaid = DiagramRenderer.check_mermaid_cli()
    if has_mermaid:
        print(f"\n✅ Mermaid CLI detected - Diagrams will be rendered to PNG")
    else:
        print(f"\n⚠️  Mermaid CLI not found - Diagrams will be saved as code only")
        print(f"    To install: npm install -g @mermaid-js/mermaid-cli")
    
    # Initialize generator with course context
    generator = CognitiveFlashcardGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        course_name=course_name,
        textbook_reference=textbook_reference
    )
    
    # Process each lecture
    for master_content_path in master_content_files:
        lecture_name = master_content_path.stem.replace("_master_content", "")
        
        print(f"\n{'─'*70}")
        print(f"📄 Processing: {lecture_name}")
        print(f"{'─'*70}")
        
        # Load content
        with open(master_content_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 Loaded {len(content):,} characters of content")
        
        # Generate flashcards
        flashcards = generator.generate_flashcards(content, lecture_name)
        
        if not flashcards:
            print(f"⚠️  No flashcards generated for {lecture_name}")
            continue
        
        # Create lecture-specific output directory
        lecture_output_dir = output_base / lecture_name
        lecture_output_dir.mkdir(exist_ok=True)
        
        diagrams_dir = lecture_output_dir / "diagrams"
        diagrams_dir.mkdir(exist_ok=True)
        
        # Render diagrams
        print(f"\n🎨 Rendering diagrams...")
        rendered_count = 0
        
        for i, card in enumerate(flashcards, 1):
            mermaid_code = card.get('mermaid_code', '').strip()
            
            if mermaid_code and has_mermaid:
                diagram_filename = f"{lecture_name}_card_{i:03d}.png"
                diagram_path = diagrams_dir / diagram_filename
                
                if DiagramRenderer.render_diagram(mermaid_code, str(diagram_path)):
                    card['diagram_image_path'] = f"diagrams/{diagram_filename}"
                    rendered_count += 1
                    print(f"  ✓ Rendered diagram {i}")
                else:
                    card['diagram_image_path'] = ""
                    print(f"  ⚠️  Failed to render diagram {i}")
            else:
                card['diagram_image_path'] = ""
        
        if rendered_count > 0:
            print(f"✅ Rendered {rendered_count} diagrams")
        
        # Prepare metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_cards': len(flashcards),
            'course_name': course_name,
            'course_id': course_id,
            'course_code': course.get('course_code', 'N/A'),
            'textbook_reference': textbook_reference,
            'source': lecture_name
        }
        
        # Export as JSON
        print(f"\n💾 Exporting flashcards...")
        
        save_flashcards_json(
            flashcards,
            metadata,
            str(lecture_output_dir / f"{lecture_name}_cognitive_flashcards.json")
        )
        
        print(f"\n✅ Complete! Output saved to: {lecture_output_dir}")
    
    # Course summary
    print(f"\n{'='*80}")
    print(f"✅ COURSE COMPLETE: {course_name}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"  • Lectures processed: {len(master_content_files)}")
    print(f"  • Output directory: {output_base}/")
    print(f"\n💡 Next Steps:")
    print(f"   1. Review the generated flashcards JSON files")
    print(f"   2. View diagrams in the diagrams/ folders")
    print(f"   3. Use JSON for your React frontend")


def main():
    """Main execution function."""
    
    print("🎓 Course-Based Cognitive Flashcard Generator\n")
    
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
    
    # Check for command-line argument (specific course ID)
    target_course_id = None
    if len(sys.argv) > 1:
        target_course_id = sys.argv[1]
        print(f"🎯 Target course: {target_course_id}")
    
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
        
        process_course_flashcards(course)
    else:
        # Process all courses
        print(f"\n🔄 Processing all courses...\n")
        for i, course in enumerate(courses, 1):
            print(f"\n{'#'*80}")
            print(f"# Course {i}/{len(courses)}")
            print(f"{'#'*80}")
            process_course_flashcards(course)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL COURSES COMPLETE!")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()

