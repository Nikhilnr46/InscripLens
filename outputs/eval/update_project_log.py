with open('PROJECT_LOG.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Add row to status table
row_target = '| Interactive headline hover color (Step C2) | Done | `frontend/src/index.css`, `frontend/src/pages/LandingPage.jsx` | rAF-throttled layered background-clip text spotlight with dynamic hue shift and 300ms leave transition. |'
row_addition = '\n| Multi-scale stroke enhancement | Done | `outputs/app_backend.py`, `api/server.py`, `frontend/src/App.jsx` | High accuracy mode via enhance_multiscale; auto GPU fallback; +20.23% faint stroke recovery on Nagavara demo. |'

assert row_target in text, 'row_target not found'
text = text.replace(row_target, row_target + row_addition, 1)

# Append milestone entry
new_milestone = """


### [2026-11-05] Multi-Scale Enhancement Integration and Verification
- What changed:
  - Added optional `mode` parameter ("standard" default, "high_accuracy") to `POST /api/analyse` in `outputs/app_backend.py` and `api/server.py`.
  - Integrated `enhance_multiscale` from `outputs/binarizer_core.py` without modifying the core function, evaluating scales 256, 384, and 512 with max-probability fusion.
  - Implemented automatic fallback to standard mode on GPU memory exhaustion (4 GB VRAM limit) or subprocess failure, returning a plain error notification (`fallback_note`).
  - Added "High accuracy mode" switch in frontend Studio with exact note: "Finds more faint strokes. Slower, and may add a few false strokes.", live progress feedback, and direct mask download button.
  - Persisted mode label in SQLite run history and export payloads (sanitized of internal model names and paths).
  - Verified on Nagavara demo stone (`HS027`): Standard mode (133 candidates, 49,848 stroke px, 2.33s), High accuracy mode (118 candidates, 59,129 stroke px, +20.23% faint stroke recovery, 2.95s).
  - Saved visual comparison to `outputs/eval/mask_mode_comparison_nagavara.png` and numerical audit to `outputs/eval/nagavara_mode_comparison_report.json`.
- Why: Give epigraphists the ability to recover eroded, faint incisions while preserving fast default scanning and zero regression on standard runs.
- Status: Done.
- Next step: Investigate line and sequence reading along inscribed stone registers.
"""

text = text + new_milestone

with open('PROJECT_LOG.md', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text)

print('Updated PROJECT_LOG.md successfully')

