/**
 * Unit tests for comparison store (localStorage integration, error handling, quota guard).
 */

import {
  saveComparison,
  listComparisons,
  getComparison,
  deleteComparison,
  exportComparisons,
  clearComparisons,
  getStorageUsage,
  COMPARISONS_STORAGE_KEY,
  CURRENT_SCHEMA_VERSION
} from '../store.js';

/**
 * Mock localStorage implementation for unit testing.
 */
export class MockLocalStorage {
  constructor() {
    this.store = {};
    this.shouldThrowQuota = false;
  }
  getItem(key) {
    return Object.prototype.hasOwnProperty.call(this.store, key) ? this.store[key] : null;
  }
  setItem(key, val) {
    if (this.shouldThrowQuota) {
      const err = new Error('QuotaExceededError');
      err.name = 'QuotaExceededError';
      err.code = 22;
      throw err;
    }
    this.store[key] = String(val);
  }
  removeItem(key) {
    delete this.store[key];
  }
  clear() {
    this.store = {};
  }
  get length() {
    return Object.keys(this.store).length;
  }
  key(idx) {
    return Object.keys(this.store)[idx] || null;
  }
}

export function runStoreTests() {
  const results = [];
  function assert(cond, msg) {
    if (!cond) throw new Error(msg);
  }

  // Set up mock localStorage
  const mockStorage = new MockLocalStorage();
  const originalLocalStorage = globalThis.localStorage;
  globalThis.localStorage = mockStorage;

  try {
    // 1. Save and retrieve a complete record
    {
      mockStorage.clear();
      const sample = {
        id: 'test_comp_1',
        run_id: 'run_nagavara_01',
        candidate_number: 16,
        candidate_index: 15,
        image_size: { width: 525, height: 1080 },
        enhancement_mode: 'standard',
        automatic: {
          bbox: [265, 147, 287, 173],
          prediction: 'ka',
          prediction_kannada: 'ಕ',
          alternatives: ['ka', 'ga', 'ta'],
          confidence: 0.82,
          model_sha256: 'sha256_mock_hash'
        },
        redrawn: {
          bbox: [263, 145, 289, 175],
          prediction: 'ka',
          prediction_kannada: 'ಕ',
          alternatives: ['ka', 'ta', 'pa'],
          confidence: 0.91,
          model_sha256: 'sha256_mock_hash'
        },
        proposed_reading: {
          text: 'ಕ',
          script: 'kannada',
          tentative: true
        },
        outcome: 'improved',
        rank_note: 'Proposed reading improved from rank #3 to #1. Ranks beyond 3 are not available.',
        automatic_thumbnail: 'data:image/jpeg;base64,mockauto',
        redrawn_thumbnail: 'data:image/jpeg;base64,mockredrawn'
      };

      const saveRes = saveComparison(sample);
      assert(saveRes.success === true, 'Save failed');
      assert(saveRes.record.schema_version === CURRENT_SCHEMA_VERSION, 'Schema version mismatch');

      const retrieved = getComparison('test_comp_1');
      assert(retrieved !== null, 'Could not retrieve saved record');
      assert(retrieved.candidate_number === 16, 'Candidate number mismatch');
      assert(retrieved.automatic.bbox[0] === 265, 'Bbox x1 mismatch');
      assert(retrieved.outcome === 'improved', 'Outcome mismatch');
      results.push('PASS: Save and retrieve comparison record');
    }

    // 2. List filtering by run ID
    {
      mockStorage.clear();
      saveComparison({ id: 'rec_1', run_id: 'run_A', candidate_number: 1 });
      saveComparison({ id: 'rec_2', run_id: 'run_B', candidate_number: 2 });
      saveComparison({ id: 'rec_3', run_id: 'run_A', candidate_number: 3 });

      const all = listComparisons();
      assert(all.length === 3, `Expected 3 records, got ${all.length}`);

      const runA = listComparisons('run_A');
      assert(runA.length === 2, `Expected 2 records for run_A, got ${runA.length}`);

      const runB = listComparisons('run_B');
      assert(runB.length === 1, `Expected 1 record for run_B, got ${runB.length}`);
      results.push('PASS: List comparisons with run_id filtering');
    }

    // 3. Delete record
    {
      const delSuccess = deleteComparison('rec_2');
      assert(delSuccess === true, 'Delete failed');
      assert(getComparison('rec_2') === null, 'Deleted record still present');
      assert(listComparisons().length === 2, 'Count mismatch after delete');
      results.push('PASS: Delete comparison record');
    }

    // 4. Export comparisons as clean JSON (strictly no file paths)
    {
      const exportedJson = exportComparisons('run_A');
      const parsed = JSON.parse(exportedJson);
      assert(parsed.total_comparisons === 2, 'Export total mismatch');
      assert(parsed.run_filter === 'run_A', 'Run filter mismatch in export');
      assert(!exportedJson.includes('/home/') && !exportedJson.includes('C:\\'), 'Detected filesystem path in export');
      results.push('PASS: Export comparisons as clean JSON');
    }

    // 5. Corrupted JSON handling in localStorage
    {
      mockStorage.setItem(COMPARISONS_STORAGE_KEY, '{ invalid JSON ::: corrupt');
      const recoveredList = listComparisons();
      assert(Array.isArray(recoveredList), 'Corrupt JSON should return array');
      assert(recoveredList.length === 0, 'Corrupt JSON should return empty array');

      // Saving after corrupt JSON should succeed and overwrite with valid JSON
      const saveAfterCorrupt = saveComparison({ id: 'after_corrupt', run_id: 'run_test' });
      assert(saveAfterCorrupt.success === true, 'Save after corrupt failed');
      assert(listComparisons().length === 1, 'Failed to recover store after corruption');
      results.push('PASS: Corrupted JSON recovery without crashing');
    }

    // 6. Full storage / QuotaExceededError handling
    {
      mockStorage.shouldThrowQuota = true;
      const quotaRes = saveComparison({ id: 'quota_overflow', run_id: 'run_test' });
      assert(quotaRes.success === false, 'Quota exceed should report success: false');
      assert(quotaRes.storageFull === true, 'storageFull flag should be true');
      assert(typeof quotaRes.error === 'string', 'Error message missing on quota exceed');
      mockStorage.shouldThrowQuota = false;
      results.push('PASS: QuotaExceededError handled gracefully without crashing');
    }

    // 7. Clear all comparisons
    {
      clearComparisons();
      assert(listComparisons().length === 0, 'Clear failed');
      results.push('PASS: Clear all comparisons');
    }
  } finally {
    globalThis.localStorage = originalLocalStorage;
  }

  return results;
}
