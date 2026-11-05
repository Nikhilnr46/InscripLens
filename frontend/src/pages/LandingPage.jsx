import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  ShieldCheck,
  ChevronRight,
  Layers,
  Search,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowUp,
  Menu,
  X
} from 'lucide-react';
import SlideToEnter from '../components/SlideToEnter.jsx';
import Marquee from '../components/Marquee.jsx';
import TabletIllustration from '../components/TabletIllustration.tsx';
import ThemeToggle from '../components/ThemeToggle.tsx';
import AboutSection from '../components/AboutSection.tsx';
import Footer from '../components/Footer.tsx';
import Reveal from '../components/Reveal';
import { refreshReveals } from '../utils/revealObserver';

const NAV_LINKS = [
  { id: 'overview', label: 'Overview', href: '/#overview' },
  { id: 'workflow', label: 'Workflow', href: '/#workflow' },
  { id: 'about', label: 'About', href: '/#about' },
  { id: 'limitations', label: 'Limitations', href: '/#limitations' }
];

export default function LandingPage({ onEnterStudio, onTryDemo }) {
  const [activeSection, setActiveSection] = useState('overview');
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0, opacity: 0 });

  const navTrackRef = useRef(null);
  const linkRefs = useRef({});
  const headlineRef = useRef(null);

  const isReducedMotion = () => {
    return typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  };

  // Scroll to section helper
  const scrollToSection = (id) => {
    const reduced = isReducedMotion();
    if (id === 'overview') {
      window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
      window.history.replaceState(null, '', window.location.pathname);
      setActiveSection('overview');
      setTimeout(() => refreshReveals(), 250);
      return;
    }

    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
      window.history.replaceState(null, '', `/#${id}`);
      setActiveSection(id);
      setTimeout(() => refreshReveals(), 250);
    }
  };

  const handleNavClick = (e, id) => {
    if (e) e.preventDefault();
    scrollToSection(id);
  };

  const scrollToTop = () => {
    const reduced = isReducedMotion();
    window.scrollTo({ top: 0, behavior: reduced ? 'auto' : 'smooth' });
    window.history.replaceState(null, '', window.location.pathname);
    setActiveSection('overview');
  };

  // Interactive Headline Spotlight (Step C2)
  useEffect(() => {
    const el = headlineRef.current;
    if (!el) return;

    // Disabled on touch devices and when prefers-reduced-motion is set
    const mediaFine = window.matchMedia('(hover: hover) and (pointer: fine)');
    const mediaMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    if (!mediaFine.matches || mediaMotion.matches) {
      return;
    }

    let rafMoveId = null;
    let rafFadeId = null;
    let latestEvent = null;
    const FADE_DURATION = 300;

    const onPointerMove = (e) => {
      latestEvent = e;
      if (rafMoveId === null) {
        rafMoveId = requestAnimationFrame(() => {
          rafMoveId = null;
          if (!latestEvent || !el) return;
          const rect = el.getBoundingClientRect();
          const x = latestEvent.clientX - rect.left;
          const y = latestEvent.clientY - rect.top;
          const normX = Math.max(0, Math.min(1, x / rect.width));
          // Hue shift between about -20deg and 20deg
          const hue = Math.round((normX - 0.5) * 40);

          el.style.setProperty('--mx', `${x.toFixed(1)}px`);
          el.style.setProperty('--my', `${y.toFixed(1)}px`);
          el.style.setProperty('--hue', `${hue}deg`);
        });
      }
    };

    const onPointerEnter = (e) => {
      if (rafFadeId !== null) {
        cancelAnimationFrame(rafFadeId);
        rafFadeId = null;
      }
      el.style.setProperty('--spotlight-opacity', '1');
      el.addEventListener('pointermove', onPointerMove, { passive: true });
      onPointerMove(e);
    };

    const onPointerLeave = () => {
      el.removeEventListener('pointermove', onPointerMove);
      if (rafMoveId !== null) {
        cancelAnimationFrame(rafMoveId);
        rafMoveId = null;
      }
      latestEvent = null;

      // Smoothly ease spotlight out over 300ms so text settles back to resting gradient
      const startVal = parseFloat(el.style.getPropertyValue('--spotlight-opacity')) || 1;
      const startTime = performance.now();

      const fadeStep = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / FADE_DURATION);
        // ease-out cubic curve
        const ease = 1 - Math.pow(1 - progress, 3);
        const currentOpacity = startVal * (1 - ease);

        el.style.setProperty('--spotlight-opacity', currentOpacity.toFixed(3));

        if (progress < 1) {
          rafFadeId = requestAnimationFrame(fadeStep);
        } else {
          el.style.setProperty('--spotlight-opacity', '0');
          rafFadeId = null;
        }
      };

      rafFadeId = requestAnimationFrame(fadeStep);
    };

    el.addEventListener('pointerenter', onPointerEnter);
    el.addEventListener('pointerleave', onPointerLeave);

    return () => {
      el.removeEventListener('pointerenter', onPointerEnter);
      el.removeEventListener('pointerleave', onPointerLeave);
      el.removeEventListener('pointermove', onPointerMove);
      if (rafMoveId !== null) cancelAnimationFrame(rafMoveId);
      if (rafFadeId !== null) cancelAnimationFrame(rafFadeId);
    };
  }, []);

  // Update sliding underline indicator position
  useEffect(() => {
    const updateIndicator = () => {
      const activeEl = linkRefs.current[activeSection];
      const track = navTrackRef.current;
      if (activeEl && track) {
        const trackRect = track.getBoundingClientRect();
        const elRect = activeEl.getBoundingClientRect();
        setIndicatorStyle({
          left: elRect.left - trackRect.left,
          width: elRect.width,
          opacity: 1
        });
      }
    };

    updateIndicator();
    window.addEventListener('resize', updateIndicator);
    return () => window.removeEventListener('resize', updateIndicator);
  }, [activeSection]);

  // Initial layout hash scroll
  useEffect(() => {
    const rawHash = window.location.hash.replace(/^#/, '');
    if (rawHash) {
      const timer = setTimeout(() => {
        if (rawHash === 'overview') {
          scrollToTop();
        } else {
          const el = document.getElementById(rawHash);
          if (el) {
            const reduced = isReducedMotion();
            el.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
            setActiveSection(rawHash);
          }
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, []);

  // Scroll-Spy & Back to Top display
  useEffect(() => {
    const sectionIds = ['overview', 'workflow', 'about', 'limitations'];

    const updateActiveSection = () => {
      const scrollY = window.scrollY;
      setShowBackToTop(scrollY > 400);

      // Top of page
      if (scrollY < 120) {
        setActiveSection('overview');
        if (window.location.hash) {
          window.history.replaceState(null, '', window.location.pathname);
        }
        return;
      }

      // Bottom of page
      if (window.innerHeight + scrollY >= document.documentElement.scrollHeight - 60) {
        setActiveSection('limitations');
        if (window.location.hash !== '#limitations') {
          window.history.replaceState(null, '', '#limitations');
        }
        return;
      }

      // Determine active section based on reading line below sticky header
      const readingLine = 120;
      let current = 'overview';

      for (const id of sectionIds) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= readingLine) {
            current = id;
          }
        }
      }

      setActiveSection(current);
      const newHash = current === 'overview' ? '' : `#${current}`;
      if (window.location.hash !== newHash) {
        window.history.replaceState(null, '', newHash || window.location.pathname);
      }
    };

    window.addEventListener('scroll', updateActiveSection, { passive: true });
    updateActiveSection();

    return () => {
      window.removeEventListener('scroll', updateActiveSection);
    };
  }, []);

  return (
    <div className="landing-page-root">
      {/* Background ambient lighting & grid overlay */}
      <div className="landing-grid-bg" />
      <div className="landing-glow-violet" />
      <div className="landing-glow-blue" />
      <div className="landing-glow-sandstone" />

      {/* Top Sticky Navigation Bar */}
      <header className="landing-header">
        <div className="landing-container landing-header-inner">
          <a
            href="/#overview"
            className="landing-brand brand-logo-shimmer"
            onClick={(e) => {
              e.preventDefault();
              scrollToTop();
            }}
            title="InscripLens Studio Home"
          >
            <span className="brand-title">InscripLens</span>
            <span className="brand-tag">Studio</span>
          </a>

          {/* Desktop Nav Track with Sliding Underline */}
          <nav className="nav-track nav-track-desktop" ref={navTrackRef} aria-label="Main Sections">
            {NAV_LINKS.map(({ id, label, href }) => (
              <a
                key={id}
                ref={(el) => (linkRefs.current[id] = el)}
                href={href}
                className={`nav-item ${activeSection === id ? 'active' : ''}`}
                onClick={(e) => handleNavClick(e, id)}
              >
                {label}
              </a>
            ))}
            <span
              className="nav-sliding-indicator"
              style={{
                transform: `translateX(${indicatorStyle.left}px)`,
                width: `${indicatorStyle.width}px`,
                opacity: indicatorStyle.opacity
              }}
            />
          </nav>

          {/* Header Right Actions - Theme Toggle & Mobile Toggle Only */}
          <div className="landing-header-actions">
            <ThemeToggle />
            <button
              type="button"
              className="mobile-drawer-toggle"
              onClick={() => setMobileDrawerOpen((prev) => !prev)}
              aria-label={mobileDrawerOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileDrawerOpen}
            >
              {mobileDrawerOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      <div className={`mobile-drawer ${mobileDrawerOpen ? 'open' : ''}`} aria-hidden={!mobileDrawerOpen}>
        <nav className="mobile-drawer-nav" aria-label="Mobile Navigation">
          {NAV_LINKS.map(({ id, label, href }) => (
            <a
              key={id}
              href={href}
              className={`mobile-drawer-link ${activeSection === id ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                setMobileDrawerOpen(false);
                setTimeout(() => scrollToSection(id), 120);
              }}
            >
              <span>{label}</span>
              {activeSection === id && <span className="mobile-drawer-dot" />}
            </a>
          ))}
        </nav>
      </div>

      {/* =========================================================================
          SECTION 1: #overview (Hero Section)
          ========================================================================= */}
      <section className="landing-hero-section" id="overview">
        <div className="landing-container landing-hero-grid">
          {/* Left Column: Headline, Description, Privacy & SlideToEnter */}
          <div className="landing-hero-copy">
            <Reveal initialShown variant="up" delay={0}>
              <div className="landing-badge">
                <Sparkles size={13} className="text-sandstone" />
                <span>Historical Kannada Epigraphy Workspace</span>
              </div>
            </Reveal>

            <Reveal initialShown variant="up" delay={60}>
              <h1 className="landing-headline" ref={headlineRef}>
                Read the stone <span className="headline-gradient">before it fades</span>
              </h1>
            </Reveal>

            <Reveal initialShown variant="up" delay={120}>
              <p className="landing-description">
                Neural binarization and diagnostic character localization for weathered stone inscriptions.
                Recover ancient Halegannada glyphs from granite erosion with verifiable epigraphic review.
              </p>
            </Reveal>

            <Reveal initialShown variant="up" delay={180}>
              <div className="landing-privacy-badge">
                <ShieldCheck size={16} className="text-green" />
                <span>Your images never leave this computer.</span>
              </div>
            </Reveal>

            <Reveal initialShown variant="up" delay={240}>
              <div className="landing-cta-area">
                <SlideToEnter onComplete={onEnterStudio} />
              </div>
            </Reveal>
          </div>

          {/* Right Column: Interactive Stone Tablet Illustration */}
          <Reveal initialShown variant="scale" delay={120} className="landing-hero-visual">
            <TabletIllustration />
          </Reveal>
        </div>

        {/* Full-Width Signal Marquee inside Overview */}
        <Reveal variant="up" delay={0} className="landing-marquee-section">
          <Marquee />
        </Reveal>
      </section>

      {/* =========================================================================
          SECTION 2: #workflow (How It Works)
          ========================================================================= */}
      <section className="landing-how-section" id="workflow">
        <div className="landing-container">
          <div className="section-header">
            <Reveal variant="up" delay={0}>
              <span className="section-eyebrow">WORKFLOW</span>
            </Reveal>
            <Reveal variant="up" delay={60}>
              <h2 className="section-title">How It Works</h2>
            </Reveal>
            <Reveal variant="up" delay={120}>
              <p className="section-subtitle">
                From raw field photograph to verified transliteration record in three local stages.
              </p>
            </Reveal>
          </div>

          {/* 3 Glass Cards with Spotlight and 3D Tilt (60ms stagger) */}
          <div className="how-grid">
            <Reveal variant="up" delay={0}>
              <div className="glass-card card-spotlight card-tilt">
                <div className="glass-card-num">01</div>
                <div className="glass-card-icon">
                  <Layers size={22} className="text-sandstone" />
                </div>
                <h3 className="glass-card-title">Capture & Select</h3>
                <p className="glass-card-body">
                  Upload a field photograph of a stone inscription or start immediately with the curated Nagavara 8th-century hero stone benchmark.
                </p>
              </div>
            </Reveal>

            <Reveal variant="up" delay={60}>
              <div className="glass-card card-spotlight card-tilt">
                <div className="glass-card-num">02</div>
                <div className="glass-card-icon">
                  <Search size={22} className="text-violet" />
                </div>
                <h3 className="glass-card-title">Enhance & Localize</h3>
                <p className="glass-card-body">
                  The Shilalekhya neural U-Net separates chiseled incisions from weather-worn granite and identifies individual candidate character regions.
                </p>
              </div>
            </Reveal>

            <Reveal variant="up" delay={120}>
              <div className="glass-card card-spotlight card-tilt">
                <div className="glass-card-num">03</div>
                <div className="glass-card-icon">
                  <CheckCircle size={22} className="text-green" />
                </div>
                <h3 className="glass-card-title">Inspect & Verify</h3>
                <p className="glass-card-body">
                  Examine high-resolution crops, compare top transliteration label alternatives, and record verifiable expert review notes into local history.
                </p>
              </div>
            </Reveal>
          </div>

          {/* Try the Demo CTA (80ms button group stagger) */}
          <div className="try-demo-container">
            <Reveal variant="up" delay={180}>
              <button
                className="btn-primary try-demo-btn btn-magnetic"
                onClick={onTryDemo}
              >
                <Sparkles size={16} /> Try the Demo Stone (Nagavara) &rarr;
              </button>
            </Reveal>
            <Reveal variant="up" delay={260}>
              <span className="try-demo-hint">
                133 candidate regions ready for interactive curtain wipe and classification
              </span>
            </Reveal>
          </div>
        </div>
      </section>

      {/* =========================================================================
          SECTION 3: #about (About Copy, Pipeline, Privacy, FAQ, Credits)
          ========================================================================= */}
      <section className="landing-about-section" id="about">
        <AboutSection />
      </section>

      {/* =========================================================================
          SECTION 4: #limitations (Prototype Limitations & Scope)
          ========================================================================= */}
      <section className="landing-limitations-section" id="limitations">
        <div className="landing-container">
          <div className="section-header" style={{ textAlign: 'center', marginBottom: '32px' }}>
            <Reveal variant="up" delay={0}>
              <span className="section-eyebrow">RESEARCH SCOPE</span>
            </Reveal>
            <Reveal variant="up" delay={60}>
              <h2 className="section-title">Limitations</h2>
            </Reveal>
            <Reveal variant="up" delay={120}>
              <p className="section-subtitle">
                Computational boundaries and operational guidelines of this local diagnostic environment.
              </p>
            </Reveal>
          </div>

          <div className="limitations-content-wrapper" style={{ maxWidth: '820px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {/* Limitations of This Prototype Glass Card */}
            <Reveal variant="up" delay={0}>
              <div className="limitations-glass-card card-spotlight">
                <div className="limitations-header">
                  <AlertTriangle size={18} className="text-sandstone" />
                  <h4>Limitations of this prototype</h4>
                </div>
                <p className="limitations-text">
                  Research prototype: enhancement works; character recognition is experimental. Published/source labels are references, not automatic readings. Translation is not yet available in the Studio interface (the API only offers an experimental, rule-based draft for reviewer-verified formulaic hero-stone text). It is not a general Old Kannada translator, and all drafts require expert epigraphic verification.
                </p>
              </div>
            </Reveal>

            {/* What it can and cannot do (Two-Column Block) */}
            <div id="capabilities" className="about-section card-spotlight">
              <Reveal variant="up" delay={0}>
                <span className="section-eyebrow">RESEARCH SCOPE</span>
                <h3 className="about-section-heading">What it can and cannot do</h3>
              </Reveal>

              <div className="capabilities-grid">
                {/* Can */}
                <Reveal variant="up" delay={0} className="capabilities-card capabilities-can">
                  <div className="capabilities-card-header">
                    <CheckCircle size={18} className="text-green" />
                    <h4>Can</h4>
                  </div>
                  <ul className="capabilities-list">
                    <li>Enhance weathered inscription photographs</li>
                    <li>Produce a foreground mask</li>
                    <li>Find candidate character regions</li>
                    <li>Suggest experimental labels with alternatives</li>
                    <li>Keep a local record of reviewer corrections</li>
                  </ul>
                </Reveal>

                {/* Cannot Yet */}
                <Reveal variant="up" delay={60} className="capabilities-card capabilities-cannot">
                  <div className="capabilities-card-header">
                    <XCircle size={18} className="text-sandstone" />
                    <h4>Cannot yet</h4>
                  </div>
                  <ul className="capabilities-list">
                    <li>Guarantee correct readings</li>
                    <li>Treat candidate regions as complete characters</li>
                    <li>Provide a verified reading order</li>
                    <li>Translate in the Studio interface (the API only offers a rule-based draft for reviewer-verified formulaic hero-stone text; not wired into the UI)</li>
                    <li>Guarantee unreviewed machine translation accuracy</li>
                  </ul>
                </Reveal>
              </div>

              <Reveal variant="up" delay={120}>
                <div className="capabilities-closing-notice">
                  <p>
                    Suggestions are aids for study, not authoritative readings. Please verify with a qualified epigraphist.
                  </p>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      {/* Back-To-Top Button */}
      <button
        type="button"
        className={`back-to-top-btn ${showBackToTop ? 'visible' : ''}`}
        onClick={scrollToTop}
        aria-label="Back to top"
        title="Back to top"
      >
        <ArrowUp size={16} />
      </button>

      {/* Unified Site Footer */}
      <Footer onNavigateHome={scrollToTop} />
    </div>
  );
}
