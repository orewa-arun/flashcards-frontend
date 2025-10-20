/**
 * API functions for admin analytics (no authentication required)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/admin-analytics`;

/**
 * Get analytics overview with high-level statistics
 * @returns {Promise<Object>} Overview statistics
 */
export async function getAnalyticsOverview() {
  try {
    const response = await fetch(`${API_ENDPOINT}/overview`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get analytics overview: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting analytics overview:', error);
    throw error;
  }
}

/**
 * Get all study sessions with details
 * @returns {Promise<Array>} Array of all study sessions
 */
export async function getAllSessions() {
  try {
    const response = await fetch(`${API_ENDPOINT}/sessions`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get all sessions: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting all sessions:', error);
    throw error;
  }
}

/**
 * Get quiz performance summary by deck
 * @returns {Promise<Array>} Array of quiz performance statistics by deck
 */
export async function getQuizPerformanceSummary() {
  try {
    const response = await fetch(`${API_ENDPOINT}/quiz-results`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get quiz performance summary: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting quiz performance summary:', error);
    throw error;
  }
}

/**
 * Get flashcard feedback summary with like/dislike counts
 * @returns {Promise<Array>} Array of flashcard feedback statistics
 */
export async function getFlashcardFeedbackSummary() {
  try {
    const response = await fetch(`${API_ENDPOINT}/flashcard-feedback/summary`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get flashcard feedback summary: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting flashcard feedback summary:', error);
    throw error;
  }
}

/**
 * Get detailed flashcard feedback log
 * @returns {Promise<Array>} Array of individual feedback entries
 */
export async function getFlashcardFeedbackDetails() {
  try {
    const response = await fetch(`${API_ENDPOINT}/flashcard-feedback/details`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get flashcard feedback details: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting flashcard feedback details:', error);
    throw error;
  }
}

/**
 * Get all users summary with activity stats
 * @returns {Promise<Array>} Array of all user summaries
 */
export async function getAllUsersSummary() {
  try {
    const response = await fetch(`${API_ENDPOINT}/users`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error(`Failed to get users summary: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting users summary:', error);
    throw error;
  }
}

/**
 * Get filtered sessions by date range
 * @param {Date} startDate - Start date for filtering
 * @param {Date} endDate - End date for filtering
 * @returns {Promise<Array>} Filtered array of sessions
 */
export async function getSessionsByDateRange(startDate, endDate) {
  try {
    const allSessions = await getAllSessions();
    
    return allSessions.filter(session => {
      const sessionDate = new Date(session.session_start_time);
      return sessionDate >= startDate && sessionDate <= endDate;
    });
  } catch (error) {
    console.error('Error getting sessions by date range:', error);
    throw error;
  }
}

/**
 * Get top performing flashcards by net feedback score
 * @param {number} limit - Number of top flashcards to return
 * @returns {Promise<Array>} Array of top performing flashcards
 */
export async function getTopPerformingFlashcards(limit = 10) {
  try {
    const feedbackSummary = await getFlashcardFeedbackSummary();
    
    // Sort by net score (likes - dislikes) in descending order
    const topFlashcards = feedbackSummary
      .sort((a, b) => b.net_score - a.net_score)
      .slice(0, limit);
    
    return topFlashcards;
  } catch (error) {
    console.error('Error getting top performing flashcards:', error);
    throw error;
  }
}

/**
 * Get worst performing flashcards by net feedback score
 * @param {number} limit - Number of worst flashcards to return
 * @returns {Promise<Array>} Array of worst performing flashcards
 */
export async function getWorstPerformingFlashcards(limit = 10) {
  try {
    const feedbackSummary = await getFlashcardFeedbackSummary();
    
    // Sort by net score (likes - dislikes) in ascending order
    const worstFlashcards = feedbackSummary
      .sort((a, b) => a.net_score - b.net_score)
      .slice(0, limit);
    
    return worstFlashcards;
  } catch (error) {
    console.error('Error getting worst performing flashcards:', error);
    throw error;
  }
}

/**
 * Get user activity statistics
 * @returns {Promise<Object>} User activity statistics
 */
export async function getUserActivityStats() {
  try {
    const [overview, sessions] = await Promise.all([
      getAnalyticsOverview(),
      getAllSessions()
    ]);
    
    // Calculate additional stats
    const completedSessions = sessions.filter(session => session.is_completed).length;
    const avgSessionDuration = sessions
      .filter(session => session.study_duration_seconds)
      .reduce((sum, session) => sum + session.study_duration_seconds, 0) / sessions.length || 0;
    
    return {
      ...overview,
      completion_rate: overview.total_sessions > 0 ? (completedSessions / overview.total_sessions) * 100 : 0,
      average_session_duration_minutes: Math.round(avgSessionDuration / 60)
    };
  } catch (error) {
    console.error('Error getting user activity stats:', error);
    throw error;
  }
}
