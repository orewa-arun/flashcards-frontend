// Flashcard.jsx
import React, { useState, useEffect, useMemo, useRef } from 'react'
import ReactDOM from 'react-dom'
import { FaLightbulb, FaStar, FaRegStar, FaThumbsUp, FaThumbsDown, FaCalculator, FaSearchPlus, FaSearchMinus, FaExpandAlt } from 'react-icons/fa'
import { addBookmark, removeBookmark, isBookmarked } from '../api/bookmarks'
import { submitFeedback, getFlashcardFeedback } from '../api/feedback'
import mermaid from 'mermaid'
import * as d3 from 'd3'
import 'd3-graphviz'
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
  const [showMathLarge, setShowMathLarge] = useState(false)
  const [graphvizLoading, setGraphvizLoading] = useState(false)
  const [graphvizError, setGraphvizError] = useState(null)
  const graphvizRef = useRef(null)
  const graphvizInstanceRef = useRef(null)

  const uniqueDiagramId = useMemo(() => {
    const q = (card && card.question) ? card.question : ''
    return `mermaid-diagram-${q.substring(0, 20).replace(/[^a-zA-Z0-9]/g, '')}-${Math.random().toString(36).substr(2, 9)}`
  }, [card])

  const diagramCacheKey = useMemo(() => {
    if (!card || !card.mermaid_diagrams || !card.mermaid_diagrams[selectedAnswer]) return null
    try {
      return `mermaid-${selectedAnswer}-${card.mermaid_diagrams[selectedAnswer].replace(/\s+/g, '').substring(0, 80)}`
    } catch {
      return null
    }
  }, [card, selectedAnswer])

  useEffect(() => {
    setIsFlipped(false)
    setSelectedAnswer('concise')
    setMermaidLoading(false)
    setMermaidError(null)
    setIsCardBookmarked(false)
    setFeedbackRating(null)
    setGraphvizLoading(false)
    setGraphvizError(null)
  }, [])

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
    // Backward compatibility: Handle legacy mermaid_code field
    if (card && !card.mermaid_diagrams && card.mermaid_code) {
      card.mermaid_diagrams = { concise: card.mermaid_code }
    }

    const currentDiagramCode = card?.mermaid_diagrams?.[selectedAnswer]?.trim()
    if (!isFlipped || !card || !currentDiagramCode) {
      // Clear diagram if no code for current answer type
      const mermaidContainer = document.getElementById(uniqueDiagramId)
      if (mermaidContainer) mermaidContainer.innerHTML = ''
      return
    }

    let mounted = true
    let timeoutHandle = null

    const renderDiagram = async () => {
      const mermaidContainer = document.getElementById(uniqueDiagramId)
      if (!mermaidContainer) return

      try {
        setMermaidLoading(true)
        setMermaidError(null)

        // Sanitize code
        let code = currentDiagramCode.trim()
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
                  <pre><code>${escapeHtml(currentDiagramCode)}</code></pre>
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
  }, [isFlipped, card, selectedAnswer, uniqueDiagramId, diagramCacheKey])

  const handleCardClick = (e) => {
    // Check if click is on any interactive element
    if (e.target.closest('.mermaid-diagram-container') || 
        e.target.closest('.answer-selector') ||
        e.target.closest('.answer-type-btn') ||
        e.target.closest('.bookmark-btn') ||
        e.target.closest('.feedback-buttons') ||
        e.target.closest('.feedback-btn') ||
        e.target.closest('.math-viz-section') ||
        e.target.closest('.math-lookup-btn')) {
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

  // ---------- GRAPHVIZ RENDER EFFECT ----------
  useEffect(() => {
    // Backward compatibility: Handle legacy diagram_image_path or missing math_visualizations
    if (card && !card.math_visualizations && card.diagram_image_path) {
      // If there's a legacy diagram_image_path, we can't render it with Graphviz
      // but we can at least prevent errors
      card.math_visualizations = {}
    }

    if (!showMathLarge || !card?.math_visualizations?.[selectedAnswer]?.trim()) {
      return
    }

    const dotCode = card.math_visualizations[selectedAnswer].trim()
    if (!dotCode) return

    let mounted = true

    const renderGraphviz = async () => {
      if (!graphvizRef.current) return

      try {
        setGraphvizLoading(true)
        setGraphvizError(null)

        // Clear previous content
        d3.select(graphvizRef.current).selectAll('*').remove()

        // Render the DOT code with enhanced settings
        const graphvizInstance = d3.select(graphvizRef.current)
          .graphviz({
            fit: true,
            zoom: true, // Re-enable zoom!
            transition: (selection) => {
              return selection.transition().duration(300)
            }
          })
          .on('renderEnd', () => {
            // Apply custom styling to the rendered SVG
            const svg = d3.select(graphvizRef.current).select('svg')
            if (svg.node()) {
              svg.selectAll('text')
                .style('font-family', 'system-ui, -apple-system, sans-serif')
                .style('font-weight', '500')

              svg.selectAll('path')
                .style('stroke-width', '2')
                .style('fill', 'none')

              svg.selectAll('.node')
                .style('stroke-width', '1.5')

              svg.selectAll('.cluster rect')
                .style('fill-opacity', '0.06')
                .style('stroke-dasharray', '6,3')

              svg.selectAll('.cluster text')
                .style('font-weight', '600')
                .style('font-size', '12px')
            }
          })

        graphvizInstanceRef.current = graphvizInstance // Store instance in ref

        await graphvizInstance.renderDot(dotCode)

        if (mounted) {
          setGraphvizLoading(false)
        }
      } catch (err) {
        console.error('Graphviz rendering error:', err)
        if (mounted) {
          setGraphvizError(err.message || 'Failed to render mathematical diagram')
          setGraphvizLoading(false)
        }
      }
    }

    renderGraphviz()

    return () => {
      mounted = false
      // Note: Cleanup is handled by the d3-graphviz library automatically
      // when the component unmounts or when new content is rendered
    }
  }, [showMathLarge, card, selectedAnswer])

  const handleZoomIn = () => {
    if (graphvizInstanceRef.current) {
      const svg = d3.select(graphvizRef.current).select('svg')
      graphvizInstanceRef.current.zoomBehavior().scaleBy(svg.transition().duration(250), 1.2)
    }
  }

  const handleZoomOut = () => {
    if (graphvizInstanceRef.current) {
      const svg = d3.select(graphvizRef.current).select('svg')
      graphvizInstanceRef.current.zoomBehavior().scaleBy(svg.transition().duration(250), 1 / 1.2)
    }
  }

  const handleZoomReset = () => {
    if (graphvizInstanceRef.current) {
      graphvizInstanceRef.current.resetZoom(d3.transition().duration(500))
    }
  }

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
            <div className="answer-selector" onClick={(e) => e.stopPropagation()}>
              {answerTypes.map((type, idx) => (
                <button
                  key={type.key}
                  className={`answer-type-btn ${selectedAnswer === type.key ? 'active' : ''}`}
                  onClick={(e) => { 
                    e.preventDefault(); 
                    e.stopPropagation(); 
                    e.nativeEvent.stopImmediatePropagation();
                    setSelectedAnswer(type.key);
                    return false;
                  }}
                  title={`${type.label} (${idx + 1})`}
                >
                  <span className="shortcut-key">{idx + 1}</span>
                  <span className="tab-label">{type.label}</span>
                </button>
              ))}
            </div>
            <div className="answer-content">
              <div className="answer-text">{getAnswerContent()}</div>
              {card.mermaid_diagrams?.[selectedAnswer]?.trim() && (
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
              
              {/* Math Visualization Button */}
              {card.math_visualizations?.[selectedAnswer]?.trim() && (
                <div className="math-viz-section">
                  <button
                    className="math-lookup-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowMathLarge(true);
                    }}
                    title="View mathematical diagram"
                  >
                    <FaCalculator /> View Math Diagram
                  </button>
                </div>
              )}

              {/* Large Modal for Mathematical Diagrams */}
              {showMathLarge && ReactDOM.createPortal(
                <>
                  <div className="math-modal-large-backdrop" onClick={() => setShowMathLarge(false)}></div>
                  <div className="math-modal-large" onClick={(e) => e.stopPropagation()}>
                    <div className="math-modal-large-content" onClick={(e) => e.stopPropagation()}>
                      <button className="math-close-btn" onClick={() => setShowMathLarge(false)}>×</button>
                      <div className="math-modal-header">
                        <h3>🔢 Math Diagram</h3>
                        <p>For {selectedAnswer.replace(/_/g, ' ')}</p>
                      </div>

                      {/* Graphviz Rendering Container */}
                      <div className="math-diagram-container-large">
                        {graphvizLoading && (
                          <div className="graphviz-loading">
                            <div className="graphviz-spinner"></div>
                            <p>Rendering mathematical diagram...</p>
                          </div>
                        )}
                        {graphvizError && (
                          <div className="graphviz-error">
                            <p>⚠️ Failed to render diagram: {graphvizError}</p>
                          </div>
                        )}
                        <div
                          ref={graphvizRef}
                          className="graphviz-diagram-large"
                        ></div>

                        <div className="math-modal-controls">
                          <button onClick={handleZoomIn} className="math-zoom-btn" title="Zoom In"><FaSearchPlus /></button>
                          <button onClick={handleZoomOut} className="math-zoom-btn" title="Zoom Out"><FaSearchMinus /></button>
                          <button onClick={handleZoomReset} className="math-zoom-btn" title="Reset Zoom"><FaExpandAlt /></button>
                        </div>
                      </div>

                      {/* Always show the source code */}
                      <details className="math-code-details">
                        <summary>View Graphviz DOT Code</summary>
                        <pre><code>{card.math_visualizations[selectedAnswer]}</code></pre>
                      </details>
                    </div>
                  </div>
                </>,
                document.getElementById('modal-root')
              )}
            </div>
            <div className="feedback-buttons" onClick={(e) => e.stopPropagation()}>
              <button
                className={`feedback-btn like-btn ${feedbackRating === 1 ? 'active' : ''}`}
                onClick={(e) => { 
                  e.preventDefault(); 
                  e.stopPropagation(); 
                  e.nativeEvent.stopImmediatePropagation();
                  handleLike(e);
                  return false;
                }}
                disabled={feedbackLoading}
                title="Like this flashcard"
              >
                {feedbackLoading && feedbackRating !== -1 ? <div className="btn-spinner"></div> : <FaThumbsUp />}
              </button>
              <button
                className={`feedback-btn dislike-btn ${feedbackRating === -1 ? 'active' : ''}`}
                onClick={(e) => { 
                  e.preventDefault(); 
                  e.stopPropagation(); 
                  e.nativeEvent.stopImmediatePropagation();
                  handleDislike(e);
                  return false;
                }}
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
