# Adaptive Quiz Engine - Implementation Summary

## Overview
We've successfully built a complete adaptive quiz engine that creates personalized quizzes based on user performance, implements checkpoint feedback, and provides detailed concept-level analytics.

## Architecture

### Backend Components

#### 1. Database Models (`backend/app/models/adaptive_quiz.py`)
- **ConceptPerformance**: Tracks individual concept metrics
  - Times attempted, correct, incorrect
  - Relevance score from flashcard
  - Last attempted timestamp
  - Auto-calculated accuracy percentage

- **UserDeckPerformance**: Overall performance for a user on a specific deck
  - Collection of concept performances
  - Total quiz attempts
  - Timestamps for creation and updates

- **Quiz Request/Response Models**:
  - `QuizGenerationRequest`: Request a new quiz
  - `QuizGenerationResponse`: Returns quiz questions
  - `QuizSubmissionRequest`: Submit answers
  - `QuizSubmissionResponse`: Returns results with weak concepts

#### 2. Quiz Router (`backend/app/routers/quiz.py`)
Provides two main endpoints:

**POST `/api/v1/quiz/generate`**
- Generates adaptive quiz based on user's history
- Phase 1 (First attempt): Selects questions from top relevance concepts
- Phase 3 (Subsequent attempts): Adaptive selection based on performance
  1. Priority: Concepts answered incorrectly (remediation)
  2. Priority: Concepts never seen (exploration)
  3. Priority: Concepts answered correctly (reinforcement - by relevance & low attempts)

**POST `/api/v1/quiz/submit`**
- Grades the quiz
- Updates concept-level performance tracking
- Identifies weak concepts (accuracy < 70% or multiple incorrect attempts)
- Returns detailed results with actionable feedback

#### 3. Quiz Size Logic
- If deck has < 15 concepts: 10-question quiz
- Otherwise: 20-question quiz
- User can override with `num_questions` parameter

### Frontend Components

#### 1. API Service (`frontend/src/api/quiz.js`)
- `generateQuiz()`: Fetches a new quiz from the backend
- `submitQuiz()`: Submits answers and gets results
- Handles user ID from localStorage

#### 2. QuizView Component (`frontend/src/views/QuizView.jsx`)
Complete quiz interface with:

**Question Types Supported:**
- Multiple Choice (MCQ)
- Scenario-based MCQ
- Sequencing (drag and drop to order)
- Categorization (assign items to categories)

**Features:**
- Real-time progress tracking
- Navigation between questions
- Checkpoint dialogs at questions 15 and 20
- Quiz results screen with concept weakness analysis
- Beautiful, responsive UI

**Sub-Components:**
- `SequencingQuestion`: Interactive drag-to-order interface
- `CategorizationQuestion`: Item-to-category assignment
- `CheckpointDialog`: Pause points with performance feedback
- `QuizResults`: Comprehensive results screen

#### 3. Checkpoint System
Automatically pauses the quiz at:
- Question 15
- Question 20

**Checkpoint Features:**
- Shows current score and accuracy
- If accuracy < 70%: Suggests reviewing flashcards
- If accuracy ≥ 70%: Encourages to continue
- Options: Continue Quiz or Review Flashcards

#### 4. Results Screen
Displays:
- Overall score (percentage and fraction)
- Time taken
- Quiz attempt number
- **Weak Concepts Section**: Shows concepts needing review with:
  - Concept name
  - Accuracy percentage
  - Times correct vs. attempted
  - Visual progress bar

## User Flow

1. **Complete Flashcard Deck** → "Start Quiz" button appears on last card
2. **Quiz Generation** → Backend creates personalized 20-question quiz
3. **Answer Questions** → User progresses through questions
4. **Checkpoint at Q15** → Pause for feedback and optional break
5. **Checkpoint at Q20** → Final checkpoint before completion (if quiz is longer)
6. **Submit Quiz** → Backend grades and updates performance
7. **View Results** → See score and weak concepts to review
8. **Take Again** → Next quiz adapts based on previous performance

## Adaptive Learning Logic

### First Quiz (Baseline)
```
Sort concepts by relevance_score (high to low)
Select top 20 concepts
Pick 1 random question from each concept
```

