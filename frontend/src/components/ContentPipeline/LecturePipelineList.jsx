import { useState, useEffect, useCallback } from 'react'
import { 
  FaSync, 
  FaPlay, 
  FaSpinner, 
  FaCheckCircle, 
  FaTimesCircle, 
  FaClock,
  FaSearch,
  FaBrain,
  FaLayerGroup,
  FaQuestionCircle,
  FaDatabase,
  FaChevronDown,
  FaChevronUp,
  FaExclamationTriangle
} from 'react-icons/fa'
import { contentPipeline } from '../../api/contentPipeline'
import './LecturePipelineList.css'

const PIPELINE_STAGES = [
  { key: 'analysis_status', label: 'Analysis', icon: FaSearch, action: 'analyze' },
  { key: 'flashcard_status', label: 'Flashcards', icon: FaLayerGroup, action: 'flashcards' },
  { key: 'quiz_status', label: 'Quiz', icon: FaQuestionCircle, action: 'quiz' },
  { key: 'qdrant_status', label: 'Indexing', icon: FaDatabase, action: 'index' }
]

const STATUS_CONFIG = {
  pending: { icon: FaClock, className: 'pending', label: 'Pending' },
  in_progress: { icon: FaSpinner, className: 'in-progress', label: 'In Progress' },
  completed: { icon: FaCheckCircle, className: 'completed', label: 'Completed' },
  failed: { icon: FaTimesCircle, className: 'failed', label: 'Failed' }
}

