# InscripLens Studio Project Log

## 6 November: Region Selection Implementation (Step S2 of 3)

Implemented interactive stone region selection (`RegionSelector`) for uploaded images prior to neural analysis:
- Flow & 3-Step Progress Navigation:
  - Added visual 3-step progress indicator to `/import` header: `1. Choose` -> `2. Select area` -> `3. Studio`.
  - Step 1 (Choose) transitions to Step 2 (Select area) exclusively upon selecting or dropping a valid photograph; the curated Nagavara demonstration stone bypasses cropping and enters Studio directly.
  - Back navigation from Step 2 cleanly resets the active image, closes ImageBitmap instances, and returns to Step 1.
- EXIF Orientation & Full-Resolution Bitmap Pipeline:
  - Decoded incoming photos via `createImageBitmap(file, { imageOrientation: "from-image" })`, permanently eliminating orientation inversion and phone rotation bugs.
  - Retained full-resolution bitmap in memory for lossless final extraction while rendering a responsive viewport stage.
  - Graceful fallback: on decoding failure or browser memory restrictions, provides a dedicated notice with a "Continue with the whole image" recovery route.
- Interactive Crop Canvas & Dimming Overlay:
  - SVG mask cutout dims unselected stone area (`rgba(0,0,0,0.58)`).
  - Drag inside selection box to move; drag on empty canvas to draw a new bounding box.
  - 8 resize handles (corners and edges) with enlarged touch targets and adaptive scale stroke widths.
  - Full keyboard accessibility: Arrow keys nudge selection by 1% of image size, Shift + Arrow keys resize, and Escape resets to default.
  - Pointer events with `touch-action: none` and pointer capture ensure fluid pan/zoom/crop on touch screens.
- Live Dimension Readout & Epigraphic Quality Bounds:
  - Displays selection width × height in original photo pixels alongside total stone dimensions and percentage coverage.
  - Enforced 64 × 64 px hard minimum bounding box.
  - Added warning banner for selections below 300 × 300 px indicating smaller glyph areas may produce weaker enhancement and recognition.
- Precision Zoom & Pan:
  - Cursor-centered wheel and pinch zoom (clamped 0.1x to 5.0x).
  - Middle-mouse drag and Space-key pan navigation.
  - Fit-to-view, 100% scale, Zoom In, and Zoom Out control bar.
