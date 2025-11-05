/**
 * API service for user profile and course enrollment
 */

import { authenticatedGet, authenticatedPost, authenticatedDelete } from '../utils/authenticatedApi';

/**
 * Get current user's profile with enrolled courses
 * @returns {Promise} User profile data
 */
export const getUserProfile = async () => {
  try {
    const data = await authenticatedGet('/api/v1/profile');
    return data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

/**
 * Enroll in a course
 * @param {string} courseId - Course identifier
 * @returns {Promise} Updated enrollment data
 */
export const enrollInCourse = async (courseId) => {
  try {
    const data = await authenticatedPost(`/api/v1/profile/enroll/${courseId}`);
    return data;
  } catch (error) {
    console.error('Error enrolling in course:', error);
    throw error;
  }
};

/**
 * Unenroll from a course
 * @param {string} courseId - Course identifier
 * @returns {Promise} Updated enrollment data
 */
export const unenrollFromCourse = async (courseId) => {
  try {
    const data = await authenticatedDelete(`/api/v1/profile/enroll/${courseId}`);
    return data;
  } catch (error) {
    console.error('Error unenrolling from course:', error);
    throw error;
  }
};

/**
 * Check enrollment status for a specific course
 * @param {string} courseId - Course identifier
 * @returns {Promise} Enrollment status
 */
export const checkEnrollmentStatus = async (courseId) => {
  try {
    const data = await authenticatedGet(`/api/v1/profile/enrollment/${courseId}`);
    return data;
  } catch (error) {
    console.error('Error checking enrollment status:', error);
    throw error;
  }
};

