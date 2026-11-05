from pathlib import Path

p = Path("PROJECT_LOG.md")
text = p.read_text(encoding="utf-8").replace("\r\n", "\n")

# Add row to status table
row_target = "| Multi-scale stroke enhancement | Done | `outputs/app_backend.py`, `api/server.py`, `frontend/src/App.jsx` | High accuracy mode via enhance_multiscale; auto GPU fallback; +20.23% faint stroke recovery on Nagavara demo. |"
row_addition = "\n| Kannada script display converter | Done | `outputs/kannada_converter.py`, `frontend/src/utils/kannadaConverter.js`, `frontend/src/App.jsx` | Display-only NFC converter; 751/764 classes mapped; modern lossy substitution tier; candidate #1 crop fix. |"

if row_addition.strip() not in text:
    assert row_target in text, "row_target not found in PROJECT_LOG.md"
    text = text.replace(row_target, row_target + row_addition, 1)

# Append milestone entry
new_milestone = """

### [2026-11-05] Kannada Script Display and Transliteration Converter Integration
- What changed:
  - Developed reversible display-layer Roman-to-Kannada converter in Python (`outputs/kannada_converter.py`) and JavaScript (`frontend/src/utils/kannadaConverter.js`).
  - Audited all 764 recognizer classes: 751 mapped with 100% certainty in Unicode NFC; 13 unmapped/ambiguous labels withheld from guessing and documented in `outputs/eval/unmapped_labels_report.md`.
  - Added "Script: Kannada / Roman" toggle in Studio toolbar (default Kannada, persisted in localStorage with try/catch).
  - Added "Modern letters" switch replacing archaic ಱ (`U+0CB1`) and ೞ (`U+0CDE`) with modern ರ (`U+0CB0`) and ಳ (`U+0CB3`) flagged with small "lossy" tags.
  - Candidate chips display large Kannada glyph with small Roman underneath (hidden when Roman-only active); confidence bars and uncertain dimming preserved.
  - Glyph Inspector displays large Kannada with Roman label in parentheses; alternatives shown as Kannada chips with Roman tooltip; review form maintains Roman input with live Kannada preview beside it.
  - Tiny regions (< 10x10 px) demarcated with "Too small to read" and no confidence bar; crop preview skeleton loading bug on candidate #1 resolved.
  - Run History and JSON exports updated to include both Roman and Kannada representations.
  - Verified with 5/5 converter unit tests and 9/9 end-to-end API regression tests.
- Why: Provide native Kannada script visualization for epigraphists while maintaining strict data integrity by preserving stored Roman transliterations throughout models and database records.
- Status: Done.
- Next step: Investigate line and sequence reading along inscribed stone registers.
"""

if "Kannada Script Display and Transliteration Converter Integration" not in text:
    text += new_milestone

with open(p, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)

print("Updated PROJECT_LOG.md with Kannada script display milestone")

