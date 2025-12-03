import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FaCalendarAlt, FaBook, FaExclamationTriangle, FaChalkboardTeacher, FaChevronRight, FaFolder, FaPencilAlt, FaPlus, FaTimes, FaCheck } from 'react-icons/fa'
import EnrollButton from '../components/EnrollButton'
import NextDeadline from '../components/NextDeadline'
import { getWeakConcepts } from '../api/weakConcepts'
import { getCoursePublic, updateCourseRepository } from '../api/courses'
import { useAuth } from '../contexts/AuthContext'
import './CourseDetailView.css'

function CourseDetailView() {
  const { courseId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [weakConcepts, setWeakConcepts] = useState(null)
  const [weakConceptsLoading, setWeakConceptsLoading] = useState(true)
  const [hoveredLecture, setHoveredLecture] = useState(null)
  
  // Repository editing state
  const [isEditingRepository, setIsEditingRepository] = useState(false)
  const [repositoryUrl, setRepositoryUrl] = useState('')
  const [repositorySaving, setRepositorySaving] = useState(false)
  const [repositoryError, setRepositoryError] = useState(null)

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

  // Normalize link for comparison (trim whitespace, remove trailing slash)
  const normalizeLink = (link) => {
    if (!link) return ''
    return link.trim().replace(/\/+$/, '')
  }

  // Check if the link has actually changed
  const hasLinkChanged = () => {
    const currentLink = normalizeLink(course?.course_repository_link)
    const newLink = normalizeLink(repositoryUrl)
    return currentLink !== newLink
  }

  // Handle repository link submission
  const handleRepositorySubmit = async (e) => {
    e.preventDefault()
    
    if (!repositoryUrl.trim()) {
      setRepositoryError('Please enter a valid link')
      return
    }
    
    // Check if the link has actually changed
    if (!hasLinkChanged()) {
      const shouldDiscard = window.confirm(
        "The link hasn't changed. Do you want to discard editing?"
      )
      if (shouldDiscard) {
        cancelEditingRepository()
      }
      return
    }
    
    setRepositorySaving(true)
    setRepositoryError(null)
    
    try {
      // Get user name from auth context (used as fallback if token doesn't have name)
      const userName = user?.displayName || user?.email?.split('@')[0] || 'Anonymous'
      const result = await updateCourseRepository(courseId, repositoryUrl.trim(), userName)
      
      // Update local course state with new repository info
      setCourse(prev => ({
        ...prev,
        course_repository_link: result.course_repository_link,
        repository_created_by: result.repository_created_by
      }))
      
      setIsEditingRepository(false)
      setRepositoryUrl('')
    } catch (err) {
      console.error('Error saving repository:', err)
      setRepositoryError(err.message || 'Failed to save repository link')
    } finally {
      setRepositorySaving(false)
    }
  }

  // Start editing with current value
  const startEditingRepository = () => {
    setRepositoryUrl(course.course_repository_link || '')
    setIsEditingRepository(true)
    setRepositoryError(null)
  }

  // Cancel editing
  const cancelEditingRepository = () => {
    setIsEditingRepository(false)
    setRepositoryUrl('')
    setRepositoryError(null)
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
          {/* Course Repository Section */}
          <div className="course-repository-container">
            {isEditingRepository ? (
              /* Edit Mode: Form to add/edit repository link */
              <form className="repository-form" onSubmit={handleRepositorySubmit}>
                <div className="repository-form-header">
                  <FaFolder className="repository-icon" />
                  <span className="repository-form-title">
                    {course.course_repository_link ? 'Edit Repository Link' : 'Start Community Drive'}
                  </span>
                </div>
                <div className="repository-form-body">
                  <input
                    type="url"
                    className="repository-input"
                    placeholder="Paste your Google Drive, Dropbox, or OneDrive link..."
                    value={repositoryUrl}
                    onChange={(e) => setRepositoryUrl(e.target.value)}
                    disabled={repositorySaving}
                    autoFocus
                  />
                  {repositoryError && (
                    <span className="repository-error">{repositoryError}</span>
                  )}
                  <div className="repository-form-actions">
                    <button 
                      type="button" 
                      className="btn-repository-cancel"
                      onClick={cancelEditingRepository}
                      disabled={repositorySaving}
                    >
                      <FaTimes /> Cancel
                    </button>
                    <button 
                      type="submit" 
                      className="btn-repository-save"
                      disabled={repositorySaving || !repositoryUrl.trim() || !hasLinkChanged()}
                      title={!hasLinkChanged() && repositoryUrl.trim() ? "Make a change to enable Save" : ""}
                    >
                      {repositorySaving ? 'Saving...' : <><FaCheck /> Save Link</>}
                    </button>
                  </div>
                </div>
              </form>
            ) : course.course_repository_link ? (
              /* Existing Link State: Show repository button with attribution */
              <div className="repository-existing">
                <a 
                  href={course.course_repository_link} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="btn-course-repository"
                >
                  <FaFolder className="repository-icon" />
                  <div className="repository-content">
                    <span className="repository-label">Course Repository</span>
                    <span className="repository-description">Community-managed resources • Contribute your own materials</span>
                  </div>
                </a>
                <div className="repository-footer">
                  {course.repository_created_by && (
                    <span className="repository-attribution">
                      Last updated by <strong>{course.repository_created_by}</strong>
                    </span>
                  )}
                  {user && (
                    <button 
                      className="btn-edit-repository"
                      onClick={startEditingRepository}
                      title="Edit repository link"
                    >
                      <FaPencilAlt /> Edit
                    </button>
                  )}
                </div>
              </div>
            ) : (
              /* Empty State: Encourage users to start the community drive */
              <div className="repository-empty">
                <div className="repository-empty-content">
                  <FaPlus className="repository-empty-icon" />
                  <div className="repository-empty-text">
                    <span className="repository-empty-title">Start the Community Drive</span>
                    <span className="repository-empty-description">
                      Be the first to share resources for this course! Add a link to a shared folder.
                    </span>
                  </div>
                </div>
                {user ? (
                  <button 
                    className="btn-start-repository"
                    onClick={startEditingRepository}
                  >
                    Add Repository Link
                  </button>
                ) : (
                  <span className="repository-login-hint">Sign in to add a repository link</span>
                )}
              </div>
            )}
          </div>

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
