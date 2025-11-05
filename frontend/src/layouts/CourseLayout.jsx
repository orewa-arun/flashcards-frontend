import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * CourseLayout - wraps all course routes and injects the ExamCountdown
 * floating orb. This ensures it's available on all course-related views.
 */
export default function CourseLayout() {
  return (
    <>
      <Outlet />
    </>
  );
}


