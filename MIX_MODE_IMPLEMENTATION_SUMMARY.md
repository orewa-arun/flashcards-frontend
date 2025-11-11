# Mix Mode Implementation Summary

## Overview

Mix Mode is a new adaptive study session type that provides an intelligent, dynamic learning experience. It prioritizes important concepts, adapts to user performance in real-time, and provides immediate remediation when needed.

## Key Features

1. **Intelligent Prioritization**: Flashcards are presented in order of `relevance_score` (highest first)
2. **Adaptive Difficulty**: Question levels adapt based on the user's Comfortability Score (CS)
3. **Immediate Remediation**: Wrong answers trigger flashcard review + follow-up question
4. **Multi-Deck Support**: Can span multiple decks for comprehensive exam preparation
5. **Session Persistence**: Users can leave and resume their sessions
6. **No Question Repeats**: Questions are tracked to avoid repetition (with intelligent fallback)
7. **Round-Based Learning**: After covering all flashcards once, new rounds begin with adapted difficulty

## Architecture

### Data Models (`backend/app/models/mix_session.py`)

#### `MixSession`
Stores the state of an active mix mode session:
- `session_id`: Unique identifier
- `user_id`: Firebase UID
- `course_id` and `deck_ids`: Content scope
- `flashcard_master_order`: Flashcards sorted by relevance_score
- `activity_queue`: Dynamic queue of upcoming activities
- `seen_in_current_round`: Tracks progress within a round
- `asked_question_hashes`: Prevents question repetition
- `current_round`: Round counter
- `status`: "in_progress", "completed", or "abandoned"

#### `MixActivity`
Represents a single activity in the queue:
- `type`: "question" or "flashcard"
- `flashcard_id`: Associated flashcard
- `level`: Difficulty level (easy, medium, hard, boss)
- `is_follow_up`: Whether this is a remediation question

#### `UserQuestionPerformance`
Tracks last performance on each specific question:
- `user_id`: Firebase UID
- `question_content_hash`: Unique question identifier
- `flashcard_id` and `level`: Question metadata
- `is_correct`: Last attempt result
- `last_attempted`: Timestamp

### Service Layer (`backend/app/services/mix_session_service.py`)

#### `MixSessionService`

**Key Methods:**

1. **`start_session(user_id, course_id, deck_ids)`**
   - Loads flashcards from all specified decks
   - Sorts by `relevance_score` (highest first)
   - Generates initial Round 1 activity queue (all medium level)
   - Saves session to database
   - Returns `(session_id, total_flashcards)`

2. **`get_next_activity(session_id, user_id)`**
   - Pops next activity from queue
   - If queue empty and round complete → generates next round
   - If queue empty and round incomplete → session complete
   - Loads flashcard content or question data
   - Returns `MixActivityResponse` with progress info

3. **`submit_answer(session_id, user_id, flashcard_id, question_hash, level, user_answer, correct_answer, is_follow_up)`**
   - Grades answer (supports partial credit for MCA)
   - Calculates points earned
   - Updates `UserFlashcardPerformance` (triggers CS recalculation)
   - Updates `UserQuestionPerformance`
   - **If incorrect AND not a follow-up**: Injects remediation activities
   - Returns `MixAnswerResponse`

4. **`_inject_remediation(session_id, flashcard_id, user_id)`**
   - Fetches updated `question_next_level` from flashcard performance
   - Prepends two activities to queue:
     1. Flashcard review activity
     2. Follow-up question at `question_next_level`
   - **Critical**: Follow-up is marked `is_follow_up=True` to prevent loop

5. **`_generate_next_round(session)`**
   - Called when a round is complete
   - For each flashcard, fetches `question_next_level` from performance
   - Creates new activity queue with adapted levels
   - Resets `seen_in_current_round`
   - Increments `current_round`

6. **`_select_question_for_flashcard(course_id, flashcard_id, level, asked_question_hashes, user_id)`**
   - **3-Tier Fallback Logic**:
     - **Priority 1**: Return an unseen question at the target level
     - **Priority 2**: Return a previously *incorrect* question at that level
     - **Priority 3**: Return a random question at that level (all answered correctly)

**Helper Methods:**
- `_load_flashcards_for_deck()`: Loads flashcard JSON from file system
- `_load_flashcard_content()`: Loads specific flashcard data
- `_load_questions_for_level()`: Loads questions from quiz files (level 1-4)
- `_hash_question()`: Creates deterministic hash from question text
- `_grade_answer()`: Handles both MCQ and MCA, returns `(is_correct, partial_credit)`
- `_calculate_points()`: Calculates points using `readiness_config.ACCURACY_POINTS`

### API Endpoints (`backend/app/routers/mix_mode.py`)

#### `POST /mix/start`
**Request:**
```json
{
  "course_id": "MS5150",
  "deck_ids": ["SI_lec_1", "SI_lec_2"]
}
```

**Response:**
```json
{
  "session_id": "mix_abc123",
  "total_flashcards": 25
}
```

#### `GET /mix/session/{session_id}/next`
**Response (Question Activity):**
```json
{
  "activity_type": "question",
  "flashcard_id": "SI_lec_1_15",
  "question": { /* full question object */ },
  "level": "medium",
  "is_follow_up": false,
  "round_number": 1,
  "progress": {
    "seen_in_round": 5,
    "total_flashcards": 25,
    "current_round": 1
  }
}
```

