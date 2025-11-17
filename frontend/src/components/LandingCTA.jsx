import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './LandingCTA.css'

function LandingCTA({ onOpenAuthModal }) {
  const { user } = useAuth()

  return (
    <section className="landing-cta landing-section bg-green section-padding-lg">
      <div className="landing-section-inner">
        <div className="cta-content text-center">
          <h2 className="cta-headline mb-md">
            Your Exam Is Approaching.<br />
            Choose Your Path Forward.
          </h2>
          <br/>
          <div className="cta-button-wrapper mb-lg">
            {user ? (
            <Link to="/courses" className="cta-button">
                <span className="button-text">Continue Learning</span>
                <span className="button-arrow">→</span>
              </Link>
            ) : (
              <button onClick={() => onOpenAuthModal('signup')} className="cta-button">
              <span className="button-text">Get Started</span>
              <span className="button-arrow">→</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}

export default LandingCTA
