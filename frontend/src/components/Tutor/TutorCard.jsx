/**
 * TutorCard - Premium card for AI Tutor feature
 * 
 * Features:
 * - Prominent design matching brand style
 * - Encourages users to try the AI tutor
 * - Navigates to chat interface
 */

import React from 'react';
import { FaBrain } from 'react-icons/fa';
import './TutorCard.css';

const TutorCard = ({ onClick }) => {
  return (
    <div className="tutor-card" onClick={onClick}>
      {/* Card Content */}
      <div className="tutor-content">
        <div className="tutor-icon">
          <FaBrain />
        </div>
        
        <h2 className="tutor-title">Personalised AI Tutor</h2>
        
        <p className="tutor-tagline">Intelligent Learning Assistant</p>
        
        <p className="tutor-description">
          Get instant, personalized explanations for any concept. Ask questions 
          in natural language and receive answers based on your course materials.
        </p>
        
        <div className="tutor-features">
          <div className="tutor-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9"/>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            <span className="feature-text">Context-Aware</span>
          </div>
          <div className="tutor-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span className="feature-text">24/7 Available</span>
          </div>
          <div className="tutor-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
            <span className="feature-text">Multi-Perspective</span>
          </div>
        </div>
        
        <button className="tutor-button">
          Start Chatting →
        </button>
      </div>
      
      {/* Glow Effect */}
      <div className="tutor-glow"></div>
    </div>
  );
};

export default TutorCard;

