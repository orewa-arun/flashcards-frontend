/**
 * API functions for quiz history management
 */

import { authenticatedGet } from '../utils/authenticatedApi';

const API_ENDPOINT = '/api/v1/quiz-history';

/**
 * Get quiz history summary for the current user
 * @returns {Promise<Array>} Array of deck summaries with highest scores
 */
export async function getQuizHistory() {
  try {
    const data = await authenticatedGet(API_ENDPOINT);
    return data;
  } catch (error) {
    console.error('Error getting quiz history:', error);
    throw error;
  }
}

/**
 * Get all quiz attempts for a specific deck
 * @param {string} deckId - Deck identifier
 * @returns {Promise<Array>} Array of quiz attempt summaries
 */
export async function getQuizHistoryByDeck(deckId) {
  try {
    const data = await authenticatedGet(`${API_ENDPOINT}/${deckId}`);
    return data;
  } catch (error) {
    console.error('Error getting quiz attempts for deck:', error);
    throw error;
  }
}

/**
 * Get detailed results for a specific quiz attempt
 * @param {string} resultId - Quiz result ID
 * @returns {Promise<Object>} Detailed quiz attempt results
 */
export async function getQuizAttemptDetails(resultId) {
  try {
    const data = await authenticatedGet(`${API_ENDPOINT}/attempt/${resultId}`);
    return data;
  } catch (error) {
    if (error.message.includes('404')) {
      throw new Error('Quiz attempt not found');
    }
    console.error('Error getting quiz attempt details:', error);
    throw error;
  }
}

/**
 * Get the highest score for a specific deck
 * @param {string} deckId - Deck identifier
 * @returns {Promise<number>} Highest percentage score for the deck
 */
export async function getHighestScore(deckId) {
  try {
    const history = await getQuizHistory();
    const deckHistory = history.find(deck => deck.deck_id === deckId);
    return deckHistory ? deckHistory.highest_percentage : 0;
  } catch (error) {
    console.error('Error getting highest score:', error);
    return 0;
  }
}

/**
 * Get the total number of quiz attempts for a user
 * @returns {Promise<number>} Total number of quiz attempts
 */
export async function getTotalQuizAttempts() {
  try {
    const history = await getQuizHistory();
    return history.reduce((total, deck) => total + deck.attempt_count, 0);
  } catch (error) {
    console.error('Error getting total quiz attempts:', error);
    return 0;
  }
}

/**
 * Get recent quiz attempts across all decks (limited number)
 * @param {number} limit - Maximum number of recent attempts to return
 * @returns {Promise<Array>} Array of recent quiz attempts
 */
export async function getRecentQuizAttempts(limit = 5) {
  try {
    const history = await getQuizHistory();
    
    // Get all attempts for all decks and flatten them
    const allAttemptsPromises = history.map(deck => 
      getQuizHistoryByDeck(deck.deck_id).then(attempts => 
        attempts.map(attempt => ({
          ...attempt,
          course_id: deck.course_id,
          deck_id: deck.deck_id
        }))
      )
    );
    
    const allAttempts = (await Promise.all(allAttemptsPromises)).flat();
    
    // Sort by completion date (most recent first) and limit
    allAttempts.sort((a, b) => new Date(b.completed_at) - new Date(a.completed_at));
    
    return allAttempts.slice(0, limit);
  } catch (error) {
    console.error('Error getting recent quiz attempts:', error);
    return [];
  }
}
