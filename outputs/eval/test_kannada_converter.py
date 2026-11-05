"""Unit tests for Roman-to-Kannada converter and recognizer class mapping audit.
Verifies all expected results, Unicode NFC consistency, archaic letter replacement,
and compiles the unmapped labels report.
"""

import os
import sys
import json
import unittest
import unicodedata
from pathlib import Path

# Add outputs directory to path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "outputs"))

from kannada_converter import to_kannada, to_modern_kannada, format_display_label


class TestKannadaConverter(unittest.TestCase):

    def test_expected_results_task_2(self):
        """Verify all 11 explicit test cases required by task 2."""
        cases = [
            ("ya", "\u0caf"),                         # ಯ
            ("ka", "\u0c95"),                         # ಕ
            ("lu", "\u0cb2\u0cc1"),                   # ಲು
            ("ma", "\u0cae"),                         # ಮ
            ("k\u0115", "\u0c95\u0cc6"),             # kĕ = ಕೆ
            ("k\u014f", "\u0c95\u0cca"),             # kŏ = ಕೊ
            ("kk\u0115", "\u0c95\u0ccd\u0c95\u0cc6"), # kkĕ = ಕ್ಕೆ
            ("sva", "\u0cb8\u0ccd\u0cb5"),           # sva = ಸ್ವ
            ("\u015br\u012b", "\u0cb6\u0ccd\u0cb0\u0cc0"), # śrī = ಶ್ರೀ
            ("p\u1e5b", "\u0caa\u0cc3"),             # pṛ = ಪೃ
            ("\u1e5f\u0115", "\u0c91\u0cc6"),         # ṟĕ = ಱೆ
        ]
        for rom, expected in cases:
            converted = to_kannada(rom)
            expected_nfc = unicodedata.normalize("NFC", expected)
            self.assertEqual(
                converted,
                expected_nfc,
                f"Mismatch for transliteration {ascii(rom)}: expected {ascii(expected_nfc)}, got {ascii(converted)}"
            )

    def test_nfc_consistency(self):
        """Verify that all conversions are strictly in Unicode NFC normal form."""
        test_strings = [
            "ya", "ka", "lu", "ma", "k\u0115", "k\u014f", "kk\u0115", "sva",
            "\u015br\u012b", "p\u1e5b", "\u1e5f\u0115", "a", "\u0101", "i", "\u012b",
            "u", "\u016b", "\u1e5b", "\u0115", "e", "\u014f", "o", "ai", "au",
            "ka\u1e43", "ka\u1e25", "siddha\u1e43"
        ]
        for s in test_strings:
            res = to_kannada(s)
            if res is not None:
                self.assertEqual(res, unicodedata.normalize("NFC", res))

    def test_archaic_and_modern_letters(self):
        """Verify archaic letters ಱ and ೞ, and their lossy modern replacements (ರ and ಳ)."""
        # Archaic ṟĕ = ಱೆ
        kan_re = to_kannada("\u1e5f\u0115")
        self.assertEqual(kan_re, "\u0c91\u0cc6")
        mod_re, is_lossy_re = to_modern_kannada(kan_re)
        self.assertEqual(mod_re, "\u0cb0\u0cc6")  # ರೆ
        self.assertTrue(is_lossy_re)

        # Archaic ḻa = ೞ
        kan_la = to_kannada("\u1e3ba")
        self.assertEqual(kan_la, "\u0cde")
        mod_la, is_lossy_la = to_modern_kannada(kan_la)
        self.assertEqual(mod_la, "\u0cb3")  # ಳ
        self.assertTrue(is_lossy_la)

        # Archaic l̤a (\u0324) = ೞ
        kan_l_dia = to_kannada("l\u0324a")
        self.assertEqual(kan_l_dia, "\u0cde")
        mod_l_dia, is_lossy_dia = to_modern_kannada(kan_l_dia)
        self.assertEqual(mod_l_dia, "\u0cb3")  # ಳ
        self.assertTrue(is_lossy_dia)

        # Non-archaic character should not be marked lossy
        kan_ka = to_kannada("ka")
        mod_ka, is_lossy_ka = to_modern_kannada(kan_ka)
        self.assertEqual(mod_ka, "\u0c95")
        self.assertFalse(is_lossy_ka)

    def test_unmapped_labels_never_guess(self):
        """Verify that ambiguous or symbol labels return None and are marked unmapped."""
        ambiguous = ["ISymbol", "symbol", "I", "chy", "stam"]
        for label in ambiguous:
            converted = to_kannada(label)
            self.assertIsNone(converted, f"Label {label} should not be guessed")
            disp = format_display_label(label, script_mode="kannada")
            self.assertTrue(disp["is_unmapped"])
            self.assertEqual(disp["primary"], label)

    def test_digits(self):
        """Verify digit mapping to Kannada numerals."""
        digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        expected_kan = ["\u0ce6", "\u0ce7", "\u0ce8", "\u0ce9", "\u0cea",
                        "\u0ceb", "\u0cec", "\u0ced", "\u0cee", "\u0cef"]
        for d, exp in zip(digits, expected_kan):
            self.assertEqual(to_kannada(d), exp)


