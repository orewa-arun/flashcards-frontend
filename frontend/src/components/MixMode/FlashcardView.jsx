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
          <span className="review-icon">💡</span>
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

