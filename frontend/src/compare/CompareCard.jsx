/**
 * CompareCard: Inspector component for glyph redrawing, comparison, and evaluation.
 *
 * Placed in the Inspector between Alternatives and Verification & Expert Review.
 * Displays:
 * 1. Initial State: "Redraw and compare" card with "Redraw box" button.
 * 2. Loading State: Dual-column skeleton pulse indicators.
 * 3. Compared State:
 *    - Context overview of the stone region with dual-box outlines and Photo/Mask switch.
 *    - Side-by-side columns: "Automatic" (dashed neutral) vs "Redrawn" (solid accent).
 *    - Crop images, primary predictions, confidence bars, and top 3 suggestion chips.
 *    - "Your reading (tentative)" field with live Kannada conversion preview.
 *    - Per-column rank readouts and overall outcome tag.
 *    - "Redraw again", "Discard", and disabled "Save" (coming in Step R3).
 */

import React, { useState, useMemo, useEffect } from 'react';
import { Crop, RotateCcw, Trash2, Save, AlertCircle, Check, Layers, Download } from 'lucide-react';
import { toKannada, formatDisplayLabel } from '../utils/kannadaConverter';
import { evaluateComparisonOutcome, findRankInAlternatives, normalizeToKannada } from './outcome';
import { saveComparison, listComparisons, downloadComparisonsJson } from './store';
import { generateThumbnailFromUrl } from './thumbnail';
import './compare.css';

