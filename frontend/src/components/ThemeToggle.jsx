import { useState, useEffect } from 'react'
import './ThemeToggle.css'

function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first, default to 'light'
    const savedTheme = localStorage.getItem('theme')
    return savedTheme || 'light'
  })

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)
    // Save to localStorage
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light')
  }

  return (
    <button 
      className="theme-toggle"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 15C12.7614 15 15 12.7614 15 10C15 7.23858 12.7614 5 10 5C7.23858 5 5 7.23858 5 10C5 12.7614 7.23858 15 10 15Z" fill="currentColor"/>
          <path d="M10 0V2M10 18V20M20 10H18M2 10H0M17.07 17.07L15.66 15.66M4.34 4.34L2.93 2.93M17.07 2.93L15.66 4.34M4.34 15.66L2.93 17.07" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17 10.5C16.1 14 13 17 9 17C5 17 2 14 2 10C2 6 5 3 9 3C9.3 3 9.6 3 9.9 3.1C8.7 4.2 8 5.8 8 7.5C8 10.5 10.5 13 13.5 13C14.8 13 16 12.5 17 11.7C17 12 17 12.2 17 12.5V10.5Z" fill="currentColor"/>
        </svg>
      )}
    </button>
  )
}

export default ThemeToggle

