import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { generateQuiz, submitQuiz } from '../api/quiz';
import './QuizView.css';

function QuizView() {
  const { courseId, deckId, lectureId } = useParams();
  const navigate = useNavigate();
  
  // Handle both deckId and lectureId parameter names
  const actualDeckId = deckId || lectureId;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Quiz state
  const [quizData, setQuizData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [quizStartTime, setQuizStartTime] = useState(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [currentAnswerCorrect, setCurrentAnswerCorrect] = useState(false);
  
  // Checkpoint state
  const [showCheckpoint, setShowCheckpoint] = useState(false);
  const [checkpointScore, setCheckpointScore] = useState({ correct: 0, total: 0 });
  
  // Results state
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const loadQuiz = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await generateQuiz(courseId, actualDeckId, 20);
      setQuizData(data);
      setQuizStartTime(Date.now());
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to load quiz');
      setLoading(false);
    }
  }, [courseId, actualDeckId]);

  useEffect(() => {
    loadQuiz();
  }, [loadQuiz]);

  const handleAnswerChange = (questionId, answer) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmitAnswer = () => {
    const currentQuestion = quizData.questions[currentQuestionIndex];
    const userAnswer = userAnswers[currentQuestion.question_id];
    
    if (!userAnswer) return; // Don't submit if no answer
    
    // Check if answer is correct and show feedback
    const isCorrect = compareAnswers(userAnswer, currentQuestion.correct_answer, currentQuestion.question_type);
    setCurrentAnswerCorrect(isCorrect);
    setShowFeedback(true);
  };

  const calculateCurrentScore = () => {
    if (!quizData) return { correct: 0, total: 0 };
    
    let correct = 0;
    const answeredQuestions = quizData.questions.slice(0, currentQuestionIndex + 1);
    
    for (const question of answeredQuestions) {
      const userAnswer = userAnswers[question.question_id];
      if (userAnswer && compareAnswers(userAnswer, question.correct_answer, question.question_type)) {
        correct++;
      }
    }
    
    return { correct, total: answeredQuestions.length };
  };

  const compareAnswers = (userAnswer, correctAnswer, questionType) => {
    if (!userAnswer) return false;
    
    if (questionType === 'mcq' || questionType === 'scenario_mcq') {
      return userAnswer.trim() === correctAnswer.trim();
    } else if (questionType === 'sequencing') {
      return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer);
    } else if (questionType === 'categorization') {
      return JSON.stringify(userAnswer) === JSON.stringify(correctAnswer);
    } else if (questionType === 'matching') {
      if (!Array.isArray(userAnswer) || !Array.isArray(correctAnswer)) return false;
      const userSet = new Set(userAnswer.map(a => String(a).trim()));
      const correctSet = new Set(correctAnswer.map(a => String(a).trim()));
      if (userSet.size !== correctSet.size) return false;
      for (let item of userSet) {
        if (!correctSet.has(item)) return false;
      }
      return true;
    }
    
    return userAnswer === correctAnswer;
  };

  const formatCorrectAnswer = (question) => {
    const { correct_answer, question_type } = question;
    
    if (question_type === 'mcq' || question_type === 'scenario_mcq') {
      return correct_answer;
    } else if (question_type === 'sequencing') {
      return correct_answer.map((item, idx) => `${idx + 1}. ${item}`).join(' → ');
    } else if (question_type === 'categorization') {
      return Object.entries(correct_answer)
        .map(([cat, items]) => `${cat}: ${items.join(', ')}`)
        .join(' | ');
    } else if (question_type === 'matching') {
      return correct_answer.join(', ');
    }
    
    return String(correct_answer);
  };

  const checkForCheckpoint = (nextIndex) => {
    // Show checkpoint at questions 15 and 20
    if (nextIndex === 15 || nextIndex === 20) {
      const score = calculateCurrentScore();
      setCheckpointScore(score);
      setShowCheckpoint(true);
      return true;
    }
    return false;
  };

  const handleNext = () => {
    const nextIndex = currentQuestionIndex + 1;
    
    // Reset feedback for next question
    setShowFeedback(false);
    setCurrentAnswerCorrect(false);
    
    if (nextIndex >= quizData.questions.length) {
      // Quiz complete - submit
      handleSubmitQuiz();
    } else {
      // Check for checkpoint
      if (!checkForCheckpoint(nextIndex)) {
        setCurrentQuestionIndex(nextIndex);
      }
    }
  };

  const handleContinueFromCheckpoint = () => {
    setShowCheckpoint(false);
    setCurrentQuestionIndex(currentQuestionIndex + 1);
  };

  const handleReturnToFlashcards = () => {
    navigate(`/courses/${courseId}/${actualDeckId}`);
  };

  const handleSubmitQuiz = async () => {
    try {
      setSubmitting(true);
      
      // Calculate time taken
      const timeTakenSeconds = Math.floor((Date.now() - quizStartTime) / 1000);
      
      // Format answers for submission
      const answers = quizData.questions.map(q => ({
        question_id: q.question_id,
        user_answer: userAnswers[q.question_id] || null
      }));
      
      const results = await submitQuiz(
        quizData.quiz_id,
        courseId,
        actualDeckId,
        answers,
        timeTakenSeconds
      );
      
      setQuizResults(results);
      setQuizCompleted(true);
      setSubmitting(false);
    } catch (err) {
      setError(err.message || 'Failed to submit quiz');
      setSubmitting(false);
    }
  };

  const renderQuestion = (question) => {
    const userAnswer = userAnswers[question.question_id];
    
    switch (question.question_type) {
      case 'mcq':
      case 'scenario_mcq':
        return (
          <div className="question-content">
            {question.scenario && (
              <div className="scenario-box">
                <h4>Scenario:</h4>
                <p>{question.scenario}</p>
              </div>
            )}
            <h3 className="question-text">{question.question}</h3>
            <div className="options-list">
              {question.options.map((option, idx) => (
                <label key={idx} className="option-item">
                  <input
                    type="radio"
                    name={`question-${question.question_id}`}
                    value={option}
                    checked={userAnswer === option}
                    onChange={(e) => handleAnswerChange(question.question_id, e.target.value)}
                  />
                  <span className="option-text">{option}</span>
                </label>
              ))}
            </div>
          </div>
        );
      
      case 'sequencing':
        return (
          <div className="question-content">
            <h3 className="question-text">{question.question}</h3>
            <SequencingQuestion
              items={question.items}
              userAnswer={userAnswer}
              onChange={(answer) => handleAnswerChange(question.question_id, answer)}
            />
          </div>
        );
      
      case 'categorization':
        return (
          <div className="question-content">
            <h3 className="question-text">{question.question}</h3>
            <CategorizationQuestion
              items={question.items}
              categories={question.categories}
              userAnswer={userAnswer}
              onChange={(answer) => handleAnswerChange(question.question_id, answer)}
            />
          </div>
        );
      
      case 'matching':
        return (
          <div className="question-content">
            <h3 className="question-text">{question.question}</h3>
            <MatchingQuestion
              premises={question.premises}
              responses={question.responses}
              userAnswer={userAnswer}
              onChange={(answer) => handleAnswerChange(question.question_id, answer)}
            />
          </div>
        );
      
      default:
        return <p>Unknown question type: {question.question_type}</p>;
    }
  };

  if (loading) {
    return (
      <div className="quiz-view loading">
        <div className="spinner"></div>
        <p>Generating your personalized quiz...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="quiz-view error">
        <h2>Error Loading Quiz</h2>
        <p>{error}</p>
        <button onClick={() => navigate(`/${courseId}/${actualDeckId}`)} className="btn-primary">
          Return to Flashcards
        </button>
      </div>
    );
  }

  if (quizCompleted && quizResults) {
    return <QuizResults results={quizResults} questions={quizData.questions} courseId={courseId} deckId={actualDeckId} />;
  }

  if (showCheckpoint) {
    return (
      <CheckpointDialog
        currentQuestion={currentQuestionIndex}
        score={checkpointScore}
        onContinue={handleContinueFromCheckpoint}
        onReturnToFlashcards={handleReturnToFlashcards}
      />
    );
  }

  if (!quizData || quizData.questions.length === 0) {
    return (
      <div className="quiz-view error">
        <h2>No Questions Available</h2>
        <p>Unable to generate quiz questions for this deck.</p>
        <button onClick={() => navigate(`/${courseId}/${actualDeckId}`)} className="btn-primary">
          Return to Flashcards
        </button>
      </div>
    );
  }

  const currentQuestion = quizData.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / quizData.questions.length) * 100;

  return (
    <div className="quiz-view">
      <div className="quiz-header">
        <button onClick={() => navigate(`/courses/${courseId}/${actualDeckId}`)} className="btn-back">
          ← Back to Flashcards
        </button>
        <div className="quiz-info">
          <h2>Quiz - Attempt #{quizData.quiz_attempt_number}</h2>
          <p className="question-counter">
            Question {currentQuestionIndex + 1} of {quizData.questions.length}
          </p>
        </div>
      </div>

      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${progress}%` }}></div>
      </div>

      <div className="quiz-content">
        <div className="concept-badge">
          <span className="concept-name">{currentQuestion.concept_context}</span>
        </div>

        {renderQuestion(currentQuestion)}

        {showFeedback && (
          <div className={`feedback-box ${currentAnswerCorrect ? 'correct' : 'incorrect'}`}>
            <div className="feedback-icon">
              {currentAnswerCorrect ? '✓' : '✗'}
            </div>
            <div className="feedback-content">
              <h4>{currentAnswerCorrect ? 'Correct!' : 'Incorrect'}</h4>
              {!currentAnswerCorrect && (
                <div className="correct-answer-display">
                  <p><strong>Correct answer:</strong></p>
                  <p className="answer-text">{formatCorrectAnswer(currentQuestion)}</p>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="quiz-navigation">
          {!showFeedback ? (
            <button
              onClick={handleSubmitAnswer}
              disabled={!userAnswers[currentQuestion.question_id]}
              className="btn-submit"
            >
              Submit Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="btn-primary"
            >
              {currentQuestionIndex === quizData.questions.length - 1 ? 'Finish Quiz' : 'Next Question'}
            </button>
          )}
        </div>
      </div>

      {submitting && (
        <div className="submitting-overlay">
          <div className="spinner"></div>
          <p>Submitting your quiz...</p>
          </div>
        )}
    </div>
  );
}

// Sequencing Question Component
function SequencingQuestion({ items, userAnswer, onChange }) {
  const [orderedItems, setOrderedItems] = useState(userAnswer || [...items]);
  const [draggedIndex, setDraggedIndex] = useState(null);

  // Reset items when the items prop changes (new question)
  useEffect(() => {
    setOrderedItems(userAnswer || [...items]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items]);

  useEffect(() => {
    onChange(orderedItems);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderedItems]);

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.currentTarget);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === index) return;
    
    const newItems = [...orderedItems];
    const draggedItem = newItems[draggedIndex];
    
    // Remove dragged item
    newItems.splice(draggedIndex, 1);
    
    // Insert at new position
    newItems.splice(index, 0, draggedItem);
    
    setOrderedItems(newItems);
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  return (
    <div className="sequencing-question">
      <p className="instruction">Drag items to reorder them:</p>
      {orderedItems.map((item, idx) => (
        <div
          key={`${item}-${idx}`}
          className={`sequence-item ${draggedIndex === idx ? 'dragging' : ''}`}
          draggable
          onDragStart={(e) => handleDragStart(e, idx)}
          onDragOver={(e) => handleDragOver(e, idx)}
          onDragEnd={handleDragEnd}
        >
          <span className="drag-handle">⋮⋮</span>
          <span className="sequence-number">{idx + 1}</span>
          <span className="sequence-text">{item}</span>
        </div>
      ))}
    </div>
  );
}

// Categorization Question Component
function CategorizationQuestion({ items, categories, userAnswer, onChange }) {
  // Initialize categorization with all categories, merging with userAnswer if provided
  const [categorization, setCategorization] = useState(() => {
    const initial = categories.reduce((acc, cat) => ({ ...acc, [cat]: [] }), {});
    if (userAnswer) {
      // Merge userAnswer with initial structure to ensure all categories exist
      Object.keys(userAnswer).forEach(cat => {
        if (cat in initial) {
          initial[cat] = userAnswer[cat];
        }
      });
    }
    return initial;
  });

  // Reset categorization when items or categories change (new question)
  useEffect(() => {
    const initial = categories.reduce((acc, cat) => ({ ...acc, [cat]: [] }), {});
    if (userAnswer) {
      Object.keys(userAnswer).forEach(cat => {
        if (cat in initial) {
          initial[cat] = userAnswer[cat];
        }
      });
    }
    setCategorization(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items, categories]);

  useEffect(() => {
    onChange(categorization);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categorization]);

  const handleDrop = (item, category) => {
    // Remove item from all categories
    const newCategorization = {};
    for (const cat of categories) {
      newCategorization[cat] = (categorization[cat] || []).filter(i => i !== item);
    }
    
    // Add item to target category
    newCategorization[category] = [...(newCategorization[category] || []), item];
    
    setCategorization(newCategorization);
  };

  const getUnassignedItems = () => {
    const assigned = new Set();
    for (const cat of categories) {
      if (categorization[cat]) {
        categorization[cat].forEach(item => assigned.add(item));
      }
    }
    return items.filter(item => !assigned.has(item));
  };

  const unassigned = getUnassignedItems();

  return (
    <div className="categorization-question">
      <div className="unassigned-items">
        <h4>Items to categorize:</h4>
        <div className="items-pool">
          {unassigned.map((item, idx) => (
            <div key={idx} className="categorization-item">
              {item}
              <div className="category-buttons">
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => handleDrop(item, cat)}
                    className="btn-category"
                  >
                    → {cat}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
              </div>
              
      <div className="categories-container">
        {categories.map(category => (
          <div key={category} className="category-box">
            <h4>{category}</h4>
            <div className="category-items">
              {(categorization[category] || []).map((item, idx) => (
                <div key={idx} className="assigned-item">
                  {item}
                  <button
                    onClick={() => {
                      const newCat = { ...categorization };
                      newCat[category] = (newCat[category] || []).filter(i => i !== item);
                      setCategorization(newCat);
                    }}
                    className="btn-remove"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Matching Question Component
function MatchingQuestion({ premises, responses, userAnswer, onChange }) {
  const [matches, setMatches] = useState(userAnswer || []);

  // Reset matches when premises or responses change (new question)
  useEffect(() => {
    setMatches(userAnswer || []);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [premises, responses]);

  useEffect(() => {
    onChange(matches);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matches]);

  const handleMatch = (premiseIdx, responseIdx) => {
    const premiseNum = premiseIdx + 1;
    const responseLetter = String.fromCharCode(65 + responseIdx); // 65 = 'A'
    const matchPair = `${premiseNum}-${responseLetter}`;
    
    // Check if this exact match already exists (to toggle it off)
    if (matches.includes(matchPair)) {
      // Remove the match (deselect)
      const newMatches = matches.filter(m => m !== matchPair);
      setMatches(newMatches.sort());
    } else {
      // Remove any existing match for this premise
      const newMatches = matches.filter(m => !m.startsWith(`${premiseNum}-`));
      
      // Add the new match
      newMatches.push(matchPair);
      
      setMatches(newMatches.sort());
    }
  };

  const getSelectedResponse = (premiseIdx) => {
    const premiseNum = premiseIdx + 1;
    const match = matches.find(m => m.startsWith(`${premiseNum}-`));
    if (match) {
      const responseLetter = match.split('-')[1];
      return responseLetter.charCodeAt(0) - 65; // Convert back to index
    }
    return null;
  };

  const clearMatch = (premiseIdx) => {
    const premiseNum = premiseIdx + 1;
    const newMatches = matches.filter(m => !m.startsWith(`${premiseNum}-`));
    setMatches(newMatches);
  };

  return (
    <div className="matching-question">
      <p className="instruction">Match each premise with the correct response:</p>
      
      <div className="matching-content">
        <div className="premises-column">
          <h4>Premises</h4>
          {premises && premises.map((premise, idx) => (
            <div key={idx} className="premise-item">
              <div className="premise-text">{premise}</div>
              <div className="premise-match">
                {getSelectedResponse(idx) !== null ? (
                  <div className="selected-match">
                    → {String.fromCharCode(65 + getSelectedResponse(idx))}
            <button
                      onClick={() => clearMatch(idx)}
                      className="btn-clear-match"
            >
                      ×
            </button>
                  </div>
                ) : (
                  <span className="no-match">Select response →</span>
                )}
              </div>
            </div>
          ))}
              </div>
              
        <div className="responses-column">
          <h4>Responses</h4>
          {responses && responses.map((response, idx) => {
            const responseLetter = String.fromCharCode(65 + idx);
            return (
              <div key={idx} className="response-item">
                <div className="response-label">{responseLetter}.</div>
                <div className="response-text">{response}</div>
                <div className="response-buttons">
                  {premises && premises.map((_, premiseIdx) => (
                    <button
                      key={premiseIdx}
                      onClick={() => handleMatch(premiseIdx, idx)}
                      className={`btn-match ${getSelectedResponse(premiseIdx) === idx ? 'selected' : ''}`}
                    >
                      {premiseIdx + 1}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="matches-summary">
        <h4>Your Matches:</h4>
        <div className="matches-list">
          {matches.length > 0 ? (
            matches.map((match, idx) => (
              <span key={idx} className="match-badge">{match}</span>
            ))
          ) : (
            <span className="no-matches">No matches selected yet</span>
          )}
        </div>
      </div>
    </div>
  );
}

// Checkpoint Dialog Component
function CheckpointDialog({ currentQuestion, score, onContinue, onReturnToFlashcards }) {
  const accuracy = score.total > 0 ? (score.correct / score.total) * 100 : 0;
  const shouldSuggestBreak = accuracy < 70;

  return (
    <div className="checkpoint-overlay">
      <div className="checkpoint-dialog">
        <h2>🎯 Checkpoint Reached!</h2>
        <p className="checkpoint-question">You've completed {currentQuestion} questions</p>
        
        <div className="checkpoint-score">
          <div className="score-display">
            <span className="score-number">{score.correct}/{score.total}</span>
            <span className="score-label">Correct</span>
          </div>
          <div className="accuracy-display">
            <span className="accuracy-number">{accuracy.toFixed(1)}%</span>
            <span className="accuracy-label">Accuracy</span>
          </div>
                  </div>

        {shouldSuggestBreak && (
          <div className="suggestion-box warning">
            <p>💡 <strong>Suggestion:</strong> If you're finding this challenging, it might be a good time to pause, review the flashcards, and come back when you're ready.</p>
                </div>
              )}

        {!shouldSuggestBreak && (
          <div className="suggestion-box success">
            <p>🌟 <strong>Great job!</strong> You're doing well. Keep up the good work!</p>
            </div>
          )}

        <div className="checkpoint-actions">
          <button onClick={onReturnToFlashcards} className="btn-secondary">
            Review Flashcards
          </button>
          <button onClick={onContinue} className="btn-primary">
            Continue Quiz
          </button>
        </div>
      </div>
    </div>
  );
}

// Quiz Results Component
function QuizResults({ results, questions, courseId, deckId }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('breakdown');
  
  // Debug logging
  // Uncomment below for debugging
  // console.log('=== QuizResults Debug ===');
  // console.log('Results:', results);
  // console.log('Questions:', questions);
  // console.log('Question IDs from questions:', questions?.map(q => q.question_id));
  // console.log('Question IDs from results:', results?.question_results?.map(r => r.question_id));
  
  // Create a map for quick question lookup
  const questionMap = new Map(questions.map(q => [q.question_id, q]));
  
  const formatAnswer = (answer, questionType) => {
    if (answer === null || answer === undefined) {
      return <span className="no-answer">Not answered</span>;
    }
    
    if (questionType === 'sequencing') {
      return (
        <ol className="answer-list">
          {answer.map((item, idx) => <li key={idx}>{item}</li>)}
        </ol>
      );
    }
    
    if (questionType === 'matching') {
      return (
        <div className="answer-matches">
          {answer.map(match => <span key={match} className="match-badge-small">{match}</span>)}
        </div>
      );
    }
    
    if (questionType === 'categorization') {
      return (
        <ul className="answer-list-cats">
          {Object.entries(answer).map(([cat, items]) => (
            <li key={cat}><strong>{cat}:</strong> {items.join(', ')}</li>
          ))}
        </ul>
      );
    }
    
    return <span>{String(answer)}</span>;
  };

  return (
    <div className="quiz-results">
      {/* Overall Performance Summary */}
      <div className="results-header">
        <h1>Quiz Complete! 🎉</h1>
        <div className="overall-score">
          <div className="score-circle">
            <span className="score-percentage">{results.percentage.toFixed(1)}%</span>
            <span className="score-fraction">{results.score}/{results.total_questions}</span>
          </div>
        </div>
      </div>

      <div className="results-stats">
        <div className="stat-item">
          <span className="stat-label">Time Taken</span>
          <span className="stat-value">{Math.floor(results.time_taken_seconds / 60)}m {results.time_taken_seconds % 60}s</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Quiz Attempt</span>
          <span className="stat-value">#{results.quiz_attempt_number}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="results-tabs">
        <button
          className={`tab-button ${activeTab === 'breakdown' ? 'active' : ''}`}
          onClick={() => setActiveTab('breakdown')}
        >
          📝 Question Breakdown
        </button>
        <button
          className={`tab-button ${activeTab === 'concepts' ? 'active' : ''}`}
          onClick={() => setActiveTab('concepts')}
        >
          📚 Concepts to Review
          {results.weak_concepts && results.weak_concepts.length > 0 && (
            <span className="tab-badge">{results.weak_concepts.length}</span>
          )}
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'breakdown' && (
          <div className="question-breakdown-section">
            <h2>Question-by-Question Results</h2>
            <p className="section-description">
              Review each question to understand your performance:
            </p>
            <div className="question-results-list">
              {results.question_results && results.question_results.length > 0 ? (
                results.question_results.map((result, idx) => {
                  const question = questionMap.get(result.question_id);
                  
                  // Debug: Log if question not found
                  // Uncomment for debugging
                  // if (!question) {
                  //   console.warn(`Question not found for ID: ${result.question_id}`);
                  //   console.log('Result object:', result);
                  // }
                  
                  // Use result data directly if question details not found
                  const questionData = question || {
                    question: 'Question details unavailable',
                    concept_context: result.concept_context,
                    question_type: result.question_type
                  };
                  
                  return (
                    <div key={result.question_id} className={`result-item ${result.is_correct ? 'correct' : 'incorrect'}`}>
                      <div className="result-item-header">
                        <span className={`result-indicator ${result.is_correct ? 'correct' : 'incorrect'}`}>
                          {result.is_correct ? '✓' : '✗'}
                        </span>
                        <span className="result-question-number">Question {idx + 1}</span>
                        <span className="result-concept-badge">{result.concept_context}</span>
                      </div>
                      
                      <p className="result-question-text">{questionData.question}</p>
                      
                      <div className="result-answers">
                        <div className="answer-section your-answer">
                          <p className="answer-label"><strong>Your Answer:</strong></p>
                          <div className="answer-content">
                            {formatAnswer(result.user_answer, result.question_type)}
                          </div>
                        </div>
                        
                        {!result.is_correct && (
                          <div className="answer-section correct-answer">
                            <p className="answer-label"><strong>Correct Answer:</strong></p>
                            <div className="answer-content">
                              {formatAnswer(result.correct_answer, result.question_type)}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="no-results">
                  <p>No question results available.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'concepts' && (
          <div className="concepts-review-section">
            {results.weak_concepts && results.weak_concepts.length > 0 ? (
              <>
                <h2>Concepts to Review</h2>
                <p className="section-description">
                  Based on your performance, we recommend reviewing these concepts:
                </p>
                <div className="weak-concepts-list">
                  {results.weak_concepts.map((concept, idx) => (
                    <div key={idx} className="weak-concept-card">
                      <h3>{concept.concept_context}</h3>
                      <div className="concept-stats">
                        <span className="stat">Accuracy: {concept.accuracy.toFixed(1)}%</span>
                        <span className="stat">
                          {concept.times_correct}/{concept.times_attempted} correct
                        </span>
                      </div>
                      <div className="progress-bar-small">
                        <div
                          className="progress-fill"
                          style={{ width: `${concept.accuracy}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="no-weak-concepts">
                <h2>🌟 Excellent Work!</h2>
                <p>You don't have any weak areas. All concepts are well understood!</p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="results-actions">
        <button
          onClick={() => navigate(`/courses/${courseId}/${deckId}`)}
          className="btn-secondary"
        >
          Review Flashcards
        </button>
        <button
          onClick={() => window.location.reload()}
          className="btn-primary"
        >
          Take Quiz Again
        </button>
      </div>
    </div>
  );
}

export default QuizView;
