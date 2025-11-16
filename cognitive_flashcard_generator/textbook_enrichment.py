"""
Textbook-First Content Enrichment Pipeline

This module handles content enrichment for courses that only have:
- A list of topics
- A reference textbook

It generates rich, detailed content that can be used with existing
flashcard and quiz generation prompts.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class TextbookContentEnricher:
    """
    Enriches sparse topic lists into comprehensive educational content
    based on reference textbooks.
    """
    
    def __init__(self, courses_json_path: str, output_dir: str = "enriched_content"):
        self.courses_json_path = courses_json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load courses data
        with open(courses_json_path, 'r') as f:
            self.courses_data = json.load(f)
        
        # Initialize Gemini model for content synthesis
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
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
    
    def should_enrich(self, lecture: Dict) -> bool:
        """
        Determine if a lecture should be enriched.
        
        Args:
            lecture: Lecture dictionary
            
        Returns:
            True if the lecture should be enriched (hasPDF == False)
        """
        return not self.is_slide_based(lecture)
    
    def generate_textbook_focused_search_queries(
        self, 
        topic: str, 
        textbook_title: str, 
        authors: str
    ) -> List[str]:
        """
        Generate targeted search queries that prioritize textbook content.
        
        Args:
            topic: The specific topic to search for
            textbook_title: The reference textbook title
            authors: The textbook authors
            
        Returns:
            List of search queries in order of priority
        """
        queries = [
            # Primary query: Most specific to textbook
            f'"{topic}" from "{textbook_title}" by {authors} explained',
            
            # Secondary queries: Still textbook-focused
            f'"{textbook_title}" "{topic}" summary chapter',
            f'{authors} "{topic}" business examples',
            f'"{textbook_title}" {topic} lecture notes',
            
            # Tertiary queries: Broader but still contextualized
            f'{topic} business statistics {textbook_title}',
            f'{topic} data analysis {authors}'
        ]
        
        return queries
    
    def synthesize_topic_content(
        self,
        topic: str,
        textbook_title: str,
        authors: str,
        course_name: str,
        course_description: str
    ) -> str:
        """
        Use Gemini to synthesize comprehensive content for a single topic
        based on the textbook context.
        
        Args:
            topic: The topic to enrich
            textbook_title: Reference textbook title
            authors: Textbook authors
            course_name: Name of the course
            course_description: Description of the course
            
        Returns:
            Synthesized, structured content for the topic
        """
        
        # Load the synthesis prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "textbook_content_synthesis_prompt.txt"
        
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        
        # Fill in the template
        prompt = prompt_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{TEXTBOOK_TITLE}}", textbook_title)
        prompt = prompt.replace("{{AUTHORS}}", authors)
        prompt = prompt.replace("{{COURSE_NAME}}", course_name)
        prompt = prompt.replace("{{COURSE_DESCRIPTION}}", course_description)
        
        # Generate content using Gemini
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=15000
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error synthesizing content for topic '{topic}': {e}")
            return f"# {topic}\n\n[Content synthesis failed for this topic]"
    
    def synthesize_topic_batch(
        self,
        topics: List[str],
        textbook_title: str,
        authors: str,
        course_name: str,
        course_description: str
    ) -> str:
        """
        Use Gemini to synthesize comprehensive content for multiple topics in one call.
        This batching approach reduces API calls while maintaining quality.
        
        Args:
            topics: List of topics to enrich (2-3 topics recommended)
            textbook_title: Reference textbook title
            authors: Textbook authors
            course_name: Name of the course
            course_description: Description of the course
            
        Returns:
            Synthesized, structured content for all topics combined
        """
        
        # Load the batch synthesis prompt
        prompt_path = Path(__file__).parent.parent / "prompts" / "textbook_content_batch_synthesis_prompt.txt"
        
        with open(prompt_path, 'r') as f:
            prompt_template = f.read()
        
        # Create a formatted list of topics
        topics_list = "\n".join([f"{i+1}. {topic}" for i, topic in enumerate(topics)])
        
        # Fill in the template
        prompt = prompt_template.replace("{{TOPICS_LIST}}", topics_list)
        prompt = prompt.replace("{{TOPIC_COUNT}}", str(len(topics)))
        prompt = prompt.replace("{{TEXTBOOK_TITLE}}", textbook_title)
        prompt = prompt.replace("{{AUTHORS}}", authors)
        prompt = prompt.replace("{{COURSE_NAME}}", course_name)
        prompt = prompt.replace("{{COURSE_DESCRIPTION}}", course_description)
        
        # Generate content using Gemini with higher token limit for batch
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=15000  # Same limit but for multiple topics
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error synthesizing batch content for {len(topics)} topics: {e}")
            # Fallback: return placeholder for each topic
            return "\n\n".join([f"# {topic}\n\n[Content synthesis failed for this topic]" for topic in topics])
    
    def enrich_single_lecture(
        self,
        course_id: str,
        lecture_number: str
    ) -> Path:
        """
        Enrich a single lecture by synthesizing content for all its topics.
        
        Args:
            course_id: The course ID (e.g., "MS5031")
            lecture_number: The lecture number (e.g., "2")
            
        Returns:
            Path to the enriched content file
        """
        # Find the course
        course = self.get_course(course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        # Find the lecture
        lecture = self.get_lecture(course, lecture_number)
        if not lecture:
            raise ValueError(f"Lecture {lecture_number} not found in course {course_id}")
        
        # Check if lecture should be enriched
        if not self.should_enrich(lecture):
            print(f"\n{'='*80}")
            print(f"Lecture {course_id}/{lecture_number} is slide-based (hasPDF implied).")
            print(f"Use structured_analysis pipeline instead.")
            print(f"{'='*80}\n")
            return None
        
        if not course.get('reference_textbooks'):
            raise ValueError(f"Course {course_id} has no reference textbooks")
        
        print(f"\n{'='*80}")
        print(f"Enriching Single Lecture: {course['course_name']}")
        print(f"Course ID: {course_id} | Lecture: {lecture_number}")
        print(f"{'='*80}\n")
        
        # Enrich the lecture
        enriched_content = self.enrich_lecture(course, lecture)
        
        # Save to output directory
        lecture_id = f"{course_id}_lecture_{lecture_number}"
        output_path = self.output_dir / course_id / f"{lecture_id}_enhanced.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(enriched_content)
        
        print(f"\n✓ Saved enriched content to: {output_path}\n")
        
        return output_path
    
    def enrich_lecture(
        self,
        course: Dict,
        lecture: Dict
    ) -> str:
        """
        Enrich a single lecture by synthesizing content for all its topics.
        
        Args:
            course: The course dictionary
            lecture: The lecture dictionary
            
        Returns:
            Comprehensive lecture content combining all topics
        """
        # Extract course metadata
        course_name = course['course_name']
        course_description = course.get('course_description', '')
        textbook_title = course['reference_textbooks'][0] if course['reference_textbooks'] else "Unknown"
        
        # Parse textbook title to extract authors
        # Format: "Title by Authors"
        if ' by ' in textbook_title:
            title_part, authors_part = textbook_title.split(' by ', 1)
        else:
            title_part = textbook_title
            authors_part = "Unknown"
        
        lecture_name = lecture.get('lecture_name', 'Unknown Lecture')
        lecture_number = lecture.get('lecture_number', 'N/A')
        topics = lecture.get('topics', [])
        
        print(f"\n{'='*80}")
        print(f"Enriching: {lecture_name}")
        print(f"Topics to process: {len(topics)}")
        print(f"Textbook: {title_part} by {authors_part}")
        print(f"{'='*80}\n")
        
        # Build the lecture document
        enriched_content = []
        
        # Add lecture header
        enriched_content.append(f"# {lecture_name}")
        enriched_content.append(f"**Lecture Number:** {lecture_number}")
        enriched_content.append(f"**Course:** {course_name}")
        enriched_content.append(f"**Reference Textbook:** {title_part} by {authors_part}")
        enriched_content.append("\n" + "="*80 + "\n")
        
        # Batch topics for efficient processing (2-3 topics per batch)
        batch_size = 2  # Conservative batch size to maintain quality
        topic_batches = [topics[i:i + batch_size] for i in range(0, len(topics), batch_size)]
        
        print(f"📦 Topics batched into {len(topic_batches)} batch(es) of ~{batch_size} topics each\n")
        
        # Process each batch
        for batch_idx, topic_batch in enumerate(topic_batches, 1):
            batch_info = f"Batch {batch_idx}/{len(topic_batches)}"
            topic_names = ", ".join([t[:40] + "..." if len(t) > 40 else t for t in topic_batch])
            print(f"Processing {batch_info}: {topic_names}")
            
            # Use batch synthesis for multiple topics, single synthesis for one topic
            if len(topic_batch) > 1:
                batch_content = self.synthesize_topic_batch(
                    topics=topic_batch,
                    textbook_title=title_part,
                    authors=authors_part,
                    course_name=course_name,
                    course_description=course_description
                )
                enriched_content.append(batch_content)
            else:
                # Single topic - use original method
                topic_content = self.synthesize_topic_content(
                    topic=topic_batch[0],
                    textbook_title=title_part,
                    authors=authors_part,
                    course_name=course_name,
                    course_description=course_description
                )
                enriched_content.append(topic_content)
            
            enriched_content.append("\n" + "-"*80 + "\n")
            print(f"✓ Completed {batch_info}: {len(topic_batch)} topic(s)\n")
            
            # Rate limiting: pause between API calls
            time.sleep(2)
        
        return "\n".join(enriched_content)
    
    def enrich_course(self, course_id: str) -> Dict[str, str]:
        """
        Enrich all lectures in a course that lack PDF slides.
        
        Args:
            course_id: The course ID (e.g., "MS5031")
            
        Returns:
            Dictionary mapping lecture identifiers to enriched content
        """
        # Find the course
        course = None
        for c in self.courses_data:
            if c['course_id'] == course_id:
                course = c
                break
        
        if not course:
            raise ValueError(f"Course {course_id} not found")
        
        if not course.get('reference_textbooks'):
            raise ValueError(f"Course {course_id} has no reference textbooks")
        
        print(f"\n{'#'*80}")
        print(f"# Starting Content Enrichment for {course['course_name']}")
        print(f"# Course ID: {course_id}")
        print(f"{'#'*80}\n")
        
        enriched_lectures = {}
        
        # Process each lecture
        for lecture in course.get('lecture_slides', []):
            # Check if lecture needs enrichment
            if 'pdf_path' in lecture and lecture['pdf_path']:
                print(f"Skipping {lecture.get('lecture_name')} - has PDF")
                continue
            
            lecture_id = f"{course_id}_lecture_{lecture.get('lecture_number', 'unknown')}"
            
            # Enrich the lecture
            enriched_content = self.enrich_lecture(course, lecture)
            enriched_lectures[lecture_id] = enriched_content
            
            # Save individual lecture content
            output_path = self.output_dir / course_id / f"{lecture_id}.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(enriched_content)
            
            print(f"✓ Saved enriched content to: {output_path}\n")
        
        return enriched_lectures
    
    def enrich_all_courses(self) -> Dict[str, Dict[str, str]]:
        """
        Enrich all courses that need content enrichment.
        
        Returns:
            Nested dictionary: {course_id: {lecture_id: enriched_content}}
        """
        courses_needing_enrichment = self.identify_courses_needing_enrichment()
        
        print(f"Found {len(courses_needing_enrichment)} course(s) needing enrichment:")
        for course in courses_needing_enrichment:
            print(f"  - {course['course_id']}: {course['course_name']}")
        print()
        
        all_enriched_content = {}
        
        for course in courses_needing_enrichment:
            course_id = course['course_id']
            enriched_lectures = self.enrich_course(course_id)
            all_enriched_content[course_id] = enriched_lectures
        
        return all_enriched_content


def main():
    """Main execution function for textbook enrichment."""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate enriched content from textbook for lectures without slides"
    )
    parser.add_argument(
        "--course",
        required=True,
        help="Course ID (e.g., MS5031)"
    )
    parser.add_argument(
        "--lecture",
        required=True,
        help="Lecture number (e.g., 2)"
    )
    parser.add_argument(
        "--courses-json",
        default="courses_resources/courses.json",
        help="Path to courses.json file"
    )
    
    args = parser.parse_args()
    
    # Path to courses.json
    courses_json_path = Path(__file__).parent.parent / args.courses_json
    
    # Initialize enricher
    enricher = TextbookContentEnricher(
        courses_json_path=str(courses_json_path),
        output_dir="enriched_content"
    )
    
    # Enrich the single lecture
    print("Starting textbook-based content enrichment...")
    output_path = enricher.enrich_single_lecture(args.course, args.lecture)
    
    if output_path:
        print(f"\n{'#'*80}")
        print("# Content Enrichment Complete!")
        print(f"# Output: {output_path}")
        print(f"{'#'*80}\n")
    
    return output_path


if __name__ == "__main__":
    main()

