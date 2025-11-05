/**
 * EnrollButton - Smart button component for course enrollment
 */

import React, { useState, useEffect } from 'react';
import { FaCheck, FaPlus, FaSpinner } from 'react-icons/fa';
import { getUserProfile, enrollInCourse, unenrollFromCourse } from '../api/profile';
import './EnrollButton.css';

const EnrollButton = ({ courseId, variant = 'default', onEnrollmentChange }) => {
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    checkEnrollmentStatus();
  }, [courseId]);

  const checkEnrollmentStatus = async () => {
    try {
      setLoading(true);
      const profile = await getUserProfile();
      const enrolled = profile.enrolled_courses?.includes(courseId) || false;
      setIsEnrolled(enrolled);
    } catch (error) {
      console.error('Error checking enrollment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEnrollmentToggle = async (e) => {
    e.stopPropagation(); // Prevent parent click events
    
    try {
      setProcessing(true);
      
      if (isEnrolled) {
        await unenrollFromCourse(courseId);
        setIsEnrolled(false);
        if (onEnrollmentChange) onEnrollmentChange(false);
      } else {
        await enrollInCourse(courseId);
        setIsEnrolled(true);
        if (onEnrollmentChange) onEnrollmentChange(true);
      }
    } catch (error) {
      console.error('Error toggling enrollment:', error);
      alert('Failed to update enrollment. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <button className={`enroll-btn ${variant} loading`} disabled>
        <FaSpinner className="spinner" /> Loading...
      </button>
    );
  }

  return (
    <button
      className={`enroll-btn ${variant} ${isEnrolled ? 'enrolled' : ''}`}
      onClick={handleEnrollmentToggle}
      disabled={processing}
    >
      {processing ? (
        <>
          <FaSpinner className="spinner" /> Processing...
        </>
      ) : isEnrolled ? (
        <>
          <FaCheck /> Enrolled
        </>
      ) : (
        <>
          <FaPlus /> Enroll
        </>
      )}
    </button>
  );
};

export default EnrollButton;

