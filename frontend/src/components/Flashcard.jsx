// Flashcard.jsx
import { useState, useEffect, useMemo } from 'react'
import { FaLightbulb, FaStar, FaRegStar, FaThumbsUp, FaThumbsDown } from 'react-icons/fa'
import { addBookmark, removeBookmark, isBookmarked } from '../api/bookmarks'
import { submitFeedback, getFlashcardFeedback } from '../api/feedback'
import mermaid from 'mermaid'
import './Flashcard.css'

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'loose',
  fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif',
  themeVariables: {
    primaryColor: '#3B82F6',
    primaryTextColor: '#1F2937',
    primaryBorderColor: '#3B82F6',
    lineColor: '#9CA3AF',
    secondaryColor: '#E5E7EB',
    tertiaryColor: '#F3F4F6',
    background: '#FFFFFF',
    mainBkg: '#FFFFFF',
    secondBkg: '#F8FAFC',
    tertiaryBkg: '#F1F5F9',
    textColor: '#1F2937',
    fontSize: '14px'
  }
})

const diagramCache = new Map()

const answerTypes = [
  { key: 'concise', label: 'Concise' },
  { key: 'analogy', label: 'Analogy' },
  { key: 'eli5', label: 'ELI5' },
  { key: 'real_world_use_case', label: 'Use Case' },
  { key: 'common_mistakes', label: 'Mistakes' },
  { key: 'example', label: 'Example' }
];

