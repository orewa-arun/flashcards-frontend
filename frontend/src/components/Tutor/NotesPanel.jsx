import React from 'react';
import './NotesPanel.css';

function NotesPanel({ notes, onChange, isSaving, lastSavedAt, disabled = false }) {
  return (
    <div className="notes-panel">
      <div className="notes-panel-header">
        <div>
          <h3>Conversation Notes</h3>
          <p>Select text from the chat to add it here, or type directly.</p>
        </div>
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
    </div>
  );
}

export default NotesPanel;

