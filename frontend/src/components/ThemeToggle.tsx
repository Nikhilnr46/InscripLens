import React, { useEffect, useRef, useState } from 'react';
import { Sun, Moon } from 'lucide-react';

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    // Read current theme set by the inline head script
    const currentTheme = (document.documentElement.getAttribute('data-theme') as 'dark' | 'light') || 'dark';
    setTheme(currentTheme);

    // Sync if changed from another tab or window
    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'inscriplens_theme' && (e.newValue === 'light' || e.newValue === 'dark')) {
        setTheme(e.newValue);
        document.documentElement.setAttribute('data-theme', e.newValue);
        updateMetaThemeColor(e.newValue);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const updateMetaThemeColor = (activeTheme: 'dark' | 'light') => {
    const meta = document.getElementById('theme-color-meta');
    if (meta) {
      meta.setAttribute('content', activeTheme === 'light' ? '#F7F2E8' : '#121214');
    }
  };

  const applyThemeChange = (nextTheme: 'dark' | 'light') => {
    document.documentElement.setAttribute('data-theme', nextTheme);
    try {
      localStorage.setItem('inscriplens_theme', nextTheme);
    } catch {
      // Storage access safely caught
    }
    updateMetaThemeColor(nextTheme);
  };

  const handleToggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    const nextTheme: 'dark' | 'light' = theme === 'dark' ? 'light' : 'dark';

    // 1. Determine pointer click coordinates or button center for keyboard trigger
    let x = e.clientX;
    let y = e.clientY;

    if ((!x && !y) || (e.detail === 0 && buttonRef.current)) {
      const rect = buttonRef.current.getBoundingClientRect();
      x = Math.round(rect.left + rect.width / 2);
      y = Math.round(rect.top + rect.height / 2);
    }

    // 2. Reduced motion compliance: switch instantly with no animation
    const prefersReducedMotion =
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      applyThemeChange(nextTheme);
      setTheme(nextTheme);
      return;
    }

    // 3. View Transitions API: circular expanding reveal from click position
    const doc = document as any;
    if (typeof doc.startViewTransition === 'function') {
      const maxDistX = Math.max(x, window.innerWidth - x);
      const maxDistY = Math.max(y, window.innerHeight - y);
      const maxRadius = Math.ceil(Math.hypot(maxDistX, maxDistY));

      const transition = doc.startViewTransition(() => {
        applyThemeChange(nextTheme);
        setTheme(nextTheme);
      });

      transition.ready.then(() => {
        document.documentElement.animate(
          {
            clipPath: [
              `circle(0px at ${x}px ${y}px)`,
              `circle(${maxRadius}px at ${x}px ${y}px)`
            ]
          },
          {
            duration: 600,
            easing: 'ease-in-out',
            pseudoElement: '::view-transition-new(root)'
          }
        );
      });
    } else {
      // 4. Fallback when startViewTransition is unsupported: 250ms fade
      document.documentElement.classList.add('theme-fade-transition');
      applyThemeChange(nextTheme);
      setTheme(nextTheme);
      setTimeout(() => {
        document.documentElement.classList.remove('theme-fade-transition');
      }, 250);
    }
  };

  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';

  return (
    <button
      ref={buttonRef}
      type="button"
      className="theme-toggle-btn"
      onClick={handleToggle}
      aria-label={label}
      title={label}
    >
      <span className={`theme-icon-container ${theme === 'dark' ? 'is-dark' : 'is-light'}`}>
        <Sun className="theme-icon icon-sun" size={17} />
        <Moon className="theme-icon icon-moon" size={17} />
      </span>
    </button>
  );
}

