/**
 * Analytics API client for tracking user progress and quiz results
 */

import axios from 'axios';
import { getUserId, isAnalyticsEnabled } from '../utils/userTracking';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/analytics`;
  

// Create axios instance for analytics API
const analyticsAPI = axios.create({
  baseURL: API_ENDPOINT,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add user ID header
analyticsAPI.interceptors.request.use(
  (config) => {
    // Only add user ID if analytics is enabled
    if (isAnalyticsEnabled()) {
      const userId = getUserId();
      if (userId) {
        config.headers['X-User-ID'] = userId;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
analyticsAPI.interceptors.response.use(
  (response) => response,
  (error) => {
    console.warn('Analytics API error:', error.message);
    // Don't throw errors for analytics - fail silently
    return Promise.resolve({ data: null, error: error.message });
  }
);

/**
 * Update deck study progress
 * @param {Object} progressData - Progress information
 * @param {string} progressData.deckId - Deck identifier
 * @param {string} progressData.courseId - Course identifier  
 * @param {number} progressData.progress - Progress as float 0.0 to 1.0
 * @param {number} progressData.cardsStudied - Number of cards studied
 * @param {number} progressData.totalCards - Total cards in deck
 */
export async function trackProgress(progressData) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping progress tracking');
    return;
  }

  try {
    const response = await analyticsAPI.post('/progress', {
      deck_id: progressData.deckId,
      course_id: progressData.courseId,
      progress: progressData.progress,
      cards_studied: progressData.cardsStudied,
      total_cards: progressData.totalCards,
    });
    
    console.log('Progress tracked:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to track progress:', error);
  }
}

/**
 * Submit quiz results
 * @param {Object} quizData - Quiz result information
 * @param {string} quizData.deckId - Deck identifier
 * @param {string} quizData.courseId - Course identifier
 * @param {number} quizData.score - Number of correct answers
 * @param {number} quizData.totalQuestions - Total questions in quiz
 * @param {number} quizData.timeTaken - Time taken in seconds
 * @param {Array} quizData.questionResults - Detailed question results (optional)
 */
export async function trackQuizResult(quizData) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping quiz result tracking');
    return;
  }

  try {
    const response = await analyticsAPI.post('/quiz-result', {
      deck_id: quizData.deckId,
      course_id: quizData.courseId,
      score: quizData.score,
      total_questions: quizData.totalQuestions,
      time_taken: quizData.timeTaken,
      question_results: quizData.questionResults || [],
    });
    
    console.log('Quiz result tracked:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to track quiz result:', error);
  }
}

/**
 * Get user summary statistics
 * @param {string} userId - User ID (optional, uses current user if not provided)
 */
export async function getUserSummary(userId = null) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping user summary request');
    return null;
  }

  try {
    const targetUserId = userId || getUserId();
    const response = await analyticsAPI.get(`/user/${targetUserId}`);
    
    console.log('User summary retrieved:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to get user summary:', error);
    return null;
  }
}

/**
 * Health check for analytics API
 */
export async function checkAnalyticsHealth() {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
    console.log('Analytics API health:', response.data);
    return response.data.status === 'healthy';
  } catch (error) {
    console.warn('Analytics API health check failed:', error.message);
    return false;
  }
}

// =============================================================================
// SESSION TRACKING API
// =============================================================================

/**
 * Start a new study session
 * @param {Object} sessionData - Session information
 * @param {string} sessionData.courseId - Course identifier
 * @param {string} sessionData.deckId - Deck identifier
 * @returns {Promise<Object>} Session response with session_id
 */
export async function startStudySession(sessionData) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping session start');
    return { session_id: 'disabled' };
  }

  try {
    const response = await analyticsAPI.post('/session/start', {
      course_id: sessionData.courseId,
      deck_id: sessionData.deckId,
    });
    
    console.log('Study session started:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to start study session:', error);
    return { session_id: 'error', error: error.message };
  }
}

/**
 * Update a study session with duration or quiz data
 * @param {Object} updateData - Update information
 * @param {string} updateData.sessionId - Session identifier
 * @param {number} [updateData.studyDurationSeconds] - Study duration in seconds
 * @param {Object} [updateData.quizData] - Quiz result data
 * @param {boolean} [updateData.isCompleted] - Mark session as completed
 * @returns {Promise<Object>} Updated session data
 */
export async function updateStudySession(updateData) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping session update');
    return;
  }

  try {
    const payload = {
      session_id: updateData.sessionId,
    };

    // Add study duration if provided
    if (updateData.studyDurationSeconds !== undefined) {
      payload.study_duration_seconds = updateData.studyDurationSeconds;
    }

    // Add quiz data if provided
    if (updateData.quizData) {
      payload.quiz_data = {
        quiz_duration_seconds: updateData.quizData.timeTaken,
        score: updateData.quizData.score,
        total_questions: updateData.quizData.totalQuestions,
        question_results: updateData.quizData.questionResults || [],
      };
    }

    // Add completion status if provided
    if (updateData.isCompleted !== undefined) {
      payload.is_completed = updateData.isCompleted;
    }

    const response = await analyticsAPI.post('/session/update', payload);
    
    console.log('Study session updated:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to update study session:', error);
    return null;
  }
}

/**
 * Get complete session summary
 * @param {string} sessionId - Session identifier
 * @returns {Promise<Object>} Complete session data
 */
export async function getSessionSummary(sessionId) {
  if (!isAnalyticsEnabled()) {
    console.log('Analytics disabled, skipping session summary');
    return null;
  }

  try {
    const response = await analyticsAPI.get(`/session/${sessionId}`);
    
    console.log('Session summary retrieved:', response.data);
    return response.data;
  } catch (error) {
    console.warn('Failed to get session summary:', error);
    return null;
  }
}

/**
 * Extract course and deck IDs from URL parameters
 * @param {Object} params - URL parameters
 * @returns {Object} Extracted IDs
 */
export function extractCourseInfo(params) {
  return {
    courseId: params.courseId || 'unknown',
    deckId: params.lectureId || 'unknown',
  };
}
