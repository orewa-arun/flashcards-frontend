import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FaHome, FaStar, FaHistory, FaBars, FaTimes } from 'react-icons/fa'
import './Navigation.css'
import LandingNavigation from './LandingNavigation'
import { useAuth } from '../contexts/AuthContext'
import LoginButton from './Auth/LoginButton'
import UserProfile from './Auth/UserProfile'

function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const location = useLocation()
  const { user, loading } = useAuth()

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const closeMenu = () => {
    setIsMenuOpen(false)
  }

  const isActive = (path) => {
    return location.pathname === path
  }

  // Show landing navigation for landing page, regular navigation for course pages
  if (location.pathname === '/') {
    return <LandingNavigation />
  }

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        {/* Logo/Brand */}
        <Link to="/courses" className="nav-brand" onClick={closeMenu}>
          {/* <span className="brand-icon">📚</span> */}
          <img src="/logo.png" alt="exammate.ai logo" className="brand-icon" />
          <span className="brand-text">exammate.ai</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="nav-links desktop-nav">
          <Link 
            to="/courses" 
            className={`nav-link ${isActive('/courses') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <FaHome />
            <span>Home</span>
          </Link>
          
          <Link 
            to="/bookmarks" 
            className={`nav-link ${isActive('/bookmarks') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <FaStar />
            <span>Bookmarks</span>
          </Link>
          
          <Link 
            to="/quiz-history" 
            className={`nav-link ${isActive('/quiz-history') ? 'active' : ''}`}
            onClick={closeMenu}
          >
            <FaHistory />
            <span>Quiz History</span>
          </Link>
        </div>

        {/* Authentication Section */}
        <div className="nav-auth desktop-nav">
          {loading ? (
            <div className="auth-loading">Loading...</div>
          ) : user ? (
            <UserProfile />
          ) : (
            <LoginButton />
          )}
        </div>

        {/* Mobile Menu Button */}
        <button 
          className="mobile-menu-btn"
          onClick={toggleMenu}
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <FaTimes /> : <FaBars />}
        </button>

        {/* Mobile Navigation */}
        <div className={`mobile-nav ${isMenuOpen ? 'open' : ''}`}>
          <div className="mobile-nav-overlay" onClick={closeMenu}></div>
          <div className="mobile-nav-content">
            <Link 
              to="/courses" 
              className={`nav-link ${isActive('/courses') ? 'active' : ''}`}
              onClick={closeMenu}
            >
              <FaHome />
              <span>Home</span>
            </Link>
            
            <Link 
              to="/bookmarks" 
              className={`nav-link ${isActive('/bookmarks') ? 'active' : ''}`}
              onClick={closeMenu}
            >
              <FaStar />
              <span>Bookmarks</span>
            </Link>
            
            <Link 
              to="/quiz-history" 
              className={`nav-link ${isActive('/quiz-history') ? 'active' : ''}`}
              onClick={closeMenu}
            >
              <FaHistory />
              <span>Quiz History</span>
            </Link>

            {/* Mobile Authentication */}
            <div className="mobile-auth-section">
              {loading ? (
                <div className="auth-loading">Loading...</div>
              ) : user ? (
                <UserProfile />
              ) : (
                <LoginButton />
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
