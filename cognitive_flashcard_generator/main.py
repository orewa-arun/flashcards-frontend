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
from typing import Dict, Any, List
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

# ==============================================================================
# NEW HELPER FUNCTION FOR CHUNKING
# ==============================================================================

def chunk_content(content: str, max_chunk_size: int = 15000, overlap: int = 500) -> List[str]:
    """
    Splits the large content string into smaller chunks with an overlap, respecting slide boundaries.
    
    Args:
        content: The full text content.
        max_chunk_size: Maximum size of a chunk.
        overlap: Overlap size to provide context to the next chunk.
        
    Returns:
        A list of content strings (chunks).
    """
    chunks = []
    current_position = 0
    total_length = len(content)
    
    # Find all slide boundaries (marked by "SLIDE X" patterns)
    slide_boundaries = []
    import re
    slide_pattern = re.compile(r'\n={60}\nSLIDE \d+\n={60}\n')
    for match in slide_pattern.finditer(content):
        slide_boundaries.append(match.start())
    
    while current_position < total_length:
        # Determine the end of the chunk (max size from current position)
        end_position = min(current_position + max_chunk_size, total_length)
        
        # If this is not the last chunk, find a good break point
        if end_position < total_length:
            # First, try to break at a slide boundary
            suitable_slide_boundary = None
            for boundary in slide_boundaries:
                if current_position < boundary <= end_position:
                    # Check if breaking here would leave a reasonable chunk size
                    if (boundary - current_position) >= max_chunk_size * 0.3:  # At least 30% of max size
                        suitable_slide_boundary = boundary
                        break
            
            if suitable_slide_boundary:
                chunk_end = suitable_slide_boundary
            else:
                # Fall back to looking for paragraph breaks
                break_point = content.rfind('\n\n', current_position, end_position)
                
                # If a clean break is found, use it, otherwise stick to max size
                if break_point != -1 and (end_position - break_point) < 1000:
                    chunk_end = break_point
                else:
                    chunk_end = end_position
        else:
            # Last chunk
            chunk_end = end_position

        chunk = content[current_position:chunk_end]
        chunks.append(chunk)

        # Set up for the next chunk with an overlap
        if chunk_end < total_length:
            # If we broke at a slide boundary, start the next chunk there (no overlap needed)
            if chunk_end in slide_boundaries:
                current_position = chunk_end
            else:
                # Move back by overlap amount for the next start
                next_start_potential = max(0, chunk_end - overlap)
                
                # Find a clean starting point near the overlap point
                clean_start_point = content.find('\n\n', next_start_potential)
                
                if clean_start_point != -1 and clean_start_point < chunk_end:
                     current_position = clean_start_point + 2 # Start after the newlines
                else:
                     current_position = next_start_potential
        else:
            current_position = total_length # End loop
            
    return chunks

# ==============================================================================
# END NEW HELPER FUNCTION FOR CHUNKING
# ==============================================================================


