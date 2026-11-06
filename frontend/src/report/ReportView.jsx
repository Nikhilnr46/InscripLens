import React, { forwardRef } from 'react';
import { SITE } from '../config/site';

/**
 * Printable Analysis Report View (InscripLens Steps E1 & E2)
 *
 * Adheres strictly to A4 portrait white-paper design with Inter and Noto Sans Kannada.
 * Avoids page breaks inside cards, figures, and section headings.
 */
const ReportView = forwardRef(function ReportView(
  {
    reportData,
    stoneProfile,
    images = {},
    options = {},
    paperSize = 'a4'
  },
  ref
) {
  if (!reportData || !stoneProfile) return null;

  const {
    modeLabel,
    dimensions,
    selectedAreaNote,
    photoCaption,
    dateTime,
    hasClassificationRun,
    candidates = []
  } = reportData;

  const {
    includeUncertain = true,
    includeTiny = false,
    includeReviewerNames = true,
    scriptMode = 'kannada',
    modernLetters = false
  } = options;

  const isRomanMode = scriptMode === 'roman';

  // Filter candidates according to options
  const visibleCandidates = candidates.filter(cand => {
    if (!includeUncertain && cand.uncertain) return false;
    if (!includeTiny && cand.isTiny) return false;
    return true;
  });

  const tinyCount = candidates.filter(c => c.isTiny).length;

  const getProvenanceText = (source) => {
    switch (source) {
      case 'demo':
        return stoneProfile.alternateName
          ? `Demonstration stone (${stoneProfile.alternateName}) · Kadamba dynasty (c. 450–500 CE)`
          : 'Demonstration stone · Kadamba dynasty (c. 450–500 CE)';
      case 'user':
        return 'Name entered by the user';
      case 'unidentified':
      default:
        return 'Stone not identified. Automatic identification is not available yet.';
    }
  };

  const photoSrc = images.photoDataUrl || '';
  const maskSrc = images.maskDataUrl || '';

  return (
    <div
      ref={ref}
      className="inscriplens-report-root paper-sheet"
      data-paper={paperSize}
    >
      {/* a. Header */}
      <header className="report-header">
        <div className="report-brand-row">
          <div className="report-wordmark">
            <span className="report-wordmark-primary">InscripLens</span>{' '}
            <span className="report-wordmark-studio">Studio</span>
          </div>
          <div className="report-type-badge">
            Analysis report &middot; {paperSize === 'letter' ? 'Letter' : 'A4'}
          </div>
        </div>

        <div className="report-meta-row">
          <span className="report-meta-item">{dateTime}</span>
          <span className="report-meta-sep">&middot;</span>
          <span className="report-meta-item">{modeLabel}</span>
          {selectedAreaNote && (
            <>
              <span className="report-meta-sep">&middot;</span>
              <span className="report-meta-item report-selection-note">{selectedAreaNote}</span>
            </>
          )}
        </div>
      </header>

      {/* b. Stone Header */}
      <section className="report-stone-header">
        <h1 className="report-stone-title">{stoneProfile.name}</h1>
        <div className="report-stone-provenance">
          {getProvenanceText(stoneProfile.nameSource)}
        </div>
      </section>

      {/* c. Side-by-Side Images */}
      <section className="report-images-section">
        <div className="report-figures-grid">
          {/* Photograph / Selected Area */}
          <figure className="report-figure">
            <div className="report-img-frame">
              {photoSrc ? (
                <img
                  src={photoSrc}
                  alt={photoCaption}
                  className="report-img"
                />
              ) : (
                <div className="report-img-placeholder">Photograph loading...</div>
              )}
            </div>
            <figcaption className="report-figcaption">
              <span className="figcaption-title">{photoCaption}</span>
              <span className="figcaption-dims">
                {dimensions.width} &times; {dimensions.height} px
              </span>
            </figcaption>
          </figure>

          {/* Extracted Strokes (Mask) on Black Background */}
          <figure className="report-figure figure-mask">
            <div className="report-img-frame mask-frame">
              {maskSrc ? (
                <img
                  src={maskSrc}
                  alt="Extracted strokes (mask)"
                  className="report-img"
                />
              ) : (
                <div className="report-img-placeholder">Binary mask loading...</div>
              )}
            </div>
            <figcaption className="report-figcaption">
              <span className="figcaption-title">Extracted strokes (mask)</span>
              <span className="figcaption-dims">
                {dimensions.width} &times; {dimensions.height} px
              </span>
            </figcaption>
          </figure>
        </div>
      </section>

      {/* d. Detected Characters Section */}
      <section className="report-characters-section">
        <h2 className="report-section-heading">Detected characters</h2>
        <div className="report-characters-intro">
          {candidates.length} candidate regions. Machine suggestions, unverified. {
            isRomanMode
              ? 'Primary display: Roman IAST transliteration.'
              : modernLetters
                ? 'Primary display: Kannada script (modern substitution active).'
                : 'Primary display: Authentic epigraphic Kannada script.'
          } Listed in detection order, not reading order.
        </div>

        {!hasClassificationRun ? (
          <div className="report-unclassified-box">
            Characters have not been classified
          </div>
        ) : (
          <>
            {visibleCandidates.length === 0 ? (
              <div className="report-unclassified-box">
                No candidate regions match current filters.
              </div>
            ) : (
              <div className="report-candidates-grid">
                {visibleCandidates.map(cand => {
                  const isReviewed = cand.status === 'reviewed' || cand.status === 'corrected';
                  return (
                    <div
                      key={cand.index}
                      className={`report-candidate-card ${cand.uncertain ? 'is-uncertain' : ''} ${isReviewed ? 'is-reviewed' : ''}`}
                    >
                      <div className="card-top-row">
                        <span className="cand-num">#{cand.number}</span>
                        {cand.uncertain && (
                          <span className="cand-tag tag-uncertain">Uncertain</span>
                        )}
                        {isReviewed && (
                          <span className="cand-tag tag-reviewed">Reviewed</span>
                        )}
                      </div>

                      <div className="cand-thumb-frame">
                        {cand.thumbUrl ? (
                          <img
                            src={cand.thumbUrl}
                            alt={`Stroke crop #${cand.number}`}
                            className="cand-thumb-img"
                          />
                        ) : (
                          <div className="cand-thumb-empty" />
                        )}
                      </div>

                      <div className="cand-labels-wrap">
                        <div className={isRomanMode ? 'cand-roman-letter' : 'cand-kannada-letter'}>
                          {(isRomanMode ? cand.romanLabel : cand.kannadaLabel) || (
                            <span className="cand-dash">&ndash;</span>
                          )}
                          {!isRomanMode && cand.isLossy && (
                            <span
                              className="cand-lossy-marker"
                              title="Lossy modern transliteration"
                            >
                              *
                            </span>
                          )}
                        </div>

                        <div className={isRomanMode ? 'cand-kannada-sublabel' : 'cand-roman-label'}>
                          {(isRomanMode ? cand.kannadaLabel : cand.romanLabel) || (
                            <span className="cand-dash">&ndash;</span>
                          )}
                        </div>

                        {cand.confidence != null && (
                          <div className="cand-confidence">
                            {Math.round(cand.confidence * 100)}%
                          </div>
                        )}
                      </div>

                      {includeReviewerNames && cand.reviewerName && (
                        <div className="cand-reviewer-name" title={cand.reviewerName}>
                          Rev: {cand.reviewerName}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {!includeTiny && tinyCount > 0 && (
              <div className="report-tiny-omitted-note">
                {tinyCount} candidate region{tinyCount > 1 ? 's' : ''} under 10 &times; 10 px omitted from grid.
              </div>
            )}
          </>
        )}
      </section>

      {/* e. Historical Context & Epigraphic Brief */}
      {(stoneProfile.overview || stoneProfile.story) && (
        <section className="report-story-section">
          <div className="story-header-row">
            <h2 className="report-section-heading">Historical context &amp; epigraphic brief</h2>
            <span className="curated-text-badge">Curated record, not generated</span>
          </div>

          {stoneProfile.overview && (
            <div className="report-facts-grid">
              <div className="report-fact-card">
                <span className="fact-label">Date of Origin</span>
                <span className="fact-value">{stoneProfile.overview.dateOfOrigin}</span>
              </div>
              <div className="report-fact-card">
                <span className="fact-label">Location of Discovery</span>
                <span className="fact-value">{stoneProfile.overview.location}</span>
              </div>
              <div className="report-fact-card">
                <span className="fact-label">Discovery Details</span>
                <span className="fact-value">{stoneProfile.overview.discovery}</span>
              </div>
              <div className="report-fact-card">
                <span className="fact-label">Medium &amp; Script</span>
                <span className="fact-value">
                  {stoneProfile.overview.medium}
                  {stoneProfile.significance?.scriptAndDialect ? ` · ${stoneProfile.significance.scriptAndDialect}` : ''}
                </span>
              </div>
            </div>
          )}

          {stoneProfile.significance && (
            <div className="report-brief-block">
              <h3 className="brief-subheading">Linguistic &amp; Cultural Significance</h3>
              <ul className="brief-points-list">
                <li>
                  <strong>Language Milestone:</strong> {stoneProfile.significance.languageMilestone}
                </li>
                <li>
                  <strong>Script &amp; Dialect:</strong> {stoneProfile.significance.scriptAndDialect}
                </li>
                <li>
                  <strong>Administrative Evidence:</strong> {stoneProfile.significance.administrativeEvidence}
                </li>
              </ul>
            </div>
          )}

          {stoneProfile.narrative && (
            <div className="report-brief-block">
              <h3 className="brief-subheading">Core Narrative &amp; Historical Context</h3>
              <div className="narrative-meta-row">
                <span><strong>Issuing Authority:</strong> {stoneProfile.narrative.issuingAuthority}</span>
                <span className="narrative-sep">&middot;</span>
                <span><strong>Purpose:</strong> {stoneProfile.narrative.purpose}</span>
              </div>
              <p className="report-story-body">{stoneProfile.narrative.story}</p>
            </div>
          )}

          {!stoneProfile.overview && stoneProfile.story && (
            <p className="report-story-body">{stoneProfile.story}</p>
          )}

          {stoneProfile.storySource && (
            <div className="report-story-source">
              Source: {stoneProfile.storySource}
            </div>
          )}
        </section>
      )}

      {/* f. Notes and Credits */}
      <section className="report-credits-section">
        <h2 className="report-section-heading">Research notes &amp; licences</h2>
        <div className="report-disclaimer-p">
          Suggestions are experimental and may be wrong. Please verify with a qualified epigraphist.
        </div>
        <div className="report-licence-text">
          Enhancement approach and code: Shilalekhya, IIIT Hyderabad (MIT licence). Public EpiSAM images and checkpoints: CC BY-SA 4.0, imagery acknowledged to The Mythic Society Bengaluru; dataset previews are derived works.
        </div>
        <div className="report-developer-line">
          Developed by {SITE.developer}, {SITE.college} &middot; {SITE.year}
        </div>
      </section>

      {/* g. Fixed Print Footer */}
      <footer className="report-print-footer">
        <span className="print-footer-stone">{stoneProfile.name}</span>
        <span className="print-footer-studio">InscripLens Studio</span>
        <span className="print-footer-dev">
          Developed by {SITE.developer}, {SITE.college} &middot; {SITE.year}
        </span>
      </footer>
    </div>
  );
});

export default ReportView;
