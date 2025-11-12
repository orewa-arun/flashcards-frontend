"""
Exam Readiness Engine V2 Configuration

This file centralizes all parameters for the persistent,
flashcard-centric exam readiness calculation system.
"""

from typing import Dict, List

# ===================================================================
# FINAL SCORE WEIGHTS
# ===================================================================
# The weighted contribution of each pillar to the final score.
# MUST sum to 1.0
FINAL_SCORE_WEIGHTS: Dict[str, float] = {
    "coverage": 0.35,
    "accuracy": 0.45,
    "momentum": 0.20,
}

# ===================================================================
# COVERAGE PILLAR
# ===================================================================
# Points awarded for attempting a question of a certain difficulty.
# This rewards exposure to concepts.
COVERAGE_POINTS: Dict[str, float] = {
    "easy": 0.3,
    "medium": 0.5,
    "hard": 0.75,
    "boss": 1.0,
}

# The maximum number of coverage points a user can accumulate
# for a single flashcard. This prevents "farming" one concept.
MAX_COVERAGE_POINTS_PER_FLASHCARD: float = 2.0

# ===================================================================
# ACCURACY PILLAR
# ===================================================================
# Points awarded (or subtracted) for getting a question
# correct or incorrect.
# 
# NOTE: The "incorrect" values are used ONLY for momentum calculation,
# making it engagement-based (same points for any attempt at a given level).
# The accuracy pillar still differentiates between correct/incorrect
# using the accuracy_score field calculated separately.
ACCURACY_POINTS: Dict[str, Dict[str, int]] = {
    "easy":   {"correct": 1, "incorrect": 0},
    "medium": {"correct": 2, "incorrect": 0},
    "hard":   {"correct": 3, "incorrect": -1},
    "boss":   {"correct": 4, "incorrect": -2},
}

# ===================================================================
# MOMENTUM PILLAR
# ===================================================================
# Configuration for the time-decay calculation.
MOMENTUM_HALF_LIFE_DAYS: float = 7.0

# The number of recent attempts to store per flashcard for
# calculating the momentum score.
MOMENTUM_RECENT_ATTEMPTS_LIMIT: int = 20

# ===================================================================
# NORMALIZATION
# ===================================================================
# Estimated number of available questions per flashcard for each difficulty level.
# This is used to calculate the maximum possible accuracy score for normalization.
# NOTE: This is a critical assumption based on how the quiz generator creates questions.
ESTIMATED_QUESTIONS_PER_FLASHCARD: Dict[str, int] = {
    "easy": 2,
    "medium": 2,
    "hard": 2,
    "boss": 1,
}

# ===================================================================
# WEAK FLASHCARD DETECTION
# ===================================================================
# A flashcard is marked 'weak' if any question is answered incorrectly.
# To be marked as 'not weak' again, the user's cumulative accuracy_score
# for that flashcard must reach this positive threshold.
WEAK_FLASHCARD_RECOVERY_THRESHOLD: int = 2

# Minimum number of attempts required before a flashcard
# can be considered "weak". Prevents flagging flashcards
# the user hasn't practiced enough.
MIN_ATTEMPTS_FOR_WEAK_DETECTION: int = 1

# ===================================================================
# COMFORTABILITY SCORE & NEXT LEVEL DETERMINATION
# ===================================================================
# Thresholds for determining the next recommended question level
# based on the user's Comfortability Score (CS).
# CS = Average points in last 3 attempts + max(2 - wrong answers in last 3, 0)
CS_THRESHOLD_EASY_TO_MEDIUM: float = 1.5
CS_THRESHOLD_MEDIUM_TO_HARD: float = 2.5
CS_THRESHOLD_HARD_TO_BOSS: float = 4.5

# ===================================================================
# DYNAMIC FEEDBACK & RECOMMENDATION MESSAGES
# ===================================================================
 
# --- POST-QUIZ FEEDBACK ---
# Triggered immediately after a quiz is submitted.
# Based on the score percentage and difficulty of that single quiz.

