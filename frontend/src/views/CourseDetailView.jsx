import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './CourseDetailView.css'

function CourseDetailView() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/courses.json')
      .then(response => response.json())
      .then(data => {
        const foundCourse = data.find(c => c.course_id === courseId)
        setCourse(foundCourse)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading course:', error)
        setLoading(false)
      })
  }, [courseId])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading course...</p>
      </div>
    )
  }

  if (!course) {
    return (
      <div className="error-container">
        <h2>Course not found</h2>
        <button onClick={() => navigate('/')}>← Back to Courses</button>
      </div>
    )
  }

  const handleLectureClick = (deck) => {
    // Extract lecture ID from PDF path (e.g., "MIS_lec_1-3.pdf" -> "MIS_lec_1-3")
    const pdfFilename = deck.pdf_path.split('/').pop()
    const lectureId = pdfFilename.replace('.pdf', '')
    navigate(`/courses/${courseId}/${lectureId}`)
  }

  return (
    <div className="course-detail-view">
      <button className="back-button" onClick={() => navigate('/')}>
        ← Back to Courses
      </button>

      <div className="course-header-section">
        <div className="course-title-row">
          <h1>{course.course_name}</h1>
          <span className="course-code-badge">{course.course_code}</span>
        </div>
        
        {course.course_description && (
          <p className="course-description-full">{course.course_description}</p>
        )}

        <div className="course-info-grid">
          {course.instructor && (
            <div className="info-card">
              <span className="info-icon">👨‍🏫</span>
              <div>
                <div className="info-label">Instructor</div>
                <div className="info-value">{course.instructor}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="lectures-section">
        <h2>📖 Lectures</h2>
        {course.lecture_slides && course.lecture_slides.length > 0 ? (
          <div className="lectures-grid">
            {course.lecture_slides.map((deck, index) => (
              <div 
                key={deck.lecture_number || index} 
                className="lecture-card"
                onClick={() => handleLectureClick(deck)}
              >
                <div className="lecture-number">Lecture {deck.lecture_number || index + 1}</div>
                <h3>{deck.lecture_name}</h3>
                
                {deck.topics && deck.topics.length > 0 && (
                  <div className="topics-list">
                    {deck.topics.map((topic, idx) => (
                      <span key={idx} className="topic-tag">{topic}</span>
                    ))}
                  </div>
                )}
                
                <button className="btn-study">
                  Start Studying →
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-lectures">
            <p>No lectures available yet for this course.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default CourseDetailView

