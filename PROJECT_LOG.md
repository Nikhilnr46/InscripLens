# InscripLens Studio Project Log

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
