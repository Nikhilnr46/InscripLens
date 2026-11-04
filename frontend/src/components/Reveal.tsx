import React, { useEffect, useRef, ElementType, HTMLAttributes, ReactNode } from 'react';
import { observeReveal } from '../utils/revealObserver';

export type RevealVariant = 'up' | 'left' | 'right' | 'scale';

export interface UseRevealOptions {
  variant?: RevealVariant;
  delay?: number;
  initialShown?: boolean;
}

/**
 * useReveal hook: attaches scroll-reveal attributes and registers with the shared observer.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(options?: UseRevealOptions) {
  const ref = useRef<T | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const variant = options?.variant || 'up';
    el.setAttribute('data-reveal-variant', variant);

    if (options?.delay) {
      el.style.setProperty('--reveal-delay', `${options.delay}ms`);
    }

    if (options?.initialShown) {
      // Reveal on first paint without waiting for scroll
      el.setAttribute('data-reveal', 'hidden');
      const raf1 = requestAnimationFrame(() => {
        const raf2 = requestAnimationFrame(() => {
          el.setAttribute('data-reveal', 'shown');
        });
        return () => cancelAnimationFrame(raf2);
      });
      const unobserve = observeReveal(el);
      return () => {
        cancelAnimationFrame(raf1);
        unobserve();
      };
    } else {
      el.setAttribute('data-reveal', 'hidden');
      return observeReveal(el);
    }
  }, [options?.variant, options?.delay, options?.initialShown]);

  return ref;
}

export interface RevealProps extends HTMLAttributes<HTMLElement> {
  children?: ReactNode;
  variant?: RevealVariant;
  delay?: number;
  initialShown?: boolean;
  className?: string;
  as?: ElementType;
}

/**
 * Reusable <Reveal> component wrapper for replaying scroll-reveal animations.
 * Uses individual translate/scale and opacity properties (never touches transform).
 */
export default function Reveal({
  children,
  variant = 'up',
  delay = 0,
  initialShown = false,
  className = '',
  as: Component = 'div',
  style,
  ...props
}: RevealProps) {
  const ref = useReveal<HTMLElement>({ variant, delay, initialShown });

  const mergedStyle: React.CSSProperties = {
    ...style,
    ...(delay > 0 ? ({ '--reveal-delay': `${delay}ms` } as React.CSSProperties) : {})
  };

  return (
    <Component
      ref={ref}
      className={`reveal-wrapper ${className}`.trim()}
      style={mergedStyle}
      data-reveal={initialShown ? 'shown' : 'hidden'}
      data-reveal-variant={variant}
      {...props}
    >
      {children}
    </Component>
  );
}

