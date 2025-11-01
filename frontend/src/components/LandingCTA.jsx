import { Link } from 'react-router-dom'
import './LandingCTA.css'

function LandingCTA() {

  return (
    <section className="landing-cta landing-section bg-green section-padding-lg">
      <div className="landing-section-inner">
        <div className="cta-content text-center">
          <h2 className="cta-headline mb-md">
            Ready to Ace Your Exams?
          </h2>
          
          <div className="center-container">
            <p className="cta-subheadline">
              Join 20+ IIT Madras students who are already mastering their courses.
            </p>
          </div>
          
          <div className="cta-button-wrapper mb-lg">
            <Link to="/courses" className="cta-button">
              <span className="button-text">Get Started Free</span>
              <span className="button-arrow">→</span>
            </Link>
            <p className="cta-guarantee">
              No credit card required • Start learning in 30 seconds
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingCTA
