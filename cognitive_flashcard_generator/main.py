"""
Main entry point for Cognitive Flashcard Generator.

Usage:
    python -m cognitive_flashcard_generator.main [course_id] [slide_analysis_prefix] [mode]
    
    Arguments:
        course_id: Optional course ID to process (e.g., MS5150)
        slide_analysis_prefix: Optional lecture prefix to process (e.g., SI_lec_1)
        mode: Optional mode - "quizzes" or "quizzes-only" to generate only quizzes
    
    If course_id is not provided, all courses in courses.json will be processed.
    If slide_analysis_prefix is provided, only that specific lecture will be processed.
    If mode is "quizzes" or "quizzes-only", only quizzes will be generated (flashcards must exist).
    
    Examples:
        # Generate flashcards and quizzes for a course
        python -m cognitive_flashcard_generator.main MS5150
        
        # Generate flashcards and quizzes for a specific lecture
        python -m cognitive_flashcard_generator.main MS5150 SI_lec_1
        
        # Generate only quizzes for a course (flashcards must already exist)
        python -m cognitive_flashcard_generator.main MS5150 quizzes
        
        # Generate only quizzes for a specific lecture
        python -m cognitive_flashcard_generator.main MS5150 SI_lec_1 quizzes
        
        # Process all courses
        python -m cognitive_flashcard_generator.main
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config import Config
from .generator import CognitiveFlashcardGenerator
from .quiz_generator import QuizGenerator
from .async_generator import AsyncCognitiveFlashcardGenerator
from .async_quiz_generator import AsyncQuizGenerator
from .batch_coordinator import run_batch_generation
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


def save_quiz_json(questions, metadata, output_path):
    """Save quiz questions as JSON with metadata."""
    data = {
        'metadata': metadata,
        'questions': questions
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved Quiz JSON: {output_path}")

# ==============================================================================
# NEW HELPER FUNCTION FOR CHUNKING
# ==============================================================================

def chunk_content(content: str, max_chunk_size: int = 6000, overlap: int = 300) -> List[str]:
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
            title = str(analysis.get('title', '')).strip()
            if title:
                slide_content += f"\nTITLE: {title}\n"
            
            # Add main text content
            main_text = str(analysis.get('main_text', '')).strip()
            if main_text:
                slide_content += f"\nCONTENT:\n{main_text}\n"
            
            # Add key concepts
            key_concepts = analysis.get('key_concepts', [])
            if key_concepts:
                slide_content += f"\nKEY CONCEPTS:\n"
                for concept in key_concepts:
                    slide_content += f"• {str(concept).strip()}\n"
            
            # Add definitions
            definitions = analysis.get('definitions', [])
            if definitions:
                slide_content += f"\nDEFINITIONS:\n"
                for definition in definitions:
                    slide_content += f"• {str(definition).strip()}\n"
            
            # Add questions
            questions = analysis.get('questions', [])
            if questions:
                slide_content += f"\nQUESTIONS:\n"
                for question in questions:
                    slide_content += f"• {str(question).strip()}\n"
            
            # Add diagrams
            diagrams = analysis.get('diagrams', [])
            if diagrams:
                slide_content += f"\nDIAGRAMS:\n"
                for diagram in diagrams:
                    slide_content += f"• {str(diagram).strip()}\n"
            
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


def process_course_flashcards(course: Dict[str, Any], slide_analysis_prefix: Optional[str] = None) -> None:
    """
    Process flashcard generation for all lectures in a course, or a specific lecture.
    
    Args:
        course: Course dictionary with metadata and slides list
        slide_analysis_prefix: Optional prefix to process only a specific lecture (e.g., 'DAA_lec_4')
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
    
    # Find structured analysis JSON files based on slide_analysis_prefix
    if slide_analysis_prefix:
        # Process only the specified lecture
        specific_file = analysis_dir / f"{slide_analysis_prefix}_structured_analysis.json"
        if not specific_file.exists():
            print(f"⚠️  Specified lecture analysis not found: {specific_file}")
            print(f"   Available lectures in {analysis_dir}:")
            for f in analysis_dir.glob("*_structured_analysis.json"):
                print(f"      • {f.stem.replace('_structured_analysis', '')}")
            return
        structured_analysis_files = [specific_file]
        print(f"\n🎯 Processing specific lecture: {slide_analysis_prefix}")
    else:
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
        content_chunks = chunk_content(content, max_chunk_size=6000, overlap=300)
        print(f"📦 Splitting content into {len(content_chunks)} manageable chunk(s)")
        print(f"   📊 Reduced chunk size to 6000 characters to prevent token limit issues")
        
        all_flashcards = []
        
        # Iterate over chunks and generate flashcards for each
        for i, chunk in enumerate(content_chunks, 1):
            chunk_info = f"Chunk {i}/{len(content_chunks)}"
            
            print(f"\n📦 Processing {chunk_info}")
            print(f"   📊 Chunk size: {len(chunk):,} characters")
            print(f"   📊 Estimated tokens: ~{len(chunk) // 4:,}")
            
            # Generate flashcards for the current chunk
            chunk_flashcards = generator.generate_flashcards(
                chunk, 
                lecture_name, 
                chunk_info=chunk_info
            )
            
            if chunk_flashcards:
                print(f"   ✅ Successfully generated {len(chunk_flashcards)} flashcards from {chunk_info}")
                # Add a tracking field (optional but helpful for debugging/review)
                for card in chunk_flashcards:
                    card['source_chunk'] = f"{lecture_name}_{i}"
                
                all_flashcards.extend(chunk_flashcards)
            else:
                print(f"   ⚠️  No flashcards generated from {chunk_info}")
                print(f"   📝 This chunk will be skipped, but processing will continue")
            
        flashcards = all_flashcards
        
        if not flashcards:
            print(f"⚠️  No flashcards generated for {lecture_name}")
            continue
        
        print(f"\n🎉 Total aggregated flashcards for {lecture_name}: {len(flashcards)}")
        
        # Add unique flashcard_id to each flashcard
        print(f"🆔 Adding unique flashcard IDs...")
        for idx, card in enumerate(flashcards, 1):
            card['flashcard_id'] = f"{lecture_name}_{idx}"
        print(f"   ✅ Added IDs from {lecture_name}_1 to {lecture_name}_{len(flashcards)}")
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
            str(lecture_output_dir / f"{lecture_name}_cognitive_flashcards_only.json")
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


