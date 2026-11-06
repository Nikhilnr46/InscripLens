/**
 * RedrawOverlay: Interactive SVG overlay for the candidate redrawing tool.
 *
 * Renders the original candidate bounding box as a dashed neutral outline,
 * and the active redrawn rectangle as a solid accent outline with 8 resize handles.
 *
 * Handles pointer events (mouse/touch/pen) for moving and resizing with
 * full boundary clamping and minimum 8x8 px enforcement.
 */

import React, { useRef, useState, useCallback } from 'react';
import { normalizeBbox } from './coordinates';

export default function RedrawOverlay({
  originalBbox,
  redrawnBbox,
  onChange,
  imageBounds,
  scale = 1
}) {
  const [dragState, setDragState] = useState(null); // { mode: 'move'|'resize', handle?: string, startClientX, startClientY, startBbox }

  const origX1 = originalBbox[0];
  const origY1 = originalBbox[1];
  const origW = Math.max(1, originalBbox[2] - originalBbox[0]);
  const origH = Math.max(1, originalBbox[3] - originalBbox[1]);

  const currX1 = redrawnBbox[0];
  const currY1 = redrawnBbox[1];
  const currX2 = redrawnBbox[2];
  const currY2 = redrawnBbox[3];
  const currW = Math.max(1, currX2 - currX1);
  const currH = Math.max(1, currY2 - currY1);

  // Scaled dimensions for handles and stroke widths
  const handleRadius = Math.max(3.5, 5 / scale);
  const touchRadius = Math.max(10, 14 / scale);
  const strokeW = Math.max(1.8, 2.5 / scale);
  const dashStrokeW = Math.max(1.2, 1.8 / scale);

  // 8 Handle positions in image coordinate space
  const handles = [
    { id: 'nw', x: currX1, y: currY1, cursor: 'nwse-resize' },
    { id: 'n', x: currX1 + currW / 2, y: currY1, cursor: 'ns-resize' },
    { id: 'ne', x: currX2, y: currY1, cursor: 'nesw-resize' },
    { id: 'e', x: currX2, y: currY1 + currH / 2, cursor: 'ew-resize' },
    { id: 'se', x: currX2, y: currY2, cursor: 'nwse-resize' },
    { id: 's', x: currX1 + currW / 2, y: currY2, cursor: 'ns-resize' },
    { id: 'sw', x: currX1, y: currY2, cursor: 'nesw-resize' },
    { id: 'w', x: currX1, y: currY1 + currH / 2, cursor: 'ew-resize' }
  ];

  // Initiate box move
  const handleMoveDown = (e) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}

    setDragState({
      mode: 'move',
      startClientX: e.clientX,
      startClientY: e.clientY,
      startBbox: [...redrawnBbox]
    });
  };

  // Initiate handle resize
  const handleResizeDown = (e, handleId) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {}

    setDragState({
      mode: 'resize',
      handle: handleId,
      startClientX: e.clientX,
      startClientY: e.clientY,
      startBbox: [...redrawnBbox]
    });
  };

  const handlePointerMove = (e) => {
    if (!dragState) return;
    e.stopPropagation();

    const dx = (e.clientX - dragState.startClientX) / scale;
    const dy = (e.clientY - dragState.startClientY) / scale;
    const snap = dragState.startBbox;

    if (dragState.mode === 'move') {
      const boxW = snap[2] - snap[0];
      const boxH = snap[3] - snap[1];

      let newX1 = Math.round(snap[0] + dx);
      let newY1 = Math.round(snap[1] + dy);

      // Clamp within image boundary
      newX1 = Math.max(0, Math.min(imageBounds.width - boxW, newX1));
      newY1 = Math.max(0, Math.min(imageBounds.height - boxH, newY1));

      const newBbox = [newX1, newY1, newX1 + boxW, newY1 + boxH];
      onChange(newBbox);
      return;
    }

    if (dragState.mode === 'resize' && dragState.handle) {
      let [x1, y1, x2, y2] = snap;
      const h = dragState.handle;

      if (h.includes('w')) x1 = Math.round(snap[0] + dx);
      if (h.includes('e')) x2 = Math.round(snap[2] + dx);
      if (h.includes('n')) y1 = Math.round(snap[1] + dy);
      if (h.includes('s')) y2 = Math.round(snap[3] + dy);

      const normalized = normalizeBbox([x1, y1, x2, y2], imageBounds, 8);
      onChange(normalized);
    }
  };

  const handlePointerUp = (e) => {
    if (!dragState) return;
    e.stopPropagation();
    try {
      e.currentTarget.releasePointerCapture(e.pointerId);
    } catch {}
    setDragState(null);
  };

  // Badge positioning: place slightly above box, or below if near top edge
  const badgeY = currY1 > 32 / scale ? currY1 - (12 / scale) : currY2 + (16 / scale);
  const badgeX = currX1 + currW / 2;

  return (
    <g
      className="redraw-interactive-layer"
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      style={{ pointerEvents: 'all' }}
    >
      {/* 1. Original Candidate Box (dashed neutral outline) */}
      <rect
        x={origX1}
        y={origY1}
        width={origW}
        height={origH}
        className="redraw-original-box"
        strokeWidth={dashStrokeW}
      >
        <title>Original candidate boundary</title>
      </rect>

      {/* 2. Active Redrawn Rectangle (solid sandstone accent) */}
      <rect
        x={currX1}
        y={currY1}
        width={currW}
        height={currH}
        className="redraw-active-box"
        strokeWidth={strokeW}
        onPointerDown={handleMoveDown}
        title="Drag inside to move redrawn box"
      />

      {/* 3. Live Size Badge */}
      <g className="redraw-dim-group" style={{ pointerEvents: 'none' }}>
        <rect
          x={badgeX - (36 / scale)}
          y={badgeY - (9 / scale)}
          width={72 / scale}
          height={18 / scale}
          rx={4 / scale}
          fill="rgba(18, 18, 20, 0.88)"
          stroke="var(--border-subtle, #28282F)"
          strokeWidth={1 / scale}
        />
        <text
          x={badgeX}
          y={badgeY}
          className="redraw-dim-badge"
          style={{ fontSize: `${Math.max(9, 11 / scale)}px` }}
        >
          {currW} &times; {currH} px
        </text>
      </g>

      {/* 4. 8 Resize Handles */}
      {handles.map((h) => (
        <g
          key={h.id}
          className="redraw-handle-group"
          style={{ cursor: h.cursor }}
          onPointerDown={(e) => handleResizeDown(e, h.id)}
        >
          {/* Expanded transparent touch/hit area */}
          <circle
            cx={h.x}
            cy={h.y}
            r={touchRadius}
            className="redraw-handle-touch"
          />
          {/* Crisp visible handle point */}
          <circle
            cx={h.x}
            cy={h.y}
            r={handleRadius}
            className="redraw-handle-dot"
            strokeWidth={Math.max(1.5, 2 / scale)}
          />
        </g>
      ))}
    </g>
  );
}
