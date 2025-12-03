import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { FaTimes, FaPaperPlane, FaSpinner, FaTrash, FaRobot, FaUser } from 'react-icons/fa';
import { 
  getFlashcardChat, 
  streamFlashcardMessage, 
  deleteFlashcardChat 
} from '../../api/flashcardChat';
import 'katex/dist/katex.min.css';
import './FlashcardChatModal.css';

/**
 * FlashcardChatModal - Full-screen modal for flashcard chat with streaming responses
 * 
 * Props:
 * - isOpen: Whether the modal is open
 * - onClose: Callback to close the modal
 * - flashcardId: Unique identifier for the flashcard
 * - courseId: Course identifier
 * - lectureId: Lecture identifier
 * - flashcardContext: The current flashcard content
 * - initialMessage: Optional message to send immediately on open
 */
const FlashcardChatModal = ({
  isOpen,
  onClose,
  flashcardId,
  courseId,
  lectureId,
  flashcardContext,
  initialMessage = ''
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState(null);
  const [chatExists, setChatExists] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const initialMessageSentRef = useRef(false);
  const loadedFlashcardRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // Load existing chat when modal opens
  const loadChat = useCallback(async () => {
    if (!flashcardId || loadedFlashcardRef.current === flashcardId) return;

    try {
      setIsLoading(true);
      setError(null);
      const chat = await getFlashcardChat(flashcardId);
      
      if (chat && chat.messages) {
        setMessages(chat.messages);
        setChatExists(true);
      } else {
        setMessages([]);
        setChatExists(false);
      }
      loadedFlashcardRef.current = flashcardId;
    } catch (err) {
      console.error('Error loading chat:', err);
      setError('Failed to load chat history');
      setMessages([]);
    } finally {
      setIsLoading(false);
    }
  }, [flashcardId]);

  useEffect(() => {
    if (isOpen && flashcardId) {
      loadChat();
      // Focus input after a short delay
      setTimeout(() => inputRef.current?.focus(), 300);
    }

    // Reset state when modal closes
    if (!isOpen) {
      setStreamingContent('');
      setIsStreaming(false);
      initialMessageSentRef.current = false;
    }
  }, [isOpen, flashcardId, loadChat]);

  // Handle initial message
  useEffect(() => {
    if (
      isOpen && 
      initialMessage && 
      !initialMessageSentRef.current && 
      !isLoading && 
      loadedFlashcardRef.current === flashcardId
    ) {
      initialMessageSentRef.current = true;
      sendMessage(initialMessage);
    }
  }, [isOpen, initialMessage, isLoading, flashcardId]);

  const sendMessage = async (messageText) => {
    if (!messageText.trim() || isStreaming) return;

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsStreaming(true);
    setStreamingContent('');
    setError(null);

    try {
      // Determine if we need to send flashcard context (first message only)
      const contextToSend = !chatExists ? flashcardContext : null;

      await streamFlashcardMessage(
        flashcardId,
        courseId,
        lectureId,
        messageText,
        contextToSend,
        (chunk) => {
          setStreamingContent(prev => prev + chunk);
        }
      );

      // After streaming completes, add the assistant message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: streamingContent + '', // Will be updated by the final state
        timestamp: new Date().toISOString()
      }]);
      
      setChatExists(true);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to get response. Please try again.');
    } finally {
      setIsStreaming(false);
    }
  };

  // Update the last assistant message with accumulated streaming content
  useEffect(() => {
    if (!isStreaming && streamingContent) {
      setMessages(prev => {
        const updated = [...prev];
        // Find or add the assistant message
        const lastAssistantIdx = updated.findIndex(
          (m, i) => m.role === 'assistant' && i === updated.length - 1
        );
        
        if (lastAssistantIdx >= 0) {
          updated[lastAssistantIdx] = {
            ...updated[lastAssistantIdx],
            content: streamingContent
          };
        } else if (streamingContent) {
          updated.push({
            role: 'assistant',
            content: streamingContent,
            timestamp: new Date().toISOString()
          });
        }
        
        return updated;
      });
      setStreamingContent('');
    }
  }, [isStreaming, streamingContent]);

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleClearChat = async () => {
    if (!window.confirm('Clear all chat history for this flashcard?')) return;

    try {
      await deleteFlashcardChat(flashcardId);
      setMessages([]);
      setChatExists(false);
      loadedFlashcardRef.current = null;
    } catch (err) {
      console.error('Error clearing chat:', err);
      setError('Failed to clear chat history');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="flashcard-chat-modal-overlay" onClick={onClose}>
      <div className="flashcard-chat-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="chat-modal-header">
          <div className="header-left">
            <img src="/logo.png" alt="Logo" className="chat-modal-logo" />
            <div className="header-title">
              <h2>Flashcard Assistant</h2>
              <p className="header-subtitle">Ask questions about this concept</p>
            </div>
          </div>
          <div className="header-actions">
            {chatExists && messages.length > 0 && (
              <button 
                className="clear-chat-btn" 
                onClick={handleClearChat}
                title="Clear chat history"
              >
                <FaTrash />
              </button>
            )}
            <button className="close-modal-btn" onClick={onClose} title="Close">
              <FaTimes />
            </button>
          </div>
        </div>

        {/* Flashcard Context Preview */}
        {flashcardContext && flashcardContext.question && (
          <div className="context-preview">
            <span className="context-label">Discussing:</span>
            <span className="context-question">{flashcardContext.question}</span>
          </div>
        )}

        {/* Messages Area */}
        <div className="chat-messages-area">
          {isLoading ? (
            <div className="chat-loading">
              <FaSpinner className="spin" />
              <p>Loading chat history...</p>
            </div>
          ) : messages.length === 0 && !isStreaming ? (
            <div className="chat-empty-state">
              <FaRobot className="empty-icon" />
              <h3>Ask me anything!</h3>
              <p>
                I have context about this flashcard and the lecture materials.
                Ask me to explain, give examples, or clarify any concepts.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg, idx) => (
                <div key={idx} className={`chat-message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? <FaUser /> : <FaRobot />}
                  </div>
                  <div className="message-content">
                    {msg.role === 'assistant' ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Streaming indicator */}
              {isStreaming && (
                <div className="chat-message assistant streaming">
                  <div className="message-avatar">
                    <FaRobot />
                  </div>
                  <div className="message-content">
                    {streamingContent ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                      >
                        {streamingContent}
                      </ReactMarkdown>
                    ) : (
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </>
          )}
          
          {error && (
            <div className="chat-error">
              <p>{error}</p>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}
        </div>

        {/* Input Area */}
        <form className="chat-input-area" onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your question..."
            disabled={isStreaming}
            className="modal-chat-input"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isStreaming}
            className="modal-send-btn"
          >
            {isStreaming ? <FaSpinner className="spin" /> : <FaPaperPlane />}
          </button>
        </form>
      </div>
    </div>
  );
};

export default FlashcardChatModal;

