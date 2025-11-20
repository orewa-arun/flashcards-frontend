import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaChevronRight, FaPaperPlane, FaRobot, FaUser } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { trackEvent } from '../utils/amplitude';
import {
  createConversation,
  getConversations,
  getConversation,
  sendMessage,
  deleteConversation,
  updateConversationNotes
} from '../api/tutorApi';
import ConversationSidebar from '../components/Tutor/ConversationSidebar';
import NotesPanel from '../components/Tutor/NotesPanel';
import './TutorChatView.css';

/**
 * Preprocess markdown content to fix common issues
 * - Fixes malformed tables (all on one line with excessive spaces)
 * - Normalizes whitespace
 */
const preprocessMarkdown = (content) => {
  if (!content) return content;
  
  let processed = content;
  
  // Fix malformed tables: detect table header followed by excessive whitespace
  // Pattern: | Header1 | Header2 | followed by 50+ spaces (indicates malformed table)
  processed = processed.replace(/(\|[^|\n]+\|[^|\n]+\|(?:\s+\|[^|\n]+)*)\s{50,}/g, (match, tableHeader) => {
    // Extract column headers
    const columns = tableHeader.split('|')
      .map(col => col.trim())
      .filter(col => col.length > 0);
    
    if (columns.length >= 2) {
      // Create a proper markdown table with header and separator
      const header = '| ' + columns.join(' | ') + ' |\n';
      const separator = '| ' + columns.map(() => '---').join(' | ') + ' |\n';
      // Add a note that the table content was incomplete
      const note = '| ' + columns.map(() => '*Content not available*').join(' | ') + ' |\n';
      return header + separator + note;
    }
    return match;
  });
  
  // Alternative pattern: table header with trailing spaces on same line
  processed = processed.replace(/(\|[^|\n]+\|[^|\n]+\|(?:\s+\|[^|\n]+)*)\s{20,}(?=\n|$)/g, (match, tableHeader) => {
    const columns = tableHeader.split('|')
      .map(col => col.trim())
      .filter(col => col.length > 0);
    
    if (columns.length >= 2) {
      const header = '| ' + columns.join(' | ') + ' |\n';
      const separator = '| ' + columns.map(() => '---').join(' | ') + ' |\n';
      return header + separator;
    }
    return match;
  });
  
  // Normalize excessive whitespace (but preserve intentional spacing in code blocks)
  // Don't normalize inside code blocks
  const codeBlockRegex = /```[\s\S]*?```/g;
  const codeBlocks = [];
  let codeBlockIndex = 0;
  
  processed = processed.replace(codeBlockRegex, (match) => {
    const placeholder = `__CODE_BLOCK_${codeBlockIndex}__`;
    codeBlocks[codeBlockIndex] = match;
    codeBlockIndex++;
    return placeholder;
  });
  
  // Normalize whitespace outside code blocks
  processed = processed.replace(/[ \t]{3,}/g, ' ');
  processed = processed.replace(/\n{4,}/g, '\n\n'); // Max 2 consecutive newlines
  
  // Restore code blocks
  codeBlocks.forEach((block, index) => {
    processed = processed.replace(`__CODE_BLOCK_${index}__`, block);
  });
  
  return processed;
};

