/**
 * API Service for Courses and Lectures
 * 
 * Adapter layer that fetches from PostgreSQL-backed API and transforms
 * the response to match the structure expected by frontend components.
 */

import { authenticatedGet, authenticatedPut } from '../utils/authenticatedApi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Fetch all courses with lecture counts.
 * Transforms API response to match legacy courses.json structure.
 * 
 * @returns {Promise<Array>} List of courses
 */
export const getCourses = async () => {
  try {
    const courses = await authenticatedGet('/api/v1/content/courses');
    
    // Transform API response to match expected frontend structure
    return courses.map(course => ({
      // Map course_code to course_id for URL routing compatibility
      course_id: course.course_code,
      course_code: course.course_code,
      course_name: course.course_name,
      course_description: course.additional_info || '',
      instructor: course.instructor || '',
      reference_textbooks: course.reference_textbooks || [],
      course_repository_link: course.course_repository_link || null,
      repository_created_by: course.repository_created_by || null,
      // Create a placeholder lecture_slides array with correct length for display
      lecture_slides: Array(course.lecture_count || 0).fill(null),
      lecture_count: course.lecture_count || 0,
      // Keep original fields for reference
      id: course.id,
      created_at: course.created_at,
      updated_at: course.updated_at
    }));
  } catch (error) {
    console.error('Failed to fetch courses:', error);
    throw error;
  }
};

/**
 * Fetch all courses without authentication (for public pages).
 * 
 * @returns {Promise<Array>} List of courses
 */
export const getCoursesPublic = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/content/courses`);
    if (!response.ok) {
      throw new Error(`Failed to fetch courses: ${response.status}`);
    }
    const courses = await response.json();
    
    // Transform API response to match expected frontend structure
    return courses.map(course => ({
      course_id: course.course_code,
      course_code: course.course_code,
      course_name: course.course_name,
      course_description: course.additional_info || '',
      instructor: course.instructor || '',
      reference_textbooks: course.reference_textbooks || [],
      course_repository_link: course.course_repository_link || null,
      repository_created_by: course.repository_created_by || null,
      lecture_slides: Array(course.lecture_count || 0).fill(null),
      lecture_count: course.lecture_count || 0,
      id: course.id,
      created_at: course.created_at,
      updated_at: course.updated_at
    }));
  } catch (error) {
    console.error('Failed to fetch courses (public):', error);
    throw error;
  }
};

/**
 * Fetch a specific course with its lectures.
 * Merges course and lecture data to match legacy nested structure.
 * 
 * @param {string} courseId - Course code (e.g., "MS5260")
 * @returns {Promise<Object>} Course with nested lecture_slides
 */
export const getCourse = async (courseId) => {
  try {
    // Fetch courses and lectures in parallel
    const [courses, lectures] = await Promise.all([
      authenticatedGet('/api/v1/content/courses'),
      authenticatedGet(`/api/v1/content/lectures?course_code=${courseId}`)
    ]);
    
    // Find the specific course
    const course = courses.find(c => c.course_code === courseId);
    if (!course) {
      throw new Error(`Course ${courseId} not found`);
    }
    
    // Transform lectures to match expected lecture_slides structure
    const lectureSlides = lectures.map((lecture, index) => ({
      // Use integer ID for routing
      id: lecture.id,
      // Keep pdf_path for legacy compatibility
      pdf_path: lecture.r2_pdf_path,
      lecture_name: lecture.lecture_title,
      // Derive lecture_number from index or title
      lecture_number: extractLectureNumber(lecture.lecture_title, index + 1),
      topics: lecture.topics || [],
      // Include status info for potential UI enhancements
      analysis_status: lecture.analysis_status,
      flashcard_status: lecture.flashcard_status,
      quiz_status: lecture.quiz_status
    }));
    
    // Return merged course object
    return {
      course_id: course.course_code,
      course_code: course.course_code,
      course_name: course.course_name,
      course_description: course.additional_info || '',
      instructor: course.instructor || '',
      reference_textbooks: course.reference_textbooks || [],
      course_repository_link: course.course_repository_link || null,
      repository_created_by: course.repository_created_by || null,
      lecture_slides: lectureSlides,
      lecture_count: lectureSlides.length,
      id: course.id,
      created_at: course.created_at,
      updated_at: course.updated_at
    };
  } catch (error) {
    console.error(`Failed to fetch course ${courseId}:`, error);
    throw error;
  }
};

/**
 * Fetch a specific course without authentication (for public pages).
 * 
 * @param {string} courseId - Course code (e.g., "MS5260")
 * @returns {Promise<Object>} Course with nested lecture_slides
 */
export const getCoursePublic = async (courseId) => {
  try {
    // Fetch courses and lectures in parallel
    const [coursesRes, lecturesRes] = await Promise.all([
      fetch(`${API_BASE_URL}/api/v1/content/courses`),
      fetch(`${API_BASE_URL}/api/v1/content/lectures?course_code=${courseId}`)
    ]);
    
    if (!coursesRes.ok || !lecturesRes.ok) {
      throw new Error('Failed to fetch course data');
    }
    
    const [courses, lectures] = await Promise.all([
      coursesRes.json(),
      lecturesRes.json()
    ]);
    
    // Find the specific course
    const course = courses.find(c => c.course_code === courseId);
    if (!course) {
      throw new Error(`Course ${courseId} not found`);
    }
    
    // Transform lectures to match expected lecture_slides structure
    const lectureSlides = lectures.map((lecture, index) => ({
      id: lecture.id,
      pdf_path: lecture.r2_pdf_path,
      lecture_name: lecture.lecture_title,
      lecture_number: extractLectureNumber(lecture.lecture_title, index + 1),
      topics: lecture.topics || [],
      analysis_status: lecture.analysis_status,
      flashcard_status: lecture.flashcard_status,
      quiz_status: lecture.quiz_status
    }));
    
    return {
      course_id: course.course_code,
      course_code: course.course_code,
      course_name: course.course_name,
      course_description: course.additional_info || '',
      instructor: course.instructor || '',
      reference_textbooks: course.reference_textbooks || [],
      course_repository_link: course.course_repository_link || null,
      repository_created_by: course.repository_created_by || null,
      lecture_slides: lectureSlides,
      lecture_count: lectureSlides.length,
      id: course.id,
      created_at: course.created_at,
      updated_at: course.updated_at
    };
  } catch (error) {
    console.error(`Failed to fetch course ${courseId} (public):`, error);
    throw error;
  }
};

/**
 * Fetch a specific lecture by ID.
 * 
 * @param {number|string} lectureId - Lecture ID (integer)
 * @returns {Promise<Object>} Lecture data
 */
export const getLecture = async (lectureId) => {
  try {
    const lecture = await authenticatedGet(`/api/v1/content/lectures/${lectureId}`);
    
    return {
      id: lecture.id,
      course_code: lecture.course_code,
      pdf_path: lecture.r2_pdf_path,
      lecture_name: lecture.lecture_title,
      lecture_number: extractLectureNumber(lecture.lecture_title, 1),
      topics: lecture.topics || [],
      analysis_status: lecture.analysis_status,
      flashcard_status: lecture.flashcard_status,
      quiz_status: lecture.quiz_status,
      qdrant_status: lecture.qdrant_status,
      error_log: lecture.error_log,
      created_at: lecture.created_at,
      updated_at: lecture.updated_at
    };
  } catch (error) {
    console.error(`Failed to fetch lecture ${lectureId}:`, error);
    throw error;
  }
};

/**
 * Fetch a specific lecture without authentication.
 * 
 * @param {number|string} lectureId - Lecture ID (integer)
 * @returns {Promise<Object>} Lecture data
 */
export const getLecturePublic = async (lectureId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/content/lectures/${lectureId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch lecture: ${response.status}`);
    }
    const lecture = await response.json();
    
    return {
      id: lecture.id,
      course_code: lecture.course_code,
      pdf_path: lecture.r2_pdf_path,
      lecture_name: lecture.lecture_title,
      lecture_number: extractLectureNumber(lecture.lecture_title, 1),
      topics: lecture.topics || [],
      analysis_status: lecture.analysis_status,
      flashcard_status: lecture.flashcard_status,
      quiz_status: lecture.quiz_status,
      qdrant_status: lecture.qdrant_status,
      error_log: lecture.error_log,
      created_at: lecture.created_at,
      updated_at: lecture.updated_at
    };
  } catch (error) {
    console.error(`Failed to fetch lecture ${lectureId} (public):`, error);
    throw error;
  }
};

