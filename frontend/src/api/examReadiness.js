/**
 * API Service for Exam Readiness Score
 */
import { authenticatedGet } from '../utils/authenticatedApi';

/**
 * Get exam readiness score with Trinity breakdown (Legacy)
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

/**
 * Get per-lecture readiness scores for an exam
 * @param {string} courseId - Course identifier
 * @param {string[]} lectureIds - Array of lecture IDs
 * @returns {Promise<Object>} Mapping of lecture_id to readiness score (0-100)
 */
export const getLectureReadiness = async (courseId, lectureIds) => {
  try {
    const lectureIdsParam = lectureIds.join(',');
    const data = await authenticatedGet(
      `/api/v1/readiness/lectures?course_id=${encodeURIComponent(courseId)}&lecture_ids=${encodeURIComponent(lectureIdsParam)}`
    );
    return data;
  } catch (error) {
    console.error('Failed to fetch lecture readiness:', error);
    throw error;
  }
};

/**
 * Get detailed exam readiness breakdown with per-lecture scores
 * @param {string} examId - Exam identifier
 * @param {string} courseId - Course identifier
 * @param {string[]} lectureIds - Array of lecture IDs covered by the exam
 * @returns {Promise<Object>} Detailed breakdown with lecture_scores and overall_score
 */
export const getExamReadinessBreakdown = async (examId, courseId, lectureIds) => {
  try {
    const lectureIdsParam = lectureIds.join(',');
    const data = await authenticatedGet(
      `/api/v1/readiness/exam/${examId}?course_id=${encodeURIComponent(courseId)}&lecture_ids=${encodeURIComponent(lectureIdsParam)}`
    );
    return data;
  } catch (error) {
    console.error('Failed to fetch exam readiness breakdown:', error);
    throw error;
  }
};

