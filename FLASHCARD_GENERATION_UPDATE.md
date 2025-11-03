# Flashcard Generation System Update

## Overview
Updated the cognitive flashcard generation system to create flashcards **without** `recall_questions` using a new dedicated prompt template.

## Changes Made

### 1. Modified `cognitive_flashcard_generator/generator.py`

#### Change 1: Updated Prompt Template Path
**Location:** Line 35 in `load_prompt_template()` method

- **Before:** Used `intelligent_flashcard_prompt.txt`
- **After:** Uses `intelligent_flashcard_only_prompt.txt`

This ensures the generator uses the new prompt template that doesn't include recall questions in its output specification.

#### Change 2: Removed Recall Questions Statistics
**Location:** Lines 127-130 in `_generate_with_retry()` method

- **Removed:** Display of recall questions count in generation statistics
- **Kept:** Mermaid diagrams, math visualizations, and examples statistics

#### Change 3: Removed Recall Questions Field Assignment
**Location:** Lines 182-196 in `_parse_flashcard_response()` method

- **Removed:** `if 'recall_questions' not in card: card['recall_questions'] = []`
- **Result:** Flashcards will no longer have a `recall_questions` field

### 2. Modified `cognitive_flashcard_generator/main.py`

#### Change: Updated Output Filename
**Location:** Line 455 in `process_course_flashcards()` function

- **Before:** `{lecture_name}_cognitive_flashcards.json`
- **After:** `{lecture_name}_cognitive_flashcards_only.json`

This creates a clear distinction between flashcard files with and without recall questions.

## Usage

To generate new flashcards without recall questions, use the same commands as before:

```bash
# Generate for all courses
python -m cognitive_flashcard_generator.main

# Generate for a specific course
python -m cognitive_flashcard_generator.main MS5130

# Generate for a specific lecture
python -m cognitive_flashcard_generator.main MS5130 OR_lec_1
```

## Output

The generated files will now:
- Be named with the `_only` suffix: `*_cognitive_flashcards_only.json`
- **NOT** contain `recall_questions` field in any flashcard object
- Contain all other fields: `question`, `answers` (all 5 types), `example`, `mermaid_diagrams`, `math_visualizations`, etc.

## File Structure Example

```
courses/MS5130/cognitive_flashcards/OR_lec_1/
├── OR_lec_1_cognitive_flashcards_only.json  ← New output file
└── diagrams/
    ├── OR_lec_1_1_card_001_concise.png
    ├── OR_lec_1_1_card_001_analogy.png
    └── ...
```

## Backwards Compatibility

- The old prompt file (`intelligent_flashcard_prompt.txt`) remains unchanged
- The old script (`create_flashcards_only.py`) remains in the root directory
- This is a replacement of the generation process, not an addition

## Related Files

- ✅ `prompts/intelligent_flashcard_only_prompt.txt` - New prompt template (already exists)
- ✅ `prompts/intelligent_flashcard_prompt_with_recall_questions.txt` - Old prompt (kept for reference)
- ✅ `cognitive_flashcard_generator/generator.py` - Modified
- ✅ `cognitive_flashcard_generator/main.py` - Modified
- ⚠️  `create_flashcards_only.py` - Kept but now redundant (can be removed if desired)

## Next Steps

1. Test the generation with a sample lecture to verify output
2. Update frontend to use the new `*_only.json` files if needed
3. Update deployment scripts if they reference the old filename pattern

