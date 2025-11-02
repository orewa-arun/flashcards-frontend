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
            FOR IIT MADRAS DoMS STUDENTS
          </div>
          
          <h1 className="hero-headline">
            Exam in 2 Days? Master Your Syllabus in 3 Hours.
          </h1>
          
          <p className="hero-subheadline">
            AI flashcards + adaptive quizzes that find your weak spots and fix them. Fast.
          </p>
          
          {user ? (
          <Link to="/courses" className="hero-cta">
              Go to Dashboard →
            </Link>
          ) : (
            <button onClick={() => onOpenAuthModal('signup')} className="hero-cta">
            Start Preparing Free →
            </button>
          )}
          
          <div className="hero-benefits">
            <span>✓ Used by 20+ IIT students</span>
            <span>✓ 100% Free</span>
            <span>✓ Start free in 30 seconds</span>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="mockup-placeholder">
            <div className="mockup-header">
              <div className="mockup-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="mockup-title">ExamMate.ai</span>
            </div>
            <div className="mockup-content">
              <div className="flashcard-preview">
                <div className="flashcard-question">
                  What are the key components of an ER diagram and how do they represent database relationships?
                </div>
                <div className="flashcard-tabs">
                  <span className="tab active">Concise</span>
                  <span className="tab">Analogy</span>
                  <span className="tab">Example</span>
                </div>
                <div className="flashcard-answer">
                  ER diagrams use entities (rectangles), attributes (ovals), and relationships (diamonds) to model database structure. Entities represent objects, attributes describe properties, and relationships show how entities connect...
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
