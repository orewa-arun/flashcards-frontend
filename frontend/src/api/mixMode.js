/**
 * API service for Mix Mode adaptive study sessions
 */

import { authenticatedPost, authenticatedGet } from '../utils/authenticatedApi';

/**
 * Start a new Mix Mode session
 * @param {string} courseId - Course identifier (e.g., "MS5150")
 * @param {Array<string>} deckIds - Array of deck/lecture identifiers (e.g., ["SI_lec_1", "SI_lec_2"])
 * @returns {Promise} Session data with session_id and total_flashcards
 */
export const startMixSession = async (courseId, deckIds) => {
  try {
    const data = await authenticatedPost('/mix/start', {
      course_id: courseId,
      deck_ids: deckIds
    });
    console.log('✅ Mix session started:', data);
    return data;
  } catch (error) {
    console.error('❌ Error starting mix session:', error);
    throw error;
  }
};

/**
 * Get an existing Mix Mode session by ID
 * @param {string} sessionId - The session identifier
 * @returns {Promise} Session data with status, progress, and metadata
 */
export const getMixSession = async (sessionId) => {
  try {
    const data = await authenticatedGet(`/mix/session/${sessionId}`);
    console.log('✅ Mix session retrieved:', data);
    return data;
  } catch (error) {
    console.error('❌ Error retrieving mix session:', error);
    throw error;
  }
};

/**
 * Get the next activity in the Mix Mode session
 * @param {string} sessionId - The session identifier
 * @returns {Promise} Activity data (question or flashcard) with progress info, or null if complete
 */
export const getNextActivity = async (sessionId) => {
  try {
    const data = await authenticatedGet(`/mix/session/${sessionId}/next`);
    console.log('✅ Next activity fetched:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching next activity:', error);
    throw error;
  }
};

/**
 * Submit an answer for a question in Mix Mode
 * @param {string} sessionId - The session identifier
 * @param {Object} answerData - Answer submission data
 * @param {string} answerData.flashcard_id - The flashcard ID
 * @param {string} answerData.question_hash - Hash of the question
 * @param {string} answerData.level - Question difficulty level
 * @param {string|Array<string>} answerData.user_answer - User's answer
 * @param {boolean} answerData.is_follow_up - Whether this was a follow-up question
 * @returns {Promise} Grading results with is_correct, correct_answer, and points_earned
 */
export const submitMixAnswer = async (sessionId, answerData) => {
  try {
    const data = await authenticatedPost(`/mix/session/${sessionId}/answer`, answerData);
    console.log('✅ Answer submitted:', data);
    return data;
  } catch (error) {
    console.error('❌ Error submitting answer:', error);
    throw error;
  }
};

/**
 * Reveal the answer to a question without recording performance
 * @param {string} sessionId - The session identifier
 * @param {Object} revealData - Reveal request data
 * @param {string} revealData.flashcard_id - The flashcard ID
 * @param {string} revealData.question_hash - Hash of the question
 * @param {string} revealData.level - Question difficulty level
 * @param {boolean} revealData.is_follow_up - Whether this was a follow-up question
 * @returns {Promise} Reveal response with correct_answer, explanation, and remediation_injected
 */
export const revealMixAnswer = async (sessionId, revealData) => {
  try {
    const data = await authenticatedPost(`/mix/session/${sessionId}/reveal`, revealData);
    console.log('✅ Answer revealed:', data);
    return data;
  } catch (error) {
    console.error('❌ Error revealing answer:', error);
    throw error;
  }
};

/**
 * Get the current status of a Mix Mode session
 * @param {string} sessionId - The session identifier
 * @returns {Promise} Session status and progress information
 */
export const getMixSessionStatus = async (sessionId) => {
  try {
    const data = await authenticatedGet(`/mix/session/${sessionId}/status`);
    console.log('✅ Session status fetched:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching session status:', error);
    throw error;
  }
};

/**
 * Get exam readiness score for one or more decks
 * @param {string} courseId - Course identifier (e.g., "MS5150")
 * @param {Array<string>} deckIds - Array of deck/lecture identifiers (e.g., ["SI_lec_1"])
 * @param {boolean} forceRefresh - Force recalculation, bypassing cache (default: false)
 * @returns {Promise} Exam readiness data with overall score and Trinity breakdown
 */
export const getDeckExamReadiness = async (courseId, deckIds, forceRefresh = false) => {
  try {
    const data = await authenticatedPost('/mix/deck-readiness', {
      course_id: courseId,
      deck_ids: deckIds,
      force_refresh: forceRefresh
    });
    console.log('✅ Deck exam readiness fetched:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching deck exam readiness:', error);
    throw error;
  }
};

/**
 * Get flashcard content for reference during a question
 * @param {string} courseId - Course identifier (e.g., "MS5150")
 * @param {string} flashcardId - Flashcard identifier (e.g., "SI_lec_1_15")
 * @returns {Promise} Full flashcard content with front, back, diagrams, etc.
 */
export const getFlashcardReference = async (courseId, flashcardId) => {
  try {
    const data = await authenticatedGet(`/mix/flashcard/${courseId}/${flashcardId}`);
    console.log('✅ Flashcard reference fetched:', data);
    return data;
  } catch (error) {
    console.error('❌ Error fetching flashcard reference:', error);
    throw error;
  }
};

export default {
  startMixSession,
  getMixSession,
  getNextActivity,
  submitMixAnswer,
  revealMixAnswer,
  getMixSessionStatus,
  getDeckExamReadiness,
  getFlashcardReference,
};

