import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import './AuthModal.css';

const AuthModal = ({ isOpen, onClose, initialMode = 'signup' }) => {
  const { signInWithGoogle } = useAuth();
  const [mode, setMode] = useState(initialMode); // 'signup' or 'login'
  const [step, setStep] = useState('email'); // 'email' or 'password'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Reset modal state when it closes
  const handleClose = () => {
    setStep('email');
    setEmail('');
    setPassword('');
    setError('');
    setLoading(false);
    onClose();
  };

  // Handle Google OAuth
  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError('');
    try {
      await signInWithGoogle();
      handleClose();
    } catch (err) {
      setError(err.message || 'Failed to sign in with Google');
      setLoading(false);
    }
  };

  // Handle email step (validation and move to password)
  const handleEmailContinue = (e) => {
    e.preventDefault();
    setError('');
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setError('Please enter your email address');
      return;
    }
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setStep('password');
  };

  // Handle password step (create account or sign in)
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!password) {
      setError('Please enter a password');
      setLoading(false);
      return;
    }

    if (mode === 'signup' && password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      // TODO: Implement email/password authentication
      // For now, we'll show a message that only Google auth is available
      setError('Email/password authentication coming soon. Please use Google Sign-In.');
      setLoading(false);
    } catch (err) {
      setError(err.message || 'Authentication failed');
      setLoading(false);
    }
  };

  // Go back to email step
  const handleBack = () => {
    setStep('email');
    setPassword('');
    setError('');
  };

  // Toggle between signup and login
  const toggleMode = () => {
    setMode(mode === 'signup' ? 'login' : 'signup');
    setStep('email');
    setPassword('');
    setError('');
  };

  if (!isOpen) return null;

  return (
    <div className="auth-modal-overlay" onClick={handleClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="auth-modal-close" onClick={handleClose} aria-label="Close">
          ×
        </button>

        {step === 'email' ? (
          // Email Step
          <div className="auth-modal-content">
            <h2 className="auth-modal-title">
              {mode === 'signup' ? 'Get Started' : 'Welcome Back'}
            </h2>
            
            <button 
              className="auth-google-button"
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>

            <div className="auth-divider">
              <span>or {mode === 'signup' ? 'sign up' : 'sign in'} with email</span>
            </div>

            <form onSubmit={handleEmailContinue}>
              <div className="auth-form-group">
                <label htmlFor="email" className="auth-label">Email address</label>
                <input
                  type="email"
                  id="email"
                  className="auth-input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  autoFocus
                />
              </div>

              {error && <div className="auth-error">{error}</div>}

              <button 
                type="submit" 
                className="auth-submit-button"
                disabled={loading}
              >
                Continue →
              </button>
            </form>

            <div className="auth-toggle">
              {mode === 'signup' ? (
                <>
                  Already have an account?{' '}
                  <button onClick={toggleMode} className="auth-toggle-link">
                    Log in
                  </button>
                </>
              ) : (
                <>
                  Don't have an account?{' '}
                  <button onClick={toggleMode} className="auth-toggle-link">
                    Sign up
                  </button>
                </>
              )}
            </div>
          </div>
        ) : (
          // Password Step
          <div className="auth-modal-content">
            <button className="auth-back-button" onClick={handleBack}>
              ← Back
            </button>

            <h2 className="auth-modal-title">
              {mode === 'signup' ? 'Create your password' : 'Enter your password'}
            </h2>

            <div className="auth-email-display">
              <span className="auth-email-label">Email:</span>
              <span className="auth-email-value">{email}</span>
            </div>

            <form onSubmit={handlePasswordSubmit}>
              <div className="auth-form-group">
                <label htmlFor="password" className="auth-label">Password</label>
                <input
                  type="password"
                  id="password"
                  className="auth-input"
                  placeholder={mode === 'signup' ? 'Create a password (min. 6 characters)' : 'Enter your password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  autoFocus
                />
              </div>

              {error && <div className="auth-error">{error}</div>}

              <button 
                type="submit" 
                className="auth-submit-button"
                disabled={loading}
              >
                {loading ? 'Please wait...' : mode === 'signup' ? 'Create Account →' : 'Sign In →'}
              </button>
            </form>

            {mode === 'login' && (
              <div className="auth-forgot-password">
                <button className="auth-forgot-link">
                  Forgot password?
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthModal;
