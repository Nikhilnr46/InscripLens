from pathlib import Path

lines = Path("frontend/src/App.jsx").read_text(encoding="utf-8").splitlines()

for i, l in enumerate(lines):
    if "route ===" in l or "route" in l and "return" in l:
        print(f"{i+1}: {l.strip()}")

