/**
 * Shared singleton IntersectionObserver for replaying scroll reveals with hysteresis.
 * - Replays every time elements enter / leave viewport (both scrolling down and up).
 * - Reveals at >= 15% visibility.
 * - Resets to hidden only at <= 0% visibility (fully out).
 * - Directly updates data-reveal attribute without React state re-renders.
 */

let sharedRevealObserver: IntersectionObserver | null = null;
const observedElements = new Set<HTMLElement>();

function getSharedObserver(): IntersectionObserver | null {
  if (typeof window === 'undefined') return null;

  if (!sharedRevealObserver) {
    sharedRevealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const el = entry.target as HTMLElement;

          // Hysteresis:
          // Reveal when at least 15% visible
          if (entry.isIntersecting && (entry.intersectionRatio >= 0.15 || entry.intersectionRect.height >= 120)) {
            el.setAttribute('data-reveal', 'shown');
          }
          // Reset when completely out of viewport (0% visible)
          else if (!entry.isIntersecting || entry.intersectionRatio <= 0) {
            el.setAttribute('data-reveal', 'hidden');
          }
        });
      },
      {
        threshold: [0, 0.15],
        rootMargin: '0px 0px 0px 0px'
      }
    );
  }

  return sharedRevealObserver;
}

export function observeReveal(element: HTMLElement | null): () => void {
  if (!element || typeof window === 'undefined') return () => {};

  const observer = getSharedObserver();
  if (!observer) return () => {};

  observedElements.add(element);
  observer.observe(element);

  return () => {
    observedElements.delete(element);
    observer.unobserve(element);
  };
}

/**
 * Re-evaluates intersection for observed elements after rapid programmatic scrolls or layout shifts.
 */
export function refreshReveals(): void {
  if (typeof window === 'undefined') return;

  const winHeight = window.innerHeight;
  observedElements.forEach((el) => {
    const rect = el.getBoundingClientRect();
    const visibleHeight = Math.max(0, Math.min(rect.bottom, winHeight) - Math.max(rect.top, 0));
    const ratio = rect.height > 0 ? visibleHeight / rect.height : 0;

    if (visibleHeight > 0 && (ratio >= 0.15 || visibleHeight >= 120)) {
      el.setAttribute('data-reveal', 'shown');
    } else if (visibleHeight <= 0) {
      el.setAttribute('data-reveal', 'hidden');
    }
  });
}

