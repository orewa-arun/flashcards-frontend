/**
 * API Service for Weak Concepts
 */
import { authenticatedGet } from '../utils/authenticatedApi';

/**
 * Get weak concepts across all lectures in a course
 * @param {string} courseId - Course identifier
 * @returns {Promise<Object>} Weak concepts data
 */
export const getWeakConcepts = async (courseId) => {
  try {
    // Corrected path to adaptive-quiz router prefix
    const data = await authenticatedGet(`/api/v1/adaptive-quiz/weak-concepts/${courseId}`);
    return data;
  } catch (error) {
    console.error('Failed to fetch weak concepts:', error);
    throw error;
  }
};

