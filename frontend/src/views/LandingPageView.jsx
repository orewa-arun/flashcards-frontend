import React, { useState } from 'react';
import LandingHero from '../components/LandingHero';
import LandingValueProps from '../components/LandingValueProps';
import LandingSocialProof from '../components/LandingSocialProof';
import LandingHowItWorks from '../components/LandingHowItWorks';
import LandingDemo from '../components/LandingDemo';
import LandingCTA from '../components/LandingCTA';
import LandingFooter from '../components/LandingFooter';
import LandingFAQ from '../components/LandingFAQ';
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
      <LandingValueProps />
      <LandingSocialProof />
      <LandingHowItWorks />
      <LandingDemo />
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
