import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './LandingHero.css'

function LandingHero({ onOpenAuthModal }) {
  const { user } = useAuth()
  
  return (
    <section className="landing-hero">
      <div className="hero-container">
        <div className="hero-content">
          <div className="hero-eyebrow">
            EXAM-FOCUSED LEARNING
          </div>
          
          <h1 className="hero-headline">
            AI-Powered Exam Prep: Get Ready in 30 Minutes, Not 3 Hours
          </h1>
          <br/>
          <p className="hero-subheadline">
            Our AI analyzes your knowledge gaps in real-time, creates personalized study paths, and adapts questions to your level—making every minute count.
          </p>
          <br/>

          {user ? (
          <Link to="/courses" className="hero-cta">
              Continue Learning →
            </Link>
          ) : (
            <button onClick={() => onOpenAuthModal('signup')} className="hero-cta">
            Start Preparing →
            </button>
          )}
          
          <div className="hero-benefits">
            <span className="benefit-item">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
              <span className="benefit-text">3x Faster</span>
            </span>
            <span className="benefit-item">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <span className="benefit-text">AI-Personalized</span>
            </span>
            <span className="benefit-item">
              <svg className="benefit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 3v18h18"/>
                <path d="M18 17V9l-5 5-5-5v8"/>
              </svg>
              <span className="benefit-text">Track Progress</span>
            </span>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="product-card floating">
            <div className="product-card-header">
              <div className="card-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="card-title">exammate.ai</span>
            </div>
            <div className="product-card-content">
              <div className="flashcard-demo">
                <div className="demo-question">
                  What are the key components of an ER diagram?
                </div>
                <div className="demo-tabs">
                  <span className="demo-tab active">Concise</span>
                  <span className="demo-tab">Analogy</span>
                  <span className="demo-tab">ELI5</span>
                  <span className="demo-tab">Example</span>
                  <span className="demo-tab">Use Case</span>
                  <span className="demo-tab">Mistakes</span>
                </div>
                <div className="demo-answer">
                  ER diagrams use entities (rectangles), attributes (ovals), and relationships (diamonds) to model database structure...
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingHero
