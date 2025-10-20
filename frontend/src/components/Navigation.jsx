import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FaHome, FaStar, FaHistory, FaBars, FaTimes } from 'react-icons/fa'
import './Navigation.css'

function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const location = useLocation()

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen)
  }

  const closeMenu = () => {
    setIsMenuOpen(false)
  }

  const isActive = (path) => {
    return location.pathname === path
  }

  return (
    <nav className="main-navigation">
      <div className="nav-container">
        {/* Logo/Brand */}
        <Link to="/" className="nav-brand" onClick={closeMenu}>
          <span className="brand-icon">📚</span>
          <span className="brand-text">Self-Learning AI</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="nav-links desktop-nav">
          <Link 
            to="/" 
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
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
              to="/" 
              className={`nav-link ${isActive('/') ? 'active' : ''}`}
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
        </div>
      </div>
    </nav>
  )
}

export default Navigation
