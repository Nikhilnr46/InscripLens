import React, { useState, useRef } from 'react';
import {
  Upload,
  Sparkles,
  ArrowLeft,
  AlertCircle,
  FileImage,
  Layers,
  ShieldCheck,
  Check
} from 'lucide-react';
import ThemeToggle from '../components/ThemeToggle.tsx';
import Reveal from '../components/Reveal';
import RegionSelector from '../components/RegionSelector';

export default function ImportPage({
  onSelectHandoff,
  onSelectFile, // backwards compatibility
  onSelectDemo,
  onBackToLanding
}) {
  // Step state: 'choose' | 'select' (Studio is navigated to on completion)
  const [step, setStep] = useState('choose');
  const [selectedFile, setSelectedFile] = useState(null);

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

    // Transition to step 2: region selection (only for uploaded images)
    setSelectedFile(file);
    setStep('select');
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

  const handleConfirmCrop = (handoffData) => {
    if (onSelectHandoff) {
      onSelectHandoff(handoffData);
    } else if (onSelectFile) {
      onSelectFile(handoffData.file);
    }
  };

  const handleUseWholeImage = (fileToUse) => {
    const targetFile = fileToUse || selectedFile;
    if (!targetFile) return;

    const payload = {
      file: targetFile,
      originalFile: targetFile,
      selection: {
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        imageWidth: 0,
        imageHeight: 0,
        isWholeImage: true
      }
    };

    if (onSelectHandoff) {
      onSelectHandoff(payload);
    } else if (onSelectFile) {
      onSelectFile(targetFile);
    }
  };

  const handleCancelSelect = () => {
    // Release image reference and return to step 1
    setSelectedFile(null);
    setStep('choose');
    setErrorMessage('');
  };

  return (
    <div className="import-page-root">
      {/* Top Header matching Studio & Landing design system */}
      <header className="import-header studio-header">
        <div className="studio-brand">
          <button
            type="button"
            onClick={step === 'select' ? handleCancelSelect : onBackToLanding}
            className="home-pill-btn"
            title={step === 'select' ? 'Return to file chooser' : 'Return to InscripLens Overview'}
            aria-label={step === 'select' ? 'Back to chooser' : 'Back to Overview'}
          >
            <ArrowLeft size={15} />
            <span className="home-pill-text">
              {step === 'select' ? 'Back to Chooser' : 'Back to Overview'}
            </span>
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

        {/* 3-Step Indicator in Top Header */}
        <nav className="import-step-nav" aria-label="Import steps progress">
          <div className={`step-node ${step === 'choose' ? 'current' : 'done'}`}>
            <span className="step-circle">
              {step !== 'choose' ? <Check size={12} /> : '1'}
            </span>
            <span className="step-text">Choose</span>
          </div>

          <div className={`step-connector ${step === 'select' ? 'active' : ''}`} />

          <div className={`step-node ${step === 'select' ? 'current' : 'future'}`}>
            <span className="step-circle">2</span>
            <span className="step-text">Select area</span>
          </div>

          <div className="step-connector" />

          <div className="step-node future">
            <span className="step-circle">3</span>
            <span className="step-text">Studio</span>
          </div>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content: Step 1 (Choose) OR Step 2 (Select area) */}
      <main className="import-main-container">
        {step === 'choose' ? (
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
        ) : (
          /* Step 2: Region Selection View */
          <div className="import-selection-container">
            <div className="import-selection-header">
              <button
                type="button"
                className="import-back-nav"
                onClick={handleCancelSelect}
                aria-label="Back to chooser"
              >
                <ArrowLeft size={14} /> Back to Chooser
              </button>
              <h1 className="import-title">Select the area to scan</h1>
              <p className="import-subtitle">
                Drag on the stone to focus on inscribed lines and exclude margins, borders, or sculptures.
              </p>
            </div>

            <RegionSelector
              file={selectedFile}
              onConfirmCrop={handleConfirmCrop}
              onUseWholeImage={handleUseWholeImage}
              onCancel={handleCancelSelect}
            />
          </div>
        )}
      </main>
    </div>
  );
}
