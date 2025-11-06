/**
 * API service for adaptive quiz system
 */

import { authenticatedPost, authenticatedGet } from '../utils/authenticatedApi';

/**
 * Start a new adaptive quiz session
 * @param {string} courseId - Course identifier (e.g., "MS5150")
 * @param {string} lectureId - Lecture identifier (e.g., "SI_PLC")
 * @param {number} level - Difficulty level (1-4)
 * @param {number} size - Number of questions (default: 20)
 * @returns {Promise} Quiz session data with personalized questions
 */
export const startQuizSession = async (courseId, lectureId, level) => {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/start', {
      course_id: courseId,
      lecture_id: lectureId,
      level: level
    });
    console.log('✅ Quiz session started:', data);
    return data;
  } catch (error) {
    console.error('❌ Error starting quiz session:', error);
    throw error;
  }
};

/**
 * Submit an answer to a quiz question
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {string} questionHash - Unique question identifier
 * @param {string} flashcardId - Source flashcard ID
 * @param {boolean} isCorrect - Whether the answer was correct
 * @param {number} level - Quiz level
 * @returns {Promise} Submission confirmation
 */
export const submitQuizAnswer = async (courseId, lectureId, questionHash, flashcardId, isCorrect, level) => {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/submit', {
      course_id: courseId,
      lecture_id: lectureId,
      question_hash: questionHash,
      flashcard_id: flashcardId,
      is_correct: isCorrect,
      level: level
    });
    return data;
  } catch (error) {
    console.error('❌ Error submitting quiz answer:', error);
    throw error;
  }
};

/**
 * Complete a quiz session and save it to history
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {number} level - Difficulty level (1-4)
 * @param {number} score - Final score
 * @param {number} totalQuestions - Total number of questions
 * @param {number} timeTakenSeconds - Time taken in seconds
 * @param {Array} questionResults - Array of question result objects
 * @returns {Promise} Completion confirmation
 */
export const completeQuizSession = async (courseId, lectureId, level, score, totalQuestions, timeTakenSeconds, questionResults) => {
  try {
    const data = await authenticatedPost('/api/v1/adaptive-quiz/session/complete', {
      course_id: courseId,
      lecture_id: lectureId,
      level: level,
      score: score,
      total_questions: totalQuestions,
      time_taken_seconds: timeTakenSeconds,
      question_results: questionResults
    });
    console.log('✅ Quiz session completed and saved to history:', data);
    return data;
  } catch (error) {
    console.error('❌ Error completing quiz session:', error);
    throw error;
  }
};

/**
 * Get user's performance statistics for a lecture
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @returns {Promise} Performance data including weakness scores
 */
export const getUserPerformance = async (courseId, lectureId) => {
  try {
    const data = await authenticatedGet(`/api/v1/adaptive-quiz/performance/${courseId}/${lectureId}`);
    return data;
  } catch (error) {
    console.error('❌ Error fetching user performance:', error);
    throw error;
  }
};

