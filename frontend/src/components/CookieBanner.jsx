/**
 * Cookie consent banner component for GDPR compliance
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { shouldShowCookieBanner, setCookieConsent } from '../utils/userTracking';
import './CookieBanner.css';

function CookieBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if we should show the banner
    setIsVisible(shouldShowCookieBanner());
  }, []);

  const handleAccept = () => {
    setCookieConsent(true);
    setIsVisible(false);
  };

  const handleDecline = () => {
    setCookieConsent(false);
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="cookie-banner">
      <div className="cookie-banner-content">
        <div className="cookie-banner-text">
          <p>
            🍪 We use cookies to track your study progress anonymously and improve your learning experience. 
            No personal information is collected.
          </p>
        </div>
        <div className="cookie-banner-actions">
          <button 
            className="cookie-btn cookie-btn-accept" 
            onClick={handleAccept}
          >
            Accept & Continue
          </button>
          <button 
            className="cookie-btn cookie-btn-decline" 
            onClick={handleDecline}
          >
            Decline
          </button>
          <Link 
            to="/privacy-policy" 
            className="cookie-btn cookie-btn-learn-more"
          >
            Learn More
          </Link>
        </div>
      </div>
    </div>
  );
}

export default CookieBanner;
