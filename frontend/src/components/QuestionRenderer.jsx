import { useState } from 'react'
import './QuestionRenderer.css'

function QuestionRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  
  if (!question) return null

  switch (question.type) {
    case 'mcq':
    case 'scenario_mcq':
      return (
        <MCQRenderer 
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'sequencing':
      return (
        <SequencingRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'categorization':
      return (
        <CategorizationRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'matching':
      return (
        <MatchingRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'fill_in_the_blank':
      return (
        <FillInTheBlankRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    case 'true_false':
      return (
        <TrueFalseRenderer
          question={question}
          userAnswer={userAnswer}
          onAnswerChange={onAnswerChange}
          showFeedback={showFeedback}
          disabled={disabled}
        />
      )
    
    default:
      return <div>Unknown question type: {question.type}</div>
  }
}

// MCQ and Scenario MCQ Renderer
function MCQRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  return (
    <div className="question-container mcq-question">
      {question.scenario && (
        <div className="scenario-box">
          <strong>Scenario:</strong>
          <p>{question.scenario}</p>
        </div>
      )}
      
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="options-list">
        {question.options && question.options.map((option, index) => (
          <div 
            key={index}
            className={`option-item ${userAnswer === option ? 'selected' : ''} ${
              showFeedback && option === question.answer ? 'correct' : ''
            } ${showFeedback && userAnswer === option && option !== question.answer ? 'incorrect' : ''}`}
            onClick={() => !disabled && onAnswerChange(option)}
          >
            <div className="option-content">
              {option}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Sequencing Renderer
// eslint-disable-next-line no-unused-vars
function SequencingRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [items, setItems] = useState(userAnswer || [...(question.items || [])])
  
  const moveItem = (fromIndex, toIndex) => {
    if (disabled) return
    const newItems = [...items]
    const [removed] = newItems.splice(fromIndex, 1)
    newItems.splice(toIndex, 0, removed)
    setItems(newItems)
    onAnswerChange(newItems)
  }

  return (
    <div className="question-container sequencing-question">
      <div className="question-text">
        <h3>{question.question}</h3>
        <p className="instruction">Drag to reorder or use arrows to arrange in correct sequence</p>
      </div>
      
      <div className="sequencing-list">
        {items.map((item, index) => (
          <div key={index} className="sequence-item">
            <span className="sequence-number">{index + 1}</span>
            <span className="sequence-content">{item}</span>
            <div className="sequence-controls">
              <button
                onClick={() => moveItem(index, Math.max(0, index - 1))}
                disabled={disabled || index === 0}
                className="move-btn"
              >
                ▲
              </button>
              <button
                onClick={() => moveItem(index, Math.min(items.length - 1, index + 1))}
                disabled={disabled || index === items.length - 1}
                className="move-btn"
              >
                ▼
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Categorization Renderer
// eslint-disable-next-line no-unused-vars
function CategorizationRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [categorization, setCategorization] = useState(userAnswer || {})
  
  const handleCategoryChange = (item, category) => {
    if (disabled) return
    const newCategorization = { ...categorization }
    
    // Remove item from all categories
    Object.keys(newCategorization).forEach(cat => {
      newCategorization[cat] = (newCategorization[cat] || []).filter(i => i !== item)
    })
    
    // Add to new category
    if (!newCategorization[category]) {
      newCategorization[category] = []
    }
    newCategorization[category].push(item)
    
    setCategorization(newCategorization)
    onAnswerChange(newCategorization)
  }

  const getItemCategory = (item) => {
    for (const cat of question.categories || []) {
      if ((categorization[cat] || []).includes(item)) {
        return cat
      }
    }
    return null
  }

  return (
    <div className="question-container categorization-question">
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="categorization-grid">
        <div className="items-list">
          <h4>Items to Categorize:</h4>
          {question.items && question.items.map((item, index) => (
            <div key={index} className="cat-item">
              <span>{item}</span>
              <select
                value={getItemCategory(item) || ''}
                onChange={(e) => handleCategoryChange(item, e.target.value)}
                disabled={disabled}
                className="category-select"
              >
                <option value="">Select category...</option>
                {question.categories && question.categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
        
        <div className="categories-display">
          {question.categories && question.categories.map(category => (
            <div key={category} className="category-box">
              <h4>{category}</h4>
              <div className="category-items">
                {(categorization[category] || []).map((item, idx) => (
                  <div key={idx} className="categorized-item">{item}</div>
                ))}
                {(!categorization[category] || categorization[category].length === 0) && (
                  <div className="empty-category">No items yet</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Matching Renderer
// eslint-disable-next-line no-unused-vars
function MatchingRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const [matches, setMatches] = useState(userAnswer || [])
  
  const handleMatch = (premise, response) => {
    if (disabled) return
    const premiseNum = premise.split('.')[0]
    // The response is the full text, no need to split
    const matchPair = `${premiseNum}-${response.split('.')[0]}`
    
    // Remove any existing match for this premise
    const newMatches = matches.filter(m => !m.startsWith(premiseNum + '-'))
    newMatches.push(matchPair)
    
    setMatches(newMatches)
    // Pass up the full response text for checking
    const answerForCheck = newMatches.map(match => {
      const [pNum, rLetter] = match.split('-')
      const fullResponse = question.responses.find(r => r.startsWith(rLetter + '.'))
      return `${pNum}-${rLetter}`
    }).sort()

    onAnswerChange(answerForCheck)
  }

  const getMatchForPremise = (premise) => {
    const premiseNum = premise.split('.')[0]
    const match = matches.find(m => m.startsWith(premiseNum + '-'))
    if (!match) return null
    
    const responseLetter = match.split('-')[1]
    return question.responses.find(r => r.startsWith(responseLetter + '.'))
  }

  return (
    <div className="question-container matching-question">
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="matching-grid">
        <div className="premises-column">
          <h4>Match these:</h4>
          {question.premises && question.premises.map((premise, index) => (
            <div key={index} className="premise-item">
              <span className="premise-text">{premise}</span>
              <select
                value={getMatchForPremise(premise) || ''}
                onChange={(e) => handleMatch(premise, e.target.value)}
                disabled={disabled}
                className="match-select"
              >
                <option value="">Select match...</option>
                {question.responses && question.responses.map((response, idx) => (
                  <option key={idx} value={response}>{response}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </div>
      
      <div className="matches-summary">
        <h4>Your Matches:</h4>
        {matches.length > 0 ? (
          <div className="matches-list">
            {matches.map((match, idx) => (
              <span key={idx} className="match-pair">{match}</span>
            ))}
          </div>
        ) : (
          <p>No matches selected yet</p>
        )}
      </div>
    </div>
  )
}

// Fill in the Blank Renderer
function FillInTheBlankRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const parts = question.question.split('________')
  
  return (
    <div className="question-container fill-in-the-blank-question">
      <div className="question-text">
        <h3>
          {parts.map((part, index) => (
            <span key={index}>
              {part}
              {index < parts.length - 1 && (
                <input
                  type="text"
                  value={userAnswer || ''}
                  onChange={(e) => onAnswerChange(e.target.value)}
                  disabled={disabled}
                  className={`blank-input ${showFeedback ? (userAnswer?.trim().toLowerCase() === question.answer.trim().toLowerCase() ? 'correct' : 'incorrect') : ''}`}
                  placeholder="Type your answer"
                />
              )}
            </span>
          ))}
        </h3>
      </div>
      
      {showFeedback && userAnswer?.trim().toLowerCase() !== question.answer.trim().toLowerCase() && (
        <div className="correct-answer-hint">
          <strong>Correct Answer:</strong> {question.answer}
        </div>
      )}
    </div>
  )
}

// True/False Renderer
function TrueFalseRenderer({ question, userAnswer, onAnswerChange, showFeedback, disabled }) {
  const options = ['True', 'False']
  
  return (
    <div className="question-container true-false-question">
      <div className="question-text">
        <h3>{question.question}</h3>
      </div>
      
      <div className="true-false-options">
        {options.map((option) => (
          <button
            key={option}
            className={`true-false-btn ${userAnswer === option ? 'selected' : ''} ${
              showFeedback && option === question.answer ? 'correct' : ''
            } ${showFeedback && userAnswer === option && option !== question.answer ? 'incorrect' : ''}`}
            onClick={() => !disabled && onAnswerChange(option)}
            disabled={disabled}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuestionRenderer

