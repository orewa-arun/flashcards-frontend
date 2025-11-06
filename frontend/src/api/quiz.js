/**
 * Quiz API service for adaptive quiz generation and submission.
 * 
 * Uses the modern adaptive quiz system that properly updates:
 * - user_performance (for weak concepts tracking)
 * - quiz_results (for exam readiness and history)
 */

import { authenticatedPost } from '../utils/authenticatedApi';

/**
 * Start a new adaptive quiz session.
 * @param {string} courseId - Course identifier (e.g., "MS5260")
 * @param {string} lectureId - Lecture identifier (e.g., "MIS_lec_4")
 * @param {number} level - Difficulty level (1-4): 1=easy, 2=medium, 3=hard, 4=boss
 * @param {number} size - Number of questions (default: 20)
 * @returns {Promise<Object>} Quiz session with questions
 */
export async function startQuizSession(courseId, lectureId, level, size = 20) {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/start', {
      course_id: courseId,
      lecture_id: lectureId,
      level: level,
      size: size,
    });

    console.log('✅ Quiz session started:', data);
    return data;
  } catch (error) {
    console.error('❌ Error starting quiz session:', error);
    throw error;
  }
}

/**
 * Submit a single quiz answer (called after each question).
 * This updates the user_performance collection for weak concepts tracking.
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {string} questionHash - Unique hash for the question
 * @param {string} flashcardId - Source flashcard ID
 * @param {boolean} isCorrect - Whether the answer was correct
 * @param {number} level - Difficulty level
 * @returns {Promise<Object>} Submission confirmation
 */
export async function submitQuizAnswer(courseId, lectureId, questionHash, flashcardId, isCorrect, level) {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/submit', {
      course_id: courseId,
      lecture_id: lectureId,
      question_hash: questionHash,
      flashcard_id: flashcardId,
      is_correct: isCorrect,
      level: level,
    });

    return data;
  } catch (error) {
    console.error('❌ Error submitting quiz answer:', error);
    throw error;
  }
}

/**
 * Complete the quiz session and save to history.
 * This updates the quiz_results collection for exam readiness calculation.
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {number} level - Difficulty level
 * @param {number} score - Number of correct answers
 * @param {number} totalQuestions - Total number of questions
 * @param {number} timeTakenSeconds - Time taken to complete quiz
 * @param {Array} questionResults - Array of question result objects
 * @returns {Promise<Object>} Completion confirmation with result_id
 */
export async function completeQuizSession(courseId, lectureId, level, score, totalQuestions, timeTakenSeconds, questionResults) {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/complete', {
      course_id: courseId,
      lecture_id: lectureId,
      level: level,
      score: score,
      total_questions: totalQuestions,
      time_taken_seconds: timeTakenSeconds,
      question_results: questionResults,
    });

    console.log('✅ Quiz session completed and saved to history:', data);
    return data;
  } catch (error) {
    console.error('❌ Error completing quiz session:', error);
    throw error;
  }
}

// ============================================================================
// LEGACY API (Old Quiz System - Deprecated)
// ============================================================================
// These functions are kept for backwards compatibility but should not be used
// for new code. They do NOT update user_performance, so weak concepts won't work.

/**
 * @deprecated Use startQuizSession() instead
 */
export async function generateQuiz(courseId, deckId, numQuestions = 20, difficulty = 'medium') {
  console.warn('⚠️ generateQuiz() is deprecated. Use startQuizSession() instead.');
  try {
    const data = await authenticatedPost('/api/v1/quiz/generate', {
        course_id: courseId,
        deck_id: deckId,
        num_questions: numQuestions,
        difficulty: difficulty,
    });

    return data;
  } catch (error) {
    console.error('Error generating quiz:', error);
    throw error;
  }
}

/**
 * @deprecated Use submitQuizAnswer() + completeQuizSession() instead
 */
export async function submitQuiz(quizId, courseId, deckId, difficulty, answers, timeTakenSeconds) {
  console.warn('⚠️ submitQuiz() is deprecated. Use submitQuizAnswer() + completeQuizSession() instead.');
  try {
    const data = await authenticatedPost('/api/v1/quiz/submit', {
        quiz_id: quizId,
        course_id: courseId,
        deck_id: deckId,
        difficulty: difficulty,
        answers: answers,
        time_taken_seconds: timeTakenSeconds,
    });

    return data;
  } catch (error) {
    console.error('Error submitting quiz:', error);
    throw error;
  }
}

