"""
Content Orchestration Module

This module provides unified orchestration for generating flashcards and quizzes
from both slide-based and textbook-based content sources.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from cognitive_flashcard_generator.generator import CognitiveFlashcardGenerator
from cognitive_flashcard_generator.quiz_generator import QuizGenerator
from cognitive_flashcard_generator.validate_quiz_consistency import (
    validate_flashcard_quiz_consistency,
    validate_flashcards_have_ids
)


def chunk_content(content: str, max_chunk_size: int = 25000, overlap: int = 500) -> List[str]:
    """
    Splits the large content string into smaller chunks with an overlap.
    
    Args:
        content: The full text content.
        max_chunk_size: Maximum size of a chunk (default: 25000 for textbook content).
        overlap: Overlap size to provide context to the next chunk (default: 500).
        
    Returns:
        A list of content strings (chunks).
    """
    chunks = []
    current_position = 0
    total_length = len(content)
    
    # Find all section boundaries (marked by "##" or "===")
    section_boundaries = []
    section_pattern = re.compile(r'\n(#{1,3}|={3,})\s')
    for match in section_pattern.finditer(content):
        section_boundaries.append(match.start())
    
    while current_position < total_length:
        # Determine the end of the chunk (max size from current position)
        end_position = min(current_position + max_chunk_size, total_length)
        
        # Try to find a natural boundary (section break) near the end
        if end_position < total_length:
            # Look for section boundaries within the last 20% of the chunk
            search_start = int(end_position - max_chunk_size * 0.2)
            nearby_boundaries = [b for b in section_boundaries if search_start <= b < end_position]
            
            if nearby_boundaries:
                # Use the last section boundary as the split point
                end_position = nearby_boundaries[-1]
        
        # Extract chunk
        chunk = content[current_position:end_position].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move to the next position with overlap (but ensure we're progressing)
        if end_position >= total_length:
            break
        
        next_position = end_position - overlap
        
        # Ensure we're making progress (advance at least half the chunk size)
        if next_position <= current_position:
            next_position = current_position + (max_chunk_size // 2)
        
        current_position = next_position
    
    return chunks


class ContentOrchestrator:
    """Orchestrates flashcard and quiz generation from various content sources."""
    
    def __init__(self, courses_json_path: str, output_base_dir: str = "courses"):
        self.courses_json_path = courses_json_path
        self.output_base_dir = Path(output_base_dir)
        
        # Load courses data
        with open(courses_json_path, 'r') as f:
            self.courses_data = json.load(f)
        
        # Get API key
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    def get_course(self, course_id: str) -> Optional[Dict]:
        """Get course by ID."""
        for course in self.courses_data:
            if course['course_id'] == course_id:
                return course
        return None
    
    def get_lecture(self, course: Dict, lecture_number: str) -> Optional[Dict]:
        """Get a specific lecture by number."""
        for lecture in course.get('lecture_slides', []):
            if str(lecture.get('lecture_number')) == str(lecture_number):
                return lecture
        return None
    
    def is_slide_based(self, lecture: Dict) -> bool:
        """
        Determine if a lecture is slide-based.
        
        Args:
            lecture: Lecture dictionary
            
        Returns:
            True if slide-based (hasPDF is True or missing), False otherwise
        """
        has_pdf = lecture.get('hasPDF')
        
        # If hasPDF is explicitly False, it's textbook-based
        if has_pdf is False:
            return False
        
        # If hasPDF is True or missing (None), treat as slide-based
        return True
    
    def resolve_content_source(self, course: Dict, lecture: Dict, lecture_number: str) -> tuple[str, Path]:
        """
        Resolve the content source for a lecture.
        
        Args:
            course: Course dictionary
            lecture: Lecture dictionary
            lecture_number: Lecture number
            
        Returns:
            Tuple of (content_type, content_path)
            content_type: "structured_analysis" or "enhanced_content"
            content_path: Path to the content file
        """
        course_id = course['course_id']
        course_code = course['course_code']
        
        if self.is_slide_based(lecture):
            # For slide-based, look for structured analysis
            # The PDF processor saves files as: {pdf_stem}_structured_analysis.json
            # Get the PDF stem from the pdf_path to match the actual filename
            pdf_path = lecture.get('pdf_path', '')
            if pdf_path:
                from pathlib import Path as PathLib
                pdf_stem = PathLib(pdf_path).stem  # e.g., "MIS_lec_5" from "MIS_lec_5.pdf"
            else:
                # Fallback: construct from course_code and lecture_number
                pdf_stem = f"{course_code}_lec_{lecture_number}"
            
            # Primary path: structured_analysis.json in slide_analysis directory
            # Use output_base_dir directly (defaults to "courses/")
            structured_path = self.output_base_dir / course_id / "slide_analysis" / f"{pdf_stem}_structured_analysis.json"
            
            # Fallback: check for master_content.txt (legacy support)
            master_content_path = self.output_base_dir / course_id / "slide_analysis" / f"{pdf_stem}_master_content.txt"
            
            # Try structured_analysis.json first (current format)
            if structured_path.exists():
                return ("structured_analysis", structured_path)
            
            # Fallback to master_content.txt if it exists
            if master_content_path.exists():
                return ("structured_analysis", master_content_path)
            
            # If nothing found, return the expected structured_analysis path (will raise error in load_content)
            return ("structured_analysis", structured_path)
        else:
            # For textbook-based, use enhanced content
            enhanced_path = self.output_base_dir.parent / "enriched_content" / course_id / f"{course_id}_lecture_{lecture_number}_enhanced.txt"
            return ("enhanced_content", enhanced_path)
    
    def load_content(self, content_path: Path, content_type: str) -> str:
        """
        Load content from file.
        
        Args:
            content_path: Path to content file
            content_type: Type of content
            
        Returns:
            Content as string
        """
        if not content_path.exists():
            raise FileNotFoundError(f"Content file not found: {content_path}")
        
        # If it's JSON (structured analysis), use the proper extraction function
        if content_path.suffix == '.json':
            # Import the extraction function from main.py
            from cognitive_flashcard_generator.main import extract_content_from_structured_json
            return extract_content_from_structured_json(content_path)
        
        # For text files (master_content.txt or enhanced content), read directly
        with open(content_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_flashcards_for_lecture(
        self,
        course_id: str,
        lecture_number: str,
        min_cards_threshold: int = 12  # Increased from 5 to 12 for better coverage
    ) -> Path:
        """
        Generate flashcards for a single lecture.
        
        Args:
            course_id: Course ID (e.g., "MS5031")
            lecture_number: Lecture number (e.g., "2")
            min_cards_threshold: Minimum number of cards expected
            
        Returns:
            Path to generated flashcards JSON file
        """
        # Get course and lecture
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        lecture = self.get_lecture(course, lecture_number)
        if not lecture:
            raise ValueError(f"Lecture {lecture_number} not found in course {course_id}")
        
        course_name = course['course_name']
        course_code = course['course_code']
        textbook = course['reference_textbooks'][0] if course.get('reference_textbooks') else ""
        lecture_name = lecture.get('lecture_name', f"Lecture {lecture_number}")
        
        print(f"\n{'='*80}")
        print(f"GENERATING FLASHCARDS")
        print(f"Course: {course_name} ({course_id})")
        print(f"Lecture: {lecture_name}")
        print(f"{'='*80}\n")
        
        # Resolve content source
        content_type, content_path = self.resolve_content_source(course, lecture, lecture_number)
        
        if self.is_slide_based(lecture):
            print(f"📄 Content source: Slide-based (structured analysis)")
        else:
            print(f"📚 Content source: Textbook-based (enhanced content)")
        print(f"📁 Content path: {content_path}\n")
        
        # Load content
        try:
            master_content = self.load_content(content_path, content_type)
        except FileNotFoundError as e:
            print(f"❌ Error: {e}")
            if not self.is_slide_based(lecture):
                print(f"\n💡 Tip: Run enrichment first:")
                print(f"   python cognitive_flashcard_generator/textbook_enrichment.py --course {course_id} --lecture {lecture_number}\n")
            raise
        
        # Initialize batch coordinator and generator
        generator = CognitiveFlashcardGenerator(
            api_key=self.api_key,
            model="gemini-2.5-flash",
            course_name=course_name,
            textbook_reference=textbook
        )
        
        # Determine chunk size based on content type
        # Slide-based content is more structured/dense, needs smaller chunks to stay within 5-6 card limit
        # Textbook-based content can handle larger chunks
        if self.is_slide_based(lecture):
            max_chunk_size = 10000  # Smaller chunks for slide-based content (aims for 5-6 cards per chunk)
            overlap = 200  # Smaller overlap for slide-based content
            content_source = "slide-based"
        else:
            max_chunk_size = 25000  # Larger chunks for textbook-based content (enhanced content)
            overlap = 500
            content_source = "textbook-based"
        
        print(f"🔍 Content type: {content_source}")
        print(f"📏 Chunk size: {max_chunk_size:,} characters (overlap: {overlap})\n")
        
        # Chunk the content
        chunks = chunk_content(
            master_content,
            max_chunk_size=max_chunk_size,
            overlap=overlap
        )
        
        print(f"📊 Content chunked into {len(chunks)} chunk(s)\n")
        
        # Generate flashcards for each chunk
        all_flashcards = []
        min_cards_per_chunk = 5  # Minimum expected cards per chunk (updated to match prompt: 5-6 cards)
        
        for idx, chunk in enumerate(chunks, 1):
            chunk_info = f"Chunk {idx}/{len(chunks)}"
            print(f"Processing {chunk_info}...")
            
            flashcards = generator.generate_flashcards(
                content=chunk,
                source_name=f"{course_code}_lec_{lecture_number}",
                chunk_info=chunk_info
            )
            
            if flashcards:
                all_flashcards.extend(flashcards)
                print(f"✓ Generated {len(flashcards)} flashcard(s) from {chunk_info}")
                
                # Warn if below expected minimum
                if len(flashcards) < min_cards_per_chunk:
                    print(f"   ⚠️  Below expected minimum of {min_cards_per_chunk} cards per chunk")
                
                # Warn if above maximum (risks JSON truncation)
                if len(flashcards) > 6:
                    print(f"   ⚠️  Generated {len(flashcards)} cards (max recommended: 6) - may risk JSON truncation")
                
                print()
            else:
                print(f"⚠️  No flashcards generated from {chunk_info}\n")
        
        # Check minimum card threshold
        if len(all_flashcards) < min_cards_threshold:
            print(f"\n⚠️  WARNING: Only {len(all_flashcards)} card(s) generated (threshold: {min_cards_threshold})")
            print(f"   This may indicate insufficient content or generation issues.\n")
        
        # Add unique flashcard IDs (required by backend)
        print(f"🆔 Adding unique flashcard IDs...")
        lecture_name = f"{course_code}_lec_{lecture_number}"
        for idx, card in enumerate(all_flashcards, 1):
            card['flashcard_id'] = f"{lecture_name}_{idx}"
        print(f"   ✅ Added IDs from {lecture_name}_1 to {lecture_name}_{len(all_flashcards)}")
        
        # Build output JSON with metadata
        output_data = {
            "metadata": {
                "course_name": course_name,
                "course_id": course_id,
                "course_code": course_code,
                "textbook_reference": textbook,
                "source": f"{course_code}_lec_{lecture_number}",
                "lecture_name": lecture_name,
                "lecture_number": lecture_number,
                "chunks_processed": len(chunks),
                "total_cards": len(all_flashcards),
                "content_type": content_type
            },
            "flashcards": all_flashcards
        }
        
        # Save flashcards in subdirectory structure: cognitive_flashcards/DAA_lec_2/
        output_dir = self.output_base_dir / course_id / "cognitive_flashcards" / f"{course_code}_lec_{lecture_number}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{course_code}_lec_{lecture_number}_cognitive_flashcards_only.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Flashcards saved to: {output_path}")
        print(f"  Total cards: {len(all_flashcards)}\n")
        
        return output_path
    
    def generate_quizzes_for_lecture(
        self,
        course_id: str,
        lecture_number: str
    ) -> Dict[str, Path]:
        """
        Generate quizzes (all levels) for a single lecture.
        
        Args:
            course_id: Course ID (e.g., "MS5031")
            lecture_number: Lecture number (e.g., "2")
            
        Returns:
            Dictionary mapping level to quiz file path
        """
        # Get course and lecture
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        lecture = self.get_lecture(course, lecture_number)
        if not lecture:
            raise ValueError(f"Lecture {lecture_number} not found in course {course_id}")
        
        course_name = course['course_name']
        course_code = course['course_code']
        textbook = course['reference_textbooks'][0] if course.get('reference_textbooks') else ""
        lecture_name = lecture.get('lecture_name', f"Lecture {lecture_number}")
        
        print(f"\n{'='*80}")
        print(f"GENERATING QUIZZES")
        print(f"Course: {course_name} ({course_id})")
        print(f"Lecture: {lecture_name}")
        print(f"{'='*80}\n")
        
        # Load flashcards from subdirectory structure: cognitive_flashcards/DAA_lec_3/
        flashcards_path = self.output_base_dir / course_id / "cognitive_flashcards" / f"{course_code}_lec_{lecture_number}" / f"{course_code}_lec_{lecture_number}_cognitive_flashcards_only.json"
        
        if not flashcards_path.exists():
            raise FileNotFoundError(
                f"Flashcards not found: {flashcards_path}\n"
                f"Generate flashcards first using 'generate-flashcards' subcommand."
            )
        
        with open(flashcards_path, 'r', encoding='utf-8') as f:
            flashcards_data = json.load(f)
        
        flashcards = flashcards_data.get('flashcards', [])
        
        if not flashcards:
            print(f"⚠️  No flashcards found in {flashcards_path}")
            print(f"   Cannot generate quizzes without flashcards.\n")
            return {}
        
        print(f"📚 Loaded {len(flashcards)} flashcard(s)\n")
        
        # Initialize quiz generator
        quiz_gen = QuizGenerator(
            api_key=self.api_key,
            model="gemini-2.5-flash",
            course_name=course_name,
            textbook_reference=textbook
        )
        
        # Generate quizzes for each level
        quiz_paths = {}
        quiz_output_dir = self.output_base_dir / course_id / "quiz"
        quiz_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Chunk flashcards to avoid token limits (3-4 flashcards per batch)
        flashcard_batch_size = 3
        flashcard_batches = [flashcards[i:i + flashcard_batch_size] for i in range(0, len(flashcards), flashcard_batch_size)]
        
        print(f"📦 Flashcards chunked into {len(flashcard_batches)} batch(es) of ~{flashcard_batch_size} flashcards each\n")
        
        for level in range(1, 5):
            print(f"Generating Level {level} quiz...")
            
            all_quiz_questions = []
            
            # Generate questions for each batch of flashcards
            for batch_idx, flashcard_batch in enumerate(flashcard_batches, 1):
                batch_info = f"Lecture {lecture_number}, Batch {batch_idx}/{len(flashcard_batches)}"
                
                batch_questions = quiz_gen.generate_quiz_questions(
                    flashcards_chunk=flashcard_batch,
                    level=level,
                    chunk_info=batch_info
                )
                
                all_quiz_questions.extend(batch_questions)
                print(f"  ✓ Batch {batch_idx}/{len(flashcard_batches)}: {len(batch_questions)} questions")
            
            # Save quiz with proper structure for backend compatibility
            quiz_path = quiz_output_dir / f"{course_code}_lec_{lecture_number}_level_{level}_quiz.json"
            
            quiz_data = {
                "questions": all_quiz_questions
            }
            
            with open(quiz_path, 'w', encoding='utf-8') as f:
                json.dump(quiz_data, f, indent=2, ensure_ascii=False)
            
            quiz_paths[f"level_{level}"] = quiz_path
            print(f"✓ Level {level} quiz saved: {len(all_quiz_questions)} question(s) total\n")
        
        # Validate consistency between flashcard IDs and quiz source_flashcard_ids
        print(f"🔍 Validating quiz consistency...")
        is_valid, errors = validate_flashcard_quiz_consistency(
            course_id=course_id,
            lecture_number=lecture_number,
            base_dir=self.output_base_dir,
            courses_json_path=self.courses_json_path
        )
        
        if not is_valid:
            print(f"\n⚠️  VALIDATION ERRORS:")
            for error in errors:
                print(f"   - {error}")
            raise ValueError(
                f"Quiz validation failed - source_flashcard_ids don't match flashcard_ids. "
                f"This will cause runtime errors in the backend."
            )
        
        return quiz_paths

