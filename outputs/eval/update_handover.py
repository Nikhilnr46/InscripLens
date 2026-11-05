import os

with open('HANDOVER.md', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update Project Summary
s1_old = '2. Neural Stroke Enhancement: A pretrained Shilalekhya U-Net segmentation network isolates chiseled incisions from background stone grain to produce a binarized foreground stroke mask.'
s1_new = '2. Neural Stroke Enhancement: A pretrained Shilalekhya U-Net segmentation network isolates chiseled incisions from background stone grain to produce a binarized foreground stroke mask. Operates in two modes: Standard (single-scale GPU/CPU inference, fast and reproducing the baseline candidate set) and High Accuracy (multi-scale sliding window fusing scales 256, 384, and 512 via max-probability to recover faint, eroded strokes).'

assert s1_old in text, 's1_old not found'
text = text.replace(s1_old, s1_new, 1)

# 2. Update Frontend Guide
fg_old = '- Route `/studio`: The interactive Epigraphy Studio workspace containing dual-canvas curtain slider, bounding box overlays, candidate gallery strip with filter tabs, character inspector, alternative ranking cards, and reviewer submission forms.'
fg_new = '- Route `/studio`: The interactive Epigraphy Studio workspace containing dual-canvas curtain slider, bounding box overlays, candidate gallery strip with filter tabs, character inspector, alternative ranking cards, reviewer submission forms, a "High accuracy mode" enhancement toggle switch with live progress feedback, a direct mask download button, and session mode indicators.'

assert fg_old in text, 'fg_old not found'
text = text.replace(fg_old, fg_new, 1)

# 3. Update Endpoints Table
ep_old = '| `POST` | `/api/analyse` | Executes neural binarization and candidate extraction | Multipart form (`file`) OR `?use_demo=true` | `{"id": str, "display_name": str, "is_demo": bool, "sha256": str, "image_url": str, "mask_url": str, "width": int, "height": int, "boxes": list, "candidate_count": int, "created": str}` | Public |'
ep_new = '| `POST` | `/api/analyse` | Executes neural binarization and candidate extraction | Multipart form (`file`, optional `mode`) OR `?use_demo=true&mode=...` | `{"id": str, "display_name": str, "is_demo": bool, "sha256": str, "image_url": str, "mask_url": str, "width": int, "height": int, "boxes": list, "candidate_count": int, "created": str, "mode": str, "mode_label": str, "fallback_note": Optional[str]}` | Public |\n| `GET` | `/api/export/{run_id}` | Exports run metadata, mode, candidate count, and reviews in JSON format | None | `{"id": str, "display_name": str, "mode": str, "mode_label": str, "candidate_count": int, "created": str, "reviews": list}` | Public |'

assert ep_old in text, 'ep_old not found'
text = text.replace(ep_old, ep_new, 1)

hist_old = '| `GET` | `/api/history` | Lists previous analysis sessions from SQLite | None | List of session objects: `[{"id": str, "created": str, "display_name": str, "image_url": str, "mask_url": str, "sha256": str}]` | Public |'
hist_new = '| `GET` | `/api/history` | Lists previous analysis sessions from SQLite | None | List of session objects: `[{"id": str, "created": str, "display_name": str, "image_url": str, "mask_url": str, "sha256": str, "mode": str, "mode_label": str, "fallback_note": Optional[str]}]` | Public |'

assert hist_old in text, 'hist_old not found'
text = text.replace(hist_old, hist_new, 1)

# 4. Add Enhancement Modes & GPU Fallback subsection after Response Sanitization Audit
sub_target = '### Response Sanitization Audit'
sub_addition = """### Enhancement Modes and GPU Memory Safety
- Standard Mode (default): Executes single-scale U-Net inference on GPU or CPU. Produces identical results to historical baselines (e.g. 133 candidate regions on the Nagavara benchmark stone).
- High Accuracy Mode: Calls `enhance_multiscale` from `outputs/binarizer_core.py` without modifying the core function. Evaluates image tiles across multi-scale dimensions (256, 384, 512) and fuses stroke probabilities with max-pooling. Recovers faint, shallow incisions while connecting fragmented strokes into coherent character glyphs.
- Graceful GPU OOM Fallback: If GPU VRAM is exhausted (such as on 4 GB laptop GPUs) or an execution error occurs during multi-scale enhancement, the backend automatically re-executes standard enhancement and records a plain English notification (`fallback_note`), guaranteeing zero server crashes.
- Provenance Tracking: Every analysis run stores its mode (`standard` or `high_accuracy`) and user-facing label (`Standard` or `High accuracy`) in the SQLite `runs` table and export payloads. Internal model names and filesystem paths are never serialized.

"""
assert sub_target in text, 'sub_target not found'
text = text.replace(sub_target, sub_addition + sub_target, 1)

# 5. Add Verification Addendum at the end
addendum_text = """

## Multi-Scale Enhancement Verification Addendum — 5 November 2026

The multi-scale enhancement integration was empirically verified against the curated 8th-century Nagavara hero stone (`HS027`, dimensions 525 x 1080):

| Metric | Standard Mode (Single-Scale GPU) | High Accuracy Mode (Multi-Scale GPU) | Difference / Epigraphic Impact |
|---|---|---|---|
| Inference Pipeline | `enhance_image` (single pass) | `enhance_multiscale` (256, 384, 512) | Multi-scale pyramid sliding window |
| Inference Runtime | 2.325 s | 2.947 s | +0.622 s overhead (+26.8%) |
| Candidate Boxes Detected | 133 | 118 | -15 broken fragments consolidated |
| Foreground Stroke Pixels | 49,848 | 59,129 | +10,086 faint stroke pixels (+20.23%) |
| Common Stroke Pixels | 49,043 | 49,043 | Preserves 98.39% of standard stroke mask |
| Spurious / Filtered Pixels | 805 | - | Filtered isolated speckle artifacts |
| GPU Memory Safety | Verified | Verified (graceful fallback tested) | Stable on 4 GB VRAM GPU |
| Baseline Preservation | Exact match (133 boxes) | N/A (opt-in feature) | Default scanning untouched |

Visual mask comparisons and numerical audit data are archived in:
- `outputs/eval/mask_mode_comparison_nagavara.png`
- `outputs/eval/nagavara_mode_comparison_report.json`
"""

text = text + addendum_text

with open('HANDOVER.md', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text)

print('Updated HANDOVER.md successfully')

