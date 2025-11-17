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
            <p>Built by students, for students.</p>
          </div>
        </div>
        
        <div className="footer-links">
          <a href="mailto:contact@exammate.ai" className="footer-link">
            Contact
          </a>
          <a href="#faq" className="footer-link" onClick={(e) => {
            e.preventDefault();
            const element = document.getElementById('faq');
            if (element) {
              element.scrollIntoView({ behavior: 'smooth' });
            } else {
              window.location.href = '/#faq';
            }
          }}>
            FAQ
          </a>
          <Link to="/privacy-policy" className="footer-link">
            Privacy
          </Link>
        </div>
      </div>
    </footer>
  )
}

export default LandingFooter
