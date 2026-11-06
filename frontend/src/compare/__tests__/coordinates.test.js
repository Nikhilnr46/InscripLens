/**
 * Unit tests for coordinate transformation and bounding box normalization.
 */

import {
  screenToImage,
  imageToScreen,
  normalizeBbox,
  screenRectToImageBbox,
  imageBboxToScreenRect
} from '../coordinates.js';

export function runCoordinateTests() {
  const results = [];
  function assert(cond, msg) {
    if (!cond) throw new Error(msg);
  }

  // 1. Identity transform at scale 1.0, pan (0,0)
  {
    const transform = { scale: 1.0, pan: { x: 0, y: 0 } };
    const pt = { x: 100, y: 200 };
    const imgPt = screenToImage(pt, transform);
    assert(imgPt.x === 100 && imgPt.y === 200, 'Identity screenToImage failed');

    const scrPt = imageToScreen(imgPt, transform);
    assert(scrPt.x === 100 && scrPt.y === 200, 'Identity imageToScreen failed');
    results.push('PASS: Identity transform at scale 1.0, pan (0,0)');
  }

  // 2. High zoom and pan (scale: 2.5, pan: {-150, 80})
  {
    const transform = { scale: 2.5, pan: { x: -150, y: 80 } };
    const origImagePt = { x: 265, y: 147 };
    const scrPt = imageToScreen(origImagePt, transform);
    // screenX = 265 * 2.5 - 150 = 662.5 - 150 = 512.5
    // screenY = 147 * 2.5 + 80 = 367.5 + 80 = 447.5
    assert(Math.abs(scrPt.x - 512.5) < 1e-4, 'Zoom imageToScreen x failed');
    assert(Math.abs(scrPt.y - 447.5) < 1e-4, 'Zoom imageToScreen y failed');

    const mappedBack = screenToImage(scrPt, transform);
    assert(mappedBack.x === 265 && mappedBack.y === 147, 'Zoom roundtrip failed');
    results.push('PASS: Scale 2.5, pan (-150, 80) zoom and pan mapping');
  }

  // 3. Zoom out and negative pan (scale: 0.8, pan: {50, -30})
  {
    const transform = { scale: 0.8, pan: { x: 50, y: -30 } };
    const imgPt = { x: 500, y: 400 };
    const scrPt = imageToScreen(imgPt, transform);
    const roundTrip = screenToImage(scrPt, transform);
    assert(roundTrip.x === 500 && roundTrip.y === 400, 'Scale 0.8 roundtrip failed');
    results.push('PASS: Scale 0.8, pan (50, -30) zoom out roundtrip');
  }

  // 4. Clamping to bounds and integer rounding
  {
    const transform = { scale: 1.0, pan: { x: 0, y: 0 } };
    const imageBounds = { width: 1000, height: 800 };

    const negativePt = screenToImage({ x: -45, y: -12 }, transform, imageBounds);
    assert(negativePt.x === 0 && negativePt.y === 0, 'Negative coordinate clamp failed');

    const overflowPt = screenToImage({ x: 1500, y: 950 }, transform, imageBounds);
    assert(overflowPt.x === 1000 && overflowPt.y === 800, 'Overflow coordinate clamp failed');

    const floatPt = screenToImage({ x: 10.4, y: 20.6 }, transform, imageBounds);
    assert(floatPt.x === 10 && floatPt.y === 21, 'Integer rounding failed');
    results.push('PASS: Clamping to image bounds and integer rounding');
  }

  // 5. Inverted coordinate normalization (x2 < x1, y2 < y1)
  {
    const imageBounds = { width: 500, height: 500 };
    const inverted = [200, 300, 150, 250]; // x1 > x2, y1 > y2
    const norm = normalizeBbox(inverted, imageBounds);
    assert(norm[0] === 150 && norm[1] === 250 && norm[2] === 200 && norm[3] === 300, 'Inverted coordinates normalization failed');
    assert(norm[0] < norm[2] && norm[1] < norm[3], 'Strict inequality failed');
    results.push('PASS: Inverted coordinate normalization');
  }

  // 6. Minimum dimension enforcement (8 x 8 px)
  {
    const imageBounds = { width: 1000, height: 1000 };
    const tinyBbox = [50, 50, 52, 53]; // 2 x 3 px
    const norm = normalizeBbox(tinyBbox, imageBounds, 8);
    const w = norm[2] - norm[0];
    const h = norm[3] - norm[1];
    assert(w >= 8, `Expected min width >= 8, got ${w}`);
    assert(h >= 8, `Expected min height >= 8, got ${h}`);
    assert(norm[0] >= 0 && norm[2] <= 1000, 'Bounds violated during expansion');
    results.push('PASS: Minimum 8x8 px dimension enforcement');
  }

  // 7. Selected-area image with custom dimensions (e.g. 1240 x 860 px)
  {
    const selectedBounds = { width: 1240, height: 860 };
    const transform = { scale: 1.8, pan: { x: -200, y: -100 } };

    // Point near corner of selected area
    const borderPt = { x: 1239, y: 859 };
    const scrPt = imageToScreen(borderPt, transform);
    const backPt = screenToImage(scrPt, transform, selectedBounds);
    assert(backPt.x === 1239 && backPt.y === 859, 'Selected-area corner mapping failed');

    // Drag box near edge
    const edgeBbox = [1235, 855, 1245, 865];
    const normalizedEdge = normalizeBbox(edgeBbox, selectedBounds, 8);
    assert(normalizedEdge[2] === 1240 && normalizedEdge[3] === 860, 'Selected-area edge clamp failed');
    assert(normalizedEdge[2] - normalizedEdge[0] >= 8, 'Selected-area edge width failed');
    assert(normalizedEdge[3] - normalizedEdge[1] >= 8, 'Selected-area edge height failed');
    results.push('PASS: Selected-area image (1240x860 px) bounds mapping and clamping');
  }

  return results;
}
