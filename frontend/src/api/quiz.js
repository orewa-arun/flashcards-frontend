/**
 * Quiz API service for adaptive quiz generation and submission.
 */

import { authenticatedPost } from '../utils/authenticatedApi';

/**
 * Generate a new quiz for a specific course and deck.
 * @param {string} courseId - Course identifier (e.g., "MS5260")
 * @param {string} deckId - Deck identifier (e.g., "MIS_lec_4")
 * @param {number} numQuestions - Number of questions (default: 20)
 * @returns {Promise<Object>} Quiz generation response with questions
 */
export async function generateQuiz(courseId, deckId, numQuestions = 20) {
  try {
    const data = await authenticatedPost('/api/v1/quiz/generate', {
        course_id: courseId,
        deck_id: deckId,
        num_questions: numQuestions,
    });

    return data;
  } catch (error) {
    console.error('Error generating quiz:', error);
    throw error;
  }
}

/**
 * Submit quiz answers and get results.
 * @param {string} quizId - Quiz session ID
 * @param {string} courseId - Course identifier
 * @param {string} deckId - Deck identifier
 * @param {Array} answers - Array of {question_id, user_answer} objects
 * @param {number} timeTakenSeconds - Time taken to complete quiz
 * @returns {Promise<Object>} Quiz results with score and weak concepts
 */
export async function submitQuiz(quizId, courseId, deckId, answers, timeTakenSeconds) {
  try {
    const data = await authenticatedPost('/api/v1/quiz/submit', {
        quiz_id: quizId,
        course_id: courseId,
        deck_id: deckId,
        answers: answers,
        time_taken_seconds: timeTakenSeconds,
    });

    return data;
  } catch (error) {
    console.error('Error submitting quiz:', error);
    throw error;
  }
}

