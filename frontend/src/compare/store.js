/**
 * Comparison store for InscripLens Glyph Inspector.
 * Persists expert redraw comparisons into localStorage under the versioned key:
 *   "inscriplens.comparisons.v1"
 *
 * Adheres strictly to requirements:
 * - Every single localStorage access wrapped in try/catch
 * - Versioned schema (schema_version: 1)
 * - Operations: save, list (by run or all), delete, export
 * - Record holds: id, schema_version, saved_at, run_id, candidate_number, candidate_index,
 *   image_size, enhancement_mode, automatic, redrawn, proposed_reading, outcome, rank_note,
 *   plus two small 96px thumbnails
 * - Strictly never stores or leaks file paths
 * - Warns when storage is nearly full; never crashes on quota or corruption
 */

export const COMPARISONS_STORAGE_KEY = 'inscriplens.comparisons.v1';
export const CURRENT_SCHEMA_VERSION = 1;

// Approximate localStorage quota threshold for warnings (4 MB of typical 5 MB browser limit)
const STORAGE_WARNING_BYTES = 4 * 1024 * 1024;

/**
 * Check estimated localStorage storage usage and determine if storage is nearly full.
 *
 * @returns {{usedBytes: number, isNearlyFull: boolean, quotaEstimate: number}}
 */
export function getStorageUsage() {
  let usedBytes = 0;
  const quotaEstimate = 5 * 1024 * 1024; // 5 MB estimate

  try {
    if (typeof localStorage !== 'undefined') {
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key) {
          const val = localStorage.getItem(key) || '';
          usedBytes += (key.length + val.length) * 2; // UTF-16 characters = 2 bytes
        }
      }
    }
  } catch {
    // Graceful fallback
  }

  const isNearlyFull = usedBytes >= STORAGE_WARNING_BYTES;
  return {
    usedBytes,
    isNearlyFull,
    quotaEstimate
  };
}

/**
 * Safely parse raw JSON string from storage, handling corrupted JSON gracefully.
 *
 * @param {string|null} raw
 * @returns {Array} List of comparison records
 */
function safeParseComparisons(raw) {
  if (!raw || typeof raw !== 'string') {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      console.warn('InscripLens comparison store was not an array. Resetting to empty list.');
      return [];
    }
    // Filter and sanitize entries
    return parsed.filter(item => item && typeof item === 'object' && item.id);
  } catch (err) {
    console.warn('InscripLens comparison store encountered corrupted JSON. Recovering gracefully.', err);
    return [];
  }
}

/**
 * Sanitize a candidate sub-record (automatic or redrawn) to guarantee no internal file paths are stored.
 *
 * @param {Object} entry
 * @returns {Object}
 */
function sanitizeCandidateRecord(entry) {
  if (!entry || typeof entry !== 'object') {
    return {
      bbox: [0, 0, 0, 0],
      prediction: '',
      prediction_kannada: '',
      alternatives: [],
      confidence: null,
      model_sha256: ''
    };
  }

  const bbox = Array.isArray(entry.bbox) && entry.bbox.length === 4
    ? [Math.round(entry.bbox[0]), Math.round(entry.bbox[1]), Math.round(entry.bbox[2]), Math.round(entry.bbox[3])]
    : [0, 0, 0, 0];

  const alts = Array.isArray(entry.alternatives)
    ? entry.alternatives.map(a => (typeof a === 'object' && a !== null ? { label: String(a.label || '') } : String(a)))
    : [];

  return {
    bbox,
    prediction: String(entry.prediction || ''),
    prediction_kannada: String(entry.prediction_kannada || ''),
    alternatives: alts,
    confidence: typeof entry.confidence === 'number' ? entry.confidence : null,
    model_sha256: String(entry.model_sha256 || entry.modelSha256 || '')
  };
}

/**
 * List comparison records, optionally filtered by run ID.
 *
 * @param {string|null} [runId=null] - Optional run identifier to filter by
 * @returns {Array}
 */
export function listComparisons(runId = null) {
  try {
    if (typeof localStorage === 'undefined') return [];
    const raw = localStorage.getItem(COMPARISONS_STORAGE_KEY);
    const records = safeParseComparisons(raw);

    if (runId && typeof runId === 'string') {
      return records.filter(r => r.run_id === runId);
    }
    return records;
  } catch (err) {
    console.warn('Failed to retrieve comparisons from localStorage:', err);
    return [];
  }
}

/**
 * Retrieve a single comparison record by ID.
 *
 * @param {string} id
 * @returns {Object|null}
 */
export function getComparison(id) {
  if (!id) return null;
  const all = listComparisons();
  return all.find(item => item.id === id) || null;
}

/**
 * Save or update a comparison record in localStorage.
 *
 * @param {Object} record - The comparison record to save
 * @returns {{success: boolean, record?: Object, error?: string, storageWarning?: boolean}}
 */