### Subsequent Quizzes (Adaptive)
```
Priority 1: Concepts with incorrect answers (remediation)
Priority 2: Concepts never attempted (exploration)
Priority 3: Concepts answered correctly (reinforcement)
  └─ Sorted by: relevance_score (desc), attempts (asc)

Fill quiz up to 20 questions from priority queue
```

## Database Collections

### `user_deck_performance`
Stores concept-level performance tracking:
```json
{
  "user_id": "uuid",
  "course_id": "MS5260",
  "deck_id": "MIS_lec_4",
  "total_concepts": 32,
  "concepts_performance": [
    {
      "concept_index": 0,
      "concept_context": "Core Database Concepts",
      "relevance_score": 10,
      "times_attempted": 3,
      "times_correct": 2,
      "times_incorrect": 1,
      "last_attempted": "2025-10-28T..."
    }
  ],
  "total_quiz_attempts": 5,
  "last_quiz_date": "2025-10-28T..."
}
```

### `quiz_sessions`
Stores active quiz sessions:
```json
{
  "quiz_id": "uuid",
  "user_id": "uuid",
  "course_id": "MS5260",
  "deck_id": "MIS_lec_4",
  "questions": [...],
  "created_at": "2025-10-28T...",
  "completed": false
}
```

## Testing the Implementation

### Backend Testing
1. Start the backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. Test quiz generation:
   ```bash
   curl -X POST http://localhost:8000/api/v1/quiz/generate \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test-user-123" \
     -d '{"course_id": "MS5260", "deck_id": "MIS_lec_4", "num_questions": 20}'
   ```

3. Test quiz submission:
   ```bash
   curl -X POST http://localhost:8000/api/v1/quiz/submit \
     -H "Content-Type: application/json" \
     -H "X-User-ID: test-user-123" \
     -d '{
       "quiz_id": "YOUR_QUIZ_ID",
       "course_id": "MS5260",
       "deck_id": "MIS_lec_4",
       "answers": [...],
       "time_taken_seconds": 300
     }'
   ```

### Frontend Testing
1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Navigate to a deck (e.g., http://localhost:5173/courses/MS5260/MIS_lec_4)
3. Complete the flashcards (or skip to the last one)
4. Click "Start Quiz"
5. Answer questions and observe:
   - Question navigation
   - Progress bar
   - Checkpoint at question 15
   - Results screen with weak concepts

### Integration Testing
1. Complete multiple quiz attempts for the same deck
2. Verify that:
   - First quiz uses top relevance concepts
   - Incorrect answers appear in next quiz
   - Performance tracking updates correctly
   - Weak concepts are identified accurately

## Configuration

### Backend Configuration
Update `backend/app/routers/quiz.py` if needed:
- `FLASHCARDS_BASE_PATH`: Path to cognitive flashcards
- Quiz size thresholds (currently 15 cards → 10 questions, else 20 questions)

### Frontend Configuration
Update `frontend/src/api/quiz.js`:
- `API_BASE_URL`: Backend API URL (default: http://localhost:8000)

## Key Features Implemented

✅ Adaptive quiz generation (Phase 1 & Phase 3)
✅ Concept-level performance tracking
✅ Multiple question types (MCQ, Scenario, Sequencing, Categorization)
✅ Checkpoint dialogs at Q15 and Q20
✅ Performance-based feedback
✅ Weak concept identification
✅ Beautiful, responsive UI
✅ Real-time progress tracking
✅ Quiz attempt numbering
✅ Persistent user tracking

## Future Enhancements (Optional)

1. **Confidence-Based Assessment**: Ask users how confident they are in their answers
2. **Immediate Feedback Mode**: Show correct answer after each question
3. **Topic-Focused Mini-Quizzes**: Allow drilling down on specific topics
4. **Spaced Repetition**: Schedule reviews based on forgetting curves
5. **Performance Analytics Dashboard**: Visualize progress over time
6. **Export Results**: Download quiz results as PDF
7. **Leaderboard**: Optional competitive element for motivated learners

## Notes

- The quiz engine automatically handles all question types from the cognitive flashcards
- Performance data persists across sessions
- The adaptive algorithm ensures comprehensive coverage before deep dives
- Checkpoints encourage optimal learning breaks based on performance
- The system is fully extensible for additional question types or quiz modes

