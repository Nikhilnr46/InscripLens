/**
 * API client for single-crop prediction in the InscripLens Compare and Studio modules.
 * Calls existing POST /api/predict-crop endpoint with integer bbox coordinates
 * in the original image pixel coordinate space.
 *
 * Implements:
 * - Single in-flight request queue to serialize backend recognition work
 * - Session-level caching by run_id + bbox so boxes are never requested twice
 * - 12-second timeout guard with plain user-facing timeout error
 * - Defensive parsing for diverse alternative and confidence shapes
 * - Strictly adheres to security rules: never stores or leaks internal filesystem paths.
 */

import { toKannada } from '../utils/kannadaConverter';

const DEFAULT_TIMEOUT_MS = 12000;

// Module-level session cache: Map<`${runId}:${x1},${y1},${x2},${y2}`, Object>
const sessionCache = new Map();

/**
 * Generate a deterministic string key for session caching.
 */
export function getCacheKey(runId, bbox) {
  if (!runId || !Array.isArray(bbox) || bbox.length < 4) return null;
  return `${runId}:${Math.round(bbox[0])},${Math.round(bbox[1])},${Math.round(bbox[2])},${Math.round(bbox[3])}`;
}

/**
 * Retrieve cached prediction result for a given run and bbox, if available.
 */
export function getCachedPrediction(runId, bbox) {
  const key = getCacheKey(runId, bbox);
  return key ? sessionCache.get(key) || null : null;
}

/**
 * Store prediction result into session cache.
 */
export function setCachedPrediction(runId, bbox, data) {
  const key = getCacheKey(runId, bbox);
  if (key && data) {
    sessionCache.set(key, data);
  }
}

/**
 * Clear session prediction cache (e.g. when changing runs).
 */
export function clearPredictionCache() {
  sessionCache.clear();
}

// Single in-flight promise queue to ensure only one predict-crop request is active on the server
let activeQueuePromise = Promise.resolve();

/**
 * Predict character label and alternatives for a cropped bounding box.
 *
 * @param {string} runId - Active analysis run identifier
 * @param {number[]} bbox - [x1, y1, x2, y2] in original image pixel coordinates
 * @param {Object} [options]
 * @param {number} [options.timeoutMs=12000] - Request timeout in milliseconds
 * @param {boolean} [options.retry=false] - Whether to attempt retry on failure
 * @param {boolean} [options.bypassCache=false] - Bypass session cache
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

  // Check session cache first (instant return, 0ms latency)
  if (!options.bypassCache) {
    const cached = getCachedPrediction(runId, intBbox);
    if (cached) {
      return cached;
    }
  }

  // Check if already aborted before enqueuing
  if (options.signal?.aborted) {
    throw new DOMException('Request aborted', 'AbortError');
  }

  const timeoutMs = typeof options.timeoutMs === 'number' && options.timeoutMs > 0
    ? options.timeoutMs
    : DEFAULT_TIMEOUT_MS;

  const executeRequest = async () => {
    // Re-check abort status
    if (options.signal?.aborted) {
      throw new DOMException('Request aborted', 'AbortError');
    }

    // Re-check cache in case a prior queued request for the same box completed
    if (!options.bypassCache) {
      const recheck = getCachedPrediction(runId, intBbox);
      if (recheck) return recheck;
    }

    const controller = new AbortController();
    let timedOut = false;

    // Link external abort signal if provided
    let removeAbortListener = null;
    if (options.signal) {
      const onAbort = () => controller.abort();
      options.signal.addEventListener('abort', onAbort, { once: true });
      removeAbortListener = () => options.signal.removeEventListener('abort', onAbort);
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

      // Defensive validation of response shape
      const isUnexpected = (
        !data ||
        typeof data !== 'object' ||
        (data.prediction !== undefined && typeof data.prediction !== 'string' && data.prediction !== null) ||
        (data.alternatives !== undefined && !Array.isArray(data.alternatives))
      );
      if (isUnexpected) {
        console.warn('InscripLens: Received unexpected response shape from predict-crop', data);
      }

      // Return typed prediction result without internal file paths
      const predictionStr = String(data?.prediction || '');
      const rawKannada = data?.prediction_kannada;
      const kannadaStr = (rawKannada && typeof rawKannada === 'string')
        ? rawKannada
        : (predictionStr ? toKannada(predictionStr) : '');

      const altsList = Array.isArray(data?.alternatives)
        ? data.alternatives.map(item => {
            if (typeof item === 'object' && item !== null) {
              return {
                label: String(item.label || ''),
                confidence: typeof item.confidence === 'number'
                  ? item.confidence
                  : (typeof item.score === 'number' ? item.score : null)
              };
            }
            return String(item || '');
          })
        : [];

      const confVal = typeof data?.confidence === 'number' && !isNaN(data.confidence)
        ? data.confidence
        : null;

      const result = {
        cropUrl: typeof data?.crop_url === 'string' ? data.crop_url : '',
        crop_url: typeof data?.crop_url === 'string' ? data.crop_url : '',
        prediction: predictionStr,
        predictionKannada: kannadaStr,
        prediction_kannada: kannadaStr,
        alternatives: altsList,
        confidence: confVal,
        model: typeof data?.model === 'string' ? data.model : 'Experimental recognizer',
        modelSha256: typeof data?.model_sha256 === 'string' ? data.model_sha256 : '',
        uncertain: Boolean(data?.uncertain),
        modelsAgree: data?.models_agree !== undefined ? data.models_agree : (data?.modelsAgree ?? null),
        models_agree: data?.models_agree !== undefined ? data.models_agree : (data?.modelsAgree ?? null),
        confidenceScores: Array.isArray(data?.confidence_scores)
          ? data.confidence_scores
          : (data?.confidenceScores || []),
        confidence_scores: Array.isArray(data?.confidence_scores)
          ? data.confidence_scores
          : (data?.confidenceScores || [])
      };

      setCachedPrediction(runId, intBbox, result);
      return result;
    } catch (err) {
      if (timedOut) {
        throw new Error(`Prediction timed out after ${Math.round(timeoutMs / 1000)} seconds. The server may be busy.`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
      if (removeAbortListener) {
        removeAbortListener();
      }
    }
  };

  // Enqueue execution to ensure only one predict-crop request is active on the server
  const runInQueue = () => {
    return executeRequest();
  };

  const currentTask = activeQueuePromise.then(runInQueue, runInQueue);
  activeQueuePromise = currentTask.catch(() => {});

  try {
    return await currentTask;
  } catch (firstErr) {
    if (options.signal?.aborted || firstErr.name === 'AbortError') {
      throw firstErr;
    }
    if (options.retry === true) {
      return await executeRequest();
    }
    throw firstErr;
  }
}
