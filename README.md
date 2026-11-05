# InscripLens

An application for analysing historical Kannada inscription images, with a hero-stone pilot dataset. It connects pretrained enhancement (standard single-scale and high-accuracy multi-scale GPU enhancement), candidate-region detection, calibrated character recognition, Kannada script display, and expert review/storage.

## Installation & Setup

For full installation and GPU acceleration setup instructions, see **[INSTALL.md](INSTALL.md)**.

### Quick Start (GPU / Local)
- **Windows**: Double-click `setup_gpu.bat` or run:
  ```powershell
  .\setup_gpu.bat
  .\run_studio.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x setup_gpu.sh
  ./setup_gpu.sh
  python launch_studio.py
  ```
- Open **`http://127.0.0.1:8000`** in your browser.

## Project Handover and Engineering Log

- **Installation & GPU Setup**: See [INSTALL.md](INSTALL.md) for step-by-step environment, CUDA, PyTorch, and asset layout instructions.
- **Project Handover & Technical Guide**: See [HANDOVER.md](HANDOVER.md) for full architecture, clean installation, API references, privacy specifications, and pre-push audit results.
- **Engineering Trajectory & Milestone Log**: See [PROJECT_LOG.md](PROJECT_LOG.md).
- **Benchmark Evaluation**: See [BENCHMARK.md](BENCHMARK.md) for character recognition, multi-scale enhancement, and calibration metrics.

## Current capabilities

- **Local Web Studio**: FastAPI backend + React Studio running locally with interactive Curtain viewer, candidate boxes, and responsive toolbar.
- **Multi-Scale GPU Enhancement**: Standard single-scale and high-accuracy multi-scale sliding window enhancement (using NVIDIA GPU with automatic CPU fallback).
- **Kannada Script Display**: Real-time transliteration converter rendering Old and Modern Kannada script (`Noto Sans Kannada`), with modern letter mapping (`ಱ/ೞ` -> `ರ/ಳ`).
- **Calibrated Character Recognition**: Calibrated ensemble recognizer with confidence scores, uncertainty tagging, and candidate alternatives.
- **Verification & Review Storage**: Epigraphic review storage in SQLite (`work/app_data/history.sqlite3`) with JSON/CSV provenance export.
- **Demonstration Stone**: Offline demonstration stone (Nagavara 971 CE hero stone) for zero-network testing.
- **Streamlit Explorer**: Legacy Streamlit interface (`streamlit run outputs/inscriplens_app.py --server.port 8501`).

Reliable full-stone OCR, historical-to-modern Kannada conversion and English translation are **not implemented**. Current diagnostic recognition is weak: broader cleaned-image HOG/SVM 77/300 (25.67%), matched hero-only HOG/SVM 63/300 (21%), small CNN 44/300 (14.67%), frozen ResNet18-feature classifier 46/300 (15.33%). These use supplied reference boxes, reused validation, and incompletely documented binarizer pretraining overlap. They are not independent end-to-end accuracy results.

## Local start

To run the InscripLens Epigraphy Studio:
```powershell
python launch_studio.py
```
Or start Uvicorn directly:
```powershell
python -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000 . This serves only on localhost. Analysis history stays in `work/app_data`.

To run the legacy Streamlit explorer:
```powershell
python -m streamlit run outputs/inscriplens_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

## Checks & Verification

Run the automated regression test suite:
```powershell
python outputs/eval/verify_kannada_regression.py
```

Run component diagnostic checks:
```powershell
python outputs/check_app.py
python outputs/check_app_backend.py
```

## Contribution and attribution

See `THIRD_PARTY.md` for upstream notices and dataset attributions (IIIT Hyderabad Shilalekhya U-Net, The Mythic Society Bengaluru EpiSAM dataset).
