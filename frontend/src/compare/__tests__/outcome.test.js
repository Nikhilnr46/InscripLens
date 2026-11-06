/**
 * Unit tests for outcome evaluation logic in glyph redrawing comparisons.
 */

import {
  evaluateComparisonOutcome,
  findRankInAlternatives,
  normalizeToKannada,
  getAlternativeKannada
} from '../outcome.js';

export function runOutcomeTests() {
  const results = [];
  function assert(cond, msg) {
    if (!cond) throw new Error(msg);
  }

  // 1. "improved" outcome: reading moves from rank 3 to rank 1
  {
    const proposed = { text: 'ಕ', script: 'kannada' };
    const auto = { alternatives: ['ಗ', 'ತ', 'ಕ'] }; // rank 3
    const redrawn = { alternatives: ['ಕ', 'ಪ', 'ಮ'] }; // rank 1
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'improved', `Expected improved, got ${res.outcome}`);
    assert(res.autoRank === 3, `Expected autoRank 3, got ${res.autoRank}`);
    assert(res.redrawnRank === 1, `Expected redrawnRank 1, got ${res.redrawnRank}`);
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome improved (rank 3 to rank 1)');
  }

  // 2. "improved" outcome: reading was not in top 3 in automatic, but enters at rank 2 in redrawn
  {
    const proposed = { text: 'ka', script: 'roman' }; // 'ಕ'
    const auto = { alternatives: ['ಗ', 'ತ', 'ಪ'] }; // not in top 3
    const redrawn = { alternatives: ['ಗ', 'ಕ', 'ತ'] }; // rank 2
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'improved', `Expected improved, got ${res.outcome}`);
    assert(res.autoRank === null, `Expected autoRank null, got ${res.autoRank}`);
    assert(res.redrawnRank === 2, `Expected redrawnRank 2, got ${res.redrawnRank}`);
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome improved (not in top 3 to rank 2)');
  }

  // 3. "worse" outcome: reading was rank 1 in auto, drops to rank 3 in redrawn
  {
    const proposed = { text: 'ಗ', script: 'kannada' };
    const auto = { alternatives: ['ಗ', 'ಕ', 'ತ'] }; // rank 1
    const redrawn = { alternatives: ['ಪ', 'ಮ', 'ಗ'] }; // rank 3
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'worse', `Expected worse, got ${res.outcome}`);
    assert(res.autoRank === 1, `Expected autoRank 1, got ${res.autoRank}`);
    assert(res.redrawnRank === 3, `Expected redrawnRank 3, got ${res.redrawnRank}`);
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome worse (rank 1 to rank 3)');
  }

  // 4. "worse" outcome: reading was rank 2 in auto, drops out of top 3 in redrawn
  {
    const proposed = { text: 'ga', script: 'roman' }; // 'ಗ'
    const auto = { alternatives: ['ಕ', 'ಗ', 'ತ'] }; // rank 2
    const redrawn = { alternatives: ['ಪ', 'ಮ', 'ದ'] }; // not in top 3
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'worse', `Expected worse, got ${res.outcome}`);
    assert(res.autoRank === 2, `Expected autoRank 2, got ${res.autoRank}`);
    assert(res.redrawnRank === null, `Expected redrawnRank null, got ${res.redrawnRank}`);
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome worse (rank 2 to not in top 3)');
  }

  // 5. "unchanged" outcome: reading is rank 1 in both
  {
    const proposed = { text: 'ಕ', script: 'kannada' };
    const auto = { alternatives: ['ಕ', 'ಗ', 'ತ'] }; // rank 1
    const redrawn = { alternatives: ['ಕ', 'ಪ', 'ಮ'] }; // rank 1
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'unchanged', `Expected unchanged, got ${res.outcome}`);
    assert(res.autoRank === 1, `Expected autoRank 1, got ${res.autoRank}`);
    assert(res.redrawnRank === 1, `Expected redrawnRank 1, got ${res.redrawnRank}`);
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome unchanged (rank 1 in both)');
  }

  // 6. "unknown" outcome: neither has reading in top 3
  {
    const proposed = { text: 'ಲ', script: 'kannada' };
    const auto = { alternatives: ['ಕ', 'ಗ', 'ತ'] };
    const redrawn = { alternatives: ['ಪ', 'ಮ', 'ದ'] };
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.outcome === 'unknown', `Expected unknown, got ${res.outcome}`);
    assert(res.autoRank === null && res.redrawnRank === null, 'Ranks should be null');
    assert(res.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome unknown (neither in top 3)');
  }

  // 7. "unknown" outcome: null or empty proposed reading
  {
    const auto = { alternatives: ['ಕ', 'ಗ', 'ತ'] };
    const redrawn = { alternatives: ['ಕ', 'ಪ', 'ಮ'] };

    const resNull = evaluateComparisonOutcome(null, auto, redrawn);
    assert(resNull.outcome === 'unknown', 'Null proposed reading should return unknown');
    assert(resNull.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');

    const resEmpty = evaluateComparisonOutcome({ text: '   ' }, auto, redrawn);
    assert(resEmpty.outcome === 'unknown', 'Whitespace proposed reading should return unknown');
    assert(resEmpty.rank_note.includes('Ranks beyond 3 are not available.'), 'Rank note suffix missing');
    results.push('PASS: Outcome unknown for empty or null proposed reading');
  }

  // 8. NFC normalization and object alternative formats
  {
    const proposed = { text: ' ಶ್ರೀ '.normalize('NFD'), script: 'kannada' };
    const auto = { alternatives: [{ label: 'ಶ್ರೀ'.normalize('NFC') }] };
    const redrawn = { alternatives: ['ಶ್ರೀ'] };
    const res = evaluateComparisonOutcome(proposed, auto, redrawn);

    assert(res.autoRank === 1 && res.redrawnRank === 1, 'NFC matching failed');
    assert(res.outcome === 'unchanged', 'NFC unchanged outcome failed');
    results.push('PASS: NFC normalization and object alternative formats');
  }

  return results;
}
