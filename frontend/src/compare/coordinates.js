/**
 * Coordinate mapping and bounding-box normalization helpers for the InscripLens viewer.
 *
 * Coordinates in the Epigraphy Studio viewer are defined by the stage CSS transform:
 *   transform: translate(${pan.x}px, ${pan.y}px) scale(${scale})
 * with width/height equal to the active image bounds (original photo or selected area).
 *
 * Adheres strictly to the task requirements:
 * - Reads viewer zoom and pan without altering viewer positioning
 * - Clamps coordinates to image bounds
 * - Rounds all values to integers
 * - Enforces x1 < x2 and y1 < y2
 * - Enforces a minimum dimension of 8 x 8 px
 */

const DEFAULT_MIN_SIZE = 8;

/**
 * Extract normalized pan and scale from diverse transform representations.
 *
 * @param {Object} transform
 * @param {number} [transform.scale=1]
 * @param {{x: number, y: number}} [transform.pan]
 * @param {number} [transform.panX]
 * @param {number} [transform.panY]
 * @returns {{scale: number, panX: number, panY: number}}
 */
export function extractTransform(transform) {
  const scale = (transform && typeof transform.scale === 'number' && transform.scale > 0)
    ? transform.scale
    : 1;

  let panX = 0;
  let panY = 0;

  if (transform) {
    if (transform.pan && typeof transform.pan.x === 'number') {
      panX = transform.pan.x;
      panY = transform.pan.y;
    } else {
      if (typeof transform.panX === 'number') panX = transform.panX;
      if (typeof transform.panY === 'number') panY = transform.panY;
    }
  }

  return { scale, panX, panY };
}

/**
 * Convert a screen coordinate relative to the viewport into image coordinates.
 *
 * @param {{x: number, y: number}} screenPoint
 * @param {Object} transform - { scale, pan: { x, y } }
 * @param {{width: number, height: number}} [imageBounds]
 * @returns {{x: number, y: number}}
 */
export function screenToImage(screenPoint, transform, imageBounds) {
  const { scale, panX, panY } = extractTransform(transform);
  const rawX = (screenPoint.x - panX) / scale;
  const rawY = (screenPoint.y - panY) / scale;

  let roundedX = Math.round(rawX);
  let roundedY = Math.round(rawY);

  if (imageBounds && typeof imageBounds.width === 'number' && typeof imageBounds.height === 'number') {
    roundedX = Math.max(0, Math.min(imageBounds.width, roundedX));
    roundedY = Math.max(0, Math.min(imageBounds.height, roundedY));
  }

  return { x: roundedX, y: roundedY };
}

/**
 * Convert an image pixel coordinate into screen coordinates relative to the viewport.
 *
 * @param {{x: number, y: number}} imagePoint
 * @param {Object} transform - { scale, pan: { x, y } }
 * @returns {{x: number, y: number}}
 */
export function imageToScreen(imagePoint, transform) {
  const { scale, panX, panY } = extractTransform(transform);
  const screenX = imagePoint.x * scale + panX;
  const screenY = imagePoint.y * scale + panY;

  return { x: screenX, y: screenY };
}

/**
 * Normalise and constrain bounding box coordinates.
 * - Enforces x1 < x2 and y1 < y2 (swapping inverted coordinates if needed)
 * - Rounds all values to integers
 * - Clamps coordinates to image bounds [0, 0, width, height]
 * - Enforces minimum dimensions of 8 x 8 px
 *
 * @param {number[]} bbox - [x1, y1, x2, y2]
 * @param {{width: number, height: number}} imageBounds
 * @param {number} [minSize=8] - Minimum width and height
 * @returns {[number, number, number, number]} Clamped and normalized [x1, y1, x2, y2]
 */
