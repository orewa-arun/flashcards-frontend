/**
 * Privacy Policy page for exammate.ai
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
          <Link to="/" className="back-link">← Back to Home</Link>
          <h1>Privacy Policy</h1>
          <p className="last-updated">Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </header>

        <main className="privacy-main">
          <section className="privacy-section">
            <h2>1. Introduction</h2>
            <p>
              Exammate.ai ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered exam preparation platform (the "Service").
            </p>
            <p>
              By using our Service, you agree to the collection and use of information in accordance with this policy. If you do not agree with our policies and practices, please do not use our Service.
            </p>
          </section>

          <section className="privacy-section">
            <h2>2. Information We Collect</h2>
            
            <h3>2.1 Information You Provide</h3>
            <p>When you create an account or use our Service, we may collect:</p>
            <ul>
              <li>Account information (email address, username)</li>
              <li>Study preferences and settings</li>
              <li>Course selections and enrollment data</li>
              <li>Communications with our support team</li>
            </ul>

            <h3>2.2 Automatically Collected Information</h3>
            <p>Our Service automatically collects certain information when you use it:</p>
            <ul>
              <li><strong>Study Progress:</strong> Flashcard completion, quiz attempts, and performance metrics</li>
              <li><strong>Usage Data:</strong> Time spent studying, features accessed, and interaction patterns</li>
              <li><strong>Device Information:</strong> Browser type, device type, operating system, and screen resolution</li>
              <li><strong>Performance Data:</strong> Quiz scores, response times, and learning analytics</li>
              <li><strong>AI Interaction Data:</strong> Questions answered, concepts reviewed, and adaptive learning patterns</li>
            </ul>

            <h3>2.3 Information We Do Not Collect</h3>
            <p>We do not collect:</p>
            <ul>
              <li>Your precise location or GPS data</li>
              <li>Browsing history outside our platform</li>
              <li>Personal information beyond what you provide</li>
              <li>Payment information (handled by third-party processors)</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>3. How We Use Your Information</h2>
            <p>We use the collected information for the following purposes:</p>
            <ul>
              <li><strong>Service Delivery:</strong> To provide, maintain, and improve our AI-powered learning platform</li>
              <li><strong>Personalization:</strong> To adapt content, difficulty levels, and study recommendations using AI algorithms</li>
              <li><strong>Progress Tracking:</strong> To track your exam readiness score and learning progress</li>
              <li><strong>AI Enhancement:</strong> To train and improve our machine learning models for better recommendations</li>
              <li><strong>Analytics:</strong> To analyze usage patterns and optimize the learning experience</li>
              <li><strong>Communication:</strong> To send you updates, support responses, and important service notifications</li>
              <li><strong>Legal Compliance:</strong> To comply with legal obligations and protect our rights</li>
            </ul>
          </section>

          <section className="privacy-section">
            <h2>4. AI and Machine Learning</h2>
            <p>
              Our Service uses artificial intelligence and machine learning to personalize your learning experience. This includes:
            </p>
            <ul>
              <li>Analyzing your quiz responses to identify knowledge gaps</li>
              <li>Generating personalized flashcard recommendations</li>
              <li>Adapting question difficulty based on your performance</li>
              <li>Predicting exam readiness scores using predictive analytics</li>
              <li>Optimizing study sequences for maximum efficiency</li>
            </ul>
            <p>
              Your data is used to train and improve our AI models, but all data is anonymized and aggregated before being used for model training. Individual user data is never shared with third parties for AI training purposes.
            </p>
          </section>

          <section className="privacy-section">
            <h2>5. Data Sharing and Disclosure</h2>
            <p>We do not sell your personal information. We may share your information only in the following circumstances:</p>
            <ul>
              <li><strong>Service Providers:</strong> With trusted third-party service providers who assist in operating our platform (e.g., cloud hosting, analytics)</li>
              <li><strong>Legal Requirements:</strong> When required by law, court order, or government regulation</li>
              <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets (with notice to users)</li>
              <li><strong>Protection of Rights:</strong> To protect our rights, privacy, safety, or property, or that of our users</li>
            </ul>
            <p>
              All service providers are contractually obligated to protect your information and use it only for specified purposes.
            </p>
          </section>

          <section className="privacy-section">
            <h2>6. Data Security</h2>
            <p>We implement industry-standard security measures to protect your information:</p>
            <ul>
              <li><strong>Encryption:</strong> All data transmission uses HTTPS/TLS encryption</li>
              <li><strong>Secure Storage:</strong> Data is stored in secure databases with access controls</li>
              <li><strong>Access Controls:</strong> Limited access to personal data on a need-to-know basis</li>
              <li><strong>Regular Audits:</strong> Security assessments and vulnerability testing</li>
              <li><strong>Data Backup:</strong> Regular backups with secure storage</li>
            </ul>
            <p>
              However, no method of transmission over the Internet or electronic storage is 100% secure. While we strive to protect your data, we cannot guarantee absolute security.
            </p>
          </section>

          <section className="privacy-section">
            <h2>7. Cookies and Tracking Technologies</h2>
            <p>We use cookies and similar tracking technologies to:</p>
            <ul>
              <li>Maintain your session and authentication state</li>
              <li>Remember your preferences and settings</li>
              <li>Analyze usage patterns and improve our Service</li>
              <li>Provide personalized content and recommendations</li>
            </ul>
            <p>
              You can control cookies through your browser settings. However, disabling cookies may limit your ability to use certain features of our Service.
            </p>
          </section>

          <section className="privacy-section">
            <h2>8. Data Retention</h2>
            <p>We retain your information for as long as necessary to:</p>
            <ul>
              <li>Provide our Service to you</li>
              <li>Comply with legal obligations</li>
              <li>Resolve disputes and enforce agreements</li>
              <li>Maintain security and prevent fraud</li>
            </ul>
            <p>
              When you delete your account, we will delete or anonymize your personal information within 30 days, except where we are required to retain it for legal purposes.
            </p>
          </section>

          <section className="privacy-section">
            <h2>9. Your Rights and Choices</h2>
            <p>Depending on your location, you may have the following rights:</p>
            <ul>
              <li><strong>Access:</strong> Request access to your personal information</li>
              <li><strong>Correction:</strong> Request correction of inaccurate data</li>
              <li><strong>Deletion:</strong> Request deletion of your personal information</li>
              <li><strong>Portability:</strong> Request transfer of your data to another service</li>
              <li><strong>Opt-Out:</strong> Opt out of certain data collection and processing</li>
              <li><strong>Objection:</strong> Object to processing of your personal information</li>
            </ul>
            <div className="rights-list">
              <div className="right-item">
                <h4>Opt Out of Analytics</h4>
                <p>You can opt out of analytics tracking at any time:</p>
                <button className="opt-out-btn" onClick={handleOptOut}>
                  Opt Out & Clear My Data
                </button>
              </div>
            </div>
            <p>
              To exercise these rights, please contact us using the information provided in the Contact section below.
            </p>
          </section>

          <section className="privacy-section">
            <h2>10. Children's Privacy</h2>
            <p>
              Our Service is not intended for children under the age of 13. We do not knowingly collect personal information from children under 13. If you believe we have collected information from a child under 13, please contact us immediately so we can delete it.
            </p>
          </section>

          <section className="privacy-section">
            <h2>11. International Data Transfers</h2>
            <p>
              Your information may be transferred to and processed in countries other than your country of residence. These countries may have data protection laws that differ from those in your country. We ensure appropriate safeguards are in place to protect your information in accordance with this Privacy Policy.
            </p>
          </section>

          <section className="privacy-section">
            <h2>12. Changes to This Privacy Policy</h2>
            <p>
              We may update this Privacy Policy from time to time. We will notify you of any material changes by posting the new Privacy Policy on this page and updating the "Last updated" date. We encourage you to review this Privacy Policy periodically.
            </p>
            <p>
              Your continued use of our Service after changes become effective constitutes acceptance of the updated Privacy Policy.
            </p>
          </section>

          <section className="privacy-section">
            <h2>13. Contact Us</h2>
            <p>
              If you have questions, concerns, or requests regarding this Privacy Policy or our data practices, please contact us:
            </p>
            <div className="contact-info">
              <p><strong>Email:</strong> <a href="mailto:arunworkacc0@gmail.com">arunworkacc0@gmail.com</a></p>
              <p><strong>Subject Line:</strong> Privacy Policy Inquiry</p>
            </div>
            <p>
              We will respond to your inquiry within 30 days.
            </p>
          </section>

          <section className="privacy-section">
            <h2>14. Governing Law</h2>
            <p>
              This Privacy Policy is governed by and construed in accordance with applicable data protection laws, including GDPR (for EU users) and CCPA (for California users), where applicable.
            </p>
          </section>
        </main>

        <footer className="privacy-footer">
          <Link to="/" className="back-to-app">← Return to Home</Link>
          <p>Thank you for using exammate.ai</p>
        </footer>
      </div>
    </div>
  );
}

export default PrivacyPolicyView;
