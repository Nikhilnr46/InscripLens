/**
 * Crop thumbnail generation helper for comparison records.
 * Generates compact 96 px data URLs for storage and quick rendering in the saved list.
 *
 * Adheres strictly to security rules: never stores or produces filesystem paths.
 */

const THUMBNAIL_SIZE = 96;

/**
 * Generate a 96 px data URL thumbnail for a given crop bounding box from an image or canvas.
 *
 * @param {HTMLImageElement|HTMLCanvasElement|ImageBitmap} source - Loaded image or canvas element
 * @param {number[]} bbox - [x1, y1, x2, y2]
 * @param {number} [targetSize=96] - Thumbnail edge size in pixels
 * @returns {string} Image data URL (JPEG/PNG)
 */
export function createCropThumbnail(source, bbox, targetSize = THUMBNAIL_SIZE) {
  if (typeof document === 'undefined') {
    // Return empty SVG data URL placeholder for non-browser/test environments
    return `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="${targetSize}" height="${targetSize}"><rect width="100%" height="100%" fill="%23222"/></svg>`;
  }

  if (!source || !Array.isArray(bbox) || bbox.length !== 4) {
    return '';
  }

  const x1 = Math.round(Math.min(bbox[0], bbox[2]));
  const x2 = Math.round(Math.max(bbox[0], bbox[2]));
  const y1 = Math.round(Math.min(bbox[1], bbox[3]));
  const y2 = Math.round(Math.max(bbox[1], bbox[3]));

  const cropW = Math.max(1, x2 - x1);
  const cropH = Math.max(1, y2 - y1);

  try {
    const canvas = document.createElement('canvas');
    canvas.width = targetSize;
    canvas.height = targetSize;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    // Dark background matching obsidian theme
    ctx.fillStyle = '#16161A';
    ctx.fillRect(0, 0, targetSize, targetSize);

    // Compute aspect-ratio-preserving fit into targetSize x targetSize
    const scale = Math.min((targetSize - 8) / cropW, (targetSize - 8) / cropH);
    const destW = Math.round(cropW * scale);
    const destH = Math.round(cropH * scale);
    const destX = Math.round((targetSize - destW) / 2);
    const destY = Math.round((targetSize - destH) / 2);

    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'medium';

    ctx.drawImage(
      source,
      x1, y1, cropW, cropH,
      destX, destY, destW, destH
    );

    return canvas.toDataURL('image/jpeg', 0.82);
  } catch {
    return '';
  }
}

/**
 * Generate a 96 px data URL thumbnail asynchronously from an image/crop URL.
 *
 * @param {string} cropUrl - Image or crop URL
 * @param {number} [targetSize=96]
 * @returns {Promise<string>}
 */
export async function generateThumbnailFromUrl(cropUrl, targetSize = THUMBNAIL_SIZE) {
  if (typeof document === 'undefined' || !cropUrl || typeof cropUrl !== 'string') {
    return '';
  }

  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';

    const timer = setTimeout(() => {
      resolve('');
    }, 3000);

    img.onload = () => {
      clearTimeout(timer);
      try {
        const canvas = document.createElement('canvas');
        canvas.width = targetSize;
        canvas.height = targetSize;
        const ctx = canvas.getContext('2d');
        if (!ctx) return resolve('');

        ctx.fillStyle = '#16161A';
        ctx.fillRect(0, 0, targetSize, targetSize);

        const w = img.naturalWidth || img.width || targetSize;
        const h = img.naturalHeight || img.height || targetSize;
        const scale = Math.min((targetSize - 8) / w, (targetSize - 8) / h);
        const destW = Math.round(w * scale);
        const destH = Math.round(h * scale);
        const destX = Math.round((targetSize - destW) / 2);
        const destY = Math.round((targetSize - destH) / 2);

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'medium';

        ctx.drawImage(img, 0, 0, w, h, destX, destY, destW, destH);
        resolve(canvas.toDataURL('image/jpeg', 0.82));
      } catch {
        resolve('');
      }
    };

    img.onerror = () => {
      clearTimeout(timer);
      resolve('');
    };

    img.src = cropUrl;
  });
}