/**
 * Extract lecture number from title.
 * Examples:
 *   "MIS Lectures 1-3" -> "1-3"
 *   "SI Product Life Cycle" -> fallback
 *   "DAA Lecture 1" -> "1"
 * 
 * @param {string} title - Lecture title
 * @param {number} fallback - Fallback number (usually index + 1)
 * @returns {string} Lecture number
 */
function extractLectureNumber(title, fallback) {
  if (!title) return String(fallback);
  
  // Try to match patterns like "Lecture 1", "Lectures 1-3", "Lec 4"
  const match = title.match(/lectures?\s*(\d+(?:-\d+)?)/i);
  if (match) {
    return match[1];
  }
  
  // Try to match just numbers at the end
  const endMatch = title.match(/(\d+(?:-\d+)?)$/);
  if (endMatch) {
    return endMatch[1];
  }
  
  return String(fallback);
}

/**
 * Update the course repository link.
 * 
 * Uses authenticated request - user info is extracted from the auth token
 * on the backend for secure attribution and audit logging.
 * 
 * @param {string} courseId - Course code (e.g., "MS5260")
 * @param {string} link - The repository/drive link
 * @param {string} userName - User's display name (used as fallback in DEBUG mode)
 * @returns {Promise<Object>} Updated repository info
 */
export const updateCourseRepository = async (courseId, link, userName) => {
  try {
    return await authenticatedPut(`/api/v1/content/courses/${courseId}/repository`, {
      link: link,
      user_name: userName  // Fallback for DEBUG mode when token doesn't have real name
    });
  } catch (error) {
    console.error(`Failed to update course repository for ${courseId}:`, error);
    throw error;
  }
};







