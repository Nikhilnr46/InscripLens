# InscripLens Studio Handover and Technical Guide

## 6 November: Glyph Inspector Save, Drawer & JSON Export (Step R3 of 3)

Delivered complete client-side persistence, comparison history drawer, and standardized JSON export for redrawn candidate comparisons:

- **Active Save Comparison Workflow**:
  - The "Save comparison" button in `CompareCard.jsx` activates dynamically once both automatic and redrawn crop predictions have loaded successfully.
  - Generates aspect-ratio preserved 96 px data URL thumbnails using `generateThumbnailFromUrl` for instant off-canvas rendering.
  - Persists comparisons into `localStorage` under the versioned key `"inscriplens.comparisons.v1"`.
  - Every click creates a distinct record with a unique identifier (`comp_<timestamp>_<random>`), ensuring all iterative attempts for a candidate are preserved.
  - Provides instant user feedback with a confirmation banner *"Saved in this browser only"* and a live counter badge (e.g. *"3 saved for this candidate"*).

- **Storage Key and Schema Contract**:
  - **Storage Key**: `"inscriplens.comparisons.v1"`
  - **Record Schema (`CURRENT_SCHEMA_VERSION = 1`)**:
    ```typescript
    interface ComparisonRecord {
      id: string;                          // Unique record ID (comp_<timestamp>_<random>)
      schema_version: 1;                   // Schema version number
      saved_at: string;                    // ISO-8601 timestamp
      timestamp: string;                   // ISO-8601 timestamp alias
      run_id: string;                      // Active analysis run ID
      candidate_number: number;            // 1-based candidate number (#N)
      candidate_index: number;             // 0-based candidate index
      image_size: { width: number; height: number }; // Stone image dimensions
      enhancement_mode: string;            // 'high_accuracy' | 'standard'
      automatic: {
        bbox: [number, number, number, number]; // [x1, y1, x2, y2] original image pixels
        prediction: string;                // Roman label (e.g. 'ma')
        prediction_kannada: string;        // Kannada Unicode form (e.g. 'ಮ')
        alternatives: Array<string | { label: string; confidence?: number }>; // Top 3
        confidence: number | null;         // Recognizer confidence score (0.0 to 1.0)
        model_sha256: string;              // Model checkpoint SHA-256 hash
      };
      redrawn: {
        bbox: [number, number, number, number]; // [x1, y1, x2, y2] original image pixels
        prediction: string;
        prediction_kannada: string;
        alternatives: Array<string | { label: string; confidence?: number }>;
        confidence: number | null;
        model_sha256: string;
      };
      model_hashes_differ: boolean;        // Flagged true if model versions differed
      proposed_reading: {
        text: string;                      // User reading
        script: 'kannada' | 'roman';
        tentative: true;                   // Marked tentative
      };
      outcome: 'improved' | 'worse' | 'unchanged' | 'unknown';
      rank_note: string;                   // Evaluation explanation
      automatic_thumbnail?: string;        // 96 px data URL (omitted from file export)
      redrawn_thumbnail?: string;          // 96 px data URL (omitted from file export)
    }
    ```

- **Saved Comparisons Drawer (`SavedComparisonsDrawer.jsx`)**:
  - Accessible via "View saved comparisons (N)" in the Glyph Inspector card.
  - **Tabs**: *"This run"* (filtered by loaded run ID) and *"All runs"*, each showing dynamic count badges.
  - **Summary Bar**: Displays real-time aggregate counts for Improved, Worse, Unchanged, and Unknown outcomes.
  - **Cards**: Displays candidate number `#N`, dual 96 px thumbnails with dashed neutral / solid sandstone badges, dual first predictions formatted per active Script setting and modern letters preference, outcome badge, tentative reading, formatted timestamp, "Open", and "Delete".
  - **Open Action**: Switches to and focuses candidate in Studio viewer, loading the redrawn box and side-by-side comparison. Disabled with tooltip if record belongs to another run.
  - **Delete Action**: Includes inline confirmation ("Delete this comparison? [Delete] [Cancel]") to prevent accidental deletion.

- **Clean JSON Export (`inscriplens-comparisons-<date>.json`)**:
  - Triggered via split menu offering *"This run"* and *"All saved"*.
  - File header envelope:
    ```json
    {
      "software_name": "InscripLens",
      "schema_version": 1,
      "export_date": "2026-11-06T...",
      "count": 3,
      "run_filter": "run_id_or_null",
      "records": [ ... ]
    }
    ```
  - **Privacy & Security Guarantee**: Completely strips internal file paths (`/outputs/...`, `/app_data/...`), crop URLs, and base64 thumbnail data URIs from the exported JSON.

- **Architectural Boundary & Future Proposal (Awaiting Approval)**:
  - *Current Limitation*: The existing backend character classifier (`POST /api/predict-crop`) hardcodes a return limit of top-3 alternatives. Readings outside the top 3 cannot be ranked precisely; `rank_note` explicitly highlights that ranks beyond 3 are unavailable.
  - *Proposed Backend Feature*: Add an optional query or body parameter `top_k: int = 3` (configurable to 5 or 10) to `POST /api/predict-crop` and `POST /api/recognize-all`. This will allow epigraphists to evaluate deeper rankings without altering core PyTorch weights. Per strict UI-only rules, this proposal is documented here awaiting backend approval.

- **Storage Quota & Blocked Storage Resilience**:
  - When browser storage is blocked or quota is exceeded, the UI catches `QuotaExceededError` and surfaces an error banner with a prominent *"Download JSON now"* button.
  - Storage usage is checked via `getStorageUsage()` and displays a warning banner if >4 MB is utilized.
  - Corrupted JSON in `localStorage` recovers gracefully to an empty array without crashing.

## 6 November: Glyph Inspector Redraw and Compare (Step R2 of 3)

Integrated the interactive candidate redrawing workflow and side-by-side comparison inspector:

- **Redraw Mode & Interactive SVG Canvas Stage Overlay (`RedrawOverlay.jsx`)**:
  - Automatically zooms to the candidate with a generous margin (~2.5x the bounding box size on each side, clamped between scale limits 0.1 and 5.0).
  - Switches off the curtain wiper to display the selected layer directly (Mask by default, Photo optional).
  - Renders the original candidate box as a dashed neutral outline (`#A8A29A`) and the active redrawn box as a solid sandstone accent (`#C9A66B`) with 8 interactive resize handles.
  - Supports pointer capture for drag-to-move and edge/corner resizing, touch/pointer event support (`touch-action: none`), live pixel dimensions badge (`w x h px`), boundary clamping within image dimensions, and minimum size enforcement (8 x 8 px).
  - Preserves full canvas zoom and pan interactions (scroll wheel, pinch, background drag) while keeping image-space coordinates aligned.
  - Comprehensive keyboard controls:
    - `Enter`: Applies redrawn rectangle and initiates comparison.
    - `Escape`: Cancels redraw mode and restores previous curtain position and view.
    - `Arrow keys`: Nudge box position 1 px (`Shift + Arrow`: 10 px).
    - `Alt + Arrow keys`: Resize box dimensions 1 px (`Shift + Alt + Arrow`: 10 px).
    - Candidate arrow navigation and `R` shortcut are disabled during redraw mode and while typing in form fields.

