import React from 'react';
import { FaPlus, FaComments, FaTrash } from 'react-icons/fa';
import './ConversationSidebar.css';

/**
 * Sidebar component for displaying conversation history
 * ChatGPT-style layout with conversation list
 */
function ConversationSidebar({ 
  conversations, 
  currentConversationId, 
  onSelectConversation, 
  onNewChat, 
  onDeleteConversation,
  isLoading 
}) {
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) {
      return 'Today';
    } else if (diffInDays === 1) {
      return 'Yesterday';
    } else if (diffInDays < 7) {
      return `${diffInDays} days ago`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const handleDelete = (e, conversationId) => {
    e.stopPropagation(); // Prevent selecting conversation when deleting
    
    const confirmed = window.confirm('Are you sure you want to delete this conversation? This action cannot be undone.');
    if (confirmed) {
      onDeleteConversation(conversationId);
    }
  };

  return (
    <div className="conversation-sidebar">
      <div className="sidebar-header">
        <button className="new-chat-button" onClick={onNewChat}>
          <FaPlus /> New Chat
        </button>
      </div>

      <div className="conversations-list">
        {isLoading && (
          <div className="sidebar-loading">
            <div className="loading-spinner"></div>
            <p>Loading conversations...</p>
          </div>
        )}

        {!isLoading && conversations.length === 0 && (
          <div className="empty-conversations">
            <FaComments className="empty-icon" />
            <p>No conversations yet</p>
            <span>Start a new chat to begin</span>
          </div>
        )}

        {!isLoading && conversations.map((conversation) => (
          <div
            key={conversation.conversation_id}
            className={`conversation-item ${
              currentConversationId === conversation.conversation_id ? 'active' : ''
            }`}
            onClick={() => onSelectConversation(conversation.conversation_id)}
          >
            <div className="conversation-content">
              <h4 className="conversation-title">{conversation.title}</h4>
              <p className="conversation-date">{formatDate(conversation.updated_at)}</p>
            </div>
            <button
              className="delete-conversation-button"
              onClick={(e) => handleDelete(e, conversation.conversation_id)}
              title="Delete conversation"
            >
              <FaTrash />
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="new-chat-button-bottom" onClick={onNewChat}>
          <FaPlus /> New Chat
        </button>
      </div>
    </div>
  );
}

export default ConversationSidebar;

