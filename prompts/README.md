# AI Prompts Directory

This directory contains the prompt templates used by the flashcard generation system.

## Files

- `flashcard_generation_prompt.txt` - Main prompt for generating flashcards from content
- `content_analysis_prompt.txt` - Prompt for analyzing content structure and topics

## Customization

You can modify these prompt files to:
- Change the style of generated flashcards
- Adjust the difficulty level
- Modify the types of questions generated
- Update LaTeX formatting instructions
- Add new flashcard types

## Format

The prompts use Python string formatting with placeholders:
- `{context}` - The context for the content (e.g., "Academic lecture material")
- `{content}` - The actual content to process

## Usage

The system automatically loads these prompts when generating flashcards. No code changes are needed to use modified prompts.