def extract_content_from_structured_json(json_path: Path) -> str:
    """
    Extract and format content from structured analysis JSON for flashcard generation.
    
    Args:
        json_path: Path to the structured analysis JSON file
        
    Returns:
        Formatted text content suitable for flashcard generation
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct array of slides (MS5031 format)
            slides = data
        elif isinstance(data, dict) and 'slides' in data:
            # Object with slides property (MS5260 format)
            slides = data.get('slides', [])
        else:
            print(f"⚠️  Unrecognized JSON structure in {json_path}")
            return ""
        
        if not slides:
            print(f"⚠️  No slides found in {json_path}")
            return ""
        
        print(f"📊 Processing {len(slides)} slides from structured analysis")
        
        content_parts = []
        
        for slide in slides:
            slide_num = slide.get('page_number', 'Unknown')
            analysis = slide.get('analysis', {})
            
            # Start each slide section
            slide_content = f"\n{'='*60}\n"
            slide_content += f"SLIDE {slide_num}\n"
            slide_content += f"{'='*60}\n"
            
            # Add title if available
            title = analysis.get('title', '').strip()
            if title:
                slide_content += f"\nTITLE: {title}\n"
            
            # Add main text content
            main_text = analysis.get('main_text', '').strip()
            if main_text:
                slide_content += f"\nCONTENT:\n{main_text}\n"
            
            # Add key concepts
            key_concepts = analysis.get('key_concepts', [])
            if key_concepts:
                slide_content += f"\nKEY CONCEPTS:\n"
                for concept in key_concepts:
                    slide_content += f"• {concept}\n"
            
            # Add definitions
            definitions = analysis.get('definitions', [])
            if definitions:
                slide_content += f"\nDEFINITIONS:\n"
                for defn in definitions:
                    term = defn.get('term', '')
                    definition = defn.get('definition', '')
                    if term and definition:
                        slide_content += f"• {term}: {definition}\n"
            
            # Add examples
            examples = analysis.get('examples', [])
            if examples:
                slide_content += f"\nEXAMPLES:\n"
                for example in examples:
                    if isinstance(example, dict):
                        example_text = example.get('description', str(example))
                    else:
                        example_text = str(example)
                    slide_content += f"• {example_text}\n"
            
            # Add diagrams information
            diagrams = analysis.get('diagrams', [])
            if diagrams:
                slide_content += f"\nDIAGRAMS:\n"
                for diagram in diagrams:
                    if isinstance(diagram, dict):
                        diagram_desc = diagram.get('description', str(diagram))
                    else:
                        diagram_desc = str(diagram)
                    slide_content += f"• {diagram_desc}\n"
            
            # Add additional notes
            notes = analysis.get('notes', '').strip()
            if notes:
                slide_content += f"\nNOTES: {notes}\n"
            
            content_parts.append(slide_content)
        
        # Combine all slide content
        full_content = "\n".join(content_parts)
        
        return full_content
        
    except Exception as e:
        print(f"❌ Error extracting content from {json_path}: {e}")
        import traceback
        traceback.print_exc()
        return ""


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
    
    # Find all structured analysis JSON files
    structured_analysis_files = list(analysis_dir.glob("*_structured_analysis.json"))
    
    if not structured_analysis_files:
        print(f"⚠️  No structured analysis files found in {analysis_dir}")
        return
    
    print(f"\n📊 Found {len(structured_analysis_files)} lecture(s) to process")
    
    # Create output base directory
    output_base.mkdir(exist_ok=True)
    
    # Check if Mermaid CLI is available
    has_mermaid = DiagramRenderer.check_mermaid_cli()
    if has_mermaid:
        print(f"\n✅ Mermaid CLI detected - Diagrams will be rendered to PNG")
    else:
        print(f"\n⚠️  Mermaid CLI not found - Diagrams will be saved as code only")
        print(f"    To install: npm install -g @mermaid-js/mermaid-cli")
    
    # Check if Graphviz is available
    has_graphviz = DiagramRenderer.check_graphviz()
    if has_graphviz:
        print(f"✅ Graphviz detected - Math visualizations will be rendered to PNG")
    else:
        print(f"⚠️  Graphviz not found - Math visualizations will be saved as code only")
        print(f"    To install: brew install graphviz (macOS) or apt-get install graphviz (Linux)")
    
    # Initialize generator with course context
    generator = CognitiveFlashcardGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        course_name=course_name,
        textbook_reference=textbook_reference
    )
    
    # Process each lecture
    for structured_analysis_path in structured_analysis_files:
        lecture_name = structured_analysis_path.stem.replace("_structured_analysis", "")
        
        print(f"\n{'─'*70}")
        print(f"📄 Processing: {lecture_name}")
        print(f"{'─'*70}")
        
        # Load and extract content from structured JSON
        content = extract_content_from_structured_json(structured_analysis_path)
        
        if not content:
            print(f"⚠️  No content extracted from {lecture_name}")
            continue
        
        print(f"📄 Extracted {len(content):,} characters of content from structured analysis")
        
        # ======================================================================
        # CHUNKING AND ITERATIVE GENERATION LOGIC (MODIFIED)
        # ======================================================================
        content_chunks = chunk_content(content, max_chunk_size=10000, overlap=500)
        print(f"📦 Splitting content into {len(content_chunks)} manageable chunk(s)")
        
        all_flashcards = []
        
        # Iterate over chunks and generate flashcards for each
        for i, chunk in enumerate(content_chunks, 1):
            chunk_info = f"Chunk {i}/{len(content_chunks)}"
            
            # Generate flashcards for the current chunk
            chunk_flashcards = generator.generate_flashcards(
                chunk, 
                lecture_name, 
                chunk_info=chunk_info
            )
            
            # Add a tracking field (optional but helpful for debugging/review)
            for card in chunk_flashcards:
                card['source_chunk'] = f"{lecture_name}_{i}"
            
            all_flashcards.extend(chunk_flashcards)
            
        flashcards = all_flashcards
        
        if not flashcards:
            print(f"⚠️  No flashcards generated for {lecture_name}")
            continue
        
        print(f"\n🎉 Total aggregated flashcards for {lecture_name}: {len(flashcards)}")
        # ======================================================================
        # END CHUNKING AND ITERATIVE GENERATION LOGIC
        # ======================================================================
        
        # Create lecture-specific output directory
        lecture_output_dir = output_base / lecture_name
        lecture_output_dir.mkdir(exist_ok=True)
        
        diagrams_dir = lecture_output_dir / "diagrams"
        diagrams_dir.mkdir(exist_ok=True)
        
        # Render diagrams
        print(f"\n🎨 Rendering diagrams...")
        rendered_count = 0
        
        for i, card in enumerate(flashcards, 1):
            # Assign a unique card ID for the filename
            card_id = card.get('source_chunk', lecture_name).replace('/', '_').replace('-', '_')
            
            # Initialize diagram image paths object
            card['diagram_image_paths'] = {}
            
            # Process each diagram type
            mermaid_diagrams = card.get('mermaid_diagrams', {})
            diagram_types = ['concise', 'analogy', 'eli5', 'real_world_use_case', 'common_mistakes', 'example']
            
            for diagram_type in diagram_types:
                mermaid_code = mermaid_diagrams.get(diagram_type, '').strip()
                
                if mermaid_code and has_mermaid:
                    diagram_filename = f"{card_id}_card_{i:03d}_{diagram_type}.png"
                    diagram_path = diagrams_dir / diagram_filename
                    
                    if DiagramRenderer.render_diagram(mermaid_code, str(diagram_path)):
                        card['diagram_image_paths'][diagram_type] = f"diagrams/{diagram_filename}"
                        rendered_count += 1
                    else:
                        card['diagram_image_paths'][diagram_type] = ""
                        print(f"  ⚠️  Failed to render {diagram_type} diagram for card {i}")
                else:
                    card['diagram_image_paths'][diagram_type] = ""
        
        if rendered_count > 0:
            print(f"✅ Rendered {rendered_count} Mermaid diagrams")
        
        # Note: Math visualizations are now rendered directly in the frontend using d3-graphviz
        # No backend rendering needed - the DOT code is preserved in the JSON and rendered on-demand

        # Count math visualizations for statistics
        total_math_viz = 0
        for card in flashcards:
            math_viz = card.get('math_visualizations', {})
            total_math_viz += sum(1 for viz in math_viz.values() if viz.strip())

        if total_math_viz > 0:
            print(f"✅ Preserved {total_math_viz} Graphviz DOT codes for frontend rendering")
        
        # Prepare metadata (UPDATED to include chunk count)
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_cards': len(flashcards),
            'course_name': course_name,
            'course_id': course_id,
            'course_code': course.get('course_code', 'N/A'),
            'textbook_reference': textbook_reference,
            'source': lecture_name,
            'chunks_processed': len(content_chunks), # NEW: Number of chunks processed
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
    print(f"  • Lectures processed: {len(structured_analysis_files)}")
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