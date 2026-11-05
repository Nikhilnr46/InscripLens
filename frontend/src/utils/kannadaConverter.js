/**
 * Roman transliteration to Kannada script converter for InscripLens.
 * Display-only conversion: never modifies stored transliterations or backend records.
 * Ensures Unicode NFC normalization and supports archaic to modern letter substitution.
 */

// Consonant definitions (ordered by longest match first)
const CONSONANTS = [
  ['kh', '\u0C96'],       // ಖ
  ['gh', '\u0C98'],       // ಘ
  ['ch', '\u0C9B'],       // ಛ
  ['jh', '\u0C9D'],       // ಝ
  ['\u1E6Dh', '\u0CA0'],  // ಠ (ṭh)
  ['\u1E0Dh', '\u0CA2'],  // ಢ (ḍh)
  ['th', '\u0CA5'],       // ಥ
  ['dh', '\u0CA7'],       // ಧ
  ['ph', '\u0CAB'],       // ಫ
  ['bh', '\u0CAD'],       // ಭ
  ['l\u0324', '\u0CDE'],  // ೞ (archaic l̤ / ḻ)
  ['k', '\u0C95'],        // ಕ
  ['g', '\u0C97'],        // ಗ
  ['\u1E45', '\u0C99'],   // ಙ (ṅ)
  ['c', '\u0C9A'],        // ಚ
  ['j', '\u0C9C'],        // ಜ
  ['\u00F1', '\u0C9E'],   // ಞ (ñ)
  ['\u1E6D', '\u0C9F'],   // ಟ (ṭ)
  ['\u1E0D', '\u0CA1'],   // ಡ (ḍ)
  ['\u1E47', '\u0CA3'],   // ಣ (ṇ)
  ['t', '\u0CA4'],        // ತ
  ['d', '\u0CA6'],        // ದ
  ['n', '\u0CA8'],        // ನ
  ['p', '\u0CAA'],        // ಪ
  ['b', '\u0CAC'],        // ಬ
  ['m', '\u0CAE'],        // ಮ
  ['y', '\u0CAF'],        // ಯ
  ['r', '\u0CB0'],        // ರ
  ['\u1E5F', '\u0CB1'],   // ಱ (ṟ - archaic r)
  ['l', '\u0CB2'],        // ಲ
  ['\u1E37', '\u0CB3'],   // ಳ (ḷ)
  ['\u1E3B', '\u0CDE'],   // ೞ (ḻ - archaic l)
  ['v', '\u0CB5'],        // ವ
  ['\u015B', '\u0CB6'],   // ಶ (ś)
  ['\u1E63', '\u0CB7'],   // ಷ (ṣ)
  ['s', '\u0CB8'],        // ಸ
  ['h', '\u0CB9']         // ಹ
];

// Independent vowels
const INDEPENDENT_VOWELS = [
  ['ai', '\u0C90'],       // ಐ
  ['au', '\u0C94'],       // ಔ
  ['a', '\u0C85'],        // ಅ
  ['\u0101', '\u0C86'],   // ಆ (ā)
  ['i', '\u0C87'],        // ಇ
  ['\u012B', '\u0C88'],   // ಈ (ī)
  ['u', '\u0C89'],        // ಉ
  ['\u016B', '\u0C8A'],   // ಊ (ū)
  ['\u1E5B', '\u0C8B'],   // ಋ (ṛ)
  ['\u0115', '\u0C8E'],   // ಎ (ĕ - short e)
  ['e', '\u0C8F'],        // ಏ (e - long e)
  ['\u0113', '\u0C8F'],   // ಏ (ē - long e)
  ['\u014F', '\u0C92'],   // ಒ (ŏ - short o)
  ['o', '\u0C93'],        // ಓ (o - long o)
  ['\u014D', '\u0C93']    // ಓ (ō - long o)
];

// Dependent vowel signs (matras attached to consonants)
const VOWEL_SIGNS = [
  ['ai', '\u0CC8'],       // ೈ
  ['au', '\u0CCC'],       // ೌ
  ['\u0101', '\u0CBE'],   // ಾ (ā)
  ['i', '\u0CBF'],        // ಿ
  ['\u012B', '\u0CC0'],   // ೀ (ī)
  ['u', '\u0CC1'],        // ು
  ['\u016B', '\u0CC2'],   // ೂ (ū)
  ['\u1E5B', '\u0CC3'],   // ೃ (ṛ)
  ['\u0115', '\u0CC6'],   // ೆ (ĕ - short e)
  ['e', '\u0CC7'],        // ೇ (e - long e)
  ['\u0113', '\u0CC7'],   // ೇ (ē - long e)
  ['\u014F', '\u0CCA'],   // ೊ (ŏ - short o)
  ['o', '\u0CCB'],        // ೋ (o - long o)
  ['\u014D', '\u0CCB'],   // ೋ (ō - long o)
  ['a', '']               // inherent vowel
];

// Modifiers
const MODIFIERS = [
  ['\u1E43', '\u0C82'],   // ಂ (ṃ - anusvara)
  ['\u1E25', '\u0C83']    // ಃ (ḥ - visarga)
];

const VIRAMA = '\u0CCD';   // ್ (virama / halant)

