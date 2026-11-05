import re
from pathlib import Path

text = Path("frontend/src/App.jsx").read_text(encoding="utf-8").replace("\r\n", "\n")
script = Path("outputs/eval/update_app_jsx.py").read_text(encoding="utf-8").replace("\r\n", "\n")

m = re.search(r'predict_box_old = """(.*?)"""', script, re.DOTALL)
if m:
    pb_old = m.group(1)
    idx = text.find("// Predict selected crop region")
    act = text[idx:idx+len(pb_old)+20]
    for i in range(min(len(pb_old), len(act))):
        if pb_old[i] != act[i]:
            print(f"Diff at char {i}:")
            print("pb_old:", repr(pb_old[max(0, i-20):i+30]))
            print("actual:", repr(act[max(0, i-20):i+30]))
            break

