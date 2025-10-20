/**
 * API functions for flashcard feedback management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/feedback`;

/**
 * Get user ID from localStorage or generate a new one
 */
import { getUserId } from "../utils/userTracking";
// function getUserId() {
//   let userId = localStorage.getItem('userId');
//   if (!userId) {
//     userId = crypto.randomUUID();
//     localStorage.setItem('userId', userId);
//   }
//   return userId;
// }

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

    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': getUserId(),
      },
      body: JSON.stringify({
        session_id: sessionId,
        course_id: courseId,
        deck_id: deckId,
        flashcard_index: index,
        rating: rating,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to submit feedback: ${response.status}`);
    }

    const data = await response.json();
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
    const response = await fetch(`${API_ENDPOINT}/user`, {
      method: 'GET',
      headers: {
        'X-User-ID': getUserId(),
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get user feedback: ${response.status}`);
    }

    const data = await response.json();
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
    const response = await fetch(API_ENDPOINT, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': getUserId(),
      },
      body: JSON.stringify({
        course_id: courseId,
        deck_id: deckId,
        flashcard_index: index,
        session_id: '', // Not needed for deletion
        rating: 0, // Not needed for deletion
      }),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Feedback not found');
      }
      throw new Error(`Failed to clear feedback: ${response.status}`);
    }

    const data = await response.json();
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
