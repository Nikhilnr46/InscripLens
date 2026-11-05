from pathlib import Path
import re

lines = Path("frontend/src/App.jsx").read_text(encoding="utf-8").splitlines()

for i, l in enumerate(lines[909:], start=910):
    # Check for direct accesses like analysis.id, analysis.boxes, etc.
    # without optional chaining analysis?.
    matches = re.findall(r'\banalysis\.([a-zA-Z0-9_]+)', l)
    if matches:
        print(f"{i}: {l.strip()}")

