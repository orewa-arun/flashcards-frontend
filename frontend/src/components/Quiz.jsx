import { useState, useEffect } from 'react'
import './Quiz.css'

function Quiz({ flashcards, onComplete }) {
  const [allQuestions, setAllQuestions] = useState([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
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
          // Filter: Only use MCQ and True/False questions (ignore fill_in_the_blank)
          if (q.type === 'mcq' || q.type === 'true_false') {
            // Sanitize MCQ options to remove duplicates (Pro fix!)
            if (q.type === 'mcq' && q.options && Array.isArray(q.options)) {
              q.options = [...new Set(q.options)]
            }
            questions.push({
              ...q,
              cardContext: card.context,
              cardType: card.type
            })
          }
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

  const handleSubmit = () => {
    if (!userAnswer) return

    // Two-stage flow: Submit Answer → Show Feedback → Next Question
    if (!isAnswerSubmitted) {
      // Stage 1: Submit and check answer
      const correct = checkAnswer()
      setIsCorrect(correct)
      setIsAnswerSubmitted(true)
      
      // Save result
      const result = {
        question: currentQuestion,
        userAnswer,
        isCorrect: correct,
        context: currentQuestion.cardContext
      }
      setResults([...results, result])
    } else {
      // Stage 2: Move to next question
      if (currentQuestionIndex < allQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1)
        setUserAnswer('')
        setIsAnswerSubmitted(false)
        setIsCorrect(false)
      } else {
        onComplete([...results])
      }
    }
  }

  const checkAnswer = () => {
    const correctAnswer = currentQuestion.answer.toString().toLowerCase().trim()
    const userAns = userAnswer.toString().toLowerCase().trim()
    
    if (currentQuestion.type === 'true_false') {
      return correctAnswer === userAns
    } else if (currentQuestion.type === 'fill_in_the_blank') {
      // Case insensitive comparison for fill in the blank
      return correctAnswer === userAns
    } else {
      // MCQ
      return correctAnswer === userAns
    }
  }

  const getOptionClass = (option) => {
    if (!isAnswerSubmitted) return 'mcq-option'
    
    const correctAnswer = currentQuestion.answer
    const isThisCorrect = option === correctAnswer
    const isThisSelected = option === userAnswer
    
    if (isThisCorrect) {
      return 'mcq-option correct'
    }
    if (isThisSelected && !isCorrect) {
      return 'mcq-option incorrect'
    }
    return 'mcq-option'
  }

  const getTFOptionClass = (value) => {
    if (!isAnswerSubmitted) return 'tf-option'
    
    const correctAnswer = currentQuestion.answer.toLowerCase()
    const isThisCorrect = value === correctAnswer
    const isThisSelected = value === userAnswer
    
    if (isThisCorrect) {
      return 'tf-option correct'
    }
    if (isThisSelected && !isCorrect) {
      return 'tf-option incorrect'
    }
    return 'tf-option'
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
        <h2>{currentQuestion.question}</h2>

        {currentQuestion.type === 'mcq' && (
          <div className="mcq-options">
            {currentQuestion.options.map((option, index) => (
              <label key={index} className={getOptionClass(option)}>
                <input
                  type="radio"
                  name="mcq"
                  value={option}
                  checked={userAnswer === option}
                  onChange={(e) => setUserAnswer(e.target.value)}
                  disabled={isAnswerSubmitted}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>
        )}

        {currentQuestion.type === 'fill_in_the_blank' && (
          <div className="fill-input">
            <input
              type="text"
              placeholder="Type your answer here..."
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !isAnswerSubmitted && handleSubmit()}
              disabled={isAnswerSubmitted}
              className={isAnswerSubmitted ? (isCorrect ? 'correct' : 'incorrect') : ''}
            />
            {isAnswerSubmitted && !isCorrect && (
              <div className="correct-answer-display">
                ✓ Correct answer: <strong>{currentQuestion.answer}</strong>
              </div>
            )}
          </div>
        )}

        {currentQuestion.type === 'true_false' && (
          <div className="true-false-options">
            <label className={getTFOptionClass('true')}>
              <input
                type="radio"
                name="tf"
                value="true"
                checked={userAnswer === 'true'}
                onChange={(e) => setUserAnswer(e.target.value)}
                disabled={isAnswerSubmitted}
              />
              <span>True</span>
            </label>
            <label className={getTFOptionClass('false')}>
              <input
                type="radio"
                name="tf"
                value="false"
                checked={userAnswer === 'false'}
                onChange={(e) => setUserAnswer(e.target.value)}
                disabled={isAnswerSubmitted}
              />
              <span>False</span>
            </label>
          </div>
        )}

        <button 
          className="submit-btn"
          onClick={handleSubmit}
          disabled={!userAnswer}
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