def process_course_quizzes(course: Dict[str, Any], slide_analysis_prefix: Optional[str] = None) -> None:
    """
    Process quiz generation for all flashcards in a course.
    
    Args:
        course: Course dictionary with metadata
        slide_analysis_prefix: Optional prefix to process only a specific lecture
    """
    course_id = course['course_id']
    course_name = course['course_name']
    
    print(f"\n{'='*80}")
    print(f"🎯 Generating Quizzes for: {course_name} ({course_id})")
    print(f"{'='*80}")
    
    # Get course metadata
    textbooks = course.get('reference_textbooks', [])
    textbook_reference = "; ".join(textbooks) if textbooks else "No reference textbooks specified"
    
    # Define paths
    course_base_dir = Path(f"./courses/{course_id}")
    flashcards_base = course_base_dir / "cognitive_flashcards"
    quiz_output_dir = course_base_dir / "quiz"
    
    # Check if flashcards directory exists
    if not flashcards_base.exists():
        print(f"⚠️  No flashcards found for this course at: {flashcards_base}")
        print(f"   Please generate flashcards first using the flashcard generator")
        return
    
    # Find all flashcard JSON files based on slide_analysis_prefix
    if slide_analysis_prefix:
        # Process only the specified lecture
        specific_file = flashcards_base / slide_analysis_prefix / f"{slide_analysis_prefix}_cognitive_flashcards_only.json"
        if not specific_file.exists():
            print(f"⚠️  Specified lecture flashcards not found: {specific_file}")
            print(f"   Available lectures in {flashcards_base}:")
            for f in flashcards_base.glob("*/*_cognitive_flashcards_only.json"):
                print(f"      • {f.parent.name}")
            return
        flashcard_files = [specific_file]
        print(f"\n🎯 Processing specific lecture: {slide_analysis_prefix}")
    else:
        # Find all flashcard files
        flashcard_files = list(flashcards_base.glob("*/*_cognitive_flashcards_only.json"))
        if not flashcard_files:
            print(f"⚠️  No flashcard files found in {flashcards_base}")
            return
        print(f"\n📊 Found {len(flashcard_files)} lecture(s) with flashcards")
    
    # Create quiz output directory
    quiz_output_dir.mkdir(exist_ok=True)
    
    # Initialize quiz generator
    quiz_generator = QuizGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        course_name=course_name,
        textbook_reference=textbook_reference
    )
    
    # Process each flashcard file
    for flashcard_file in flashcard_files:
        lecture_name = flashcard_file.parent.name
        
        print(f"\n{'─'*70}")
        print(f"📄 Processing Quizzes for: {lecture_name}")
        print(f"{'─'*70}")
        
        # Load flashcards
        try:
            with open(flashcard_file, 'r', encoding='utf-8') as f:
                flashcard_data = json.load(f)
        except Exception as e:
            print(f"❌ Error loading flashcards from {flashcard_file}: {e}")
            continue
        
        flashcards = flashcard_data.get('flashcards', [])
        if not flashcards:
            print(f"⚠️  No flashcards found in {flashcard_file}")
            continue
        
        print(f"📚 Loaded {len(flashcards)} flashcard(s)")
        
        # Extract content from flashcards for quiz generation
        # For each flashcard, we'll include: question, all answer types, and example
        simplified_flashcards = []
        for idx, card in enumerate(flashcards):
            # Use persistent flashcard_id if available, otherwise fallback to generated ID
            flashcard_id = card.get('flashcard_id', f"{lecture_name}_{idx + 1}")
            
            simplified_card = {
                "id": flashcard_id,
                "question": card.get('question', ''),
                "answers": card.get('answers', {}),
                "example": card.get('example', ''),
                "context": card.get('context', ''),
                "tags": card.get('tags', [])
            }
            simplified_flashcards.append(simplified_card)
        
        # Chunk flashcards into groups of 3-5 for quiz generation
        # Each chunk will be processed separately to avoid token limits
        chunk_size = 4  # 4 flashcards per chunk (4 * 5 = 20 questions per chunk)
        flashcard_chunks = [simplified_flashcards[i:i + chunk_size] 
                           for i in range(0, len(simplified_flashcards), chunk_size)]
        
        print(f"📦 Split into {len(flashcard_chunks)} chunk(s) of ~{chunk_size} flashcards each")
        
        # Generate quizzes for each level (1-4)
        for level in range(1, 5):
            print(f"\n{'~'*60}")
            print(f"🎯 Generating Level {level} Quiz")
            print(f"{'~'*60}")
            
            all_questions = []
            
            # Process each chunk
            for chunk_idx, chunk in enumerate(flashcard_chunks, 1):
                chunk_info = f"Chunk {chunk_idx}/{len(flashcard_chunks)}"
                
                # Generate questions for this chunk
                questions = quiz_generator.generate_quiz_questions(
                    chunk,
                    level=level,
                    chunk_info=chunk_info
                )
                
                if questions:
                    all_questions.extend(questions)
                    print(f"   ✅ Generated {len(questions)} questions from {chunk_info}")
                else:
                    print(f"   ⚠️  No questions generated from {chunk_info}")
            
            if not all_questions:
                print(f"⚠️  No Level {level} questions generated for {lecture_name}")
                continue
            
            print(f"\n🎉 Total Level {level} questions: {len(all_questions)}")
            
            # Prepare metadata
            metadata = {
                'generated_at': datetime.now().isoformat(),
                'total_questions': len(all_questions),
                'course_name': course_name,
                'course_id': course_id,
                'course_code': course.get('course_code', 'N/A'),
                'textbook_reference': textbook_reference,
                'lecture': lecture_name,
                'difficulty_level': level,
                'source_flashcards': len(flashcards)
            }
            
            # Save quiz JSON
            quiz_filename = f"{lecture_name}_level_{level}_quiz.json"
            quiz_output_path = quiz_output_dir / quiz_filename
            
            save_quiz_json(all_questions, metadata, str(quiz_output_path))
            
            print(f"✅ Level {level} quiz saved: {quiz_output_path}")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"✅ QUIZ GENERATION COMPLETE: {course_name}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"  • Lectures processed: {len(flashcard_files)}")
    print(f"  • Quiz output directory: {quiz_output_dir}/")
    print(f"\n💡 Next Steps:")
    print(f"   1. Review the generated quiz JSON files")
    print(f"   2. Integrate quizzes into your learning platform")


