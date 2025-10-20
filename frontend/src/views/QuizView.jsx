import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { selectQuizFlashcards, selectRandomRecallQuestions, checkAnswer, calculateScore } from '../utils/quizUtils'
import { updateStudySession } from '../api/analytics'
import QuestionRenderer from '../components/QuestionRenderer'
import './QuizView.css'

function QuizView() {
  const { courseId, lectureId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [flashcardsData, setFlashcardsData] = useState(null)
  const [quizQuestions, setQuizQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [quizStartTime, setQuizStartTime] = useState(null)
  const [questionStartTime, setQuestionStartTime] = useState(null)
  
  // Get session ID from navigation state
  const sessionId = location.state?.sessionId

  useEffect(() => {
    // Load flashcards
    const flashcardsPath = `/courses/${courseId}/cognitive_flashcards/${lectureId}/${lectureId}_cognitive_flashcards.json`
    
    fetch(flashcardsPath)
      .then(response => response.json())
      .then(data => {
        setFlashcardsData(data)
        
        // Select quiz flashcards using weighted sampling
        const selectedFlashcards = selectQuizFlashcards(data.flashcards, 10)
        const questions = selectRandomRecallQuestions(selectedFlashcards)
        
        setQuizQuestions(questions)
        setQuizStartTime(Date.now()) // Start timing the quiz
        setQuestionStartTime(Date.now()) // Start timing the first question
        setLoading(false)
      })
      .catch(error => {
        console.error('Error loading flashcards:', error)
        setLoading(false)
      })
  }, [courseId, lectureId])

  const handleSubmitAnswer = () => {
    const currentQuestion = quizQuestions[currentQuestionIndex]
    const isCorrect = checkAnswer(currentQuestion, userAnswer)
    const questionTime = questionStartTime ? Math.round((Date.now() - questionStartTime) / 1000) : 0
    
    const questionResult = {
      question_number: currentQuestionIndex + 1,
      question_type: currentQuestion.type,
      user_answer: userAnswer,
      correct_answer: currentQuestion.answer,
      is_correct: isCorrect,
      time_taken: questionTime
    }
    
    setResults([...results, {
      question: currentQuestion,
      userAnswer,
      isCorrect,
      questionResult // Store for analytics
    }])
    
    setShowFeedback(true)
  }

  const handleNext = async () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
      setUserAnswer(null)
      setShowFeedback(false)
      setQuestionStartTime(Date.now()) // Start timing the next question
    } else {
      // Quiz completed - track results in session
      const totalTime = quizStartTime ? Math.round((Date.now() - quizStartTime) / 1000) : 0
      const correctAnswers = results.filter(r => r.isCorrect).length
      const questionResults = results.map(r => r.questionResult).filter(Boolean)

      // Update session with quiz results
      if (sessionId) {
        await updateStudySession({
          sessionId,
          quizData: {
            score: correctAnswers,
            totalQuestions: quizQuestions.length,
            timeTaken: totalTime,
            questionResults: questionResults
          },
          isCompleted: true
        })
      } else {
        console.warn('No session ID available for quiz completion tracking')
      }

      navigate(`/courses/${courseId}/${lectureId}/results`, {
        state: { 
          results, 
          total: quizQuestions.length,
          sessionId, // Pass session ID to results view for potential summary display
          quizTime: totalTime // Pass total quiz time for database storage
        }
      })
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Preparing your quiz...</p>
      </div>
    )
  }

  if (quizQuestions.length === 0) {
    return (
      <div className="error-container">
        <h2>No quiz questions available</h2>
        <button onClick={() => navigate(`/courses/${courseId}/${lectureId}`)}>
          ← Back to Study
        </button>
      </div>
    )
  }

  const currentQuestion = quizQuestions[currentQuestionIndex]
  const progress = ((currentQuestionIndex + 1) / quizQuestions.length) * 100

  return (
    <div className="quiz-view">
      <div className="quiz-header">
        <button className="back-button" onClick={() => navigate(`/courses/${courseId}/${lectureId}`)}>
          ← Exit Quiz
        </button>
        
        <div className="quiz-progress">
          <span className="question-counter">
            Question {currentQuestionIndex + 1} of {quizQuestions.length}
          </span>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      </div>

      <div className="quiz-content">
        {currentQuestion.flashcardContext && (
          <div className="question-context">
            📚 {currentQuestion.flashcardContext}
          </div>
        )}

        <QuestionRenderer
          question={currentQuestion}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={showFeedback}
          disabled={showFeedback}
        />

        <div className="quiz-actions">
          {!showFeedback ? (
            <button
              className="submit-answer-btn"
              onClick={handleSubmitAnswer}
              disabled={userAnswer === null || userAnswer === undefined}
            >
              Submit Answer
            </button>
          ) : (
            <div className="feedback-section">
              <div className={`feedback-message ${results[results.length - 1].isCorrect ? 'correct' : 'incorrect'}`}>
                {results[results.length - 1].isCorrect ? (
                  <>
                    <span className="feedback-icon">✓</span>
                    <span>Correct!</span>
                  </>
                ) : (
                  <>
                    <span className="feedback-icon">✗</span>
                    <span>Incorrect</span>
                  </>
                )}
              </div>
              
              {!results[results.length - 1].isCorrect && (
                <div className="correct-answer-display">
                  <strong>Correct Answer:</strong>
                  <div className="answer-text">
                    {JSON.stringify(currentQuestion.answer, null, 2).replace(/["{}\[\]]/g, '')}
                  </div>
                </div>
              )}

              <button className="next-question-btn" onClick={handleNext}>
                {currentQuestionIndex < quizQuestions.length - 1 ? 'Next Question →' : 'See Results →'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default QuizView

