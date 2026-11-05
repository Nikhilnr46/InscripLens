"""Single-command launcher for InscripLens Epigraphy Studio.
Starts the local FastAPI server and opens the modern React Studio interface.
"""

from pathlib import Path
import subprocess
import sys
import webbrowser
import shutil

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("=======================================================")
    print("  InscripLens Epigraphy Studio (Local Web Interface)")
    print("  Running on: http://127.0.0.1:8000")
    print("=======================================================")
    
    # Check if frontend bundle exists; if not, build it automatically if npm is available
    dist_index = ROOT / "frontend" / "dist" / "index.html"
    if not dist_index.is_file():
        print("[NOTICE] Frontend build not found in frontend/dist.")
        if shutil.which("npm"):
            print("Building frontend assets automatically via npm...")
            try:
                subprocess.run(["npm", "run", "build"], cwd=str(ROOT / "frontend"), check=True, shell=True)
                print("Frontend build complete.")
            except Exception as e:
                print(f"[WARNING] Could not automatically build frontend: {e}")
                print("Please run: cd frontend && npm install && npm run build")
        else:
            print("Please install Node.js/npm and build the frontend: cd frontend && npm install && npm run build")

    # Open browser automatically
    webbrowser.open("http://127.0.0.1:8000")
    
    # Run Uvicorn serving both API and bundled React frontend
    subprocess.run([
        sys.executable, "-m", "uvicorn", "server:app",
        "--app-dir", "api",
        "--host", "127.0.0.1",
        "--port", "8000"
    ], check=True)
