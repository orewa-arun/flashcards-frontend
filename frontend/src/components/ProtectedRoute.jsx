import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginButton from './Auth/LoginButton';
import './ProtectedRoute.css';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="protected-route-loading">
        <div className="loading-spinner"></div>
        <p>Checking authentication...</p>
      </div>
    );
  }

  // If user is not authenticated, show login prompt
  if (!user) {
    return (
      <div className="protected-route-container">
        <div className="protected-route-content">
          <div className="lock-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
              <path 
                d="M6 10V8C6 5.79086 7.79086 4 10 4H14C16.2091 4 18 5.79086 18 8V10" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round"
              />
              <rect 
                x="4" 
                y="10" 
                width="16" 
                height="10" 
                rx="2" 
                stroke="currentColor" 
                strokeWidth="2"
              />
              <circle cx="12" cy="15" r="1" fill="currentColor"/>
            </svg>
          </div>
          
          <h2>Sign In Required</h2>
          <p>
            You need to sign in to access course content and track your progress.
          </p>
          
          <div className="login-section">
            <LoginButton />
          </div>
          
          <div className="benefits-list">
            <h3>Why sign in?</h3>
            <ul>
              <li>📚 Access all course materials</li>
              <li>📊 Track your learning progress</li>
              <li>⭐ Bookmark important content</li>
              <li>📈 View your quiz history</li>
              <li>🎯 Get personalized recommendations</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // User is authenticated, render the protected content
  return children;
};

export default ProtectedRoute;
