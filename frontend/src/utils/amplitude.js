import * as amplitude from '@amplitude/analytics-browser';
import { sessionReplayPlugin } from '@amplitude/plugin-session-replay-browser';

let isInitialized = false;

/**
 * Initialize Amplitude analytics
 * Should be called once when the app starts
 */
export const initializeAmplitude = () => {
  const apiKey = import.meta.env.VITE_AMPLITUDE_API_KEY;
  
  if (!apiKey) {
    console.warn('Amplitude API key not found. Analytics will not be tracked.');
    return;
  }

  if (isInitialized) {
    console.log('Amplitude already initialized');
    return;
  }

  try {
    // Initialize Session Replay plugin BEFORE amplitude.init
    const sessionReplay = sessionReplayPlugin({
      sampleRate: 1, // 100% in development (lower to 0.1-0.3 in production)
      privacyConfig: {
        maskAllInputs: true, // Mask all input fields
        maskAllText: false, // Allow UI text to be visible
        maskTextSelector: 'input, textarea, [contenteditable]', // Mask these elements
        blockSelector: '[data-sensitive], .sensitive-data', // Completely block these elements
      },
    });

    amplitude.init(apiKey, {
      serverZone: 'EU', // EU data center
      defaultTracking: {
        sessions: true,
        pageViews: true,
        formInteractions: false,
        fileDownloads: false,
      },
    }).promise.then(() => {
      // Add Session Replay plugin after init completes
      amplitude.add(sessionReplay);
      console.log('Amplitude initialized successfully with Session Replay');
    });
    
    isInitialized = true;
  } catch (error) {
    console.error('Failed to initialize Amplitude:', error);
    console.error('Error details:', error.message);
    // Don't throw - allow app to continue without analytics
  }
};

/**
 * Identify a user in Amplitude
 * @param {string} userId - The unique user ID (Firebase UID)
 * @param {Object} userProperties - Additional user properties (name, email, etc.)
 */
export const identifyUser = (userId, userProperties = {}) => {
  if (!isInitialized) {
    console.warn('Amplitude not initialized. Cannot identify user.');
    return;
  }

  try {
    amplitude.setUserId(userId);
    
    if (Object.keys(userProperties).length > 0) {
      const identifyEvent = new amplitude.Identify();
      
      Object.entries(userProperties).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          identifyEvent.set(key, value);
        }
      });
      
      amplitude.identify(identifyEvent);
    }
    
    console.log('User identified in Amplitude:', userId);
  } catch (error) {
    console.error('Failed to identify user in Amplitude:', error);
  }
};

/**
 * Track a custom event in Amplitude
 * @param {string} eventName - The name of the event
 * @param {Object} eventProperties - Additional properties for the event
 */
export const trackEvent = (eventName, eventProperties = {}) => {
  if (!isInitialized) {
    console.warn('Amplitude not initialized. Cannot track event:', eventName);
    return;
  }

  try {
    amplitude.track(eventName, eventProperties);
    console.log('Event tracked:', eventName, eventProperties);
  } catch (error) {
    console.error('Failed to track event in Amplitude:', error);
  }
};

/**
 * Reset user identity (on logout)
 */
export const resetUser = () => {
  if (!isInitialized) {
    return;
  }

  try {
    amplitude.reset();
    console.log('Amplitude user reset');
  } catch (error) {
    console.error('Failed to reset Amplitude user:', error);
  }
};

export default {
  initializeAmplitude,
  identifyUser,
  trackEvent,
  resetUser,
};

