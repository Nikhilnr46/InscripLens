// Shared rAF-throttled pointer-tracking and scroll-reveal interactions

export function initSiteInteractions(): () => void {
  // Respect prefers-reduced-motion and touch device capability
  const isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isHoverCapable = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  // 1. IntersectionObserver for once-only scroll-reveal
  let observer: IntersectionObserver | null = null;
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-revealed');
            observer?.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
      observer?.observe(el);
    });
  } else {
    document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
      el.classList.add('is-revealed');
    });
  }

  // If touch device or reduced motion, skip pointer-tracking effects
  if (!isHoverCapable || isReducedMotion) {
    return () => {
      observer?.disconnect();
    };
  }

  // 2. Shared rAF-throttled pointer tracking loop
  let activeMagneticEl: HTMLElement | null = null;
  let activeCardEl: HTMLElement | null = null;

  let pointerX = 0;
  let pointerY = 0;
  let rafId: number | null = null;

  let magCurrentX = 0;
  let magCurrentY = 0;
  let magTargetX = 0;
  let magTargetY = 0;

  function updateInteractions() {
    // A. Magnetic button effect (drifts up to 6px toward cursor)
    if (activeMagneticEl) {
      magCurrentX += (magTargetX - magCurrentX) * 0.25;
      magCurrentY += (magTargetY - magCurrentY) * 0.25;
      activeMagneticEl.style.setProperty('--mag-x', `${magCurrentX.toFixed(2)}px`);
      activeMagneticEl.style.setProperty('--mag-y', `${magCurrentY.toFixed(2)}px`);
    }

    // B. Card cursor spotlight & 3D tilt
    if (activeCardEl) {
      const rect = activeCardEl.getBoundingClientRect();
      const relX = pointerX - rect.left;
      const relY = pointerY - rect.top;

      activeCardEl.style.setProperty('--card-mx', `${Math.round(relX)}px`);
      activeCardEl.style.setProperty('--card-my', `${Math.round(relY)}px`);
      activeCardEl.style.setProperty('--card-spotlight', '1');

      if (activeCardEl.classList.contains('card-tilt')) {
        const normX = (relX / rect.width) - 0.5;
        const normY = (relY / rect.height) - 0.5;
        // 2 to 4 degree 3D tilt
        const tiltX = Number((-normY * 6).toFixed(2));
        const tiltY = Number((normX * 6).toFixed(2));
        activeCardEl.style.setProperty('--tilt-x', `${tiltX}deg`);
        activeCardEl.style.setProperty('--tilt-y', `${tiltY}deg`);
      }
    }

    // Continue loop only if an interaction is active or returning
    const isMagneticRunning = activeMagneticEl || Math.abs(magCurrentX) > 0.05 || Math.abs(magCurrentY) > 0.05;
    if (isMagneticRunning || activeCardEl) {
      rafId = requestAnimationFrame(updateInteractions);
    } else {
      rafId = null;
    }
  }

  function startRafIfNeeded() {
    if (!rafId) {
      rafId = requestAnimationFrame(updateInteractions);
    }
  }

  // Pointer event delegation
  function handlePointerMove(e: PointerEvent) {
    pointerX = e.clientX;
    pointerY = e.clientY;

    if (activeMagneticEl) {
      const rect = activeMagneticEl.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      const dx = pointerX - centerX;
      const dy = pointerY - centerY;
      // Drift up to 6px toward cursor
      magTargetX = Math.max(-6, Math.min(6, (dx / (rect.width / 2)) * 6));
      magTargetY = Math.max(-6, Math.min(6, (dy / (rect.height / 2)) * 6));
      startRafIfNeeded();
    }

    if (activeCardEl) {
      startRafIfNeeded();
    }
  }

  function handlePointerOver(e: Event) {
    const target = e.target as HTMLElement | null;
    if (!target) return;

    // Check for magnetic button
    const mag = target.closest<HTMLElement>('.btn-magnetic');
    if (mag && mag !== activeMagneticEl) {
      activeMagneticEl = mag;
      startRafIfNeeded();
    }

    // Check for spotlight / tilt card
    const card = target.closest<HTMLElement>('.card-spotlight');
    if (card && card !== activeCardEl) {
      activeCardEl = card;
      startRafIfNeeded();
    }
  }

  function handlePointerOut(e: Event) {
    const target = e.target as HTMLElement | null;
    if (!target) return;

    if (activeMagneticEl && !activeMagneticEl.contains(e.target as Node)) {
      const el = activeMagneticEl;
      magTargetX = 0;
      magTargetY = 0;
      activeMagneticEl = null;
      // Reset smoothly
      setTimeout(() => {
        el.style.setProperty('--mag-x', '0px');
        el.style.setProperty('--mag-y', '0px');
      }, 150);
    }

    if (activeCardEl && !activeCardEl.contains(e.target as Node)) {
      const el = activeCardEl;
      activeCardEl = null;
      el.style.setProperty('--card-spotlight', '0');
      el.style.setProperty('--tilt-x', '0deg');
      el.style.setProperty('--tilt-y', '0deg');
    }
  }

  window.addEventListener('pointermove', handlePointerMove, { passive: true });
  document.addEventListener('pointerover', handlePointerOver, { passive: true });
  document.addEventListener('pointerout', handlePointerOut, { passive: true });

  return () => {
    observer?.disconnect();
    window.removeEventListener('pointermove', handlePointerMove);
    document.removeEventListener('pointerover', handlePointerOver);
    document.removeEventListener('pointerout', handlePointerOut);
    if (rafId) cancelAnimationFrame(rafId);
  };
}

