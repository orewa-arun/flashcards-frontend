# Quiz Generation System Guide

## Overview

This system generates multi-level quiz questions from cognitive flashcards using AI-powered question generation. It creates four difficulty levels of multiple-choice questions (MCQs) based on existing flashcard content.

## Features

- **4 Difficulty Levels**: Foundation (L1), Comprehension & Application (L2), Analysis & Critical Thinking (L3), Synthesis & Mastery (L4)
- **Intelligent Chunking**: Processes flashcards in manageable chunks to handle large datasets
- **Retry Logic**: Automatic retry with reduced chunk sizes if generation fails
- **Structured Output**: JSON format with metadata for easy integration
- **Visual Support**: Questions can include Graphviz, Plotly, or LaTeX visualizations

## Architecture

### New Files Created

1. **`cognitive_flashcard_generator/quiz_generator.py`**
   - Core `QuizGenerator` class
   - Handles AI-powered question generation
   - Implements retry logic and error handling
   - Validates question structure

2. **`generate_quizzes.py`**
   - Entry point script for quiz generation
   - Command-line interface
   - Orchestrates the quiz generation workflow

3. **Modified: `cognitive_flashcard_generator/main.py`**
   - Added `process_course_quizzes()` function
   - Added `save_quiz_json()` helper function
   - Imports `QuizGenerator` class

## Usage

### Command Line

```bash
# Generate quizzes for all courses
python generate_quizzes.py

# Generate quizzes for a specific course
python generate_quizzes.py MS5130

# Generate quizzes for a specific lecture
python generate_quizzes.py MS5130 OR_lec_1
```

### Prerequisites

1. **Flashcards must exist**: Run the flashcard generator first
   ```bash
   python -m cognitive_flashcard_generator.main MS5130
   ```

2. **Flashcard files required**: `*_cognitive_flashcards_only.json` files must be present in:
   ```
   courses/{course_id}/cognitive_flashcards/{lecture_name}/
   ```

## How It Works

### Input Processing

1. **Load Flashcards**: Reads `*_cognitive_flashcards_only.json` files
2. **Extract Content**: For each flashcard, extracts:
   - Question
   - All 5 answer types (concise, analogy, eli5, real_world_use_case, common_mistakes)
   - Example
   - Context
   - Tags
3. **Create Simplified Structure**: Builds a simplified JSON structure for AI processing

### Chunking Strategy

- **Chunk Size**: 4 flashcards per chunk
- **Expected Output**: ~20 questions per chunk (5 questions per flashcard × 4 flashcards)
- **Retry Logic**: Reduces chunk size by 30% on each retry if generation fails

### AI Generation

For each difficulty level (1-4):
1. Loads the appropriate prompt template (`prompts/level_{level}_quiz_prompt.txt`)
2. Sends flashcard chunk to Gemini AI
3. Receives JSON array of quiz questions
4. Validates and parses the response
5. Aggregates questions from all chunks

## Output Structure

### Directory Layout

```
courses/{course_id}/
├── cognitive_flashcards/
│   └── {lecture_name}/
│       └── {lecture_name}_cognitive_flashcards_only.json
└── quiz/
    ├── {lecture_name}_level_1_quiz.json
    ├── {lecture_name}_level_2_quiz.json
    ├── {lecture_name}_level_3_quiz.json
    └── {lecture_name}_level_4_quiz.json
```

### Quiz JSON Structure

```json
{
  "metadata": {
    "generated_at": "2025-11-03T12:00:00",
    "total_questions": 80,
    "course_name": "Operations Research",
    "course_id": "MS5130",
    "course_code": "OR",
    "textbook_reference": "Reference textbook info",
    "lecture": "OR_lec_1",
    "difficulty_level": 1,
    "source_flashcards": 16
  },
  "questions": [
    {
      "type": "mcq",
      "question_text": "What is...",
      "visual_type": "None" | "Graphviz" | "Plotly" | "LaTeX",
      "visual_code": "...", 
      "alt_text": "...",
      "options": {
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      },
      "correct_answer": "Full text of the correct option",
      "explanation": "Detailed explanation...",
      "difficulty_level": 1,
      "source_flashcard_id": "OR_lec_1_1",
      "tags": ["tag1", "tag2"]
    }
  ]
}
```

## Difficulty Levels

### Level 1: Foundation (30-45 seconds)
- **Cognitive Load**: Single concept, direct application
- **Target Pass Rate**: 70-80%
- **Question Type**: "What is...", "Which of these is...", "Identify the..."