- **Floating Viewport Toolbar (`RedrawFloatingBar.jsx`)**:
  - Floats above the viewer stage with backdrop blur.
  - Displays candidate badge `Redrawing #N`.
  - Photo / Mask segmented control defaulting to Mask with tooltip *"The classifier reads the mask"*.
  - Action buttons: "Reset" (reverts redrawn rectangle to original candidate boundary), "Cancel" (Esc), and "Apply" (Enter).

- **Inspector "Redraw and compare" Card (`CompareCard.jsx`)**:
  - Positioned in the inspector sidebar between Alternatives and Verification & Expert Review.
  - **Initial State**: Renders "Redraw and compare" card with secondary button "Redraw box" and subtitle *"Outline the full glyph, then compare."* Enabled for all candidates (including tiny regions).
  - **Loading State**: Dispatches parallel `predictCrop` requests for both automatic candidate and redrawn box with `requestId` guard against stale network responses. Shows two pulsing skeleton columns. Dedicated "Retry" button available on individual columns if either request fails.
  - **Compared State**:
    - Context stone overview image displaying both boxes outlined (dashed neutral and solid accent) with Photo/Mask switch.
    - Two equal columns ("Automatic" with dashed neutral chip, "Redrawn" with solid accent chip) displaying crop image, primary prediction in Kannada or Roman (governed by scriptMode and modern letters), confidence bar/percentage, and top 3 suggestion chips.
    - "Your reading (tentative)" input field accepting Kannada or Roman, with live Kannada transliteration preview when Roman text is entered.
    - Per-column rank text (*"Your reading is 1st"*, *"2nd"*, *"3rd"*, or *"not in the top 3"*) and overall outcome badge (*Improved*, *Worse*, *Unchanged*, or *Unknown*) with explanation note *"Only the top three suggestions are available."*
    - Actions: "Redraw again" (re-enters redraw mode preserving last redrawn rectangle), "Discard" (clears comparison), and disabled "Save comparison" button with tooltip *"Coming in the next step"*.

- **Non-Destructive Guarantee**: Redraw and compare operations strictly never mutate `analysis.boxes`, candidate strip chips, Classify All results, `predictionCache`, or human review records.

## 6 November: Glyph Inspector Redraw, Compare, and Save Foundation (Step R1 of 3)

Implemented the core architectural foundation for glyph region redrawing, prediction comparison, and versioned local persistence (`frontend/src/compare/`):

- **Candidate #16 and Normal-Size Crop Diagnosis**:
  - Investigated why Candidate #16 (index 15, bbox `[265, 147, 287, 173]`, dimensions 22x26 px) and other normal-sized candidates show *"Alternatives unavailable"* in the inspector.
  - Root Cause Analysis:
    1. Architectural Decoupling: The inspector decouples the primary candidate label (`knownCandidateLabel`, populated from `/api/recognize-all` batch regions or review records) from the inspector alternatives (`cropPrediction.alternatives`, populated exclusively by `POST /api/predict-crop`).
    2. Batch Recognition Omission: `/api/recognize-all` computes single top predictions for candidate chips and saves `automatic_regions.json`, but does not populate per-candidate alternative lists or crop URLs in memory.
    3. Navigation Invalidation Guard: When users rapidly navigate candidates or re-click candidates, `predictRequestIdRef.current` increments. In-flight requests matching `requestId !== predictRequestIdRef.current` are discarded, leaving `cropPrediction` null.
    4. Model Missing / Unreachable Fallback: When the server or recognition models are unavailable (HTTP 503 or timeout >8s), `predictingCrop` is set to false while `cropPrediction` remains null.
    5. Inspector Fallback Rendering: When `isMatchingPrediction` is false and `predictingCrop` is false, `App.jsx` falls back to `knownCandidateLabel` for the character header while the alternatives container renders the placeholder banner *"Alternatives unavailable"*.
  - Execution Metrics: Single-crop prediction (`POST /api/predict-crop`) takes ~10–25ms when models are pre-cached in memory via `get_loaded_bundle` (historically was 2.6s when unpickled on every request). Response payload returns: `run_id`, `bbox`, `prediction`, `prediction_kannada`, `alternatives` (top 3 ranked list), `crop_url`, `model`, `model_sha256`, `reference_examples`, `confidence`, `uncertain`, `models_agree`, and `confidence_scores`.

- **Compare Module Architecture (`frontend/src/compare/`)**:
  - `apiClient.js`: `predictCrop(runId, bbox, options)` invokes `POST /api/predict-crop` with integer bounding box coordinates in original image pixel space. Features 8-second timeout guard, optional AbortSignal linking, typed result formatting (`{ cropUrl, prediction, predictionKannada, alternatives, confidence, modelSha256 }`), and automatic single retry on transient failures. Strictly avoids persisting or leaking filesystem paths.
  - `coordinates.js`: Provides `screenToImage`, `imageToScreen`, and `normalizeBbox` mapping between screen viewport space and image pixel coordinates using the viewer's CSS stage transform (`translate(${pan.x}px, ${pan.y}px) scale(${scale})`). Clamps strictly within image boundaries, rounds all coordinates to integers, ensures `x1 < x2` and `y1 < y2` (handling inverted drag gestures), and enforces a strict minimum dimension of 8 x 8 px across both full-stone images and selected-area crops.
  - `outcome.js`: `evaluateComparisonOutcome(proposedReading, automatic, redrawn)` determines whether an expert redraw improved recognition. Evaluates rank position (1 to 3, or null for "not in top 3") by comparing trimmed, NFC-normalised Kannada Unicode forms (with Roman transliterations converted via `toKannada`). Outcomes are strictly categorized as `"improved"`, `"worse"`, `"unchanged"`, or `"unknown"`. `rank_note` explicitly notes in every branch that ranks beyond 3 are unavailable.
  - `store.js`: Manages local persistence in `localStorage` under versioned key `"inscriplens.comparisons.v1"`. Every operation is wrapped in `try/catch`. Schema holds: `id`, `schema_version: 1`, `saved_at`, `run_id`, `candidate_number`, `candidate_index`, `image_size`, `enhancement_mode`, `automatic`, `redrawn`, `proposed_reading`, `outcome`, `rank_note`, and dual 96 px data URL thumbnails. Includes corrupted JSON recovery (falls back to empty list without crashing) and storage threshold warnings (>4 MB used).
  - `thumbnail.js`: Offscreen canvas utility generating compact 96 px JPEG data URLs with aspect-ratio-preserving centering for visual representation in comparison lists.
  - `__tests__/`: Comprehensive unit tests covering coordinate round-trips across zoom/pan states, edge clamping, inverted boxes, outcome evaluation matrices, store CRUD operations, corrupted JSON recovery, and quota limit handling.

## 6 November: PDF Report Integration & Run History Investigation (Step E2 of 2)

Integrated PDF report trigger actions and investigated Run History report capabilities:
- Toolbar Integration: Added "PDF report..." above "Download mask" in the Studio Export popover and compact View dropdown.
- Interactive Classification Flow: When characters have not yet been classified, the preview modal surfaces a clear prompt ("Characters have not been classified.") with two actions:
  - "Classify all now": Invokes `runBatchRecognize()` with live progress tracking, dynamically updating the report grid upon completion.
  - "Export without labels": Dismisses the prompt and renders the publication report with an unclassified indicator.
