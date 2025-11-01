import { Link } from 'react-router-dom'
import './LandingFooter.css'

function LandingFooter() {
  return (
    <footer className="landing-footer">
      <div className="footer-container">
        <div className="footer-brand">
          <img src="/logo.png" alt="exammate.ai logo" className="footer-logo" />
          <h3>exammate.ai</h3>
          <div className="center-container">
            <p>Built by IIT Madras students, for IIT Madras students.</p>
          </div>
        </div>
        
        <div className="footer-links">
          <Link to="/privacy-policy" className="footer-link">
            Contact
          </Link>
          <Link to="/privacy-policy" className="footer-link">
            FAQ
          </Link>
        </div>
      </div>
    </footer>
  )
}

export default LandingFooter
