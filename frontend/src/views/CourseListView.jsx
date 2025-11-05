import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import EnrollButton from '../components/EnrollButton'
import CourseCountdownDock from '../components/CourseCountdownDock'
import CourseCardBadge from '../components/CourseCardBadge'
import './CourseListView.css'

function CourseListView() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/courses.json')
      .then(response => response.json())
      .then(data => {
        setCourses(data)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading courses:', error)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading courses...</p>
      </div>
    )
  }

  return (
    <div className="course-list-view">
      <CourseCountdownDock />
      <header className="page-header">
        <img src="/logo.png" alt="exammate.ai logo" className="logo-icon" />
        <h1>exammate.ai</h1>
        <p className="subtitle">Study smart, when time is short</p>
      </header>

      <div className="courses-container">
        <h2>Select a Course</h2>
        <div className="courses-grid">
          {courses.map(course => (
            <div 
              key={course.course_id} 
              className="course-card"
              onClick={() => navigate(`/courses/${course.course_id}`)}
              data-course-id={course.course_id}
            >
              <div className="course-header">
                <h3>{course.course_name}</h3>
                <span className="course-code">{course.course_code}</span>
              </div>
              
              {course.course_description && (
                <p className="course-description">{course.course_description}</p>
              )}
              
              <div className="course-meta">
                <div className="meta-item">
                  <span className="icon">📖</span>
                  <span>{course.lecture_slides?.length || 0} lecture{course.lecture_slides?.length !== 1 ? 's' : ''}</span>
                </div>
                {course.instructor && (
                  <div className="meta-item">
                    <span className="icon">👨‍🏫</span>
                    <span>{course.instructor}</span>
                  </div>
                )}
              </div>
              
              {/* Badge with countdown anchored above footer */}
              <CourseCardBadge courseId={course.course_id} />

              <div className="card-footer">
                <EnrollButton 
                  courseId={course.course_id} 
                  variant="compact"
                  onEnrollmentChange={() => {}}
                />
                <button 
                  className="btn-primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/courses/${course.course_id}`);
                  }}
                >
                  View Course →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CourseListView

