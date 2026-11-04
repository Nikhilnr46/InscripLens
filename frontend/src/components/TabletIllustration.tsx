import React, { useEffect, useRef } from 'react';
import { Database, ShieldCheck, Cpu, Compass } from 'lucide-react';
import Reveal from './Reveal';
import './TabletIllustration.css';

// Seeded PRNG for deterministic, load-identical cracks
class SeededRNG {
  private s: number;
  constructor(seed = 20261104) {
    this.s = seed;
  }
  next(): number {
    this.s = (this.s * 1664525 + 1013904223) >>> 0;
    return this.s / 4294967296;
  }
  range(min: number, max: number): number {
    return min + this.next() * (max - min);
  }
}

// Generate jagged walk path between waypoints
function generateJaggedPath(
  waypoints: [number, number][],
  rng: SeededRNG,
  jitter = 1.5,
  step = 6.0
): string {
  const points: [number, number][] = [waypoints[0]];
  for (let i = 0; i < waypoints.length - 1; i++) {
    const p1 = waypoints[i];
    const p2 = waypoints[i + 1];
    const dx = p2[0] - p1[0];
    const dy = p2[1] - p1[1];
    const dist = Math.hypot(dx, dy);
    const steps = Math.max(1, Math.floor(dist / step));
    const ux = dx / dist;
    const uy = dy / dist;
    const nx = -uy;
    const ny = ux;
    for (let s = 1; s < steps; s++) {
      const t = s / steps;
      const bx = p1[0] + dx * t;
      const by = p1[1] + dy * t;
      const j = rng.range(-jitter, jitter);
      points.push([
        Number((bx + nx * j).toFixed(1)),
        Number((by + ny * j).toFixed(1))
      ]);
    }
    points.push(p2);
  }
  return 'M ' + points.map((p) => `${p[0]},${p[1]}`).join(' L ');
}

interface CrackDef {
  id: string;
  mainD: string;
  branchDs: string[];
}

// Fixed-seed deterministic hairline cracks
function createHairlineCracks(): CrackDef[] {
  const rng = new SeededRNG(20261104);

  // Crack 1: Top right arch down right margin
  const c1_main = generateJaggedPath([[270, 78], [274, 110], [278, 145], [275, 185]], rng, 1.4, 6.0);
  const c1_b1 = generateJaggedPath([[274, 110], [262, 108]], rng, 1.0, 4.0);
  const c1_b2 = generateJaggedPath([[278, 145], [285, 155]], rng, 1.0, 4.0);

  // Crack 2: Left margin upper
  const c2_main = generateJaggedPath([[60, 95], [63, 130], [59, 165], [64, 205]], rng, 1.4, 6.0);
  const c2_b1 = generateJaggedPath([[63, 130], [72, 134]], rng, 1.0, 4.0);
  const c2_b2 = generateJaggedPath([[59, 165], [52, 172]], rng, 1.0, 4.0);

  // Crack 3: Transverse crack between row 5 & 6 (gap at y~231)
  const c3_main = generateJaggedPath([[62, 230], [95, 231], [130, 229], [168, 231]], rng, 1.4, 6.0);
  const c3_b1 = generateJaggedPath([[95, 231], [97, 224]], rng, 1.0, 4.0);
  const c3_b2 = generateJaggedPath([[130, 229], [132, 237]], rng, 1.0, 4.0);

  // Crack 4: Lower left margin down toward base
  const c4_main = generateJaggedPath([[61, 275], [66, 315], [62, 355], [70, 395]], rng, 1.4, 6.0);
  const c4_b1 = generateJaggedPath([[66, 315], [75, 320]], rng, 1.0, 4.0);
  const c4_b2 = generateJaggedPath([[62, 355], [55, 362]], rng, 1.0, 4.0);

  // Crack 5: Lower right margin
  const c5_main = generateJaggedPath([[277, 225], [281, 265], [278, 305], [282, 345]], rng, 1.4, 6.0);
  const c5_b1 = generateJaggedPath([[281, 265], [268, 268]], rng, 1.0, 4.0);
  const c5_b2 = generateJaggedPath([[278, 305], [269, 302]], rng, 1.0, 4.0);

  // Crack 6: Bottom margin base fissure
  const c6_main = generateJaggedPath([[125, 402], [160, 400], [195, 403], [235, 401]], rng, 1.4, 6.0);
  const c6_b1 = generateJaggedPath([[160, 400], [163, 393]], rng, 1.0, 4.0);
  const c6_b2 = generateJaggedPath([[195, 403], [197, 408]], rng, 1.0, 4.0);

  return [
    { id: 'c1', mainD: c1_main, branchDs: [c1_b1, c1_b2] },
    { id: 'c2', mainD: c2_main, branchDs: [c2_b1, c2_b2] },
    { id: 'c3', mainD: c3_main, branchDs: [c3_b1, c3_b2] },
    { id: 'c4', mainD: c4_main, branchDs: [c4_b1, c4_b2] },
    { id: 'c5', mainD: c5_main, branchDs: [c5_b1, c5_b2] },
    { id: 'c6', mainD: c6_main, branchDs: [c6_b1, c6_b2] }
  ];
}

