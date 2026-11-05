import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  AlertTriangle,
  AlertCircle,
  Crop,
  Check,
  ArrowRight,
  Hand,
  Sparkles
} from 'lucide-react';

const MIN_SIZE_ORIG_PX = 64;
const WARN_THRESHOLD_PX = 300;
const MAX_EXPORT_LONG_SIDE = 3200;

export default function RegionSelector({
  file,
  initialSelection = null,
  onConfirmCrop,
  onUseWholeImage,
  onCancel
}) {
  const [loading, setLoading] = useState(true);
  const [decodeError, setDecodeError] = useState(null);
  const [exporting, setExporting] = useState(false);

  // Original image dimensions
  const [origDimensions, setOrigDimensions] = useState({ width: 0, height: 0 });

  // Selection stored in ORIGINAL image coordinates: { x, y, width, height }
  const [selection, setSelection] = useState(null);

  // Viewport zoom & pan
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isSpacePressed, setIsSpacePressed] = useState(false);

  // Drag interaction states: 'none' | 'draw' | 'move' | 'resize'
  const [dragMode, setDragMode] = useState('none');
  const [activeHandle, setActiveHandle] = useState(null);

  // Refs
  const viewportRef = useRef(null);
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const fullBitmapRef = useRef(null);
  const previewUrlRef = useRef(null);
  const dragStartRef = useRef({ x: 0, y: 0, origX: 0, origY: 0, selSnapshot: null });
  const panStartRef = useRef(null);

  // Cleanup helper
  const cleanupResources = useCallback(() => {
    if (fullBitmapRef.current) {
      try {
        fullBitmapRef.current.close();
      } catch {}
      fullBitmapRef.current = null;
    }
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupResources();
    };
  }, [cleanupResources]);

  // Decode file on mount with createImageBitmap respecting EXIF orientation
  useEffect(() => {
    let active = true;

    async function loadAndDecode() {
      setLoading(true);
      setDecodeError(null);

      try {
        let bitmap = null;
        if (typeof window.createImageBitmap === 'function') {
          try {
            bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
          } catch (e) {
            // Fallback without options if imageOrientation unsupported
            bitmap = await createImageBitmap(file);
          }
        }

        // If createImageBitmap failed or unsupported, fallback to Image element
        if (!bitmap) {
          const url = URL.createObjectURL(file);
          previewUrlRef.current = url;
          const img = new Image();
          await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = () => reject(new Error('Failed to load image element'));
            img.src = url;
          });
          bitmap = await createImageBitmap(img);
        }

        if (!active) {
          bitmap.close();
          return;
        }

        fullBitmapRef.current = bitmap;
        const origW = bitmap.width;
        const origH = bitmap.height;
        setOrigDimensions({ width: origW, height: origH });

        // Draw downscaled preview on canvas for smooth viewing
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.width = origW;
          canvas.height = origH;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(bitmap, 0, 0);
          }
        }

        // Restore initial selection if provided, otherwise pre-select centered 80% rectangle
        if (initialSelection && initialSelection.width && initialSelection.height && !initialSelection.isWholeImage) {
          const selW = Math.max(MIN_SIZE_ORIG_PX, Math.min(origW, initialSelection.width));
          const selH = Math.max(MIN_SIZE_ORIG_PX, Math.min(origH, initialSelection.height));
          const selX = Math.max(0, Math.min(origW - selW, initialSelection.x));
          const selY = Math.max(0, Math.min(origH - selH, initialSelection.y));

          setSelection({
            x: selX,
            y: selY,
            width: selW,
            height: selH
          });
        } else {
          const initW = Math.round(origW * 0.8);
          const initH = Math.round(origH * 0.8);
          const initX = Math.round((origW - initW) / 2);
          const initY = Math.round((origH - initH) / 2);

          setSelection({
            x: initX,
            y: initY,
            width: Math.max(MIN_SIZE_ORIG_PX, initW),
            height: Math.max(MIN_SIZE_ORIG_PX, initH)
          });
        }

        setLoading(false);

        // Fit preview into viewport once loaded
        requestAnimationFrame(() => {
          fitToViewport(origW, origH);
        });
      } catch (err) {
        if (!active) return;
        setDecodeError(err.message || 'Image decoding failed.');
        setLoading(false);
      }
    }

    loadAndDecode();

    return () => {
      active = false;
    };
  }, [file]);

  // Fit image to available viewport
  const fitToViewport = useCallback((wOverride, hOverride) => {
    const vp = viewportRef.current;
    const imgW = wOverride || origDimensions.width;
    const imgH = hOverride || origDimensions.height;
    if (!vp || !imgW || !imgH) return;

    const vpRect = vp.getBoundingClientRect();
    const pad = 40;
    const availW = Math.max(80, vpRect.width - pad);
    const availH = Math.max(80, vpRect.height - pad);

    const fitScale = Math.min(availW / imgW, availH / imgH);
    const targetScale = Math.max(0.05, Math.min(3.0, fitScale));

    const panX = (vpRect.width - imgW * targetScale) / 2;
    const panY = (vpRect.height - imgH * targetScale) / 2;

    setScale(targetScale);
    setPan({ x: panX, y: panY });
  }, [origDimensions]);

  // Zoom controls
  const handleZoom = useCallback((factor, clientCenterX, clientCenterY) => {
    const vp = viewportRef.current;
    if (!vp || !origDimensions.width) return;

    const vpRect = vp.getBoundingClientRect();
    const cx = clientCenterX !== undefined ? clientCenterX - vpRect.left : vpRect.width / 2;
    const cy = clientCenterY !== undefined ? clientCenterY - vpRect.top : vpRect.height / 2;

    setScale((prevScale) => {
      const nextScale = Math.max(0.1, Math.min(5.0, prevScale * factor));
      setPan((prevPan) => {
        const nextX = cx - (cx - prevPan.x) * (nextScale / prevScale);
        const nextY = cy - (cy - prevPan.y) * (nextScale / prevScale);
        return { x: nextX, y: nextY };
      });
      return nextScale;
    });
  }, [origDimensions]);

  const zoomIn = () => handleZoom(1.25);
  const zoomOut = () => handleZoom(1 / 1.25);
  const zoomTo100 = () => {
    const vp = viewportRef.current;
    if (!vp || !origDimensions.width) return;
    const vpRect = vp.getBoundingClientRect();
    setScale(1.0);
    setPan({
      x: (vpRect.width - origDimensions.width) / 2,
      y: (vpRect.height - origDimensions.height) / 2
    });
  };

  // Wheel zoom centered on cursor
  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return;

    const onWheel = (e) => {
      e.preventDefault();
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      handleZoom(factor, e.clientX, e.clientY);
    };

    vp.addEventListener('wheel', onWheel, { passive: false });
    return () => vp.removeEventListener('wheel', onWheel);
  }, [handleZoom]);

  // Space key tracker for panning
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.code === 'Space' && !e.repeat && e.target.tagName !== 'INPUT') {
        setIsSpacePressed(true);
      }
    };
    const onKeyUp = (e) => {
      if (e.code === 'Space') {
        setIsSpacePressed(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, []);

  // Convert client viewport coordinates to original image coordinates
  const clientToOrig = useCallback((clientX, clientY) => {
    const vp = viewportRef.current;
    if (!vp) return { x: 0, y: 0 };
    const vpRect = vp.getBoundingClientRect();
    const stageX = clientX - vpRect.left - pan.x;
    const stageY = clientY - vpRect.top - pan.y;
    const origX = Math.round(stageX / scale);
    const origY = Math.round(stageY / scale);
    return {
      x: Math.max(0, Math.min(origDimensions.width, origX)),
      y: Math.max(0, Math.min(origDimensions.height, origY))
    };
  }, [pan, scale, origDimensions]);

  // Pointer event handlers for drawing, moving, resizing, and panning
  const handlePointerDown = (e) => {
    // Middle mouse button OR Space pressed: Pan
    if (e.button === 1 || (e.button === 0 && isSpacePressed)) {
      e.preventDefault();
      panStartRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        panX: pan.x,
        panY: pan.y
      };
      setDragMode('pan');
      e.currentTarget.setPointerCapture(e.pointerId);
      return;
    }

    if (e.button !== 0) return; // Only primary button
    e.preventDefault();

    const coords = clientToOrig(e.clientX, e.clientY);
    const handle = e.target.dataset?.handle;

    if (handle && selection) {
      // Resize handle clicked
      setDragMode('resize');
      setActiveHandle(handle);
      dragStartRef.current = {
        startX: coords.x,
        startY: coords.y,
        selSnapshot: { ...selection }
      };
      e.currentTarget.setPointerCapture(e.pointerId);
      return;
    }

    // Check if clicked inside selection box
    if (
      selection &&
      coords.x >= selection.x &&
      coords.x <= selection.x + selection.width &&
      coords.y >= selection.y &&
      coords.y <= selection.y + selection.height
    ) {
      setDragMode('move');
      dragStartRef.current = {
        startX: coords.x,
        startY: coords.y,
        selSnapshot: { ...selection }
      };
      e.currentTarget.setPointerCapture(e.pointerId);
      return;
    }

    // Clicked empty space: Draw new rectangle
    setDragMode('draw');
    dragStartRef.current = {
      startX: coords.x,
      startY: coords.y,
      selSnapshot: null
    };
    setSelection({
      x: coords.x,
      y: coords.y,
      width: 0,
      height: 0
    });
    e.currentTarget.setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e) => {
    if (dragMode === 'none') return;

    if (dragMode === 'pan' && panStartRef.current) {
      const dx = e.clientX - panStartRef.current.startX;
      const dy = e.clientY - panStartRef.current.startY;
      setPan({
        x: panStartRef.current.panX + dx,
        y: panStartRef.current.panY + dy
      });
      return;
    }

    const coords = clientToOrig(e.clientX, e.clientY);
    const imgW = origDimensions.width;
    const imgH = origDimensions.height;

    if (dragMode === 'draw') {
      const startX = dragStartRef.current.startX;
      const startY = dragStartRef.current.startY;
      const x1 = Math.min(startX, coords.x);
      const y1 = Math.min(startY, coords.y);
      const x2 = Math.max(startX, coords.x);
      const y2 = Math.max(startY, coords.y);

      setSelection({
        x: x1,
        y: y1,
        width: x2 - x1,
        height: y2 - y1
      });
      return;
    }

    if (dragMode === 'move' && dragStartRef.current.selSnapshot) {
      const snap = dragStartRef.current.selSnapshot;
      const dx = coords.x - dragStartRef.current.startX;
      const dy = coords.y - dragStartRef.current.startY;

      let nextX = snap.x + dx;
      let nextY = snap.y + dy;

      nextX = Math.max(0, Math.min(imgW - snap.width, nextX));
      nextY = Math.max(0, Math.min(imgH - snap.height, nextY));

      setSelection({
        ...snap,
        x: nextX,
        y: nextY
      });
      return;
    }

    if (dragMode === 'resize' && activeHandle && dragStartRef.current.selSnapshot) {
      const snap = dragStartRef.current.selSnapshot;
      const dx = coords.x - dragStartRef.current.startX;
      const dy = coords.y - dragStartRef.current.startY;

      let { x, y, width, height } = snap;

      if (activeHandle.includes('w')) {
        const newX = Math.min(snap.x + dx, snap.x + snap.width - MIN_SIZE_ORIG_PX);
        const clampedX = Math.max(0, newX);
        width = snap.width + (snap.x - clampedX);
        x = clampedX;
      }
      if (activeHandle.includes('e')) {
        const newW = snap.width + dx;
        width = Math.max(MIN_SIZE_ORIG_PX, Math.min(imgW - snap.x, newW));
      }
      if (activeHandle.includes('n')) {
        const newY = Math.min(snap.y + dy, snap.y + snap.height - MIN_SIZE_ORIG_PX);
        const clampedY = Math.max(0, newY);
        height = snap.height + (snap.y - clampedY);
        y = clampedY;
      }
      if (activeHandle.includes('s')) {
        const newH = snap.height + dy;
        height = Math.max(MIN_SIZE_ORIG_PX, Math.min(imgH - snap.y, newH));
      }

      setSelection({ x, y, width, height });
    }
  };

  const handlePointerUp = (e) => {
    if (dragMode === 'draw' && selection) {
      // Enforce minimum size on newly drawn box
      if (selection.width < MIN_SIZE_ORIG_PX || selection.height < MIN_SIZE_ORIG_PX) {
        // Reset to default 80% if drawn box was tiny accidental click
        resetToDefault();
      }
    }
    setDragMode('none');
    setActiveHandle(null);
    panStartRef.current = null;
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {}
  };

  // Keyboard navigation on selection
  const handleKeyDown = (e) => {
    if (!selection) return;

    if (e.key === 'Escape') {
      e.preventDefault();
      resetToDefault();
      return;
    }

    const imgW = origDimensions.width;
    const imgH = origDimensions.height;
    const step = Math.max(1, Math.round(imgW * 0.01)); // 1% step

    let { x, y, width, height } = selection;

    if (e.shiftKey) {
      // Shift + Arrows: Resize
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        width = Math.min(imgW - x, width + step);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        width = Math.max(MIN_SIZE_ORIG_PX, width - step);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        height = Math.min(imgH - y, height + step);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        height = Math.max(MIN_SIZE_ORIG_PX, height - step);
      }
    } else {
      // Arrows: Move
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        x = Math.min(imgW - width, x + step);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        x = Math.max(0, x - step);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        y = Math.min(imgH - height, y + step);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        y = Math.max(0, y - step);
      }
    }

    setSelection({ x, y, width, height });
  };

  // Reset to 80% centered default
  const resetToDefault = () => {
    const origW = origDimensions.width;
    const origH = origDimensions.height;
    if (!origW || !origH) return;

    const initW = Math.round(origW * 0.8);
    const initH = Math.round(origH * 0.8);
    const initX = Math.round((origW - initW) / 2);
    const initY = Math.round((origH - initH) / 2);

    setSelection({
      x: initX,
      y: initY,
      width: Math.max(MIN_SIZE_ORIG_PX, initW),
      height: Math.max(MIN_SIZE_ORIG_PX, initH)
    });
  };

  // Select 100% whole image
  const selectWholeImage = () => {
    onUseWholeImage?.(file);
  };

  // Export cropped PNG and dispatch to Studio
  const handleConfirm = async () => {
    if (!selection || !fullBitmapRef.current || exporting) return;

    const origW = origDimensions.width;
    const origH = origDimensions.height;
    const selArea = selection.width * selection.height;
    const totalArea = origW * origH;
    const coverage = totalArea > 0 ? selArea / totalArea : 1;

    // If 99% or more coverage, pass original File unchanged with zero re-encoding
    if (coverage >= 0.99) {
      onConfirmCrop({
        file,
        originalFile: file,
        selection: {
          x: 0,
          y: 0,
          width: origW,
          height: origH,
          imageWidth: origW,
          imageHeight: origH,
          isWholeImage: true
        },
        originalSize: { width: origW, height: origH }
      });
      return;
    }

    setExporting(true);

    try {
      // Cap long side at 3200 px to respect memory and backend bounds
      const maxDim = Math.max(selection.width, selection.height);
      const capScale = maxDim > MAX_EXPORT_LONG_SIDE ? MAX_EXPORT_LONG_SIDE / maxDim : 1.0;
      const targetW = Math.max(1, Math.round(selection.width * capScale));
      const targetH = Math.max(1, Math.round(selection.height * capScale));

      const offscreen = document.createElement('canvas');
      offscreen.width = targetW;
      offscreen.height = targetH;
      const ctx = offscreen.getContext('2d');
      if (!ctx) throw new Error('Could not obtain offscreen canvas context');

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      ctx.drawImage(
        fullBitmapRef.current,
        selection.x,
        selection.y,
        selection.width,
        selection.height,
        0,
        0,
        targetW,
        targetH
      );

      const blob = await new Promise((resolve, reject) => {
        offscreen.toBlob((b) => {
          if (b) resolve(b);
          else reject(new Error('Failed to generate cropped PNG blob'));
        }, 'image/png');
      });

      const croppedFile = new File([blob], 'selected-area.png', { type: 'image/png' });

      onConfirmCrop({
        file: croppedFile,
        originalFile: file,
        selection: {
          x: selection.x,
          y: selection.y,
          width: selection.width,
          height: selection.height,
          imageWidth: origW,
          imageHeight: origH,
          isWholeImage: false
        },
        originalSize: { width: origW, height: origH }
      });
    } catch (err) {
      console.error('Cropping error:', err);
      // Fallback: use whole image if crop failed
      onConfirmCrop({
        file,
        originalFile: file,
        selection: {
          x: 0,
          y: 0,
          width: origW,
          height: origH,
          imageWidth: origW,
          imageHeight: origH,
          isWholeImage: true
        },
        originalSize: { width: origW, height: origH }
      });
    } finally {
      setExporting(false);
    }
  };

  // Live metrics calculations
  const isSmallSelection =
    selection &&
    (selection.width < WARN_THRESHOLD_PX || selection.height < WARN_THRESHOLD_PX);

  const isValidSelection =
    selection &&
    selection.width >= MIN_SIZE_ORIG_PX &&
    selection.height >= MIN_SIZE_ORIG_PX;

  const coveragePercent =
    selection && origDimensions.width && origDimensions.height
      ? Math.round(
          ((selection.width * selection.height) /
            (origDimensions.width * origDimensions.height)) *
            100
        )
      : 100;

  // Handle definitions for 8 resize points
  const handles = [
    { id: 'nw', x: selection?.x, y: selection?.y, cursor: 'nw-resize' },
    { id: 'n', x: (selection?.x || 0) + (selection?.width || 0) / 2, y: selection?.y, cursor: 'n-resize' },
    { id: 'ne', x: (selection?.x || 0) + (selection?.width || 0), y: selection?.y, cursor: 'ne-resize' },
    { id: 'e', x: (selection?.x || 0) + (selection?.width || 0), y: (selection?.y || 0) + (selection?.height || 0) / 2, cursor: 'e-resize' },
    { id: 'se', x: (selection?.x || 0) + (selection?.width || 0), y: (selection?.y || 0) + (selection?.height || 0), cursor: 'se-resize' },
    { id: 's', x: (selection?.x || 0) + (selection?.width || 0) / 2, y: (selection?.y || 0) + (selection?.height || 0), cursor: 's-resize' },
    { id: 'sw', x: selection?.x, y: (selection?.y || 0) + (selection?.height || 0), cursor: 'sw-resize' },
    { id: 'w', x: selection?.x, y: (selection?.y || 0) + (selection?.height || 0) / 2, cursor: 'w-resize' }
  ];

  if (decodeError) {
    return (
      <div className="region-selector-error-card">
        <div className="error-icon-box">
          <AlertCircle size={32} className="text-red" />
        </div>
        <h2 className="error-heading">Image Decoding Notice</h2>
        <p className="error-message">
          The browser encountered an issue reading the image orientation ({decodeError}).
          You can continue directly with the original photograph.
        </p>
        <div className="error-actions">
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Choose Another Image
          </button>
          <button
            type="button"
            className="btn-primary btn-magnetic"
            onClick={() => onUseWholeImage(file)}
          >
            Continue with the Whole Image &rarr;
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="region-selector-root"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="region"
      aria-label="Select stone inscription region"
    >
      {/* Top Readout & Toolbar */}
      <div className="region-selector-topbar">
        <div className="region-dimensions-group">
          <div className="dimension-pill selected-pill">
            <Crop size={14} className="text-sandstone" />
            <span className="pill-label">Selected Area:</span>
            <span className="pill-value">
              {selection ? `${selection.width} × ${selection.height} px` : '--'}
            </span>
            <span className="pill-badge">{coveragePercent}%</span>
          </div>

          <div className="dimension-pill original-pill">
            <span className="pill-label">Original Stone:</span>
            <span className="pill-value">
              {origDimensions.width} × {origDimensions.height} px
            </span>
          </div>
        </div>

        {/* Viewport Zoom & Fit Controls */}
        <div className="region-zoom-controls">
          <button
            type="button"
            className="zoom-btn"
            onClick={() => fitToViewport()}
            title="Fit image to view"
            aria-label="Fit to view"
          >
            <Maximize2 size={13} />
            <span className="btn-label-text">Fit</span>
          </button>
          <button
            type="button"
            className="zoom-btn"
            onClick={zoomTo100}
            title="Actual size (100%)"
            aria-label="Zoom 100 percent"
          >
            100%
          </button>
          <button
            type="button"
            className="zoom-btn"
            onClick={zoomOut}
            title="Zoom out"
            aria-label="Zoom out"
          >
            <ZoomOut size={13} />
          </button>
          <span className="zoom-level-text">{Math.round(scale * 100)}%</span>
          <button
            type="button"
            className="zoom-btn"
            onClick={zoomIn}
            title="Zoom in"
            aria-label="Zoom in"
          >
            <ZoomIn size={13} />
          </button>
        </div>
      </div>

      {/* Small Area Warning Banner */}
      {isSmallSelection && (
        <div className="region-warning-banner" role="alert">
          <AlertTriangle size={14} className="warning-icon" />
          <span>
            Selected area is smaller than 300 × 300 px. Small areas may give weaker enhancement and character recognition results.
          </span>
        </div>
      )}

      {/* Main Interactive Stage Viewport */}
      <div
        className={`region-viewport ${isSpacePressed ? 'pan-cursor' : ''}`}
        ref={viewportRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        style={{ touchAction: 'none' }}
      >
        {loading && (
          <div className="region-loader-overlay">
            <Sparkles size={24} className="text-sandstone animate-spin" />
            <span>Decoding inscription image...</span>
          </div>
        )}

        {/* Scaled & Panned Content Stage */}
        <div
          className="region-stage"
          ref={containerRef}
          style={{
            width: origDimensions.width,
            height: origDimensions.height,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
            transformOrigin: '0 0'
          }}
        >
          {/* Base Image Canvas */}
          <canvas ref={canvasRef} className="region-base-canvas" />

          {/* SVG Mask and Interactive Selection Box */}
          {selection && origDimensions.width > 0 && (
            <svg
              className="region-svg-overlay"
              width={origDimensions.width}
              height={origDimensions.height}
              viewBox={`0 0 ${origDimensions.width} ${origDimensions.height}`}
            >
              <defs>
                <mask id="scrim-mask">
                  {/* White background: fully visible mask */}
                  <rect
                    x="0"
                    y="0"
                    width={origDimensions.width}
                    height={origDimensions.height}
                    fill="white"
                  />
                  {/* Black cutout: reveals the selected stone area */}
                  <rect
                    x={selection.x}
                    y={selection.y}
                    width={selection.width}
                    height={selection.height}
                    fill="black"
                  />
                </mask>
              </defs>

              {/* Outside Dimmed Area */}
              <rect
                x="0"
                y="0"
                width={origDimensions.width}
                height={origDimensions.height}
                fill="rgba(0, 0, 0, 0.58)"
                mask="url(#scrim-mask)"
                style={{ pointerEvents: 'none' }}
              />

              {/* Selection Border */}
              <rect
                x={selection.x}
                y={selection.y}
                width={selection.width}
                height={selection.height}
                fill="none"
                stroke="var(--accent-sandstone)"
                strokeWidth={Math.max(1, Math.round(2 / scale))}
                strokeDasharray={`${Math.round(8 / scale)} ${Math.round(4 / scale)}`}
                className="selection-active-rect"
                style={{ cursor: isSpacePressed ? 'grab' : 'move' }}
              />

              {/* Inner Focus Solid Border */}
              <rect
                x={selection.x}
                y={selection.y}
                width={selection.width}
                height={selection.height}
                fill="rgba(201, 166, 107, 0.04)"
                stroke="rgba(255, 255, 255, 0.5)"
                strokeWidth={Math.max(1, Math.round(1 / scale))}
                style={{ cursor: isSpacePressed ? 'grab' : 'move' }}
              />

              {/* 8 Resize Handles */}
              {handles.map((h) => {
                const handleRadius = Math.max(4, Math.round(6 / scale));
                const hitRadius = Math.max(12, Math.round(16 / scale));
                return (
                  <g key={h.id} className="handle-group">
                    {/* Invisible larger hit target for touch & precision */}
                    <circle
                      cx={h.x}
                      cy={h.y}
                      r={hitRadius}
                      fill="transparent"
                      data-handle={h.id}
                      style={{ cursor: h.cursor }}
                    />
                    {/* Visible crisp handle */}
                    <circle
                      cx={h.x}
                      cy={h.y}
                      r={handleRadius}
                      fill="#FFFFFF"
                      stroke="var(--accent-sandstone)"
                      strokeWidth={Math.max(1.5, Math.round(2 / scale))}
                      data-handle={h.id}
                      style={{ cursor: h.cursor, filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.5))' }}
                    />
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>

      {/* Keyboard & Touch Navigation Hints */}
      <div className="region-hints-strip">
        <span className="hint-item">
          <Hand size={12} /> Drag inside to move &middot; Drag corners to resize
        </span>
        <span className="hint-sep">&middot;</span>
        <span className="hint-item">
          Wheel or pinch to zoom &middot; Space+drag to pan
        </span>
        <span className="hint-sep">&middot;</span>
        <span className="hint-item">
          Arrow keys nudge &middot; Shift+Arrow resize
        </span>
      </div>

      {/* Bottom Action Controls */}
      <div className="region-bottom-actions">
        <div className="actions-left">
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            title="Return to image chooser"
          >
            Change image
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={resetToDefault}
            title="Reset to 80% centered area"
          >
            <RotateCcw size={14} /> Reset selection
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={selectWholeImage}
            title="Scan entire photograph without cropping"
          >
            Use whole image
          </button>
        </div>

        <div className="actions-right">
          <button
            type="button"
            className="btn-primary btn-magnetic"
            disabled={!isValidSelection || exporting}
            onClick={handleConfirm}
          >
            {exporting ? (
              <span>Preparing selected area...</span>
            ) : (
              <>
                <span>Continue to Studio</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
