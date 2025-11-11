/**
 * API functions for flashcard feedback management
 */

import { authenticatedPost, authenticatedGet, authenticatedDelete } from '../utils/authenticatedApi';

/**
 * Submit feedback for a flashcard (like or dislike)
 * @param {Object} params - Feedback parameters
 * @param {string} params.sessionId - Current study session ID
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier
 * @param {number} params.index - Flashcard index
 * @param {number} params.rating - Rating (1 for like, -1 for dislike)
 * @returns {Promise<Object>} Feedback response
 */
export async function submitFeedback({ sessionId, courseId, deckId, index, rating }) {
  try {
    // Validate rating
    if (rating !== 1 && rating !== -1) {
      throw new Error('Rating must be 1 (like) or -1 (dislike)');
    }

    const payload = {
      session_id: sessionId || 'standalone', // Fallback to 'standalone' if no sessionId
      course_id: courseId,
      deck_id: deckId,
      flashcard_index: index,
      rating: rating,
    };
    
    console.log('📤 Submitting feedback:', payload);

    const data = await authenticatedPost('/api/v1/feedback', payload);

    return data;
  } catch (error) {
    console.error('Error submitting feedback:', error);
    throw error;
  }
}

/**
 * Like a flashcard
 * @param {Object} params - Flashcard parameters
 * @param {string} params.sessionId - Current study session ID
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier
 * @param {number} params.index - Flashcard index
 * @returns {Promise<Object>} Feedback response
 */
export async function likeFlashcard({ sessionId, courseId, deckId, index }) {
  return submitFeedback({ sessionId, courseId, deckId, index, rating: 1 });
}

/**
 * Dislike a flashcard
 * @param {Object} params - Flashcard parameters
 * @param {string} params.sessionId - Current study session ID
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier
 * @param {number} params.index - Flashcard index
 * @returns {Promise<Object>} Feedback response
 */
export async function dislikeFlashcard({ sessionId, courseId, deckId, index }) {
  return submitFeedback({ sessionId, courseId, deckId, index, rating: -1 });
}

/**
 * Get all feedback for the current user
 * @returns {Promise<Array>} Array of user feedback summaries
 */
export async function getUserFeedback() {
  try {
    const data = await authenticatedGet('/api/v1/feedback/user');
    return data;
  } catch (error) {
    console.error('Error getting user feedback:', error);
    throw error;
  }
}

/**
 * Clear/remove feedback for a flashcard
 * @param {Object} params - Flashcard parameters
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier
 * @param {number} params.index - Flashcard index
 * @returns {Promise<Object>} Success message
 */
export async function clearFeedback({ courseId, deckId, index }) {
  try {
    const data = await authenticatedDelete('/api/v1/feedback', {
      course_id: courseId,
      deck_id: deckId,
      flashcard_index: index,
      session_id: '', // Not needed for deletion
      rating: 0, // Not needed for deletion
    });
    return data;
  } catch (error) {
    console.error('Error clearing feedback:', error);
    throw error;
  }
}

/**
 * Get feedback status for a specific flashcard
 * @param {string} courseId - Course identifier
 * @param {string} deckId - Deck identifier
 * @param {number} index - Flashcard index
 * @returns {Promise<number|null>} Rating (1, -1, or null if no feedback)
 */
export async function getFlashcardFeedback(courseId, deckId, index) {
  try {
    const userFeedback = await getUserFeedback();
    const feedback = userFeedback.find(
      item =>
        item.course_id === courseId &&
        item.deck_id === deckId &&
        item.flashcard_index === index
    );
    return feedback ? feedback.rating : null;
  } catch (error) {
    console.error('Error getting flashcard feedback:', error);
    return null;
  }
}
