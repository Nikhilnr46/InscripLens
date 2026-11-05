import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ChevronRight,
  Upload,
  Sliders,
  Search,
  Sparkles,
  CheckCircle,
  XCircle,
  HelpCircle,
  FileText,
  ChevronDown,
  User,
  Compass,
  ArrowRight
} from 'lucide-react';
import { SITE } from '../config/site';
import ThemeToggle from '../components/ThemeToggle';
import Footer from '../components/Footer';

interface AboutPageProps {
  onNavigateHome: () => void;
  onNavigateStudio: () => void;
}

const SECTIONS = [
  { id: 'what-is-inscriplens', label: 'What is InscripLens' },
  { id: 'why-it-exists', label: 'Why it exists' },
  { id: 'how-it-works', label: 'How it works' },
  { id: 'privacy', label: 'Privacy' },
  { id: 'capabilities', label: 'Can & cannot do' },
  { id: 'faq', label: 'FAQ' },
  { id: 'credits', label: 'Credits & licences' },
  { id: 'developer', label: 'Developer' }
];

const FAQ_ITEMS = [
  {
    q: 'Are my images uploaded anywhere?',
    a: 'No. Processing happens on this computer. All neural inference, character detection, and reviews operate strictly inside your local worker without cloud connections.'
  },
  {
    q: 'Why do some regions look like noise?',
    a: 'Candidates are detected automatically and may split a letter, merge several, or pick up marks in the stone. Natural fissures, granite grain, and chisel marks can occasionally generate false candidate boxes.'
  },
  {
    q: 'Why are some predictions missing or wrong?',
    a: 'Recognition is experimental and trained on limited data; treat it as a starting suggestion. It is designed to assist epigraphists with transcription hints rather than replace expert human reading.'
  },
  {
    q: 'Which images work best?',
    a: 'Clear, evenly lit photographs of a single face of the stone, PNG or JPG. Oblique raking lighting that casts subtle shadows across chiseled strokes produces the cleanest foreground masks.'
  },
  {
    q: 'Can I export results?',
    a: 'Use the download options available in the Studio. Review records and localized candidate boxes can be exported as structured JSON datasets.'
  }
];