def process_course_batch(course: Dict[str, Any], slide_analysis_prefix: Optional[str] = None) -> None:
    """
    Process flashcards and quizzes for a course using batch processing.
    
    Args:
        course: Course dictionary with metadata
        slide_analysis_prefix: Optional prefix to process only a specific lecture
    """
    if not Config.BATCH_PROCESSING_ENABLED:
        # Fall back to sequential processing
        print("⚠️  Batch processing disabled, using sequential mode")
        process_course_flashcards(course, slide_analysis_prefix)
        process_course_quizzes(course, slide_analysis_prefix)
        return
    
    course_id = course['course_id']
    course_name = course['course_name']
    course_code = course.get('course_code', 'N/A')
    
    print(f"\n{'='*80}")
    print(f"🚀 BATCH PROCESSING: {course_name} ({course_id})")
    print(f"{'='*80}")
    
    # Get course metadata
    textbooks = course.get('reference_textbooks', [])
    textbook_reference = "; ".join(textbooks) if textbooks else "No reference textbooks specified"
    
    # Define paths
    course_base_dir = Path(f"./courses/{course_id}")
    slide_analysis_dir = course_base_dir / "slide_analysis"
    flashcards_base = course_base_dir / "cognitive_flashcards"
    quiz_output_dir = course_base_dir / "quiz"
    
    # Check if slide analysis directory exists
    if not slide_analysis_dir.exists():
        print(f"⚠️  No slide analysis found at: {slide_analysis_dir}")
        return
    
    # Find structured analysis files
    if slide_analysis_prefix:
        pattern = f"{slide_analysis_prefix}_structured_analysis.json"
        structured_analysis_files = list(slide_analysis_dir.glob(pattern))
        if not structured_analysis_files:
            print(f"⚠️  No structured analysis file found matching: {pattern}")
            return
    else:
        structured_analysis_files = list(slide_analysis_dir.glob("*_structured_analysis.json"))
        if not structured_analysis_files:
            print(f"⚠️  No structured analysis files found in: {slide_analysis_dir}")
            return
    
    print(f"📊 Found {len(structured_analysis_files)} lecture(s) to process")
    
    # Initialize async generators
    flashcard_generator = AsyncCognitiveFlashcardGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL,
        course_name=course_name,
        textbook_reference=textbook_reference
    )
    
    quiz_generator = AsyncQuizGenerator(
        api_key=Config.GEMINI_API_KEY,
        model="gemini-2.0-flash-exp",
        course_name=course_name,
        textbook_reference=textbook_reference
    )
    
    # ==============================================================================
    # PHASE 1: COLLECT ALL FLASHCARD GENERATION TASKS
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"📋 PHASE 1: Collecting flashcard generation tasks...")
    print(f"{'~'*80}\n")
    
    flashcard_tasks = []
    task_metadata = []  # Store metadata for each task
    
    for structured_analysis_path in structured_analysis_files:
        lecture_name = structured_analysis_path.stem.replace("_structured_analysis", "")
        
        # Load and extract content
        content = extract_content_from_structured_json(structured_analysis_path)
        
        if not content:
            print(f"⚠️  No content extracted from {lecture_name}, skipping")
            continue
        
        # Chunk the content
        content_chunks = chunk_content(content, max_chunk_size=6000, overlap=300)
        print(f"📦 {lecture_name}: {len(content_chunks)} chunk(s)")
        
        # Create tasks for each chunk
        for i, chunk in enumerate(content_chunks, 1):
            task_id = f"{lecture_name}_chunk_{i}"
            chunk_info = f"Chunk {i}/{len(content_chunks)}"
            
            flashcard_tasks.append({
                'content': chunk,
                'source_name': lecture_name,
                'chunk_info': chunk_info,
                'task_id': task_id
            })
            
            task_metadata.append({
                'lecture_name': lecture_name,
                'chunk_index': i,
                'total_chunks': len(content_chunks)
            })
    
    print(f"\n✅ Collected {len(flashcard_tasks)} flashcard generation tasks")
    
    # ==============================================================================
    # PHASE 2: EXECUTE FLASHCARD GENERATION IN BATCH
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"⚡ PHASE 2: Executing flashcard generation batch...")
    print(f"{'~'*80}\n")
    
    # Run batch generation (no quiz tasks yet, so pass empty list)
    flashcard_results, _ = run_batch_generation(
        flashcard_generator,
        quiz_generator,
        flashcard_tasks,
        [],  # No quiz tasks yet
        max_concurrent=Config.MAX_CONCURRENT_REQUESTS
    )
    
    # ==============================================================================
    # PHASE 3: ORGANIZE AND SAVE FLASHCARD RESULTS
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"💾 PHASE 3: Organizing and saving flashcards...")
    print(f"{'~'*80}\n")
    
    # Group results by lecture
    lecture_flashcards = {}
    for result, meta in zip(flashcard_results, task_metadata):
        lecture_name = meta['lecture_name']
        
        if lecture_name not in lecture_flashcards:
            lecture_flashcards[lecture_name] = []
        
        if result['success']:
            # Add source_chunk to each flashcard
            for card in result['flashcards']:
                card['source_chunk'] = f"{lecture_name}_{meta['chunk_index']}"
            
            lecture_flashcards[lecture_name].extend(result['flashcards'])
    
    # Save flashcards for each lecture
    flashcards_base.mkdir(exist_ok=True)
    
    for lecture_name, flashcards in lecture_flashcards.items():
        if not flashcards:
            print(f"⚠️  No flashcards for {lecture_name}")
            continue
        
        # Add unique flashcard_id
        for idx, card in enumerate(flashcards, 1):
            card['flashcard_id'] = f"{lecture_name}_{idx}"
        
        # Create lecture output directory
        lecture_output_dir = flashcards_base / lecture_name
        lecture_output_dir.mkdir(exist_ok=True)
        
        # Prepare metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_cards': len(flashcards),
            'course_name': course_name,
            'course_id': course_id,
            'course_code': course_code,
            'textbook_reference': textbook_reference,
            'source': lecture_name,
            'chunks_processed': max(meta['chunk_index'] for meta in task_metadata if meta['lecture_name'] == lecture_name)
        }
        
        # Save JSON
        output_path = lecture_output_dir / f"{lecture_name}_cognitive_flashcards_only.json"
        save_flashcards_json(flashcards, metadata, str(output_path))
        
        print(f"✅ {lecture_name}: {len(flashcards)} flashcards saved")
    
    # ==============================================================================
    # PHASE 4: COLLECT ALL QUIZ GENERATION TASKS
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"📋 PHASE 4: Collecting quiz generation tasks...")
    print(f"{'~'*80}\n")
    
    quiz_tasks = []
    quiz_metadata = []
    
    quiz_output_dir.mkdir(exist_ok=True)
    
    for lecture_name, flashcards in lecture_flashcards.items():
        if not flashcards:
            continue
        
        # Simplify flashcards for quiz generation
        simplified_flashcards = []
        for card in flashcards:
            simplified = {
                'flashcard_id': card.get('flashcard_id', ''),
                'question': card.get('question', ''),
                'answers': card.get('answers', {}),
                'example': card.get('example', ''),
                'context': card.get('context', ''),
                'tags': card.get('tags', [])
            }
            simplified_flashcards.append(simplified)
        
        # Chunk flashcards (4 per chunk)
        chunk_size = 4
        flashcard_chunks = [simplified_flashcards[i:i + chunk_size] 
                           for i in range(0, len(simplified_flashcards), chunk_size)]
        
        print(f"📦 {lecture_name}: {len(flashcard_chunks)} quiz chunk(s) across 4 levels")
        
        # Create tasks for each level and chunk
        for level in range(1, 5):
            for chunk_idx, chunk in enumerate(flashcard_chunks, 1):
                task_id = f"{lecture_name}_L{level}_chunk_{chunk_idx}"
                chunk_info = f"Chunk {chunk_idx}/{len(flashcard_chunks)}"
                
                quiz_tasks.append({
                    'flashcards_chunk': chunk,
                    'level': level,
                    'chunk_info': chunk_info,
                    'task_id': task_id
                })
                
                quiz_metadata.append({
                    'lecture_name': lecture_name,
                    'level': level,
                    'chunk_index': chunk_idx,
                    'total_chunks': len(flashcard_chunks),
                    'total_flashcards': len(flashcards)
                })
    
    print(f"\n✅ Collected {len(quiz_tasks)} quiz generation tasks")
    
    # ==============================================================================
    # PHASE 5: EXECUTE QUIZ GENERATION IN BATCH
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"⚡ PHASE 5: Executing quiz generation batch...")
    print(f"{'~'*80}\n")
    
    _, quiz_results = run_batch_generation(
        flashcard_generator,
        quiz_generator,
        [],  # No flashcard tasks
        quiz_tasks,
        max_concurrent=Config.MAX_CONCURRENT_REQUESTS
    )
    
    # ==============================================================================
    # PHASE 6: ORGANIZE AND SAVE QUIZ RESULTS
    # ==============================================================================
    print(f"\n{'~'*80}")
    print(f"💾 PHASE 6: Organizing and saving quizzes...")
    print(f"{'~'*80}\n")
    
    # Group results by lecture and level
    lecture_level_questions = {}
    for result, meta in zip(quiz_results, quiz_metadata):
        lecture_name = meta['lecture_name']
        level = meta['level']
        key = (lecture_name, level)
        
        if key not in lecture_level_questions:
            lecture_level_questions[key] = []
        
        if result['success']:
            lecture_level_questions[key].extend(result['questions'])
    
    # Save quizzes for each lecture and level
    for (lecture_name, level), questions in lecture_level_questions.items():
        if not questions:
            print(f"⚠️  No Level {level} questions for {lecture_name}")
            continue
        
        # Get metadata for this lecture
        lecture_meta = next((m for m in quiz_metadata 
                           if m['lecture_name'] == lecture_name and m['level'] == level), None)
        
        if not lecture_meta:
            continue
        
        # Prepare metadata
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'total_questions': len(questions),
            'course_name': course_name,
            'course_id': course_id,
            'course_code': course_code,
            'textbook_reference': textbook_reference,
            'lecture': lecture_name,
            'difficulty_level': level,
            'source_flashcards': lecture_meta['total_flashcards']
        }
        
        # Save quiz JSON
        quiz_filename = f"{lecture_name}_level_{level}_quiz.json"
        quiz_output_path = quiz_output_dir / quiz_filename
        save_quiz_json(questions, metadata, str(quiz_output_path))
        
        print(f"✅ {lecture_name} Level {level}: {len(questions)} questions saved")
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"✅ BATCH PROCESSING COMPLETE: {course_name}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"  • Lectures processed: {len(lecture_flashcards)}")
    print(f"  • Total flashcards: {sum(len(cards) for cards in lecture_flashcards.values())}")
    print(f"  • Total quiz questions: {sum(len(questions) for questions in lecture_level_questions.values())}")
    print(f"  • Flashcard output: {flashcards_base}/")
    print(f"  • Quiz output: {quiz_output_dir}/")
    print(f"{'='*80}\n")


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
    
    # Check for command-line arguments
    target_course_id = None
    slide_analysis_prefix = None
    mode = None  # "quizzes" or "quizzes-only" to generate only quizzes
    
    if len(sys.argv) > 1:
        target_course_id = sys.argv[1]
        print(f"🎯 Target course: {target_course_id}")
    
    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        # Check if it's a mode flag
        if arg2.lower() in ["quizzes", "quizzes-only"]:
            mode = arg2.lower()
            print(f"🎯 Mode: Quizzes only")
        else:
            slide_analysis_prefix = arg2
        print(f"🎯 Target lecture: {slide_analysis_prefix}")
    
    if len(sys.argv) > 3:
        mode = sys.argv[3].lower()
        if mode in ["quizzes", "quizzes-only"]:
            print(f"🎯 Mode: Quizzes only")
        else:
            print(f"⚠️  Unknown mode: {mode}, ignoring")
            mode = None
    
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
        
        # Check if mode is quizzes-only
        if mode in ["quizzes", "quizzes-only"]:
            print(f"\n📝 Quiz-only mode: Generating quizzes only (flashcards must already exist)")
            process_course_quizzes(course, slide_analysis_prefix)
        else:
            # Use batch processing if enabled, otherwise fall back to sequential
            if Config.BATCH_PROCESSING_ENABLED:
                process_course_batch(course, slide_analysis_prefix)
            else:
        process_course_flashcards(course, slide_analysis_prefix)
                process_course_quizzes(course, slide_analysis_prefix)
    else:
        # Process all courses (slide_analysis_prefix is ignored when processing all courses)
        if slide_analysis_prefix:
            print(f"⚠️  Note: slide_analysis_prefix '{slide_analysis_prefix}' ignored when processing all courses")
            print(f"   Please specify a course_id to use slide_analysis_prefix")
        
        # Check if mode is quizzes-only for all courses
        if mode in ["quizzes", "quizzes-only"]:
            print(f"\n📝 Quiz-only mode: Generating quizzes only for all courses (flashcards must already exist)")
        else:
        print(f"\n🔄 Processing all courses...\n")
        
        for i, course in enumerate(courses, 1):
            print(f"\n{'#'*80}")
            print(f"# Course {i}/{len(courses)}")
            print(f"{'#'*80}")
            
            # Check if mode is quizzes-only
            if mode in ["quizzes", "quizzes-only"]:
                process_course_quizzes(course)
            else:
                # Use batch processing if enabled
                if Config.BATCH_PROCESSING_ENABLED:
                    process_course_batch(course)
                else:
            process_course_flashcards(course)
                    process_course_quizzes(course)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL COURSES COMPLETE!")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()