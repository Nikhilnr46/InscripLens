# Studio onboarding verification — 4 November 2026

Pulled origin/main fast-forward from 141d5a6 to 4b40179. Read PROJECT_LOG.md and HANDOVER.md and inspected the API and frontend source. Existing untracked research outputs were preserved.

## Verified on this machine
- npm install --prefix frontend completed; npm audit reported zero vulnerabilities at install time.
- npm run build --prefix frontend passed (Vite 8.3.5).
- Binarizer weights, Python 3.12 worker and HS027 demo image are present. Worker imports PyTorch 2.5.1+cpu.
- GET /api/status: 200, ready=true, demo_available=true, recognizer_available=true.
- GET /api/demo, /api/demo/image, / and /studio: 200.
- Demo enhancement: 133 candidate regions, 23.37 seconds on one measured run.
- Batch recognition: 133 predictions. This is a workflow count, not an accuracy result.
- Single-region prediction returned a label and three ranked alternatives.
- Saved and read back a QA review with empty suggestion, reviewer STARTUP_QA and model_prediction_unverified status. No expert reading was asserted.
- Missing analysis input, invalid crop geometry and missing batch run identifier each returned HTTP 400.
- Browser loaded the production landing and Studio pages, analysed the demo and displayed the canvas without page errors.
- Resized-canvas regression test passes: API dimensions match processed 1600 x 800 mask for a 2000 x 1000 upload.

## Repairs made during onboarding
- Added FastAPI, Uvicorn and python-multipart to requirements.txt; these were absent from the handover's clean-install requirements.
- Fixed /api/analyse dimensions: coordinates now describe the processed image, not the original larger upload.
- The existing .venv could not start its Python 3.11 interpreter in this session. Created work/studio_env with Python 3.14 and system site packages for local startup; installed the missing FastAPI dependencies there. A fully isolated clean-machine installation was not tested.

## Start locally
From the repository root:

```powershell
.\work\studio_env\Scripts\python.exe -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000
```

The verified server is bound to localhost only. Production frontend files are in frontend/dist and must be rebuilt after frontend changes. Runtime weights and environments remain ignored by Git.

## What changed, and what did not
React/Vite now provides the landing site and three-panel Studio, with FastAPI bridging the existing Python modules. SQLite continues to store analyses and unverified review records. The legacy Streamlit interface retains dataset exploration, printed-source review, source examples and JSON export. These features should not be described as fully migrated to Studio: the current React component has no export action, and the crop API returns reference labels without reference images.

The model benchmarks remain 77/300 (25.67%) with supplied boxes and 52/300 (17.33%) for automatic localization plus correct label. UI polish does not improve these metrics. The handover calls translation outside scope; the original Phase 2 scope included it, so this presentation correctly lists it as unfinished. The handover's 4–10 s enhancement estimate was not reproduced here. Startup checks are not a complete security, accessibility or performance audit.

## Ready next steps
1. Evaluate the fixed original-plus-mask feature candidate before replacing the deployed recognizer.
2. Complete reliable line-level supervision and pass the sequence sanity gate before larger sequence-model training.
3. Bring published-reading/source-example and export workflows into Studio if needed for a unified demo.
4. Review literature eligibility and the explicitly qualified paper results before panel submission.

PPT: outputs/presentation/InscripLens_Presentation3_Studio_final.pptx. It uses the original PES logo on all 48 slides, restores 12 detailed literature entries, adds comparative tables, and updates the architecture, screenshots and verified tests.
