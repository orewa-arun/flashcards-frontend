import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FaCalendarAlt, FaBook, FaExclamationTriangle, FaChevronDown, FaChevronUp } from 'react-icons/fa'
import EnrollButton from '../components/EnrollButton'
import { getWeakConcepts } from '../api/weakConcepts'
import './CourseDetailView.css'

function CourseDetailView() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [weakConcepts, setWeakConcepts] = useState(null)
  const [weakConceptsLoading, setWeakConceptsLoading] = useState(true)
  const [expandedConcepts, setExpandedConcepts] = useState(new Set())

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

  useEffect(() => {
    loadWeakConcepts()
  }, [courseId])

  const loadWeakConcepts = async () => {
    try {
      setWeakConceptsLoading(true)
      const data = await getWeakConcepts(courseId)
      setWeakConcepts(data)
    } catch (error) {
      console.error('Error loading weak concepts:', error)
      setWeakConcepts(null)
    } finally {
      setWeakConceptsLoading(false)
    }
  }

  const toggleConceptExpanded = (flashcardId) => {
    const newExpanded = new Set(expandedConcepts)
    if (newExpanded.has(flashcardId)) {
      newExpanded.delete(flashcardId)
    } else {
      newExpanded.add(flashcardId)
    }
    setExpandedConcepts(newExpanded)
  }

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
          <EnrollButton courseId={courseId} variant="large" />
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

      {/* Quick Actions */}
      <div className="quick-actions-section">
        <button 
          className="action-card timetable-card"
          onClick={() => navigate(`/courses/${courseId}/timetable`)}
        >
          <FaCalendarAlt className="action-icon" />
          <div className="action-content">
            <h3>Exam Timetable</h3>
            <p>View and manage your exam schedule</p>
          </div>
        </button>
      </div>

      {/* Weak Concepts Section - Compact Summary Card */}
      {!weakConceptsLoading && weakConcepts && weakConcepts.has_attempts && weakConcepts.total_weak > 0 && (
        <div className="weak-concepts-compact-card">
          <div className="compact-card-header">
            <FaExclamationTriangle className="warning-icon" />
            <div className="header-content">
              <h3>Concepts You Need to Review</h3>
              <p>
                You have <strong>{weakConcepts.total_weak}</strong> concept{weakConcepts.total_weak !== 1 ? 's' : ''} with accuracy below 60%. 
                Focus on these to improve your exam readiness.
              </p>
            </div>
          </div>
          <button 
            className="view-weak-concepts-btn"
            onClick={() => navigate('/weak-concepts')}
          >
            View All Weak Concepts →
          </button>
        </div>
      )}

      <div className="lectures-section">
        <h2><FaBook /> Lectures</h2>
        {course.lecture_slides && course.lecture_slides.length > 0 ? (
          <div className="lectures-grid">
            {course.lecture_slides.map((deck, index) => (
              <div 
                key={deck.lecture_number || index} 
                className="lecture-card"
              >
                <div className="lecture-number">Lecture {deck.lecture_number || index + 1}</div>
                <h3>{deck.lecture_name}</h3>
                
                {deck.topics && deck.topics.length > 0 && (
                  <div className="topics-container">
                    <div className="topics-list">
                      {deck.topics.slice(0, 3).map((topic, idx) => (
                        <span key={idx} className="topic-tag">{topic}</span>
                      ))}
                      {deck.topics.length > 3 && (
                        <span className="topic-tag more-topics">
                          +{deck.topics.length - 3} more
                        </span>
                      )}
                    </div>
                    
                    {/* Tooltip with all topics */}
                    {deck.topics.length > 3 && (
                      <div className="topics-tooltip">
                        <div className="tooltip-header">All Topics Covered ({deck.topics.length}):</div>
                        <div className="tooltip-content">
                          {deck.topics.map((topic, idx) => (
                            <div key={idx} className="tooltip-topic">• {topic}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <button 
                  className="btn-study"
                  onClick={() => handleLectureClick(deck)}
                >
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


