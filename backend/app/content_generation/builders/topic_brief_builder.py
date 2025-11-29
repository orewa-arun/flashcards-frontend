"""
Topic Brief Builder for Enhanced Flashcard Generation.

This module transforms consolidated topics into structured prompts optimized
for generating rich, multi-faceted flashcard answers.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TopicBrief:
    """
    A structured representation of a topic optimized for flashcard generation.
    
    Each section is designed to feed specific answer types:
    - definitions → concise answers
    - examples → real_world_use_case, example
    - diagrams → mermaid_diagrams, analogy
    - relationships → common_mistakes
    """
    topic_name: str
    educational_value: float
    source_slides: List[int]
    
    # Core content
    summary: str = ""
    main_content: str = ""
    
    # Answer-type specific sections
    definitions: List[Dict[str, str]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    
    # Enhanced context
    academic_references: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)  # For common_mistakes
    
    def to_prompt_context(self) -> str:
        """Convert to structured prompt context for LLM."""
        sections = []
        
        # Header
        sections.append(f"# TOPIC: {self.topic_name}")
        sections.append(f"Educational Value: {self.educational_value:.2f}/1.0")
        sections.append(f"Source Slides: {', '.join(map(str, self.source_slides[:10]))}")
        sections.append("")
        
        # Summary (if available)
        if self.summary:
            sections.append("## TOPIC OVERVIEW")
            sections.append(self.summary[:500])
            sections.append("")
        
        # Definitions (for concise answers)
        if self.definitions:
            sections.append("## DEFINITIONS (Use for `concise` answers)")
            for defn in self.definitions[:8]:  # Limit to 8 definitions
                term = defn.get("term", "")
                definition = defn.get("definition", "")
                sections.append(f"- **{term}**: {definition}")
            sections.append("")
        
        # Key Concepts to Cover
        if self.key_concepts:
            sections.append("## KEY CONCEPTS TO COVER")
            sections.append(", ".join(self.key_concepts[:20]))  # Limit to 20 concepts
            sections.append("")
        
        # Real-World Examples (for real_world_use_case and example)
        if self.examples:
            sections.append("## REAL-WORLD EXAMPLES (Use for `real_world_use_case` and `example`)")
            for i, example in enumerate(self.examples[:10], 1):  # Limit to 10 examples
                # Clean up example text
                example_text = example.strip()
                if len(example_text) > 200:
                    example_text = example_text[:200] + "..."
                sections.append(f"{i}. {example_text}")
            sections.append("")
        
        # Visual Frameworks (for diagrams and analogies)
        if self.diagrams:
            sections.append("## VISUAL FRAMEWORKS (Use for `mermaid_diagrams` and `analogy`)")
            for diagram in self.diagrams[:5]:  # Limit to 5 diagrams
                dtype = diagram.get("type", "diagram")
                desc = diagram.get("description", "")[:200]
                key_points = diagram.get("key_points", [])
                
                sections.append(f"- [{dtype.upper()}]: {desc}")
                if key_points:
                    for point in key_points[:3]:
                        sections.append(f"  • {point[:100]}")
            sections.append("")
        
        # Academic References (for credibility)
        if self.academic_references:
            sections.append("## ACADEMIC REFERENCES (Cite in answers)")
            for ref in self.academic_references[:5]:
                sections.append(f"- {ref}")
            sections.append("")
        
        # Relationships (for common_mistakes)
        if self.relationships:
            sections.append("## CONCEPT RELATIONSHIPS (Use for `common_mistakes`)")
            sections.append("These distinctions help prevent confusion:")
            for rel in self.relationships[:5]:
                sections.append(f"- {rel}")
            sections.append("")
        
        # Learning Objectives (for prioritization)
        if self.learning_objectives:
            sections.append("## LEARNING OBJECTIVES")
            for obj in self.learning_objectives[:5]:
                sections.append(f"- {obj}")
            sections.append("")
        
        # Main Content (condensed)
        if self.main_content:
            sections.append("## DETAILED CONTENT")
            # Limit main content to avoid token explosion
            content = self.main_content[:3000]
            if len(self.main_content) > 3000:
                content += "\n\n[Content truncated for brevity...]"
            sections.append(content)
        
        return "\n".join(sections)


class TopicBriefBuilder:
    """
    Builds structured TopicBriefs from consolidated content.
    
    Transforms raw consolidated topics into prompts optimized for
    generating rich, multi-faceted flashcard answers.
    """
    
    def __init__(
        self,
        max_definitions: int = 8,
        max_examples: int = 10,
        max_diagrams: int = 5,
        max_concepts: int = 20,
        extract_references: bool = True,
        generate_relationships: bool = True
    ):
        """
        Initialize the builder.
        
        Args:
            max_definitions: Maximum definitions to include
            max_examples: Maximum examples to include
            max_diagrams: Maximum diagrams to include
            max_concepts: Maximum key concepts to include
            extract_references: Whether to extract academic references
            generate_relationships: Whether to generate concept relationships
        """
        self.max_definitions = max_definitions
        self.max_examples = max_examples
        self.max_diagrams = max_diagrams
        self.max_concepts = max_concepts
        self.extract_references = extract_references
        self.generate_relationships = generate_relationships
    
    def build_from_consolidated_topic(
        self,
        topic: Dict[str, Any],
        structured_content: Optional[Dict[str, Any]] = None,
        lecture_title: str = ""
    ) -> TopicBrief:
        """
        Build a TopicBrief from a consolidated topic.
        
        Args:
            topic: Consolidated topic dictionary
            structured_content: Optional structured_content from LLM condensing
            lecture_title: Title of the lecture
            
        Returns:
            TopicBrief optimized for flashcard generation
        """
        brief = TopicBrief(
            topic_name=topic.get("name", "Unknown Topic").title(),
            educational_value=topic.get("educational_value", 0.5),
            source_slides=topic.get("slides", [])[:10]
        )
        
        # Extract main content
        brief.main_content = topic.get("main_text", "")
        
        # Extract definitions (for concise answers)
        definitions = topic.get("definitions", [])
        brief.definitions = definitions[:self.max_definitions]
        
        # Extract examples (for real_world_use_case and example)
        examples = topic.get("examples", [])
        # Prioritize specific, detailed examples
        brief.examples = self._prioritize_examples(examples)[:self.max_examples]
        
        # Extract diagrams (for mermaid_diagrams and analogy)
        diagrams = topic.get("diagrams", [])
        # Filter for educational diagrams
        brief.diagrams = self._filter_educational_diagrams(diagrams)[:self.max_diagrams]
        
        # Extract key concepts
        key_concepts = topic.get("key_concepts", [])
        brief.key_concepts = key_concepts[:self.max_concepts]
        
        # Extract academic references from content
        if self.extract_references:
            brief.academic_references = self._extract_references(
                brief.main_content + " " + topic.get("notes", "")
            )
        
        # Generate concept relationships for common_mistakes
        if self.generate_relationships:
            brief.relationships = self._generate_relationships(
                brief.definitions,
                brief.key_concepts
            )
        
        # Add context from structured_content if available
        if structured_content:
            # Add summary
            brief.summary = structured_content.get("summary", "")[:500]
            
            # Add learning objectives
            objectives = structured_content.get("learning_objectives", [])
            brief.learning_objectives = objectives[:5]
            
            # Enrich with section-level key points
            sections = structured_content.get("sections", [])
            for section in sections:
                if isinstance(section, dict):
                    key_points = section.get("key_points", [])
                    for point in key_points:
                        if point not in brief.key_concepts:
                            brief.key_concepts.append(point)
        
        return brief
    
    def build_from_semantic_chunk(
        self,
        chunk: Dict[str, Any],
        all_topics: List[Dict[str, Any]],
        structured_content: Optional[Dict[str, Any]] = None,
        lecture_title: str = ""
    ) -> TopicBrief:
        """
        Build a TopicBrief from a semantic chunk.
        
        Args:
            chunk: Semantic chunk dictionary
            all_topics: List of all consolidated topics
            structured_content: Optional structured_content from LLM condensing
            lecture_title: Title of the lecture
            
        Returns:
            TopicBrief combining all topics in the chunk
        """
        topic_names = chunk.get("topics", [])
        
        # Find the actual topic data
        chunk_topics = []
        for topic in all_topics:
            if topic.get("name") in topic_names:
                chunk_topics.append(topic)
        
        if not chunk_topics:
            # Fallback: create from chunk content directly
            return TopicBrief(
                topic_name=", ".join(topic_names).title(),
                educational_value=chunk.get("educational_value", 0.5),
                source_slides=[],
                main_content=chunk.get("content", ""),
                key_concepts=chunk.get("key_concepts", [])[:self.max_concepts]
            )
        
        # Merge multiple topics into one brief
        merged_brief = TopicBrief(
            topic_name=" & ".join([t.get("name", "").title() for t in chunk_topics]),
            educational_value=max(t.get("educational_value", 0.5) for t in chunk_topics),
            source_slides=[]
        )
        
        # Merge content from all topics
        all_slides = []
        all_definitions = []
        all_examples = []
        all_diagrams = []
        all_concepts = []
        all_main_text = []
        
        for topic in chunk_topics:
            all_slides.extend(topic.get("slides", []))
            all_definitions.extend(topic.get("definitions", []))
            all_examples.extend(topic.get("examples", []))
            all_diagrams.extend(topic.get("diagrams", []))
            all_concepts.extend(topic.get("key_concepts", []))
            if topic.get("main_text"):
                all_main_text.append(topic.get("main_text"))
        
        # Deduplicate
        merged_brief.source_slides = list(dict.fromkeys(all_slides))[:10]
        merged_brief.definitions = self._deduplicate_definitions(all_definitions)[:self.max_definitions]
        merged_brief.examples = self._prioritize_examples(all_examples)[:self.max_examples]
        merged_brief.diagrams = self._filter_educational_diagrams(all_diagrams)[:self.max_diagrams]
        merged_brief.key_concepts = list(dict.fromkeys(all_concepts))[:self.max_concepts]
        merged_brief.main_content = "\n\n".join(all_main_text)
        
        # Extract references and relationships
        if self.extract_references:
            merged_brief.academic_references = self._extract_references(
                merged_brief.main_content
            )
        
        if self.generate_relationships:
            merged_brief.relationships = self._generate_relationships(
                merged_brief.definitions,
                merged_brief.key_concepts
            )
        
        # Add structured_content context
        if structured_content:
            merged_brief.summary = structured_content.get("summary", "")[:500]
            merged_brief.learning_objectives = structured_content.get("learning_objectives", [])[:5]
        
        return merged_brief
    
    def _prioritize_examples(self, examples: List[str]) -> List[str]:
        """
        Prioritize examples that are most useful for flashcards.
        
        Criteria:
        1. Contains company/brand names (Nike, Amazon, etc.)
        2. Contains specific details (numbers, prices, dates)
        3. Is longer and more detailed
        """
        scored = []
        
        company_keywords = [
            "nike", "amazon", "apple", "google", "microsoft", "coca-cola", "ikea",
            "adidas", "samsung", "tesla", "netflix", "spotify", "uber", "airbnb",
            "starbucks", "mcdonald", "disney", "facebook", "instagram", "twitter"
        ]
        
        for example in examples:
            if not example or not isinstance(example, str):
                continue
            
            score = 0
            example_lower = example.lower()
            
            # Company name bonus
            for company in company_keywords:
                if company in example_lower:
                    score += 3
                    break
            
            # Specificity bonus (numbers, percentages, prices)
            import re
            if re.search(r'\d+%|\$\d+|€\d+|\d+ years|\d+ users', example):
                score += 2
            
            # Length bonus (longer = more detailed)
            if len(example) > 100:
                score += 1
            if len(example) > 200:
                score += 1
            
            # Avoid generic examples
            generic_phrases = ["for example", "e.g.", "such as", "like"]
            if any(phrase in example_lower for phrase in generic_phrases) and len(example) < 50:
                score -= 1
            
            scored.append((score, example))
        
        # Sort by score descending
        scored.sort(key=lambda x: -x[0])
        
        return [example for score, example in scored]
    
    def _filter_educational_diagrams(self, diagrams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter for diagrams that are educationally valuable."""
        educational_types = {
            "flowchart", "diagram", "table", "framework", "matrix", "chart",
            "process", "hierarchy", "timeline", "comparison", "model"
        }
        
        non_educational_types = {
            "logo", "photo", "image", "illustration", "icon", "screenshot"
        }
        
        result = []
        
        for diagram in diagrams:
            if not isinstance(diagram, dict):
                continue
            
            dtype = diagram.get("type", "").lower()
            
            # Skip non-educational
            if any(ne in dtype for ne in non_educational_types):
                continue
            
            # Prioritize educational
            if any(ed in dtype for ed in educational_types):
                result.append(diagram)
            elif diagram.get("key_points"):  # Has key points = educational
                result.append(diagram)
        
        return result
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract academic references from text."""
        import re
        
        references = []
        
        # Pattern for citations like "Lemon & Verhoef (2016)" or "(Smith, 2020)"
        patterns = [
            r'([A-Z][a-z]+(?:\s*[&,]\s*[A-Z][a-z]+)*)\s*\((\d{4})\)',  # Author (Year)
            r'\(([A-Z][a-z]+(?:\s*[&,]\s*[A-Z][a-z]+)*),?\s*(\d{4})\)',  # (Author, Year)
            r'([A-Z][a-z]+\s+et\s+al\.?)\s*\((\d{4})\)',  # Author et al. (Year)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    ref = f"{match[0]} ({match[1]})"
                else:
                    ref = match
                if ref not in references:
                    references.append(ref)
        
        return references[:5]  # Limit to 5 references
    
    def _generate_relationships(
        self,
        definitions: List[Dict[str, str]],
        key_concepts: List[str]
    ) -> List[str]:
        """
        Generate concept relationships to help prevent common mistakes.
        
        These highlight distinctions between similar concepts.
        """
        relationships = []
        
        # Find similar terms in definitions
        terms = [d.get("term", "").lower() for d in definitions]
        
        # Look for related terms that might be confused
        confusion_pairs = [
            ("pre-purchase", "post-purchase"),
            ("brand-owned", "customer-owned"),
            ("brand-owned", "partner-owned"),
            ("partner-owned", "customer-owned"),
            ("awareness", "consideration"),
            ("familiarity", "loyalty"),
            ("touchpoint", "channel"),
            ("persona", "segment"),
            ("buyer", "shopper"),
            ("purchase", "consumption"),
        ]
        
        for term1, term2 in confusion_pairs:
            term1_found = any(term1 in t for t in terms) or any(term1 in c.lower() for c in key_concepts)
            term2_found = any(term2 in t for t in terms) or any(term2 in c.lower() for c in key_concepts)
            
            if term1_found and term2_found:
                relationships.append(
                    f"'{term1.title()}' vs '{term2.title()}' - Don't confuse these related but distinct concepts"
                )
        
        # Add generic relationship for stages if found
        if any("stage" in t for t in terms):
            relationships.append(
                "The stages are sequential - understand the order and what happens at each"
            )
        
        return relationships[:5]
    
    def _deduplicate_definitions(self, definitions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Deduplicate definitions by term."""
        seen_terms = set()
        result = []
        
        for defn in definitions:
            term = defn.get("term", "").lower().strip()
            if term and term not in seen_terms:
                seen_terms.add(term)
                result.append(defn)
        
        return result


def build_enriched_prompt_context(
    consolidation_result: Dict[str, Any],
    structured_content: Optional[Dict[str, Any]] = None,
    lecture_title: str = "",
    chunk_index: int = 0
) -> str:
    """
    Convenience function to build enriched prompt context from consolidation result.
    
    Args:
        consolidation_result: Output from ContentConsolidator
        structured_content: Optional structured_content from database
        lecture_title: Title of the lecture
        chunk_index: Which semantic chunk to process (0-indexed)
        
    Returns:
        Structured prompt context string
    """
    builder = TopicBriefBuilder()
    
    topics = consolidation_result.get("topics", [])
    chunks = consolidation_result.get("semantic_chunks", [])
    
    if chunk_index < len(chunks):
        chunk = chunks[chunk_index]
        brief = builder.build_from_semantic_chunk(
            chunk=chunk,
            all_topics=topics,
            structured_content=structured_content,
            lecture_title=lecture_title
        )
    elif topics:
        # Fallback: use first topic
        brief = builder.build_from_consolidated_topic(
            topic=topics[0],
            structured_content=structured_content,
            lecture_title=lecture_title
        )
    else:
        # Empty case
        return ""
    
    return brief.to_prompt_context()


