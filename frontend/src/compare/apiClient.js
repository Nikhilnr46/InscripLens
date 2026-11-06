/**
 * API client for single-crop prediction in the InscripLens Compare module.
 * Calls existing POST /api/predict-crop endpoint with integer bbox coordinates
 * in the original image pixel coordinate space.
 *
 * Implements timeout handling, automatic single retry, and typed results.
 * Strictly adheres to security rules: never stores or leaks internal filesystem paths.
 */

import { toKannada } from '../utils/kannadaConverter';

const DEFAULT_TIMEOUT_MS = 8000;

/**
 * Predict character label and alternatives for a cropped bounding box.
 *
 * @param {string} runId - Active analysis run identifier
 * @param {number[]} bbox - [x1, y1, x2, y2] in original image pixel coordinates
 * @param {Object} [options]
 * @param {number} [options.timeoutMs=8000] - Request timeout in milliseconds
 * @param {boolean} [options.retry=true] - Whether to attempt one retry on failure
 * @param {AbortSignal} [options.signal] - Optional external abort signal
 * @returns {Promise<{cropUrl: string, prediction: string, predictionKannada: string, alternatives: Array, confidence: number|null, modelSha256: string}>}
 */
export async function predictCrop(runId, bbox, options = {}) {
  if (!runId || typeof runId !== 'string') {
    throw new Error('Analysis run ID is required for crop prediction.');
  }

  if (!Array.isArray(bbox) || bbox.length !== 4) {
    throw new Error('Bounding box must be an array of [x1, y1, x2, y2] coordinates.');
  }

  // Ensure coordinates are integers in original image pixel space
  const intBbox = [
    Math.round(bbox[0]),
    Math.round(bbox[1]),
    Math.round(bbox[2]),
    Math.round(bbox[3])
  ];

  if (intBbox[2] <= intBbox[0] || intBbox[3] <= intBbox[1]) {
    throw new Error('Invalid crop bounding box: width and height must be positive.');
  }

  const timeoutMs = typeof options.timeoutMs === 'number' && options.timeoutMs > 0
    ? options.timeoutMs
    : DEFAULT_TIMEOUT_MS;

  const shouldRetry = options.retry !== false;

  const executeRequest = async () => {
    const controller = new AbortController();
    let timedOut = false;

    // Link external abort signal if provided
    if (options.signal) {
      if (options.signal.aborted) {
        throw new DOMException('Request aborted', 'AbortError');
      }
      options.signal.addEventListener('abort', () => controller.abort(), { once: true });
    }

    const timer = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);

    try {
      const res = await fetch('/api/predict-crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: runId,
          bbox: intBbox
        }),
        signal: controller.signal
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const detail = errJson.detail || `Prediction request failed with status ${res.status}`;
        throw new Error(detail);
      }

      const data = await res.json();

      // Return typed prediction result without internal file paths
      const predictionStr = String(data.prediction || '');
      const rawKannada = data.prediction_kannada;
      const kannadaStr = (rawKannada && typeof rawKannada === 'string')
        ? rawKannada
        : (predictionStr ? toKannada(predictionStr) : '');

      const altsList = Array.isArray(data.alternatives) ? data.alternatives : [];

      return {
        cropUrl: typeof data.crop_url === 'string' ? data.crop_url : '',
        prediction: predictionStr,
        predictionKannada: kannadaStr,
        alternatives: altsList,
        confidence: typeof data.confidence === 'number' ? data.confidence : null,
        modelSha256: typeof data.model_sha256 === 'string' ? data.model_sha256 : ''
      };
    } catch (err) {
      if (timedOut) {
        throw new Error(`Crop prediction timed out after ${Math.round(timeoutMs / 1000)} seconds.`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  };

  try {
    return await executeRequest();
  } catch (firstErr) {
    // If request was aborted by external signal, do not retry
    if (options.signal?.aborted || firstErr.name === 'AbortError') {
      throw firstErr;
    }

    if (shouldRetry) {
      try {
        // One retry on request
        return await executeRequest();
      } catch (retryErr) {
        throw retryErr;
      }
    }

    throw firstErr;
  }
}