// Special exact word and number mappings
const SPECIAL_MAPPINGS = {
  'siddha\u1E43': '\u0CB8\u0CBF\u0CA6\u0CCD\u0CA7\u0C82', // ಸಿದ್ಧಂ
  '\u1E43': '\u0C82',     // ಂ
  '\u0C84': '\u0C84',     // ಄
  '\u0CE6': '\u0CE6',     // ೦
  '0': '\u0CE6', '1': '\u0CE7', '2': '\u0CE8', '3': '\u0CE9', '4': '\u0CEA',
  '5': '\u0CEB', '6': '\u0CEC', '7': '\u0CED', '8': '\u0CEE', '9': '\u0CEF'
};

// Archaic to modern letter mappings
const ARCHAIC_TO_MODERN = {
  '\u0CB1': '\u0CB0',     // ಱ -> ರ
  '\u0CDE': '\u0CB3'      // ೞ -> ಳ
};

/**
 * Convert Roman transliterated string to Kannada script in Unicode NFC.
 * Returns null if string cannot be converted with certainty.
 */
export function toKannada(text) {
  if (!text || typeof text !== 'string') return null;

  const trimmed = text.trim().normalize('NFC');
  if (!trimmed) return null;

  if (SPECIAL_MAPPINGS[trimmed]) {
    return SPECIAL_MAPPINGS[trimmed].normalize('NFC');
  }

  // Handle leading anusvara (e.g. ṃda -> ಂದ)
  let prefix = '';
  let s = trimmed;
  if (s.startsWith('\u1E43')) {
    prefix = '\u0C82';
    s = s.slice(1);
  }

  // Strip trailing anusvara or visarga
  let mod = '';
  for (const [mRom, mKan] of MODIFIERS) {
    if (s.endsWith(mRom)) {
      mod = mKan;
      s = s.slice(0, -mRom.length);
      break;
    }
  }

  // Check independent vowel
  for (const [vRom, vKan] of INDEPENDENT_VOWELS) {
    if (s === vRom) {
      return (prefix + vKan + mod).normalize('NFC');
    }
  }

  // Check consonant cluster + vowel sign
  for (const [vRom, vMatra] of VOWEL_SIGNS) {
    if (s.endsWith(vRom)) {
      const remCons = s.slice(0, -vRom.length);
      if (!remCons) continue;

      let idx = 0;
      const consList = [];
      let valid = true;

      while (idx < remCons.length) {
        let matched = false;
        for (const [cRom, cKan] of CONSONANTS) {
          if (remCons.startsWith(cRom, idx)) {
            consList.push(cKan);
            idx += cRom.length;
            matched = true;
            break;
          }
        }
        if (!matched) {
          valid = false;
          break;
        }
      }

      if (valid && consList.length > 0) {
        let res = '';
        for (let i = 0; i < consList.length; i++) {
          if (i > 0) res += VIRAMA;
          res += consList[i];
        }
        res += vMatra + mod;
        return (prefix + res).normalize('NFC');
      }
    }
  }

  return null;
}

/**
 * Replace archaic Kannada letters (ಱ, ೞ) with modern equivalents (ರ, ಳ).
 * Returns { text: string, isLossy: boolean }
 */
export function toModernKannada(kannadaText) {
  if (!kannadaText || typeof kannadaText !== 'string') {
    return { text: kannadaText, isLossy: false };
  }

  let isLossy = false;
  let result = '';

  for (const ch of kannadaText) {
    if (ARCHAIC_TO_MODERN[ch]) {
      result += ARCHAIC_TO_MODERN[ch];
      isLossy = true;
    } else {
      result += ch;
    }
  }

  return {
    text: result.normalize('NFC'),
    isLossy
  };
}

/**
 * Format label for display according to active script switch settings.
 * Returns {
 *   primary: string,
 *   secondary: string | null,
 *   isLossy: boolean,
 *   isUnmapped: boolean,
 *   roman: string,
 *   kannada: string | null
 * }
 */
export function formatDisplayLabel(romanLabel, scriptMode = 'kannada', modernLetters = false) {
  if (!romanLabel) {
    return {
      primary: '·',
      secondary: null,
      isLossy: false,
      isUnmapped: false,
      roman: '',
      kannada: null
    };
  }

  const rawKannada = toKannada(romanLabel);

  if (rawKannada === null) {
    // Unmapped: show Roman with small marker
    return {
      primary: romanLabel,
      secondary: null,
      isLossy: false,
      isUnmapped: true,
      roman: romanLabel,
      kannada: null
    };
  }

  let displayKannada = rawKannada;
  let isLossy = false;

  if (modernLetters) {
    const modern = toModernKannada(rawKannada);
    displayKannada = modern.text;
    isLossy = modern.isLossy;
  }

  if (scriptMode === 'roman') {
    return {
      primary: romanLabel,
      secondary: null,
      isLossy: false,
      isUnmapped: false,
      roman: romanLabel,
      kannada: displayKannada
    };
  }

  // scriptMode === 'kannada'
  return {
    primary: displayKannada,
    secondary: romanLabel,
    isLossy,
    isUnmapped: false,
    roman: romanLabel,
    kannada: displayKannada
  };
}

