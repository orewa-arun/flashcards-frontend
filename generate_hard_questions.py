"""
Hard Quiz Questions Generator - CLI Tool

Generates challenging, tricky quiz questions from structured slide analysis JSON files.

Usage:
    python generate_hard_questions.py [course_id] [lecture_name]
    
    If course_id is not provided, all courses will be processed.
    If lecture_name is provided, only that specific lecture will be processed.
    
Examples:
    python generate_hard_questions.py MS5260
    python generate_hard_questions.py MS5260 MIS_lec_4
    python generate_hard_questions.py
"""

import sys
import json
import os
import re # Import re module
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai

from config import Config


class HardQuestionGenerator:
    """Generator for hard quiz questions using Gemini AI."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        Initialize the hard question generator.
        
        Args:
            api_key: Gemini API key
            model: Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load the hard questions prompt template."""
        prompt_path = Path("prompts/hard_questions_prompt.txt")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                "Please ensure hard_questions_prompt.txt exists in the prompts/ directory."
            )
    
    def _extract_slide_content(self, structured_json_path: Path) -> str:
        """
        Extract formatted slide content from structured analysis JSON.
        
        Args:
            structured_json_path: Path to the structured analysis JSON file
            
        Returns:
            Formatted text content for question generation
        """
        try:
            with open(structured_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                slides = data
            elif isinstance(data, dict) and 'slides' in data:
                slides = data.get('slides', [])
            else:
                print(f"⚠️  Unrecognized JSON structure in {structured_json_path}")
                return ""
            
            if not slides:
                print(f"⚠️  No slides found in {structured_json_path}")
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
                
                # Add title
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
                        if isinstance(defn, dict):
                            term = defn.get('term', '')
                            definition = defn.get('definition', '')
                            if term and definition:
                                slide_content += f"• {term}: {definition}\n"
                        else:
                            slide_content += f"• {defn}\n"
                
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
            print(f"❌ Error extracting content from {structured_json_path}: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def generate_questions(self, content: str, lecture_name: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Generate hard questions from slide content with retry logic.
        
        Args:
            content: Formatted slide content
            lecture_name: Name of the lecture (e.g., 'MIS_lec_4')
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with questions list or None if generation fails
        """
        print(f"\n{'='*70}")
        print(f"🧠 Generating Hard Quiz Questions")
        print(f"📚 Lecture: {lecture_name}")
        print(f"{'='*70}")
        
        for attempt in range(max_retries):
            try:
                print(f"\n🔄 Attempt {attempt + 1}/{max_retries}")
                
                # Prepare the full prompt
                full_prompt = f"{self.prompt_template}\n\n# LECTURE CONTENT\n\nLecture Name: {lecture_name}\n\n{content}"
                
                print(f"📤 Sending request to Gemini...")
                print(f"   📊 Content length: {len(content):,} characters")
                print(f"   📊 Estimated tokens: ~{len(content) // 4:,}")
                
                # Generate content
                response = self.model.generate_content(full_prompt)
                
                if not response or not response.text:
                    print(f"⚠️  Empty response from Gemini")
                    continue
                
                print(f"📥 Received response from Gemini")
                
                # Parse JSON response
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # NEW: Clean up trailing commas from objects and arrays
                response_text = re.sub(r",(\s*[}\]])", r"\1", response_text)
                
                # Parse JSON
                questions_data = json.loads(response_text)
                
                # Validate structure
                if not isinstance(questions_data, dict) or 'questions' not in questions_data:
                    print(f"⚠️  Invalid response structure (missing 'questions' key)")
                    continue
                
                questions = questions_data['questions']
                
                if not isinstance(questions, list) or len(questions) == 0:
                    print(f"⚠️  No questions generated")
                    continue
                
                print(f"✅ Successfully generated {len(questions)} questions")
                
                # Validate question types distribution
                type_counts = {}
                for q in questions:
                    q_type = q.get('type', 'unknown')
                    type_counts[q_type] = type_counts.get(q_type, 0) + 1
                
                print(f"\n📊 Question Type Distribution:")
                for q_type, count in sorted(type_counts.items()):
                    percentage = (count / len(questions)) * 100
                    print(f"   • {q_type}: {count} ({percentage:.1f}%)")
                
                return questions_data
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                # Log the problematic text for easier debugging
                print(f"   RAW RESPONSE (first 500 chars): {response.text[:500]}...")
                if attempt < max_retries - 1:
                    print(f"   Retrying...")
                continue
                
            except Exception as e:
                print(f"❌ Error generating questions: {e}")
                if attempt < max_retries - 1:
                    print(f"   Retrying...")
                continue
        
        print(f"❌ Failed to generate questions after {max_retries} attempts")
        return None


def save_hard_questions(questions_data: Dict[str, Any], output_path: Path, lecture_name: str, course_id: str):
    """
    Save hard questions to JSON file with metadata.
    
    Args:
        questions_data: Dictionary containing questions list
        output_path: Path to save the JSON file
        lecture_name: Name of the lecture
        course_id: Course identifier
    """
    # Add metadata
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_questions': len(questions_data.get('questions', [])),
            'course_id': course_id,
            'lecture_name': lecture_name,
            'difficulty': 'hard',
            'generator_version': '1.0.0'
        },
        'questions': questions_data.get('questions', [])
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved hard questions: {output_path}")


def check_cache(output_path: Path) -> bool:
    """
    Check if hard questions already exist for this lecture.
    
    Args:
        output_path: Path where questions would be saved
        
    Returns:
        True if cache exists, False otherwise
    """
    if output_path.exists():
        print(f"✅ Cache found: {output_path}")
        print(f"   Skipping generation (delete file to regenerate)")
        return True
    return False


def process_lecture(course_id: str, lecture_name: str, generator: HardQuestionGenerator, force_regenerate: bool = False):
    """
    Process a single lecture to generate hard questions.
    
    Args:
        course_id: Course identifier (e.g., 'MS5260')
        lecture_name: Lecture name (e.g., 'MIS_lec_4')
        generator: HardQuestionGenerator instance
        force_regenerate: If True, regenerate even if cache exists
    """
    print(f"\n{'─'*70}")
    print(f"📄 Processing: {lecture_name}")
    print(f"{'─'*70}")
    
    # Define paths
    course_base_dir = Path(f"./courses/{course_id}")
    analysis_dir = course_base_dir / "slide_analysis"
    structured_json_path = analysis_dir / f"{lecture_name}_structured_analysis.json"
    
    # Output path
    output_dir = course_base_dir / "cognitive_flashcards" / lecture_name
    output_path = output_dir / f"{lecture_name}_hard_questions.json"
    
    # Check if structured analysis exists
    if not structured_json_path.exists():
        print(f"❌ Structured analysis not found: {structured_json_path}")
        return False
    
    # Check cache
    if not force_regenerate and check_cache(output_path):
        return True
    
    # Extract content
    content = generator._extract_slide_content(structured_json_path)
    
    if not content:
        print(f"⚠️  No content extracted from {lecture_name}")
        return False
    
    print(f"📄 Extracted {len(content):,} characters of content")
    
    # Generate questions
    questions_data = generator.generate_questions(content, lecture_name)
    
    if not questions_data:
        print(f"❌ Failed to generate questions for {lecture_name}")
        return False
    
    # Save questions
    save_hard_questions(questions_data, output_path, lecture_name, course_id)
    
    print(f"✅ Successfully processed {lecture_name}")
    return True


def process_course(course_id: str, lecture_name: Optional[str] = None, force_regenerate: bool = False):
    """
    Process a course to generate hard questions for all or specific lectures.
    
    Args:
        course_id: Course identifier (e.g., 'MS5260')
        lecture_name: Optional specific lecture to process
        force_regenerate: If True, regenerate even if cache exists
    """
    print(f"\n{'='*80}")
    print(f"📚 Generating Hard Questions for Course: {course_id}")
    print(f"{'='*80}")
    
    # Initialize generator
    generator = HardQuestionGenerator(
        api_key=Config.GEMINI_API_KEY,
        model=Config.GEMINI_MODEL
    )
    
    # Define paths
    course_base_dir = Path(f"./courses/{course_id}")
    analysis_dir = course_base_dir / "slide_analysis"
    
    # Check if analysis directory exists
    if not analysis_dir.exists():
        print(f"⚠️  No slide analysis found for course: {course_id}")
        print(f"   Please run: python -m pdf_slide_processor.main {course_id}")
        return
    
    # Find lectures to process
    if lecture_name:
        # Process specific lecture
        specific_file = analysis_dir / f"{lecture_name}_structured_analysis.json"
        if not specific_file.exists():
            print(f"⚠️  Lecture analysis not found: {specific_file}")
            print(f"   Available lectures in {analysis_dir}:")
            for f in analysis_dir.glob("*_structured_analysis.json"):
                print(f"      • {f.stem.replace('_structured_analysis', '')}")
            return
        
        lectures = [lecture_name]
        print(f"\n🎯 Processing specific lecture: {lecture_name}")
    else:
        # Find all lectures
        structured_files = list(analysis_dir.glob("*_structured_analysis.json"))
        if not structured_files:
            print(f"⚠️  No structured analysis files found in {analysis_dir}")
            return
        
        lectures = [f.stem.replace("_structured_analysis", "") for f in structured_files]
        print(f"\n📊 Found {len(lectures)} lecture(s) to process")
    
    # Process each lecture
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, lec_name in enumerate(lectures, 1):
        print(f"\n{'#'*80}")
        print(f"# Lecture {i}/{len(lectures)}")
        print(f"{'#'*80}")
        
        try:
            result = process_lecture(course_id, lec_name, generator, force_regenerate)
            if result:
                # Check if it was cached or newly generated
                output_path = course_base_dir / "cognitive_flashcards" / lec_name / f"{lec_name}_hard_questions.json"
                if output_path.exists():
                    with open(output_path, 'r') as f:
                        data = json.load(f)
                        generated_at = data.get('metadata', {}).get('generated_at', '')
                        # Simple heuristic: if generated in last 5 seconds, it's new
                        from datetime import datetime, timedelta
                        if generated_at:
                            gen_time = datetime.fromisoformat(generated_at)
                            if datetime.now() - gen_time < timedelta(seconds=5):
                                success_count += 1
                            else:
                                skip_count += 1
                        else:
                            success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ Error processing {lec_name}: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
            print(f"⏭️  Skipping {lec_name} and continuing...")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"✅ COURSE COMPLETE: {course_id}")
    print(f"{'='*80}")
    print(f"📊 Summary:")
    print(f"   • Total lectures: {len(lectures)}")
    print(f"   • Successfully generated: {success_count}")
    print(f"   • Skipped (cached): {skip_count}")
    print(f"   • Failed: {fail_count}")
    print(f"\n💡 Output location: {course_base_dir}/cognitive_flashcards/[lecture_name]/")


def load_courses() -> List[Dict[str, Any]]:
    """Load courses from courses.json."""
    courses_file = Path("courses.json")
    
    if not courses_file.exists():
        print(f"❌ courses.json not found")
        return []
    
    try:
        with open(courses_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            courses = data.get('courses', [])
            return courses
    except Exception as e:
        print(f"❌ Error loading courses.json: {e}")
        return []


def main():
    """Main execution function."""
    
    print("🎓 Hard Quiz Questions Generator\n")
    
    # Validate configuration
    is_valid, error_msg = Config.validate()
    if not is_valid:
        print(f"❌ Configuration Error: {error_msg}")
        return
    
    # Parse command-line arguments
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
        # Process specific course
        process_course(target_course_id, lecture_name)
    else:
        # Process all courses
        courses = load_courses()
        if not courses:
            print(f"⚠️  No courses found. Please ensure courses.json exists.")
            return
        
        print(f"📚 Loaded {len(courses)} course(s) from courses.json")
        
        if lecture_name:
            print(f"⚠️  Note: lecture_name '{lecture_name}' ignored when processing all courses")
            print(f"   Please specify a course_id to use lecture_name")
        
        print(f"\n🔄 Processing all courses...\n")
        
        for i, course in enumerate(courses, 1):
            course_id = course.get('course_id')
            if not course_id:
                print(f"⚠️  Skipping course without course_id")
                continue
            
            print(f"\n{'#'*80}")
            print(f"# Course {i}/{len(courses)}")
            print(f"{'#'*80}")
            
            process_course(course_id)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL COURSES COMPLETE!")
        print(f"{'='*80}")


if __name__ == "__main__":
    main()

