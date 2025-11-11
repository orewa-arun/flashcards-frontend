/**
 * MixModeCard - Premium, highlighted card for Mix Mode
 * 
 * Features:
 * - Larger and more prominent than other options
 * - "Recommended" tag
 * - Premium design with brand colors
 * - Displays exam readiness score preview
 */

import React, { useEffect, useState } from 'react';
import { FaShapes } from 'react-icons/fa';
import { getDeckExamReadiness } from '../../api/mixMode';
import './MixModeCard.css';

const MixModeCard = ({ onClick, courseId, deckId }) => {
  const [readinessScore, setReadinessScore] = useState(null);
  const [isLoadingReadiness, setIsLoadingReadiness] = useState(false);
  
  useEffect(() => {
    const fetchReadiness = async () => {
      if (!courseId || !deckId) return;
      
      setIsLoadingReadiness(true);
      try {
        const data = await getDeckExamReadiness(courseId, [deckId], false);
        setReadinessScore(data.overall_readiness_score);
      } catch (error) {
        console.error('Failed to fetch readiness for MixModeCard:', error);
        // Fail silently - readiness is optional
      } finally {
        setIsLoadingReadiness(false);
      }
    };
    
    fetchReadiness();
  }, [courseId, deckId]);
  
  const getReadinessColor = (score) => {
    if (score < 40) return '#E74C3C';
    if (score < 70) return '#F39C12';
    if (score < 85) return '#27AE60';
    return '#2d7a3e';
  };
  
  return (
    <div className="mix-mode-card" onClick={onClick}>
      {/* Recommended Tag */}
      <div className="recommended-tag">
        <span className="recommended-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          Recommended
        </span>
      </div>
      
      {/* Readiness Score Badge */}
      {readinessScore !== null && !isLoadingReadiness && (
        <div 
          className="readiness-badge"
        >
          <div 
            className="readiness-ring"
            style={{ 
              background: `conic-gradient(${getReadinessColor(readinessScore)} ${Math.round(readinessScore)}%, rgba(0,0,0,0.08) 0)` 
            }}
          >
            <div className="readiness-inner">
              <span 
                className="readiness-score" 
                style={{ color: getReadinessColor(readinessScore) }}
              >
                {Math.round(readinessScore)}%
              </span>
            </div>
          </div>
        </div>
      )}
      
      {/* Card Content */}
      <div className="mix-mode-content">
        <div className="mix-mode-icon">
          <FaShapes />
        </div>
        
        <h2 className="mix-mode-title">Adaptive Mix Mode</h2>
        
        <p className="mix-mode-tagline">Adaptive Learning Experience</p>
        
        <p className="mix-mode-description">
          Our intelligent system adapts to your performance in real-time. 
          Questions and flashcards are personalized based on importance and 
          your comfort level with each concept.
        </p>
        
        <div className="mix-mode-features">
          <div className="mix-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <circle cx="12" cy="12" r="6"/>
              <circle cx="12" cy="12" r="2"/>
            </svg>
            <span className="feature-text">Smart Prioritization</span>
          </div>
          <div className="mix-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
              <polyline points="16 7 22 7 22 13"/>
            </svg>
            <span className="feature-text">Adaptive Difficulty</span>
          </div>
          <div className="mix-feature">
            <svg className="feature-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            <span className="feature-text">Instant Remediation</span>
          </div>
        </div>
        
        <button className="mix-mode-button">
          Start Adaptive Mix Mode →
        </button>
      </div>
      
      {/* Premium Glow Effect */}
      <div className="mix-mode-glow"></div>
    </div>
  );
};

export default MixModeCard;