function escapeHtml(str = '') {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function Flashcard({ card, courseId, deckId, index, sessionId }) {
  const [isFlipped, setIsFlipped] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState('concise')
  const [mermaidLoading, setMermaidLoading] = useState(false)
  const [mermaidError, setMermaidError] = useState(null)
  const [isCardBookmarked, setIsCardBookmarked] = useState(false)
  const [feedbackRating, setFeedbackRating] = useState(null)
  const [feedbackLoading, setFeedbackLoading] = useState(false)
  const [bookmarkLoading, setBookmarkLoading] = useState(false)

  const uniqueDiagramId = useMemo(() => {
    const q = (card && card.question) ? card.question : ''
    return `mermaid-diagram-${q.substring(0, 20).replace(/[^a-zA-Z0-9]/g, '')}-${Math.random().toString(36).substr(2, 9)}`
  }, [card.question])

  const diagramCacheKey = useMemo(() => {
    if (!card || !card.mermaid_code) return null
    try {
      return `mermaid-${card.mermaid_code.replace(/\s+/g, '').substring(0, 80)}`
    } catch {
      return null
    }
  }, [card && card.mermaid_code])

  useEffect(() => {
    setIsFlipped(false)
    setSelectedAnswer('concise')
    setMermaidLoading(false)
    setMermaidError(null)
    setIsCardBookmarked(false)
    setFeedbackRating(null)
  }, [card])

  useEffect(() => {
    const loadCardState = async () => {
      if (!courseId || !deckId || index === undefined) return
      try {
        const bookmarked = await isBookmarked(courseId, deckId, index)
        setIsCardBookmarked(bookmarked)
        const rating = await getFlashcardFeedback(courseId, deckId, index)
        setFeedbackRating(rating)
      } catch (error) {
        console.error('Error loading card state:', error)
      }
    }
    loadCardState()
  }, [courseId, deckId, index])

  const handleBookmarkToggle = async (e) => {
    e.stopPropagation()
    if (bookmarkLoading) return
    setBookmarkLoading(true)
    try {
      if (isCardBookmarked) {
        await removeBookmark({ courseId, deckId, index })
        setIsCardBookmarked(false)
      } else {
        await addBookmark({ courseId, deckId, index })
        setIsCardBookmarked(true)
      }
    } catch (error) {
      console.error('Error toggling bookmark:', error)
    } finally {
      setBookmarkLoading(false)
    }
  }

  const handleLike = async (e) => {
    e.stopPropagation()
    if (feedbackLoading || !sessionId) return
    setFeedbackLoading(true)
    try {
      const newRating = feedbackRating === 1 ? null : 1
      if (newRating === null) {
        setFeedbackRating(null)
      } else {
        await submitFeedback({ sessionId, courseId, deckId, index, rating: newRating })
        setFeedbackRating(newRating)
      }
    } catch (error) {
      console.error('Error submitting like:', error)
    } finally {
      setFeedbackLoading(false)
    }
  }

  const handleDislike = async (e) => {
    e.stopPropagation()
    if (feedbackLoading || !sessionId) return
    setFeedbackLoading(true)
    try {
      const newRating = feedbackRating === -1 ? null : -1
      if (newRating === null) {
        setFeedbackRating(null)
      } else {
        await submitFeedback({ sessionId, courseId, deckId, index, rating: newRating })
        setFeedbackRating(newRating)
      }
    } catch (error) {
      console.error('Error submitting dislike:', error)
    } finally {
      setFeedbackLoading(false)
    }
  }

  // ---------- MERMAID RENDER EFFECT ----------
  useEffect(() => {
    if (!isFlipped || !card || !card.mermaid_code?.trim()) return

    let mounted = true
    let timeoutHandle = null

    const renderDiagram = async () => {
      const mermaidContainer = document.getElementById(uniqueDiagramId)
      if (!mermaidContainer) return

      try {
        setMermaidLoading(true)
        setMermaidError(null)

        // Sanitize code
        let code = card.mermaid_code.trim()
        code = code.replace(/^```(?:mermaid)?\s*/, '').replace(/\s*```$/, '').trim()
        code = code.replace(/\\n/g, '\n').replace(/\\r/g, '\n').replace(/\\t/g, '\t')
        code = code.split('\n').map(l => l.replace(/\s{2,}/g, ' ').trimEnd()).join('\n')
        code = code.replace(/(\]|\))(?=[A-Za-z0-9_])/g, '$1\n')
        code = code.replace(/([A-Za-z0-9_])-->/g, '$1 -->')
        code = code.replace(/\n{2,}/g, '\n\n').trim()

        if (!code) throw new Error('Diagram source is empty after sanitization.')

        if (diagramCacheKey && diagramCache.has(diagramCacheKey)) {
          if (!mounted) return
          mermaidContainer.innerHTML = diagramCache.get(diagramCacheKey)
          setMermaidLoading(false)
          return
        }

        // Render
        const renderId = `mermaid-svg-${Date.now()}-${Math.random().toString(36).slice(2,9)}`
        const result = await Promise.race([
          mermaid.render(renderId, code),
          new Promise((_, reject) => {
            timeoutHandle = setTimeout(() => reject(new Error('Mermaid render timeout')), 7000)
          })
        ])

        const svg = (typeof result === 'string') ? result : (result?.svg || JSON.stringify(result))
        if (diagramCacheKey) diagramCache.set(diagramCacheKey, svg)
        if (mounted) {
          mermaidContainer.innerHTML = svg
          setMermaidLoading(false)
        }
      } catch (err) {
        console.error('Mermaid rendering error:', err)
        if (mounted) {
          setMermaidError(err.message || 'Failed to render diagram')
          setMermaidLoading(false)
          const mermaidContainer = document.getElementById(uniqueDiagramId)
          if (mermaidContainer) {
            mermaidContainer.innerHTML = `
              <div class="mermaid-error">
                <p>⚠️ Diagram could not be rendered: ${escapeHtml(err.message || 'Unknown error')}</p>
                <details>
                  <summary>View diagram code</summary>
                  <pre><code>${escapeHtml(card.mermaid_code)}</code></pre>
                </details>
              </div>
            `
          }
        }
      } finally {
        if (timeoutHandle) clearTimeout(timeoutHandle)
      }
    }

    const scheduledRender = setTimeout(renderDiagram, 50)
    return () => {
      mounted = false
      clearTimeout(scheduledRender)
      if (timeoutHandle) clearTimeout(timeoutHandle)
    }
  }, [isFlipped, card?.mermaid_code, uniqueDiagramId, diagramCacheKey])

  const handleCardClick = (e) => {
    if (e.target.closest('.mermaid-diagram-container') || 
        e.target.closest('.answer-selector') ||
        e.target.closest('.bookmark-btn') ||
        e.target.closest('.feedback-buttons')) {
      return
    }
    setIsFlipped(!isFlipped)
  }

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.code === 'Space') {
        event.preventDefault()
        setIsFlipped(!isFlipped)
      }
      if (isFlipped && event.key >= '1' && event.key <= '6') {
        event.preventDefault()
        const answerIndex = parseInt(event.key) - 1
        if (answerIndex < answerTypes.length) {
          setSelectedAnswer(answerTypes[answerIndex].key)
        }
      }
      if (isFlipped && event.key === 'Tab') {
        event.preventDefault()
        const currentIndex = answerTypes.findIndex(type => type.key === selectedAnswer)
        const nextIndex = (currentIndex + 1) % answerTypes.length
        setSelectedAnswer(answerTypes[nextIndex].key)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isFlipped, selectedAnswer])

  const getAnswerContent = () => {
    if (selectedAnswer === 'example') return card.example || 'No example available.'
    return card.answers?.[selectedAnswer] || 'No answer available.'
  }

  return (
    <div className="flashcard-wrapper">
      <div 
        className={`flashcard ${isFlipped ? 'flipped' : ''}`}
        onClick={handleCardClick}
      >
        <div className="flashcard-front">
          <button
            className={`bookmark-btn ${isCardBookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmarkToggle}
            disabled={bookmarkLoading}
            title={isCardBookmarked ? 'Remove bookmark' : 'Add bookmark'}
          >
            {bookmarkLoading ? <div className="btn-spinner"></div> :
              isCardBookmarked ? <FaStar /> : <FaRegStar />}
          </button>
          <div className="card-content">
            <div className="question-text">{card.question}</div>
          </div>
        </div>
        <div className="flashcard-back">
          <button
            className={`bookmark-btn ${isCardBookmarked ? 'bookmarked' : ''}`}
            onClick={handleBookmarkToggle}
            disabled={bookmarkLoading}
            title={isCardBookmarked ? 'Remove bookmark' : 'Add bookmark'}
          >
            {bookmarkLoading ? <div className="btn-spinner"></div> :
              isCardBookmarked ? <FaStar /> : <FaRegStar />}
          </button>
          <div className="card-content">
            <div className="answer-selector">
              {answerTypes.map((type, idx) => (
                <button
                  key={type.key}
                  className={`answer-type-btn ${selectedAnswer === type.key ? 'active' : ''}`}
                  onClick={(e) => { e.stopPropagation(); setSelectedAnswer(type.key) }}
                  title={`${type.label} (${idx + 1})`}
                >
                  <span className="shortcut-key">{idx + 1}</span>
                  <span className="tab-label">{type.label}</span>
                </button>
              ))}
            </div>
            <div className="answer-content">
              <div className="answer-text">{getAnswerContent()}</div>
              {card.mermaid_code?.trim() && (
                <div className="mermaid-diagram-wrapper">
                  {mermaidLoading && (
                    <div className="mermaid-loading">
                      <div className="mermaid-spinner"></div>
                      <p>Rendering diagram...</p>
                    </div>
                  )}
                  <div id={uniqueDiagramId} className={`mermaid-diagram-container ${mermaidLoading ? 'loading' : ''}`}></div>
                  {mermaidError && <div className="mermaid-error-inline"><small>{mermaidError}</small></div>}
                </div>
              )}
            </div>
            <div className="feedback-buttons">
              <button
                className={`feedback-btn like-btn ${feedbackRating === 1 ? 'active' : ''}`}
                onClick={handleLike}
                disabled={feedbackLoading}
                title="Like this flashcard"
              >
                {feedbackLoading && feedbackRating !== -1 ? <div className="btn-spinner"></div> : <FaThumbsUp />}
              </button>
              <button
                className={`feedback-btn dislike-btn ${feedbackRating === -1 ? 'active' : ''}`}
                onClick={handleDislike}
                disabled={feedbackLoading}
                title="Dislike this flashcard"
              >
                {feedbackLoading && feedbackRating !== 1 ? <div className="btn-spinner"></div> : <FaThumbsDown />}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Flashcard
