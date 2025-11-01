import LandingFlashcard from './LandingFlashcard'
import './LandingDemo.css'

function LandingDemo() {
  return (
    <section className="landing-demo landing-section bg-gradient section-padding-lg">
      <div className="landing-section-inner">
        <div className="demo-header text-center mb-lg">
          <h2 className="demo-headline mb-md">
            Experience the Learning Method
          </h2>
          <div className="center-container">
            <p className="demo-subheadline">
              See how our AI-powered flashcards adapt to different learning styles. 
              Click the card to flip it, then try different answer types.
            </p>
          </div>
        </div>
        
        <div className="demo-flashcard-container">
          <LandingFlashcard />
        </div>
        
        <div className="demo-features text-center">
          <div className="feature-grid grid-3">
            <div className="feature-item">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L15.09 8.26L22 9L17 14L18.18 21L12 17.77L5.82 21L7 14L2 9L8.91 8.26L12 2Z" fill="currentColor"/>
                </svg>
              </div>
              <h3>6 Learning Styles</h3>
              <p>From concise definitions to real-world examples</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" fill="currentColor"/>
                </svg>
              </div>
              <h3>Visual Diagrams</h3>
              <p>Complex concepts made simple with interactive diagrams</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M7 14l3-3 3 3 5-5-1.5-1.5L13 11 10 8 5.5 12.5 7 14zm5-12C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="currentColor"/>
                </svg>
              </div>
              <h3>Instant Feedback</h3>
              <p>Learn faster with immediate explanations</p>
            </div>
          </div>
        </div>
        
        <div className="demo-cta text-center">
          <div className="center-container">
            <p className="demo-instruction">
              This is how you'll master 150+ concepts across all your courses.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingDemo
