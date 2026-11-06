/**
 * Outcome evaluation logic for glyph redrawing comparisons.
 *
 * Compares an expert proposed reading against the top 3 ranked alternatives
 * returned by the character recognizer for the automatic candidate and the redrawn candidate.
 *
 * Adheres strictly to the task requirements:
 * - Rank is the position in the top 3 alternatives list (1 to 3) or "not in top 3" (null)
 * - Proposed reading is compared to the Kannada form of each alternative (NFC-normalised, trimmed)
 * - Roman readings are converted using the existing toKannada converter
 * - Outcome is strictly "improved", "worse", "unchanged", or "unknown"
 * - rank_note always states that ranks beyond 3 are not available
 */

import { toKannada } from '../utils/kannadaConverter.js';

const RANKS_NOTE_SUFFIX = 'Ranks beyond 3 are not available.';

/**
 * Normalise any text representation into trimmed, NFC-normalised Kannada script.
 *
 * @param {string} text - Raw input text (Roman transliteration or Kannada)
 * @param {string} [scriptHint] - Optional hint ("roman" | "kannada")
 * @returns {string} Trimmed, NFC-normalised Kannada Unicode string
 */
export function normalizeToKannada(text, scriptHint) {
  if (!text || typeof text !== 'string') return '';

  const trimmed = text.trim();
  if (!trimmed) return '';

  // Determine if text should be passed through Roman-to-Kannada converter
  const isRoman = scriptHint === 'roman' || /[a-zA-Z]/.test(trimmed);

  if (isRoman) {
    const converted = toKannada(trimmed);
    return (converted || '').normalize('NFC').trim();
  }

  return trimmed.normalize('NFC');
}

/**
 * Extract the normalised Kannada form of a single alternative entry.
 *
 * @param {string|Object} alt - Alternative from model response
 * @returns {string}
 */
export function getAlternativeKannada(alt) {
  if (!alt) return '';

  let label = '';
  if (typeof alt === 'string') {
    label = alt;
  } else if (typeof alt === 'object' && alt !== null) {
    label = alt.label || alt.prediction || alt.prediction_kannada || '';
  }

  return normalizeToKannada(label);
}

/**
 * Determine the rank (1, 2, or 3) of a target reading within a list of alternatives.
 *
 * @param {Array} alternatives - List of up to 3 alternatives from predict-crop
 * @param {string} targetKannada - Normalised Kannada form of proposed reading
 * @returns {number|null} 1, 2, 3 if found in top 3; null if not in top 3
 */
export function findRankInAlternatives(alternatives, targetKannada) {
  if (!Array.isArray(alternatives) || !targetKannada) {
    return null;
  }

  // Inspect only up to the first 3 alternatives
  const searchLimit = Math.min(3, alternatives.length);

  for (let idx = 0; idx < searchLimit; idx++) {
    const altKannada = getAlternativeKannada(alternatives[idx]);
    if (altKannada && altKannada === targetKannada) {
      return idx + 1; // 1-based rank (1 to 3)
    }
  }

  return null;
}

/**
 * Evaluate comparison outcome between automatic candidate and redrawn candidate.
 *
 * @param {{text: string, script?: string, tentative?: boolean}|null} proposedReading
 * @param {{alternatives?: Array}} automatic - Automatic candidate prediction result
 * @param {{alternatives?: Array}} redrawn - Redrawn candidate prediction result
 * @returns {{
 *   outcome: "improved"|"worse"|"unchanged"|"unknown",
 *   autoRank: number|null,
 *   redrawnRank: number|null,
 *   rank_note: string,
 *   proposedKannada: string
 * }}
 */
export function evaluateComparisonOutcome(proposedReading, automatic, redrawn) {
  const rawText = proposedReading?.text || '';
  const proposedKannada = normalizeToKannada(rawText, proposedReading?.script);

  const autoAlts = Array.isArray(automatic?.alternatives) ? automatic.alternatives : [];
  const redrawnAlts = Array.isArray(redrawn?.alternatives) ? redrawn.alternatives : [];

  if (!proposedKannada) {
    return {
      outcome: 'unknown',
      autoRank: null,
      redrawnRank: null,
      rank_note: `No proposed reading provided. ${RANKS_NOTE_SUFFIX}`,
      proposedKannada: ''
    };
  }

  const autoRank = findRankInAlternatives(autoAlts, proposedKannada);
  const redrawnRank = findRankInAlternatives(redrawnAlts, proposedKannada);

  // Case 1: Neither box contains the reading in top 3
  if (autoRank === null && redrawnRank === null) {
    return {
      outcome: 'unknown',
      autoRank: null,
      redrawnRank: null,
      rank_note: `Proposed reading not present in top 3 alternatives for either region. ${RANKS_NOTE_SUFFIX}`,
      proposedKannada
    };
  }

  // Case 2: Reading entered top 3 in redrawn region (was not in top 3 in automatic)
  if (autoRank === null && redrawnRank !== null) {
    return {
      outcome: 'improved',
      autoRank: null,
      redrawnRank,
      rank_note: `Proposed reading entered top 3 at rank #${redrawnRank} in redrawn region (was not in top 3 in automatic region). ${RANKS_NOTE_SUFFIX}`,
      proposedKannada
    };
  }

  // Case 3: Reading dropped out of top 3 in redrawn region
  if (autoRank !== null && redrawnRank === null) {
    return {
      outcome: 'worse',
      autoRank,
      redrawnRank: null,
      rank_note: `Proposed reading dropped out of top 3 in redrawn region (was rank #${autoRank} in automatic region). ${RANKS_NOTE_SUFFIX}`,
      proposedKannada
    };
  }

  // Case 4: Both regions ranked the reading within top 3 (compare numeric ranks)
  if (redrawnRank < autoRank) {
    return {
      outcome: 'improved',
      autoRank,
      redrawnRank,
      rank_note: `Proposed reading improved from rank #${autoRank} to #${redrawnRank}. ${RANKS_NOTE_SUFFIX}`,
      proposedKannada
    };
  }

  if (redrawnRank > autoRank) {
    return {
      outcome: 'worse',
      autoRank,
      redrawnRank,
      rank_note: `Proposed reading worsened from rank #${autoRank} to #${redrawnRank}. ${RANKS_NOTE_SUFFIX}`,
      proposedKannada
    };
  }

  return {
    outcome: 'unchanged',
    autoRank,
    redrawnRank,
    rank_note: `Proposed reading remained at rank #${autoRank} across both regions. ${RANKS_NOTE_SUFFIX}`,
    proposedKannada
  };
}
