/**
 * API Service for Exam Readiness Score (The Trinity Engine)
 */
import { authenticatedGet } from '../utils/authenticatedApi';

/**
 * Get exam readiness score with Trinity breakdown
 * @param {string} courseId - Course identifier
 * @param {string} examId - Exam identifier
 * @returns {Promise<Object>} Readiness score with breakdown and recommendations
 */
export const getExamReadiness = async (courseId, examId) => {
  try {
    const data = await authenticatedGet(`/api/v1/timetables/${courseId}/exams/${examId}/readiness`);
    return data;
  } catch (error) {
    console.error('Failed to fetch exam readiness:', error);
    throw error;
  }
};

