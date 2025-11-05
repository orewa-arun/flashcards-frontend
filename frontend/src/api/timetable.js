/**
 * API service for course exam timetables
 */

import { authenticatedGet, authenticatedPut, authenticatedDelete } from '../utils/authenticatedApi';

/**
 * Get exam timetable for a course
 * All dates returned in IST format
 * @param {string} courseId - Course identifier (e.g., "MS5031")
 * @returns {Promise} Timetable data
 */
export const getTimetable = async (courseId) => {
  try {
    const data = await authenticatedGet(`/api/v1/timetables/${courseId}`);
    return data;
  } catch (error) {
    console.error('Error fetching timetable:', error);
    throw error;
  }
};

/**
 * Update exam timetable for a course
 * Dates should be provided in IST format
 * @param {string} courseId - Course identifier
 * @param {Array} exams - Array of exam objects with date_ist, subject, notes
 * @returns {Promise} Updated timetable
 */
export const updateTimetable = async (courseId, exams) => {
  try {
    const data = await authenticatedPut(`/api/v1/timetables/${courseId}`, {
      exams: exams
    });
    return data;
  } catch (error) {
    console.error('Error updating timetable:', error);
    throw error;
  }
};

/**
 * Delete a specific exam from the timetable
 * @param {string} courseId - Course identifier
 * @param {string} examId - Exam identifier to delete
 * @returns {Promise} Deletion confirmation
 */
export const deleteExam = async (courseId, examId) => {
  try {
    const data = await authenticatedDelete(`/api/v1/timetables/${courseId}/exams/${examId}`);
    return data;
  } catch (error) {
    console.error('Error deleting exam:', error);
    throw error;
  }
};

/**
 * Get aggregated exam schedule for all enrolled courses
 * @returns {Promise} Aggregated schedule with all exams
 */
export const getMySchedule = async () => {
  try {
    const data = await authenticatedGet('/api/v1/timetables/my-schedule');
    return data;
  } catch (error) {
    console.error('Error fetching aggregated schedule:', error);
    throw error;
  }
};

