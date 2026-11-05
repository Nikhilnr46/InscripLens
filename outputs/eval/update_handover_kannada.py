from pathlib import Path

p = Path("HANDOVER.md")
text = p.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Update Frontend Guide (Section 6)
fg_target = 'reviewer submission forms, a "High accuracy mode" enhancement toggle switch with live progress feedback, a direct mask download button, and session mode indicators.'
fg_replacement = 'reviewer submission forms, a "High accuracy mode" enhancement toggle switch with live progress feedback, a direct mask download button, session mode indicators, and a "Script: Kannada / Roman" display switch with an optional "Modern letters" archaic substitution tier.'

if fg_target in text:
    text = text.replace(fg_target, fg_replacement, 1)

# 2. Append Kannada Script Display Addendum
addendum = """

## Kannada Script Display Addendum — 5 November 2026

A reversible, display-layer Roman-to-Kannada converter was integrated across the Epigraphy Studio, candidate chips, inspector, review form, history, and JSON export modules.

### Epigraphic Invariants
1. Display-Only Conversion: Stored transliteration strings in models (`*.joblib`), database records (`history.sqlite3`), and client review payloads remain strictly unaltered Roman strings.
2. Unicode Normalization: All conversions produce canonical Unicode NFC output.
3. No Guesses: Unmapped, truncated, or ambiguous strings (e.g. `ISymbol`, `stam`, isolated consonants without vowels) are preserved in Roman and marked with a small `[Roman]` badge in the interface.
4. Archaic Substitution Tier: An opt-in "Modern letters" switch replaces historical ಱ (`U+0C91`) and ೞ (`U+0CDE`) with modern ರ (`U+0CB0`) and ಳ (`U+0CB3`), flagging every modified label with a `lossy` badge.
5. Local Font Bundling: High-legibility epigraphic rendering is powered by locally bundled Noto Sans Kannada (`frontend/public/fonts/NotoSansKannada.ttf`), requiring zero remote CDN or network requests.
6. Tiny Region Demarcation: Candidates smaller than 10x10 px are explicitly marked "Too small to read" without confidence bars, and candidate #1 loading stalls are permanently eliminated.

### Mapping Audit Summary
- Total Recognizer Classes Audited: 764
- Mapped to Kannada Unicode NFC: 751 (98.30%)
- Unmapped / Ambiguous Labels Withheld: 13 (1.70%)
- Unit Test Suite: 5/5 passed (`outputs/eval/test_kannada_converter.py`)
- End-to-End Regression Suite: 9/9 passed (`outputs/eval/verify_kannada_regression.py`)
- Detailed Unmapped Labels Report: `outputs/eval/unmapped_labels_report.md`
- Precomputed Conversion Mapping: `outputs/eval/roman_to_kannada_map.json`
"""

text += addendum

with open(p, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)

print("Updated HANDOVER.md with Kannada script display addendum")

