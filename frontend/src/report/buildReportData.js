import { formatDisplayLabel } from '../utils/kannadaConverter';

/**
 * Prepares downscaled display copies of photograph and mask (max 1600 px long side)
 * and clips crisp mask thumbnails (max 96 px) for each candidate bounding box.
 *
 * @param {Object} params
 * @param {Object} params.analysis - Analysis record containing image_url and mask_url
 * @param {Array<Array<number>>} params.boxes - Array of [ymin, xmin, ymax, xmax] coordinates
 * @returns {Promise<{ photoDataUrl: string, maskDataUrl: string, thumbnails: Record<number, string> }>}
 */
export async function prepareReportImages({ analysis, boxes = [] }) {
  const MAX_DISPLAY_SIDE = 1600;
  const MAX_THUMBNAIL_SIDE = 96;
  const PADDING = 3;

  // Helper to load an image element
  const loadImage = (url) => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => resolve(img);
      img.onerror = (err) => reject(err);
      img.src = url;
    });
  };

  const results = {
    photoDataUrl: '',
    maskDataUrl: '',
    thumbnails: {}
  };

  try {
    const [photoImg, maskImg] = await Promise.all([
      loadImage(analysis.image_url),
      loadImage(analysis.mask_url)
    ]);

    // 1. Photograph display copy (JPEG quality 0.85, max 1600 px long side)
    const photoScale = Math.min(1, MAX_DISPLAY_SIDE / Math.max(photoImg.naturalWidth, photoImg.naturalHeight));
    const pCanvas = document.createElement('canvas');
    pCanvas.width = Math.max(1, Math.round(photoImg.naturalWidth * photoScale));
    pCanvas.height = Math.max(1, Math.round(photoImg.naturalHeight * photoScale));
    const pCtx = pCanvas.getContext('2d');
    pCtx.drawImage(photoImg, 0, 0, pCanvas.width, pCanvas.height);
    results.photoDataUrl = pCanvas.toDataURL('image/jpeg', 0.85);

    // 2. Mask display copy (PNG, max 1600 px long side)
    const maskScale = Math.min(1, MAX_DISPLAY_SIDE / Math.max(maskImg.naturalWidth, maskImg.naturalHeight));
    const mCanvas = document.createElement('canvas');
    mCanvas.width = Math.max(1, Math.round(maskImg.naturalWidth * maskScale));
    mCanvas.height = Math.max(1, Math.round(maskImg.naturalHeight * maskScale));
    const mCtx = mCanvas.getContext('2d');
    mCtx.drawImage(maskImg, 0, 0, mCanvas.width, mCanvas.height);
    results.maskDataUrl = mCanvas.toDataURL('image/png');

    // 3. Candidate thumbnails directly clipped from mask
    const thumbCanvas = document.createElement('canvas');
    const tCtx = thumbCanvas.getContext('2d');

    const naturalW = maskImg.naturalWidth;
    const naturalH = maskImg.naturalHeight;

    boxes.forEach((bbox, idx) => {
      const [ymin, xmin, ymax, xmax] = bbox;
      const srcX = Math.max(0, xmin - PADDING);
      const srcY = Math.max(0, ymin - PADDING);
      const srcW = Math.min(naturalW - srcX, Math.max(1, (xmax - xmin) + PADDING * 2));
      const srcH = Math.min(naturalH - srcY, Math.max(1, (ymax - ymin) + PADDING * 2));

      const tScale = Math.min(1, MAX_THUMBNAIL_SIDE / Math.max(srcW, srcH));
      thumbCanvas.width = Math.max(1, Math.round(srcW * tScale));
      thumbCanvas.height = Math.max(1, Math.round(srcH * tScale));

      // Clear and draw sub-rectangle
      tCtx.clearRect(0, 0, thumbCanvas.width, thumbCanvas.height);
      tCtx.drawImage(maskImg, srcX, srcY, srcW, srcH, 0, 0, thumbCanvas.width, thumbCanvas.height);

      results.thumbnails[idx] = thumbCanvas.toDataURL('image/png');
    });
  } catch (err) {
    console.error('Failed to prepare report images offscreen:', err);
    // Fall back to original URLs if offscreen canvas decoding fails
    results.photoDataUrl = analysis.image_url;
    results.maskDataUrl = analysis.mask_url;
  }

  return results;
}