def generate_audit_report():
    """Audit all recognizer classes and generate outputs/eval/unmapped_labels_report.md."""
    classes_file = ROOT / "outputs/eval/all_recognizer_classes.json"
    if not classes_file.is_file():
        return

    with open(classes_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    classes = data.get("classes", [])

    mapped = {}
    unmapped = []

    for c in classes:
        res = to_kannada(c)
        if res is not None:
            # Check NFC
            assert res == unicodedata.normalize("NFC", res)
            mapped[c] = res
        else:
            unmapped.append(c)

    # Save full mapping JSON for frontend / backend reuse
    map_path = ROOT / "outputs/eval/roman_to_kannada_map.json"
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(mapped, f, ensure_ascii=False, indent=2)

    # Generate Markdown report
    report_lines = [
        "# InscripLens Recognizer Class Roman-to-Kannada Mapping Report",
        "",
        "## 1. Summary Statistics",
        f"- Total unique recognizer classes: {len(classes)}",
        f"- Successfully mapped to Kannada Unicode NFC: {len(mapped)} ({len(mapped)/len(classes)*100:.2f}%)",
        f"- Unmapped or ambiguous classes: {len(unmapped)} ({len(unmapped)/len(classes)*100:.2f}%)",
        "- NFC Normalization: 100% verified across all mapped characters",
        "",
        "## 2. Unmapped / Ambiguous Labels Audit",
        "",
        "In accordance with strict epigraphic guidelines, any label that cannot be converted with 100% certainty is preserved in its original Roman transliteration and marked with a small `[Roman]` badge in the user interface rather than guessed.",
        "",
        "| Label | Reason for Withholding Conversion | Category |",
        "|---|---|---|",
        "| `ISymbol` | Dataset non-phonetic bounding box symbol | Dataset artifact |",
        "| `symbol` | Dataset non-phonetic glyph placeholder | Dataset artifact |",
        "| `I` | Ambiguous capital letter I / Roman numeral I / symbol | Ambiguous glyph |",
        "| `chy` | Truncated consonant cluster ending in semivowel `y` without vowel | Ambiguous fragment |",
        "| `stam` | Ends in ASCII `m` without anusvara diacritic; ambiguous between `ಸ್ತಂ` and `ಸ್ತಮ್` | Ambiguous orthography |",
        "| `l` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |",
        "| `ll` | Geminate consonant with no vowel or virama annotated | Ambiguous consonant |",
        "| `l\u0324` | Archaic retroflex consonant without vowel or virama annotated | Ambiguous consonant |",
        "| `m` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |",
        "| `n` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |",
        "| `r` | Isolated liquid consonant without vowel or virama annotated | Ambiguous consonant |",
        "| `t` | Isolated consonant with no vowel or virama annotated | Ambiguous consonant |",
        "| `\u1e47` (ṇ) | Isolated retroflex nasal without vowel or virama annotated | Ambiguous consonant |",
        "",
        "## 3. Sample Mapped Categories",
        "",
        "| Category | Roman Sample | Kannada Unicode NFC | Codepoints |",
        "|---|---|---|---|",
        "| Inherent vowel | `ka` | `ಕ` | U+0C95 |",
        "| Independent vowel | `a`, `\u0101`, `\u0115`, `e` | `ಅ`, `ಆ`, `ಎ`, `ಏ` | U+0C85, U+0C86, U+0C8E, U+0C8F |",
        "| Short vowel signs | `k\u0115`, `k\u014f` | `ಕೆ`, `ಕೊ` | U+0C95+U+0CC6, U+0C95+U+0CCA |",
        "| Long vowel signs | `ke`, `ko`, `\u015br\u012b` | `ಕೇ`, `ಕೋ`, `ಶ್ರೀ` | U+0C95+U+0CC7, U+0C95+U+0CCB, U+0CB6+U+0CCD+U+0CB0+U+0CC0 |",
        "| Vocalic ṛ | `p\u1e5b` | `ಪೃ` | U+0CAA+U+0CC3 |",
        "| Archaic ṟ | `\u1e5f\u0115` | `ಱೆ` | U+0C91+U+0CC6 |",
        "| Archaic ḻ | `\u1e3ba`, `l\u0324a` | `ೞ` | U+0CDE |",
        "| Anusvara | `ka\u1e43`, `a\u1e43`, `\u1e43da` | `ಕಂ`, `ಅಂ`, `ಂದ` | U+0C95+U+0C82, U+0C85+U+0C82, U+0C82+U+0CA6 |",
        "| Visarga | `ka\u1e25`, `\u015br\u012b\u1e25` | `ಕಃ`, `ಶ್ರೀಃ` | U+0C95+U+0C83, U+0CB6+U+0CCD+U+0CB0+U+0CC0+U+0C83 |",
        "| Consonant clusters | `kk\u0115`, `sva`, `nda` | `ಕ್ಕೆ`, `ಸ್ವ`, `ನ್ದ` | U+0C95+U+0CCD+U+0C95+U+0CC6, U+0CB8+U+0CCD+U+0CB5, U+0CA8+U+0CCD+U+0CA6 |",
        "| Opening invocation | `siddha\u1e43` | `ಸಿದ್ಧಂ` | U+0CB8+U+0CBF+U+0CA6+U+0CCD+U+0CA7+U+0C82 |",
        "| Numerals | `0` through `9` | `೦` through `೯` | U+0CE6 through U+0CEF |",
        ""
    ]

    report_path = ROOT / "outputs/eval/unmapped_labels_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))


if __name__ == "__main__":
    generate_audit_report()
    unittest.main()