export default function AboutPage({ onNavigateHome, onNavigateStudio }: AboutPageProps) {
  const [activeSection, setActiveSection] = useState('what-is-inscriplens');
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  // Scroll spy via IntersectionObserver
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0.1 }
    );

    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveSection(id);
    }
  };

  const toggleFaq = (idx: number) => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  return (
    <div className="about-page-root">
      {/* Background ambient lighting & grid overlay */}
      <div className="landing-grid-bg" />
      <div className="landing-glow-violet" />
      <div className="landing-glow-blue" />
      <div className="landing-glow-sandstone" />

      {/* Top Header */}
      <header className="landing-header">
        <div className="landing-container landing-header-inner">
          <div
            className="landing-brand brand-logo-shimmer"
            onClick={onNavigateHome}
            role="button"
            tabIndex={0}
            title="Return to Home"
          >
            <span className="brand-title">InscripLens</span>
            <span className="brand-tag">Studio</span>
          </div>

          <nav className="nav-track" aria-label="Main Navigation">
            <button type="button" className="nav-item btn-ghost" onClick={onNavigateHome}>Home</button>
            <span className="nav-item active">About</span>
            <button type="button" className="nav-item btn-ghost" onClick={onNavigateStudio}>Studio</button>
          </nav>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <ThemeToggle />
            <button
              className="btn-primary btn-magnetic"
              onClick={onNavigateStudio}
              style={{ padding: '6px 16px', fontSize: '0.85rem' }}
            >
              Enter Studio <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Banner */}
      <div className="about-hero-section">
        <div className="landing-container">
          <div className="landing-badge hero-fade-1">
            <Compass size={13} className="text-sandstone" />
            <span>Research Documentation & System Reference</span>
          </div>
          <h1 className="about-headline hero-fade-2">
            About <span className="headline-gradient">{SITE.name}</span>
          </h1>
          <p className="about-subheadline hero-fade-3">
            An offline computational workspace for weathering recovery and diagnostic character study in historical Kannada epigraphy.
          </p>
        </div>
      </div>

      {/* Main Two-Column Layout: Left Sticky Index + Right Content */}
      <div className="landing-container about-content-container">
        {/* Left Sticky Section Index */}
        <aside className="about-sidebar">
          <div className="about-index-box card-spotlight">
            <div className="about-index-title">CONTENTS</div>
            <nav className="about-index-nav">
              {SECTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  className={`about-index-link ${activeSection === id ? 'active' : ''}`}
                  onClick={() => scrollToSection(id)}
                >
                  <span className="about-index-indicator" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Right Content Sections */}
        <main className="about-main-content">
          {/* A. What is InscripLens */}
          <section id="what-is-inscriplens" className="about-section card-spotlight">
            <span className="section-eyebrow">OVERVIEW</span>
            <h2 className="about-section-heading">What is InscripLens</h2>
            <p className="about-body-text">
              InscripLens is a local research workspace for studying photographs of historical Kannada stone inscriptions. It enhances weathered carvings, separates the carved strokes from the stone, and marks candidate characters so a reader can examine them one at a time.
            </p>
          </section>

          {/* B. Why it exists */}
          <section id="why-it-exists" className="about-section card-spotlight">
            <span className="section-eyebrow">HISTORICAL CONTEXT</span>
            <h2 className="about-section-heading">Why it exists</h2>
            <p className="about-body-text">
              Many inscriptions, including hero stones (Veeragallu) found across Karnataka, have been worn down by centuries of weathering. In photographs the carved strokes often blend into the rough surface, which makes careful study slow. InscripLens aims to make the carving easier to see and to organise what is found.
            </p>
          </section>

          {/* C. How it works (Five Steps) */}
          <section id="how-it-works" className="about-section card-spotlight">
            <span className="section-eyebrow">PIPELINE</span>
            <h2 className="about-section-heading">How it works</h2>
            <div className="workflow-steps-list">
              <div className="workflow-step-card card-spotlight">
                <div className="workflow-step-num">01</div>
                <div className="workflow-step-body">
                  <h3 className="workflow-step-title">Upload a photograph, or use the demonstration stone.</h3>
                  <p className="workflow-step-desc">
                    Field images of historical hero stones and inscribed slabs can be loaded directly from your device.
                  </p>
                </div>
              </div>

              <div className="workflow-step-card card-spotlight">
                <div className="workflow-step-num">02</div>
                <div className="workflow-step-body">
                  <h3 className="workflow-step-title">Enhance</h3>
                  <p className="workflow-step-desc">
                    A neural segmentation model predicts which pixels belong to carved strokes and produces a clean foreground mask.
                  </p>
                </div>
              </div>

              <div className="workflow-step-card card-spotlight">
                <div className="workflow-step-num">03</div>
                <div className="workflow-step-body">
                  <h3 className="workflow-step-title">Locate</h3>
                  <p className="workflow-step-desc">
                    A connected-component detector finds candidate character regions across the enhanced stroke mask.
                  </p>
                </div>
              </div>

              <div className="workflow-step-card card-spotlight">
                <div className="workflow-step-num">04</div>
                <div className="workflow-step-body">
                  <h3 className="workflow-step-title">Recognise (experimental)</h3>
                  <p className="workflow-step-desc">
                    A classifier suggests a label for each region, with alternatives and confidence estimations where available.
                  </p>
                </div>
              </div>

              <div className="workflow-step-card card-spotlight">
                <div className="workflow-step-num">05</div>
                <div className="workflow-step-body">
                  <h3 className="workflow-step-title">Review</h3>
                  <p className="workflow-step-desc">
                    A reader can record a correction with their initials or name, storing verifiable provenance records locally.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* D. Privacy */}
          <section id="privacy" className="about-section card-spotlight about-privacy-section">
            <div className="privacy-badge-banner">
              <ShieldCheck size={20} className="text-green" />
              <span>100% Offline Processing</span>
            </div>
            <h2 className="about-section-heading">Privacy</h2>
            <p className="about-body-text" style={{ fontSize: '1.05rem', fontWeight: '500' }}>
              Your images never leave this computer. All analysis runs on a local worker, and no cloud OCR service is used.
            </p>
          </section>

          {/* E. What it can and cannot do */}
          <section id="capabilities" className="about-section card-spotlight">
            <span className="section-eyebrow">RESEARCH SCOPE</span>
            <h2 className="about-section-heading">What it can and cannot do</h2>

            <div className="capabilities-grid">
              {/* Can */}
              <div className="capabilities-card capabilities-can">
                <div className="capabilities-card-header">
                  <CheckCircle size={18} className="text-green" />
                  <h3>Can</h3>
                </div>
                <ul className="capabilities-list">
                  <li>Enhance weathered inscription photographs</li>
                  <li>Produce a foreground mask</li>
                  <li>Find candidate character regions</li>
                  <li>Suggest experimental labels with alternatives</li>
                  <li>Keep a local record of reviewer corrections</li>
                </ul>
              </div>

              {/* Cannot Yet */}
              <div className="capabilities-card capabilities-cannot">
                <div className="capabilities-card-header">
                  <XCircle size={18} className="text-sandstone" />
                  <h3>Cannot yet</h3>
                </div>
                <ul className="capabilities-list">
                  <li>Guarantee correct readings</li>
                  <li>Treat candidate regions as complete characters</li>
                  <li>Provide a verified reading order</li>
                  <li>Translate in the Studio interface (the API only offers a rule-based draft for reviewer-verified formulaic hero-stone text; not wired into the UI)</li>

                  <li>Guarantee unreviewed machine translation accuracy</li>
                </ul>
              </div>
            </div>

            <div className="capabilities-closing-notice">
              <p>
                Suggestions are aids for study, not authoritative readings. Please verify with a qualified epigraphist.
              </p>
            </div>
          </section>

          {/* F. FAQ Accordion */}
          <section id="faq" className="about-section card-spotlight">
            <span className="section-eyebrow">QUESTIONS & ANSWERS</span>
            <h2 className="about-section-heading">Frequently Asked Questions</h2>
            <div className="faq-accordion-group">
              {FAQ_ITEMS.map((item, idx) => (
                <div
                  key={idx}
                  className={`faq-item card-spotlight ${openFaq === idx ? 'open' : ''}`}
                >
                  <button
                    type="button"
                    className="faq-question-btn"
                    onClick={() => toggleFaq(idx)}
                    aria-expanded={openFaq === idx}
                  >
                    <span>{item.q}</span>
                    <ChevronDown size={16} className={`faq-chevron ${openFaq === idx ? 'rotated' : ''}`} />
                  </button>
                  {openFaq === idx && (
                    <div className="faq-answer-pane">
                      <p>{item.a}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* G. Credits and Licences */}
          <section id="credits" className="about-section card-spotlight">
            <span className="section-eyebrow">ATTRIBUTION</span>
            <h2 className="about-section-heading">Credits and licences</h2>
            <p className="about-body-text">
              Enhancement approach and code: Shilalekhya, IIIT Hyderabad (MIT licence). Public EpiSAM images and checkpoints: CC BY-SA 4.0; imagery acknowledged to The Mythic Society, Bengaluru. Dataset previews shown in the application are derived works.
            </p>
            <div className="about-source-links">
              <a
                href="https://github.com/epigraph-shilalekhya"
                target="_blank"
                rel="noreferrer"
                className="inline-link"
              >
                Shilalekhya Code Repository (MIT) &rarr;
              </a>
              <a
                href="https://mythicsociety.org"
                target="_blank"
                rel="noreferrer"
                className="inline-link"
              >
                The Mythic Society Bengaluru (EpiSAM Images) &rarr;
              </a>
            </div>
          </section>

          {/* H. Developer */}
          <section id="developer" className="about-section card-spotlight">
            <span className="section-eyebrow">PROJECT AUTHORSHIP</span>
            <h2 className="about-section-heading">Developer</h2>
            <div className="developer-card card-spotlight">
              <div className="developer-avatar-box">
                <User size={24} className="text-sandstone" />
              </div>
              <div>
                <h3 className="developer-title">
                  Designed and developed by {SITE.developer}, {SITE.college}.
                </h3>
                <p className="developer-subtitle">
                  Academic research and local epigraphic engineering project &middot; {SITE.year}
                </p>
              </div>
            </div>
          </section>
        </main>
      </div>

      {/* Unified Footer */}
      <Footer
        onNavigateHome={onNavigateHome}
        onNavigateStudio={onNavigateStudio}
        onNavigateAbout={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        onNavigateCredits={() => scrollToSection('credits')}
      />
    </div>
  );
}

