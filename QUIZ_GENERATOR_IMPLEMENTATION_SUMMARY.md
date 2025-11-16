# Quiz Generator Implementation Summary

## ✅ Implementation Complete

A comprehensive multi-level quiz generation system has been successfully implemented to generate MCQ questions from cognitive flashcards.

## Files Created

### 1. `cognitive_flashcard_generator/quiz_generator.py` (new)
**Purpose**: Core quiz generation logic

**Key Components**:
- `QuizGenerator` class with AI-powered question generation
- `_load_quiz_prompt_template(level)` - Loads level-specific prompts
- `generate_quiz_questions()` - Main generation method
- `_generate_with_retry()` - Retry logic with exponential backoff
- `_parse_quiz_response()` - JSON parsing and validation
- `_try_parse_json_with_fixes()` - Robust JSON parsing with fallbacks
- `_validate_question()` - Question structure validation

**Features**:
- Supports 4 difficulty levels (1-4)
- Handles chunked flashcard processing
- Automatic retry with reduced chunk sizes
- Comprehensive error handling

### 2. `generate_quizzes.py` (new)
**Purpose**: Entry point script for quiz generation

**Usage**:
```bash
python generate_quizzes.py                    # All courses
python generate_quizzes.py MS5130             # Specific course
python generate_quizzes.py MS5130 OR_lec_1    # Specific lecture
```

**Features**:
- Command-line interface
- Course and lecture targeting
- Integration with existing course infrastructure

### 3. `cognitive_flashcard_generator/main.py` (modified)
**Changes Made**:
- Added import: `from .quiz_generator import QuizGenerator`
- Added `save_quiz_json()` helper function
- Added `process_course_quizzes()` function (167 lines)

**New Function: `process_course_quizzes()`**:
- Loads flashcards from `*_cognitive_flashcards_only.json`
- Extracts relevant content (question, all answers, example)
- Chunks flashcards into groups of 4
- Generates quizzes for all 4 difficulty levels
- Saves to `courses/{course_id}/quiz/{lecture}_level_{level}_quiz.json`

### 4. `QUIZ_GENERATION_GUIDE.md` (documentation)
Comprehensive guide covering:
- System overview and architecture
- Usage instructions
- Input/output structures
- Difficulty level specifications
- Error handling and troubleshooting
- Integration examples

## How It Works

### Workflow

```
1. Load Flashcards
   ↓
2. Extract Content
   (question + all answers + example)
   ↓
3. Create Simplified Structure
   ↓
4. Chunk Flashcards
   (groups of 4)
   ↓
5. For Each Level (1-4):
   ├─ Load Level Prompt
   ├─ For Each Chunk:
   │  ├─ Send to Gemini AI
   │  ├─ Parse Response
   │  └─ Validate Questions
   ├─ Aggregate All Questions
   └─ Save Level Quiz JSON
```

### Input Structure (Simplified Flashcards)

```json
{
  "id": "OR_lec_1_1",
  "question": "What is Operations Research?",
  "answers": {
    "concise": "...",
    "analogy": "...",
    "eli5": "...",
    "real_world_use_case": "...",
    "common_mistakes": "..."
  },
  "example": "...",
  "context": "...",
  "tags": ["..."]
}
```

### Output Structure (Quiz Questions)

```json
{
  "metadata": {
    "generated_at": "2025-11-03T...",
    "total_questions": 80,
    "course_name": "Operations Research",
    "course_id": "MS5130",
    "lecture": "OR_lec_1",
    "difficulty_level": 1,
    "source_flashcards": 16
  },
  "questions": [
    {
      "type": "mcq",
      "question_text": "...",
      "visual_type": "None" | "Graphviz" | "Plotly" | "LaTeX",
      "visual_code": "...",
      "alt_text": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "...",
      "explanation": "...",
      "difficulty_level": 1,
      "source_flashcard_id": "OR_lec_1_1",
      "tags": ["..."]
    }
  ]
}
```

## Key Features

### 1. Multi-Level Generation
- **Level 1**: Foundation (70-80% pass rate, 30-45 sec)
- **Level 2**: Comprehension & Application (50-65% pass rate, 60-90 sec)
- **Level 3**: Analysis & Critical Thinking (30-45% pass rate, 90-120 sec)
- **Level 4**: Synthesis & Mastery (15-30% pass rate, 120-180 sec)

### 2. Intelligent Chunking
- Processes 4 flashcards per chunk
- Expected output: 20 questions per chunk (5 per flashcard)
- Prevents token limit issues

### 3. Retry Logic
- Automatic retry on failure
- Progressive reduction: 100% → 70% → 49%
- Reduces both chunk size and token limits

### 4. Robust Parsing
- Multiple JSON parsing strategies
- Handles malformed AI responses
- Extracts partial valid JSON when possible
- Fixes common JSON errors automatically