export function saveComparison(record) {
  if (!record || typeof record !== 'object') {
    return { success: false, error: 'A valid comparison record object must be provided.' };
  }

  const usage = getStorageUsage();
  if (usage.isNearlyFull) {
    console.warn('InscripLens comparison storage is nearly full (>4MB used).');
  }

  try {
    const all = listComparisons();

    // Construct sanitized versioned record
    const id = record.id || `comp_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const candidateNumber = typeof record.candidate_number === 'number'
      ? record.candidate_number
      : (typeof record.candidate_index === 'number' ? record.candidate_index + 1 : 1);
    const candidateIndex = typeof record.candidate_index === 'number'
      ? record.candidate_index
      : Math.max(0, candidateNumber - 1);

    const imageSize = record.image_size && typeof record.image_size.width === 'number'
      ? { width: Math.round(record.image_size.width), height: Math.round(record.image_size.height) }
      : { width: 0, height: 0 };

    const proposedReading = record.proposed_reading && typeof record.proposed_reading === 'object'
      ? {
          text: String(record.proposed_reading.text || '').trim(),
          script: record.proposed_reading.script === 'roman' ? 'roman' : 'kannada',
          tentative: Boolean(record.proposed_reading.tentative)
        }
      : null;

    const autoRec = sanitizeCandidateRecord(record.automatic);
    const redrawnRec = sanitizeCandidateRecord(record.redrawn);
    const modelHashesDiffer = Boolean(
      autoRec.model_sha256 &&
      redrawnRec.model_sha256 &&
      autoRec.model_sha256 !== redrawnRec.model_sha256
    );

    const validatedRecord = {
      id,
      schema_version: CURRENT_SCHEMA_VERSION,
      saved_at: record.saved_at || new Date().toISOString(),
      timestamp: record.timestamp || record.saved_at || new Date().toISOString(),
      run_id: String(record.run_id || ''),
      candidate_number: candidateNumber,
      candidate_index: candidateIndex,
      image_size: imageSize,
      enhancement_mode: String(record.enhancement_mode || 'standard'),
      automatic: autoRec,
      redrawn: redrawnRec,
      model_hashes_differ: modelHashesDiffer,
      proposed_reading: proposedReading,
      outcome: ['improved', 'worse', 'unchanged', 'unknown'].includes(record.outcome)
        ? record.outcome
        : 'unknown',
      rank_note: String(record.rank_note || 'Ranks beyond 3 are not available.'),
      automatic_thumbnail: typeof record.automatic_thumbnail === 'string' ? record.automatic_thumbnail : '',
      redrawn_thumbnail: typeof record.redrawn_thumbnail === 'string' ? record.redrawn_thumbnail : ''
    };

    // Replace if exists, else append to front
    const existingIdx = all.findIndex(item => item.id === id);
    if (existingIdx >= 0) {
      all[existingIdx] = validatedRecord;
    } else {
      all.unshift(validatedRecord);
    }

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(COMPARISONS_STORAGE_KEY, JSON.stringify(all));
    }

    return {
      success: true,
      record: validatedRecord,
      storageWarning: usage.isNearlyFull
    };
  } catch (err) {
    const isQuota = err && (err.name === 'QuotaExceededError' || err.code === 22 || err.code === 1014);
    const errorMsg = isQuota
      ? 'Storage quota exceeded. Please export or delete older comparisons to free up space.'
      : (err.message || 'Failed to save comparison to local storage.');

    console.warn('Error saving comparison record:', errorMsg);
    return {
      success: false,
      error: errorMsg,
      storageFull: isQuota
    };
  }
}

/**
 * Delete a comparison record by its ID.
 *
 * @param {string} id - Record ID to delete
 * @returns {boolean} True if successfully removed
 */
export function deleteComparison(id) {
  if (!id) return false;

  try {
    const all = listComparisons();
    const filtered = all.filter(item => item.id !== id);
    if (filtered.length === all.length) {
      return false; // Record was not present
    }

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(COMPARISONS_STORAGE_KEY, JSON.stringify(filtered));
    }
    return true;
  } catch (err) {
    console.warn('Failed to delete comparison record from localStorage:', err);
    return false;
  }
}

/**
 * Export comparisons formatted as a clean JSON string, strictly excluding any internal file paths or crop URLs.
 *
 * @param {string|null} [runId=null] - Optional run ID filter
 * @returns {string} Formatted JSON string
 */
export function exportComparisons(runId = null) {
  const records = listComparisons(runId);
  const cleanRecords = records.map(r => ({
    id: r.id,
    run_id: r.run_id,
    candidate_number: r.candidate_number,
    candidate_index: r.candidate_index,
    image_size: r.image_size,
    enhancement_mode: r.enhancement_mode,
    automatic: {
      bbox: r.automatic.bbox,
      prediction: r.automatic.prediction,
      prediction_kannada: r.automatic.prediction_kannada,
      alternatives: r.automatic.alternatives,
      confidence: r.automatic.confidence,
      model_sha256: r.automatic.model_sha256
    },
    redrawn: {
      bbox: r.redrawn.bbox,
      prediction: r.redrawn.prediction,
      prediction_kannada: r.redrawn.prediction_kannada,
      alternatives: r.redrawn.alternatives,
      confidence: r.redrawn.confidence,
      model_sha256: r.redrawn.model_sha256
    },
    model_hashes_differ: Boolean(r.model_hashes_differ),
    proposed_reading: r.proposed_reading || { text: '', script: 'kannada', tentative: true },
    outcome: r.outcome,
    rank_note: r.rank_note,
    timestamp: r.saved_at || r.timestamp
  }));

  const payload = {
    software_name: 'InscripLens',
    schema_version: CURRENT_SCHEMA_VERSION,
    export_date: new Date().toISOString(),
    count: cleanRecords.length,
    run_filter: runId || null,
    records: cleanRecords
  };

  return JSON.stringify(payload, null, 2);
}

/**
 * Triggers a client-side browser download for the comparison records JSON.
 * Produces a file named `inscriplens-comparisons-<date>.json`.
 *
 * @param {string|null} [runId=null] - Optional run ID filter
 */
export function downloadComparisonsJson(runId = null) {
  if (typeof document === 'undefined') return;
  const jsonStr = exportComparisons(runId);
  const dateStr = new Date().toISOString().slice(0, 10);
  const filename = `inscriplens-comparisons-${dateStr}.json`;

  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Clear all stored comparisons (useful for test resets).
 *
 * @returns {boolean}
 */
export function clearComparisons() {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(COMPARISONS_STORAGE_KEY);
    }
    return true;
  } catch {
    return false;
  }
}