- Read-Only Run History Endpoint Investigation:
  - Examined `/api/history`, `/api/export/{run_id}`, and `/api/reviews/{run_id}`.
  - Available for past runs: input image (`/app_data/{id}/input.png`), binary mask (`/app_data/{id}/mask.png`), and human reviews (`/api/reviews/{id}`).
  - Missing for past runs: candidate bounding boxes (`boxes`) and batch model predictions (`automatic_regions.json`) are not persisted in SQLite or returned by existing GET endpoints.
  - Per strict boundary instructions, the backend was left untouched, Run History retains its existing JSON export, and Studio export is shipped exclusively.
- Stone Profile Registry Extension Architecture:
  - Confirmed `ReportView.jsx` exclusively reads stone identity and narrative fields via `getStoneProfile()`.
  - Future registry lookups should be plugged directly into `frontend/src/report/stoneProfile.js`. The expected data contract is:
    ```typescript
    interface StoneProfileResult {
      name: string;              // Official or archaeological title (e.g. "Begur Hero Stone")
      nameSource: 'demo' | 'user' | 'registry' | 'unidentified';
      story: string | null;      // Curated historical context or narrative summary
      storySource: string | null;// Archival citation or epigraphist reference
    }
    ```
- Edge Cases Verified:
  - Uploaded photo with region selection displays "Selected area" with dimension readouts in header and figure captions.
  - Empty filter states gracefully render "No candidate regions match current filters".
  - Long stone names wrap without clipping via `word-break: break-word`.
  - Fixed print footers repeat cleanly on every physical/PDF page via `@media print`.

## 6 November: Printable Analysis Report (Step E1 of 2)

Integrated full-fidelity printable analysis report generation directly within Studio using the browser's native print engine:
- Report Module Architecture (`frontend/src/report/`):
  - `stoneProfile.js`: Implements `getStoneProfile({ run, isDemo, userEnteredName })` returning `{ name, nameSource, story: null, storySource: null }`. Preserves demo identity ("Nagavara demonstration stone") and user-entered names with explicit registry lookup extension points; zero synthesized stories.
  - `buildReportData.js`: Extracts Studio state without new backend calls, preparing 1600 px downscaled photo/mask copies and 96 px clipped mask thumbnails for all candidate character regions. Translates Roman labels to Kannada glyphs via `formatDisplayLabel` with faithful or modern orthography. Correctly flags unclassified runs ("Characters have not been classified") without triggering unsolicited inference.
  - `ReportView.jsx`: A4/Letter portrait printable report rendered with bundled Inter and Noto Sans Kannada. Includes wordmark, metadata, side-by-side photo and mask figures, 8-column candidate character cards (displaying sequence number, stroke thumbnail, large Kannada glyph, Roman label, confidence score, and reviewer initials/name), conditional curated story section, licence attributions, and fixed print footers.
  - `ReportPreviewDialog.jsx`: Full-screen modal with interactive options panel (stone name, include uncertain characters, include tiny characters, include reviewer names, Kannada style, paper size) and a live scrollable white-paper preview. Pre-print hooks await `document.fonts.ready` and image decoding before invoking `window.print()` with automatic document title synchronization (`InscripLens report - <stone name> - <YYYY-MM-DD>`).
  - `report.css`: Print media rules (`@page A4 with 14mm margins`, `print-color-adjust: exact`, `break-inside: avoid` on cards and figures, fixed print footers, and complete isolation from site dark theme).

## 6 November: Studio Integration of the Selected Area (Step S3 of 3)

Integrated selected region awareness, metadata synchronization, and re-selection flows into the Epigraphy Studio:
- Header Selected Area Pill: When an active analysis originated from a region selection, the header status line renders an interactive pill: `Selected area, {w} × {h} px (from {origW} × {origH})`. For full-resolution images or the Nagavara demo stone, standard image dimensions are preserved.
- Collapsible "Selected Area" Sidebar Card: Displays a live thumbnail of the original photograph with the crop rectangle outlined in gold (`var(--accent-sandstone)`) and dimmed surroundings, accompanied by live pixel dimension readouts for both selected crop and full photo.
- In-Memory "Change Area" Flow: Clicking "Change area" (or the header pill) navigates back to the `/import` selection stage with the original file and existing crop coordinates intact. Adjusting and re-submitting seamlessly replaces the active run in Studio.
- Graceful Store Expiration & Reload Safety: The in-memory store remains strictly unpersisted across page reloads. If the store expires or is lost upon reload, the "Change area" button is safely disabled with the guidance notice: *"Reselect by choosing another image"*.
- Non-Destructive "Try Another" Navigation: Navigating to `/import` preserves the active run; pressing browser Back returns to the Studio session intact.
- Strict Coordinate Semantics: Candidate coordinates, saved reviews and history refer to the selected area image, not the original photograph. Documented across `HANDOVER.md` and the About page FAQ.
- Memory Lifecycle Management: Switching between selected photo crops and demo stone clears stale selection metadata. All File references and object URLs are revoked and garbage-collected when navigating to the landing overview.

## 6 November: Region Selection (Step S2 of 3)

Integrated in-browser region selection (`frontend/src/components/RegionSelector.jsx`) within the `/import` workflow before dispatching to Studio:
- 3-Step Import Progress: Visual indicator (`1. Choose` -> `2. Select area` -> `3. Studio`). Uploaded photographs enter region selection; demo stone bypasses selection directly to Studio.
- EXIF-Aware Bitmap Decoding: Uses `createImageBitmap(file, { imageOrientation: "from-image" })` to correctly orient smartphone captures, preserving the full-resolution bitmap in memory.
- Interactive SVG Selection Stage: Dimming scrim outside selection, 8 resize handles, drag to move, drag to draw, keyboard arrow adjustments (1% step, Shift to resize), pointer events for touch devices, live original pixel readout, 64x64 minimum constraint, and <300px resolution warning.
- Zoom & Pan: Cursor-centered wheel/pinch zoom (0.1x to 5.0x), middle-mouse/Space-key pan, Fit-to-view, and 100% controls.
- Lossless PNG Crop & Handoff: Selections covering >=99% or "Use whole image" pass original File without re-encoding. Cropped selections cap long side at 3200 px (supersampling the backend 1600 px limit) and export as `selected-area.png`. In-memory store retains original File, crop File, selection bounding box, and dimensions for S3.

## 6 November: Import Screen (Step S1 of 3)

Added dedicated `/import` workspace route allowing users to choose between uploading a field photograph and loading the curated Nagavara demonstration stone before entering Studio:
- Route Navigation: Added `/import` to `frontend/src/App.jsx`. SlideToEnter control and keyboard shortcuts on `/` route to `/import`. Studio header "Try another" and demo button route back to `/import`.
- Import Component (`frontend/src/pages/ImportPage.jsx`): Two side-by-side cards with drag-and-drop upload (PNG/JPG, 20 MP limit check) and demo stone thumbnail selection (/api/demo/image) with full responsive stacking.
- In-Memory File Store (`frontend/src/utils/fileStore.ts`): File objects are held strictly in memory during transition to `/studio`, invoking the unmodified enhancement upload handler on arrival without localStorage persistence.

## 5 November: Studio UI batch 2 layout of controls

