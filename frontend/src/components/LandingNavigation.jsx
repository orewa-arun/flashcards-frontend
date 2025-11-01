import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './LandingNavigation.css'

function LandingNavigation() {
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <nav className={`landing-navigation ${isScrolled ? 'scrolled' : ''}`}>
      <div className="landing-nav-container">
        {/* Logo */}
        <Link to="/" className="landing-nav-logo">
          <img src="/logo.png" alt="exammate.ai logo" className="landing-logo" />
          exammate.ai
        </Link>

        {/* Navigation Links */}
        <div className="landing-nav-links">
          <button 
            onClick={() => scrollToSection('how-it-works')}
            className="landing-nav-link"
          >
            How It Works
          </button>
          
          <Link to="/courses" className="landing-nav-cta">
            Start Free →
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default LandingNavigation
