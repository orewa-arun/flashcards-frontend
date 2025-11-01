import React from 'react';
import LandingHero from '../components/LandingHero';
import LandingValueProps from '../components/LandingValueProps';
import LandingSocialProof from '../components/LandingSocialProof';
import LandingHowItWorks from '../components/LandingHowItWorks';
import LandingDemo from '../components/LandingDemo';
import LandingCTA from '../components/LandingCTA';
import LandingFooter from '../components/LandingFooter';
import LandingFAQ from '../components/LandingFAQ';
import './LandingPageView.css';

function LandingPageView() {
  return (
    <div className="landing-page-view">
      <LandingHero />
      <LandingValueProps />
      <LandingSocialProof />
      <LandingHowItWorks />
      <LandingDemo />
      <LandingFAQ />
      <LandingCTA />
      <LandingFooter />
    </div>
  );
}

export default LandingPageView;
