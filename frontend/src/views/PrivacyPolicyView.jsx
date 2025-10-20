/**
 * Privacy Policy page for GDPR compliance and transparency
 */

import { Link } from 'react-router-dom';
import { clearTrackingData } from '../utils/userTracking';
import './PrivacyPolicyView.css';

function PrivacyPolicyView() {
  
  const handleOptOut = () => {
    if (confirm('Are you sure you want to opt out of analytics tracking? This will clear all your progress data.')) {
      clearTrackingData();
      alert('You have been opted out of analytics tracking. Your data has been cleared.');
      window.location.href = '/';
    }
  };

  return (
    <div className="privacy-policy-view">
      <div className="privacy-content">
        <header className="privacy-header">
          <Link to="/" className="back-link">← Back to Study Tool</Link>
          <h1>Privacy Policy</h1>
          <p className="last-updated">Last updated: {new Date().toLocaleDateString()}</p>
        </header>

        <main className="privacy-main">
          <section className="privacy-section">
            <h2>🎯 Our Commitment to Your Privacy</h2>
            <p>
              We are committed to protecting your privacy while helping you study more effectively. 
              This Privacy Policy explains how we collect, use, and protect your information when you use our study tool.
            </p>
          </section>

          <section className="privacy-section">
            <h2>📊 What Information We Collect</h2>
            <div className="info-list">
              <div className="info-item">
                <h3>Anonymous Study Analytics</h3>
                <ul>
                  <li><strong>Study Progress:</strong> Which cards you've studied and your progress through flashcard decks</li>
                  <li><strong>Quiz Performance:</strong> Your quiz scores, time taken, and question responses</li>
                  <li><strong>Usage Patterns:</strong> How often you study and which courses you focus on</li>
                  <li><strong>Anonymous Identifier:</strong> A randomly generated ID (not linked to your identity)</li>
                </ul>
              </div>
              
              <div className="info-item">
                <h3>What We DON'T Collect</h3>
                <ul>
                  <li>❌ Your name, email, or any personal information</li>
                  <li>❌ IP addresses or device fingerprints</li>
                  <li>❌ Location data</li>
                  <li>❌ Browsing history outside our app</li>
                  <li>❌ Any data that could identify you personally</li>
                </ul>
              </div>
            </div>
          </section>

          <section className="privacy-section">
            <h2>🔧 How We Use Your Information</h2>
            <ul>
              <li><strong>Improve Study Experience:</strong> Identify which topics are most challenging for students</li>
              <li><strong>Optimize Content:</strong> Understand which flashcards and quiz questions are most effective</li>
              <li><strong>Track Your Progress:</strong> Show you your personal study statistics and achievements</li>
              <li><strong>Educational Research:</strong> Analyze anonymous learning patterns to improve study methods</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>🍪 Cookies and Tracking</h2>
            <p>We use one essential cookie to provide our service:</p>
            <div className="cookie-info">
              <h4>study_user_id</h4>
              <ul>
                <li><strong>Purpose:</strong> Anonymous user identification for progress tracking</li>
                <li><strong>Duration:</strong> 1 year (renewable)</li>
                <li><strong>Type:</strong> Randomly generated UUID (impossible to trace back to you)</li>
              </ul>
            </div>
            <p>
              <strong>Note:</strong> If you clear your cookies or switch devices, your progress will be lost 
              since we have no way to link the data back to you.
            </p>
          </section>

          <section className="privacy-section">
            <h2>🛡️ Data Security & Storage</h2>
            <ul>
              <li><strong>Secure Database:</strong> Data is stored in MongoDB Atlas with enterprise-grade security</li>
              <li><strong>Encryption:</strong> All data transmission uses HTTPS encryption</li>
              <li><strong>Access Control:</strong> Only authorized systems can access the anonymous data</li>
              <li><strong>No Backups of Personal Data:</strong> Since we don't collect personal data, there's nothing sensitive to backup</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>⏱️ Data Retention</h2>
            <ul>
              <li><strong>Study Progress:</strong> Kept while you actively use the tool</li>
              <li><strong>Quiz Results:</strong> Aggregated for educational insights after 6 months</li>
              <li><strong>Inactive Users:</strong> Anonymous data may be cleaned up after 2 years of inactivity</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>✅ Your Rights & Choices</h2>
            <div className="rights-list">
              <div className="right-item">
                <h4>🚫 Opt Out Anytime</h4>
                <p>You can stop analytics tracking at any time by clicking the button below:</p>
                <button className="opt-out-btn" onClick={handleOptOut}>
                  🗑️ Opt Out & Clear My Data
                </button>
              </div>
              
              <div className="right-item">
                <h4>🔄 Change Your Mind</h4>
                <p>You can re-enable tracking by accepting cookies again on your next visit.</p>
              </div>
              
              <div className="right-item">
                <h4>🔍 Data Transparency</h4>
                <p>Since your data is anonymous, we cannot identify or retrieve your specific records.</p>
              </div>
            </div>
          </section>

          <section className="privacy-section">
            <h2>🌍 Legal Compliance</h2>
            <p>
              This tool complies with GDPR, CCPA, and other privacy regulations because:
            </p>
            <ul>
              <li>We collect only anonymous, non-personal data</li>
              <li>You have full control over data collection (opt-in/opt-out)</li>
              <li>We are transparent about our data practices</li>
              <li>Data is used solely to improve the educational experience</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>📧 Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="contact-info">
              <p><strong>Email:</strong> privacy@studytool.example.com</p>
              <p><strong>Subject Line:</strong> Privacy Policy Question</p>
            </div>
          </section>

          <section className="privacy-section">
            <h2>🔄 Policy Updates</h2>
            <p>
              We may update this Privacy Policy occasionally to reflect changes in our practices or legal requirements. 
              Any changes will be posted on this page with an updated "Last Updated" date.
            </p>
          </section>
        </main>

        <footer className="privacy-footer">
          <Link to="/" className="back-to-app">← Return to Study Tool</Link>
          <p>Thank you for trusting us with your learning journey! 🎓</p>
        </footer>
      </div>
    </div>
  );
}

export default PrivacyPolicyView;
