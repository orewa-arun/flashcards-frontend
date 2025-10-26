import { useState, useEffect } from 'react'
import QuestionRenderer from './QuestionRenderer'
import './Quiz.css'

function Quiz({ flashcards, onComplete }) {
  const [allQuestions, setAllQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState(null)
  const [results, setResults] = useState([])
  const [showTransition, setShowTransition] = useState(true)
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false)
  const [isCorrect, setIsCorrect] = useState(false)

  useEffect(() => {
    // Collect all recall questions from all flashcards
    const questions = []
    flashcards.forEach(card => {
      if (card.recall_questions && card.recall_questions.length > 0) {
        card.recall_questions.forEach(q => {
          // Sanitize MCQ options to remove duplicates
          if (q.type === 'mcq' && q.options && Array.isArray(q.options)) {
            q.options = [...new Set(q.options)]
          }
          questions.push({
            ...q,
            cardContext: card.context,
            cardType: card.type
          })
        })
      }
    })
    
    // Shuffle all questions
    const shuffled = questions.sort(() => Math.random() - 0.5)
    
    // Select only 10 random questions to keep the quiz focused
    const selectedQuestions = shuffled.slice(0, 10)
    setAllQuestions(selectedQuestions)

    // Show transition for 2 seconds
    setTimeout(() => setShowTransition(false), 2000)
  }, [flashcards])

  const currentQuestion = allQuestions[currentQuestionIndex]

  // Reset answer when question changes
  useEffect(() => {
    setUserAnswer(null)
  }, [currentQuestionIndex])

  const handleSubmit = () => {
    // Check if user has provided an answer
    if (!userAnswer && userAnswer !== false && userAnswer !== 0) return

    // Two-stage flow: Submit Answer → Show Feedback → Next Question
    if (!isAnswerSubmitted) {
      // Stage 1: Submit and check answer
      const correct = checkAnswer()
      setIsCorrect(correct)
      setIsAnswerSubmitted(true)
      
      // Save result
      const result = {
        question: currentQuestion,
        userAnswer: userAnswer,
        isCorrect: correct,
        context: currentQuestion.cardContext
      }
      setResults([...results, result])
    } else {
      // Stage 2: Move to next question
      if (currentQuestionIndex < allQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setUserAnswer(null)
        setIsAnswerSubmitted(false)
        setIsCorrect(false)
      } else {
        onComplete([...results])
      }
    }
  }

  const checkAnswer = () => {
    const correctAnswer = currentQuestion.answer
    
    // Handle different question types
    switch (currentQuestion.type) {
      case 'sequencing':
        return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
      
      case 'categorization':
        return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer)
      
      case 'matching':
        // Matching answers are arrays of pairs
        if (Array.isArray(userAnswer) && Array.isArray(correctAnswer)) {
          const sortedUser = [...userAnswer].sort()
          const sortedCorrect = [...correctAnswer].sort()
          return JSON.stringify(sortedUser) === JSON.stringify(sortedCorrect)
        }
        return false
      
      case 'true_false':
        return correctAnswer.toString().toLowerCase() === userAnswer.toString().toLowerCase()
      
      case 'fill_in_the_blank':
        return correctAnswer.toString().toLowerCase().trim() === userAnswer.toString().toLowerCase().trim()
      
      case 'mcq':
      case 'scenario_mcq':
      default:
        return correctAnswer.toString().toLowerCase().trim() === userAnswer.toString().toLowerCase().trim()
    }
  }

  if (showTransition) {
    return (
      <div className="quiz-transition">
        <div className="transition-content">
          <h1>🎯 Quiz Time!</h1>
          <p>Get ready to test your knowledge</p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    )
  }

  if (allQuestions.length === 0) {
    return <div className="quiz">No questions available</div>
  }

  return (
    <div className="quiz">
      <div className="quiz-header">
        <h1>📝 Quiz</h1>
        <div className="quiz-progress">
          Question {currentQuestionIndex + 1} of {allQuestions.length}
        </div>
      </div>

      <div className="question-card">
        <div className="question-type-badge">{currentQuestion.type.replace('_', ' ')}</div>
        
        <QuestionRenderer
          question={currentQuestion}
          userAnswer={userAnswer}
          onAnswerChange={setUserAnswer}
          showFeedback={isAnswerSubmitted}
          disabled={isAnswerSubmitted}
        />

        {isAnswerSubmitted && (
          <div className={`feedback-message ${isCorrect ? 'correct-feedback' : 'incorrect-feedback'}`}>
            {isCorrect ? (
              <span>✅ Correct!</span>
            ) : (
              <span>❌ Incorrect</span>
            )}
          </div>
        )}

        <button 
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!userAnswer && userAnswer !== false && userAnswer !== 0}
        >
          {isAnswerSubmitted 
            ? (currentQuestionIndex < allQuestions.length - 1 ? 'Next Question →' : 'Finish Quiz 🎉')
            : 'Submit Answer'
          }
        </button>
      </div>
    </div>
  )
}

export default Quiz