/**
 * Builds candidate metadata, Kannada transliterations, confidence scores,
 * and review annotations from the existing Studio state.
 *
 * @param {Object} params
 * @param {Object} params.analysis - Current analysis object from Studio
 * @param {Object} [params.selectionInfo] - Crop region metadata if active
 * @param {Array} [params.batchRegions] - Batch predictions array from Classify All
 * @param {Record<number, any>} [params.predictionCache] - Single crop predictions cache
 * @param {Array} [params.reviewsList] - Review records
 * @param {boolean} [params.highAccuracy] - Whether high accuracy mode was used
 * @param {Object} [params.options] - Report display options
 * @param {boolean} [params.options.modernLetters] - True for modern letters, false for faithful
 * @param {Record<number, string>} [params.thumbnails] - Pre-cut candidate thumbnails
 * @returns {Object} Structured report data ready for ReportView
 */
export function buildReportData({
  analysis,
  selectionInfo = null,
  batchRegions = [],
  predictionCache = {},
  reviewsList = [],
  highAccuracy = false,
  options = {},
  thumbnails = {}
}) {
  if (!analysis) return null;

  const modernLetters = Boolean(options.modernLetters);
  const boxes = analysis.boxes || [];

  // Match review by coordinates [ymin, xmin, ymax, xmax] or [x1, y1, x2, y2]
  const findReview = (bbox) => {
    if (!reviewsList || !reviewsList.length) return null;
    return reviewsList.find(r =>
      Array.isArray(r.bbox) &&
      r.bbox[0] === bbox[0] &&
      r.bbox[1] === bbox[1] &&
      r.bbox[2] === bbox[2] &&
      r.bbox[3] === bbox[3]
    );
  };

  let hasAnyPrediction = false;

  const candidates = boxes.map((bbox, idx) => {
    const ymin = bbox[0];
    const xmin = bbox[1];
    const ymax = bbox[2];
    const xmax = bbox[3];

    const width = Math.max(0, xmax - xmin);
    const height = Math.max(0, ymax - ymin);
    const isTiny = width < 10 && height < 10;

    const review = findReview(bbox);

    let status = 'unpredicted';
    let romanLabel = null;
    let confidence = null;
    let uncertain = false;
    let reviewerName = null;

    if (review) {
      hasAnyPrediction = true;
      if (review.suggested_label && review.suggested_label.trim() !== '') {
        status = 'corrected';
        romanLabel = review.suggested_label.trim();
      } else {
        status = 'reviewed';
        romanLabel = review.prediction || null;
      }
      confidence = review.confidence ?? null;
      uncertain = Boolean(review.uncertain);
      reviewerName = review.reviewer || review.reviewer_name || null;
    } else {
      const batchMatch = batchRegions.find(r => r.candidate === idx + 1);
      const cached = predictionCache[idx];
      const pred = batchMatch
        ? batchMatch.predicted_source_label
        : (typeof cached === 'object' ? cached?.prediction : cached);

      if (pred) {
        hasAnyPrediction = true;
        status = 'predicted';
        romanLabel = pred;
        confidence = batchMatch?.confidence ?? (typeof cached === 'object' ? cached?.confidence : null);
        uncertain = Boolean(batchMatch?.uncertain ?? (typeof cached === 'object' ? cached?.uncertain : false));
      }
    }

    // Convert Roman label to Kannada display form
    let kannadaLabel = null;
    let isLossy = false;
    let isUnmapped = false;

    if (romanLabel) {
      const display = formatDisplayLabel(romanLabel, 'kannada', modernLetters);
      kannadaLabel = display.primary;
      isLossy = Boolean(display.isLossy);
      isUnmapped = Boolean(display.isUnmapped);
    }

    return {
      index: idx,
      number: idx + 1,
      bbox,
      width,
      height,
      isTiny,
      status,
      romanLabel,
      kannadaLabel,
      isLossy,
      isUnmapped,
      confidence,
      uncertain,
      reviewerName,
      thumbUrl: thumbnails[idx] || null
    };
  });

  const now = new Date();
  const formattedDateTime = now.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  }) + ' · ' + now.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit'
  });

  const isSelection = Boolean(selectionInfo && !selectionInfo.isWholeImage);

  const selectedAreaNote = isSelection
    ? `Selected area: ${selectionInfo.width} × ${selectionInfo.height} px (from ${selectionInfo.originalWidth} × ${selectionInfo.originalHeight} px photograph)`
    : null;

  const photoCaption = isSelection ? 'Selected area' : 'Photograph provided';

  return {
    runId: analysis.id,
    isDemo: Boolean(analysis.is_demo),
    modeLabel: highAccuracy ? 'High accuracy mode' : 'Standard mode',
    dimensions: {
      width: analysis.width,
      height: analysis.height
    },
    selectedAreaNote,
    photoCaption,
    dateTime: formattedDateTime,
    hasClassificationRun: hasAnyPrediction,
    candidates
  };
}
