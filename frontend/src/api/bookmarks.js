/**
 * API functions for bookmarks management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/bookmarks`;

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
 * Add a bookmark for a flashcard
 * @param {Object} params - Bookmark parameters
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier  
 * @param {number} params.index - Flashcard index
 * @returns {Promise<Object>} Bookmark response
 */
export async function addBookmark({ courseId, deckId, index }) {
  try {
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': getUserId(),
      },
      body: JSON.stringify({
        course_id: courseId,
        deck_id: deckId,
        flashcard_index: index,
      }),
    });

    if (!response.ok) {
      if (response.status === 409) {
        throw new Error('Flashcard already bookmarked');
      }
      throw new Error(`Failed to add bookmark: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error adding bookmark:', error);
    throw error;
  }
}

/**
 * Remove a bookmark for a flashcard
 * @param {Object} params - Bookmark parameters
 * @param {string} params.courseId - Course identifier
 * @param {string} params.deckId - Deck identifier
 * @param {number} params.index - Flashcard index
 * @returns {Promise<Object>} Success message
 */
export async function removeBookmark({ courseId, deckId, index }) {
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
      }),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Bookmark not found');
      }
      throw new Error(`Failed to remove bookmark: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error removing bookmark:', error);
    throw error;
  }
}

/**
 * Get all bookmarks for the current user
 * @returns {Promise<Array>} Array of bookmark objects with flashcard data
 */
export async function getUserBookmarks() {
  try {
    const response = await fetch(API_ENDPOINT, {
      method: 'GET',
      headers: {
        'X-User-ID': getUserId(),
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get bookmarks: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting bookmarks:', error);
    throw error;
  }
}

/**
 * Check if a flashcard is bookmarked
 * @param {string} courseId - Course identifier
 * @param {string} deckId - Deck identifier
 * @param {number} index - Flashcard index
 * @returns {Promise<boolean>} True if bookmarked
 */
export async function isBookmarked(courseId, deckId, index) {
  try {
    const bookmarks = await getUserBookmarks();
    return bookmarks.some(
      bookmark =>
        bookmark.course_id === courseId &&
        bookmark.deck_id === deckId &&
        bookmark.flashcard_index === index
    );
  } catch (error) {
    console.error('Error checking bookmark status:', error);
    return false;
  }
}
