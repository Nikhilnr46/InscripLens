/**
 * RedrawOverlay: Interactive SVG overlay for the candidate redrawing tool.
 *
 * Renders the original candidate bounding box as a dashed neutral outline,
 * and the active redrawn rectangle as a solid accent outline with 8 resize handles.
 *
 * Handles pointer events (mouse/touch/pen) for moving and resizing with
 * full boundary clamping and minimum 8x8 px enforcement.
 */

import React, { useRef, useState, useEffect } from 'react';

export default function RedrawOverlay({
  originalBbox,
  redrawnBbox,
  onChange,
  imageBounds,
  scale = 1
}) {
  const [activeHandle, setActiveHandle] = useState(null);
  const [isMoving, setIsMoving] = useState(false);
  const dragRef = useRef(null);

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

  // Initiate drag operation (move or resize) with global window listeners
  const startDrag = (e, mode, handleId = null) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    e.stopPropagation();
    e.preventDefault();

    const startClientX = e.clientX;
    const startClientY = e.clientY;
    const startBbox = [...redrawnBbox];

    dragRef.current = {
      mode,
      handleId,
      startClientX,
      startClientY,
      startBbox
    };

    if (mode === 'move') {
      setIsMoving(true);
    } else {
      setActiveHandle(handleId);
    }

    const onPointerMove = (moveEvt) => {
      if (!dragRef.current) return;
      moveEvt.preventDefault();

      const { mode: currentMode, handleId: currentHandle, startClientX: startX, startClientY: startY, startBbox: snap } = dragRef.current;
      const dx = (moveEvt.clientX - startX) / scale;
      const dy = (moveEvt.clientY - startY) / scale;

      if (currentMode === 'move') {
        const boxW = snap[2] - snap[0];
        const boxH = snap[3] - snap[1];

        let newX1 = Math.round(snap[0] + dx);
        let newY1 = Math.round(snap[1] + dy);

        // Clamp within image boundary
        newX1 = Math.max(0, Math.min(imageBounds.width - boxW, newX1));
        newY1 = Math.max(0, Math.min(imageBounds.height - boxH, newY1));

        onChange([newX1, newY1, newX1 + boxW, newY1 + boxH]);
      } else if (currentMode === 'resize' && currentHandle) {
        let [x1, y1, x2, y2] = snap;
        const minSize = 8;

        if (currentHandle.includes('w')) {
          x1 = Math.max(0, Math.min(snap[2] - minSize, Math.round(snap[0] + dx)));
        }
        if (currentHandle.includes('e')) {
          x2 = Math.min(imageBounds.width, Math.max(snap[0] + minSize, Math.round(snap[2] + dx)));
        }
        if (currentHandle.includes('n')) {
          y1 = Math.max(0, Math.min(snap[3] - minSize, Math.round(snap[1] + dy)));
        }
        if (currentHandle.includes('s')) {
          y2 = Math.min(imageBounds.height, Math.max(snap[1] + minSize, Math.round(snap[3] + dy)));
        }

        onChange([x1, y1, x2, y2]);
      }
    };

    const onPointerUp = () => {
      dragRef.current = null;
      setIsMoving(false);
      setActiveHandle(null);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
      window.removeEventListener('pointercancel', onPointerUp);
    };

    window.addEventListener('pointermove', onPointerMove, { passive: false });
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      dragRef.current = null;
    };
  }, []);

  // Badge positioning: place slightly above box, or below if near top edge
  const badgeY = currY1 > 32 / scale ? currY1 - (12 / scale) : currY2 + (16 / scale);
  const badgeX = currX1 + currW / 2;

  return (
    <g
      className="redraw-interactive-layer"
      style={{ pointerEvents: 'none', userSelect: 'none' }}
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
        className={`redraw-active-box ${isMoving ? 'moving' : ''}`}
        strokeWidth={strokeW}
        onPointerDown={(e) => startDrag(e, 'move')}
        onMouseDown={(e) => { e.stopPropagation(); }}
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
      {handles.map((h) => {
        const isActive = activeHandle === h.id;
        return (
          <g
            key={h.id}
            className={`redraw-handle-group ${isActive ? 'active' : ''}`}
            style={{ cursor: h.cursor }}
            onPointerDown={(e) => startDrag(e, 'resize', h.id)}
            onMouseDown={(e) => { e.stopPropagation(); }}
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
              r={isActive ? handleRadius * 1.2 : handleRadius}
              className="redraw-handle-dot"
              strokeWidth={Math.max(1.5, 2 / scale)}
            />
          </g>
        );
      })}
    </g>
  );
}
