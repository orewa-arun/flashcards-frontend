import React, { useState, useRef, useEffect } from 'react';
import { FaPaperPlane, FaComments, FaSpinner } from 'react-icons/fa';
import { getFlashcardChat } from '../../api/flashcardChat';
import './FlashcardChatInput.css';

/**
 * FlashcardChatInput - Input bar shown below flashcards for context-aware chat
 * 
 * Props:
 * - flashcardId: Unique identifier for the flashcard
 * - courseId: Course identifier
 * - lectureId: Lecture identifier
 * - flashcardContext: The current flashcard content (question + answers)
 * - onOpenModal: Callback to open the full chat modal
 * - disabled: Whether input is disabled
 */
const FlashcardChatInput = ({
  flashcardId,
  courseId,
  lectureId,
  flashcardContext,
  onOpenModal,
  disabled = false
}) => {
  const [inputValue, setInputValue] = useState('');
  const [hasExistingChat, setHasExistingChat] = useState(false);
  const [checkingChat, setCheckingChat] = useState(true);
  const inputRef = useRef(null);
  const fetchedRef = useRef(null);

  // Check if there's an existing chat for this flashcard
  useEffect(() => {
    const checkExistingChat = async () => {
      if (!flashcardId || fetchedRef.current === flashcardId) {
        setCheckingChat(false);
        return;
      }

      try {
        setCheckingChat(true);
        const chat = await getFlashcardChat(flashcardId);
        setHasExistingChat(chat && chat.messages && chat.messages.length > 0);
        fetchedRef.current = flashcardId;
      } catch (error) {
        console.error('Error checking for existing chat:', error);
        setHasExistingChat(false);
      } finally {
        setCheckingChat(false);
      }
    };

    checkExistingChat();
  }, [flashcardId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || disabled) return;

    // Open modal with the message to send
    onOpenModal(inputValue.trim());
    setInputValue('');
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleExpandClick = () => {
    onOpenModal('');
  };

  return (
    <div className="flashcard-chat-input-container">
      <form onSubmit={handleSubmit} className="chat-input-form">
        <button
          type="button"
          className="expand-chat-btn"
          onClick={handleExpandClick}
          disabled={disabled}
          title={hasExistingChat ? 'Continue conversation' : 'Start a conversation'}
        >
          <FaComments />
          {!checkingChat && hasExistingChat && (
            <span className="chat-indicator-dot" />
          )}
        </button>
        
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={
            checkingChat 
              ? 'Loading...' 
              : hasExistingChat 
                ? 'Continue your conversation...' 
                : 'Ask a question about this flashcard...'
          }
          disabled={disabled || checkingChat}
          className="chat-input-field"
        />
        
        <button
          type="submit"
          disabled={!inputValue.trim() || disabled || checkingChat}
          className="send-message-btn"
          title="Send message"
        >
          {checkingChat ? <FaSpinner className="spin" /> : <FaPaperPlane />}
        </button>
      </form>
      
      <p className="chat-hint">
        Press Enter to send, or click the chat icon to expand
      </p>
    </div>
  );
};

export default FlashcardChatInput;

