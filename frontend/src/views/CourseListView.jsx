import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FaBook, FaChalkboardTeacher, FaCheckCircle } from 'react-icons/fa'
import EnrollButton from '../components/EnrollButton'
import CourseCountdownDock from '../components/CourseCountdownDock'
import NextDeadline from '../components/NextDeadline'
import CourseCardBadge from '../components/CourseCardBadge'
import { getCoursesPublic } from '../api/courses'
import './CourseListView.css'

function CourseListView() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hoveredCard, setHoveredCard] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const data = await getCoursesPublic()
        setCourses(data)
        setError(null)
      } catch (err) {
        console.error('Error loading courses:', err)
        setError('Failed to load courses. Please try again later.')
      } finally {
        setLoading(false)
      }
    }
    
    loadCourses()
  }, [])

  const truncateText = (text, maxLength = 150) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength).trim() + '...'
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading courses...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  return (
    <div className="course-list-view">
      <CourseCountdownDock />
      
      {/* Refined Header */}
      <header className="page-header">
        <h1 className="page-title">Select a Course</h1>
      </header>

      {/* Spiral Binding Divider */}
      <div className="spiral-divider">
        <div className="spiral-ring"></div>
        <div className="spiral-ring"></div>
        <div className="spiral-ring"></div>
        <div className="spiral-ring"></div>
        <div className="spiral-ring"></div>
      </div>

      <div className="courses-container">
        <div className="courses-grid">
          {courses.map(course => (
            <div 
              key={course.course_id} 
              className="course-card"
              onClick={() => navigate(`/courses/${course.course_id}`)}
              onMouseEnter={() => setHoveredCard(course.course_id)}
              onMouseLeave={() => setHoveredCard(null)}
              data-course-id={course.course_id}
            >
              {/* Course Code Tab */}
              <div className="course-code-tab">
                {course.course_code}
              </div>

              {/* Course Content */}
              <div className="course-content">
                <h3 className="course-title">{course.course_name}</h3>
                
                {course.course_description && (
                  <div className="course-description-wrapper">
                    <p className="course-description">
                      {truncateText(course.course_description, 120)}
                    </p>
                    {course.course_description.length > 120 && hoveredCard === course.course_id && (
                      <div className="description-tooltip">
                        {course.course_description}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Badge with countdown */}
              {/* <CourseCardBadge courseId={course.course_id} /> */}

              {/* Metadata Footer */}
              <div className="course-footer">
                <div className="course-meta">
                  <div className="meta-item">
                    <FaBook className="meta-icon" />
                    <span className="meta-text">
                      {course.lecture_count || 0} lecture{course.lecture_count !== 1 ? 's' : ''}
                    </span>
                  </div>
                  {course.instructor && (
                    <div className="meta-item">
                      <FaChalkboardTeacher className="meta-icon" />
                      <span className="meta-text">{course.instructor}</span>
                    </div>
                  )}
                  <NextDeadline courseId={course.course_id} />
                </div>

                {/* Action Buttons */}
                <div className="card-actions">
                  <EnrollButton 
                    courseId={course.course_id} 
                    variant="compact"
                    onEnrollmentChange={() => {}}
                  />
                  <button 
                    className="btn-view-course"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/courses/${course.course_id}`);
                    }}
                  >
                    View Course →
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default CourseListView
