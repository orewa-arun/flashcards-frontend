"""
Content Consolidation Module for Pre-Flashcard Processing.

This module consolidates fragmented slide analyses into coherent topic-based
documents, removing redundancy and non-educational content before flashcard generation.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Topic:
    """Represents a consolidated topic from multiple slides."""
    name: str
    slides: List[int] = field(default_factory=list)
    main_text: str = ""
    key_concepts: List[str] = field(default_factory=list)
    definitions: List[Dict[str, str]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    notes: str = ""
    educational_value: float = 0.0  # 0.0 to 1.0


class ContentConsolidator:
    """
    Consolidates fragmented slide analyses into topic-based documents.
    
    Key Functions:
    1. Filters out non-educational slides (title, logistics, agenda)
    2. Groups slides by topic similarity
    3. Merges related content while removing redundancy
    4. Creates semantic chunks ready for flashcard generation
    """
    
    # Keywords indicating non-educational content
    NON_EDUCATIONAL_KEYWORDS = {
        "title_slide": [
            "session", "module", "week", "lecture", "course", "welcome",
            "thank you", "questions?", "q&a", "thank", "logo", "accreditation"
        ],
        "logistics": [
            "schedule", "deadline", "assignment", "submission", "grading",
            "blackboard", "moodle", "coaching", "office hours", "sit with your group",
            "google sheet", "be prepared", "what i expect"
        ],
        "agenda": [
            "today we will", "topics to be covered", "agenda", "outline",
            "in this session", "overview", "semester view", "before we start"
        ]
    }
    
    # Keywords indicating high educational value
    EDUCATIONAL_KEYWORDS = [
        "definition", "concept", "theory", "framework", "model", "approach",
        "example", "case study", "formula", "equation", "principle", "method",
        "comparison", "difference", "relationship", "characteristics", "types"
    ]
    
    def __init__(
        self,
        topic_similarity_threshold: float = 0.5,
        min_educational_value: float = 0.3,
        consolidate_by_title: bool = True
    ):
        """
        Initialize the content consolidator.
        
        Args:
            topic_similarity_threshold: Threshold for grouping topics (0.0-1.0)
            min_educational_value: Minimum score to include slide (0.0-1.0)
            consolidate_by_title: Whether to group by title similarity
        """
        self.topic_similarity_threshold = topic_similarity_threshold
        self.min_educational_value = min_educational_value
        self.consolidate_by_title = consolidate_by_title
    
    def consolidate(
        self,
        raw_slide_analyses: List[Dict[str, Any]],
        lecture_title: str = ""
    ) -> Dict[str, Any]:
        """
        Consolidate raw slide analyses into topic-based content.
        
        Args:
            raw_slide_analyses: List of slide analysis dictionaries
            lecture_title: Title of the lecture for context
            
        Returns:
            Dictionary with consolidated topics and metadata
        """
        logger.info(f"Consolidating {len(raw_slide_analyses)} slides for: {lecture_title}")
        
        # Step 1: Score and filter slides
        scored_slides = self._score_slides(raw_slide_analyses)
        educational_slides = [
            s for s in scored_slides 
            if s["educational_value"] >= self.min_educational_value
        ]
        
        filtered_count = len(raw_slide_analyses) - len(educational_slides)
        logger.info(f"Filtered out {filtered_count} non-educational slides")
        
        # Step 2: Group slides by topic
        topic_groups = self._group_by_topic(educational_slides)
        logger.info(f"Grouped into {len(topic_groups)} distinct topics")
        
        # Step 3: Consolidate each topic group
        consolidated_topics = []
        for topic_name, slides in topic_groups.items():
            topic = self._consolidate_topic(topic_name, slides)
            if topic.main_text.strip() or topic.key_concepts or topic.definitions:
                consolidated_topics.append(topic)
        
        # Step 4: Generate semantic chunks
        semantic_chunks = self._create_semantic_chunks(consolidated_topics)
        
        return {
            "lecture_title": lecture_title,
            "total_original_slides": len(raw_slide_analyses),
            "educational_slides_count": len(educational_slides),
            "filtered_slides_count": filtered_count,
            "topic_count": len(consolidated_topics),
            "topics": [self._topic_to_dict(t) for t in consolidated_topics],
            "semantic_chunks": semantic_chunks,
            "consolidation_summary": self._generate_summary(consolidated_topics)
        }
    
    def _score_slides(
        self, 
        slides: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score each slide for educational value."""
        scored = []
        
        for slide in slides:
            # Handle nested 'analysis' structure
            if "analysis" in slide:
                analysis = slide.get("analysis", {})
                slide_num = slide.get("slide_number", analysis.get("slide_number", 0))
            else:
                analysis = slide
                slide_num = slide.get("slide_number", 0)
            
            # Handle case where analysis might be a string (JSON not parsed)
            if isinstance(analysis, str):
                logger.warning(f"Slide {slide_num}: analysis is a string, skipping")
                continue
            
            if "error" in analysis:
                continue
            
            score = self._calculate_educational_value(analysis)
            
            # Log first few slides for debugging
            if slide_num <= 3:
                title = (analysis.get('title') or "")[:30] if analysis.get('title') else ""
                main_text = analysis.get('main_text') or ""
                logger.debug(
                    f"Slide {slide_num}: score={score:.2f}, "
                    f"title='{title}...', "
                    f"text_len={len(main_text)}"
                )
            
            scored.append({
                "slide_number": slide_num,
                "analysis": analysis,
                "educational_value": score,
                "title": (analysis.get("title") or "").strip(),
                "classification": self._classify_slide(analysis, score)
            })
        
        # Log score distribution
        if scored:
            scores = [s["educational_value"] for s in scored]
            logger.info(f"Score distribution: min={min(scores):.2f}, max={max(scores):.2f}, avg={sum(scores)/len(scores):.2f}")
        
        return scored
    
    def _calculate_educational_value(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate educational value score for a slide.
        
        Considers:
        - Presence of definitions, examples, formulas
        - Content length
        - Educational keywords
        - Non-educational indicators
        """
        # Start with a base score of 0.3 - most slides have some value
        score = 0.3
        
        # Handle None values - convert to empty string before calling .lower()
        title = (analysis.get("title") or "").lower()
        main_text = (analysis.get("main_text") or "").lower()
        notes = (analysis.get("notes") or "").lower()
        combined_text = f"{title} {main_text} {notes}"
        
        # Check if this is clearly a non-educational slide
        is_title_slide = any(kw in title for kw in ["session", "welcome", "thank you", "q&a", "questions?"])
        is_logistics = any(kw in combined_text for kw in ["deadline", "submission", "grading", "office hours"])
        is_agenda = any(kw in combined_text for kw in ["agenda", "outline", "today we will"])
        
        if is_title_slide or is_logistics or is_agenda:
            # Only penalize if there's very little other content
            if len(main_text) < 100:
                score = 0.1
        
        # Reward educational content
        definitions = analysis.get("definitions", [])
        examples = analysis.get("examples", [])
        formulas = analysis.get("formulas", [])
        diagrams = analysis.get("diagrams", [])
        key_concepts = analysis.get("key_concepts", [])
        
        # Definitions are highly valuable
        score += min(len(definitions) * 0.2, 0.4)
        
        # Examples are valuable
        score += min(len(examples) * 0.1, 0.2)
        
        # Formulas are valuable
        score += min(len(formulas) * 0.1, 0.2)
        
        # Informative diagrams (not just logos/illustrations)
        informative_diagrams = [
            d for d in diagrams 
            if isinstance(d, dict) and 
            (d.get("type") or "").lower() not in ["logo", "illustration", "image", "photo"]
        ]
        score += min(len(informative_diagrams) * 0.15, 0.3)
        
        # Key concepts
        score += min(len(key_concepts) * 0.05, 0.2)
        
        # Content length bonus
        content_length = len(main_text)
        if content_length > 500:
            score += 0.15
        elif content_length > 200:
            score += 0.1
        elif content_length > 50:
            score += 0.05
        elif content_length < 20:
            score -= 0.2  # Very short content is likely a title slide
        
        # Educational keyword bonus
        edu_keywords_found = sum(1 for kw in self.EDUCATIONAL_KEYWORDS if kw in combined_text)
        score += min(edu_keywords_found * 0.03, 0.15)
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _classify_slide(
        self, 
        analysis: Dict[str, Any], 
        score: float
    ) -> str:
        """Classify slide type."""
        # Handle None values - convert to empty string before calling .lower()
        title = (analysis.get("title") or "").lower()
        main_text = (analysis.get("main_text") or "").lower()
        
        if score < 0.2:
            # Check specific non-educational types
            for keyword in self.NON_EDUCATIONAL_KEYWORDS["title_slide"]:
                if keyword in title:
                    return "title_slide"
            for keyword in self.NON_EDUCATIONAL_KEYWORDS["logistics"]:
                if keyword in f"{title} {main_text}":
                    return "logistics"
            for keyword in self.NON_EDUCATIONAL_KEYWORDS["agenda"]:
                if keyword in f"{title} {main_text}":
                    return "agenda"
            return "low_value"
        
        if analysis.get("definitions"):
            return "definition"
        if analysis.get("examples"):
            return "example"
        if analysis.get("diagrams"):
            return "diagram"
        if analysis.get("formulas"):
            return "formula"
        
        return "content"
    
    def _group_by_topic(
        self, 
        slides: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group slides by topic similarity."""
        if not self.consolidate_by_title:
            # Don't consolidate, use slide numbers as keys
            return {
                f"slide_{s['slide_number']}": [s] 
                for s in slides
            }
        
        topic_groups = defaultdict(list)
        
        for slide in slides:
            # Handle None values
            title = (slide.get("title") or "").strip()
            
            # Normalize title for grouping
            normalized_title = self._normalize_title(title)
            
            if not normalized_title:
                normalized_title = f"untitled_slide_{slide['slide_number']}"
            
            # Find existing group with similar title
            matched_group = None
            for existing_title in topic_groups.keys():
                if self._titles_similar(normalized_title, existing_title):
                    matched_group = existing_title
                    break
            
            if matched_group:
                topic_groups[matched_group].append(slide)
            else:
                topic_groups[normalized_title].append(slide)
        
        return dict(topic_groups)
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Handle None values
        if title is None:
            return ""
        
        # Remove common prefixes/suffixes
        title = re.sub(r'^(slide|page|section)\s*\d*\s*[-:.]?\s*', '', title, flags=re.I)
        title = re.sub(r'\s*[-:.]?\s*\d+\s*$', '', title)
        
        # Remove extra whitespace
        title = re.sub(r'\s+', ' ', title).strip().lower()
        
        return title
    
    def _titles_similar(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar enough to be grouped."""
        if title1 == title2:
            return True
        
        # Check if one contains the other
        if title1 in title2 or title2 in title1:
            return True
        
        # Word overlap check
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap >= self.topic_similarity_threshold
    
    def _consolidate_topic(
        self, 
        topic_name: str, 
        slides: List[Dict[str, Any]]
    ) -> Topic:
        """Consolidate multiple slides into a single topic."""
        topic = Topic(name=topic_name)
        
        seen_text = set()
        seen_concepts = set()
        seen_definitions = set()
        seen_examples = set()
        
        text_parts = []
        
        for slide in sorted(slides, key=lambda x: x["slide_number"]):
            topic.slides.append(slide["slide_number"])
            analysis = slide.get("analysis", slide)
            topic.educational_value = max(
                topic.educational_value, 
                slide.get("educational_value", 0)
            )
            
            # Consolidate main text (deduplicate)
            main_text = (analysis.get("main_text") or "").strip()
            if main_text:
                text_hash = hash(main_text[:100])  # First 100 chars for dedup
                if text_hash not in seen_text:
                    seen_text.add(text_hash)
                    text_parts.append(main_text)
            
            # Consolidate key concepts (deduplicate)
            for concept in analysis.get("key_concepts", []):
                concept_str = str(concept).lower().strip()
                if concept_str not in seen_concepts:
                    seen_concepts.add(concept_str)
                    topic.key_concepts.append(concept if isinstance(concept, str) else str(concept))
            
            # Consolidate definitions (deduplicate by term)
            for defn in analysis.get("definitions", []):
                if isinstance(defn, dict):
                    term = (defn.get("term") or "").lower().strip()
                    if term not in seen_definitions:
                        seen_definitions.add(term)
                        topic.definitions.append(defn)
            
            # Consolidate examples (deduplicate)
            for example in analysis.get("examples", []):
                example_hash = hash(str(example)[:50])
                if example_hash not in seen_examples:
                    seen_examples.add(example_hash)
                    topic.examples.append(example)
            
            # Collect diagrams (informative ones only)
            for diagram in analysis.get("diagrams", []):
                if isinstance(diagram, dict):
                    dtype = (diagram.get("type") or "").lower()
                    if dtype not in ["logo", "illustration", "image", "photo"]:
                        topic.diagrams.append(diagram)
            
            # Collect formulas
            topic.formulas.extend(analysis.get("formulas", []))
            
            # Append notes
            notes = (analysis.get("notes") or "").strip()
            if notes and notes not in topic.notes:
                topic.notes += f" {notes}"
        
        # Combine text parts intelligently
        topic.main_text = self._merge_text_parts(text_parts)
        topic.notes = topic.notes.strip()
        
        return topic
    
    def _merge_text_parts(self, parts: List[str]) -> str:
        """Merge text parts, removing redundancy."""
        if not parts:
            return ""
        
        if len(parts) == 1:
            return parts[0]
        
        # Simple deduplication at sentence level
        seen_sentences = set()
        merged_parts = []
        
        for part in parts:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', part)
            unique_sentences = []
            
            for sentence in sentences:
                sentence_normalized = sentence.lower().strip()[:50]
                if sentence_normalized not in seen_sentences:
                    seen_sentences.add(sentence_normalized)
                    unique_sentences.append(sentence)
            
            if unique_sentences:
                merged_parts.append(" ".join(unique_sentences))
        
        return "\n\n".join(merged_parts)
    
    def _create_semantic_chunks(
        self, 
        topics: List[Topic],
        max_chunk_size: int = 10000
    ) -> List[Dict[str, Any]]:
        """
        Create semantic chunks from consolidated topics.
        
        Each chunk is a self-contained unit ready for flashcard generation.
        """
        chunks = []
        current_chunk = {
            "topics": [],
            "content": "",
            "key_concepts": [],
            "educational_value": 0.0
        }
        current_size = 0
        
        for topic in sorted(topics, key=lambda t: -t.educational_value):
            topic_content = self._format_topic_for_chunk(topic)
            topic_size = len(topic_content)
            
            # If topic is too large, it becomes its own chunk
            if topic_size > max_chunk_size:
                # Save current chunk first
                if current_chunk["topics"]:
                    chunks.append(current_chunk)
                
                # Topic as its own chunk
                chunks.append({
                    "topics": [topic.name],
                    "content": topic_content,
                    "key_concepts": topic.key_concepts[:10],
                    "educational_value": topic.educational_value
                })
                
                current_chunk = {
                    "topics": [],
                    "content": "",
                    "key_concepts": [],
                    "educational_value": 0.0
                }
                current_size = 0
                continue
            
            # Check if adding would exceed limit
            if current_size + topic_size > max_chunk_size and current_chunk["topics"]:
                chunks.append(current_chunk)
                current_chunk = {
                    "topics": [],
                    "content": "",
                    "key_concepts": [],
                    "educational_value": 0.0
                }
                current_size = 0
            
            # Add topic to current chunk
            current_chunk["topics"].append(topic.name)
            current_chunk["content"] += f"\n\n{'='*50}\n{topic_content}"
            current_chunk["key_concepts"].extend(topic.key_concepts)
            current_chunk["educational_value"] = max(
                current_chunk["educational_value"], 
                topic.educational_value
            )
            current_size += topic_size
        
        # Add final chunk
        if current_chunk["topics"]:
            chunks.append(current_chunk)
        
        # Deduplicate key concepts per chunk
        for chunk in chunks:
            chunk["key_concepts"] = list(dict.fromkeys(chunk["key_concepts"]))[:15]
        
        return chunks
    
    def _format_topic_for_chunk(self, topic: Topic) -> str:
        """Format a topic for inclusion in a semantic chunk."""
        parts = [f"## Topic: {topic.name.title()}"]
        parts.append(f"(Source slides: {', '.join(map(str, topic.slides))})")
        
        if topic.main_text:
            parts.append(f"\n### Content\n{topic.main_text}")
        
        if topic.definitions:
            parts.append("\n### Definitions")
            for defn in topic.definitions:
                term = defn.get("term", "")
                definition = defn.get("definition", "")
                parts.append(f"- **{term}**: {definition}")
        
        if topic.key_concepts:
            parts.append(f"\n### Key Concepts: {', '.join(topic.key_concepts)}")
        
        if topic.examples:
            parts.append("\n### Examples")
            for example in topic.examples:
                parts.append(f"- {example}")
        
        if topic.diagrams:
            parts.append("\n### Visual Elements")
            for diagram in topic.diagrams:
                dtype = diagram.get("type", "diagram")
                desc = diagram.get("description", "")
                key_points = diagram.get("key_points", [])
                parts.append(f"- [{dtype}] {desc}")
                if key_points:
                    parts.append(f"  Key points: {', '.join(key_points)}")
        
        if topic.formulas:
            parts.append("\n### Formulas")
            for formula in topic.formulas:
                parts.append(f"- {formula}")
        
        return "\n".join(parts)
    
    def _topic_to_dict(self, topic: Topic) -> Dict[str, Any]:
        """Convert Topic dataclass to dictionary."""
        return {
            "name": topic.name,
            "slides": topic.slides,
            "main_text": topic.main_text,
            "key_concepts": topic.key_concepts,
            "definitions": topic.definitions,
            "examples": topic.examples,
            "diagrams": topic.diagrams,
            "formulas": topic.formulas,
            "notes": topic.notes,
            "educational_value": topic.educational_value
        }
    
    def _generate_summary(self, topics: List[Topic]) -> str:
        """Generate a summary of the consolidated content."""
        if not topics:
            return "No educational content found after consolidation."
        
        topic_names = [t.name for t in topics]
        total_definitions = sum(len(t.definitions) for t in topics)
        total_examples = sum(len(t.examples) for t in topics)
        total_concepts = sum(len(t.key_concepts) for t in topics)
        
        summary = f"Consolidated into {len(topics)} topics: {', '.join(topic_names[:5])}"
        if len(topic_names) > 5:
            summary += f" (+{len(topic_names) - 5} more)"
        summary += f". Contains {total_definitions} definitions, {total_examples} examples, and {total_concepts} key concepts."
        
        return summary


def consolidate_for_flashcards(
    raw_slide_analyses: List[Dict[str, Any]],
    lecture_title: str = "",
    min_educational_value: float = 0.3
) -> List[str]:
    """
    Convenience function to consolidate slides and return ready-to-use chunks.
    
    Args:
        raw_slide_analyses: List of slide analysis dictionaries
        lecture_title: Title of the lecture
        min_educational_value: Minimum educational value threshold (0.0-1.0)
        
    Returns:
        List of content strings ready for flashcard generation
    """
    consolidator = ContentConsolidator(min_educational_value=min_educational_value)
    result = consolidator.consolidate(raw_slide_analyses, lecture_title)
    
    return [chunk["content"] for chunk in result.get("semantic_chunks", [])]

