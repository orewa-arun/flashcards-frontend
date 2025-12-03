import { authenticatedFetch } from '../utils/authenticatedApi';
// import { auth } from '../utils/firebase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const contentPipeline = {
  /**
   * Ingest new course content
   * @param {FormData} formData - Form data containing course details and files
   * @returns {Promise<Object>} Response data
   */
  async ingestContent(formData) {
    const response = await authenticatedFetch(`/api/v1/content/ingest`, {
      method: 'POST',
      // Do NOT set Content-Type here, let browser set it for FormData
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to ingest content');
    }

    return response.json();
  },

  /**
   * Trigger a specific pipeline action for a lecture
   * @param {string} action - Action name (analyze, flashcards, quiz, index)
   * @param {number} lectureId - ID of the lecture
   * @returns {Promise<Object>} Response data
   */
  async triggerAction(action, lectureId) {
    const response = await authenticatedFetch(`/api/v1/content/${action}/${lectureId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to trigger action ${action}`);
    }
    return response.json();
  },

  /**
   * Get list of lectures with status
   * @param {string} [courseCode] - Optional course code to filter
   * @returns {Promise<Array>} List of lectures
   */
  async getLectures(courseCode = null) {
    let url = `/api/v1/content/lectures`;
    if (courseCode) {
      url += `?course_code=${encodeURIComponent(courseCode)}`;
    }
    const response = await authenticatedFetch(url);
    if (!response.ok) throw new Error('Failed to fetch lectures');
    return response.json();
  },

  /**
   * Get list of all courses
   * @returns {Promise<Array>} List of courses
   */
  async getCourses() {
    const response = await authenticatedFetch(`/api/v1/content/courses`);
    if (!response.ok) throw new Error('Failed to fetch courses');
    return response.json();
  },

  /**
   * Delete a lecture (soft delete)
   * @param {number} lectureId - ID of the lecture to delete
   * @returns {Promise<Object>} Response data
   */
  async deleteLecture(lectureId) {
    const response = await authenticatedFetch(`/api/v1/content/lectures/${lectureId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete lecture');
    }
    return response.json();
  },

  /**
   * Run the full pipeline for a lecture (Analysis → Flashcards → Quiz → Indexing)
   * This triggers background processing; the request returns immediately.
   * @param {number} lectureId - ID of the lecture to process
   * @returns {Promise<Object>} Response data with status message
   */
  async processLecture(lectureId) {
    const response = await authenticatedFetch(`/api/v1/content/process/${lectureId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start pipeline');
    }
    return response.json();
  }
};