POST_QUIZ_FEEDBACK = {
    # === High Performance (Score > 90%) ===
    "high_performance": {
        "messages": [
            "Incredible performance on that {difficulty} quiz! You're building some serious momentum. Ready to take on a {next_difficulty} challenge?",
            "Flawless victory! You've clearly mastered these concepts at the {difficulty} level. Time to test your skills on {next_difficulty} mode!",
            "Absolutely crushed it! That's a top-tier score for a {difficulty} quiz. Let's see how you do on {next_difficulty}!",
        ],
        # Special message for acing the highest difficulty
        "boss_level_mastery": "You've conquered the boss level. You're in the top tier of students for this topic. Keep practicing to maintain this peak performance!"
    },

    # === Good Performance (Score 70-89%) ===
    "good_performance": {
        "messages": [
            "Solid performance! You have a strong handle on this. Take a moment to review the {num_weak_concepts} concept(s) you missed before your next session.",
            "Nice work! You're very close to mastering this. The concepts you stumbled on are tricky; a quick flashcard review on those will make a huge difference.",
            "Great job! You answered most questions correctly. The few you missed are now marked as 'weak'. Let's focus on redeeming them in your next quiz.",
        ]
    },

    # === Average Performance (Score 50-69%) ===
    "average_performance": {
        "messages": [
            "Good effort. This is a tough topic. The concepts you missed are crucial building blocks. We've marked them as 'weak' for you to focus on.",
            "You're making progress! Every mistake is a learning opportunity. Let's solidify your understanding by reviewing the flashcards for the topics you found challenging.",
            "Okay, we've got a baseline. Now you know exactly which concepts to target. Review your {num_weak_concepts} weak flashcards, and you'll see a big jump in your next score.",
        ]
    },

    # === Low Performance (Score < 50%) ===
    "low_performance": {
        "messages": [
            "No worries, this is one of the hardest topics. The best move now is to go back to the flashcards for this lecture. Focus on understanding the core ideas before trying another quiz.",
            "Okay, this quiz revealed some key areas for us to work on. Let's not focus on the score, but on the opportunity. Head to the flashcards to build a stronger foundation.",
            "This is part of the learning process! The most effective students are the ones who analyze their mistakes. We've identified your weak concepts—let's review them thoroughly.",
        ]
    }
}

# --- READINESS DASHBOARD FEEDBACK ---
# Triggered when a user views their overall Exam Readiness.
# Based on their weakest aggregated pillar (Coverage, Accuracy, or Momentum).

READINESS_DASHBOARD_FEEDBACK = {
    # === Weakest Pillar: COVERAGE ===
    # User has low score because they haven't seen enough material.
    "weak_coverage": {
        "headline": "Broaden Your Knowledge",
        "messages": [
            "Your top priority is to cover more ground. You have several lectures you haven't been quizzed on yet. Let's tackle a new topic to build your knowledge base.",
            "You're doing well on the topics you've studied, but you're missing some key areas. Focus on taking quizzes from your 'uncovered' lectures.",
            "There are concepts in this exam you haven't seen yet. The fastest way to boost your score is to take a quiz on a lecture you haven't touched.",
        ]
    },

    # === Weakest Pillar: ACCURACY ===
    # User has seen the material but struggles with correctness.
    "weak_accuracy": {
        "headline": "Deepen Your Understanding",
        "messages": [
            "You've covered the material, now it's time for mastery. Your accuracy is the key area for improvement. Dive into your 'Weak Concepts' and focus on redeeming those flashcards.",
            "Your foundation is broad, but not yet deep enough. Let's target the specific concepts you're struggling with. Work on turning those weak concepts into strengths!",
            "Knowledge gaps in a few key areas are holding your score back. The most effective use of your time right now is to review your identified weak flashcards and retake a quiz on them.",
        ]
    },

    # === Weakest Pillar: MOMENTUM ===
    # User's recent performance is trending downwards.
    "weak_momentum": {
        "headline": "Regain Your Momentum",
        "messages": [
            "Your recent performance has dipped. It happens! The best way to get back on track is with consistent practice. Let's do a quick quiz session to get your confidence back up.",
            "You've been a bit cold recently. Let's get a quick win to rebuild your momentum. A mixed review quiz on your stronger topics can help sharpen your skills.",
            "Consistency is key. You understand the material, but let's shake off the rust. A practice session now will help solidify your knowledge for exam day.",
        ]
    },

    # === All Pillars Strong: MAINTENANCE ===
    # User is in great shape and just needs to stay sharp.
    "maintenance": {
        "headline": "You're Exam Ready!",
        "messages": [
            "You're in the zone! Your knowledge is broad, deep, and consistent. The goal now is to stay sharp. Challenge yourself with a 'hard' or 'boss' level quiz to maintain your edge.",
            "Excellent work. You are on track for a great result. Keep the engine warm with a practice session every couple of days to ensure you hold onto this peak performance.",
            "You've demonstrated true mastery. To lock in this knowledge, continue to challenge yourself with the hardest questions available. Don't let your skills fade!",
        ]
    }
}

# ===================================================================
# DIFFICULTY LEVEL MAPPING
# ===================================================================
# Maps various difficulty representations to standardized levels
DIFFICULTY_LEVEL_MAP: Dict[str, str] = {
    "easy": "easy",
    "medium": "medium",
    "hard": "hard",
    "boss": "boss",
    "level_1": "easy",
    "level_2": "medium",
    "level_3": "hard",
    "level_4": "boss",
}

# Next difficulty suggestions for progression
NEXT_DIFFICULTY_MAP: Dict[str, str] = {
    "easy": "medium",
    "medium": "hard",
    "hard": "boss",
    "boss": "boss",  # Already at max
}

