# InscripLens Recognizer Class Roman-to-Kannada Mapping Report

## 1. Summary Statistics
- Total unique recognizer classes: 764
- Successfully mapped to Kannada Unicode NFC: 751 (98.30%)
- Unmapped or ambiguous classes: 13 (1.70%)
- NFC Normalization: 100% verified across all mapped characters

## 2. Unmapped / Ambiguous Labels Audit

In accordance with strict epigraphic guidelines, any label that cannot be converted with 100% certainty is preserved in its original Roman transliteration and marked with a small `[Roman]` badge in the user interface rather than guessed.

| Label | Reason for Withholding Conversion | Category |
|---|---|---|
| `ISymbol` | Dataset non-phonetic bounding box symbol | Dataset artifact |
| `symbol` | Dataset non-phonetic glyph placeholder | Dataset artifact |
| `I` | Ambiguous capital letter I / Roman numeral I / symbol | Ambiguous glyph |
| `chy` | Truncated consonant cluster ending in semivowel `y` without vowel | Ambiguous fragment |
| `stam` | Ends in ASCII `m` without anusvara diacritic; ambiguous between `ಸ್ತಂ` and `ಸ್ತಮ್` | Ambiguous orthography |
| `l` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |
| `ll` | Geminate consonant with no vowel or virama annotated | Ambiguous consonant |
| `l̤` | Archaic retroflex consonant without vowel or virama annotated | Ambiguous consonant |
| `m` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |
| `n` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |
| `r` | Isolated liquid consonant without vowel or virama annotated | Ambiguous consonant |
| `t` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |
| `ṇ` (ṇ) | Isolated retroflex nasal without vowel or virama annotated | Ambiguous consonant |

## 3. Sample Mapped Categories

| Category | Roman Sample | Kannada Unicode NFC | Codepoints |
|---|---|---|---|
| Inherent vowel | `ka` | `ಕ` | U+0C95 |
| Independent vowel | `a`, `ā`, `ĕ`, `e` | `ಅ`, `ಆ`, `ಎ`, `ಏ` | U+0C85, U+0C86, U+0C8E, U+0C8F |
| Short vowel signs | `kĕ`, `kŏ` | `ಕೆ`, `ಕೊ` | U+0C95+U+0CC6, U+0C95+U+0CCA |
| Long vowel signs | `ke`, `ko`, `śrī` | `ಕೇ`, `ಕೋ`, `ಶ್ರೀ` | U+0C95+U+0CC7, U+0C95+U+0CCB, U+0CB6+U+0CCD+U+0CB0+U+0CC0 |
| Vocalic ṛ | `pṛ` | `ಪೃ` | U+0CAA+U+0CC3 |
| Archaic ṟ | `ṟĕ` | `ಱೆ` | U+0CB1+U+0CC6 |
| Archaic ḻ | `ḻa`, `l̤a` | `ೞ` | U+0CDE |
| Anusvara | `kaṃ`, `aṃ`, `ṃda` | `ಕಂ`, `ಅಂ`, `ಂದ` | U+0C95+U+0C82, U+0C85+U+0C82, U+0C82+U+0CA6 |
| Visarga | `kaḥ`, `śrīḥ` | `ಕಃ`, `ಶ್ರೀಃ` | U+0C95+U+0C83, U+0CB6+U+0CCD+U+0CB0+U+0CC0+U+0C83 |
| Consonant clusters | `kkĕ`, `sva`, `nda` | `ಕ್ಕೆ`, `ಸ್ವ`, `ನ್ದ` | U+0C95+U+0CCD+U+0C95+U+0CC6, U+0CB8+U+0CCD+U+0CB5, U+0CA8+U+0CCD+U+0CA6 |
| Opening invocation | `siddhaṃ` | `ಸಿದ್ಧಂ` | U+0CB8+U+0CBF+U+0CA6+U+0CCD+U+0CA7+U+0C82 |
| Numerals | `0` through `9` | `೦` through `೯` | U+0CE6 through U+0CEF |