export function normalizeBbox(bbox, imageBounds, minSize = DEFAULT_MIN_SIZE) {
  if (!Array.isArray(bbox) || bbox.length !== 4) {
    throw new Error('Bounding box must be an array of 4 coordinates [x1, y1, x2, y2].');
  }

  if (!imageBounds || typeof imageBounds.width !== 'number' || typeof imageBounds.height !== 'number') {
    throw new Error('Valid image bounds { width, height } must be provided.');
  }

  const maxWidth = Math.max(1, Math.round(imageBounds.width));
  const maxHeight = Math.max(1, Math.round(imageBounds.height));

  // Determine effective min dimension (cannot exceed image bounds)
  const effectiveMinWidth = Math.min(maxWidth, Math.max(1, minSize));
  const effectiveMinHeight = Math.min(maxHeight, Math.max(1, minSize));

  let x1 = Math.round(Math.min(bbox[0], bbox[2]));
  let x2 = Math.round(Math.max(bbox[0], bbox[2]));
  let y1 = Math.round(Math.min(bbox[1], bbox[3]));
  let y2 = Math.round(Math.max(bbox[1], bbox[3]));

  // Clamp raw coordinates to image bounds
  x1 = Math.max(0, Math.min(maxWidth, x1));
  x2 = Math.max(0, Math.min(maxWidth, x2));
  y1 = Math.max(0, Math.min(maxHeight, y1));
  y2 = Math.max(0, Math.min(maxHeight, y2));

  // Enforce minimum width
  let width = x2 - x1;
  if (width < effectiveMinWidth) {
    const deficit = effectiveMinWidth - width;
    const expandLeft = Math.floor(deficit / 2);
    const expandRight = deficit - expandLeft;

    x1 -= expandLeft;
    x2 += expandRight;

    // Shift back into bounds if expansion exceeded boundaries
    if (x1 < 0) {
      x2 = Math.min(maxWidth, x2 - x1);
      x1 = 0;
    }
    if (x2 > maxWidth) {
      x1 = Math.max(0, x1 - (x2 - maxWidth));
      x2 = maxWidth;
    }
  }

  // Enforce minimum height
  let height = y2 - y1;
  if (height < effectiveMinHeight) {
    const deficit = effectiveMinHeight - height;
    const expandTop = Math.floor(deficit / 2);
    const expandBottom = deficit - expandTop;

    y1 -= expandTop;
    y2 += expandBottom;

    // Shift back into bounds if expansion exceeded boundaries
    if (y1 < 0) {
      y2 = Math.min(maxHeight, y2 - y1);
      y1 = 0;
    }
    if (y2 > maxHeight) {
      y1 = Math.max(0, y1 - (y2 - maxHeight));
      y2 = maxHeight;
    }
  }

  // Final sanity guard to guarantee x1 < x2 and y1 < y2
  if (x2 <= x1) {
    x2 = Math.min(maxWidth, x1 + 1);
    if (x2 <= x1 && x1 > 0) x1 = x2 - 1;
  }
  if (y2 <= y1) {
    y2 = Math.min(maxHeight, y1 + 1);
    if (y2 <= y1 && y1 > 0) y1 = y2 - 1;
  }

  return [x1, y1, x2, y2];
}

/**
 * Convert a screen drag rectangle into an image pixel bounding box.
 *
 * @param {{x1: number, y1: number, x2: number, y2: number}} screenRect
 * @param {Object} transform - { scale, pan: { x, y } }
 * @param {{width: number, height: number}} imageBounds
 * @param {number} [minSize=8]
 * @returns {[number, number, number, number]}
 */
export function screenRectToImageBbox(screenRect, transform, imageBounds, minSize = DEFAULT_MIN_SIZE) {
  const p1 = screenToImage({ x: screenRect.x1, y: screenRect.y1 }, transform);
  const p2 = screenToImage({ x: screenRect.x2, y: screenRect.y2 }, transform);

  return normalizeBbox([p1.x, p1.y, p2.x, p2.y], imageBounds, minSize);
}

/**
 * Convert an image pixel bounding box [x1, y1, x2, y2] to a screen rectangle.
 *
 * @param {number[]} bbox - [x1, y1, x2, y2]
 * @param {Object} transform - { scale, pan: { x, y } }
 * @returns {{left: number, top: number, right: number, bottom: number, width: number, height: number}}
 */
export function imageBboxToScreenRect(bbox, transform) {
  const p1 = imageToScreen({ x: bbox[0], y: bbox[1] }, transform);
  const p2 = imageToScreen({ x: bbox[2], y: bbox[3] }, transform);

  const left = Math.min(p1.x, p2.x);
  const top = Math.min(p1.y, p2.y);
  const right = Math.max(p1.x, p2.x);
  const bottom = Math.max(p1.y, p2.y);

  return {
    left,
    top,
    right,
    bottom,
    width: right - left,
    height: bottom - top
  };
}
