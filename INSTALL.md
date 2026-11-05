# InscripLens Setup & GPU Installation Guide

This document describes how to install and configure InscripLens on a clean machine, including NVIDIA CUDA GPU acceleration, the local FastAPI Epigraphy Studio, the React frontend, and model runtime assets.

---

## 1. System Requirements

- **Operating System**: Windows 10/11 (64-bit) or Linux (Ubuntu 20.04/22.04 LTS recommended)
- **Python**: Python 3.10, 3.11, 3.12, or 3.13 (64-bit)
- **Node.js**: Node.js 18.x or 20.x with `npm` (required for React Studio build)
- **GPU (Recommended for Multi-Scale Enhancement)**:
  - NVIDIA GeForce RTX 3050, 3060, 4060, or higher (minimum 4 GB VRAM)
  - NVIDIA Driver version supporting CUDA 12.x or 11.8
  - CPU Fallback: Standard enhancement mode runs on CPU automatically if no GPU is available or if VRAM runs out.

---

## 2. Quick Setup (1-Click Automated Script)

### On Windows:
Double-click `setup_gpu.bat` or run in Command Prompt / PowerShell:
```powershell
.\setup_gpu.bat
```

### On Linux / macOS:
```bash
chmod +x setup_gpu.sh
./setup_gpu.sh
```

The script will automatically:
1. Verify Python and npm.
2. Create a virtual environment `.venv`.
3. Install PyTorch with CUDA 12.4 support (`--index-url https://download.pytorch.org/whl/cu124`).
4. Install all core application dependencies from `requirements.txt`.
5. Build the React frontend bundle (`frontend/dist`).
6. Verify GPU detection (`torch.cuda.is_available()`).

---

## 3. Manual Step-by-Step Installation

If you prefer to configure your environment manually:

### Step 3.1: Create and Activate Virtual Environment
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3.2: Install PyTorch with CUDA Acceleration
```bash
# For CUDA 12.4 (RTX 30-series, 40-series, etc.):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# For CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CPU-only (no GPU):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Step 3.3: Install Application Dependencies
```bash
pip install -r requirements.txt
```

### Step 3.4: Build the React Epigraphy Studio Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 4. Runtime Model Assets & Data Layout

InscripLens relies on the following runtime model files:

| File Path | Description | Source |
|---|---|---|
| `work/shilalekhya/Unet/model.py` | Shilalekhya U-Net Model architecture | [IIIT Hyderabad Shilalekhya](https://github.com/ihdia/shilalekhya-binarization) |
| `work/shilalekhya/binarizer.pth` | Shilalekhya pretrained weights (~120 MB) | [IIIT Hyderabad Shilalekhya](https://github.com/ihdia/shilalekhya-binarization) |
| `outputs/broad_clean_study/mask_svm_bundle.joblib` | Calibrated character recognition bundle (~76.8 MB) | Trained from EpiSAM hero & temple stones |
| `outputs/full_binarizer/HS027_original.png` | Nagavara demonstration hero stone photograph | The Mythic Society Bengaluru / EpiSAM |

> [!NOTE]
> If you received `InscripLens_runtime_assets.zip` or `InscripLens_recognizer_update.zip`, extract them directly into the repository root so the `work/` and `outputs/` folders merge into place.

To verify that model assets are in place, check:
```powershell
python -c "from pathlib import Path; print('Binarizer model exists:', (Path('work/shilalekhya/binarizer.pth')).is_file()); print('Recognizer bundle exists:', (Path('outputs/broad_clean_study/mask_svm_bundle.joblib')).is_file())"
```

---

## 5. Launching the Application

### Option A: Launch InscripLens Epigraphy Studio (Recommended)
Double-click `run_studio.bat` or run:
```powershell
python launch_studio.py
```
Or start Uvicorn directly:
```powershell
python -m uvicorn server:app --app-dir api --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.

### Option B: Launch Legacy Streamlit Explorer
```powershell
streamlit run outputs/inscriplens_app.py --server.port 8501
```
Open **`http://127.0.0.1:8501`** in your browser.

---

## 6. Verification and Diagnostics

Run the automated regression verification suite:
```powershell
python outputs/eval/verify_kannada_regression.py
```
This tests:
1. `/api/status`: Asset readiness and demo stone presence
2. `/api/analyse`: High accuracy and standard enhancement execution
3. `/api/predict-crop`: Character prediction and Kannada script rendering
4. `/api/reviews`: SQLite review storage and provenance tracking
5. `/api/export`: CSV / JSON export integrity
6. `/api/recognize-all`: Batch character recognition

GPU verification command:
```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available(), '| Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

