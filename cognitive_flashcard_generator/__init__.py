"""
Cognitive Flashcard Generator - Universal engine for creating intelligent study materials.

This package generates flashcards with:
- Relevance scoring (1-10) for exam importance
- Textbook-aligned examples
- PlantUML diagrams (code preserved for on-demand rendering)
- Future-proof JSON for React frontends

Features:
- Works with any subject/textbook
- Dynamic prompt population
- Hybrid approach: stores PlantUML code (new) while keeping legacy Mermaid support
- Optional Mermaid CLI rendering for historical diagrams
- Course-aware: reads from courses.json for all metadata
"""

__version__ = "1.0.0"

