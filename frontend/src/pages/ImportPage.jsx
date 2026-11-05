import React, { useState, useRef } from 'react';
import {
  Upload,
  Sparkles,
  ArrowLeft,
  AlertCircle,
  FileImage,
  Layers,
  ShieldCheck
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle.tsx';
import Reveal from '../components/Reveal';

export default function ImportPage({
  onSelectFile,
  onSelectDemo,
  onBackToLanding
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef(null);

  const validateAndHandle = (file) => {
    setErrorMessage('');
    if (!file) return;

    // Validate MIME type and file extension for PNG and JPG
    const acceptedMimes = ['image/png', 'image/jpeg', 'image/jpg'];
    const fileName = (file.name || '').toLowerCase();
    const isPngOrJpg = fileName.endsWith('.png') || fileName.endsWith('.jpg') || fileName.endsWith('.jpeg');
    const isAcceptedMime = acceptedMimes.includes(file.type);

    if (!isPngOrJpg && !isAcceptedMime) {
      setErrorMessage('Unsupported file format. Please upload a PNG or JPG photograph.');
      return;
    }

    // Size limit check: 20 megapixels / ~30 MB guard
    if (file.size > 30 * 1024 * 1024) {
      setErrorMessage('Image exceeds the 20 megapixel limit. Please select a smaller photograph.');
      return;
    }

    onSelectFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only unset dragging if leaving the drag area entirely
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      validateAndHandle(files[0]);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndHandle(file);
    }
  };

  return (
    <div className="import-page-root">
      {/* Top Header matching Studio & Landing design system */}
      <header className="import-header studio-header">
        <div className="studio-brand">
          <button
            type="button"
            onClick={onBackToLanding}
            className="home-pill-btn"
            title="Return to InscripLens Overview"
            aria-label="Return to Overview"
          >
            <ArrowLeft size={15} />
            <span className="home-pill-text">Back to Overview</span>
          </button>
          <div
            className="brand-logo-shimmer"
            style={{
              fontWeight: '700',
              fontSize: '1.15rem',
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              flexShrink: 0,
              whiteSpace: 'nowrap'
            }}
            onClick={onBackToLanding}
            title="Return to Landing Page"
          >
            <span className="brand-title">InscripLens</span>{' '}
            <span
              className="brand-tag"
              style={{
                color: 'var(--accent-sandstone)',
                fontSize: '0.85rem',
                fontWeight: '500'
              }}
            >
              Studio
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Centered Content */}
      <main className="import-main-container">
        <Reveal initialShown variant="up" delay={0}>
          <div className="import-card-wrapper card-spotlight">
            <div className="import-card-header">
              <button
                type="button"
                className="import-back-nav"
                onClick={onBackToLanding}
                aria-label="Back to landing page"
              >
                <ArrowLeft size={14} /> Back
              </button>
              <h1 className="import-title">Choose a stone image</h1>
              <p className="import-subtitle">
                Select a field photograph for neural stroke enhancement or begin with the curated benchmark stone.
              </p>
            </div>

            {errorMessage && (
              <div className="import-error-banner" role="alert">
                <AlertCircle size={15} className="import-error-icon" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Two large options side by side (stacked on narrow screens) */}
            <div className="import-options-grid">
              {/* Option A: Upload a photograph */}
              <div
                className={`import-option-panel upload-panel ${isDragging ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className="import-option-top">
                  <div className="import-icon-badge">
                    <Upload size={20} className="text-sandstone" />
                  </div>
                  <div>
                    <h2 className="import-option-heading">Upload a photograph</h2>
                    <p className="import-option-desc">
                      High-resolution field photo of an inscription.
                    </p>
                  </div>
                </div>

                <div
                  className="import-dropzone"
                  onClick={() => fileInputRef.current?.click()}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      fileInputRef.current?.click();
                    }
                  }}
                  aria-label="Upload field photograph dropzone"
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    style={{ display: 'none' }}
                    accept="image/png,image/jpeg,image/jpg"
                    onChange={handleFileChange}
                  />

                  <div className="dropzone-body">
                    <div className="dropzone-icon-circle">
                      <FileImage size={28} />
                    </div>
                    <span className="dropzone-prompt">
                      Drag and drop your image here
                    </span>
                    <span className="dropzone-divider">or</span>
                    <button
                      type="button"
                      className="btn-primary btn-browse btn-magnetic"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                    >
                      <Upload size={14} /> Browse image
                    </button>
                    <span className="dropzone-specs">
                      Accepted: PNG or JPG (up to 20 megapixels)
                    </span>
                  </div>
                </div>
              </div>

              {/* Option B: Use the demo stone */}
              <div
                className="import-option-panel demo-panel"
                onClick={onSelectDemo}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectDemo();
                  }
                }}
                aria-label="Use Nagavara demonstration stone"
              >
                <div className="import-option-top">
                  <div className="import-icon-badge">
                    <Sparkles size={20} className="text-sandstone" />
                  </div>
                  <div>
                    <h2 className="import-option-heading">Use the demo stone</h2>
                    <p className="import-option-desc">
                      Nagavara demonstration stone
                    </p>
                  </div>
                </div>

                <div className="demo-stone-card">
                  <div className="demo-stone-thumbnail-box">
                    <img
                      src="/api/demo/image"
                      alt="Nagavara demonstration stone"
                      className="demo-stone-img"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        const fallback = e.currentTarget.parentElement?.querySelector('.demo-fallback-box');
                        if (fallback) fallback.style.display = 'flex';
                      }}
                    />
                    <div className="demo-fallback-box" style={{ display: 'none' }}>
                      <Layers size={32} className="text-sandstone" />
                      <span>Nagavara Hero Stone</span>
                    </div>
                    <div className="demo-epoch-tag">971 CE &middot; Ganga Period</div>
                  </div>

                  <div className="demo-stone-info">
                    <div className="demo-stone-meta">
                      <span className="demo-stone-name">Nagavara demonstration stone</span>
                      <span className="demo-stone-details">
                        Historical hero stone with 133 candidate glyph regions and benchmark stroke ground truth.
                      </span>
                    </div>

                    <button
                      type="button"
                      className="btn-primary demo-action-btn btn-magnetic"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectDemo();
                      }}
                    >
                      <Sparkles size={14} /> Load Demo Stone &rarr;
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="import-card-footer">
              <ShieldCheck size={15} className="text-green" />
              <span>100% offline analysis. Your images are processed locally and never leave this machine.</span>
            </div>
          </div>
        </Reveal>
      </main>
    </div>
  );
}
