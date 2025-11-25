"""Content condensing and structuring module."""

import logging
import json
from typing import Dict, Any, List

from app.content_generation.llm.client import LLMClient

logger = logging.getLogger(__name__)


class ContentCondenser:
    """Condense and structure slide analyses into coherent content."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize content condenser.
        
        Args:
            llm_client: LLM client for text generation
        """
        self.llm_client = llm_client
    
    def condense(
        self,
        slide_analyses: List[Dict[str, Any]],
        lecture_title: str,
        course_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Condense slide analyses into structured content.
        
        Args:
            slide_analyses: List of slide analysis dicts
            lecture_title: Title of the lecture
            course_context: Course metadata
            
        Returns:
            Structured content dict
        """
        logger.info(f"Condensing content for: {lecture_title}")
        
        # Format slides into text
        formatted_content = self._format_slides(slide_analyses)
        
        # Build condensing prompt
        prompt = self._build_condensing_prompt(
            formatted_content,
            lecture_title,
            course_context
        )
        
        # Generate structured content
        response = self.llm_client.generate(prompt)
        
        # Parse response
        structured_content = self._parse_structured_content(response)
        
        logger.info("Content condensing completed")
        return structured_content
    
    def _format_slides(self, slide_analyses: List[Dict[str, Any]]) -> str:
        """Format slide analyses into readable text.
        
        Handles both old format (with nested 'analysis' key) and new flat format.
        """
        formatted_parts = []
        
        for slide_data in slide_analyses:
            slide_num = slide_data.get("slide_number", "?")
            
            # Support both old nested format and new flat format
            if "analysis" in slide_data:
                analysis = slide_data.get("analysis", {})
            else:
                # New flat format - slide_data IS the analysis
                analysis = slide_data
            
            if "error" in analysis:
                continue
            
            slide_text = f"\n=== SLIDE {slide_num} ===\n"
            
            if "title" in analysis:
                slide_text += f"Title: {analysis['title']}\n"
            
            if "main_text" in analysis:
                slide_text += f"\nContent:\n{analysis['main_text']}\n"
            
            if "key_concepts" in analysis and analysis["key_concepts"]:
                concepts = analysis['key_concepts']
                if isinstance(concepts, list):
                    slide_text += f"\nKey Concepts: {', '.join(str(c) for c in concepts)}\n"
            
            if "definitions" in analysis and analysis["definitions"]:
                slide_text += "\nDefinitions:\n"
                for defn in analysis["definitions"]:
                    if isinstance(defn, dict):
                        term = defn.get("term", "")
                        definition = defn.get("definition", "")
                        slide_text += f"- {term}: {definition}\n"
                    else:
                        slide_text += f"- {defn}\n"
            
            if "examples" in analysis and analysis["examples"]:
                slide_text += "\nExamples:\n"
                for example in analysis["examples"]:
                    slide_text += f"- {example}\n"
            
            if "formulas" in analysis and analysis["formulas"]:
                slide_text += "\nFormulas:\n"
                for formula in analysis["formulas"]:
                    slide_text += f"- {formula}\n"
            
            if "diagrams" in analysis and analysis["diagrams"]:
                slide_text += "\nDiagrams:\n"
                for diagram in analysis["diagrams"]:
                    if isinstance(diagram, dict):
                        dtype = diagram.get("type", "diagram")
                        desc = diagram.get("description", "")
                        slide_text += f"- [{dtype}] {desc}\n"
                    else:
                        slide_text += f"- {diagram}\n"
            
            formatted_parts.append(slide_text)
        
        return "\n".join(formatted_parts)
    
    def _build_condensing_prompt(
        self,
        content: str,
        lecture_title: str,
        course_context: Dict[str, Any]
    ) -> str:
        """Build prompt for content condensing."""
        course_name = course_context.get('course_name', 'N/A')
        textbooks = ', '.join(course_context.get('reference_textbooks', []))
        
        return f"""You are an expert content structurer for the course "{course_name}".

Reference textbooks: {textbooks}

Your task is to analyze the following lecture slides and create a well-structured summary.

Lecture Title: {lecture_title}

Slide Content:
{content}

Please create a structured analysis with the following JSON format:
{{
    "summary": "Overall lecture summary (2-3 paragraphs)",
    "sections": [
        {{
            "title": "Section title",
            "content": "Section content",
            "key_points": ["point1", "point2"]
        }}
    ],
    "key_concepts": [
        {{
            "name": "Concept name",
            "description": "Brief description"
        }}
    ],
    "learning_objectives": ["objective1", "objective2"]
}}

Focus on:
1. Identifying main themes and organizing them into logical sections
2. Extracting key concepts with clear descriptions
3. Creating a coherent narrative from the slides
4. Highlighting learning objectives

Return ONLY valid JSON, no additional text.
"""
    
    def _parse_structured_content(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to structured content."""
        try:
            # Remove code fences
            if response.startswith("```"):
                parts = response.split("```")
                if len(parts) >= 2:
                    response = parts[1]
                    if response.startswith("json"):
                        response = response[4:].strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured content: {str(e)}")
            # Return minimal structure
            return {
                "summary": response[:500],
                "sections": [],
                "key_concepts": [],
                "learning_objectives": []
            }

