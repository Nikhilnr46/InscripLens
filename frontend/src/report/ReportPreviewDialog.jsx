import React, { useState, useEffect, useRef } from 'react';
import { Printer, X, FileText, Info, Loader2, Sparkles, AlertCircle } from 'lucide-react';
import ReportView from './ReportView';
import { getStoneProfile } from './stoneProfile';
import { buildReportData, prepareReportImages } from './buildReportData';
import './report.css';

/**
 * Fullscreen Report Preview Modal with Interactive Options Panel (Steps E1 & E2)
 */
export default function ReportPreviewDialog({
  isOpen,
  onClose,
  analysis,
  selectionInfo = null,
  batchRegions = [],
  predictionCache = {},
  reviewsList = [],
  highAccuracy = false,
  scriptMode = 'kannada',
  initialModernLetters = false,
  onClassifyAll = null,
  isClassifying = false
}) {
  const [userEnteredName, setUserEnteredName] = useState('');
  const [includeUncertain, setIncludeUncertain] = useState(true);
  const [includeTiny, setIncludeTiny] = useState(false);
  const [includeReviewerNames, setIncludeReviewerNames] = useState(true);
  const [kannadaStyle, setKannadaStyle] = useState(initialModernLetters ? 'modern' : 'faithful');
  const [paperSize, setPaperSize] = useState('a4');
  const [exportWithoutLabels, setExportWithoutLabels] = useState(false);

  const [imagesReady, setImagesReady] = useState(false);
  const [preparedImages, setPreparedImages] = useState({ photoDataUrl: '', maskDataUrl: '', thumbnails: {} });
  const [isPrinting, setIsPrinting] = useState(false);

  const reportRef = useRef(null);

  // Sync initial state from Studio when dialog opens
  useEffect(() => {
    if (isOpen) {
      setKannadaStyle(initialModernLetters ? 'modern' : 'faithful');
      setUserEnteredName('');
      setExportWithoutLabels(false);
    }
  }, [isOpen, initialModernLetters]);

  // Prepare images on open
  useEffect(() => {
    if (!isOpen || !analysis) return;
    let isCancelled = false;
    setImagesReady(false);

    prepareReportImages({
      analysis,
      boxes: analysis.boxes || []
    }).then((imgs) => {
      if (!isCancelled) {
        setPreparedImages(imgs);
        setImagesReady(true);
      }
    }).catch(err => {
      console.error('Failed to prepare report images:', err);
      if (!isCancelled) {
        setImagesReady(true);
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [isOpen, analysis]);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !isPrinting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isPrinting, onClose]);

  if (!isOpen || !analysis) return null;

  const isDemo = Boolean(analysis.is_demo);
  const modernLetters = kannadaStyle === 'modern';

  const stoneProfile = getStoneProfile({
    run: analysis,
    isDemo,
    userEnteredName
  });

  const reportData = buildReportData({
    analysis,
    selectionInfo,
    batchRegions,
    predictionCache,
    reviewsList,
    highAccuracy,
    options: {
      modernLetters
    },
    thumbnails: preparedImages.thumbnails
  });

  const showUnclassifiedNotice = Boolean(reportData && !reportData.hasClassificationRun && !exportWithoutLabels);

  const handleClassifyAllNow = async () => {
    if (onClassifyAll) {
      await onClassifyAll();
    }
  };

  const handleSaveAsPdf = async () => {
    setIsPrinting(true);
    const origTitle = document.title;
    const dateStr = new Date().toISOString().split('T')[0];
    const safeStoneName = (stoneProfile.name || 'Stone').replace(/[\\/:*?"<>|]/g, '');
    document.title = `InscripLens report - ${safeStoneName} - ${dateStr}`;

    const restoreTitle = () => {
      document.title = origTitle;
      window.removeEventListener('afterprint', restoreTitle);
    };
    window.addEventListener('afterprint', restoreTitle);

    try {
      // 1. Wait for document fonts to be ready
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }

      // 2. Wait for all <img> elements in the report to decode
      if (reportRef.current) {
        const imgs = Array.from(reportRef.current.querySelectorAll('img'));
        await Promise.all(
          imgs.map(img => {
            if (img.complete) return Promise.resolve();
            return img.decode().catch(() => {});
          })
        );
      }

      // 3. Trigger browser native print dialog
      window.print();
    } catch (err) {
      console.error('Print trigger failed:', err);
    } finally {
      setIsPrinting(false);
      // Fallback restore in case afterprint doesn't fire immediately
      setTimeout(() => {
        document.title = origTitle;
      }, 1000);
    }
  };

  return (
    <div
      className="report-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Analysis report preview"
    >
      {/* Left Options Control Panel */}
      <aside className="report-options-panel">
        <div className="options-panel-header">
          <div className="options-title-row">
            <FileText size={18} className="text-sandstone" />
            <h2 className="options-title">Report settings</h2>
          </div>
          <button
            type="button"
            className="options-close-icon-btn"
            onClick={onClose}
            aria-label="Close report preview"
            disabled={isPrinting}
          >
            <X size={18} />
          </button>
        </div>

        <div className="options-scroll-content">
          {/* Stone Name Input (Hidden for demo stone) */}
          {!isDemo && (
            <div className="option-group">
              <label htmlFor="report-stone-name-input" className="option-label">
                Stone name
              </label>
              <input
                id="report-stone-name-input"
                type="text"
                className="option-input-text"
                value={userEnteredName}
                onChange={(e) => setUserEnteredName(e.target.value)}
                placeholder="e.g. Begur hero stone"
                maxLength={100}
              />
              <span className="option-help-text">
                Leave empty for "Stone not identified".
              </span>
            </div>
          )}

          {/* Toggle Switches */}
          <div className="option-group">
            <span className="option-group-title">Content options</span>

            <label className="option-toggle-row">
              <input
                type="checkbox"
                checked={includeUncertain}
                onChange={(e) => setIncludeUncertain(e.target.checked)}
                className="option-checkbox"
              />
              <span className="option-toggle-label">Include uncertain characters</span>
            </label>

            <label className="option-toggle-row">
              <input
                type="checkbox"
                checked={includeTiny}
                onChange={(e) => setIncludeTiny(e.target.checked)}
                className="option-checkbox"
              />
              <span className="option-toggle-label">Include characters under 10 &times; 10 px</span>
            </label>

            <label className="option-toggle-row">
              <input
                type="checkbox"
                checked={includeReviewerNames}
                onChange={(e) => setIncludeReviewerNames(e.target.checked)}
                className="option-checkbox"
              />
              <span className="option-toggle-label">Include reviewer names</span>
            </label>
          </div>

          {/* Kannada Style (Faithful vs Modern Letters) */}
          <div className="option-group">
            <span className="option-group-title">Kannada style</span>
            <div className="segmented-control option-segmented">
              <button
                type="button"
                className={`segmented-btn ${kannadaStyle === 'faithful' ? 'active' : ''}`}
                onClick={() => setKannadaStyle('faithful')}
              >
                Faithful
              </button>
              <button
                type="button"
                className={`segmented-btn ${kannadaStyle === 'modern' ? 'active' : ''}`}
                onClick={() => setKannadaStyle('modern')}
              >
                Modern letters
              </button>
            </div>
            <span className="option-help-text">
              {kannadaStyle === 'modern'
                ? 'Maps archaic Halegannada letters (ಱ, ೞ) to modern forms with an asterisk.'
                : 'Preserves authentic epigraphic characters without modern substitution.'}
            </span>
          </div>

          {/* Paper Size (A4 vs Letter) */}
          <div className="option-group">
            <span className="option-group-title">Paper size</span>
            <div className="segmented-control option-segmented">
              <button
                type="button"
                className={`segmented-btn ${paperSize === 'a4' ? 'active' : ''}`}
                onClick={() => setPaperSize('a4')}
              >
                A4
              </button>
              <button
                type="button"
                className={`segmented-btn ${paperSize === 'letter' ? 'active' : ''}`}
                onClick={() => setPaperSize('letter')}
              >
                Letter
              </button>
            </div>
          </div>

          {/* Helper destination notice */}
          <div className="option-destination-notice">
            <Info size={14} className="text-sandstone" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>In the print window choose <strong>Save as PDF</strong> as the destination.</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="options-panel-actions">
          <button
            type="button"
            className="btn-primary options-save-btn"
            onClick={handleSaveAsPdf}
            disabled={!imagesReady || isPrinting}
          >
            {isPrinting ? (
              <>
                <Loader2 size={15} className="spin-icon" /> Preparing print...
              </>
            ) : (
              <>
                <Printer size={15} /> Save as PDF
              </>
            )}
          </button>
          <button
            type="button"
            className="btn-secondary options-cancel-btn"
            onClick={onClose}
            disabled={isPrinting}
          >
            Close
          </button>
        </div>
      </aside>

      {/* Right Scrollable Paper Preview */}
      <main className="report-preview-scroll-area">
        {!imagesReady && (
          <div className="report-loading-indicator">
            <Loader2 size={24} className="spin-icon text-sandstone" />
            <span>Preparing report figures and stroke thumbnails...</span>
          </div>
        )}

        {/* Step E2 Task 1: Unclassified Characters Notice */}
        {showUnclassifiedNotice && (
          <div className="report-unclassified-banner">
            <div className="unclassified-banner-header">
              <AlertCircle size={18} className="text-sandstone" style={{ flexShrink: 0 }} />
              <div className="unclassified-banner-title">
                Characters have not been classified.
              </div>
            </div>
            <p className="unclassified-banner-desc">
              Candidate character regions have been detected on the stone, but classification has not been run. You can classify them now to populate Kannada letters and transliterations, or proceed to export without labels.
            </p>
            <div className="unclassified-banner-actions">
              <button
                type="button"
                className="btn-primary unclassified-action-btn"
                onClick={handleClassifyAllNow}
                disabled={isClassifying}
              >
                {isClassifying ? (
                  <>
                    <Loader2 size={14} className="spin-icon" /> Classifying candidate regions...
                  </>
                ) : (
                  <>
                    <Sparkles size={14} /> Classify all now
                  </>
                )}
              </button>
              <button
                type="button"
                className="btn-secondary unclassified-action-btn"
                onClick={() => setExportWithoutLabels(true)}
                disabled={isClassifying}
              >
                Export without labels
              </button>
            </div>
          </div>
        )}

        <ReportView
          ref={reportRef}
          reportData={reportData}
          stoneProfile={stoneProfile}
          images={preparedImages}
          options={{
            includeUncertain,
            includeTiny,
            includeReviewerNames,
            modernLetters
          }}
          paperSize={paperSize}
        />
      </main>
    </div>
  );
}
