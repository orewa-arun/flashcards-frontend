# Exam Readiness Score Plan

## 1. Goal

To provide users with a clear, actionable, and relevant "Exam Readiness Score" that accurately reflects their preparedness, especially for short-term, high-intensity study sessions (e.g., cramming 48 hours before an exam).

The score is designed to be more insightful than a simple accuracy percentage by incorporating concept priority, depth of knowledge, and recent performance momentum.

## 2. Core Metrics

The final score is a composite of three core metrics:

### a. Coverage Score (40% Weight)

**Question:** "Have I seen the most important topics?"

- **Purpose:** Measures the breadth of knowledge, heavily prioritizing the concepts most likely to appear on an exam.
- **Calculation:**
  - This is a weighted percentage based on the `relevance_score` of each flashcard.
  - **Formula:**
    ```
    (Sum of relevance_scores of all seen concepts) / (Sum of relevance_scores of ALL concepts in the lecture) * 100
    ```
- **Example:** Covering a concept with a `relevance_score` of 0.9 contributes more to this score than covering one with a score of 0.3.

### b. Mastery Score (50% Weight)

**Question:** "How well do I understand the topics I've studied?"

- **Purpose:** Measures the depth of knowledge. It heavily rewards correct answers on higher-difficulty questions.
- **Calculation:**
  - A point system is used for questions answered for each concept (flashcard).
  - **Points System:**
    - Correct Level 1 (Easy): **+1 point**
    - Correct Level 2 (Medium): **+3 points**
    - Correct Level 3 (Hard): **+6 points**
    - Correct Level 4 (Boss): **+10 points**
    - *Incorrect answers will subtract a proportional number of points.*
  - **Formula:**
    ```
    (Total points earned across all concepts) / (Total points possible for concepts seen) * 100
    ```

### c. Recent Performance Score (10% Weight)

**Question:** "Am I improving or declining right now?"

- **Purpose:** Measures recent momentum to provide immediate feedback on the current study session's effectiveness.
- **Calculation:**
  - Compares the user's most recent quiz performance against their short-term average.
  - **Formula:**
    ```
    (Last quiz percentage * 0.7) + (Average percentage of last 3 quizzes * 0.3)
    ```
  - *Note: This score is normalized and adjusted for difficulty to ensure fairness.*

## 3. Final Calculation

The three core metrics are combined in a weighted average to produce the final Exam Readiness Score.

> **Final Score = (Coverage Score * 0.4) + (Mastery Score * 0.5) + (Recent Performance Score * 0.1)**

## 4. Readiness Status Levels

The final numerical score is mapped to a simple, qualitative status to give users an immediate understanding of where they stand.

-   **< 60%:** **Not Ready** (Focus on increasing concept coverage).
-   **60% - 79%:** **Getting There** (Coverage is improving, now focus on mastery).
-   **80% - 89%:** **Almost Ready** (Solid foundation, challenge yourself with harder quizzes).
-   **>= 90%:** **Exam Ready** (You've demonstrated broad, deep, and consistent knowledge).
