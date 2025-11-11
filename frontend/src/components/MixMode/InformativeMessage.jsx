/**
 * InformativeMessage - Contextual message for previously incorrect questions
 */

import React from 'react';
import { FaRedoAlt } from 'react-icons/fa';
import './InformativeMessage.css';

const InformativeMessage = ({ type = 'review' }) => {
  const messages = {
    review: {
      icon: <FaRedoAlt />,
      text: "Let's review this concept",
      className: 'review-message'
    },
    followUp: {
      icon: <FaRedoAlt />,
      text: "Follow-up question",
      className: 'followup-message'
    }
  };
  
  const message = messages[type] || messages.review;
  
  return (
    <div className={`informative-message ${message.className}`}>
      <span className="message-icon">{message.icon}</span>
      <span className="message-text">{message.text}</span>
    </div>
  );
};

export default InformativeMessage;

