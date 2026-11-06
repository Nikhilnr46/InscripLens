# InscripLens Assistant Guidelines (GEMINI.md)

This document guides the AI assistant on how the user works, how they communicate, and the strict rules governing this repository.

---

## 1. User Communication & Prompting Style

- **Direct, Concise User Prompts**: The user frequently gives succinct, high-context prompts (e.g., *"check last push"*, *"get me time and date of last push"*, *"fix this"*, *"the redraw box glitches out"*, *"about to push now"*, *"is my work ruined, yes or no"*).
  - Do not ask unnecessary clarifying questions if the intent is clear from context or recent commits.
  - Diagnose, fix, build, and verify immediately.
- **Direct Answers First**:
  - When the user asks a safety, git, or status question (*"will this ruin my work?"*, *"did the push go through?"*), **always start with a clear, direct "YES" or "NO"** before providing technical details.
  - Reassure the user with exact commit hashes, timestamps, and `git status` when asked.
- **Screenshot-Driven Debugging**:
  - The user often uploads screenshots of bugs, UI layout cutoffs, or error screens without long explanations.
  - Visually inspect the screenshot immediately: check bounding boxes, resize handles, zoom levels, console/boundary error messages, and CSS layout edges.
- **Strictly No Emojis**:
  - Never use emojis anywhere: not in code, not in the UI, not in commit messages, and not in chat responses.
- **Concise, Professional Tone**:
  - Keep responses structured, technical, and to the point. No conversational filler or generic apologies.

---

## 2. Strict Project Rules & Boundaries

1. **Code Modification Scope**:
   - By default, edit **only `frontend/src/` and documentation** (`PROJECT_LOG.md`, `HANDOVER.md`).
   - Do **NOT** touch `outputs/`, `models`, `checkpoints`, `datasets`, `work/`, the database, dependencies, or `package.json` unless explicitly instructed.
   - Any backend change in `api/` requires **explicit user permission/approval**.
2. **No Deleting Files**: Never delete existing project files or scripts.
3. **No Autonomous Commits or Pushes**:
   - Do NOT run `git commit` or `git push` on your own.
   - When the user says *"about to push now"* or requests verification: run `git status`, `git diff --stat`, confirm the build is fresh, and provide a suggested commit message for the user to review.
4. **No Internal File Paths in UI**: Never expose internal filesystem paths (e.g., `C:\nikhil\...`) or raw stack traces in the user interface or client-facing API responses.
5. **Always Build Frontend Assets**:
   - The FastAPI backend serves the frontend directly from `frontend/dist/`.
   - After any frontend edit, **always run `npm --prefix frontend run build`** to ensure the production build is in sync.
6. **Documentation Synchronization**:
   - Always update `PROJECT_LOG.md` and `HANDOVER.md` after completing a feature or milestone.
   - Always conclude significant changes with `git diff --stat`.

---

## 3. Architecture & Environment Quick Reference

- **Operating System**: Windows (PowerShell shell).
- **Backend**: FastAPI app in `api/server.py`.
  - Start command: `python -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000`
  - Mounts: `dist_dir = ROOT / "frontend/dist"` mounted at `/`.
  - Machine learning runtime: PyTorch and torchvision located in `work/binarizer_env/Lib/site-packages` (appended to `sys.path`).
  - Serialized inference: Uses `_INFERENCE_LOCK` and `torch.no_grad()` with automatic CPU fallback on CUDA OOM.
- **Alternative Explorer**: Streamlit app in `outputs/inscriplens_app.py` (port 8501).
- **Frontend**: Vite + React 19 in `frontend/`.
  - Build: `npm --prefix frontend run build`
  - Lint: `npm --prefix frontend run lint`

---

## 4. Completed Feature History (Up to commit `7c57394`)

1. **Glyph Inspector Redraw, Compare & Persistence (Steps R1–R3)**:
   - Interactive SVG canvas overlay with 8 resize handles, image boundary clamping, and grab-hand pan preservation.
   - Side-by-side comparison card evaluating top-3 alternative ranks.
   - Local persistence under `inscriplens.comparisons.v1`.
2. **Predict-Crop Latency & Robustness Hardening (Step D1)**:
   - In-memory singletons for recognizers, PyTorch CUDA acceleration, and DAG agreement check (~38ms repeat latency).
   - In-flight request cancellation (`AbortController`), 200ms debounce, session cache, 12s timeout guards.
3. **Printable PDF Analysis Report & Preview Modal (Steps E1–E2)**:
   - Fullscreen preview modal (`ReportPreviewDialog.jsx`) and printable sheet (`ReportView.jsx`).
   - Continuous white sheet CSS fix (`height: auto !important; flex-shrink: 0 !important;`) preventing card cutoff.
   - Interactive Script switch (`[ ಕನ್ನಡ | Roman ]`) and Kannada style toggle (`[ Faithful | Modern letters ]`).
   - Dynamic `@page` print paper size injection (`A4` vs `Letter`).
   - Curated Halmidi Inscription archaeological and epigraphic brief (Dr. M. H. Krishna 1936, Kadamba script, royal land grant).