function TutorChatView() {
  const { courseId, lectureId, conversationId } = useParams();
  const navigate = useNavigate();
  const [courseData, setCourseData] = useState(null);
  const [lectureData, setLectureData] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarLoading, setIsSidebarLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notes, setNotes] = useState('');
  const [isNotesSaving, setIsNotesSaving] = useState(false);
  const [lastNotesSavedAt, setLastNotesSavedAt] = useState(null);
  const notesSaveTimeoutRef = useRef(null);
  const chatMessagesRef = useRef(null);
  const [selectionPrompt, setSelectionPrompt] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Load course and lecture data
  useEffect(() => {
    fetch('/courses.json')
      .then(response => response.json())
      .then(data => {
        const course = data.find(c => c.course_id === courseId);
        if (course) {
          setCourseData(course);
          const lecture = course.lecture_slides?.find(slide => {
            const pdfFilename = slide.pdf_path.split('/').pop().replace('.pdf', '');
            return pdfFilename === lectureId;
          });
          setLectureData(lecture);
        }
      })
      .catch(error => console.error('Error loading course data:', error));
  }, [courseId, lectureId]);

  // Load conversations list
  const loadConversations = async () => {
    try {
      setIsSidebarLoading(true);
      const convs = await getConversations(courseId, lectureId);
      setConversations(convs);
    } catch (error) {
      console.error('Error loading conversations:', error);
    } finally {
      setIsSidebarLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [courseId, lectureId]);

  // Load specific conversation when conversationId changes
  useEffect(() => {
    if (conversationId) {
      loadConversationMessages(conversationId);
    } else {
      // No conversation selected - show empty state
      setCurrentConversation(null);
      setMessages([]);
      setNotes('');
      setIsNotesSaving(false);
      setSelectionPrompt(null);
    }
  }, [conversationId]);

  const loadConversationMessages = async (convId) => {
    try {
      setIsLoading(true);
      const conversation = await getConversation(convId);
      setCurrentConversation(conversation);
      setNotes(conversation.notes || '');
      setLastNotesSavedAt(conversation.notes ? new Date(conversation.updated_at) : null);
      setIsNotesSaving(false);
      setSelectionPrompt(null);
      
      // Convert messages to display format
      const formattedMessages = conversation.messages.map(msg => ({
              role: msg.role,
              content: msg.content,
        timestamp: new Date(msg.timestamp)
            }));
      setMessages(formattedMessages);
    } catch (error) {
      console.error('Error loading conversation:', error);
      setError('Failed to load conversation. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cleanup notes save timer on unmount
  useEffect(() => {
    return () => {
      if (notesSaveTimeoutRef.current) {
        clearTimeout(notesSaveTimeoutRef.current);
      }
    };
  }, []);

  // Track page view
  useEffect(() => {
    trackEvent('Viewed AI Tutor Chat', { courseId, lectureId });
  }, [courseId, lectureId]);

  const handleNewChat = async () => {
    try {
      const newConvId = await createConversation(courseId, lectureId);
      await loadConversations(); // Refresh sidebar
      navigate(`/courses/${courseId}/${lectureId}/tutor/${newConvId}`);
      trackEvent('Created New Chat', { courseId, lectureId });
    } catch (error) {
      console.error('Error creating conversation:', error);
      setError('Failed to create new chat. Please try again.');
    }
  };

  const handleSelectConversation = (convId) => {
    navigate(`/courses/${courseId}/${lectureId}/tutor/${convId}`);
  };

  const handleDeleteConversation = async (convId) => {
    try {
      await deleteConversation(convId);
      await loadConversations(); // Refresh sidebar
      
      // If deleted conversation was active, navigate to empty state
      if (convId === conversationId) {
        navigate(`/courses/${courseId}/${lectureId}/tutor`);
      }
      
      trackEvent('Deleted Chat', { courseId, lectureId });
    } catch (error) {
      console.error('Error deleting conversation:', error);
      setError('Failed to delete conversation. Please try again.');
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    // If no conversation is active, create one first
    if (!conversationId) {
      await handleNewChat();
      // Wait a bit for the conversation to be created and navigation to happen
      setTimeout(() => {
        // The inputMessage will still be there, user can send again
      }, 500);
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setError(null);

    // Add user message to chat immediately for better UX
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);

    // Track message sent
    trackEvent('Sent Tutor Message', { courseId, lectureId, messageLength: userMessage.length });

    setIsLoading(true);

    try {
      // Send message to backend
      const response = await sendMessage(conversationId, userMessage);

      // Add assistant response to chat
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Refresh conversations list to update the title and timestamp
      await loadConversations();

      // Track response received
      trackEvent('Received Tutor Response', { 
        courseId, 
        lectureId, 
        responseLength: response.answer.length 
      });
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to get response. Please try again.');
      
      // Remove the user message if request failed
      setMessages(prev => prev.slice(0, -1));
      
      // Restore the input
      setInputMessage(userMessage);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Format lecture ID for display
  const formatLectureTitle = (id) => {
    return id
      .replace(/_/g, ' ')
      .replace(/lec/i, 'Lecture')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const scheduleNotesSave = (content) => {
    if (!conversationId) return;
    setIsNotesSaving(true);
    if (notesSaveTimeoutRef.current) {
      clearTimeout(notesSaveTimeoutRef.current);
    }
    notesSaveTimeoutRef.current = setTimeout(() => {
      saveNotesToServer(content);
    }, 1000);
  };

  const saveNotesToServer = async (content) => {
    if (!conversationId) return;
    try {
      await updateConversationNotes(conversationId, content);
      setIsNotesSaving(false);
      setLastNotesSavedAt(new Date());
    } catch (err) {
      console.error('Error saving notes:', err);
      setIsNotesSaving(false);
    }
  };

  const handleNotesChange = (value) => {
    setNotes(value);
    scheduleNotesSave(value);
  };

  const handleChatMouseUp = () => {
    if (!conversationId) return;
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setSelectionPrompt(null);
      return;
    }
    const text = selection.toString().trim();
    if (!text) {
      setSelectionPrompt(null);
      return;
    }
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const container = chatMessagesRef.current;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    setSelectionPrompt({
      text,
      top: rect.top - containerRect.top + container.scrollTop - 40,
      left: rect.left - containerRect.left
    });
  };

  const clearSelectionPrompt = () => {
    setSelectionPrompt(null);
    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
    }
  };

  const handleAddSelectionToNotes = () => {
    if (!selectionPrompt?.text) return;
    setNotes(prev => {
      const updated = prev ? `${prev}\n\n${selectionPrompt.text}` : selectionPrompt.text;
      scheduleNotesSave(updated);
      return updated;
    });
    clearSelectionPrompt();
  };

  return (
    <div className="tutor-chat-view-container">
      <ConversationSidebar
        conversations={conversations}
        currentConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        isLoading={isSidebarLoading}
      />

      <div className="tutor-main-content">
    <div className="tutor-chat-view">
      <div className="tutor-chat-container">
        {/* Header */}
        <header className="tutor-header">
          {/* Breadcrumb Navigation */}
          <nav className="breadcrumb-nav">
            <button onClick={() => navigate('/courses')} className="breadcrumb-link">
              Courses
            </button>
            <FaChevronRight className="breadcrumb-separator" />
            <button onClick={() => navigate(`/courses/${courseId}`)} className="breadcrumb-link">
              {courseData?.course_name || courseId}
            </button>
            <FaChevronRight className="breadcrumb-separator" />
            <button onClick={() => navigate(`/courses/${courseId}/${lectureId}`)} className="breadcrumb-link">
              {lectureData?.lecture_name || formatLectureTitle(lectureId)}
            </button>
            <FaChevronRight className="breadcrumb-separator" />
            <span className="breadcrumb-current">AI Tutor</span>
          </nav>

            {/* Title */}
          <div className="tutor-header-content">
            <div className="tutor-header-left">
              <div className="tutor-icon-header">
                <FaRobot />
              </div>
              <div>
                <h1 className="tutor-header-title">AI Tutor</h1>
                <p className="tutor-header-subtitle">
                  {lectureData?.lecture_name || formatLectureTitle(lectureId)}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Chat Messages Area */}
          <div
            className="chat-messages-area"
            ref={chatMessagesRef}
            onMouseUp={handleChatMouseUp}
            onScroll={clearSelectionPrompt}
          >
            {selectionPrompt && (
              <button
                className="add-to-notes-button"
                style={{
                  top: `${selectionPrompt.top}px`,
                  left: `${selectionPrompt.left}px`
                }}
                onClick={handleAddSelectionToNotes}
              >
                + Add to Notes
              </button>
            )}
            {messages.length === 0 && !error && !conversationId && (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FaRobot />
              </div>
              <h2 className="empty-state-title">Welcome to your AI Tutor!</h2>
              <p className="empty-state-description">
                Ask me anything about {lectureData?.lecture_name || 'this lecture'}. 
                I can help you understand concepts, clarify doubts, and provide detailed explanations.
              </p>
              <div className="example-questions">
                <p className="example-questions-title">Try asking:</p>
                <button 
                  className="example-question"
                  onClick={() => setInputMessage("Can you explain the main concepts from this lecture?")}
                >
                  "Can you explain the main concepts from this lecture?"
                </button>
                <button 
                  className="example-question"
                  onClick={() => setInputMessage("What are the key takeaways I should remember?")}
                >
                  "What are the key takeaways I should remember?"
                </button>
                <button 
                  className="example-question"
                  onClick={() => setInputMessage("Can you give me a real-world example?")}
                >
                  "Can you give me a real-world example?"
                </button>
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div 
              key={index} 
              className={`chat-message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <div className="message-avatar">
                {message.role === 'user' ? <FaUser /> : <FaRobot />}
              </div>
              <div className="message-content">
                {message.role === 'assistant' ? (
                  <div className="message-text markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {preprocessMarkdown(message.content)}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <div className="message-text">{message.content}</div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-message assistant-message">
              <div className="message-avatar">
                <FaRobot />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              <p>{error}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          <div className="chat-input-container">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask a question about this lecture..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
                disabled={isLoading}
              rows={1}
            />
            <button 
              className="send-button" 
              onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
            >
              <FaPaperPlane />
            </button>
          </div>
          <p className="chat-input-hint">
            Press Enter to send, Shift+Enter for new line
          </p>
          </div>
          </div>
        </div>

        <div className="notes-panel-wrapper">
          <NotesPanel
            notes={notes}
            onChange={handleNotesChange}
            isSaving={isNotesSaving}
            lastSavedAt={lastNotesSavedAt}
            disabled={!conversationId}
          />
        </div>
      </div>
    </div>
  );
}

export default TutorChatView;
