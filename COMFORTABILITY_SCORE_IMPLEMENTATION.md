# Comfortability Score (CS) Implementation Summary

## Overview
This document summarizes the implementation of the Comfortability Score (CS) metric and the `question_next_level` recommendation system for flashcard performance tracking.

## What Was Implemented

### 1. Configuration (`backend/app/readiness_config.py`)
Added new configuration variables for CS thresholds:
- `CS_THRESHOLD_EASY_TO_MEDIUM = 1.5`
- `CS_THRESHOLD_MEDIUM_TO_HARD = 3.0`
- `CS_THRESHOLD_HARD_TO_BOSS = 4.0`

These thresholds determine the recommended next question difficulty level based on the user's CS.

### 2. Data Models (`backend/app/models/readiness_v2.py`)

#### Updated to Support Partial Credit:
- `PerformanceByLevel.points`: Changed to `float` to store partial credit points
- `RecentAttempt.points_earned`: Changed to `float` to support partial points (e.g., 1.5)
- `UserFlashcardPerformance.accuracy_score`: Changed to `float`
- `UserFlashcardPerformance.total_points_earned`: Changed to `float`
- `WeakFlashcard.accuracy_score`: Changed to `float`
- `RawScores.accuracy_total`: Changed to `float`
- `MaxPossibleScores.accuracy`: Changed to `float`

#### New Fields Added to `UserFlashcardPerformance`:
- `comfortability_score: float` - The calculated CS based on recent performance
- `question_next_level: str` - Recommended next difficulty level ('easy', 'medium', 'hard', or 'boss')

### 3. Service Layer (`backend/app/services/flashcard_performance_service.py`)

#### Updated Methods:
- `update_performance_from_quiz()`: Now calculates and stores CS and next level for each flashcard
- `_calculate_points_for_attempt()`: Enhanced to handle partial credit scores
- `_calculate_accuracy_score()`: Updated to use the new `points` field from `PerformanceByLevel`

#### New Methods:
- `_calculate_comfortability_score()`: Implements the CS formula
  - Formula: `Average points in last 3 attempts + max(2 - wrong answers in last 3, 0)`
  - Returns a float representing the user's comfort level with the flashcard

- `_determine_question_next_level()`: Determines recommended difficulty
  - CS < 1.5 → 'easy'
  - 1.5 ≤ CS < 3.0 → 'medium'
  - 3.0 ≤ CS < 4.0 → 'hard'
  - CS ≥ 4.0 → 'boss'

## How It Works

### Partial Credit Example
If a user answers a hard question (worth 3 points) and gets 1 out of 2 correct options:
- `partial_credit_score = 0.5`
- `points_earned = 3 * 0.5 = 1.5`

### Comfortability Score Calculation
For a flashcard with recent attempts earning: +1, +2, -1, +3, -2

Taking the last 3 attempts: -1, +3, -2
- Average points: (-1 + 3 - 2) / 3 = 0
- Wrong answers: 2 (the -1 and -2 attempts)
- Bonus: max(2 - 2, 0) = 0
- **CS = 0 + 0 = 0**
- **Recommended next level: 'easy'** (since CS < 1.5)

### Another Example
Last 3 attempts: +3, +3, +2
- Average points: (3 + 3 + 2) / 3 = 2.67
- Wrong answers: 0
- Bonus: max(2 - 0, 0) = 2
- **CS = 2.67 + 2 = 4.67**
- **Recommended next level: 'boss'** (since CS ≥ 4.0)

## Data Storage

Each `UserFlashcardPerformance` document now stores:
```json
{
  "user_id": "user-123",
  "flashcard_id": "SI_lec_1_15",
  "accuracy_score": 9.5,
  "total_points_earned": 9.5,
  "comfortability_score": 3.2,
  "question_next_level": "hard",
  "recent_attempts": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "hard",
      "is_correct": true,
      "points_earned": 3.0
    },
    {
      "timestamp": "2024-01-15T10:35:00Z",
      "level": "hard",
      "is_correct": false,
      "points_earned": -1.0
    }
  ],
  "performance_by_level": {
    "easy": {"attempts": 5, "correct": 4, "points": 4.0},
    "medium": {"attempts": 3, "correct": 3, "points": 6.0},
    "hard": {"attempts": 2, "correct": 1, "points": 2.0},
    "boss": {"attempts": 1, "correct": 0, "points": -2.0}
  }
}
```

## Benefits

1. **Partial Credit Support**: Accurately tracks performance on MCA questions where users can get partial points
2. **Dynamic Difficulty**: Automatically recommends the next appropriate difficulty level for each flashcard
3. **Recent Performance Focus**: CS emphasizes the last 3 attempts, making it responsive to learning progress
4. **Configurable Thresholds**: Easy to adjust CS thresholds via configuration without code changes
5. **Comprehensive Tracking**: Individual attempt points are stored for full transparency

## Usage

The system automatically calculates CS and `question_next_level` every time a quiz is submitted. Frontend applications can use the `question_next_level` field to:
- Show recommended difficulty for practice
- Filter flashcards by readiness level
- Create adaptive learning paths
- Display progress indicators

## Files Modified

1. `backend/app/readiness_config.py` - Added CS threshold configuration
2. `backend/app/models/readiness_v2.py` - Updated models for partial credit and added CS fields
3. `backend/app/services/flashcard_performance_service.py` - Implemented CS calculation and next level logic

## Backward Compatibility

All changes are backward compatible:
- Fields have default values
- `points_earned` defaults to 0.0 for old records
- Existing data will work without migration (though CS will be 0 until new attempts are recorded)

