@echo off
setlocal enabledelayedexpansion
title InscripLens GPU & Environment Setup

echo =====================================================================
echo   InscripLens Studio: Automated GPU & Environment Setup
echo =====================================================================
echo.

:: 1. Check Python installation
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH.
    echo Please install Python 3.10, 3.11, 3.12, or 3.13 from https://www.python.org/
    pause
    exit /b 1
)
python -c "import sys; print(f'Detected Python {sys.version.split()[0]}')"

:: 2. Check Node.js / npm installation
echo.
echo [2/6] Checking Node.js and npm (required for React Studio)...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] npm is not found in PATH.
    echo Please install Node.js 18+ from https://nodejs.org/ if you plan to build frontend changes.
) else (
    echo npm is available.
)

:: 3. Create or reuse virtual environment
echo.
echo [3/6] Setting up Python virtual environment...
if not exist ".venv" (
    echo Creating virtual environment in .venv...
    python -m venv .venv
) else (
    echo Existing .venv found.
)
set VENV_PY=.venv\Scripts\python.exe
set VENV_PIP=.venv\Scripts\pip.exe

:: Upgrade pip
%VENV_PY% -m pip install --upgrade pip

:: 4. Install PyTorch with NVIDIA CUDA 12.4
echo.
echo [4/6] Installing PyTorch with NVIDIA CUDA 12.4 acceleration...
echo (If you do not have an NVIDIA GPU, press Ctrl+C to cancel and run CPU setup instead)
%VENV_PIP% install torch torchvision --index-url https://download.pytorch.org/whl/cu124
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install CUDA 12.4 wheel, falling back to standard torch installation...
    %VENV_PIP% install torch torchvision
)

:: Install core dependencies
echo.
echo Installing core application dependencies...
%VENV_PIP% install -r requirements.txt

:: 5. Build React Studio frontend
echo.
echo [5/6] Building React Epigraphy Studio frontend...
if exist "frontend\package.json" (
    where npm >nul 2>&1
    if %errorlevel% equ 0 (
        cd frontend
        echo Installing npm packages...
        call npm install
        echo Building production bundle...
        call npm run build
        cd ..
    ) else (
        echo [NOTICE] Skipping npm build because npm is not installed.
    )
)

:: 6. Verify GPU and Environment
echo.
echo [6/6] Verifying GPU and installation status...
%VENV_PY% -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU Device Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU (No CUDA GPU detected)')"
%VENV_PY% -c "import fastapi, uvicorn, streamlit, sklearn; print('All core Python packages imported successfully!')"

echo.
echo =====================================================================
echo   Setup Complete!
echo   To launch the Epigraphy Studio:
echo      run_studio.bat
echo   Or run:
echo     .venv\Scripts\python.exe launch_studio.py
echo =====================================================================
echo.
pause