**Response (Flashcard Activity):**
```json
{
  "activity_type": "flashcard",
  "flashcard_id": "SI_lec_1_15",
  "flashcard_content": { /* full flashcard object */ },
  "round_number": 1,
  "progress": { /* same as above */ }
}
```

**Response (Session Complete):**
```json
null
```

#### `POST /mix/session/{session_id}/answer`
**Request:**
```json
{
  "flashcard_id": "SI_lec_1_15",
  "question_hash": "abc123def456",
  "level": "medium",
  "user_answer": "A",
  "is_follow_up": false
}
```

**Response:**
```json
{
  "is_correct": true,
  "correct_answer": "A",
  "explanation": null,
  "points_earned": 2.0
}
```

#### `GET /mix/session/{session_id}/status`
**Response:**
```json
{
  "session_id": "mix_abc123",
  "status": "in_progress",
  "current_round": 1,
  "total_flashcards": 25,
  "seen_in_current_round": 5,
  "activities_remaining": 20,
  "created_at": "2025-11-10T10:00:00Z",
  "last_updated": "2025-11-10T10:15:00Z"
}
```

## Database Collections

### `mix_sessions`
Stores active and completed mix sessions.

**Indexes:**
- `session_id` (unique)
- `(user_id, status)` (compound)
- `user_id`
- `created_at`
- `last_updated`

### `user_question_performance`
Tracks user's last performance on each unique question.

**Indexes:**
- `(user_id, question_content_hash)` (unique, compound)
- `user_id`
- `flashcard_id`
- `last_attempted`

## Mix Mode Flow

### Round 1: Initial Coverage
1. User starts session with specific `course_id` and `deck_ids`
2. System loads all flashcards and sorts by `relevance_score`
3. Queue populated with medium-level questions for each flashcard
4. User answers questions sequentially
5. **If correct** (any points > 0): Move to next flashcard
6. **If incorrect**: 
   - Show flashcard for review
   - Show follow-up question at `question_next_level` (based on CS)
   - Follow-up does NOT trigger further remediation
7. Round complete when all flashcards seen once

### Round 2+: Adaptive Difficulty
1. System checks each flashcard's `question_next_level` (from CS)
2. Queue populated with questions at adapted levels
3. Same remediation logic applies
4. Rounds continue until user completes or abandons session

### Question Selection Priority
For each flashcard at a target level:
1. **First**: Show questions never asked in this session
2. **Then**: Show questions previously answered incorrectly
3. **Finally**: Randomly repeat questions (all answered correctly)

## Integration

### Files Modified
1. `backend/app/main.py`: Added `mix_mode` router import and inclusion
2. `backend/app/database_indexes.py`: Added indexes for new collections

### Files Created
1. `backend/app/models/mix_session.py`: All data models for Mix Mode
2. `backend/app/services/mix_session_service.py`: Core business logic
3. `backend/app/routers/mix_mode.py`: API endpoints

## Configuration

Mix Mode uses existing configuration from `backend/app/readiness_config.py`:

- `ACCURACY_POINTS`: Points awarded per level and correctness
- `CS_THRESHOLD_EASY_TO_MEDIUM`: CS threshold for level progression (1.5)
- `CS_THRESHOLD_MEDIUM_TO_HARD`: CS threshold (3.0)
- `CS_THRESHOLD_HARD_TO_BOSS`: CS threshold (4.0)

## Question Identification

Questions are identified using a **deterministic hash** of their `question_text`:
- Hash function: SHA-256 → first 16 characters
- Generated when questions are loaded
- Stored in `asked_question_hashes` to prevent repeats
- Stored in `user_question_performance` to track history

## Dependencies

Mix Mode integrates with existing systems:

1. **FlashcardPerformanceService**: Updates flashcard performance and CS
2. **AdaptiveQuizService**: Loads quiz questions from JSON files
3. **Firebase Auth**: User authentication via JWT tokens
4. **MongoDB**: Session and performance storage

## Empty State Handling

When a user has never attempted questions from a flashcard (CS = 0):
- Round 1 starts with **medium** level questions
- This provides a balanced starting point for adaptive learning

## Testing Recommendations

1. **Start Session**: Test with single deck and multiple decks
2. **Question Flow**: Verify correct priority ordering by relevance_score
3. **Remediation**: Test incorrect answer triggers flashcard + follow-up
4. **Follow-up Isolation**: Verify follow-up incorrect doesn't trigger more remediation
5. **Round Progression**: Test transition from Round 1 → Round 2 with adapted levels
6. **Question Selection**: Test all 3 priority tiers of question selection
7. **Partial Credit**: Test MCA questions with partial answers
8. **Session Persistence**: Test leaving and resuming sessions
9. **Empty States**: Test with flashcards user has never seen
10. **Multi-Deck Exams**: Test with decks from different lectures

## Notes

- All timestamps use UTC
- Session IDs use format: `mix_<16-character-hex>`
- Questions from files: `{deck_id}_level_{1-4}_quiz.json`
- Flashcards from files: `{deck_id}_cognitive_flashcards_only.json`
- Partial credit calculated as: `correct_selections / total_correct_answers`
- Points calculated using level-specific values from config

