/**
 * API service for AI Tutor chatbot
 * Communicates with the main backend (port 8000) for conversation management
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
 * Create a new conversation
 * 
 * @param {string} courseId - Course identifier (e.g., "MS5260")
 * @param {string} lectureId - Lecture identifier (e.g., "MIS_lec_1-3")
 * @returns {Promise<string>} conversation_id
 */
export const createConversation = async (courseId, lectureId) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        course_id: courseId,
        lecture_id: lectureId
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create conversation: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Conversation created:', data);
    return data.conversation_id;
  } catch (error) {
    console.error('❌ Error creating conversation:', error);
    throw error;
  }
};

/**
 * Get all conversations for current user
 * 
 * @param {string} courseId - Optional course filter
 * @param {string} lectureId - Optional lecture filter
 * @returns {Promise<Array>} List of conversations
 */
export const getConversations = async (courseId = null, lectureId = null) => {
  try {
    const token = await getAuthToken();
    const params = new URLSearchParams();
    if (courseId) params.append('course_id', courseId);
    if (lectureId) params.append('lecture_id', lectureId);
    
    const url = `${API_BASE_URL}/api/tutor/conversations?${params.toString()}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get conversations: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Conversations retrieved:', data);
    return data;
  } catch (error) {
    console.error('❌ Error getting conversations:', error);
    throw error;
  }
};

/**
 * Get a specific conversation with all messages
 * 
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<Object>} Conversation with messages
 */
export const getConversation = async (conversationId) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to get conversation: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Conversation retrieved:', data);
    return data;
  } catch (error) {
    console.error('❌ Error getting conversation:', error);
    throw error;
  }
};

/**
 * Send a message in a conversation
 * 
 * @param {string} conversationId - Conversation ID
 * @param {string} message - User's message
 * @returns {Promise<Object>} Response with answer
 */
export const sendMessage = async (conversationId, message) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: message
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to send message: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Message sent successfully:', data);
    return data;
  } catch (error) {
    console.error('❌ Error sending message:', error);
    throw error;
  }
};

/**
 * Send a message and stream the response
 * 
 * @param {string} conversationId - Conversation ID
 * @param {string} message - User's message
 * @param {Function} onChunk - Callback for each text chunk
 * @returns {Promise<void>}
 */
export const streamMessage = async (conversationId, message, onChunk) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}/stream`, {
      method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ message })
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
    
    console.log('✅ Stream completed');
  } catch (error) {
    console.error('❌ Error streaming message:', error);
    throw error;
  }
};

/**
 * Delete a conversation
 * 
 * @param {string} conversationId - Conversation ID
 * @returns {Promise<Object>} Success response
 */
export const deleteConversation = async (conversationId) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}`, {
      method: 'DELETE',
        headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to delete conversation: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Conversation deleted:', data);
    return data;
  } catch (error) {
    console.error('❌ Error deleting conversation:', error);
    throw error;
  }
};

/**
 * Update conversation title
 * 
 * @param {string} conversationId - Conversation ID
 * @param {string} title - New title
 * @returns {Promise<Object>} Success response
 */
export const updateConversationTitle = async (conversationId, title) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}/title`, {
      method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: title
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to update title: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Title updated:', data);
    return data;
  } catch (error) {
    console.error('❌ Error updating title:', error);
    throw error;
  }
};

/**
 * Update conversation notes content
 * 
 * @param {string} conversationId - Conversation ID
 * @param {string} notes - Notes content
 * @returns {Promise<Object>} Success response
 */
export const updateConversationNotes = async (conversationId, notes) => {
  try {
    const token = await getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/tutor/conversations/${conversationId}/notes`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        notes
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to update notes: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('❌ Error updating notes:', error);
    throw error;
  }
};

export default {
  createConversation,
  getConversations,
  getConversation,
  sendMessage,
  deleteConversation,
  updateConversationTitle,
  updateConversationNotes
};

