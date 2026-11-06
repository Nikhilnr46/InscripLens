import React, { useState } from 'react';
import {
  ShieldCheck,
  ChevronDown,
  Compass
} from 'lucide-react';
import { SITE } from '../config/site';
import Reveal from './Reveal';
import pesLogo from '../assets/pes-logo.png';

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
  },
  {
    q: 'How do candidate coordinates relate to selected image regions?',
    a: 'Candidate coordinates, saved reviews and history refer to the selected area image, not the original photograph.'
  }
];

export default function AboutSection() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (idx: number) => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  return (
    <div className="about-section-wrapper">
      <div className="landing-container">
        <div className="section-header" style={{ textAlign: 'center', marginBottom: '40px' }}>
          <Reveal variant="up" delay={0}>
            <div className="landing-badge" style={{ margin: '0 auto 12px' }}>
              <Compass size={13} className="text-sandstone" />
              <span>Research Documentation & System Reference</span>
            </div>
          </Reveal>
          <Reveal variant="up" delay={60}>
            <h2 className="section-title">
              About <span className="headline-gradient">{SITE.name}</span>
            </h2>
          </Reveal>
          <Reveal variant="up" delay={120}>
            <p className="section-subtitle" style={{ maxWidth: '680px', margin: '0 auto' }}>
              An offline computational workspace for weathering recovery and diagnostic character study in historical Kannada epigraphy.
            </p>
          </Reveal>
        </div>

        {/* Single Centered Column Layout */}
        <div className="about-single-column">
          <main className="about-main-content">
            {/* A. What is InscripLens */}
            <Reveal variant="up" delay={0}>
              <div id="what-is-inscriplens" className="about-section card-spotlight">
                <span className="section-eyebrow">OVERVIEW</span>
                <h3 className="about-section-heading">What is InscripLens</h3>
                <p className="about-body-text">
                  InscripLens is a local research workspace for studying photographs of historical Kannada stone inscriptions. It enhances weathered carvings, separates the carved strokes from the stone, and marks candidate characters so a reader can examine them one at a time.
                </p>
              </div>
            </Reveal>

            {/* B. Why it exists */}
            <Reveal variant="up" delay={60}>
              <div id="why-it-exists" className="about-section card-spotlight">
                <span className="section-eyebrow">HISTORICAL CONTEXT</span>
                <h3 className="about-section-heading">Why it exists</h3>
                <p className="about-body-text">
                  Many inscriptions, including hero stones (Veeragallu) found across Karnataka, have been worn down by centuries of weathering. In photographs the carved strokes often blend into the rough surface, which makes careful study slow. InscripLens aims to make the carving easier to see and to organise what is found.
                </p>
              </div>
            </Reveal>

            {/* C. How it works (Five Steps with 60ms Stagger) */}
            <div id="pipeline" className="about-section card-spotlight">
              <Reveal variant="up" delay={0}>
                <span className="section-eyebrow">PIPELINE</span>
                <h3 className="about-section-heading">How it works</h3>
              </Reveal>
              <div className="workflow-steps-list">
                <Reveal variant="up" delay={0}>
                  <div className="workflow-step-card card-spotlight">
                    <div className="workflow-step-num">01</div>
                    <div className="workflow-step-body">
                      <h4 className="workflow-step-title">Upload a photograph, or use the demonstration stone.</h4>
                      <p className="workflow-step-desc">
                        Field images of historical hero stones and inscribed slabs can be loaded directly from your device.
                      </p>
                    </div>
                  </div>
                </Reveal>

                <Reveal variant="up" delay={60}>
                  <div className="workflow-step-card card-spotlight">
                    <div className="workflow-step-num">02</div>
                    <div className="workflow-step-body">
                      <h4 className="workflow-step-title">Enhance</h4>
                      <p className="workflow-step-desc">
                        A neural segmentation model predicts which pixels belong to carved strokes and produces a clean foreground mask.
                      </p>
                    </div>
                  </div>
                </Reveal>

                <Reveal variant="up" delay={120}>
                  <div className="workflow-step-card card-spotlight">
                    <div className="workflow-step-num">03</div>
                    <div className="workflow-step-body">
                      <h4 className="workflow-step-title">Locate</h4>
                      <p className="workflow-step-desc">
                        A connected-component detector finds candidate character regions across the enhanced stroke mask.
                      </p>
                    </div>
                  </div>
                </Reveal>

                <Reveal variant="up" delay={180}>
                  <div className="workflow-step-card card-spotlight">
                    <div className="workflow-step-num">04</div>
                    <div className="workflow-step-body">
                      <h4 className="workflow-step-title">Recognise (experimental)</h4>
                      <p className="workflow-step-desc">
                        A classifier suggests a label for each region, with alternatives and confidence estimations where available.
                      </p>
                    </div>
                  </div>
                </Reveal>

                <Reveal variant="up" delay={240}>
                  <div className="workflow-step-card card-spotlight">
                    <div className="workflow-step-num">05</div>
                    <div className="workflow-step-body">
                      <h4 className="workflow-step-title">Review</h4>
                      <p className="workflow-step-desc">
                        A reader can record a correction with their initials or name, storing verifiable provenance records locally.
                      </p>
                    </div>
                  </div>
                </Reveal>
              </div>
            </div>

            {/* D. Privacy */}
            <Reveal variant="up" delay={60}>
              <div id="privacy" className="about-section card-spotlight about-privacy-section">
                <div className="privacy-badge-banner">
                  <ShieldCheck size={20} className="text-green" />
                  <span>100% Offline Processing</span>
                </div>
                <h3 className="about-section-heading">Privacy</h3>
                <p className="about-body-text" style={{ fontSize: '1.05rem', fontWeight: '500' }}>
                  Your images never leave this computer. All analysis runs on a local worker, and no cloud OCR service is used.
                </p>
              </div>
            </Reveal>

            {/* E. FAQ Accordion (60ms Staggered Items) */}
            <div id="faq" className="about-section card-spotlight">
              <Reveal variant="up" delay={0}>
                <span className="section-eyebrow">QUESTIONS & ANSWERS</span>
                <h3 className="about-section-heading">Frequently Asked Questions</h3>
              </Reveal>
              <div className="faq-accordion-group">
                {FAQ_ITEMS.map((item, idx) => (
                  <Reveal key={idx} variant="up" delay={idx * 60}>
                    <div
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
                  </Reveal>
                ))}
              </div>
            </div>

            {/* F. Credits and Licences */}
            <div id="credits" className="about-section card-spotlight">
              <Reveal variant="up" delay={0}>
                <span className="section-eyebrow">ATTRIBUTION & INSTITUTION</span>
                <h3 className="about-section-heading">Credits and authorship</h3>
                <div className="about-authorship-card card-spotlight">
                  <img src={pesLogo} alt="PES College Logo" className="about-authorship-logo" />
                  <div className="about-authorship-info">
                    <div className="about-authorship-name">
                      Designed and developed by {SITE.developer}
                    </div>
                    <div className="about-authorship-college">
                      {SITE.collegeFull || SITE.college} &middot; Academic research in historical Kannada epigraphy &middot; {SITE.year}
                    </div>
                  </div>
                </div>
                <p className="about-body-text">
                  Enhancement approach and code: Shilalekhya, IIIT Hyderabad (MIT licence). Public EpiSAM images and checkpoints: CC BY-SA 4.0; imagery acknowledged to The Mythic Society, Bengaluru. Dataset previews shown in the application are derived works.
                </p>
              </Reveal>
              <div className="about-source-links">
                {/* Links staggered by 80ms */}
                <Reveal variant="up" delay={60}>
                  <a
                    href="https://github.com/epigraph-shilalekhya"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-link"
                  >
                    Shilalekhya Code Repository (MIT) &rarr;
                  </a>
                </Reveal>
                <Reveal variant="up" delay={140}>
                  <a
                    href="https://mythicsociety.org"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-link"
                  >
                    The Mythic Society Bengaluru (EpiSAM Images) &rarr;
                  </a>
                </Reveal>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
