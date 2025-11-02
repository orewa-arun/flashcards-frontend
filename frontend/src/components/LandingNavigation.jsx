import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import AuthModal from './Auth/AuthModal'
import './LandingNavigation.css'

function LandingNavigation() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [authModalMode, setAuthModalMode] = useState('signup')
  const { user } = useAuth()

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

  const openAuthModal = (mode) => {
    setAuthModalMode(mode)
    setIsAuthModalOpen(true)
  }

  const closeAuthModal = () => {
    setIsAuthModalOpen(false)
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
          
          {user ? (
          <Link to="/courses" className="landing-nav-cta">
              Go to Dashboard →
          </Link>
          ) : (
            <>
              <button 
                onClick={() => openAuthModal('login')}
                className="landing-nav-login"
              >
                Log In
              </button>
              <button 
                onClick={() => openAuthModal('signup')}
                className="landing-nav-cta"
              >
                Sign Up
              </button>
            </>
          )}
        </div>
      </div>

      <AuthModal 
        isOpen={isAuthModalOpen}
        onClose={closeAuthModal}
        initialMode={authModalMode}
      />
    </nav>
  )
}

export default LandingNavigation