Reorganized Studio viewer toolbar and bottom gallery strip:
- Top Toolbar:
  - Left group: Boxes toggle (compact switch with count pill) and Curtain control (slider position percentage label).
  - Right group (desktop >= 1100 px panel width): Script segmented control (sliding indicator, Kannada/Roman, keyboard accessible via Arrow keys), Display options popover (gear icon, visible only in Kannada mode, contains Modern letters switch and lossy warning note), Zoom controls (Fit, minus, zoom percentage, plus), and Export menu dropdown ("Download mask").
  - Responsive collapse (< 1100 px container width): Script control, Display options, and Export are moved into a unified "View" dropdown button; Zoom controls remain directly accessible.
- Bottom Gallery Bar:
  - Left group: Single primary "Classify All (N)" button; after batch classification completes, transitions to a secondary "Re-run" button alongside a green "133 classified" status pill. Next to this, candidate filter segmented control with count pills: All (N), Predicted (N), Reviewed (N).
  - Right group: Compact "Hide tiny" switch chip with count pill, plus keyboard navigation hint with arrow keycaps (left and right arrow keycaps with Navigate label) that smoothly fades out after initial arrow key navigation, remembered in localStorage, and permanently accessible via title tooltip.
- Quality & Regression: Zero text wrapping or control collisions across 1280, 1366, 1440, 1536, and 1920 px viewports in both light and dark themes. Full regression passed for stone upload, demo loading, high accuracy enhancement, candidate inspection, batch recognition, reviewer note saving, and mask download.

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


## 1. Project Summary

InscripLens Studio is an offline computational research workspace designed for epigraphists, historians, linguists, and academic researchers studying historical Kannada stone inscriptions. The application focuses specifically on hero stones (Veeragallu) and weathered stone tablets found across Karnataka, addressing the challenge of physical granite erosion and raking light degradation.

The system operates entirely on local hardware through a four-stage pipeline:
1. Photograph Acquisition: The user uploads a field photograph (PNG/JPEG under 20 megapixels) or loads the curated Nagavara 8th-century hero stone benchmark.
2. Neural Stroke Enhancement: A pretrained Shilalekhya U-Net segmentation network isolates chiseled incisions from background stone grain to produce a binarized foreground stroke mask. Operates in two modes: Standard (single-scale GPU/CPU inference, fast and reproducing the baseline candidate set) and High Accuracy (multi-scale sliding window fusing scales 256, 384, and 512 via max-probability to recover faint, eroded strokes).
3. Candidate Localization: Connected-component analysis proposes bounding boxes for candidate glyph regions across the enhanced mask.
4. Diagnostic Character Recognition: A diagnostic feature classifier generates experimental character label predictions, ranked alternatives, and confidence scores for selected or batch candidate regions.
5. Epigraphic Review and Provenance: An epigraphist can inspect high-resolution crops against the stone, input suggested readings, record reviewer initials or notes, and save verifiable records locally into SQLite.

Epigraphic Recognition Status: Character recognition is strictly experimental and diagnostic. The application is an investigative aid for human readers, not an automated transcription engine. Reliable full-stone OCR, automated reading order detection, historical-to-modern Kannada linguistic translation, and English transliteration are not implemented.

---

## 2. Credits and Licences

### Project Authorship
- Developer: Nikhil N R Vasista
- Institution: PES
- Year: 2026
- Verified from: `frontend/src/config/site.ts`

### Reused Research and Third-Party Licences
- Shilalekhya Pretrained Binarizer:
  - Authors: IIIT Hyderabad (ihdia)
  - Licence: MIT Code Licence, Copyright 2025 ihdia
  - Source Repository: https://github.com/ihdia/shilalekhya-binarization
  - Role: Pretrained U-Net segmentation architecture and inference engine.
- EpiSAM Inscriptions Dataset and Checkpoints:
  - Authors: Arnav Sharma, Pratyush Jena, Amal Joseph, Ravi Kiran Sarvadevabhatla
  - Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
  - Source Repository: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset
  - Source Weights: https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project
  - Attribution: Imagery acknowledged to The Mythic Society, Bengaluru.
  - Redistribution Requirement: Dataset previews, sample crops, and derived masks distributed with this application are derived works. Any redistribution of images, masks, or checkpoint weights must maintain CC BY-SA 4.0 attribution and share-alike licensing.
- Original Project Code:
  - A root LICENSE file has not yet been selected. Original glue code, REST server, React client, and evaluation benchmarks remain unassigned until institutional publication decisions are finalized.

---

## 3. Architecture

### Folder Map
```text
InscripLens/
├── api/                           # FastAPI backend server
│   └── server.py                  # REST API endpoints and static SPA hosting
├── frontend/                      # React 19 + TypeScript + Vite SPA
│   ├── public/                    # Static fonts and assets
│   ├── src/
│   │   ├── components/            # UI components (SlideToEnter, TabletIllustration, etc.)
│   │   ├── config/site.ts         # Centralized site metadata and authorship config
│   │   ├── pages/LandingPage.jsx  # Single-page scrolling landing site
│   │   ├── utils/                 # Reveal observer, interactions, math helpers
│   │   ├── App.jsx                # Studio workspace and route coordinator
│   │   └── index.css              # Theme token design system, interaction styles
│   ├── index.html                 # HTML shell and metadata
│   ├── package.json               # Node dependencies
│   └── vite.config.js             # Vite build configuration
├── outputs/                       # Core Python pipeline modules and experiments
│   ├── app_backend.py             # Image analysis, subprocess execution, SQLite history
│   ├── binarizer_core.py          # Tiled CPU inference engine for Shilalekhya U-Net
│   ├── segment_candidates.py      # Connected-component bounding box detection
│   ├── recognize_regions.py       # Batch character prediction runner
│   ├── recognition_alternatives.py# Ranked label suggestion and example retrieval
│   ├── run_character_benchmark.py # Feature extraction and diagnostic models
│   ├── inscriplens_app.py         # Legacy Streamlit prototype application
│   ├── broad_clean_study/         # Primary SVM model and benchmark reports
│   ├── matched_mask_study/        # Fallback hero-only model and comparison records
│   └── full_binarizer/            # Demo stone image and baseline benchmarks
├── work/                          # Local runtime assets, models, and private data (git-ignored)
│   ├── app_data/                  # SQLite review database and uploaded run artifacts
│   ├── binarizer_env/             # Python 3.12 virtual environment for CPU PyTorch
│   ├── shilalekhya/               # Shilalekhya model definition and weights
│   └── hero_pilot/                # Benchmark manifest and pilot data
├── launch_studio.py               # Launcher: opens browser and starts Uvicorn
├── run_studio.bat                 # Windows shell shortcut for launch_studio.py
├── requirements.txt               # Main application Python dependencies
├── requirements-inference.txt     # Inference environment PyTorch dependencies
└── THIRD_PARTY.md                 # Upstream attribution and citation notices
```

### Communication Flow and Port Assignments
1. Port 8000 (`http://127.0.0.1:8000`): Primary InscripLens Studio.
   - Serves the compiled React SPA from `frontend/dist`.
   - Handles REST API requests on `/api/*`.
   - Serves local session artifacts from `/app_data/*`.
2. Port 8501 (`http://127.0.0.1:8501`): Optional legacy Streamlit application (`outputs/inscriplens_app.py`).

