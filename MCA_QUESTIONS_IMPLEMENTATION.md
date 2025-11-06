# Multiple Correct Answer (MCA) Questions Implementation

## Overview
This document describes the implementation of Multiple Correct Answer (MCA) questions in the self-learning AI platform. MCA questions allow for more challenging and nuanced assessments by requiring students to select all correct answers from a set of options.

## Implementation Summary

### 1. Quiz Generation Prompts (AI Layer)

Updated all four difficulty level prompts (`level_1_quiz_prompt.txt` through `level_4_quiz_prompt.txt`) to support both MCQ and MCA question types with progressive difficulty ratios:

- **Level 1 (Foundation):** 95% MCQ, 5% MCA
- **Level 2 (Comprehension & Application):** 70% MCQ, 30% MCA
- **Level 3 (Analysis & Critical Thinking):** 50% MCQ, 50% MCA
- **Level 4 (Synthesis & Mastery):** 30% MCQ, 70% MCA

#### Key Changes:
- Added `"mca"` as a new question type
- Updated validation checklists to handle 2-3 correct answers for MCA questions
- Modified output format to use `correct_answers` (array) for MCA vs `correct_answer` (string) for MCQ
- Added instruction to include "(Select all that apply)" in MCA question text
- Required explanations to address why each option is correct or incorrect

### 2. Backend Models

#### `backend/app/models/adaptive_quiz.py`

**QuizQuestion Model:**
- Updated `question_type` description to include `"mca"`
- Modified `correct_answer` field description to clarify it can be a string (MCQ) or list (MCA)

**QuestionResult Model:**
- Added `partial_credit_score` field (Optional[float]) to store partial credit for MCA questions (0.0 to 1.0)

### 3. Backend Scoring Logic

#### `backend/app/routers/quiz.py`

**Updated `compare_answers` function:**
- Changed return type from `bool` to `tuple[bool, Optional[float]]`
- Returns `(is_correct, partial_credit_score)` for all question types
- For MCA questions:
  - Normalizes user answers and correct answers as sets
  - Calculates partial credit: `(correct_selections - incorrect_selections) / total_correct`
  - Uses floor of 0 (no negative scores)
  - Marks as fully correct only if all correct answers selected and no incorrect ones

**Scoring Formula for MCA:**
```python
correct_selections = len(user_set & correct_set)  # Intersection
incorrect_selections = len(user_set - correct_set)  # Wrong selections
raw_score = correct_selections - incorrect_selections
partial_score = max(0, raw_score) / total_correct
```

**Updated `submit_quiz` function:**
- Changed score from `int` to `float` to support partial credit
- For MCA questions, adds partial credit score to total
- For other question types, maintains binary scoring (0 or 1)
- Rounds final score for display purposes

### 4. Frontend Components

#### `frontend/src/components/QuestionRenderer.jsx`

**Added MCARenderer component:**
- Renders checkboxes instead of radio buttons
- Manages array of selected answers
- Displays "(Select all that apply)" instruction
- Shows visual feedback for:
  - **Correct:** Green border (options that should be selected)
  - **Incorrect:** Red border (options incorrectly selected)
  - **Missed:** Yellow/warning border (correct options not selected)
- Displays selection count feedback after submission

#### `frontend/src/components/QuestionRenderer.css`

**Added MCA-specific styles:**
- `.mca-question` - Container styling
- `.checkbox-option` - Flexbox layout for checkbox + text
- `.checkbox-wrapper` - Checkbox alignment
- `.option-checkbox` - Checkbox styling with accent color
- `.option-item.missed` - Warning style for missed correct answers
- `.mca-feedback` - Feedback panel styling

#### `frontend/src/components/Quiz.jsx`

**Updated `checkAnswer` function:**
- Added case for `'mca'` type
- Compares sorted arrays of user answers vs correct answers
- Uses JSON.stringify for deep equality check

**Updated `handleSubmit` function:**
- Special handling for MCA questions to allow empty arrays
- Validates that userAnswer is an array for MCA questions

## Data Flow

### Question Generation Flow
1. AI receives flashcard data and difficulty level
2. AI generates mix of MCQ and MCA questions based on level
3. For MCA questions, AI creates `correct_answers` array with 2-3 correct options
4. Questions stored in quiz session with proper type designation

