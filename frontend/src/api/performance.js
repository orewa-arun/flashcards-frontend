/**
 * API service for user performance tracking
 */

import { authenticatedGet } from '../utils/authenticatedApi';

/**
 * Fetches the user's weak flashcards.
 * These are flashcards where performance is below a certain threshold.
 * @returns {Promise<Array>} A promise that resolves to an array of weak flashcard performance objects.
 */
export const getWeakFlashcards = async () => {
  try {
    const data = await authenticatedGet('/api/v1/performance/weak-flashcards');
    return data;
  } catch (error) {
    console.error('Error fetching weak flashcards:', error);
    throw error;
  }
};
