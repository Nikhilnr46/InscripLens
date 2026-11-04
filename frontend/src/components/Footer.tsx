import React from 'react';
import { SITE } from '../config/site';

interface FooterProps {
  onNavigateHome?: () => void;
  onNavigateStudio?: () => void;
  onNavigateAbout?: () => void;
  onNavigateCredits?: () => void;
}

export default function Footer({ onNavigateHome }: FooterProps) {
  const handleHome = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onNavigateHome) onNavigateHome();
  };

  return (
    <footer className="site-footer">
      <div className="landing-container site-footer-inner">
        <div className="site-footer-brand">
          <a
            href="/#overview"
            className="landing-brand brand-logo-shimmer"
            onClick={handleHome}
            title="InscripLens Studio Home"
          >
            <span className="brand-title">InscripLens</span>
            <span className="brand-tag">Studio</span>
          </a>
          <p className="site-footer-tagline">
            Local research workspace for historical Kannada stone inscriptions.
          </p>
        </div>

        <div className="site-footer-meta">
          <div className="site-footer-credit">
            <span>Developed by {SITE.developer}</span>
            <span className="footer-credit-sep" aria-hidden="true">|</span>
            <span className="institution-pill">{SITE.collegeFull || SITE.college}</span>
          </div>
          <div className="site-footer-sub">
            Runs locally on this machine. No cloud OCR service used.
          </div>
        </div>
      </div>
    </footer>
  );
}