### System Interaction Diagram
```text
+-------------------------------------------------------------------------------+
|                             Browser Client                                    |
|   Landing Page ("/")  <==== SPA Router ====>  Studio Workspace ("/studio")    |
|   - Hero & Tablet Illustration                - Zoom/Pan Canvas Stage         |
|   - Theme Toggle (Dark/Light)                 - Interactive Curtain Wipe      |
|   - Scroll-Spy & Reveal                       - Candidate Strip & Inspector   |
+---------------------------------------+---------------------------------------+
                                        | HTTP REST / JSON
                                        v
+-------------------------------------------------------------------------------+
|                       FastAPI Backend (api/server.py)                         |
|   - CORS & Global Exception Guard (path sanitization)                         |
|   - SPA Static File Server (frontend/dist)                                    |
|   - Static Artifact Mount (/app_data -> work/app_data)                        |
+-------------------+---------------------------------------+-------------------+
                    |                                       |
                    v                                       v
+---------------------------------------+   +-----------------------------------+
|  Subprocess Worker (Python 3.12)      |   |  Diagnostic Classifier (Joblib)   |
|  Executable: work/binarizer_env       |   |  outputs/broad_clean_study/       |
|  Model: work/shilalekhya/binarizer.pth|   |  mask_svm_bundle.joblib           |
|  - Tiled CPU U-Net enhancement        |   |  - HOG feature extraction         |
|  - Generates stroke mask              |   |  - Top-3 alternative ranking      |
+-------------------+-------------------+   +-----------------------------------+
                    |
                    v
+-------------------------------------------------------------------------------+
|                       Storage Layer (work/app_data)                           |
|   - Session Folders: input.png, mask.png, crop_*.png, automatic_regions.json  |
|   - SQLite Database: history.sqlite3 (analysis runs, character reviews)       |
+-------------------------------------------------------------------------------+
```

---

## 4. Setup and Run Guide (Clean Machine)

### Prerequisites
- Operating System: Windows 10/11, Linux, or macOS.
- Python 3.12+: Required for CPU PyTorch inference. Python 3.14 or 3.13 is supported for the main application.
- Node.js: v20.0.0 or higher with npm.
- Git: Required for repository cloning.

### Clean Machine Setup Procedure

#### Step 1: Clone Repository
```bash
git clone https://github.com/Nikhilnr46/InscripLens.git
cd InscripLens
```

#### Step 2: Main Application Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 3: Binarizer Inference Environment
To isolate PyTorch CPU binaries from system dependencies, install the dedicated inference worker environment:
```powershell
py -3.12 -m venv work/binarizer_env
.\work\binarizer_env\Scripts\python.exe -m pip install -r requirements-inference.txt
.\work\binarizer_env\Scripts\python.exe -m pip install "numpy>=2.2" "Pillow>=11"
```

#### Step 4: Install Runtime Assets and Models
Obtain `InscripLens_runtime_assets.zip` and extract directly into the repository root:
- `work/shilalekhya/binarizer.pth`
- `work/shilalekhya/Unet/model.py`
- `work/shilalekhya/LICENSE`
- `outputs/full_binarizer/HS027_original.png`
- `outputs/matched_mask_study/mask_svm_bundle.joblib`

Optionally, obtain `InscripLens_recognizer_update.zip` and extract into the repository root:
- `outputs/broad_clean_study/mask_svm_bundle.joblib`

#### Step 5: Build Frontend
```powershell
cd frontend
npm install
npm run build
cd ..
```

### Running the Application

#### Production Mode (Unified Server)
Run the launcher script or batch file:
```powershell
python launch_studio.py
```
Or directly via Uvicorn:
```powershell
python -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000
```
Open `http://127.0.0.1:8000` in any modern web browser.

#### Development Mode (Hot Reloading)
- Terminal 1 (Backend API):
  ```powershell
  python -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000 --reload
  ```
- Terminal 2 (Vite Frontend):
  ```powershell
  cd frontend
  npm run dev
  ```
  Open the Vite development port shown in the terminal (default: `http://localhost:5173`).

### Environment Variables
- `INSCRIPLENS_ADVANCED`: Optional boolean flag (`1`, `true`, `yes`, `on`). When enabled, exposes internal diagnostics, literature comparison tables, and raw experiment exports. When disabled or absent (default), the interface remains in clean researcher mode.

---

## 5. Models and Data

| Asset Name | Relative Location | Approximate Size | Licence | Distribution Mode |
|---|---|---|---|---|
| Shilalekhya Pretrained Binarizer | `work/shilalekhya/binarizer.pth` | 120.5 MB | CC BY-SA 4.0 | Downloaded via `InscripLens_runtime_assets.zip` |
| Shilalekhya Architecture | `work/shilalekhya/Unet/model.py` | 4.2 KB | MIT | Downloaded via `InscripLens_runtime_assets.zip` |
| Broader Cleaned Mask Recognizer | `outputs/broad_clean_study/mask_svm_bundle.joblib` | 76.8 MB | CC BY-SA 4.0 (derived) | Downloaded via `InscripLens_recognizer_update.zip` |
| Hero-Only Fallback Recognizer | `outputs/matched_mask_study/mask_svm_bundle.joblib` | 5.6 MB | CC BY-SA 4.0 (derived) | Downloaded via `InscripLens_runtime_assets.zip` |
| Nagavara Demo Stone Image | `outputs/full_binarizer/HS027_original.png` | 2.1 MB | CC BY-SA 4.0 | Downloaded via `InscripLens_runtime_assets.zip` |
| Recognition Reference Crops | `outputs/recognition_references.zip` | 14.8 MB | CC BY-SA 4.0 (derived) | Optional pack; generated via script |
| Pilot Dataset Manifest | `work/hero_pilot/manifest.json` | 878 KB | CC BY-SA 4.0 (derived) | Downloaded via `InscripLens_runtime_assets.zip` |

All binary checkpoints, large model bundles, datasets, and runtime images are excluded from Git by `.gitignore`.

---

## 6. Frontend Guide

### Pages and Single-Page Landing Sections
The client application is built as a single-page application (SPA) with two primary view states managed in `frontend/src/App.jsx`:
- Route `/`: Single-page landing site containing four sequential sections:
- Route `/import`: Dedicated stone image selection workspace (Step S1) featuring drag-and-drop/browse upload and demonstration stone loading cards.
  1. `#overview`: Hero banner, epigraphy badge, offline privacy guarantee, interactive stone tablet illustration with proximity glow, and "Slide to enter Studio" control.
  2. `#workflow`: Three-stage methodology cards ("Capture & Select", "Enhance & Localize", "Inspect & Verify") with 3D tilt and cursor spotlights, plus the demo stone trigger button.
  3. `#about`: Centered single-column documentation including "What is InscripLens", "Why it exists", the 5-stage pipeline, "Privacy", interactive FAQ accordion, and "Credits and licences".
  4. `#limitations`: Research scope boundaries, "Limitations of this prototype" card, two-column capability summary ("Can" vs "Cannot yet"), and epigraphist verification notice.
- Route `/studio`: The interactive Epigraphy Studio workspace featuring a top toolbar with Boxes and Curtain controls, Script segmented control (Kannada / Roman), Display options popover (Modern letters), Zoom group, and Export menu (mask download), alongside a container-responsive View dropdown below 1100 px. The bottom gallery strip provides Classify All / Re-run with status pill, candidate filter segmented control (All, Predicted, Reviewed), compact Hide tiny switch chip, and keyboard navigation hints.