### 5. Comprehensive Validation
- Checks all required fields
- Validates options structure (A, B, C, D)
- Ensures correct_answer and explanation are present
- Provides detailed error messages

## Directory Structure

```
courses/
└── MS5130/
    ├── cognitive_flashcards/
    │   └── OR_lec_1/
    │       └── OR_lec_1_cognitive_flashcards_only.json
    └── quiz/                                    ← NEW
        ├── OR_lec_1_level_1_quiz.json          ← NEW
        ├── OR_lec_1_level_2_quiz.json          ← NEW
        ├── OR_lec_1_level_3_quiz.json          ← NEW
        └── OR_lec_1_level_4_quiz.json          ← NEW
```

## Configuration

### Model
- Default: `gemini-2.5-flash`
- Temperature: `0.8` (creative question generation)
- Max output tokens: `16384` (with progressive reduction on retry)

### Prompts
Located in `prompts/`:
- `level_1_quiz_prompt.txt` - Foundation questions
- `level_2_quiz_prompt.txt` - Application questions
- `level_3_quiz_prompt.txt` - Analysis questions
- `level_4_quiz_prompt.txt` - Synthesis questions

## Testing Plan

### Recommended Test Scenario

```bash
# Step 1: Ensure flashcards exist
python -m cognitive_flashcard_generator.main MS5130 OR_lec_1

# Step 2: Generate quizzes
python generate_quizzes.py MS5130 OR_lec_1

# Expected Output:
# - courses/MS5130/quiz/OR_lec_1_level_1_quiz.json
# - courses/MS5130/quiz/OR_lec_1_level_2_quiz.json
# - courses/MS5130/quiz/OR_lec_1_level_3_quiz.json
# - courses/MS5130/quiz/OR_lec_1_level_4_quiz.json
```

### What to Verify

1. **Files Created**: 4 quiz JSON files per lecture
2. **Question Count**: ~80 questions (16 flashcards × 5 questions per flashcard)
3. **Structure**: Metadata + questions array
4. **Question Fields**: All required fields present
5. **Difficulty**: Questions match their difficulty level
6. **Visuals**: Visual_type, visual_code, alt_text populated when appropriate
7. **Explanations**: Comprehensive explanations for each question

## Performance Expectations

### For OR_lec_1 (example with 16 flashcards)

- **Chunks**: 4 chunks (4 flashcards each)
- **Questions per Level**: ~80 (16 flashcards × 5 questions)
- **Total Questions**: ~320 (4 levels × 80 questions)
- **Processing Time**: ~20-40 minutes (all 4 levels)
- **API Calls**: 16 calls (4 chunks × 4 levels)

## Integration Notes

### Frontend Integration

The quiz JSON can be directly consumed by the frontend:

```javascript
// Load quiz
const quizData = await fetch('/courses/MS5130/quiz/OR_lec_1_level_1_quiz.json');
const quiz = await quizData.json();

// Access questions
const questions = quiz.questions;

// Display question
const q = questions[0];
console.log(q.question_text);
console.log(q.options);
console.log(q.correct_answer);
```

### Backend Integration

The quiz generation can be triggered programmatically:

```python
from cognitive_flashcard_generator.main import process_course_quizzes
from cognitive_flashcard_generator.utils import load_courses, get_course_by_id

courses = load_courses()
course = get_course_by_id("MS5130", courses)
process_course_quizzes(course, "OR_lec_1")
```

## Error Handling

### Graceful Degradation
- If a chunk fails after all retries, processing continues with next chunk
- Partial results are saved
- Detailed error messages for debugging

### Common Scenarios Handled
- Token limit exceeded → Retry with smaller chunks
- Invalid JSON → Multiple parsing strategies
- Missing flashcards → Clear error messages with suggestions
- API errors → Retry logic with exponential backoff

## Next Steps

1. ✅ Implementation Complete
2. ⏳ Testing Required
3. 📋 Future Enhancements:
   - Question deduplication
   - Difficulty calibration based on performance
   - Export to LMS formats (Moodle, Canvas, etc.)
   - Visual pre-rendering (Graphviz, LaTeX)
   - Question bank versioning

## Success Criteria

✅ **Implemented**:
- Quiz generator module created
- Entry point script created
- Integration with main.py complete
- Comprehensive documentation written
- Error handling and retry logic implemented
- Support for all 4 difficulty levels
- Chunking strategy implemented
- JSON validation implemented

⏳ **Pending**:
- Run test with sample course (OR_lec_1)
- Verify output quality
- Frontend integration (separate task)

## Related Files

- `QUIZ_GENERATION_GUIDE.md` - User guide
- `FLASHCARD_GENERATION_UPDATE.md` - Flashcard system docs
- `cognitive_flashcard_generator/quiz_generator.py` - Core implementation
- `generate_quizzes.py` - Entry point
- `prompts/level_*_quiz_prompt.txt` - Prompt templates

