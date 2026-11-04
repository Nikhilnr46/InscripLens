"""Single-command launcher for InscripLens Epigraphy Studio.
Starts the local FastAPI server and opens the modern React Studio interface.
"""

from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("=======================================================")
    print("  InscripLens Epigraphy Studio (Local Web Interface)")
    print("  Running on: http://127.0.0.1:8000")
    print("=======================================================")
    
    # Open browser automatically
    webbrowser.open("http://127.0.0.1:8000")
    
    # Run Uvicorn serving both API and bundled React frontend
    subprocess.run([
        sys.executable, "-m", "uvicorn", "server:app",
        "--app-dir", "api",
        "--host", "127.0.0.1",
        "--port", "8000"
    ], check=True)