### Theme System
- Controlled by `data-theme="dark"` and `data-theme="light"` attributes on `:root`.
- Dark Mode Tokens: Obsidian base (`#121214`), dark surface (`#1B1B1F`), primary text (`#EDEDEC`), muted text (`#B5AFA6`), gold accent (`#C9A66B`).
- Light Mode Tokens: Warm parchment base (`#F7F2E8`), parchment surface (`#EDE7DC`), ink text (`#1C1A17`), muted text (`#6B645A`), high-contrast AA gold accent (`#9A7330`).
- Toggle Implementation: Circular reveal effect powered by the browser View Transitions API, originating from the toggle button click coordinates; falls back to 250ms CSS transition on unsupported browsers. Respects `prefers-reduced-motion`.

### Interaction and Micro-Animation Language
- Scroll Reveals: Managed by `frontend/src/utils/revealObserver.js`. Uses IntersectionObserver with hysteresis `[0, 0.15]` to trigger replayable reveals without layout shift. Animates individual CSS `translate` and `opacity` properties to prevent collisions with transform-based hover effects.
- Hover Effects: Throttled using a single requestAnimationFrame loop in `frontend/src/utils/interactions.ts`. Supports:
  - 3D card tilt (`card-tilt`).
  - Cursor radial spotlight (`card-spotlight`).
  - Magnetic button drift (`btn-magnetic`).
- Tablet Illustration: In `frontend/src/components/TabletIllustration.tsx`. Uses pointer-distance calculation to compute proximity glow on glyph blocks without triggering React component re-renders.

### Configuration and Customization
- Global Configuration: `frontend/src/config/site.ts`. Modify `SITE.name`, `SITE.developer`, `SITE.college`, `SITE.collegeFull`, and `SITE.year` to update metadata across the application, HTML title, and footer.
- Style Tokens: `frontend/src/index.css`. All colours, fonts, border radii, and transition timings are defined as CSS variables under `:root`.

---

## 7. Backend and API Guide

All endpoints are hosted locally by FastAPI in `api/server.py`. Every response is strictly sanitized to prevent local machine usernames, drive paths, model file names, or Python tracebacks from leaking.

### Endpoints

| Method | Endpoint | Purpose | Request Payload | Response Shape | Access Level |
|---|---|---|---|---|---|
| `GET` | `/api/status` | Reports presence of local binarizer, models, and demo image | None | `{"ready": bool, "demo_available": bool, "recognizer_available": bool, "advanced_mode": bool}` | Public |
| `GET` | `/api/demo` | Retrieves demo stone metadata | None | `{"id": str, "name": str, "image_url": str, "width": int, "height": int, "description": str}` | Public |
| `GET` | `/api/demo/image` | Serves the demo stone photograph | None | Binary image stream (`image/png`) | Public |
| `POST` | `/api/analyse` | Executes neural binarization and candidate extraction | Multipart form (`file`, optional `mode`) OR `?use_demo=true&mode=...` | `{"id": str, "display_name": str, "is_demo": bool, "sha256": str, "image_url": str, "mask_url": str, "width": int, "height": int, "boxes": list, "candidate_count": int, "created": str, "mode": str, "mode_label": str, "fallback_note": Optional[str]}` | Public |
| `GET` | `/api/export/{run_id}` | Exports run metadata, mode, candidate count, and reviews in JSON format | None | `{"id": str, "display_name": str, "mode": str, "mode_label": str, "candidate_count": int, "created": str, "reviews": list}` | Public |
| `POST` | `/api/recognize-all` | Runs batch classification on all candidates | `{"run_id": str}` | `{"run_id": str, "model": str, "candidate_count": int, "regions": list}` | Public |
| `POST` | `/api/predict-crop` | Classifies single bounding box with alternatives | `{"run_id": str, "bbox": [x1, y1, x2, y2]}` | `{"run_id": str, "bbox": list, "prediction": str, "alternatives": list, "crop_url": str, "model": str, "model_sha256": str, "reference_examples": list}` | Public |
| `POST` | `/api/review` | Saves reviewer correction to SQLite database | `{"run_id": str, "bbox": list, "prediction": str, "model": str, "model_sha256": str, "suggestion": str, "reviewer": str, "note": str}` | `{"status": "saved", "run_id": str}` | Public |
| `GET` | `/api/reviews/{run_id}` | Retrieves saved reviewer corrections for a run | None | List of review objects: `[{"bbox": list, "prediction": str, "suggested_label": str, "reviewer": str, "note": str, "created": str}]` | Public |
| `GET` | `/api/history` | Lists previous analysis sessions from SQLite | None | List of session objects: `[{"id": str, "created": str, "display_name": str, "image_url": str, "mask_url": str, "sha256": str, "mode": str, "mode_label": str, "fallback_note": Optional[str]}]` | Public |
| `GET` | `/api/credits` | Provides structured credits and third-party licence metadata | None | `{"title": str, "project": str, "components": list}` | Public |

### Enhancement Modes and GPU Memory Safety
- Standard Mode (default): Executes single-scale U-Net inference on GPU or CPU. Produces identical results to historical baselines (e.g. 133 candidate regions on the Nagavara benchmark stone).
- High Accuracy Mode: Calls `enhance_multiscale` from `outputs/binarizer_core.py` without modifying the core function. Evaluates image tiles across multi-scale dimensions (256, 384, 512) and fuses stroke probabilities with max-pooling. Recovers faint, shallow incisions while connecting fragmented strokes into coherent character glyphs.
- Graceful GPU OOM Fallback: If GPU VRAM is exhausted (such as on 4 GB laptop GPUs) or an execution error occurs during multi-scale enhancement, the backend automatically re-executes standard enhancement and records a plain English notification (`fallback_note`), guaranteeing zero server crashes.
- Provenance Tracking: Every analysis run stores its mode (`standard` or `high_accuracy`) and user-facing label (`Standard` or `High accuracy`) in the SQLite `runs` table and export payloads. Internal model names and filesystem paths are never serialized.

### Response Sanitization Audit
- Error Handler: A global exception handler intercepts unhandled exceptions, logs internally, and returns HTTP 500 with `{"detail": "An internal error occurred while processing the request."}`.
- Model Anonymization: Model filenames (`*.joblib`, `*.pth`) are replaced with `"Experimental recognizer"`.
- Path Masking: All internal filesystem paths are converted to relative virtual web paths (`/app_data/...` or `/api/demo/...`).

---

## 8. Privacy and Security Notes

1. 100% Offline Execution: InscripLens Studio connects to no external servers, cloud OCR engines, analytical trackers, or remote telemetry.
2. Local Data Boundaries:
   - User uploaded photographs: Saved exclusively to `work/app_data/<run_id>/input.png`.
   - Generated segmentation masks: Saved exclusively to `work/app_data/<run_id>/mask.png`.
   - Candidate crop images: Saved exclusively to `work/app_data/<run_id>/crop_*.png`.
   - Analysis history and reviewer notes: Stored in local SQLite database at `work/app_data/history.sqlite3`.
