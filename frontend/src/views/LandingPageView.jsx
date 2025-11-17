import React, { useState } from 'react';
import LandingHero from '../components/LandingHero';
import LandingExamFocus from '../components/LandingExamFocus';
import LandingComparison from '../components/LandingComparison';
import LandingHowItWorks from '../components/LandingHowItWorks';
import LandingProductShowcase from '../components/LandingProductShowcase';
import LandingValueProps from '../components/LandingValueProps';
import LandingSocialProof from '../components/LandingSocialProof';
import LandingFAQ from '../components/LandingFAQ';
import LandingCTA from '../components/LandingCTA';
import LandingFooter from '../components/LandingFooter';
import AuthModal from '../components/Auth/AuthModal';
import './LandingPageView.css';

function LandingPageView() {
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('signup');

  const openAuthModal = (mode = 'signup') => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  return (
    <div className="landing-page-view">
      <LandingHero onOpenAuthModal={openAuthModal} />
      <LandingExamFocus />
      <LandingComparison />
      <LandingHowItWorks />
      <LandingProductShowcase />
      <LandingValueProps />
      <LandingSocialProof />
      <LandingFAQ />
      <LandingCTA onOpenAuthModal={openAuthModal} />
      <LandingFooter />
      
      <AuthModal 
        isOpen={isAuthModalOpen}
        onClose={closeAuthModal}
        initialMode={authModalMode}
      />
    </div>
  );
}

export default LandingPageView;