const STATIC_CRACKS = createHairlineCracks();

interface GlyphBlock {
  id: number;
  x: number;
  y: number;
  w: number;
  h: number;
  cx: number;
  cy: number;
}

// 87 Authentically spaced Halegannada inscription blocks
const GLYPH_BLOCKS: GlyphBlock[] = [
  // Line 1 (y=118)
  { id: 0, x: 76, y: 118, w: 12, h: 10, cx: 82, cy: 123 },
  { id: 1, x: 94, y: 118, w: 14, h: 10, cx: 101, cy: 123 },
  { id: 2, x: 114, y: 118, w: 10, h: 10, cx: 119, cy: 123 },
  { id: 3, x: 130, y: 118, w: 18, h: 10, cx: 139, cy: 123 },
  { id: 4, x: 154, y: 118, w: 12, h: 10, cx: 160, cy: 123 },
  { id: 5, x: 172, y: 118, w: 16, h: 10, cx: 180, cy: 123 },
  { id: 6, x: 194, y: 118, w: 14, h: 10, cx: 201, cy: 123 },
  { id: 7, x: 214, y: 118, w: 20, h: 10, cx: 224, cy: 123 },
  { id: 8, x: 240, y: 118, w: 14, h: 10, cx: 247, cy: 123 },

  // Line 2 (y=142)
  { id: 9, x: 76, y: 142, w: 16, h: 10, cx: 84, cy: 147 },
  { id: 10, x: 98, y: 142, w: 12, h: 10, cx: 104, cy: 147 },
  { id: 11, x: 116, y: 142, w: 18, h: 10, cx: 125, cy: 147 },
  { id: 12, x: 140, y: 142, w: 10, h: 10, cx: 145, cy: 147 },
  { id: 13, x: 156, y: 142, w: 14, h: 10, cx: 163, cy: 147 },
  { id: 14, x: 176, y: 142, w: 20, h: 10, cx: 186, cy: 147 },
  { id: 15, x: 202, y: 142, w: 12, h: 10, cx: 208, cy: 147 },
  { id: 16, x: 220, y: 142, w: 16, h: 10, cx: 228, cy: 147 },
  { id: 17, x: 242, y: 142, w: 18, h: 10, cx: 251, cy: 147 },

  // Line 3 (y=166)
  { id: 18, x: 76, y: 166, w: 14, h: 10, cx: 83, cy: 171 },
  { id: 19, x: 96, y: 166, w: 20, h: 10, cx: 106, cy: 171 },
  { id: 20, x: 122, y: 166, w: 12, h: 10, cx: 128, cy: 171 },
  { id: 21, x: 140, y: 166, w: 16, h: 10, cx: 148, cy: 171 },
  { id: 22, x: 162, y: 166, w: 14, h: 10, cx: 169, cy: 171 },
  { id: 23, x: 182, y: 166, w: 18, h: 10, cx: 191, cy: 171 },
  { id: 24, x: 206, y: 166, w: 10, h: 10, cx: 211, cy: 171 },
  { id: 25, x: 222, y: 166, w: 22, h: 10, cx: 233, cy: 171 },
  { id: 26, x: 250, y: 166, w: 10, h: 10, cx: 255, cy: 171 },

  // Line 4 (y=190)
  { id: 27, x: 76, y: 190, w: 18, h: 10, cx: 85, cy: 195 },
  { id: 28, x: 100, y: 190, w: 12, h: 10, cx: 106, cy: 195 },
  { id: 29, x: 118, y: 190, w: 14, h: 10, cx: 125, cy: 195 },
  { id: 30, x: 138, y: 190, w: 22, h: 10, cx: 149, cy: 195 },
  { id: 31, x: 166, y: 190, w: 12, h: 10, cx: 172, cy: 195 },
  { id: 32, x: 184, y: 190, w: 16, h: 10, cx: 192, cy: 195 },
  { id: 33, x: 206, y: 190, w: 14, h: 10, cx: 213, cy: 195 },
  { id: 34, x: 226, y: 190, w: 18, h: 10, cx: 235, cy: 195 },
  { id: 35, x: 248, y: 190, w: 12, h: 10, cx: 254, cy: 195 },

  // Line 5 (y=214)
  { id: 36, x: 76, y: 214, w: 12, h: 10, cx: 82, cy: 219 },
  { id: 37, x: 94, y: 214, w: 16, h: 10, cx: 102, cy: 219 },
  { id: 38, x: 116, y: 214, w: 20, h: 10, cx: 126, cy: 219 },
  { id: 39, x: 142, y: 214, w: 12, h: 10, cx: 148, cy: 219 },
  { id: 40, x: 160, y: 214, w: 14, h: 10, cx: 167, cy: 219 },
  { id: 41, x: 180, y: 214, w: 22, h: 10, cx: 191, cy: 219 },
  { id: 42, x: 208, y: 214, w: 14, h: 10, cx: 215, cy: 219 },
  { id: 43, x: 228, y: 214, w: 10, h: 10, cx: 233, cy: 219 },
  { id: 44, x: 244, y: 214, w: 16, h: 10, cx: 252, cy: 219 },

  // Line 6 (y=238)
  { id: 45, x: 76, y: 238, w: 18, h: 10, cx: 85, cy: 243 },
  { id: 46, x: 100, y: 238, w: 14, h: 10, cx: 107, cy: 243 },
  { id: 47, x: 120, y: 238, w: 12, h: 10, cx: 126, cy: 243 },
  { id: 48, x: 138, y: 238, w: 18, h: 10, cx: 147, cy: 243 },
  { id: 49, x: 162, y: 238, w: 20, h: 10, cx: 172, cy: 243 },
  { id: 50, x: 188, y: 238, w: 14, h: 10, cx: 195, cy: 243 },
  { id: 51, x: 208, y: 238, w: 16, h: 10, cx: 216, cy: 243 },
  { id: 52, x: 230, y: 238, w: 12, h: 10, cx: 236, cy: 243 },
  { id: 53, x: 248, y: 238, w: 14, h: 10, cx: 255, cy: 243 },

  // Line 7 (y=262)
  { id: 54, x: 76, y: 262, w: 14, h: 10, cx: 83, cy: 267 },
  { id: 55, x: 96, y: 262, w: 18, h: 10, cx: 105, cy: 267 },
  { id: 56, x: 120, y: 262, w: 12, h: 10, cx: 126, cy: 267 },
  { id: 57, x: 138, y: 262, w: 16, h: 10, cx: 146, cy: 267 },
  { id: 58, x: 160, y: 262, w: 10, h: 10, cx: 165, cy: 267 },
  { id: 59, x: 176, y: 262, w: 22, h: 10, cx: 187, cy: 267 },
  { id: 60, x: 204, y: 262, w: 14, h: 10, cx: 211, cy: 267 },
  { id: 61, x: 224, y: 262, w: 18, h: 10, cx: 233, cy: 267 },
  { id: 62, x: 248, y: 262, w: 12, h: 10, cx: 254, cy: 267 },

  // Line 8 (y=286)
  { id: 63, x: 76, y: 286, w: 20, h: 10, cx: 86, cy: 291 },
  { id: 64, x: 102, y: 286, w: 12, h: 10, cx: 108, cy: 291 },
  { id: 65, x: 120, y: 286, w: 16, h: 10, cx: 128, cy: 291 },
  { id: 66, x: 142, y: 286, w: 14, h: 10, cx: 149, cy: 291 },
  { id: 67, x: 162, y: 286, w: 18, h: 10, cx: 171, cy: 291 },
  { id: 68, x: 186, y: 286, w: 12, h: 10, cx: 192, cy: 291 },
  { id: 69, x: 204, y: 286, w: 20, h: 10, cx: 214, cy: 291 },
  { id: 70, x: 230, y: 286, w: 14, h: 10, cx: 237, cy: 291 },

  // Line 9 (y=310)
  { id: 71, x: 76, y: 310, w: 16, h: 10, cx: 84, cy: 315 },
  { id: 72, x: 98, y: 310, w: 14, h: 10, cx: 105, cy: 315 },
  { id: 73, x: 118, y: 310, w: 18, h: 10, cx: 127, cy: 315 },
  { id: 74, x: 142, y: 310, w: 12, h: 10, cx: 148, cy: 315 },
  { id: 75, x: 160, y: 310, w: 20, h: 10, cx: 170, cy: 315 },
  { id: 76, x: 186, y: 310, w: 10, h: 10, cx: 191, cy: 315 },
  { id: 77, x: 202, y: 310, w: 16, h: 10, cx: 210, cy: 315 },
  { id: 78, x: 224, y: 310, w: 22, h: 10, cx: 235, cy: 315 },

  // Line 10 (y=334)
  { id: 79, x: 76, y: 334, w: 18, h: 10, cx: 85, cy: 339 },
  { id: 80, x: 100, y: 334, w: 12, h: 10, cx: 106, cy: 339 },
  { id: 81, x: 118, y: 334, w: 22, h: 10, cx: 129, cy: 339 },
  { id: 82, x: 146, y: 334, w: 14, h: 10, cx: 153, cy: 339 },
  { id: 83, x: 166, y: 334, w: 18, h: 10, cx: 175, cy: 339 },
  { id: 84, x: 190, y: 334, w: 12, h: 10, cx: 196, cy: 339 },
  { id: 85, x: 208, y: 334, w: 16, h: 10, cx: 216, cy: 339 },
  { id: 86, x: 230, y: 334, w: 14, h: 10, cx: 237, cy: 339 }
];

