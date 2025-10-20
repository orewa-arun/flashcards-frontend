import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import StudyDeck from '../components/StudyDeck'
import { startStudySession, updateStudySession } from '../api/analytics'
import './DeckView.css'

function DeckView() {
  const { courseId, lectureId } = useParams()
  const navigate = useNavigate()
  const [flashcardsData, setFlashcardsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  
  // Track if session has been initialized for this specific deck
  const sessionInitialized = useRef(false)
  const studyStartTime = useRef(null)
  const currentDeckRef = useRef(null)

  // Finish study session
  const finishStudySession = useCallback(async () => {
    if (!sessionId || !studyStartTime.current) return
    
    try {
      const studyDurationSeconds = Math.round((Date.now() - studyStartTime.current) / 1000)
      
      await updateStudySession({
        sessionId,
        studyDurationSeconds
      })
      
      console.log(`Study session completed. Duration: ${studyDurationSeconds}s`)
    } catch (error) {
      console.warn('Failed to update study session:', error)
    }
  }, [sessionId])

  // Handle quiz start
  const handleStartQuiz = useCallback(async () => {
    await finishStudySession()
    
    navigate(`/courses/${courseId}/${lectureId}/quiz`, {
      state: { sessionId }
    })
  }, [finishStudySession, navigate, courseId, lectureId, sessionId])

  // Main effect: Load flashcards and initialize session
  useEffect(() => {
    const deckKey = `${courseId}-${lectureId}`
    
    // Reset state if we're viewing a different deck
    if (currentDeckRef.current !== deckKey) {
      currentDeckRef.current = deckKey
      sessionInitialized.current = false
      setSessionId(null)
      studyStartTime.current = null
      setFlashcardsData(null)
      setLoading(true)
      setError(null)
    }
    
    // Skip if already initialized for this deck
    if (sessionInitialized.current) return
    
    const initializeDeck = async () => {
      try {
        // Load flashcards
        const flashcardsPath = `/courses/${courseId}/cognitive_flashcards/${lectureId}/${lectureId}_cognitive_flashcards.json`
        const response = await fetch(flashcardsPath)
        
        if (!response.ok) {
          throw new Error('Flashcards not found')
        }
        
        const data = await response.json()
        setFlashcardsData(data)
        
        // Start study session
        try {
          const sessionResponse = await startStudySession({
            courseId,
            deckId: lectureId
          })
          
          if (sessionResponse.session_id && 
              sessionResponse.session_id !== 'disabled' && 
              sessionResponse.session_id !== 'error') {
            setSessionId(sessionResponse.session_id)
            studyStartTime.current = Date.now()
            console.log('Study session initialized:', sessionResponse.session_id)
          }
        } catch (sessionError) {
          console.warn('Failed to initialize study session:', sessionError)
        }
        
        setLoading(false)
        sessionInitialized.current = true
      } catch (error) {
        console.error('Error loading flashcards:', error)
        setError(error.message)
        setLoading(false)
      }
    }
    
    initializeDeck()
  }, [courseId, lectureId])

  // Cleanup effect
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (sessionId && studyStartTime.current) {
        const studyDurationSeconds = Math.round((Date.now() - studyStartTime.current) / 1000)
        navigator.sendBeacon(
          'http://localhost:8000/api/v1/analytics/session/update',
          JSON.stringify({
            session_id: sessionId,
            study_duration_seconds: studyDurationSeconds
          })
        )
      }
    }

    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      finishStudySession()
    }
  }, [sessionId, finishStudySession])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading flashcards...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>❌ {error}</h2>
        <p>The flashcards for this lecture might not have been generated yet.</p>
        <button onClick={() => navigate(`/courses/${courseId}`)}>
          ← Back to Course
        </button>
      </div>
    )
  }

  return (
    <div className="deck-view">
      <button className="back-button" onClick={() => navigate(`/courses/${courseId}`)}>
        ← Back to Course
      </button>

      <StudyDeck 
        flashcards={flashcardsData.flashcards} 
        metadata={flashcardsData.metadata}
        onStartQuiz={handleStartQuiz}
        courseId={courseId}
        deckId={lectureId}
        sessionId={sessionId}
      />
    </div>
  )
}

export default DeckView