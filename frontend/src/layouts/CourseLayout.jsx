import React from 'react'
import { Outlet } from 'react-router-dom'
import ExamCountdown from '../components/ExamCountdown'

/**
 * CourseLayout - wraps all course routes and injects the ExamCountdown
 */
export default function CourseLayout() {
  return (
    <>
      <ExamCountdown />
      <Outlet />
    </>
  )
}