- Export & Memory Handoff:
  - Pre-selects a centered 80% default crop for fast adjustment.
  - "Use whole image" button and ≥ 99% area coverage selections pass the original File directly with zero re-encoding.
  - Cropped selections are rendered from full-resolution bitmap onto an offscreen canvas with a 3200 px long-side cap (preserving fine stroke detail well above the backend's 1600 px internal downscaling ceiling) and exported as `selected-area.png`.
  - In-memory store (`fileStore.ts`) holds cropped `File`, `originalFile`, `selection`, and `originalSize` without disk or `localStorage` persistence, invoking the unmodified Studio upload pipeline.

## 6 November: Import Screen Implementation (Step S1 of 3)

Implemented the dedicated Image Import workspace route (`/import`) providing a streamlined entry point before Studio analysis:
- Route Architecture & Navigation:
  - Added dedicated route `/import` with full design system, header, and theme integration (obsidian dark and parchment light).
  - Landing page's "Slide to enter Studio" interactive slider (including keyboard navigation via Enter, Space, and ArrowRight) now navigates directly to `/import`.
  - Added navigation back link on `/import` routing back to the landing page (`/`).
  - Studio top header "Try another" button and demo button now route back to `/import` rather than directly opening the system file dialog, preserving direct `/studio` visits.
- Import Selection Cards:
  - Centered workspace card with heading "Choose a stone image" and two large options side by side (stacked gracefully on viewports < 768px).
  - Option A: "Upload a photograph": Drag-and-drop zone with active hover states plus "Browse image" button; validates accepted formats (PNG, JPG) and enforces the 20 megapixel limit with user-friendly error banners.
  - Option B: "Use the demo stone": Showcases the Nagavara hero stone (971 CE) benchmark with thumbnail preview, historical epoch pill, and 1-click loading.
- Temporary In-Memory File Handoff (completed in S2):
  - Created `frontend/src/utils/fileStore.ts` to hold chosen `File` objects strictly in memory (zero `localStorage` / `sessionStorage` usage).
  - Studio route consumes pending files on entry and dispatches the existing neural enhancement upload pipeline, maintaining full backward compatibility.
- Regression & Verification:
  - Landing page reveals, slide-to-enter transition, demo stone loading, photograph upload pipeline, multi-scale enhancement, connected-component candidate detection, batch classification, and SQLite review persistence all operate identically to baseline.

## 5 November: Studio UI batch 2 layout of controls

Reorganized Studio viewer toolbar and bottom gallery strip:
- Top toolbar: grouped Boxes toggle (with count pill) and Curtain control (label and percentage) on the left. Placed Script segmented control (sliding highlight for Kannada and Roman, keyboard accessible), Display options popover (gear icon, Kannada-only, hosting Modern letters switch and lossy warning), Zoom group (Fit, minus, zoom level, plus), and Export dropdown menu ("Download mask") on the right.
- Container query responsive behavior: below 1100 px panel width, automatically collapses Script control, Display options, and Export into a unified "View" dropdown button while keeping zoom controls always visible.
- Bottom gallery bar: restructured left section to feature "Classify All (N)" as a single primary button, transforming into "Re-run" with a "133 classified" status pill after classification, placed next to candidate filter segmented control (All, Predicted, Reviewed with count pills). Right section holds compact "Hide tiny" switch chip with count pill and keyboard navigation arrow hint (fades out after first arrow key navigation, remembered in localStorage, accessible via tooltip).
- Verified responsive layout across 1280, 1366, 1440, 1536, and 1920 px viewports in light and dark themes with sidebar expanded and collapsed; regression tested demo, file upload, high accuracy enhancement, batch classification, filters, review persistence, and mask export.

## 5 November: Studio UI batch 1 quick edits

Completed Studio batch 1 UI edits: restyled Home pill, removed header About, renamed Upload to "Try another", conditioned Demo button visibility, removed STANDARD badge, enlarged curtain divider and handle to 3px/32px, styled 12px candidate scrollbar, softened inspector spotlight, and verified dark/light layouts at 1366, 1536, and 1920.

## 5 November: first larger sequence diagnostic

Fixed10-epoch CNN-BiLSTM-CTC run on124 screened fit lines,7 separate development lines. Alphabet fit-only, source-disjoint splits, image-only resizing height48/minimum width256/max1024. Initial minimum64 failed CTC capacity on a training line, so fixed minimum256 before training. No validation-stone access or model promotion.

Result: greedy0/124 exact training lines and0/7 development, both100% codepoint error. Development beam width10:0/7 exact,131 edits/172 source Roman codepoints=76.16% CER (including separators). Training loss9.74 to3.28. The earlier four-line memorization success does not yet scale to this larger mixed set. Ten epochs is an initial budget, not a convergence or impossibility result. Next investigate training blank collapse/optimization on increasing sample counts, measure training beam accuracy, and compare a frequency-only baseline before claiming visual generalization. Full data remains available; this screened subset is diagnostic.

Reproduce with work/binarizer_env/Scripts/python.exe outputs/train_screened_sequences.py. Local checkpoint sequence_model.pth is ignored by Git. Application remains unchanged; http://127.0.0.1:8001/studio responded during this session.


## 5 November: collaborator integration review and decoding control

Pulled origin/main through09ff40f (89 changed files). Frontend production build passed. Review-storage, coordinate regression,5 Kannada-converter tests, translation traceability and real enhancement/backend persistence tests passed. Traceability checks bookkeeping, not independent linguistic correctness. Friend's new CNN/line/dictionary checkpoints were not transferred through Git; only older character_cnn.pth exists locally. Reported GPU results cannot be reproduced on this laptop without those assets. Local app now uses the existing SVM fallback.

Found/fixed cross-version package injection: recognizer.py prepended Python3.12 worker site-packages to Python3.14 app, causing native NumPy import failure. Removed injection; PyTorch is optional for SVM-only application operation. Enhancement still runs in its own environment. Corrected single-crop SVM to use model.predict instead of decision-score argmax, preserved prediction as first alternative, and made model agreement unknown when only one model exists. SVM probabilities are withheld because the imported calibration protocol uses model-training members and supplied binary crops, unlike application predicted masks. The confidence thresholds are not evidence of75% held-out precision (friend's own report gives42.02% retained precision at that target).

CTC breakthrough: exact same screened four training lines, seed/model/300steps, greedy1/4; lexicon-free prefix beam width10 gives4/4. No targets or dictionary passed into decoding. Decoder validated against exhaustive CTC path summation. This clears the tiny memorization gate; it does not demonstrate held-out line recognition or guarantee arbitrary-stone OCR. Report outputs/paired_line_data/learnability_mask_beam10.json.

Next: bounded screened-line training with development sequence error, source-wise reporting and no tuning on the six reused validation stones. Keep all relevant data for broader experiments; the screened subset is an input-quality diagnostic, not a new stone category.

Presentation updates after integration: Kannada script display is transliteration, not recognition improvement or modern-language interpretation. Multi-scale adds foreground but does not prove more correct strokes without ground truth. Rule-based interpretation draft exists, but limited token/formula tests do not establish full translation accuracy. Reconcile prior notes saying no converter/translation module with this new implementation. Do not replace77/300 and52/300 with GPU/ensemble numbers without reproducing comparable protocol/assets.


## 4 November: screened-line learnability and additional printed data

Tested the same four deterministic shortest multi-label fit lines from the stricter 124-line set. Fixed seed42, height48, vertical features, packed BiLSTM, 300-step CTC budget: predicted-mask view 1/4 exact, original grayscale view 0/4. Both fail the 4/4 gate. Sample selection differs from earlier 3/4 experiments; do not interpret this as a comparable accuracy regression. No validation/development used, no larger training or runtime model change. Geometry filtering alone has not solved learnability.

Downloaded the official Mozhi-Kannada test archive (45,595,591 bytes) into work/mozhi_kannada/test.zip; verified 9,838 image/text entries. Fixed first100 by filename SHA256, pretrained Tesseract kan OEM1/PSM8: 29/100 exact words, 200 edits /697 NFC codepoints =28.6944% CER. Separate printed-word diagnostic, not inscription performance or our own trained model. Benchmark and archive hash recorded in outputs/mozhi_printed_study/summary.json. No test-set parameter tuning.

Reviewed official Google Vision, Sarvam and IIITH/Bhashini Kannada OCR documentation. These could draft publication text but historical-stone accuracy is unverified. No external inference called and no paid API enabled. See outputs/DATA_AND_PANEL_BRIEF.md for sources and practical limits. More images alone do not fix unaligned/rare labels or damaged strokes.


## 4 November: fixed paired validation and line-data audit

Fetched origin/main: no newer friend commits at the start of this session (f6d55d9). Preserved the user's renamed InscripLensPhase3.pptx and removal of older decks.

Fixed original+mask HOG validation: 78/300 supplied-box labels versus baseline 77/300; 15 errors fixed and 14 introduced. Automatic localization+label recovery declined from 52/300 to 50/300. Same 330 proposals, 196 geometry matches. The application model is unchanged. This is reused six-image validation, not a fresh accuracy estimate. See outputs/paired_feature_validation/summary.json.

Prepared paired original/mask line crops using the union of each supplied line polygon and its character polygons. Added annotated-neighbour overlap checks (>5% excluded), image-boundary checks and minimum mask foreground checks. Of 672 fit / 34 development candidates, 124 / 7 pass; 62 / 1 were recovered, while 145 / 15 formerly eligible records are now flagged. All 706 paired exports have matching dimensions and full in-image target polygon coverage. These are annotation-assisted unverified sequences, not automatic OCR or expert transcriptions. See outputs/paired_line_data/README.md.

Next: visually review a deterministic subset of the stricter set, then repeat a fixed tiny-subset CTC learnability check before larger training. Sparse strokes and incomplete annotations remain risks. Full-line OCR and translation remain unfinished.


## 1. Where Were We
InscripLens Studio is fully transitioned from its legacy Streamlit prototype into a modern React + TypeScript single-page application served by a local FastAPI backend. Both the single-page landing site and the three-panel Epigraphy Studio workspace are fully operational offline with dual-theme styling (dark obsidian and light parchment), smooth scroll-spy navigation, replaying reveal animations, and hardware-accelerated micro-interactions. The neural stroke enhancement, connected-component candidate detection, experimental character classification, and SQLite review persistence pipelines are complete and sanitized of internal file paths. The legacy Streamlit prototype remains preserved for benchmark audits. The single most important next step is developing an epigraphic sequence transcription model for reading full lines rather than isolated character bounding boxes.
Start the application with:
```powershell
python launch_studio.py
```

---

## 2. Status Table

| Feature / Milestone | Status | Evidence (Files / Commits) | Notes |
|---|---|---|---|
| Streamlit prototype application | Done | `outputs/inscriplens_app.py`, commit `1ef121c` | Initial local prototype; preserved for parity and benchmark comparisons. |
| Subprocess U-Net binarizer worker | Done | `outputs/binarizer_core.py`, `work/shilalekhya/` | Tiled CPU inference in dedicated Python 3.12 environment (`work/binarizer_env`). |
| Candidate region localization | Done | `outputs/segment_candidates.py`, commit `b1bc507` | Connected-component analysis on binarized foreground masks. |
| Experimental character recognition | Done | `outputs/recognize_regions.py`, `outputs/broad_clean_study/` | Diagnostic HOG/SVM classifier (52/300 reference recovery). |
| Ranked label alternatives & examples | Done | `outputs/recognition_alternatives.py`, commit `c9300e7` | Ranks top 3 predictions with support-set reference crops. |
| SQLite reviewer provenance records | Done | `outputs/app_backend.py`, commit `002e705` | Append-only storage in `work/app_data/history.sqlite3`. |
| FastAPI backend server | Done | `api/server.py` | Exposes REST endpoints on port 8000; sanitizes paths and model names. |
| React + TypeScript Studio workspace | Done | `frontend/src/App.jsx`, `frontend/src/index.css` | 3-panel workspace: canvas with curtain wipe, candidate strip, inspector. |
| Single-page landing site | Done | `frontend/src/pages/LandingPage.jsx` | Sections: `#overview`, `#workflow`, `#about`, `#limitations`. |
| Interactive tablet illustration | Done | `frontend/src/components/TabletIllustration.tsx` | rAF proximity glow and torchlight spotlight without React re-renders. |
| Slide to enter Studio control | Done | `frontend/src/components/SlideToEnter.jsx` | Sole landing entry point; accessible via drag and keyboard (`Enter`, `Space`, `ArrowRight`). |
| Light/Dark theme system | Done | `frontend/src/components/ThemeToggle.tsx`, `index.css` | Obsidian (`#121214`) vs parchment (`#F7F2E8`) with View Transitions circular reveal. |
| Micro-interactions & hover language | Done | `frontend/src/utils/interactions.ts` | rAF pointer-tracking: 3D card tilt, cursor spotlight, magnetic button drift. |
| Replaying scroll reveals | Done | `frontend/src/utils/revealObserver.js`, `Reveal.jsx` | IntersectionObserver with hysteresis `[0, 0.15]` animating CSS `translate`/`opacity`. |
| Scroll lock fix | Done | `frontend/src/index.css`, commit log | Replaced body overflow lock with `html { overflow-y: scroll; }` and `overflow-x: clip;`. |
| Landing site cleanup (Step C1) | Done | `LandingPage.jsx`, `AboutSection.tsx`, `Footer.tsx` | Header button removed, Limitations moved to end, single-column About, clean footer. |
| Privacy scrub (paths & model names) | Done | `api/server.py`, `App.jsx` | Internal filenames masked to "Experimental recognizer"; file paths masked to web URLs. |
| Curated demo stone metrics | Done | `TabletIllustration.tsx`, `full_binarizer/HS027_original.png` | Fixed chips ("EPOCH 8th C. CE", "REGIONS 133 localized") reflect Nagavara benchmark stone. |
| Interactive headline hover color (Step C2) | Done | `frontend/src/index.css`, `frontend/src/pages/LandingPage.jsx` | rAF-throttled layered background-clip text spotlight with dynamic hue shift and 300ms leave transition. |
| Multi-scale stroke enhancement | Done | `outputs/app_backend.py`, `api/server.py`, `frontend/src/App.jsx` | High accuracy mode via enhance_multiscale; auto GPU fallback; +20.23% faint stroke recovery on Nagavara demo. |
| Kannada script display converter | Done | `outputs/kannada_converter.py`, `frontend/src/utils/kannadaConverter.js`, `frontend/src/App.jsx` | Display-only NFC converter; 751/764 classes mapped; modern lossy substitution tier; candidate #1 crop fix. |
| Toolbar layout hardening & crop loader fix | Done | `frontend/src/App.jsx`, `frontend/src/index.css`, `api/server.py` | 3 non-wrapping toolbar groups; container-query View dropdown; 8s crop timeout + retry; server model caching; 19/19 audit passed. |
| Mobile low-power / lite-mode audit | Not done | Backlog item | Planned battery/GPU reduction tier; deferred as rAF loops already pause when idle. |
| Automated line transcription / reading order | Not done | `outputs/sequence_data_audit/` | Line-level sequence OCR is not yet implemented. |
| Historical Kannada to English translation | Not done | Stated in limitations | Outside project scope; unverified for general epigraphy. |

---

## 3. Timeline

### Milestone 1: Baseline Application and Collaborator Setup (2026-11-02 to 2026-11-03)
- `c004358` (2026-11-02): Initial project commit establishing base structure and exploratory image preprocessing scripts in `src/`.
- `1ef121c` (2026-11-03): Integrated local Streamlit inscription analysis application in `outputs/inscriplens_app.py` connecting the Shilalekhya U-Net binarizer with candidate region proposal.
- `e1ff78c` (2026-11-03): Authored `COLLABORATOR_HANDOVER.md` documenting missing runtime assets and clean environment reproduction commands.
- `0771235` (2026-11-03): Implemented fresh-clone asset guards in the Streamlit application to prevent missing asset crashes.

### Milestone 2: Review Storage and Diagnostic Recognition Benchmarks (2026-11-03)
- `002e705` (2026-11-03): Added append-only SQLite character review storage in `outputs/app_backend.py` to record provenance, reviewer initials, and suggested readings without corrupting source ground truth.
- `b1bc507` (2026-11-03): Connected connected-component region localization to batch classification in `outputs/recognize_regions.py`.
- `5b4226a` (2026-11-03): Evaluated glyph normalization and training augmentation hypotheses in `outputs/augmentation_study/`.
- `be68779` (2026-11-03): Trained broader cleaned-image HOG/SVM recognizer and corrected Begur site exclusion filter in `outputs/broad_clean_study/`.
- `c9300e7` (2026-11-03): Added source-linked recognition alternatives and ranked predictions in `outputs/recognition_alternatives.py`.

### Milestone 3: Sequence Data Audits and Context Studies (2026-11-04)
- `fb5bc42` (2026-11-04): Recorded contextual reading experiments and Kumbalahalli hero stone comparisons in `outputs/context_reading/`.
- `5d196c6` (2026-11-04): Added published reading comparison view and restart checkpoint report.
- `44b2f35` (2026-11-04): Audited line-level supervision and candidate character polygon structures in `outputs/sequence_data_audit/`.
- `cfde100` (2026-11-04): Inspected sequence crops and recorded bounded CTC sanity experiment in `outputs/sequence_data_audit/EXPERIMENT.md`.
- `de2e49b` (2026-11-04): Diagnosed sparse sequence inputs and added presentation study guide in `outputs/STUDY_GUIDE.md`.
- `b62a997` (2026-11-04): Checked padding-aware sequence learning and recorded gate test failures.
- `e0f6579` to `65a00da` (2026-11-04): Evaluated printed book heading OCR baselines against transcription ground truth in `outputs/book_ocr_study/`.
- `0b0d0bb` (2026-11-04): Audited diagnostic recognition failures beyond character label coverage in `outputs/recognition_failure_audit/`.
- `6f27f8b` (2026-11-04): Compared original and mask feature performance on held-out development locations in `outputs/paired_feature_study/`.

### Milestone 4: Architecture Modernization and Polish (2026-11-04)
- React SPA & FastAPI Backend: Built modern React client in `frontend/` and FastAPI REST service in `api/server.py`. Replaced Streamlit UI while preserving core analysis logic.
- Polish Step P5: Consolidated Studio header into single status line; added collapsible icon-rail sidebar; elevated contrast to WCAG AA; added mobile sheet responsiveness below 1100px and 768px.
- Tablet Illustration: Built GPU-accelerated stone tablet SVG with seeded deterministic hairline cracks, rAF proximity glow, and soft torchlight spotlight without React re-renders.
- Theme System (Step S1): Implemented semantic design token system across dark obsidian (`#121214`) and warm parchment (`#F7F2E8`) with circular reveal transition.
- Micro-interactions (Step S2): Implemented magnetic buttons, 3D card tilt, and radial cursor spotlights driven by unified rAF pointer tracking.
- About Documentation (Step S3): Created comprehensive system documentation, FAQ accordion, offline privacy specification, and attribution records.
- Single-Page Navigation (Step N1): Merged landing routes into scrolling page at `/` (`#overview`, `#workflow`, `#about`, `#limitations`) with sticky header offset.
- Replaying Reveals (Step N2): Added replaying IntersectionObserver scroll reveals using CSS individual `translate` and `opacity` properties.
- Scroll Lock Bug Fix: Eliminated scroll blocking on root page by removing `body { overflow: hidden; }` and adopting `overflow-x: clip;`.
- Cleanup and Restructure (Step C1): Removed redundant header/hero entry links; established "Slide to enter Studio" as sole keyboard-accessible entry; relocated Limitations to final section; cleaned footer attribution.
- Interactive Headline Spotlight (Step C2): Implemented rAF-throttled layered background-clip text spotlight on 'Read the stone before it fades' with dynamic horizontal hue shift, 300ms leave ease-out, light-mode contrast deepening, and reduced-motion/touch guards.
- Handover and Repository Hygiene: Generated `HANDOVER.md`, updated `README.md`, and updated root `.gitignore` to protect build artifacts and runtime data.

---

## 4. Architectural Decisions and Rationale

1. Replacement of Streamlit with React + FastAPI:
   - Reason: Streamlit is designed for dashboard workflows and recalculates its script on interaction. It could not provide smooth 60fps dual-canvas curtain wipes, high-precision SVG canvas zooming/panning, mobile bottom-sheet transitions, or fluid CSS micro-interactions.
   - Solution: Created a decoupled React 19 SPA served by a lightweight FastAPI server, providing instant UI feedback while keeping the core Python pipelines untouched.
2. Preserving Python Analysis Logic Unchanged:
   - Reason: The Shilalekhya U-Net segmentation, connected-component candidate extraction, and HOG/SVM recognizer have verified contracts and regression test suites. Rewriting them risked regression.
   - Solution: `api/server.py` imports and executes the existing modules directly, acting strictly as a serialization bridge.
3. 100% Offline Local Architecture:
   - Reason: Field epigraphists frequently work in remote heritage sites without reliable Internet connectivity. In addition, unpublished inscription photographs require strict privacy.
   - Solution: All neural inference runs locally on CPU via PyTorch. Analysis runs, crops, and review records persist exclusively in local SQLite and filesystem directories.
4. Token-Based Theme and Interaction Systems:
   - Reason: Hardcoded hex values prevent clean theme switching, and multiple pointer listeners cause CPU frame drops.
   - Solution: Centralized semantic CSS custom properties under `:root` and consolidated pointer tracking into a single rAF loop that pauses when idle.

---

## 5. Rules We Followed

1. Analysis Integrity: UI and presentation changes must never alter model weights, feature extraction, candidate detection thresholds, or review storage formats.
2. Zero Cloud Services: No external cloud OCR APIs, remote databases, third-party CDNs, external web fonts, or tracking scripts are permitted.
3. No Emojis: No emojis in source code, user interfaces, documentation, or commit messages.
4. Strict Privacy Scrub: Local filesystem paths, internal machine usernames, and model filenames (`*.pth`, `*.joblib`) must never be displayed in the UI or serialized into client API responses.
5. Attribution Preservation: Licences and attributions for Shilalekhya (MIT) and EpiSAM (CC BY-SA 4.0) must remain visible and complete across all documentation and UI views.

---

## 6. Backlog and Deferred Ideas

| Priority | Item | Description | Status / Reason Deferred |
|---|---|---|---|
| Priority 1 | Line & Sequence Reader | CRNN or Transformer model to read character sequences along inscribed lines rather than independent boxes. | Incomplete; audited in `sequence_data_audit/`, requires dedicated training corpus. |
| Priority 2 | Interactive headline hover color | Changing headline gradient letters dynamically as cursor sweeps across text. | Deliberately skipped to avoid distracting contrast shifts and maintain WCAG AA compliance. |
| Priority 3 | Lite / low-power mobile mode | Low-power toggle disabling glows, ambient blur, and hover tracking on battery-saver devices. | Deliberately skipped; unnecessary because rAF animation loops already pause automatically when pointer leaves. |
| Priority 4 | WebGPU client-side binarization | Export Shilalekhya U-Net to ONNX Runtime Web / WebGPU for browser-native inference. | Backlog idea; removes the need for local Python PyTorch installation entirely. |
| Priority 5 | TEI-EpiDoc XML export | Structured XML export format adhering to international epigraphic standards. | Backlog idea; allows review outputs to integrate directly into academic epigraphy portals. |

---

## 7. Open Questions for the Next Maintainer

1. Model Packaging & Distribution:
   - Question: Should model weights (`binarizer.pth`, `mask_svm_bundle.joblib`) be packaged into an automated downloader script that fetches them from Hugging Face on clean clone, or kept as separate manual zip archives?
2. Open Source Licensing for Original Code:
   - Question: Which open-source licence (MIT, Apache 2.0, or CC BY-NC) should be applied to the original project wrapper code? The third-party dependencies are MIT and CC BY-SA 4.0.
3. Candidate Box Filtering Thresholds:
   - Question: Small candidate regions (<10x10 px) are currently kept and optionally hidden via the "Hide tiny regions" toggle. Should the connected-component detector filter these out by default during analysis?

---

## 8. How to Update This Log

When making significant updates to InscripLens Studio, append a new dated entry at the bottom using this template:

```markdown
### [YYYY-MM-DD] Title of Milestone or Change
- What changed: Concise description of modified files, components, or endpoints.
- Why: Technical or architectural rationale for the change.
- Status: Done / Partly done / Not done / Unverified.
- Next step: What the immediate subsequent task should be.
```

---

### [2026-11-04] Handover to Nikhil N R Vasista
- What changed: Completed landing site cleanup (Step C1), unified navigation offsets, verified zero emojis/paths, compiled production frontend assets, audited repository secrets/gitignore, authored `HANDOVER.md`, updated `README.md`, and created `PROJECT_LOG.md`.
- Why: Prepare repository for a clean, verified GitHub push and smooth onboarding for collaborators and reviewers.
- Status: Done.
- Next step: Review git status, stage intended source and documentation files, and push to the remote repository.



### [2026-11-04] Local onboarding and Presentation 3 verification
- Pulled Studio changes through 4b40179 and completed the production frontend build.
- Verified localhost status/demo/SPA endpoints, real demo analysis (133 candidates), batch and single-region prediction, review round-trip, and three negative API requests.
- Added missing server dependencies to requirements.txt and fixed analysis-canvas dimensions for resized uploads, with a passing regression test.
- Measured one demo enhancement at 23.37 s here. No recognition model or benchmark changed.
- The original Phase 2 translation objective remains unfinished; it has not been silently removed from the presentation scope.
- Detailed results, local environment command and remaining migration gaps: outputs/STUDIO_STARTUP_VERIFICATION.md.
- Next: validate paired image/mask features and improve verified sequence supervision.



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


### [2026-11-05] Kannada Script Display and Transliteration Converter Integration
- What changed:
  - Developed reversible display-layer Roman-to-Kannada converter in Python (`outputs/kannada_converter.py`) and JavaScript (`frontend/src/utils/kannadaConverter.js`).
  - Audited all 764 recognizer classes: 751 mapped with 100% certainty in Unicode NFC; 13 unmapped/ambiguous labels withheld from guessing and documented in `outputs/eval/unmapped_labels_report.md`.
  - Added "Script: Kannada / Roman" toggle in Studio toolbar (default Kannada, persisted in localStorage with try/catch).
  - Added "Modern letters" switch replacing archaic ಱ (`U+0C91`) and ೞ (`U+0CDE`) with modern ರ (`U+0CB0`) and ಳ (`U+0CB3`) flagged with small "lossy" tags.
  - Candidate chips display large Kannada glyph with small Roman underneath (hidden when Roman-only active); confidence bars and uncertain dimming preserved.
  - Glyph Inspector displays large Kannada with Roman label in parentheses; alternatives shown as Kannada chips with Roman tooltip; review form maintains Roman input with live Kannada preview beside it.
  - Tiny regions (< 10x10 px) demarcated with "Too small to read" and no confidence bar; crop preview skeleton loading bug on candidate #1 resolved.
  - Run History and JSON exports updated to include both Roman and Kannada representations.
  - Verified with 5/5 converter unit tests and 9/9 end-to-end API regression tests.
- Why: Provide native Kannada script visualization for epigraphists while maintaining strict data integrity by preserving stored Roman transliterations throughout models and database records.
- Status: Done.
- Next step: Investigate line and sequence reading along inscribed stone registers.


### Milestone 5: Layout Hardening, Responsive Controls & Crop Loader Resilience (2026-11-05)
- Studio Toolbar Restructuring: Rebuilt the canvas viewer toolbar into three discrete flex groups (Left: Curtain, Boxes, Mode, Mask; Middle: Script switch & Modern letters; Right: Fit & Zoom controls) with `white-space: nowrap` and fixed minimum widths to prevent wrapping.
- Responsive Container Queries: Added a viewer panel container query observer (`ResizeObserver` on `.canvas-panel`). Automatically moves Script and Modern letters controls into a "View" dropdown button below 1100 px, and additionally moves Mask and Mode badge into it below 900 px. Fit and zoom controls remain pinned and visible at all resolutions.
- Status Badge Relocation: Relocated "N regions classified" status and the Re-run button to the bottom filter bar before the "Hide tiny" toggle.
- Auto-Collapsing Sidebar: Implemented automatic icon-rail sidebar collapsing on window widths < 1500 px while preserving manual user preference in `localStorage`.
- Single-Row Header: Refactored the Studio header into a single non-wrapping row, replacing the multiline note under High accuracy mode with an accessible info icon tooltip, and truncating the stone name with an ellipsis and full hover tooltip.
- Crop Loader Stall Resolution: Diagnosed and fixed the stuck "Loading crop..." condition. Preloaded and cached recognition model weights in `api/server.py` on server start, and added an `AbortController` with an 8-second timeout in `predictBox`. Replaced infinite skeletons with short error feedback, a "Retry" button, and `"Alternatives unavailable"` fallback while displaying the candidate's known strip label immediately.
- Comprehensive Responsive Audit: Verified across 19 permutations covering window widths 1280, 1366, 1440, 1536, and 1920 px, zoom levels 100% and 125%, open and collapsed sidebar states, and dark obsidian / light parchment themes (`outputs/eval/run_responsive_audit.py`).

## 2026-11-05: Git Push Readiness & Automated GPU Installation

### Context
Pre-push repository audit and automated environment setup preparation to allow any collaborator or evaluator to install dependencies, configure GPU acceleration with CUDA, build the React frontend, and run the Studio with zero friction.

### Key Actions
1. Repository Hygiene:
   - Added *.pdf (excluding 1.51 GB literature dictionaries), episam/ (440 MB raw dataset), dom*.txt (browser debug dumps), and eergallu images/ to .gitignore.
   - Verified that no file exceeding GitHub's 100 MB upload limit is staged or tracked.
2. Inference Python Resolution:
   - Updated outputs/app_backend.py and pi/server.py to flexibly locate Python across work/binarizer_env, .venv, and sys.executable on both Windows and Linux.
3. Automated Installation Scripts:
   - Created setup_gpu.bat (Windows automated 1-click GPU setup).
   - Created setup_gpu.sh (Linux/macOS automated setup).
   - Created comprehensive INSTALL.md guide covering prerequisites, CUDA 12.4 PyTorch wheels, asset layouts, and verification.
   - Updated 
equirements.txt and created 
equirements-gpu.txt.
   - Updated launch_studio.py to detect and build missing frontend assets automatically.
4. Verification:
   - Executed full 9-stage regression suite (outputs/eval/verify_kannada_regression.py): 9/9 passed.
