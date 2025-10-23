import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
      <header className="page-header">
        <h1>📚⚡ exammate.ai</h1>
        <p className="subtitle">Your intelligent study companion</p>
      </header>

      <div className="courses-container">
        <h2>Select a Course</h2>
        <div className="courses-grid">
          {courses.map(course => (
            <div 
              key={course.course_id} 
              className="course-card"
              onClick={() => navigate(`/courses/${course.course_id}`)}
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
              
              <div className="card-footer">
                <button className="btn-primary">
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

