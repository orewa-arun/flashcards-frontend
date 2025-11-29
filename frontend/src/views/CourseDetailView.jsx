import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FaCalendarAlt, FaBook, FaExclamationTriangle, FaChalkboardTeacher, FaChevronRight } from 'react-icons/fa'
import EnrollButton from '../components/EnrollButton'
import NextDeadline from '../components/NextDeadline'
import { getWeakConcepts } from '../api/weakConcepts'
import { getCoursePublic } from '../api/courses'
import './CourseDetailView.css'

function CourseDetailView() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [weakConcepts, setWeakConcepts] = useState(null)
  const [weakConceptsLoading, setWeakConceptsLoading] = useState(true)
  const [hoveredLecture, setHoveredLecture] = useState(null)

  useEffect(() => {
    const loadCourse = async () => {
      try {
        const data = await getCoursePublic(courseId)
        setCourse(data)
        setError(null)
      } catch (err) {
        console.error('Error loading course:', err)
        setError('Failed to load course')
        setCourse(null)
      } finally {
        setLoading(false)
      }
    }
    
    loadCourse()
  }, [courseId])

  const loadWeakConcepts = useCallback(async () => {
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
  }, [courseId])

  useEffect(() => {
    loadWeakConcepts()
  }, [loadWeakConcepts])

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
        <button onClick={() => navigate('/courses')}>← Back to Courses</button>
      </div>
    )
  }

  const handleLectureClick = (deck) => {
    // Use integer ID for routing (from PostgreSQL)
    navigate(`/courses/${courseId}/${deck.id}`)
  }

  const truncateTopics = (topics, maxVisible = 3) => {
    if (!topics || topics.length === 0) return []
    return topics.slice(0, maxVisible)
  }

  return (
    <div className="course-detail-view">
      {/* Breadcrumb Navigation */}
      <nav className="breadcrumb">
        <button onClick={() => navigate('/courses')} className="breadcrumb-link">
          Courses
        </button>
        <FaChevronRight className="breadcrumb-separator" />
        <span className="breadcrumb-current">{course.course_name}</span>
      </nav>

      {/* Header: The Binder's Title Page */}
      <header className="course-header">
        <div className="course-title-block">
          <div className="title-row">
            <h1 className="course-title">{course.course_name}</h1>
            <span className="course-code-tab">{course.course_code}</span>
          </div>
          {course.course_description && (
            <p className="course-subtitle">{course.course_description}</p>
          )}
        </div>
        <div className="header-actions">
          <EnrollButton courseId={courseId} variant="large" />
        </div>
      </header>

      {/* Two-Column Layout */}
      <div className="course-content-layout">
        
        {/* Main Content: Lecture Cards */}
        <main className="lectures-main">
          <h2 className="section-title">
            <FaBook /> Lectures
          </h2>
          
          {course.lecture_slides && course.lecture_slides.length > 0 ? (
            <div className="lectures-grid">
              {course.lecture_slides.map((deck, index) => (
                <div 
                  key={deck.id || index} 
                  className="lecture-card"
                  onClick={() => handleLectureClick(deck)}
                  onMouseEnter={() => setHoveredLecture(index)}
                  onMouseLeave={() => setHoveredLecture(null)}
                >
                  {/* Lecture Number Tab (like course code tab) */}
                  <div className="lecture-number-tab">
                    Lecture {deck.lecture_number || index + 1}
                  </div>

                  {/* Card Content */}
                  <div className="lecture-content">
                    <h3 className="lecture-title">{deck.lecture_name}</h3>
                    
                    {/* Topics Preview */}
                    {deck.topics && deck.topics.length > 0 && (
                      <div className="topics-preview">
                        <div className="topics-list">
                          {truncateTopics(deck.topics, 3).map((topic, idx) => (
                            <span key={idx} className="topic-bullet">• {topic}</span>
                          ))}
                          {deck.topics.length > 3 && (
                            <span className="topic-bullet more-indicator">
                              +{deck.topics.length - 3} more topics
                            </span>
                          )}
                        </div>

                        {/* Tooltip with all topics (on hover) */}
                        {deck.topics.length > 3 && hoveredLecture === index && (
                          <div className="topics-tooltip">
                            <div className="tooltip-header">
                              All Topics Covered ({deck.topics.length}):
                            </div>
                            <div className="tooltip-topics">
                              {deck.topics.map((topic, idx) => (
                                <div key={idx} className="tooltip-topic">• {topic}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Action Button */}
                  <div className="lecture-footer">
                    <button 
                      className="btn-start-studying"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleLectureClick(deck);
                      }}
                    >
                      Start Studying →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-lectures">
              <p>No lectures available yet for this course.</p>
            </div>
          )}
        </main>

        {/* Right Sidebar: Status & Tools Panel */}
        <aside className="course-sidebar">
          
          {/* Instructor Card */}
          {course.instructor && (
            <div className="sidebar-card instructor-card">
              <div className="card-label">Instructor</div>
              <div className="instructor-info">
                <FaChalkboardTeacher className="instructor-icon" />
                <span className="instructor-name">{course.instructor}</span>
              </div>
            </div>
          )}

          {/* Next Deadline Card */}
          <div className="sidebar-card deadline-card">
            <div className="card-label">Next Deadline</div>
            <NextDeadline courseId={courseId} />
          </div>

          {/* Exam Timetable Link */}
          <button 
            className="sidebar-card timetable-link"
            onClick={() => navigate(`/courses/${courseId}/timetable`)}
          >
            <FaCalendarAlt className="timetable-icon" />
            <div className="timetable-content">
              <h4>View Full Schedule</h4>
              <p>Manage your exam timetable</p>
            </div>
          </button>

          {/* Weak Concepts Panel */}
          {!weakConceptsLoading && weakConcepts && weakConcepts.has_attempts && weakConcepts.total_weak > 0 && (
            <div className="sidebar-card weak-concepts-card">
              <div className="card-header-with-icon">
                <FaExclamationTriangle className="warning-icon" />
                <div className="card-label">Concepts to Review</div>
              </div>
              <p className="weak-concepts-summary">
                You have <strong>{weakConcepts.total_weak}</strong> concept{weakConcepts.total_weak !== 1 ? 's' : ''} with accuracy below 60%. 
                Focus on these to improve your exam readiness.
              </p>
              <button 
                className="btn-view-weak-concepts"
                onClick={() => navigate('/weak-concepts')}
              >
                View All Weak Concepts →
              </button>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

export default CourseDetailView
