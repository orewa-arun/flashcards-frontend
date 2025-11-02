/**
 * API functions for bookmarks management
 */

import { authenticatedPost, authenticatedDelete, authenticatedGet } from '../utils/authenticatedApi';

const API_ENDPOINT = '/api/v1/bookmarks';

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
    const data = await authenticatedPost(API_ENDPOINT, {
        course_id: courseId,
        deck_id: deckId,
        flashcard_index: index,
    });
    return data;
  } catch (error) {
    if (error.message.includes('409')) {
      throw new Error('Flashcard already bookmarked');
    }
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
    const data = await authenticatedDelete(API_ENDPOINT, {
        course_id: courseId,
        deck_id: deckId,
        flashcard_index: index,
    });
    return data;
  } catch (error) {
    if (error.message.includes('404')) {
      throw new Error('Bookmark not found');
    }
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
    const data = await authenticatedGet(API_ENDPOINT);
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
