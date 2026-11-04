import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';
import Reveal from './Reveal';

const COMPLETE_THRESHOLD_RATIO = 0.85;
const COMPLETE_ANIMATION_MS = 300;

export default function SlideToEnter({ onComplete }) {
  const trackRef = useRef(null);
  const handleRef = useRef(null);

  const [offsetPx, setOffsetPx] = useState(0);
  const [maxOffset, setMaxOffset] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [completing, setCompleting] = useState(false);
  const dragStartXRef = useRef(0);

  function triggerComplete() {
    setCompleting(true);
    setTimeout(() => {
      onComplete?.();
    }, COMPLETE_ANIMATION_MS);
  }

  useEffect(() => {
    const track = trackRef.current;
    const handle = handleRef.current;
    if (!track || !handle) return;

    function measure() {
      setMaxOffset(Math.max(0, track.clientWidth - handle.clientWidth - 8));
    }
    measure();

    const observer = new ResizeObserver(measure);
    observer.observe(track);
    return () => observer.disconnect();
  }, []);

  function handlePointerDown(event) {
    dragStartXRef.current = event.clientX - offsetPx;
    setDragging(true);
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function handlePointerMove(event) {
    if (!dragging) return;
    const delta = event.clientX - dragStartXRef.current;
    setOffsetPx(Math.max(0, Math.min(delta, maxOffset)));
  }

  function handlePointerUp() {
    if (!dragging) return;
    setDragging(false);
    const reachedEnd = maxOffset > 0 && offsetPx >= maxOffset * COMPLETE_THRESHOLD_RATIO;
    if (reachedEnd) {
      setOffsetPx(maxOffset);
      triggerComplete();
    } else {
      setOffsetPx(0);
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ' || event.key === 'ArrowRight') {
      event.preventDefault();
      setOffsetPx(maxOffset);
      triggerComplete();
    }
  }

  const fillPercent = maxOffset > 0 ? (offsetPx / maxOffset) * 100 : 0;

  return (
    <div className="slide-to-enter-container">
      <Reveal initialShown variant="up" delay={0} className="slide-to-enter" role="group" aria-label="Slide to enter workspace">
        <div className="slide-to-enter-track" ref={trackRef}>
          {/* Progress fill bar */}
          <div
            className="slide-to-enter-fill"
            style={{ width: `${fillPercent}%` }}
          />

          {/* Shimmer label */}
          <div className="slide-to-enter-label-area">
            <span className="slide-to-enter-label">
              Slide to enter Studio <span className="slide-arrow">&rarr;</span>
            </span>
          </div>

          {/* Draggable knob */}
          <button
            type="button"
            ref={handleRef}
            className={`slide-to-enter-handle ${dragging ? 'dragging' : ''} ${completing ? 'completing' : ''}`}
            style={{ transform: `translateX(${offsetPx}px)` }}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            onKeyDown={handleKeyDown}
            aria-label="Slide to enter Studio"
          >
            <ArrowRight size={18} />
          </button>
        </div>
      </Reveal>
    </div>
  );
}

