import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './NotesPanel.css';

function NotesPanel({ 
  notes, 
  onChange, 
  isSaving, 
  lastSavedAt, 
  disabled = false,
  actionLabel,
  onAction 
}) {
  const [isPreview, setIsPreview] = useState(false);

  return (
    <div className="notes-panel">
      <div className="notes-panel-header">
        <div>
          <h3>Conversation Notes</h3>
          <p>Select text from the chat to add it here, or type directly.</p>
        </div>
        <div className="notes-panel-header-right">
          <div className="notes-panel-controls">
            <button 
              type="button"
              className={`notes-mode-button ${!isPreview ? 'active' : ''}`}
              onClick={() => setIsPreview(false)}
            >
              Write
            </button>
            <button 
              type="button"
              className={`notes-mode-button ${isPreview ? 'active' : ''}`}
              onClick={() => setIsPreview(true)}
            >
              Preview
            </button>
          </div>

          {actionLabel && onAction && (
            <button 
              type="button" 
              className="notes-panel-action-button"
              onClick={onAction}
            >
              {actionLabel}
            </button>
          )}
          <div className="notes-status">
            {isSaving ? (
              <span className="notes-status-saving">Saving...</span>
            ) : lastSavedAt ? (
              <span className="notes-status-saved">
                Saved {lastSavedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            ) : null}
          </div>
        </div>
      </div>

      {isPreview ? (
        <div className="notes-preview markdown-content">
          {notes ? (
            <ReactMarkdown 
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeKatex]}
            >
              {notes}
            </ReactMarkdown>
          ) : (
            <p className="notes-placeholder-text">Nothing to preview yet.</p>
          )}
        </div>
      ) : (
        <textarea
          className="notes-textarea"
          value={notes}
          onChange={(e) => onChange(e.target.value)}
          placeholder={
            disabled
              ? "Start a conversation to take notes."
              : "Highlight text in the chat and click “Add to Notes” or type here..."
          }
          disabled={disabled}
        />
      )}
    </div>
  );
}

export default NotesPanel;

