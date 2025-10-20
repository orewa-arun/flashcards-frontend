/**
 * User tracking utilities for anonymous analytics
 */

import Cookies from 'js-cookie';
import { v4 as uuidv4 } from 'uuid';

const USER_COOKIE_KEY = 'study_user_id';
const COOKIE_CONSENT_KEY = 'cookie_consent';
const ANALYTICS_ENABLED_KEY = 'analytics_enabled';

/**
 * Get or create a user ID for analytics tracking
 * @returns {string} UUID v4 string
 */
export function getUserId() {
  let userId = Cookies.get(USER_COOKIE_KEY);
  
  if (!userId) {
    userId = uuidv4();
    // Set cookie with 1 year expiration
    Cookies.set(USER_COOKIE_KEY, userId, { expires: 365, sameSite: 'strict' });
    console.log('Generated new user ID for analytics:', userId);
  }
  
  return userId;
}

/**
 * Check if user has consented to cookies
 * @returns {boolean}
 */
export function hasCookieConsent() {
  return Cookies.get(COOKIE_CONSENT_KEY) === 'true';
}

/**
 * Set cookie consent status
 * @param {boolean} consent - Whether user consents to cookies
 */
export function setCookieConsent(consent) {
  if (consent) {
    Cookies.set(COOKIE_CONSENT_KEY, 'true', { expires: 365, sameSite: 'strict' });
    Cookies.set(ANALYTICS_ENABLED_KEY, 'true', { expires: 365, sameSite: 'strict' });
    // Generate user ID now that consent is given
    getUserId();
  } else {
    Cookies.set(COOKIE_CONSENT_KEY, 'false', { expires: 365, sameSite: 'strict' });
    Cookies.set(ANALYTICS_ENABLED_KEY, 'false', { expires: 365, sameSite: 'strict' });
    // Remove user tracking cookie if it exists
    Cookies.remove(USER_COOKIE_KEY);
  }
}

/**
 * Check if analytics tracking is enabled
 * @returns {boolean}
 */
export function isAnalyticsEnabled() {
  const consent = hasCookieConsent();
  const enabled = Cookies.get(ANALYTICS_ENABLED_KEY) === 'true';
  return consent && enabled;
}

/**
 * Check if we should show the cookie banner
 * @returns {boolean}
 */
export function shouldShowCookieBanner() {
  return Cookies.get(COOKIE_CONSENT_KEY) === undefined;
}

/**
 * Initialize user tracking (call this on app startup)
 */
export function initializeUserTracking() {
  // Only generate user ID if user has consented
  if (isAnalyticsEnabled()) {
    getUserId();
    console.log('Analytics tracking initialized');
  } else {
    console.log('Analytics tracking disabled - no consent');
  }
}

/**
 * Clear all tracking data (for opt-out)
 */
export function clearTrackingData() {
  Cookies.remove(USER_COOKIE_KEY);
  Cookies.remove(ANALYTICS_ENABLED_KEY);
  console.log('Tracking data cleared');
}