### Level 2: Comprehension & Application (60-90 seconds)
- **Cognitive Load**: Single concept, applied in new context
- **Target Pass Rate**: 50-65%
- **Question Type**: "Given [scenario], what happens?", "How would you apply..."

### Level 3: Analysis & Critical Thinking (90-120 seconds)
- **Cognitive Load**: Multiple related concepts, requires comparison/evaluation
- **Target Pass Rate**: 30-45%
- **Question Type**: "Why did [problem] occur?", "What is the most likely error..."
- **Must Include**: Trick elements (business requirement contradicts theory, temporal dependency, etc.)

### Level 4: Synthesis & Mastery (120-180 seconds)
- **Cognitive Load**: 2-3 concepts from different topics/lectures
- **Target Pass Rate**: 15-30%
- **Question Type**: "What is the root cause...", "Which approach best balances..."
- **Must Include**: Integration of concepts from 2+ lectures, second-order consequences

## Configuration

### Model Settings

In `cognitive_flashcard_generator/quiz_generator.py`:
```python
model: str = "gemini-2.0-flash-exp"  # Default model
temperature: 0.8                      # Creative question generation
max_output_tokens: 16384             # Base token limit
```

### Prompt Templates

Located in `prompts/`:
- `level_1_quiz_prompt.txt`
- `level_2_quiz_prompt.txt`
- `level_3_quiz_prompt.txt`
- `level_4_quiz_prompt.txt`

Each prompt contains:
- Core task description
- Difficulty rubric
- Concept extraction framework
- Distractor design patterns
- Visual generation toolkit
- Answer explanation template
- Output format specification

## Error Handling

### Retry Strategy

1. **Attempt 1**: Full chunk (4 flashcards)
2. **Attempt 2**: Reduced to ~3 flashcards (70% of original)
3. **Attempt 3**: Reduced to ~2 flashcards (49% of original)

### Common Issues

1. **Token Limit Exceeded**
   - Automatically retries with smaller chunks
   - Reduces max_output_tokens progressively

2. **Invalid JSON Response**
   - Multiple parsing strategies with fallbacks
   - Attempts to extract partial valid JSON
   - Removes trailing commas and fixes common errors

3. **Missing Flashcards**
   - Clear error messages with available options
   - Suggests running flashcard generator first

## Integration Example

```python
from cognitive_flashcard_generator.quiz_generator import QuizGenerator
from cognitive_flashcard_generator.utils import load_courses, get_course_by_id

# Load course
courses = load_courses()
course = get_course_by_id("MS5130", courses)

# Initialize generator
quiz_gen = QuizGenerator(
    api_key=Config.GEMINI_API_KEY,
    model="gemini-2.0-flash-exp",
    course_name=course['course_name'],
    textbook_reference="; ".join(course['reference_textbooks'])
)

# Generate questions
flashcards = [...]  # Load from JSON
questions = quiz_gen.generate_quiz_questions(
    flashcards_chunk=flashcards[:4],
    level=1,
    chunk_info="Chunk 1/5"
)
```

## Performance Expectations

### Processing Time

- **Per Flashcard Chunk (4 cards)**: 30-60 seconds per level
- **Per Lecture (16 flashcards, 4 levels)**: ~20-40 minutes
- **Per Course (multiple lectures)**: Varies based on lecture count

### Question Output

- **Expected**: 5 questions per flashcard per level
- **Example**: 16 flashcards × 5 questions × 4 levels = **320 total questions**

## Troubleshooting

### Issue: No flashcards found
**Solution**: Generate flashcards first using:
```bash
python -m cognitive_flashcard_generator.main MS5130
```

### Issue: API errors or timeout
**Solution**: 
- Check `Config.GEMINI_API_KEY` is set correctly
- Verify internet connection
- Wait and retry (API rate limits)

### Issue: Low quality questions
**Solution**:
- Review and adjust prompt templates in `prompts/`
- Modify temperature setting (lower = more conservative)
- Ensure flashcard content is comprehensive

## Future Enhancements

1. **Question Deduplication**: Detect and remove similar questions
2. **Difficulty Calibration**: Adjust based on actual student performance
3. **Question Bank Management**: Version control and update tracking
4. **Export Formats**: Support for various LMS formats (Moodle XML, etc.)
5. **Visual Rendering**: Pre-render Graphviz and LaTeX in backend

## Related Documentation

- `FLASHCARD_GENERATION_UPDATE.md` - Flashcard generation system
- `prompts/README.md` - Prompt engineering guidelines
- `cognitive_flashcard_generator/README.md` - Module documentation

