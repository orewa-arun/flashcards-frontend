import { auth } from './firebase';
import { onAuthStateChanged } from 'firebase/auth';

// Base API URL - adjust this to match your backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Wait for Firebase auth to be ready and return the current user
 * @returns {Promise<User>} - Firebase user object
 */
const waitForAuthReady = () => {
  return new Promise((resolve, reject) => {
    // If user is already available, return immediately
    if (auth.currentUser) {
      resolve(auth.currentUser);
      return;
    }

    // Otherwise, wait for the auth state to be determined
    const unsubscribe = onAuthStateChanged(
      auth,
      (user) => {
        unsubscribe();
        if (user) {
          resolve(user);
        } else {
          reject(new Error('User not authenticated'));
        }
      },
      (error) => {
        unsubscribe();
        reject(error);
      }
    );
  });
};

/**
 * Makes an authenticated API request with Firebase ID token
 * @param {string} endpoint - API endpoint (e.g., '/api/courses')
 * @param {Object} options - Fetch options (method, body, etc.)
 * @returns {Promise<Response>} - Fetch response
 */
export const authenticatedFetch = async (endpoint, options = {}) => {
  try {
    // Wait for auth to be ready and get the current user
    const user = await waitForAuthReady();

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
  const response = await authenticatedFetch(endpoint, { method: 'GET' });
  if (!response.ok) {
    throw new Error(`GET request failed: ${response.status}`);
  }
  return response.json();
};

/**
 * Convenience method for POST requests
 */
export const authenticatedPost = async (endpoint, data) => {
  const response = await authenticatedFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`POST request failed: ${response.status}`);
  }
  return response.json();
};

/**
 * Convenience method for PUT requests
 */
export const authenticatedPut = async (endpoint, data) => {
  const response = await authenticatedFetch(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`PUT request failed: ${response.status}`);
  }
  return response.json();
};

/**
 * Convenience method for DELETE requests
 */
export const authenticatedDelete = async (endpoint, data = null) => {
  const options = { method: 'DELETE' };
  if (data) {
    options.body = JSON.stringify(data);
  }
  const response = await authenticatedFetch(endpoint, options);
  if (!response.ok) {
    throw new Error(`DELETE request failed: ${response.status}`);
  }
  return response.json();
};
