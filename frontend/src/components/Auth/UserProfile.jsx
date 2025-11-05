import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import './UserProfile.css';

const UserProfile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      setShowDropdown(false);
      // Redirect to landing page after logout
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!user) return null;

  // Get initials for fallback avatar
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const displayName = user.displayName || user.email?.split('@')[0] || 'User';
  const initials = getInitials(displayName);

  return (
    <div className="user-profile">
      <div 
        className="profile-trigger"
        onClick={() => setShowDropdown(!showDropdown)}
      >
        <div className="profile-avatar-fallback">
          {initials}
        </div>
        <span className="profile-name">{displayName}</span>
        <svg 
          className={`dropdown-arrow ${showDropdown ? 'open' : ''}`} 
          width="12" 
          height="12" 
          viewBox="0 0 12 12"
        >
          <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="2" fill="none"/>
        </svg>
      </div>

      {showDropdown && (
        <div className="profile-dropdown">
          <div className="dropdown-header">
            <div className="dropdown-avatar-fallback">
              {initials}
            </div>
            <div className="dropdown-info">
              <div className="dropdown-name">{displayName}</div>
              <div className="dropdown-email">{user.email}</div>
            </div>
          </div>
          <div className="dropdown-divider"></div>
          <button className="dropdown-item logout-button" onClick={handleLogout}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" strokeWidth="2"/>
              <polyline points="16,17 21,12 16,7" stroke="currentColor" strokeWidth="2"/>
              <line x1="21" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="2"/>
            </svg>
            Sign Out
          </button>
        </div>
      )}

      {showDropdown && (
        <div 
          className="dropdown-overlay" 
          onClick={() => setShowDropdown(false)}
        ></div>
      )}
    </div>
  );
};

export default UserProfile;
