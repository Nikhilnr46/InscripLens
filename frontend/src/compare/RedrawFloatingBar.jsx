/**
 * RedrawFloatingBar: Floating viewer control panel for Redraw Mode.
 *
 * Provides candidate title pill, Photo/Mask layer toggle (defaulting to Mask),
 * and Reset, Cancel, and Apply actions.
 */

import React from 'react';
import { RotateCcw, X, Check, Eye } from 'lucide-react';

export default function RedrawFloatingBar({
  candidateNumber,
  layer = 'mask',
  onLayerChange,
  onReset,
  onCancel,
  onApply
}) {
  return (
    <div
      className="redraw-floating-bar"
      role="toolbar"
      aria-label="Redraw candidate toolbar"
    >
      {/* Candidate Title */}
      <div className="redraw-bar-title">
        <span>Redrawing</span>
        <span className="pill-accent">#{candidateNumber}</span>
      </div>

      <div className="redraw-bar-divider" />

      {/* Layer Toggle (Mask vs Photo) */}
      <div
        className="redraw-layer-toggle"
        role="group"
        aria-label="Underlying image layer"
        title="The classifier reads the mask"
      >
        <button
          type="button"
          className={`redraw-layer-btn ${layer === 'mask' ? 'active' : ''}`}
          onClick={() => onLayerChange('mask')}
          aria-pressed={layer === 'mask'}
          title="Display binarized stroke mask (The classifier reads the mask)"
        >
          Mask
        </button>
        <button
          type="button"
          className={`redraw-layer-btn ${layer === 'photo' ? 'active' : ''}`}
          onClick={() => onLayerChange('photo')}
          aria-pressed={layer === 'photo'}
          title="Display raw photograph"
        >
          Photo
        </button>
      </div>

      <div className="redraw-bar-divider" />

      {/* Actions */}
      <div className="redraw-bar-actions">
        <button
          type="button"
          className="btn-secondary redraw-bar-btn"
          onClick={onReset}
          title="Reset redrawn rectangle to original candidate boundary"
        >
          <RotateCcw size={12} /> Reset
        </button>
        <button
          type="button"
          className="btn-secondary redraw-bar-btn"
          onClick={onCancel}
          title="Cancel redrawing and restore viewer (Esc)"
        >
          <X size={12} /> Cancel
        </button>
        <button
          type="button"
          className="btn-primary redraw-bar-btn"
          onClick={onApply}
          title="Apply new bounding box and run comparison (Enter)"
        >
          <Check size={12} /> Apply
        </button>
      </div>
    </div>
  );
}
