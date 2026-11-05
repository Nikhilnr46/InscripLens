#!/usr/bin/env bash
set -e

echo "====================================================================="
echo "  InscripLens Studio: Automated GPU & Environment Setup (Linux/Mac)"
echo "====================================================================="
echo ""

# 1. Check Python
echo "[1/6] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10-3.13."
    exit 1
fi
python3 -c "import sys; print(f'Detected Python {sys.version.split()[0]}')"

# 2. Check Node.js & npm
echo ""
echo "[2/6] Checking Node.js and npm..."
if ! command -v npm &> /dev/null; then
    echo "[WARNING] npm not found. Install Node.js 18+ to build the frontend."
else
    echo "npm is available."
fi

# 3. Create Virtual Environment
echo ""
echo "[3/6] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

$VENV_PY -m pip install --upgrade pip

# 4. Install PyTorch with CUDA 12.4
echo ""
echo "[4/6] Installing PyTorch with CUDA 12.4..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing CUDA 12.4 PyTorch wheels..."
    $VENV_PIP install torch torchvision --index-url https://download.pytorch.org/whl/cu124
else
    echo "No NVIDIA GPU detected. Installing default PyTorch..."
    $VENV_PIP install torch torchvision
fi

echo "Installing core application dependencies..."
$VENV_PIP install -r requirements.txt

# 5. Build React Studio frontend
echo ""
echo "[5/6] Building React Epigraphy Studio frontend..."
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    cd frontend
    npm install
    npm run build
    cd ..
fi

# 6. Verify Installation
echo ""
echo "[6/6] Verifying GPU and installation status..."
$VENV_PY -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
$VENV_PY -c "import fastapi, uvicorn, streamlit, sklearn; print('All core Python packages imported successfully!')"

echo ""
echo "====================================================================="
echo "  Setup Complete!"
echo "  Launch Studio with:"
echo "    .venv/bin/python launch_studio.py"
echo "====================================================================="