export default function CompareCard({
  candidateIndex,
  candidateNumber,
  analysis,
  scriptMode = 'kannada',
  modernLetters = false,
  highAccuracy = false,
  isComparing = false,
  comparisonData = null,
  onStartRedraw,
  onRedrawAgain,
  onDiscard,
  onRetryAuto,
  onRetryRedrawn,
  onOpenSavedDrawer
}) {
  const [overviewLayer, setOverviewLayer] = useState('mask'); // 'mask' | 'photo'
  const [tentativeReading, setTentativeReading] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccessNotice, setSaveSuccessNotice] = useState(false);
  const [storageErrorNotice, setStorageErrorNotice] = useState(null);
  const [savedCountVersion, setSavedCountVersion] = useState(0);

  // Live Kannada conversion preview when user enters Roman text
  const liveKannadaPreview = useMemo(() => {
    if (!tentativeReading || !tentativeReading.trim()) return '';
    const trimmed = tentativeReading.trim();
    if (/[a-zA-Z]/.test(trimmed)) {
      return toKannada(trimmed);
    }
    return '';
  }, [tentativeReading]);

  // Counts of saved records for this candidate and run
  const savedCandidateCount = useMemo(() => {
    if (!analysis?.id || candidateIndex == null) return 0;
    try {
      const records = listComparisons(analysis.id);
      return records.filter(r => r.candidate_index === candidateIndex).length;
    } catch {
      return 0;
    }
  }, [analysis?.id, candidateIndex, savedCountVersion]);

  const totalRunSavedCount = useMemo(() => {
    if (!analysis?.id) return 0;
    try {
      return listComparisons(analysis.id).length;
    } catch {
      return 0;
    }
  }, [analysis?.id, savedCountVersion]);

  // Compute outcome and per-column ranks
  const outcomeResult = useMemo(() => {
    if (!comparisonData?.automatic?.result || !comparisonData?.redrawn?.result) {
      return null;
    }
    const proposed = tentativeReading && tentativeReading.trim()
      ? { text: tentativeReading.trim(), script: /[a-zA-Z]/.test(tentativeReading) ? 'roman' : 'kannada' }
      : null;

    return evaluateComparisonOutcome(
      proposed,
      comparisonData.automatic.result,
      comparisonData.redrawn.result
    );
  }, [comparisonData, tentativeReading]);

  // Save comparison handler
  const handleSaveComparison = async () => {
    if (
      !analysis ||
      candidateIndex == null ||
      !comparisonData?.automatic?.result ||
      !comparisonData?.redrawn?.result
    ) {
      return;
    }

    setIsSaving(true);
    setStorageErrorNotice(null);

    const autoRes = comparisonData.automatic.result;
    const redrawnRes = comparisonData.redrawn.result;
    const autoBbox = comparisonData.automatic.bbox;
    const redrawnBbox = comparisonData.redrawn.bbox;

    // Generate compact 96px thumbnails
    const [autoThumb, redrawnThumb] = await Promise.all([
      generateThumbnailFromUrl(autoRes.cropUrl, 96),
      generateThumbnailFromUrl(redrawnRes.cropUrl, 96)
    ]);

    const proposed = tentativeReading && tentativeReading.trim()
      ? {
          text: tentativeReading.trim(),
          script: /[a-zA-Z]/.test(tentativeReading) ? 'roman' : 'kannada',
          tentative: true
        }
      : {
          text: '',
          script: 'kannada',
          tentative: true
        };

    const recordToSave = {
      // Omitting id so saveComparison generates a distinct ID for each save attempt
      run_id: analysis.id,
      candidate_number: candidateNumber,
      candidate_index: candidateIndex,
      image_size: { width: analysis.width, height: analysis.height },
      enhancement_mode: highAccuracy ? 'high_accuracy' : 'standard',
      automatic: {
        bbox: autoBbox,
        prediction: autoRes.prediction,
        prediction_kannada: autoRes.predictionKannada,
        alternatives: autoRes.alternatives,
        confidence: autoRes.confidence,
        model_sha256: autoRes.modelSha256
      },
      redrawn: {
        bbox: redrawnBbox,
        prediction: redrawnRes.prediction,
        prediction_kannada: redrawnRes.predictionKannada,
        alternatives: redrawnRes.alternatives,
        confidence: redrawnRes.confidence,
        model_sha256: redrawnRes.modelSha256
      },
      proposed_reading: proposed,
      outcome: outcomeResult ? outcomeResult.outcome : 'unknown',
      rank_note: outcomeResult ? outcomeResult.rank_note : 'Ranks beyond 3 are not available.',
      automatic_thumbnail: autoThumb,
      redrawn_thumbnail: redrawnThumb
    };

    const saveRes = saveComparison(recordToSave);
    setIsSaving(false);

    if (saveRes.success) {
      setSaveSuccessNotice(true);
      setSavedCountVersion(v => v + 1);
      setTimeout(() => setSaveSuccessNotice(false), 4500);
    } else {
      setStorageErrorNotice(saveRes.error || 'Storage full or blocked. Download JSON now.');
    }
  };

  // Compute context bounding box for the stone region overview image
  const overviewBox = useMemo(() => {
    if (!comparisonData?.automatic?.bbox || !comparisonData?.redrawn?.bbox || !analysis) {
      return null;
    }
    const b1 = comparisonData.automatic.bbox;
    const b2 = comparisonData.redrawn.bbox;

    const minX = Math.min(b1[0], b2[0]);
    const minY = Math.min(b1[1], b2[1]);
    const maxX = Math.max(b1[2], b2[2]);
    const maxY = Math.max(b1[3], b2[3]);

    const boxW = Math.max(1, maxX - minX);
    const boxH = Math.max(1, maxY - minY);

    // Add 45% margin around the combined boxes
    const padX = Math.round(boxW * 0.45);
    const padY = Math.round(boxH * 0.45);

    const ovX = Math.max(0, minX - padX);
    const ovY = Math.max(0, minY - padY);
    const ovW = Math.min(analysis.width - ovX, boxW + padX * 2);
    const ovH = Math.min(analysis.height - ovY, boxH + padY * 2);

    return { x: ovX, y: ovY, width: Math.max(10, ovW), height: Math.max(10, ovH) };
  }, [comparisonData, analysis]);

  // Format rank string: 1st, 2nd, 3rd, or not in the top 3
  const formatRankLabel = (rank) => {
    if (rank === 1) return 'Your reading is 1st';
    if (rank === 2) return 'Your reading is 2nd';
    if (rank === 3) return 'Your reading is 3rd';
    return 'not in the top 3';
  };

  // 1. Initial State: Button to enter redraw mode
  if (!isComparing && !comparisonData) {
    return (
      <div className="inspector-section compare-card-section">
        <div className="compare-card-header">
          <div className="compare-card-title">
            <Crop size={14} color="var(--accent-sandstone, #C9A66B)" />
            <span>Redraw and compare</span>
          </div>
          {savedCandidateCount > 0 && (
            <span
              className="compare-saved-count-pill"
              title={`${savedCandidateCount} comparisons saved for candidate #${candidateNumber}`}
            >
              {savedCandidateCount} saved
            </span>
          )}
        </div>

        <div className="compare-initial-box">
          <p className="compare-initial-desc">
            Outline the full glyph, then compare.
          </p>
          <button
            type="button"
            className="btn-secondary"
            onClick={onStartRedraw}
            style={{ width: '100%', height: '32px', fontSize: '0.8rem', gap: '6px' }}
            title="Outline a custom region for this candidate and compare predictions (R)"
          >
            <Crop size={13} /> Redraw box
          </button>

          {totalRunSavedCount > 0 && onOpenSavedDrawer && (
            <button
              type="button"
              className="btn-secondary compare-view-drawer-btn"
              onClick={onOpenSavedDrawer}
              style={{ width: '100%', height: '28px', fontSize: '0.74rem', gap: '5px', marginTop: '4px' }}
              title="Open saved comparisons drawer"
            >
              <Layers size={12} /> View saved comparisons ({totalRunSavedCount})
            </button>
          )}
        </div>
      </div>
    );
  }

  // 2. Loading State: Parallel prediction skeletons
  if (isComparing && !comparisonData) {
    return (
      <div className="inspector-section compare-card-section">
        <div className="compare-card-header">
          <div className="compare-card-title">
            <Crop size={14} color="var(--accent-sandstone, #C9A66B)" />
            <span>Comparing glyph regions...</span>
          </div>
        </div>

        <div className="compare-grid">
          {/* Automatic Skeleton Column */}
          <div className="compare-column">
            <div className="compare-col-chip automatic">Automatic</div>
            <div className="compare-col-crop skeleton-pulse" />
            <div style={{ height: '36px', width: '50px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px' }} className="skeleton-pulse" />
            <div style={{ height: '14px', width: '80%', backgroundColor: 'var(--bg-elevated)', borderRadius: '3px' }} className="skeleton-pulse" />
          </div>

          {/* Redrawn Skeleton Column */}
          <div className="compare-column">
            <div className="compare-col-chip redrawn">Redrawn</div>
            <div className="compare-col-crop skeleton-pulse" />
            <div style={{ height: '36px', width: '50px', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px' }} className="skeleton-pulse" />
            <div style={{ height: '14px', width: '80%', backgroundColor: 'var(--bg-elevated)', borderRadius: '3px' }} className="skeleton-pulse" />
          </div>
        </div>
      </div>
    );
  }

  const autoRes = comparisonData?.automatic?.result;
  const autoErr = comparisonData?.automatic?.error;
  const autoBbox = comparisonData?.automatic?.bbox;

  const redrawnRes = comparisonData?.redrawn?.result;
  const redrawnErr = comparisonData?.redrawn?.error;
  const redrawnBbox = comparisonData?.redrawn?.bbox;

  const canSave = Boolean(autoRes && redrawnRes && !autoErr && !redrawnErr);

  return (
    <div className="inspector-section compare-card-section">
      <div className="compare-card-header">
        <div className="compare-card-title">
          <Crop size={14} color="var(--accent-sandstone, #C9A66B)" />
          <span>Redraw &amp; Compare</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {savedCandidateCount > 0 && (
            <span
              className="compare-saved-count-pill"
              title={`${savedCandidateCount} comparisons saved for candidate #${candidateNumber}`}
            >
              {savedCandidateCount} saved
            </span>
          )}
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Candidate #{candidateNumber}
          </span>
        </div>
      </div>

      {/* Overview Image with Outlines & Photo/Mask Switch */}
      {overviewBox && analysis && (
        <div className="compare-overview-container">
          <div className="compare-overview-header">
            <span>Context Overview</span>
            <div className="redraw-layer-toggle" role="group" aria-label="Overview layer">
              <button
                type="button"
                className={`redraw-layer-btn ${overviewLayer === 'mask' ? 'active' : ''}`}
                onClick={() => setOverviewLayer('mask')}
                aria-pressed={overviewLayer === 'mask'}
              >
                Mask
              </button>
              <button
                type="button"
                className={`redraw-layer-btn ${overviewLayer === 'photo' ? 'active' : ''}`}
                onClick={() => setOverviewLayer('photo')}
                aria-pressed={overviewLayer === 'photo'}
              >
                Photo
              </button>
            </div>
          </div>

          <svg
            viewBox={`${overviewBox.x} ${overviewBox.y} ${overviewBox.width} ${overviewBox.height}`}
            className="compare-overview-svg"
            preserveAspectRatio="xMidYMid meet"
          >
            <image
              href={overviewLayer === 'mask' ? analysis.mask_url : analysis.image_url}
              x={0}
              y={0}
              width={analysis.width}
              height={analysis.height}
            />
            {/* Automatic Box (Dashed Neutral) */}
            {autoBbox && (
              <rect
                x={autoBbox[0]}
                y={autoBbox[1]}
                width={autoBbox[2] - autoBbox[0]}
                height={autoBbox[3] - autoBbox[1]}
                fill="rgba(168, 162, 154, 0.15)"
                stroke="var(--text-subtle, #A8A29A)"
                strokeWidth={1.8}
                strokeDasharray="4 3"
              />
            )}
            {/* Redrawn Box (Solid Sandstone Accent) */}
            {redrawnBbox && (
              <rect
                x={redrawnBbox[0]}
                y={redrawnBbox[1]}
                width={redrawnBbox[2] - redrawnBbox[0]}
                height={redrawnBbox[3] - redrawnBbox[1]}
                fill="rgba(201, 166, 107, 0.2)"
                stroke="var(--accent-sandstone, #C9A66B)"
                strokeWidth={2}
              />
            )}
          </svg>
        </div>
      )}

      {/* Two-Column Side-by-Side Comparison */}
      <div className="compare-grid">
        {/* Column 1: Automatic Candidate */}
        <div className="compare-column">
          <div className="compare-col-header">
            <span className="compare-col-chip automatic">Automatic</span>
            {autoBbox && (
              <span style={{ fontSize: '0.65rem', color: 'var(--text-subtle)' }}>
                {autoBbox[2] - autoBbox[0]}&times;{autoBbox[3] - autoBbox[1]}px
              </span>
            )}
          </div>

          {autoErr ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', padding: '8px', color: '#E06C75', fontSize: '0.72rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <AlertCircle size={12} />
                <span>Prediction failed</span>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={onRetryAuto}
                style={{ height: '22px', fontSize: '0.68rem', padding: '0 6px' }}
              >
                <RotateCcw size={10} /> Retry
              </button>
            </div>
          ) : autoRes ? (
            <>
              <div className="compare-col-crop">
                {autoRes.cropUrl ? (
                  <img
                    src={autoRes.cropUrl}
                    alt={`Automatic crop of candidate #${candidateNumber}`}
                  />
                ) : (
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>No crop</span>
                )}
              </div>

              {/* Primary Prediction */}
              {(() => {
                const disp = formatDisplayLabel(autoRes.prediction, scriptMode, modernLetters);
                return (
                  <div className="compare-col-prediction">
                    <span
                      className="compare-large-glyph"
                      style={{
                        fontFamily: (scriptMode === 'kannada' && !disp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit'
                      }}
                    >
                      {disp.primary}
                    </span>
                    {disp.secondary && (
                      <span className="compare-sub-glyph">
                        ({disp.secondary})
                      </span>
                    )}
                  </div>
                );
              })()}

              {/* Confidence Bar if Present */}
              {autoRes.confidence != null && (
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-subtle)', marginBottom: '2px' }}>
                    <span>Confidence</span>
                    <span>{Math.round(autoRes.confidence * 100)}%</span>
                  </div>
                  <div className="confidence-bar-subtle" style={{ height: '3px' }}>
                    <div
                      className="confidence-bar-subtle-fill"
                      style={{ width: `${Math.round(autoRes.confidence * 100)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Top 3 Alternatives */}
              {Array.isArray(autoRes.alternatives) && autoRes.alternatives.length > 0 && (
                <div className="compare-col-alts">
                  {autoRes.alternatives.slice(0, 3).map((alt, idx) => {
                    const label = typeof alt === 'object' ? alt.label : alt;
                    const disp = formatDisplayLabel(label, scriptMode, modernLetters);
                    return (
                      <button
                        key={idx}
                        type="button"
                        className="compare-alt-chip"
                        onClick={() => setTentativeReading(label)}
                        title={`Click to adopt '${label}' as your reading`}
                      >
                        {disp.primary}
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <div className="compare-col-crop skeleton-pulse" />
          )}
        </div>

        {/* Column 2: Redrawn Candidate */}
        <div className="compare-column">
          <div className="compare-col-header">
            <span className="compare-col-chip redrawn">Redrawn</span>
            {redrawnBbox && (
              <span style={{ fontSize: '0.65rem', color: 'var(--text-subtle)' }}>
                {redrawnBbox[2] - redrawnBbox[0]}&times;{redrawnBbox[3] - redrawnBbox[1]}px
              </span>
            )}
          </div>

          {redrawnErr ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', padding: '8px', color: '#E06C75', fontSize: '0.72rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <AlertCircle size={12} />
                <span>Prediction failed</span>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={onRetryRedrawn}
                style={{ height: '22px', fontSize: '0.68rem', padding: '0 6px' }}
              >
                <RotateCcw size={10} /> Retry
              </button>
            </div>
          ) : redrawnRes ? (
            <>
              <div className="compare-col-crop">
                {redrawnRes.cropUrl ? (
                  <img
                    src={redrawnRes.cropUrl}
                    alt={`Redrawn crop for candidate #${candidateNumber}`}
                  />
                ) : (
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)' }}>No crop</span>
                )}
              </div>

              {/* Primary Prediction */}
              {(() => {
                const disp = formatDisplayLabel(redrawnRes.prediction, scriptMode, modernLetters);
                return (
                  <div className="compare-col-prediction">
                    <span
                      className="compare-large-glyph"
                      style={{
                        fontFamily: (scriptMode === 'kannada' && !disp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit'
                      }}
                    >
                      {disp.primary}
                    </span>
                    {disp.secondary && (
                      <span className="compare-sub-glyph">
                        ({disp.secondary})
                      </span>
                    )}
                  </div>
                );
              })()}

              {/* Confidence Bar if Present */}
              {redrawnRes.confidence != null && (
                <div style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-subtle)', marginBottom: '2px' }}>
                    <span>Confidence</span>
                    <span>{Math.round(redrawnRes.confidence * 100)}%</span>
                  </div>
                  <div className="confidence-bar-subtle" style={{ height: '3px' }}>
                    <div
                      className="confidence-bar-subtle-fill"
                      style={{ width: `${Math.round(redrawnRes.confidence * 100)}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Top 3 Alternatives */}
              {Array.isArray(redrawnRes.alternatives) && redrawnRes.alternatives.length > 0 && (
                <div className="compare-col-alts">
                  {redrawnRes.alternatives.slice(0, 3).map((alt, idx) => {
                    const label = typeof alt === 'object' ? alt.label : alt;
                    const disp = formatDisplayLabel(label, scriptMode, modernLetters);
                    return (
                      <button
                        key={idx}
                        type="button"
                        className="compare-alt-chip"
                        onClick={() => setTentativeReading(label)}
                        title={`Click to adopt '${label}' as your reading`}
                      >
                        {disp.primary}
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <div className="compare-col-crop skeleton-pulse" />
          )}
        </div>
      </div>

      {/* "Your reading (tentative)" Section */}
      <div className="compare-reading-box">
        <div className="compare-reading-header">
          <label
            htmlFor="tentative-reading-input"
            style={{ fontSize: '0.74rem', fontWeight: '600', color: 'var(--text-primary)' }}
          >
            Your reading (tentative)
          </label>
          {outcomeResult && tentativeReading.trim() && (
            <span className={`compare-outcome-badge outcome-${outcomeResult.outcome}`}>
              {outcomeResult.outcome}
            </span>
          )}
        </div>

        <div className="compare-reading-input-wrap">
          <input
            id="tentative-reading-input"
            type="text"
            className="compare-reading-input"
            placeholder="Type Kannada or Roman..."
            value={tentativeReading}
            onChange={(e) => setTentativeReading(e.target.value)}
          />
          {liveKannadaPreview && (
            <span className="compare-live-kannada-tag" title="Live Kannada transliteration">
              {liveKannadaPreview}
            </span>
          )}
        </div>

        {/* Per-Column Ranks when Reading is Provided */}
        {tentativeReading.trim() && outcomeResult && (
          <div>
            <div className="compare-ranks-summary">
              <div>Automatic: <strong>{formatRankLabel(outcomeResult.autoRank)}</strong></div>
              <div>Redrawn: <strong>{formatRankLabel(outcomeResult.redrawnRank)}</strong></div>
            </div>
            <div className="compare-ranks-note">
              Only the top three suggestions are available.
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="compare-card-actions">
        <button
          type="button"
          className="btn-secondary"
          onClick={onRedrawAgain}
          style={{ flex: 1, height: '30px', fontSize: '0.75rem', gap: '4px' }}
          title="Tweak redrawn rectangle in the viewer"
        >
          <RotateCcw size={12} /> Redraw again
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={onDiscard}
          style={{ flex: 1, height: '30px', fontSize: '0.75rem', gap: '4px' }}
          title="Discard this comparison"
        >
          <Trash2 size={12} /> Discard
        </button>
      </div>

      {/* Save Success Confirmation Banner */}
      {saveSuccessNotice && (
        <div className="compare-save-success-banner" role="status">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Check size={13} color="#5CB85C" />
            <span>Saved in this browser only</span>
          </div>
          <span className="compare-saved-count-pill">
            {savedCandidateCount} saved for this candidate
          </span>
        </div>
      )}

      {/* Storage Error Banner */}
      {storageErrorNotice && (
        <div className="compare-storage-error-banner" role="alert">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertCircle size={13} color="#E06C75" />
            <span>Storage full or blocked. Download JSON now to keep your records.</span>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => downloadComparisonsJson(analysis.id)}
            style={{ height: '24px', fontSize: '0.7rem', padding: '0 8px', marginTop: '6px' }}
          >
            <Download size={11} /> Download JSON now
          </button>
        </div>
      )}

      {/* Save comparison button */}
      <button
        type="button"
        className="btn-primary"
        disabled={!canSave || isSaving}
        onClick={handleSaveComparison}
        style={{
          width: '100%',
          height: '32px',
          fontSize: '0.78rem',
          gap: '6px',
          opacity: canSave ? 1 : 0.5,
          cursor: canSave ? 'pointer' : 'not-allowed'
        }}
        title={canSave ? 'Save comparison record to browser storage' : 'Waiting for both predictions to load'}
      >
        <Save size={13} />
        <span>{isSaving ? 'Saving...' : 'Save comparison'}</span>
      </button>

      {/* Open Saved Comparisons Drawer Button */}
      {onOpenSavedDrawer && (
        <button
          type="button"
          className="btn-secondary compare-view-drawer-btn"
          onClick={onOpenSavedDrawer}
          style={{ width: '100%', height: '28px', fontSize: '0.74rem', gap: '5px' }}
          title="Open saved comparisons drawer"
        >
          <Layers size={12} />
          <span>View saved comparisons ({totalRunSavedCount})</span>
        </button>
      )}
    </div>
  );
}
