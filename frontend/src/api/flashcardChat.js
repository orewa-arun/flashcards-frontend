/**
 * API service for Flashcard Chat functionality
 * Separate from AI Tutor - provides context-aware chat for individual flashcards
 */

import { auth } from '../utils/firebase';

// Main Backend API URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Get auth token for authenticated requests
 */
const getAuthToken = async () => {
  const user = auth.currentUser;
  if (!user) {
    throw new Error('User not authenticated');
  }
  return await user.getIdToken();
};

/**
 * Get existing chat for a flashcard
 * 
 * @param {string} flashcardId - Flashcard identifier
 * @returns {Promise<Object|null>} Chat with messages or null if none exists
 */
export const getFlashcardChat = async (flashcardId) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/flashcard-chat/${flashcardId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get flashcard chat: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Flashcard chat retrieved:', data);
    return data;
  } catch (error) {
    console.error('❌ Error getting flashcard chat:', error);
    throw error;
  }
};

/**
 * Send a message in a flashcard chat (non-streaming)
 * Creates chat on first message with flashcard context
 * 
 * @param {string} flashcardId - Flashcard identifier
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {string} message - User's message
 * @param {Object} flashcardContext - Flashcard content (only used on first message)
 * @returns {Promise<Object>} Response with answer and chat_id
 */
export const sendFlashcardMessage = async (flashcardId, courseId, lectureId, message, flashcardContext = null) => {
  try {
    const token = await getAuthToken();
    
    const requestBody = {
      flashcard_id: flashcardId,
      course_id: courseId,
      lecture_id: lectureId,
      message: message
    };
    
    // Only include flashcard_context on first message
    if (flashcardContext) {
      requestBody.flashcard_context = flashcardContext;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/flashcard-chat/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Flashcard message sent successfully:', data);
    return data;
  } catch (error) {
    console.error('❌ Error sending flashcard message:', error);
    throw error;
  }
};

/**
 * Send a message and stream the response
 * Creates chat on first message with flashcard context
 * 
 * @param {string} flashcardId - Flashcard identifier
 * @param {string} courseId - Course identifier
 * @param {string} lectureId - Lecture identifier
 * @param {string} message - User's message
 * @param {Object} flashcardContext - Flashcard content (only used on first message)
 * @param {Function} onChunk - Callback for each text chunk
 * @returns {Promise<void>}
 */
export const streamFlashcardMessage = async (flashcardId, courseId, lectureId, message, flashcardContext, onChunk) => {
  try {
    const token = await getAuthToken();
    
    const requestBody = {
      flashcard_id: flashcardId,
      course_id: courseId,
      lecture_id: lectureId,
      message: message
    };
    
    // Only include flashcard_context on first message
    if (flashcardContext) {
      requestBody.flashcard_context = flashcardContext;
    }
    
    const response = await fetch(`${API_BASE_URL}/api/flashcard-chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Stream failed: ${response.status} ${errorText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const text = decoder.decode(value, { stream: true });
      onChunk(text);
    }
    
    console.log('✅ Flashcard chat stream completed');
  } catch (error) {
    console.error('❌ Error streaming flashcard message:', error);
    throw error;
  }
};

/**
 * Delete a flashcard chat (clear history)
 * Allows user to start fresh with new context
 * 
 * @param {string} flashcardId - Flashcard identifier
 * @returns {Promise<Object>} Success response
 */
export const deleteFlashcardChat = async (flashcardId) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/flashcard-chat/${flashcardId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to delete flashcard chat: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Flashcard chat deleted:', data);
    return data;
  } catch (error) {
    console.error('❌ Error deleting flashcard chat:', error);
    throw error;
  }
};

/**
 * Get all flashcard chats for the current user
 * 
 * @param {string} courseId - Optional course filter
 * @param {string} lectureId - Optional lecture filter
 * @returns {Promise<Array>} List of flashcard chats
 */
export const getUserFlashcardChats = async (courseId = null, lectureId = null) => {
  try {
    const token = await getAuthToken();
    const params = new URLSearchParams();
    if (courseId) params.append('course_id', courseId);
    if (lectureId) params.append('lecture_id', lectureId);
    
    const url = `${API_BASE_URL}/api/flashcard-chat/user/chats?${params.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get user chats: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ User flashcard chats retrieved:', data);
    return data;
  } catch (error) {
    console.error('❌ Error getting user flashcard chats:', error);
    throw error;
  }
};

export default {
  getFlashcardChat,
  sendFlashcardMessage,
  streamFlashcardMessage,
  deleteFlashcardChat,
  getUserFlashcardChats
};

