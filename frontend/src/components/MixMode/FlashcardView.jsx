/**
 * FlashcardView - Wrapper for the actual Flashcard component in Mix Mode
 * 
 * Uses the existing premium Flashcard component with a continue button
 */

import React from 'react';
import { FaArrowRight } from 'react-icons/fa';
import Flashcard from '../Flashcard';
import './FlashcardView.css';

const FlashcardView = ({ flashcard, onContinue }) => {
  if (!flashcard) return null;
  
  // Extract course_id and deck_id from flashcard_id
  // Format: "SI_Pricing_2_11" -> courseId: from context, deckId: "SI_Pricing_2"
  const flashcardId = flashcard.flashcard_id || '';
  const parts = flashcardId.split('_');
  const deckId = parts.slice(0, -1).join('_'); // Everything except the last number
  
  return (
    <div className="mix-flashcard-view-container">
      {/* Header */}
      <div className="mix-flashcard-header">
        <div className="review-badge">
          <svg className="review-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="review-text">Review This Concept</span>
        </div>
        <p className="review-subtitle">
          Take a moment to review before continuing
        </p>
      </div>
      
      {/* Use the actual Flashcard component */}
      <div className="mix-flashcard-wrapper">
        <Flashcard
          card={flashcard}
          courseId="MS5150" // TODO: Get from context
          deckId={deckId}
          index={0}
          sessionId={null} // No session for Mix Mode flashcards
        />
      </div>
      
      {/* Continue Button */}
      <div className="mix-flashcard-actions">
        <button className="mix-continue-button" onClick={onContinue}>
          <span>Continue to Follow-up Question</span>
          <FaArrowRight />
        </button>
      </div>
    </div>
  );
};

export default FlashcardView;

