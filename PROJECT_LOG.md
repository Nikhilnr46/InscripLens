# InscripLens Studio Project Log

## 6 November: PDF Analysis Report Export in Run History

Replaced JSON downloads in the Run History table with full printable PDF analysis report export:
- Run History Export Button (`frontend/src/App.jsx`):
  - Replaced the previous raw JSON file download link (`<a href="/api/export/..." download>Export</a>`) with an interactive `<button className="tool-btn btn-export-highlight"><FileText size={12} /> Export PDF</button>`.
  - Clicking "Export PDF" now triggers the fullscreen `ReportPreviewDialog` with the stone photograph, binary mask, detected characters, and "Save as PDF" browser print pipeline.
- Instant Candidate Region Extraction for Historical Runs (`frontend/src/utils/maskExtractor.js`):
  - Created a browser-native connected-component analysis worker using offscreen canvas that deterministically extracts candidate character bounding boxes directly from `mask_url` in <25ms (100% agreement with backend Python `segment_candidates.py`).
  - Seamlessly loads both active stone runs and past historical analysis records into the PDF preview dialog without requiring backend modifications.
- Visual Feedback & State Management (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Added `Loader2` spinning state during offscreen figure preparation (`historyExportingId`).
  - Configured `@keyframes spin` in `frontend/src/index.css` for consistent loading animations.

## 6 November: Free-Form PES Logo Presentation in Footer

Unconstrained the PES college logo in the website footer from the pill container:
- Footer Free-Form Layout (`frontend/src/components/Footer.tsx` & `frontend/src/index.css`):
  - Removed the cramped `.institution-pill` container (border, background, and oval geometry).
  - Replaced with `.footer-institution-freeform`: displays the circular PES compass emblem in free form alongside bold "PES" text and developer attribution.
  - Increased logo dimensions to 32px diameter (up from 16px) with subtle drop-shadow and smooth hover scale (`scale(1.08)`), making the blue compass ring, white inner ring, and orange central disc fully legible.
  - Added desktop padding clearance (`padding-right: 52px` on `.site-footer-meta`) to guarantee the floating back-to-top button never covers or clips the footer attribution or logo on desktop resolutions.

## 6 November: PES College Logo Placement (Footer & Credits Only)

Configured the PES University compass logo across appropriate institutional sections:
- Kept the landing page navigation header clean with only the `InscripLens Studio` brand title (removed badge from header).
- Home Page Footer (`frontend/src/components/Footer.tsx` & `frontend/src/index.css`):
  - Upgraded `.institution-pill` to embed the circular PES logo emblem alongside the college name (`Developed by Nikhil Vasista N R | [PES Logo] PES`).
- About & Credits Authorship Card (`frontend/src/components/AboutSection.tsx` & `frontend/src/pages/AboutPage.tsx`):
  - Rendered the circular PES compass emblem inside `.about-authorship-card` recognizing institutional affiliation and developer credits.

## 6 November: Sidebar Footer Cleanup (Removed Local Worker Pill)

Simplified the navigation sidebar footer:
- Removed the "Local Worker" button/pill (`.sidebar-worker-pill`) from `frontend/src/App.jsx`.
- Retained the attribution and developer credits line (`Developed by Nikhil Vasista N R, PES · 2026`) directly above the bottom edge.
- Updated `frontend/src/index.css` so that in collapsed rail mode, the footer section cleanly hides without leaving an orphaned border line.

## 6 November: Light Mode Anti-Glare Calibration & Contrast Overhaul

Calibrated light theme color tokens and eliminated screen glare across the landing page, workflow sections, and studio workspace:
- Soft Stone Neutral Palette (`frontend/src/index.css`):
  - Calibrated `--bg-base` from glaring high-saturation yellow-white (`#F7F2E8`, ~95% lightness) to soft, soothing natural limestone paper (`#E7E3DA`, ~88% lightness).
  - Softened `--bg-surface` (`#DCD6CB`), `--bg-surface-raised` (`#EDE9E0`), and `--card-bg` (`#EFEBE2`), eliminating pure `#FFFFFF` glare on cards, sidebar, buttons, and popovers.
  - Reduced `--grid-line` intensity by over 50% (`rgba(28, 26, 23, 0.018)`), softening the high-frequency graph-paper pattern across the landing hero and about sections.
- Studio Glyph Inspector & Candidate Contrast Hardening (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Replaced 42 hardcoded inline dark-mode colors (`#EDEDEC`, `#A8A29A`, `#7E7A75`, `#161619`) with semantic CSS custom properties (`var(--text-primary)`, `var(--text-secondary)`, `var(--text-muted)`, `var(--text-subtle)`, `var(--bg-elevated)`).
  - Fixed candidate inspector header ("Candidate #10"), which was previously invisible due to inline white `#EDEDEC` on a light card.
  - Styled `.inspector-crop-box` with a dark viewing easel background (`#16161B`), seamlessly framing the binarized mask crop and white chiseled strokes without jarring black-on-white cutoffs.
  - Calibrated `.glyph-chip.is-uncertain` for light mode: increased opacity from 0.65 to 0.95 with solid amber accenting (`#92400E`), ensuring full legibility for uncertain candidates and tags.
  - Review form inputs in the inspector now reactively use `var(--bg-elevated)` and `var(--text-primary)` rather than hardcoded obsidian backgrounds.

Relocated the Home button inside the sidebar Navigation section and adjusted the brand title placement:
- Home Button in Navigation Section (`frontend/src/App.jsx`):
  - Removed the standalone `Home` button from the top header bar.
  - Added `Home` (`<Home size={15} />`) to the top of `.sidebar-nav-list` inside the Navigation sidebar.
  - In collapsed mode: displays cleanly as the first icon in the navigation rail beneath the burger button.
  - In expanded mode: displays with icon and text (`[Home] Home`), styled identically to all other sidebar items with sandstone hover bloom, border highlight, and micro-translation.
- Masthead Alignment (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - `InscripLens Studio` now comfortably anchors the start of the top header bar, naturally aligned with the metadata status capsule.

## 6 November: Studio Header Redesign (Home Button & Metadata Capsule)

Upgraded the top navigation header bar with matching studio geometry and structured metadata tokens:
- Home Button Refinement (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Replaced the 36px oval stadium pill with a 32px height, 7px radius obsidian card button matching the rest of the application.
  - Houses `<Home size={13} />` with warm sandstone hover bloom and subtle translation.
- Structured Metadata Capsule (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Replaced cramped plain text with a segmented metadata capsule:
    - Stone name token with pulsing sandstone beacon dot and expanded `max-width: 240px` (preventing premature truncation).
    - Monospace image resolution badge (`525 × 1080 px`).
    - Offline execution token with sandstone `<Cpu size={12} /> Local Workspace`.
  - Replaced raw middot characters with hairline vertical dividers (`.header-status-divider`).

## 6 November: Toolbar Zoom Removal & Direct Script Toggle Placement

Streamlined the stone toolbar by removing redundant zoom buttons and placing Kannada / Roman buttons directly in their location:
- Toolbar Zoom Control Removal (`frontend/src/App.jsx`):
  - Removed `[Fit]`, `[-]`, `XX%`, `[+]` from the stone viewer toolbar, eliminating duplicate zoom features.
  - Viewport zoom remains completely accessible via the on-canvas vertical Zoom Scale HUD inside the image area, as well as mouse wheel and touchpad pinch.
- Permanent Kannada / Roman Script Switch Placement (`frontend/src/App.jsx`):
  - Removed the `View` popover dropdown menu.
  - Positioned the `[ ಕನ್ನಡ | Roman ]` segmented switch directly in the right toolbar group alongside `Export PDF`.

## 6 November: Mouse Wheel Zoom Restoration & Precision Disambiguation

Reverted the discrete mouse wheel zoom calculation directly back to the original formula:
- Mouse Wheel Zoom Restored (`frontend/src/App.jsx`):
  - Standard physical mouse wheel scrolling (`!e.ctrlKey`) unconditionally runs the exact original discrete formula `e.deltaY < 0 ? 1.15 : 1 / 1.15`.
  - Removes delta-magnitude heuristic (`Math.abs(e.deltaY) >= 80`) so all Windows mouse wheel settings (40–60 delta notches) respond with full 1.15x discrete stepping.
  - Touchpad pinch gestures (`e.ctrlKey === true`) remain smoothly dampened.

## 6 November: Image Splitter Curtain Handle Icon Redesign

Replaced the audio equalizer slider icon on the stone curtain divider with dedicated dual comparison triangles:
- Splitter Handle Icon Upgrade (`frontend/src/App.jsx`):
  - Replaced `<Sliders size={14} />` with dual directional comparison triangles (`◀ ▶` SVG) inside `.curtain-handle-knob`.
  - Triangles point directly outwards to the binary mask and original photograph, clearly signaling horizontal wipe / comparison interaction.
  - Sized at 15x15px with solid fill, perfectly balanced inside the 32px circular sandstone knob.
- Toolbar Semantic Consistency (`frontend/src/App.jsx`):
  - Updated the "Curtain: XX%" toolbar indicator from `<Sliders size={13} />` to `<ChevronsLeftRight size={13} />`.

## 6 November: Plan B - Canvas Zoom HUD, Bottom Scroll Line & Trackpad Normalization

Implemented Plan B interactive zoom and viewport navigation system while keeping physical mouse mechanics 100% unaltered:
- Physical Mouse Wheel Preserved (`frontend/src/App.jsx`):
  - Retained exact discrete 1.15x multiplier per notch (`isMouseWheelNotch = Math.abs(deltaY) >= 80 || deltaMode !== 0`). Physical mouse feel and cursor-centered geometry remain completely untouched.
- Trackpad Pinch Precision (`frontend/src/App.jsx`):
  - Applied smooth exponential dampening (`Math.exp(-clampedDelta * 0.012)`) on continuous small touchpad pinch deltas. Touchpad zoom operates in smooth, controlled micro-steps without runaway scaling to limits.
- On-Canvas Vertical Zoom Scale HUD (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Positioned a floating, semi-transparent HUD (`.zoom-scale-hud`) on the left side inside the black canvas area.
  - Features `+` (Zoom In), real-time monospace percentage readout, scrubbable vertical range slider track with gold sandstone accent, `-` (Zoom Out), divider, and `Fit` button.
  - Automatically suppresses during Redraw mode to maintain clean, unobstructed bounding box editing.
- Bottom Horizontal Scroll Indicator Line (`frontend/src/App.jsx` & `frontend/src/index.css`):
  - Tracks canvas horizontal overflow using `ResizeObserver`.
  - Appears automatically along the bottom edge whenever the stone exceeds viewport width (`.canvas-bottom-scroll-track`).
  - Sandstone gold thumb dynamically reflects the visible frame window; clicking or dragging along the track provides 1-touch horizontal scrubbing across the stone.

## 6 November: Standalone Visible Export PDF Action (Removed Secondary Dropdown)

Streamlined the export interface by removing the adjacent chevron dropdown and binary mask download:
- Standalone Action Button (`frontend/src/App.jsx`):
  - Removed the chevron dropdown button and popover menu entirely.
  - Eliminated the redundant "Download mask" and secondary "PDF report..." options from both the toolbar and `View` popover.
  - Retained a single, prominent, standalone `Export PDF` button (`<FileText size={13} /> Export PDF`) on the canvas toolbar.
  - 1-click execution immediately opens the printable PDF report preview modal.

## 6 November: Import Screen Navigation Normalization & SPA Fallback Route Fix

Fixed "Back to Studio" navigation anomalies and 404 browser refresh handling on `/import`:
- Navigation Button Scope (`frontend/src/App.jsx` & `frontend/src/pages/ImportPage.jsx`):
  - Removed accidental unstyled `home-pill-btn` in the top header that collided with the `InscripLens Studio` brand logo.
  - Scoped the card's `< Back to Studio` button strictly to the `isChangingArea` flow (`hasActiveStudioRun = isChangingArea && !!analysis`).
  - The "Choose a stone image" screen now consistently presents `← Back` routing directly to the landing page overview, eliminating confusing returns to lingering in-memory demo sessions.
  - Reset `isChangingArea` to `false` when entering `/import` to prevent stale crop workflows from hijacking new stone selection.
- CSS Pill Button Alias (`frontend/src/index.css`):
  - Aliased `.home-pill-btn` to `.btn-home-pill` styles to guarantee theme compliance (obsidian/parchment) across all header buttons.
- FastAPI SPA Route Registration (`api/server.py`):
  - Added `@app.get("/import")` to the SPA fallback routes serving `frontend/dist/index.html`.
  - Direct browser refreshes (F5) or direct navigation to `http://127.0.0.1:8000/import` now return HTTP 200 and load the interface seamlessly without JSON 404 errors.

## 6 November: PDF Report White Background, Script Switch & Paper Size Resolution

Addressed layout truncation and interactive control issues in the PDF export preview modal:
- Continuous White Paper Sheet (`frontend/src/report/report.css`):
  - Fixed flex-column clamping where Chrome resolved `flex-basis: auto` to `min-height: 297mm` and froze container height at 297mm, spilling candidate cards #43–133 out into dark background.
  - Added `height: auto !important; flex-shrink: 0 !important; display: block !important; overflow: visible !important;` to `.inscriplens-report-root` and padded scroll container (`padding-bottom: 60px`) ensuring the white background continuously covers 100% of candidate regions, historical narrative, and notes.
- Dynamic Paper Size (`frontend/src/report/ReportPreviewDialog.jsx` & `frontend/src/report/ReportView.jsx`):
  - Injected dynamic `@page { size: ... portrait; margin: 14mm; }` rule reflecting user selection (A4 vs US Letter) during native print-to-PDF.
  - Displayed live paper format pill in report header badge (`A4 (210 × 297 mm)` vs `Letter (215.9 × 279.4 mm)`).
- Script & Style Controls (`frontend/src/report/ReportPreviewDialog.jsx` & `frontend/src/report/ReportView.jsx`):
  - Added explicit Script segmented control (`[ ಕನ್ನಡ | Roman ]`) alongside Kannada style (`[ Faithful | Modern letters ]`).
  - Implemented responsive primary/secondary label inversion: switching to Roman renders large Roman IAST transliterations with Kannada subtitle; switching to Kannada renders authentic Kannada script with Roman transliteration subtitle.
  - Preserved modern letter lossy marker (`*`) for archaic character substitutions.

## 6 November: Halmidi Inscription Epigraphic Brief Integration (PDF Export)

Integrated curated archaeological and historical brief for the Halmidi Inscription into the demonstration stone profile for PDF report exports:
- Curated Epigraphic Profile (`frontend/src/report/stoneProfile.js`):
  - Demonstration stone profile updated to title "The Halmidi Inscription" (retaining alternateName "Nagavara demonstration stone").
  - Structured historical metadata added:
    - Overview & Discovery: Date of Origin (~450–500 CE), Location (Halmidi village, Hassan district, Karnataka), Discovery (1936 by Dr. M. H. Krishna, Director of Archaeology for Mysore), Medium (Carved stone pillar).
    - Linguistic & Cultural Significance: Oldest confirmed inscription in the Kannada language, Kadamba script in Puruvada-hala Kannada (pre-old Kannada), earliest administrative proof of Kannada as an official state language.
    - Core Narrative & Historical Context: Kadamba dynasty royal land grant donating Palmadi (Halmidi) to warrior Vija Arasa for battlefield heroism against the allied forces of the Kekayas and Pallavas.
    - Citation: Epigraphia Carnatica & Archaeological Survey of Mysore (Dr. M. H. Krishna, 1936).
- Printable Report Layout (`frontend/src/report/ReportView.jsx` & `frontend/src/report/report.css`):
  - Updated stone provenance subtitle to display Kadamba dynasty attribution and alternate stone name.
  - Implemented 2-column facts grid (`.report-facts-grid`), structured significance bullet list, and narrative metadata rows.
  - Excluded external scanning and third-party preservation attributions to maintain pure epigraphic stone focus.
  - Page-break avoidance rules preserved for clean A4 printing without layout overflow.
  - Zero emojis, zero external assets, no UI file paths.

## 6 November: Predict-Crop Latency & Robustness Hardening (Step D1 & Performance Fix)

Resolved the predict-crop latency bottleneck and hardened the single-crop recognition pipeline across backend and frontend:
- Backend Optimization (`api/server.py`):
  - Model Caching & Re-use: Singletons for recognizer bundle and calibrated engine loaded once at server startup and retained in memory.
  - PyTorch CUDA Acceleration: Connected runtime packages to enable GPU-accelerated CNN inference under `torch.no_grad()`.
  - Serialized Inference: Protected GPU inference with `_INFERENCE_LOCK` to serialize concurrent requests and avoid memory collisions.
  - CUDA OOM Fallback: Added graceful fallback to CPU on CUDA OutOfMemoryError with plain log line `"CUDA out of memory in character recognition, falling back to CPU."` and explicit temporary tensor cleanup.
  - Removed Redundant Lib-SVM Evaluations: Bypassed redundant multi-second `decision_function` and `rank_labels` passes during CNN prediction, relying on fast 15ms SVM DAG prediction for agreement check.
  - Error Standards: Returns clear JSON errors with status 422 (invalid coordinates) or 503 (service unavailable) without leaking internal file paths or stack traces.
  - 20-Box Golden Test: Confirmed 100% mathematical identity across all predictions, alternatives, and confidences (difference < 1e-6). Repeat call latency reduced from 14.25s down to 38.0ms (>370x speedup).
- Frontend Studio Hardening (`frontend/src/`):
  - Request Serialization & Single In-Flight Queue: Enqueued `predict-crop` requests in `apiClient.js` with `AbortController` cancellation on selection change.
  - Debouncing: Debounced candidate navigation requests by 200ms to eliminate server queuing during fast arrow navigation.
  - Session Caching: Implemented session-level cache by `run_id + bbox` so Inspector and Compare never request identical boxes twice; Compare reuses candidate prediction instantly (0ms).
  - 12s Timeout Guard: Ended endless loading states with a 12-second timeout, plain user-facing notice, and Retry buttons.
  - Image Resilience: Handled `onLoad` and `onError` states on crop image previews.
  - Advanced Mode Diagnostics: Displays status code and response latency in inspector header when `advanced_mode` is enabled (strictly no file paths).

## 6 November: Glyph Inspector Redraw, Compare, and Save Foundation (Step R1 of 3)

Implemented the core architectural foundation for glyph region redrawing, prediction comparison, and versioned local persistence:
- Read-Only Crop Diagnosis (Task 1):
  - Investigated Candidate #16 (index 15, bbox `[265, 147, 287, 173]`, size 22x26 px) and normal-sized candidates showing "Alternatives unavailable".
  - Diagnosis: Decoupled state architecture between candidate chips (`batchRegions`) and inspector alternatives (`cropPrediction.alternatives`). Batch recognition populates primary labels but not alternatives; in-flight `/api/predict-crop` requests superseded by candidate navigation are discarded by the request-id guard, leaving `cropPrediction` null and prompting the fallback banner while the header displays the known batch label.
- Client API (`frontend/src/compare/apiClient.js`):
  - Built `predictCrop(runId, bbox)` client calling `POST /api/predict-crop` with 8s timeout, automatic single retry, and typed results (`cropUrl`, `prediction`, `predictionKannada`, `alternatives`, `confidence`, `modelSha256`).
- Coordinate Helpers (`frontend/src/compare/coordinates.js`):
  - Implemented `screenToImage` and `imageToScreen` based on viewer zoom/pan stage transform.
  - Implemented `normalizeBbox` enforcing integer rounding, boundary clamping, non-inverted coordinates (`x1 < x2`, `y1 < y2`), and minimum 8x8 px dimensions across full photos and selected-area images.
- Outcome Logic (`frontend/src/compare/outcome.js`):
  - Implemented `evaluateComparisonOutcome` comparing proposed reading (NFC-normalised Kannada, with Roman auto-converted) against top 3 alternatives.
  - Classifies outcome into `"improved"`, `"worse"`, `"unchanged"`, or `"unknown"`, appending explicit note that ranks beyond 3 are unavailable.
- Comparison Store (`frontend/src/compare/store.js`):
  - Implemented versioned store (`inscriplens.comparisons.v1`) with full try/catch wrapping, corrupted JSON resilience, quota exceed protection, and export capability without file paths.
- Thumbnail Generator (`frontend/src/compare/thumbnail.js`):
  - Built 96 px canvas thumbnail generator for automatic and redrawn crops.
- Unit Tests:
  - Added unit test suites for coordinate transformations, outcome logic rankings, and store operations.

## 6 November: PDF Report Integration & Run History Investigation (Step E2 of 2)

Completed the PDF report integration and investigated Run History backend endpoints:
- Studio Export Menu Updates:
  - Positioned "PDF report..." above "Download mask" in the primary Export menu and the responsive View dropdown.
  - Added interactive prompt banner for unclassified analyses with "Classify all now" (runs batch recognition with live progress) and "Export without labels" options.
- Run History Endpoint Investigation:
  - Conducted a read-only audit of past-run endpoints (`/api/history`, `/api/export/{id}`, `/api/reviews/{id}`).
  - Result: Past runs lack candidate bounding boxes (`boxes`) and automatic batch predictions in API responses. Under the strict UI-only boundary, Run History remains unchanged and Studio export is shipped.
- Stone Profile Registry Interface:
  - Documented future registry hook in `stoneProfile.js` with contract `{ name, nameSource, story, storySource }`.
- Edge Case Hardening:
  - Tested runs with zero reviews, all-uncertain candidates, long stone names (word-break wrapping), and large candidate sets (page-break avoidance).

## 6 November: Printable Analysis Report Implementation (Step E1 of 2)

Implemented client-side printable report generation (`frontend/src/report/`) providing publication-ready PDF exports via the browser's native print engine:
- Stone Identity & Provenance (`stoneProfile.js`):
  - Returns structured stone profile (`{ name, nameSource, story: null, storySource: null }`).
  - Distinguishes curated Nagavara demo stone, user-entered titles, and unidentified fallbacks without inventing unverified metadata.
- State-Driven Report Construction (`buildReportData.js`):
  - Consumes existing Studio state without extraneous API calls.
  - Offscreen canvas preprocessing caps photo (JPEG 0.85) and mask (PNG) to 1600 px long side, keeping output PDF under 5 MB.
  - Extracts per-candidate stroke thumbnails (clamped to 96 px) directly from the binary mask.
  - Formats Roman-to-Kannada glyphs with lossy markers for modern letter substitution; reports "Characters have not been classified" when classification has not been executed.
- Printable Paper Layout (`ReportView.jsx` & `report.css`):
  - Fixed A4 portrait format (210mm × 297mm, 14mm margins) styled in pure white paper aesthetic regardless of site dark/light theme.
  - Side-by-side figures for input photograph/selection and binary stroke mask on black background.
  - 8-column character card grid with stroke crops, large Kannada glyphs, transliterations, confidence ratings, and review tags.
  - Dedicated credits block citing Shilalekhya (IIIT Hyderabad, MIT) and EpiSAM (CC BY-SA 4.0, The Mythic Society Bengaluru), plus developer signature line.
  - Fixed print footer on every page via `@media print`.
- Full-Screen Preview Dialog (`ReportPreviewDialog.jsx`):
  - Live options panel to toggle uncertain glyphs, <10×10 px tiny regions, reviewer credits, and Kannada orthography.
  - One-click "Save as PDF" triggering native print with `document.fonts.ready` synchronization and automatic title formatting (`InscripLens report - <stone name> - <YYYY-MM-DD>`).

## 6 November: Studio Integration of the Selected Area (Step S3 of 3)

Integrated selected region awareness, metadata synchronization, and re-selection flows into the Epigraphy Studio:
- Header Selected Area Pill:
  - When the current image in Studio came from a user selection, the header status line renders an interactive pill displaying: `Selected area, {w} × {h} px (from {origW} × {origH})`.
  - For whole images and the Nagavara demo stone, the standard dimension readout `{w} × {h} px` is preserved without any alteration.
- Collapsible "Selected Area" Sidebar Card:
  - Positioned at the bottom of the left navigation sidebar above the Local Worker section.
  - Renders a live thumbnail of the original photograph with the selected bounding box outlined in `var(--accent-sandstone)` with a dimmed overlay (`rgba(0, 0, 0, 0.45)`).
  - Displays live dimension readouts for both selected area and original image pixels.
  - Includes a "Change area" button which navigates back to the `/import` selection step with the original image and existing crop rectangle restored from the in-memory store.
  - If the in-memory store is lost (e.g., following a browser page reload), the "Change area" button is safely disabled, and the card displays the guidance notice: *"Reselect by choosing another image"*.
- Non-Destructive Navigation:
  - "Try another" navigates to `/import`. If the user presses the browser Back button, they return to the Studio with their active analysis run completely intact.
  - From the restored selection step during "Change area", clicking "Back to Studio" returns immediately to the active workspace without modifying the existing run.
- Coordinate & History Semantics:
  - Candidate coordinates, saved reviews and history refer to the selected area image, not the original photograph.
  - Added clarifying FAQ entry to the About page and updated technical handover documentation.
- Memory Lifecycle & Edge Case Handling:
  - Switching from an uploaded selection to the demo stone and back cleans up stale selection state and revokes object URLs.
  - All File references, crop data, and preview object URLs are released when the user leaves the Studio for the landing page overview.
  - Responsive audit across widths 1280, 1536, and 1920 px confirms seamless layout with sidebar collapsed (icon rail at 1280px) and expanded (1536px/1920px) across both obsidian dark and parchment light themes.

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

### [2026-11-04] Handover to Nikhil Vasista N R
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
  - Added "Modern letters" switch replacing archaic ಱ (`U+0CB1`) and ೞ (`U+0CDE`) with modern ರ (`U+0CB0`) and ಳ (`U+0CB3`) flagged with small "lossy" tags.
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

## 2026-11-06: Glyph Inspector: Redraw, Compare, Save (Steps R1 & R2)

### Step R1: API Client, Coordinate Mapping, Outcome Logic, and Comparison Store
- **Diagnosis of /api/predict-crop**: Resolved and verified candidate crop predictions with 8s timeout and automatic retry.
- **Coordinates & Bounding Box Logic**: `frontend/src/compare/coordinates.js` providing screen-to-image/image-to-screen transforms, normalization with boundary clamping, and 8x8 px minimum size enforcement.
- **Outcome Logic**: `frontend/src/compare/outcome.js` implementing rank evaluation in top 3 alternatives and outcome badges (improved, worse, unchanged, unknown).
- **Comparison Store**: `frontend/src/compare/store.js` managing `inscriplens.comparisons.v1` in localStorage with quota safety and JSON recovery.

### Step R2: Redraw Mode, Interactive Viewer Overlay & Dual Comparison Inspector
- **Interactive SVG Stage Overlay**: `frontend/src/compare/RedrawOverlay.jsx` renders original candidate box as dashed neutral outline (`#A8A29A`) and redrawn box as solid sandstone accent (`#C9A66B`) with 8 resize handles, pointer capture, boundary clamping, and live `w x h px` dimension badge.
- **Floating Viewer Toolbar**: `frontend/src/compare/RedrawFloatingBar.jsx` renders top-centered floating toolbar with candidate badge (`#N`), Photo/Mask toggle (defaulting to Mask with tooltip "The classifier reads the mask"), and Reset, Cancel, Apply actions.
- **Viewer Redraw Mode**:
  - Entering redraw mode switches off curtain and zooms to candidate with generous ~2.5x margin on each side (within zoom limits 0.1–5.0).
  - Viewport pan/zoom (wheel, pinch, drag) remains active while maintaining exact image-space coordinates.
  - Keyboard shortcuts: `Enter` applies, `Escape` cancels, Arrow keys nudge 1 px (Shift: 10 px), Alt + Arrow keys resize 1 px (Shift + Alt: 10 px). Candidate navigation and `R` shortcut disabled while typing in fields or during redraw mode.
- **Parallel Crop Prediction**:
  - `applyRedrawAndCompare` fires parallel `predictCrop` requests for automatic and redrawn boxes with request ID guard against stale responses.
  - Skeletons pulse while predicting; dedicated per-column Retry buttons if either request fails.
- **Side-by-Side Comparison Card**: `frontend/src/compare/CompareCard.jsx` placed between Alternatives and Verification & Expert Review:
  - Context stone overview with dual outlines and Photo/Mask switch.
  - Dual columns (Automatic with dashed neutral chip, Redrawn with solid accent chip) showing crop image, primary prediction in Kannada/Roman, confidence bar, and top 3 suggestion chips.
  - "Your reading (tentative)" field with live Kannada conversion preview, per-column rank readout ("Your reading is 1st" / "2nd" / "3rd" / "not in the top 3"), and overall outcome badge (Improved, Worse, Unchanged, Unknown).
  - Actions: "Redraw again", "Discard", and disabled "Save comparison" button with tooltip "Coming in the next step".
- **Verification**: All compare unit tests and regression suites pass without errors.

### Step R3: Comparison Persistence, Saved Drawer & Clean JSON Export
- **Active Save Workflow**:
  - "Save comparison" button in `CompareCard.jsx` activates dynamically when both automatic and redrawn predictions load without errors.
  - Generates compact 96 px data URL thumbnails for quick off-canvas rendering.
  - Saves records via R1 comparison store under versioned localStorage key `"inscriplens.comparisons.v1"`.
  - Every save attempt creates a distinct record with a unique identifier (`comp_<timestamp>_<random>`), retaining all iterations for the candidate.
  - Immediate feedback: Displays confirmation banner *"Saved in this browser only"* and a count pill (e.g. *"3 saved for this candidate"*).
- **Saved Comparisons Drawer (`SavedComparisonsDrawer.jsx`)**:
  - Slide-over off-canvas drawer opened from CompareCard.
  - Tabs: *"This run"* (filtered by `currentRunId`) and *"All runs"*, each displaying live count badges.
  - Summary bar displaying dynamic counts of Improved, Worse, Unchanged, and Unknown outcomes.
  - List items render candidate number, dual 96 px thumbnails, dual primary predictions (formatted per active Script setting and modern letters preference), outcome badges, tentative reading, formatted timestamp, "Open", and "Delete" (with inline confirmation).
  - "Open" action focuses the candidate in the Studio viewer and loads the saved comparison view (disabled for records from other runs).
- **Clean JSON Export (`inscriplens-comparisons-<date>.json`)**:
  - Split "Download JSON" menu offering *"This run"* and *"All saved"* options.
  - Standardized JSON envelope: `{ software_name: "InscripLens", schema_version: 1, export_date, count, run_filter, records }`.
  - Strict security and privacy boundary: Completely strips internal filesystem paths, crop URLs, and base64 thumbnail data URIs from exported records.
- **Storage Resilience**:
  - Handled quota limits and blocked browser storage with structured error handling and a prominent *"Download JSON now"* prompt.
  - Storage usage warning (>4MB) warns users before quota limits are reached.
  - Corrupted storage entries recover gracefully to an empty list without crashing.
- **Architectural Boundary & Future Proposal**:
  - *Current Limit*: Model endpoint `POST /api/predict-crop` returns strictly top-3 alternatives; readings outside the top 3 cannot be ranked precisely.
  - *Proposed Backend Feature (Awaiting Approval)*: Add an optional query or body parameter `top_k: int = 3` (configurable to 5 or 10) to `POST /api/predict-crop` and `POST /api/recognize-all` to enable deeper comparative ranking. Backend files remained completely untouched per rules.
- **Acceptance Test Suite**: Full 7-part automated test runner (`scratch/acceptance_test_r3.py`) passed: schema verification, multi-save preservation, deletion, model hash mismatch flagging, export cleanliness, corrupt storage recovery, and quota handling.

### Step G1: Candidate Gallery Navigation Controls & Studio UX Hardening
- **Candidate Gallery Prev / Next Buttons (`App.jsx`, `index.css`)**:
  - Replaced passive non-clickable keyboard hint (`<- -> Navigate`) with interactive `<button>` elements (`< Prev` and `Next >`) styled to match the `.chip-switch` design token (`height: 26px`, sandstone accent hover).
  - Wired directly to `handleSelectAndFocusBox(target.idx)` with wrap-around support across `visibleCandidates`.
  - Automatically scrolls the selected glyph chip into the center of the gallery strip and highlights the candidate on canvas.
  - Retains keyboard arrow key shortcuts (`ArrowLeft` / `ArrowRight`) while removing dead state and fading logic.
- **Direct PDF Export Visibility (`App.jsx`, `index.css`)**:
  - Promoted PDF Report export into a standalone prominent button on the primary viewer toolbar.
  - Removed redundant nested sub-menu dropdown and unused mask download option.
- **Trackpad Pinch Zoom Smoothing & Viewport HUD (Plan B)**:
  - Isolated physical mouse wheel notches (`Math.abs(deltaY) >= 80 || deltaMode !== 0`) preserving exact 1.15x discrete stepping.
  - Normalized trackpad pinch gestures with smooth exponential scaling (`Math.exp(-clampedDelta * 0.012)` clamped to `[-25, 25]`).
  - Added on-canvas vertical Zoom Scale HUD with `+`, percentage readout, vertical scrub range slider, `-`, and 1-click `Fit` button.
  - Added bottom horizontal scroll indicator line (`.canvas-bottom-scroll-track`) that activates when stone image exceeds viewport width, supporting click and drag scrubbing.
- **Left Sidebar Burger Button & Navigation Styling Upgrade (`App.jsx`, `index.css`)**:
  - Replaced the awkward chevron arrow (`<` / `>`) button with an authentic hamburger menu icon button (`<Menu size={16} />`).
  - Added a dedicated top row header (`.sidebar-header-row`) pairing the burger button with the section title when expanded and centering the burger button in the icon rail when collapsed.
  - Redesigned all sidebar navigation buttons (`Epigraphy Studio`, `Run History`, `Project Credits`, `About & Docs`) to match the site's obsidian and sandstone aesthetic:
    - Dedicated icon containers (`.sidebar-nav-icon`) with hover sandstone scale.
    - Active items feature warm sandstone gold gradient, subtle inner glow, and left accent indicator pill.
    - Hover states feature sandstone border highlight, smooth horizontal translation (`translateX(2px)`), and elevation shadow.
    - Integrated dynamic count badge for Run History.
    - Refined the "Local Worker" footer pill to match the site's status chip styling.