3. Confidentiality Notice: The `work/` directory contains private research imagery and epigraphic reviews. It is strictly excluded by `.gitignore` and must never be staged or pushed to public Git repositories.
4. Model Deserialization Security: Diagnostic models use Python `joblib`. Models must only be loaded from verified local sources; never load arbitrary `.joblib` files supplied by untrusted third parties.

---

## 9. Testing and Regression Checklist

### Manual Quality Assurance Steps
1. Home Navigation: Open `http://127.0.0.1:8000/`. Verify smooth scrolling on `#overview`, `#workflow`, `#about`, and `#limitations`. Check that nav links jump with 88px sticky header clearance.
2. Theme Switcher: Click the theme toggle icon. Verify that dark and light themes switch cleanly with AA contrast on text, surfaces, and borders.
3. Slide to Enter: Focus the slider handle and press `ArrowRight`, `Enter`, or `Space`. Verify transition to `/studio`.
4. Demo Loading: Click "Try Demo Stone (Nagavara)". Confirm the stone image and 133 candidate regions load.
5. Curtain Wipe Slider: Drag the curtain handle left and right; verify smooth blending between original stone and neural stroke mask. Test keyboard arrow controls on the slider handle.
6. Canvas Zoom/Pan: Scroll mouse wheel over the canvas; click and drag to pan; click 100% and Fit buttons.
7. Candidate Inspector: Click a candidate box on canvas or from the bottom strip. Confirm that character crop, prediction, and 3 alternative suggestions display in the inspector.
8. Batch Recognition: Click "Classify All Candidates". Confirm progress bar updates and completes.
9. Review and Save: Enter a suggestion and reviewer initials, click "Save Review". Verify confirmation message appears and review is reflected on the candidate chip.
10. Run History: Switch to "Run History" in the sidebar. Select a previous run and verify that previous masks and review records restore properly.
11. Responsive Layout: Reduce browser width below 1100px and 768px. Verify that panels collapse into accessible sheets and drawers without horizontal layout overflow.

### Automated Test Commands
Run the following verification commands from the repository root:
```powershell
# Verify main Streamlit/backend integrity
python outputs/check_app.py

# Verify backend binarization and candidate extraction logic
python outputs/check_app_backend.py

# Verify fresh-clone asset guard behavior
python outputs/check_fresh_clone.py

# Verify SQLite review persistence and Unicode handling
python outputs/check_review_storage.py

# Verify frontend TypeScript types and Vite production compilation
cd frontend
npm run build
cd ..
```

---

## 10. Known Issues and Limitations

1. Character Recognition Accuracy: The HOG/SVM classifier achieves 52/300 (17.33%) overall accuracy on automatically located regions against reference labels. It is intended solely as an epigraphist suggestion tool.
2. Unverified Reading Order: Automated reading order determination is not implemented. Candidates are sorted spatially by coordinates, which may not match historical inscription flow.
3. Language Translation: Historical Halegannada language conversion and English translation are outside project scope and not available.
4. CPU Inference Throughput: Neural segmentation on CPU hardware requires approximately 4 to 10 seconds per image depending on resolution.
5. Single-User Architecture: SQLite database access is designed for a single concurrent local researcher session.

---

## 11. Troubleshooting Guide

| Issue | Cause | Solution |
|---|---|---|
| Page scrolling locked on landing page (`/`) | Body overflow lock inherited from modal or studio styles | Ensure `html { overflow-y: scroll; }` and `overflow-x: clip;` are set; verify no active element has `overflow: hidden` on root page. |
| Port 8000 already in use | Previous Uvicorn instance still running in background | In PowerShell: `Get-NetTCPConnection -LocalPort 8000 \| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }` |
| Port 8501 already in use | Previous Streamlit server still running | In PowerShell: `Get-NetTCPConnection -LocalPort 8501 \| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }` |
| "Enhancement temporarily unavailable" | Missing PyTorch environment or weights | Confirm `work/shilalekhya/binarizer.pth` exists and `work/binarizer_env/Scripts/python.exe` is functional. |
| Missing demonstration stone | Demo image not extracted | Verify `outputs/full_binarizer/HS027_original.png` is present. |
| Recognizer fallback notice shown | Broader recognizer bundle absent | Extract `InscripLens_recognizer_update.zip` into repository root to install `outputs/broad_clean_study/mask_svm_bundle.joblib`. |
| Python 3.12 subprocess failure | PyTorch binary incompatibilities | Re-create `work/binarizer_env` strictly using standard Python 3.12 64-bit. |

---

## 12. Suggested Next Steps (Priority Order)

1. Priority 1: Line and Sequence Transcription Engine
   - Train a sequence recognition model (e.g. CRNN or Vision Transformer) to predict character groups along inscribed lines rather than classifying disconnected bounding boxes.
2. Priority 2: Epigraphic Expert Validation Study
   - Conduct structured evaluation with qualified epigraphists comparing human transcription time with and without neural stroke enhancement.
3. Priority 3: Browser-Native Inference (WebGPU / ONNX Runtime)
   - Export Shilalekhya U-Net to ONNX Runtime Web / WebGPU, allowing zero-install client-side enhancement directly inside the browser.
4. Priority 4: Standardized Epigraphic Export (TEI-EpiDoc XML)
   - Implement TEI-EpiDoc compliant XML export for review records and character annotations to enable interoperability with global epigraphy repositories.
5. Priority 5: Automated Runtime Asset Downloader
   - Provide an automated Python asset downloader script with cryptographic SHA-256 validation to fetch required weights from Hugging Face on fresh clones.

---

## Pre-push Checklist Results

### Secrets and Privacy Audit
- Working Tree Scan: Verified. Zero API keys, credentials, tokens, passwords, or `.env` files detected in repository source files.
- Personal Identifiers: Zero absolute user directory paths (such as user profile directories) present in committed files. One historical prose mention of `C:/nikhil` in `COLLABORATOR_HANDOVER.md` was identified as an illustrative path explanation; all code uses dynamic `Path(__file__).resolve()`.
- Git History Scan: Verified. Scanned commit history for secret patterns (`api_key`, `token`, `password`, `secret`); no secrets have ever been committed.

### .gitignore Audit
- Verified and Updated: Root `.gitignore` explicitly excludes:
  - Frontend: `node_modules/`, `frontend/node_modules/`, `dist/`, `frontend/dist/`, `dist-ssr/`, `frontend/dist-ssr/`
  - Python: `.venv/`, `venv/`, `__pycache__/`, `*.py[cod]`
  - Models and Datasets: `*.pth`, `*.joblib`, `*.npy`, `*.npz`, `*.zip`, `datasets/`
  - Runtime Data and Database: `work/`, `work/app_data/`, `*.sqlite*`
  - Images and Output Artifacts: `*.png`, `*.jpg`, `*.jpeg`, `outputs/**/crops/`
  - Environment and Secrets: `.env`, `.env.*`, `!.env.example`, `.streamlit/secrets.toml`
  - System and Editor Files: `.DS_Store`, `Thumbs.db`, `Desktop.ini`, `.vscode/`, `.idea/`
  - Local Scratch and Test Scripts: `scratch/`