export default function TabletIllustration() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const tabletWrapperRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const spotlightGroupRef = useRef<SVGGElement | null>(null);
  const crackMaskGroupRef = useRef<SVGGElement | null>(null);

  // Cached DOM elements for 60fps rAF updates without React re-render
  const glyphRefs = useRef<(SVGRectElement | null)[]>([]);
  const frameRefs = useRef<(SVGRectElement | null)[]>([]);

  // Interaction tracking state (refs only, NO React state on pointermove)
  const isPointerActive = useRef<boolean>(false);
  const isTouchDragging = useRef<boolean>(false);
  const targetSvgX = useRef<number>(170);
  const targetSvgY = useRef<number>(220);
  const curSvgX = useRef<number>(170);
  const curSvgY = useRef<number>(220);
  const targetGlow = useRef<number>(0);
  const curGlow = useRef<number>(0);

  // Parallax nudge (2 to 3px)
  const targetParallaxX = useRef<number>(0);
  const targetParallaxY = useRef<number>(0);
  const curParallaxX = useRef<number>(0);
  const curParallaxY = useRef<number>(0);

  // Cached layout metrics (recalculated on resize ONLY)
  const cachedRect = useRef<{ left: number; top: number; width: number; height: number }>({
    left: 0,
    top: 0,
    width: 320,
    height: 440
  });

  const rafId = useRef<number | null>(null);
  const isRafRunning = useRef<boolean>(false);
  const reducedMotion = useRef<boolean>(false);

  // Measure and cache tablet bounding box on resize only
  const updateCachedRect = () => {
    if (svgRef.current) {
      const r = svgRef.current.getBoundingClientRect();
      cachedRect.current = {
        left: r.left,
        top: r.top,
        width: r.width || 320,
        height: r.height || 440
      };
    }
  };

  useEffect(() => {
    // Check prefers-reduced-motion
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    reducedMotion.current = mediaQuery.matches;

    const handleMotionChange = (e: MediaQueryListEvent) => {
      reducedMotion.current = e.matches;
    };
    mediaQuery.addEventListener('change', handleMotionChange);

    updateCachedRect();
    window.addEventListener('resize', updateCachedRect, { passive: true });
    window.addEventListener('scroll', updateCachedRect, { passive: true });

    return () => {
      mediaQuery.removeEventListener('change', handleMotionChange);
      window.removeEventListener('resize', updateCachedRect);
      window.removeEventListener('scroll', updateCachedRect);
      if (rafId.current) {
        cancelAnimationFrame(rafId.current);
      }
    };
  }, []);

  // Proximity glow & nearest block focus frame calculation
  const updateBlockProximity = (svgX: number, svgY: number, glow: number) => {
    if (reducedMotion.current) return;

    let nearestIdx = -1;
    let minDist = Infinity;

    if (glow > 0.01) {
      for (let i = 0; i < GLYPH_BLOCKS.length; i++) {
        const b = GLYPH_BLOCKS[i];
        const dist = Math.hypot(svgX - b.cx, svgY - b.cy);
        if (dist < minDist) {
          minDist = dist;
          nearestIdx = i;
        }
      }
      if (minDist > 105) {
        nearestIdx = -1;
      }
    }

    for (let i = 0; i < GLYPH_BLOCKS.length; i++) {
      const b = GLYPH_BLOCKS[i];
      const frameEl = frameRefs.current[i];
      const glyphEl = glyphRefs.current[i];
      if (!frameEl || !glyphEl) continue;

      const dist = Math.hypot(svgX - b.cx, svgY - b.cy);

      if (glow > 0.01 && dist < 90) {
        const norm = 1 - dist / 90;
        const falloff = norm * norm; // smooth falloff
        const isNearest = i === nearestIdx;
        const frameOpacity = isNearest ? 0.95 : falloff * 0.75 * glow;

        frameEl.style.opacity = frameOpacity.toFixed(3);
        frameEl.classList.add('is-active');

        if (isNearest) {
          frameEl.classList.add('is-nearest');
        } else {
          frameEl.classList.remove('is-nearest');
        }

        // Proximity brightness boost on glyph rect
        glyphEl.style.filter = `brightness(${(1 + falloff * 0.65 * glow).toFixed(2)})`;
        glyphEl.classList.add('is-active');
      } else {
        frameEl.style.opacity = '0';
        frameEl.classList.remove('is-active', 'is-nearest');
        glyphEl.style.filter = '';
        glyphEl.classList.remove('is-active');
      }
    }
  };

  // Single performant requestAnimationFrame loop
  const runLoop = () => {
    if (reducedMotion.current) {
      isRafRunning.current = false;
      return;
    }

    // Smooth easing interpolation
    curGlow.current += (targetGlow.current - curGlow.current) * 0.16;
    curSvgX.current += (targetSvgX.current - curSvgX.current) * 0.22;
    curSvgY.current += (targetSvgY.current - curSvgY.current) * 0.22;

    curParallaxX.current += (targetParallaxX.current - curParallaxX.current) * 0.09;
    curParallaxY.current += (targetParallaxY.current - curParallaxY.current) * 0.09;

    const xVal = Number(curSvgX.current.toFixed(1));
    const yVal = Number(curSvgY.current.toFixed(1));
    const glowVal = Number(curGlow.current.toFixed(3));
    const px = Number(curParallaxX.current.toFixed(2));
    const py = Number(curParallaxY.current.toFixed(2));

    // 1. Write CSS custom properties on container element
    if (containerRef.current) {
      containerRef.current.style.setProperty('--mx', `${xVal}px`);
      containerRef.current.style.setProperty('--my', `${yVal}px`);
      containerRef.current.style.setProperty('--glow', `${glowVal}`);
    }

    // 2. Parallax nudge on tablet element
    if (tabletWrapperRef.current) {
      tabletWrapperRef.current.style.transform = `translate3d(${px}px, ${py}px, 0)`;
    }

    // 3. Update direct transforms for SVG spotlight and crack lighting mask
    if (spotlightGroupRef.current) {
      spotlightGroupRef.current.setAttribute('transform', `translate(${xVal}, ${yVal})`);
      spotlightGroupRef.current.style.opacity = `${glowVal}`;
    }
    if (crackMaskGroupRef.current) {
      crackMaskGroupRef.current.setAttribute('transform', `translate(${xVal}, ${yVal})`);
      crackMaskGroupRef.current.style.opacity = `${glowVal}`;
    }

    // 4. Update glyph blocks proximity
    updateBlockProximity(xVal, yVal, glowVal);

    // 5. Check if animation should continue or pause
    const isSettled =
      !isPointerActive.current &&
      glowVal < 0.005 &&
      Math.abs(px) < 0.04 &&
      Math.abs(py) < 0.04;

    if (isSettled) {
      curGlow.current = 0;
      curParallaxX.current = 0;
      curParallaxY.current = 0;
      if (containerRef.current) {
        containerRef.current.style.setProperty('--glow', '0');
      }
      if (tabletWrapperRef.current) {
        tabletWrapperRef.current.style.transform = 'translate3d(0, 0, 0)';
      }
      updateBlockProximity(0, 0, 0);
      isRafRunning.current = false;
      rafId.current = null;
    } else {
      rafId.current = requestAnimationFrame(runLoop);
    }
  };

  const startLoopIfNeeded = () => {
    if (!isRafRunning.current && !reducedMotion.current) {
      isRafRunning.current = true;
      rafId.current = requestAnimationFrame(runLoop);
    }
  };

  // Convert client viewport coordinates to SVG coordinate space
  const updatePointerPosition = (clientX: number, clientY: number) => {
    const rect = cachedRect.current;
    if (rect.width <= 0 || rect.height <= 0) return;

    const relX = clientX - rect.left;
    const relY = clientY - rect.top;

    // SVG viewBox is 0 0 340 440
    const svgX = (relX / rect.width) * 340;
    const svgY = (relY / rect.height) * 440;

    targetSvgX.current = Math.max(0, Math.min(340, svgX));
    targetSvgY.current = Math.max(0, Math.min(440, svgY));

    // Parallax nudge: 2 to 3px toward cursor with easing
    const normX = ((relX / rect.width) - 0.5) * 2;
    const normY = ((relY / rect.height) - 0.5) * 2;
    targetParallaxX.current = Math.max(-2.6, Math.min(2.6, normX * 2.5));
    targetParallaxY.current = Math.max(-2.6, Math.min(2.6, normY * 2.5));
  };

  // Pointer event handlers
  const handlePointerEnter = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') return;
    isPointerActive.current = true;
    targetGlow.current = 1;
    updatePointerPosition(e.clientX, e.clientY);
    startLoopIfNeeded();
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') {
      if (!isTouchDragging.current) return;
      isPointerActive.current = true;
      targetGlow.current = 1;
      updatePointerPosition(e.clientX, e.clientY);
      startLoopIfNeeded();
      return;
    }
    isPointerActive.current = true;
    targetGlow.current = 1;
    updatePointerPosition(e.clientX, e.clientY);
    startLoopIfNeeded();
  };

  const handlePointerLeave = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') return;
    isPointerActive.current = false;
    targetGlow.current = 0;
    targetParallaxX.current = 0;
    targetParallaxY.current = 0;
    startLoopIfNeeded();
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') {
      isTouchDragging.current = true;
      isPointerActive.current = true;
      targetGlow.current = 1;
      updatePointerPosition(e.clientX, e.clientY);
      startLoopIfNeeded();
    }
  };

  const handlePointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') {
      isTouchDragging.current = false;
      isPointerActive.current = false;
      targetGlow.current = 0;
      targetParallaxX.current = 0;
      targetParallaxY.current = 0;
      startLoopIfNeeded();
    }
  };

  const handlePointerCancel = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.pointerType === 'touch') {
      isTouchDragging.current = false;
      isPointerActive.current = false;
      targetGlow.current = 0;
      targetParallaxX.current = 0;
      targetParallaxY.current = 0;
      startLoopIfNeeded();
    }
  };

  return (
    <div
      ref={containerRef}
      className="stone-tablet-hero"
      aria-hidden="true"
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      onPointerMove={handlePointerMove}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
    >
      {/* Background ambient radial aura */}
      <div className="stone-tablet-glow" />

      {/* Frame Viewfinder Corner Brackets (untouched) */}
      <span className="tablet-bracket bracket-tl" />
      <span className="tablet-bracket bracket-tr" />
      <span className="tablet-bracket bracket-bl" />
      <span className="tablet-bracket bracket-br" />

      {/* Four Floating HUD Chips */}
      <Reveal initialShown variant="up" delay={60} className="hud-chip hud-chip-tl card-spotlight">
        <Compass size={12} className="hud-icon" />
        <span>EPOCH <strong>8th C. CE</strong></span>
      </Reveal>

      <Reveal initialShown variant="up" delay={120} className="hud-chip hud-chip-tr card-spotlight">
        <Database size={12} className="hud-icon text-sandstone" />
        <span>REGIONS <strong>133 localized</strong></span>
      </Reveal>

      <Reveal initialShown variant="up" delay={180} className="hud-chip hud-chip-bl card-spotlight">
        <Cpu size={12} className="hud-icon text-violet" />
        <span>MODEL <strong>Shilalekhya U-Net</strong></span>
      </Reveal>

      <Reveal initialShown variant="up" delay={240} className="hud-chip hud-chip-br card-spotlight">
        <ShieldCheck size={12} className="hud-icon text-green" />
        <span>PRIVACY <strong>100% Local</strong></span>
      </Reveal>

      {/* Parallax-nudged Tablet SVG Wrapper */}
      <div className="tablet-svg-wrapper" ref={tabletWrapperRef}>
        <svg
          ref={svgRef}
          viewBox="0 0 340 440"
          className="stone-tablet-svg"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Ambient Stone Gradients */}
            <linearGradient id="stoneBody" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#1E1E24" />
              <stop offset="50%" stopColor="#141418" />
              <stop offset="100%" stopColor="#0E0E12" />
            </linearGradient>

            <linearGradient id="chiseledBorder" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#C9A66B" stopOpacity="0.8" />
              <stop offset="40%" stopColor="#818CF8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#2A2A35" stopOpacity="0.3" />
            </linearGradient>

            <linearGradient id="glyphGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#C9A66B" />
              <stop offset="50%" stopColor="#DFBA7E" />
              <stop offset="100%" stopColor="#93C5FD" />
            </linearGradient>

            {/* Chisel glow filter */}
            <filter id="softGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="1.8" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>

            {/* Tablet Clip Path */}
            <clipPath id="tabletOutlineClip">
              <path d="M 50 80 Q 170 15 290 80 L 290 410 L 50 410 Z" />
            </clipPath>

            {/* Soft Torch Spotlight Radial Gradient */}
            <radialGradient id="torchRadialGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#DFBA7E" stopOpacity="0.14" />
              <stop offset="35%" stopColor="#C9A66B" stopOpacity="0.09" />
              <stop offset="70%" stopColor="#C9A66B" stopOpacity="0.03" />
              <stop offset="100%" stopColor="#C9A66B" stopOpacity="0" />
            </radialGradient>

            {/* Crack Illumination Mask Gradient (White reveals, black masks) */}
            <radialGradient id="crackMaskGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="1" />
              <stop offset="35%" stopColor="#FFFFFF" stopOpacity="0.8" />
              <stop offset="70%" stopColor="#FFFFFF" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#000000" stopOpacity="0" />
            </radialGradient>

            {/* Hairline Crack Tapering Gradients */}
            <linearGradient id="crackTaperBase" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#524A42" stopOpacity="0.18" />
              <stop offset="50%" stopColor="#443D36" stopOpacity="0.13" />
              <stop offset="100%" stopColor="#36312B" stopOpacity="0.08" />
            </linearGradient>

            <linearGradient id="crackTaperLit" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#F5DFB3" stopOpacity="0.95" />
              <stop offset="55%" stopColor="#DFBA7E" stopOpacity="0.80" />
              <stop offset="100%" stopColor="#C9A66B" stopOpacity="0.45" />
            </linearGradient>

            {/* Mask to illuminate cracks under the torchlight */}
            <mask id="torchCrackMask">
              <rect x="0" y="0" width="340" height="440" fill="#000000" />
              <g className="tablet-crack-mask-group" ref={crackMaskGroupRef}>
                <circle cx="0" cy="0" r="125" fill="url(#crackMaskGrad)" />
              </g>
            </mask>
          </defs>

          {/* Tablet Drop Shadow Silhouette */}
          <path
            d="M 50 80 Q 170 15 290 80 L 290 410 L 50 410 Z"
            fill="#08080A"
            opacity="0.8"
            transform="translate(4, 6)"
          />

          {/* Main Stone Tablet Slab with Arched Top */}
          <path
            d="M 50 80 Q 170 15 290 80 L 290 410 L 50 410 Z"
            fill="url(#stoneBody)"
            stroke="url(#chiseledBorder)"
            strokeWidth="2"
          />

          {/* Inner Recessed Inscription Panel */}
          <path
            d="M 64 92 Q 170 38 276 92 L 276 396 L 64 396 Z"
            fill="#101014"
            stroke="#262630"
            strokeWidth="1.5"
          />

          {/* Crest Relief: Sun, Moon & Heroic Kalasa Crest (Nagavara Style) */}
          <g opacity="0.85">
            <circle cx="100" cy="74" r="9" fill="none" stroke="#C9A66B" strokeWidth="1.5" />
            <circle cx="100" cy="74" r="3" fill="#C9A66B" />
            <path d="M 235 66 A 9 9 0 0 0 245 82 A 7 7 0 0 1 235 66 Z" fill="#818CF8" />
            <polygon points="170,48 163,62 177,62" fill="#C9A66B" opacity="0.9" />
            <rect x="166" y="62" width="8" height="14" fill="#C9A66B" opacity="0.75" />
            <line x1="72" y1="98" x2="268" y2="98" stroke="#3A3A46" strokeWidth="1" strokeDasharray="3 3" />
          </g>

          {/* Natural Hairline Cracks - Layer 1: Base Dark Warm Grey (10-15% Opacity) */}
          <g className="tablet-cracks-base" clipPath="url(#tabletOutlineClip)">
            {STATIC_CRACKS.map((crack) => (
              <g key={`base-${crack.id}`}>
                <path
                  d={crack.mainD}
                  stroke="url(#crackTaperBase)"
                  strokeWidth="0.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {crack.branchDs.map((bd, bi) => (
                  <path
                    key={bi}
                    d={bd}
                    stroke="url(#crackTaperBase)"
                    strokeWidth="0.65"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ))}
              </g>
            ))}
          </g>

          {/* Halegannada Inscription Glyphs with Proximity Hover Frames */}
          <g>
            {GLYPH_BLOCKS.map((b, i) => (
              <g key={b.id}>
                {/* Glyph block */}
                <rect
                  ref={(el) => { glyphRefs.current[i] = el; }}
                  x={b.x}
                  y={b.y}
                  width={b.w}
                  height={b.h}
                  rx="2"
                  className="tablet-glyph-rect"
                />
                {/* 1px Selection Frame (rounded, sandstone/gold) */}
                <rect
                  ref={(el) => { frameRefs.current[i] = el; }}
                  x={b.x - 2}
                  y={b.y - 2}
                  width={b.w + 4}
                  height={b.h + 4}
                  rx="3"
                  className="tablet-glyph-frame"
                />
              </g>
            ))}
          </g>

          {/* Soft Torchlight Spotlight (clipped to tablet outline) */}
          <g clipPath="url(#tabletOutlineClip)">
            <g className="tablet-spotlight-group" ref={spotlightGroupRef}>
              <circle cx="0" cy="0" r="140" fill="url(#torchRadialGrad)" />
            </g>
          </g>

          {/* Natural Hairline Cracks - Layer 2: Lit Gold Fissure (Catching the torchlight) */}
          <g className="tablet-cracks-lit" clipPath="url(#tabletOutlineClip)" mask="url(#torchCrackMask)">
            {STATIC_CRACKS.map((crack) => (
              <g key={`lit-${crack.id}`}>
                <path
                  d={crack.mainD}
                  stroke="url(#crackTaperLit)"
                  strokeWidth="0.9"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {crack.branchDs.map((bd, bi) => (
                  <path
                    key={bi}
                    d={bd}
                    stroke="url(#crackTaperLit)"
                    strokeWidth="0.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ))}
              </g>
            ))}
          </g>

          {/* Animated Sweeping Chisel/Scanning Laser Line */}
          <line
            className="tablet-scan-line"
            x1="66"
            y1="94"
            x2="274"
            y2="94"
            stroke="url(#glyphGlow)"
            strokeWidth="1.5"
            opacity="0.75"
          >
            <animate
              attributeName="y1"
              values="94;390;94"
              dur="6s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="y2"
              values="94;390;94"
              dur="6s"
              repeatCount="indefinite"
            />
          </line>
        </svg>
      </div>
    </div>
  );
}