function LecturePipelineList({ refreshTrigger }) {
  const [lectures, setLectures] = useState([])
  const [courses, setCourses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedLectures, setExpandedLectures] = useState(new Set())
  const [actionInProgress, setActionInProgress] = useState({})

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      console.log('Fetching courses and lectures...')
      
      // Fetch courses first
      let coursesData = []
      try {
        coursesData = await contentPipeline.getCourses()
        console.log('Courses:', coursesData)
      } catch (courseErr) {
        console.error('Error fetching courses:', courseErr)
        // Don't fail completely, just log and continue
      }
      
      // Fetch lectures
      let lecturesData = []
      try {
        lecturesData = await contentPipeline.getLectures(selectedCourse || null)
        console.log('Lectures:', lecturesData)
      } catch (lectureErr) {
        console.error('Error fetching lectures:', lectureErr)
        throw lectureErr // Re-throw to show error
      }
      
      setCourses(coursesData || [])
      setLectures(lecturesData || [])
    } catch (err) {
      console.error('Error fetching data:', err)
      setError(err.message || 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }, [selectedCourse])

  useEffect(() => {
    fetchData()
  }, [fetchData, refreshTrigger])

  const toggleLectureExpansion = (lectureId) => {
    const newExpanded = new Set(expandedLectures)
    if (newExpanded.has(lectureId)) {
      newExpanded.delete(lectureId)
    } else {
      newExpanded.add(lectureId)
    }
    setExpandedLectures(newExpanded)
  }

  const canTriggerAction = (lecture, stageIndex) => {
    const currentStage = PIPELINE_STAGES[stageIndex]
    const currentStatus = lecture[currentStage.key]
    
    // Can't trigger if already in progress
    if (currentStatus === 'in_progress') {
      return false
    }
    
    // First stage (Analysis) can always be triggered/retried
    if (stageIndex === 0) {
      return true
    }
    
    // For other stages: can trigger if previous stage is completed
    // AND current stage is not in_progress
    const previousStage = PIPELINE_STAGES[stageIndex - 1]
    const previousStatus = lecture[previousStage.key]
    
    return previousStatus === 'completed'
  }

  const handleTriggerAction = async (lectureId, action, stageKey) => {
    const actionKey = `${lectureId}-${action}`
    setActionInProgress(prev => ({ ...prev, [actionKey]: true }))
    
    try {
      await contentPipeline.triggerAction(action, lectureId)
      // Refresh data after action
      await fetchData()
    } catch (err) {
      console.error(`Failed to trigger ${action}:`, err)
      // Show error in the lecture's error_log field temporarily
      setLectures(prev => prev.map(l => 
        l.id === lectureId 
          ? { ...l, error_log: err.message }
          : l
      ))
    } finally {
      setActionInProgress(prev => ({ ...prev, [actionKey]: false }))
    }
  }

  const renderStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
    const Icon = config.icon
    
    return (
      <span className={`status-badge ${config.className}`}>
        <Icon className={status === 'in_progress' ? 'spinning' : ''} />
        {config.label}
      </span>
    )
  }

  const renderActionButton = (lecture, stage, stageIndex) => {
    const actionKey = `${lecture.id}-${stage.action}`
    const isLoading = actionInProgress[actionKey]
    const canTrigger = canTriggerAction(lecture, stageIndex)
    const status = lecture[stage.key]
    
    // Don't show button if in progress (handled by status badge)
    if (status === 'in_progress') {
      return null
    }

    // Determine button style based on status
    let btnClass = 'run'
    let btnText = 'Run'
    
    if (status === 'failed') {
      btnClass = 'retry-failed'
      btnText = 'Retry'
    } else if (status === 'completed') {
      btnClass = 'retry'
      btnText = 'Retry'
    }

    return (
      <button
        className={`action-btn ${btnClass}`}
        onClick={() => handleTriggerAction(lecture.id, stage.action, stage.key)}
        disabled={!canTrigger || isLoading}
        title={!canTrigger ? 'Complete previous stage first' : `${btnText} ${stage.label}`}
      >
        {isLoading ? (
          <FaSpinner className="spinning" />
        ) : (
          <FaPlay />
        )}
        {btnText}
      </button>
    )
  }

  const renderErrorLog = (errorLog) => {
    if (!errorLog) return null

    let displayText = ''

    if (typeof errorLog === 'string') {
      displayText = errorLog
    } else {
      try {
        displayText = JSON.stringify(errorLog, null, 2)
      } catch (e) {
        displayText = String(errorLog)
      }
    }

    return (
      <div className="error-log">
        <strong>Error Log:</strong>
        <pre>{displayText}</pre>
      </div>
    )
  }

  if (loading && lectures.length === 0) {
    return (
      <div className="pipeline-list-container">
        <div className="loading-state">
          <FaSpinner className="spinning large" />
          <p>Loading lectures...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="pipeline-list-container">
      <div className="list-header">
        <h2>
          <FaBrain className="header-icon" />
          Content Pipeline
        </h2>
        <div className="header-controls">
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="course-filter"
          >
            <option value="">All Courses</option>
            {courses.map(course => (
              <option key={course.id} value={course.course_code}>
                {course.course_name} ({course.course_code})
              </option>
            ))}
          </select>
          <button 
            className="refresh-btn" 
            onClick={fetchData}
            disabled={loading}
          >
            <FaSync className={loading ? 'spinning' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="list-error">
          <FaExclamationTriangle />
          {error}
        </div>
      )}

      {lectures.length === 0 ? (
        <div className="empty-state">
          <FaLayerGroup className="empty-icon" />
          <p>No lectures found. Upload some PDFs to get started!</p>
        </div>
      ) : (
        <div className="lectures-list">
          {lectures.map(lecture => (
            <div key={lecture.id} className="lecture-card">
              <div 
                className="lecture-header"
                onClick={() => toggleLectureExpansion(lecture.id)}
              >
                <div className="lecture-info">
                  <span className="lecture-title">{lecture.lecture_title}</span>
                  <span className="lecture-course">{lecture.course_code}</span>
                </div>
                <div className="lecture-status-summary">
                  {PIPELINE_STAGES.map(stage => {
                    const status = lecture[stage.key]
                    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
                    const Icon = config.icon
                    return (
                      <span 
                        key={stage.key} 
                        className={`status-dot ${config.className}`}
                        title={`${stage.label}: ${config.label}`}
                      >
                        <Icon className={status === 'in_progress' ? 'spinning' : ''} />
                      </span>
                    )
                  })}
                  {expandedLectures.has(lecture.id) ? <FaChevronUp /> : <FaChevronDown />}
                </div>
              </div>

              {expandedLectures.has(lecture.id) && (
                <div className="lecture-details">
                  <div className="pipeline-stages">
                    {PIPELINE_STAGES.map((stage, index) => {
                      const StageIcon = stage.icon
                      const status = lecture[stage.key]
                      return (
                        <div key={stage.key} className="pipeline-stage">
                          <div className="stage-info">
                            <StageIcon className="stage-icon" />
                            <span className="stage-label">{stage.label}</span>
                          </div>
                          <div className="stage-status">
                            {renderStatusBadge(status)}
                            {renderActionButton(lecture, stage, index)}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {renderErrorLog(lecture.error_log)}

                  <div className="lecture-meta">
                    <span>ID: {lecture.id}</span>
                    <span>Created: {new Date(lecture.created_at).toLocaleString()}</span>
                    {lecture.updated_at && (
                      <span>Updated: {new Date(lecture.updated_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default LecturePipelineList