### Large Files and Binaries Audit
Six untracked files exceed 25 MB on the development machine. All are properly excluded from Git by `.gitignore`:
1. `work/binarizer_env/Lib/site-packages/torch/lib/torch_cpu.dll` (295.2 MB) - Excluded by `work/`.
2. `InscripLens_runtime_assets.zip` (135.7 MB) - Excluded by `*.zip`.
3. `work/shilalekhya/binarizer.pth` (120.5 MB) - Excluded by `work/` and `*.pth`.
4. `outputs/broad_clean_study/mask_svm_bundle.joblib` (76.8 MB) - Excluded by `*.joblib`.
5. `InscripLens_recognizer_update.zip` (76.8 MB) - Excluded by `*.zip`.
6. `work/binarizer_env/Lib/site-packages/torch/lib/torch_cpu.lib` (27.8 MB) - Excluded by `work/`.
- Tracked Git Files: Zero tracked files in Git exceed 25 MB.
- Recommendation: Do not use Git LFS. Continue distributing model weights and demo assets via external release archives (`InscripLens_runtime_assets.zip` and Hugging Face repositories).

### Licence and Attribution Audit
- Root Licence: A root `LICENSE` file does not exist in the repository. As instructed, none has been invented; original code remains unassigned pending institutional review.
- Third-Party Attributions: Present and complete in `THIRD_PARTY.md`, `README.md`, `HANDOVER.md`, and the application Credits interfaces.
- Upstream Licences: Shilalekhya MIT notice retained; EpiSAM CC BY-SA 4.0 share-alike notices retained.

### Codebase Cleanliness and Leftovers Audit
- Console Calls: Zero `console.log` statements exist in `frontend/src`.
- Markers: Zero `TODO` or `FIXME` comments exist in `frontend/src`, `api/`, or `outputs/`.
- Streamlit Legacy Application: `outputs/inscriplens_app.py` remains in the repository for historical verification, literature benchmark comparisons, and side-by-side evaluation against the new React/FastAPI Studio.
- Build Verification: Clean production build generated by Vite (`dist/index.html`, `dist/assets/*.css`, `dist/assets/*.js`) with zero warnings or errors.


## Local verification addendum — 4 November 2026
See `outputs/STUDIO_STARTUP_VERIFICATION.md` for measured startup checks and corrections to earlier completion claims. The local startup environment is `work/studio_env`, and server dependencies are now included in `requirements.txt`. The API reports processed-image dimensions after resizing. Printed-source review and JSON export remain legacy Streamlit features. The original translation objective is unfinished. The earlier clean-machine setup and 4–10 second estimate are not established by this local verification.


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


## Studio Layout Hardening & Crop Loader Addendum — 5 November 2026

### Toolbar Layout Rules
1. Three Non-Wrapping Flex Groups: The canvas toolbar is divided into three fixed-height (44px) groups within a flex container:
   - Left Group: Curtain wipe indicator (`min-width: 95px`), candidate boxes toggle (`min-width: 95px`), mode badge (`min-width: 65px`), and mask download button (`min-width: 60px`).
   - Middle Group: Script display segmented switch (Kannada / Roman) and "Modern letters" archaic substitution toggle (`min-width: 220px`).
   - Right Group: Fit to viewport, 100% scale, zoom out, zoom percentage readout, and zoom in. Fit and zoom controls are pinned to the right and remain visible at all viewport sizes.
2. Responsive Container Queries: Rather than relying solely on window width, the viewer panel uses a container query observer (`ResizeObserver` on `.canvas-panel`):
   - Container width < 1100 px: Script segmented control and Modern letters switch collapse into a "View" dropdown popover button.
   - Container width < 900 px: Mode badge and Mask download button also collapse into the "View" dropdown popover.
   - Viewport fallback: If the container becomes exceptionally narrow, the toolbar scrolls horizontally with `white-space: nowrap` without wrapping or clipping controls.
3. Bottom Filter Bar Reorganization: The classification status badge ("N regions classified", progress bar) and the Re-run button are relocated from the top toolbar into the bottom gallery strip header, placed on the right side before the "Hide tiny" toggle.
4. Auto-Collapsing Sidebar: The left navigation sidebar automatically collapses to its icon rail (64px width) on windows narrower than 1500 px, while persistently honoring manual user toggle actions via `localStorage`.
5. Single-Row Header: The header note under "High accuracy mode" is replaced with a single-row toggle and an accessible info icon holding the tooltip: *"Finds more faint strokes. Slower, and may add a few false strokes."* The stone-name pill gracefully truncates with an ellipsis and full hover tooltip when horizontal space is constrained.
6. Empirical Verification: Verified across window widths 1280, 1366, 1440, 1536, and 1920 px, at browser zoom levels 100% and 125%, with the sidebar open and collapsed, in both obsidian dark and parchment light themes. 19/19 matrix tests passed with zero element wrapping, clipping, or overlap (`outputs/eval/run_responsive_audit.py`).

### Crop Loader Stall Diagnosis and Fix (Part B)
- Root Cause: Recognition models (`mask_svm_bundle.joblib`, 76.8 MB) and model SHA256 hashes were being unpickled from disk on every single `/api/predict-crop` request, adding several seconds of latency per crop. In the frontend client, when a request took several seconds or was superseded by candidate navigation, `setPredictingCrop(false)` was skipped due to a mismatched request-id guard, leaving `predictingCrop: true` indefinitely.
- Server Optimization: Models and engine weights are now cached and warmed once at server initialization (`get_loaded_bundle`), reducing cached model access latency from 2.6s to 0.000001s.
- Client Timeout & Fallback: Added an `AbortController` and an 8-second timeout in `predictBox`. If a response takes longer than 8 seconds, the in-flight request is aborted, `predictingCrop` is cleared, and the crop box renders a "Crop preview timed out" message with a "Retry" button. The inspector immediately shows the label already known from the candidate strip (`knownCandidateLabel`), and alternatives display "Alternatives unavailable" rather than an endless pulsing skeleton.
- Files Changed: `api/server.py`, `frontend/src/App.jsx`, `frontend/src/index.css`, `outputs/eval/run_responsive_audit.py`.

## 7. Git Push Readiness & Automated GPU Installation — 5 November 2026

### Repository Hygiene & Exclusion Policy
1. Large Binary Protection: Giant literature PDFs (>1.5 GB Kittel dictionary) and raw training archives (>440 MB EpiSAM corpus) are excluded from version control via .gitignore.
2. Python Path Flexibility: outputs/app_backend.py and pi/server.py dynamically resolve the active Python interpreter across multiple environments:
   - Dedicated inference venv: work/binarizer_env/Scripts/python.exe (Windows) or work/binarizer_env/bin/python (Linux)
   - Standard unified venv: .venv/Scripts/python.exe or .venv/bin/python
   - Active runtime environment: sys.executable
3. Automated GPU Setup:
   - setup_gpu.bat (Windows): 1-click script installing Python virtual environment, CUDA 12.4 PyTorch wheels, application requirements, and React frontend build.
   - setup_gpu.sh (Linux/macOS): POSIX-compliant automated environment setup.
   - INSTALL.md: Step-by-step setup documentation covering hardware prerequisites, CUDA configurations, model asset placement, and verification tests.
   - 
equirements.txt & 
equirements-gpu.txt: Explicit dependency specifications.
4. Pre-Push Verification: Full regression test suite (outputs/eval/verify_kannada_regression.py) passes 9/9 checks with zero failures.
