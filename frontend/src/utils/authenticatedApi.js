import { auth } from './firebase';

// Base API URL - adjust this to match your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Makes an authenticated API request with Firebase ID token
 * @param {string} endpoint - API endpoint (e.g., '/api/courses')
 * @param {Object} options - Fetch options (method, body, etc.)
 * @returns {Promise<Response>} - Fetch response
 */
export const authenticatedFetch = async (endpoint, options = {}) => {
  try {
    // Get the current user's ID token
    const user = auth.currentUser;
    if (!user) {
      throw new Error('User not authenticated');
    }

    const idToken = await user.getIdToken();

    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${idToken}`,
      ...options.headers,
    };

    // Make the request
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    // Handle authentication errors
    if (response.status === 401) {
      // Token might be expired, try to refresh
      const refreshedToken = await user.getIdToken(true);
      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          'Authorization': `Bearer ${refreshedToken}`,
        },
      });
      
      if (retryResponse.status === 401) {
        // Still unauthorized, redirect to login
        throw new Error('Authentication failed');
      }
      
      return retryResponse;
    }

    return response;
  } catch (error) {
    console.error('Authenticated API request failed:', error);
    throw error;
  }
};

/**
 * Convenience method for GET requests
 */
export const authenticatedGet = async (endpoint) => {
  return authenticatedFetch(endpoint, { method: 'GET' });
};

/**
 * Convenience method for POST requests
 */
export const authenticatedPost = async (endpoint, data) => {
  return authenticatedFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

/**
 * Convenience method for PUT requests
 */
export const authenticatedPut = async (endpoint, data) => {
  return authenticatedFetch(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
};

/**
 * Convenience method for DELETE requests
 */
export const authenticatedDelete = async (endpoint) => {
  return authenticatedFetch(endpoint, { method: 'DELETE' });
};
