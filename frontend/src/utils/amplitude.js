import * as amplitude from '@amplitude/analytics-browser';
import { sessionReplayPlugin } from '@amplitude/plugin-session-replay-browser';

let isInitialized = false;
let isInitializing = false;
let queuedEvents = []; // Queue for events fired before initialization completes

/**
 * Initialize Amplitude analytics
 * Should be called once when the app starts
 * @returns {Promise<void>} Promise that resolves when initialization is complete
 */
export const initializeAmplitude = () => {
  const apiKey = import.meta.env.VITE_AMPLITUDE_API_KEY;
  
  if (!apiKey) {
    console.warn('Amplitude API key not found. Analytics will not be tracked.');
    isInitialized = false; // Explicitly mark as not initialized
    return Promise.resolve();
  }

  if (isInitialized) {
    console.log('Amplitude already initialized');
    return Promise.resolve();
  }

  if (isInitializing) {
    console.log('Amplitude initialization already in progress');
    return Promise.resolve();
  }

  isInitializing = true;

  try {
    // Initialize Session Replay plugin BEFORE amplitude.init
    const sessionReplay = sessionReplayPlugin({
      sampleRate: 0.3, // 30% in production (adjust as needed)
      privacyConfig: {
        maskAllInputs: true, // Mask all input fields
        maskAllText: false, // Allow UI text to be visible
        maskTextSelector: 'input, textarea, [contenteditable]', // Mask these elements
        blockSelector: '[data-sensitive], .sensitive-data', // Completely block these elements
      },
    });

    return amplitude.init(apiKey, {
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
      
      // CRITICAL: Only set isInitialized to true AFTER Amplitude confirms it's ready
      isInitialized = true;
      isInitializing = false;
      
      console.log('✅ Amplitude initialized successfully with Session Replay');
      
      // Flush queued events
      if (queuedEvents.length > 0) {
        console.log(`📤 Flushing ${queuedEvents.length} queued events to Amplitude`);
        queuedEvents.forEach(({ eventName, eventProperties }) => {
          amplitude.track(eventName, eventProperties);
        });
        queuedEvents = []; // Clear the queue
      }
    }).catch((error) => {
      console.error('❌ Failed to initialize Amplitude:', error);
      isInitialized = false;
      isInitializing = false;
      // Don't throw - allow app to continue without analytics
    });
  } catch (error) {
    console.error('❌ Failed to initialize Amplitude:', error);
    console.error('Error details:', error.message);
    isInitialized = false;
    isInitializing = false;
    return Promise.reject(error);
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
  // If Amplitude is still initializing or not initialized, queue the event
  if (!isInitialized) {
    if (isInitializing) {
      // Queue the event - it will be sent once initialization completes
      queuedEvents.push({ eventName, eventProperties });
      console.log(`⏳ Queued event (Amplitude initializing): ${eventName}`);
    } else {
      // Amplitude failed to initialize or API key is missing - silently skip
      console.debug(`⚠️ Skipping event (Amplitude not available): ${eventName}`);
    }
    return;
  }

  try {
    amplitude.track(eventName, eventProperties);
    console.log('📊 Event tracked:', eventName, eventProperties);
  } catch (error) {
    console.error('❌ Failed to track event in Amplitude:', error);
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