### Question Rendering Flow
1. Frontend receives question with `type: "mca"`
2. QuestionRenderer switches to MCARenderer component
3. User selects multiple options via checkboxes
4. Selections stored as array in component state

### Submission & Scoring Flow
1. Frontend submits answers (array for MCA, string for MCQ)
2. Backend `compare_answers` function:
   - For MCA: Calculates partial credit based on correct/incorrect selections
   - For MCQ: Binary correct/incorrect
3. Backend aggregates scores (sum of partial credits + binary scores)
4. Backend returns results with `partial_credit_score` for each question
5. Frontend displays results with appropriate feedback

## Example MCA Question Structure

```json
{
  "type": "mca",
  "question_text": "Which of the following are characteristics of a good database design? (Select all that apply)",
  "options": [
    "Minimizes data redundancy",
    "Ensures data integrity",
    "Maximizes table size",
    "Maintains data consistency"
  ],
  "correct_answers": [
    "Minimizes data redundancy",
    "Ensures data integrity",
    "Maintains data consistency"
  ],
  "explanation": "Options A, B, and D are correct because they represent fundamental principles of good database design. Option C is incorrect because maximizing table size is not a design goal; efficient storage is preferred.",
  "difficulty_level": 2,
  "source_flashcard_id": "DB_lec_4_2",
  "tags": ["database", "design", "normalization"]
}
```

## Scoring Examples

### Example 1: Perfect Score
- Correct answers: [A, B, C]
- User selected: [A, B, C]
- Calculation: (3 correct - 0 incorrect) / 3 = 1.0
- **Score: 1.0 (100%)**

### Example 2: Partial Credit
- Correct answers: [A, B, C]
- User selected: [A, B]
- Calculation: (2 correct - 0 incorrect) / 3 = 0.67
- **Score: 0.67 (67%)**

### Example 3: With Incorrect Selection
- Correct answers: [A, B, C]
- User selected: [A, B, D]
- Calculation: (2 correct - 1 incorrect) / 3 = 0.33
- **Score: 0.33 (33%)**

### Example 4: More Wrong Than Right
- Correct answers: [A, B, C]
- User selected: [A, D, E]
- Calculation: (1 correct - 2 incorrect) / 3 = -0.33 → max(0, -0.33) = 0.0
- **Score: 0.0 (0%)**

## Benefits

1. **Increased Cognitive Demand:** Students must evaluate each option independently
2. **Reduced Guessing:** Much lower probability of guessing correct combination
3. **Partial Credit:** Recognizes partial understanding rather than all-or-nothing
4. **Progressive Difficulty:** More MCA questions at higher difficulty levels
5. **Better Assessment:** Distinguishes between complete and partial mastery

## Testing Recommendations

1. **Generate test quizzes** at each difficulty level to verify question type ratios
2. **Test scoring logic** with various MCA answer combinations
3. **Verify frontend rendering** for both MCQ and MCA questions
4. **Check partial credit calculation** in quiz results
5. **Test edge cases:** Empty selections, all wrong selections, etc.

## Future Enhancements

1. **Weighted Options:** Allow different point values for different correct answers
2. **Explanation Breakdown:** Show per-option explanations in results
3. **Analytics:** Track MCA vs MCQ performance separately
4. **Adaptive Difficulty:** Adjust MCA ratio based on user performance
5. **Question Bank:** Build library of high-quality MCA questions per topic

## Migration Notes

- **Backward Compatible:** Existing MCQ questions continue to work unchanged
- **No Database Migration Required:** Existing quiz results remain valid
- **Gradual Rollout:** New MCA questions will be generated as quizzes are created
- **Existing Quizzes:** Will continue to use MCQ format until regenerated

## Files Modified

### Backend
- `backend/app/models/adaptive_quiz.py`
- `backend/app/routers/quiz.py`

### Frontend
- `frontend/src/components/QuestionRenderer.jsx`
- `frontend/src/components/QuestionRenderer.css`
- `frontend/src/components/Quiz.jsx`

### Prompts
- `prompts/level_1_quiz_prompt.txt`
- `prompts/level_2_quiz_prompt.txt`
- `prompts/level_3_quiz_prompt.txt`
- `prompts/level_4_quiz_prompt.txt`

---

**Implementation Date:** November 5, 2025
**Status:** ✅ Complete

