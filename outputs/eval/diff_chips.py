from pathlib import Path

text = Path("frontend/src/App.jsx").read_text(encoding="utf-8").replace("\r\n", "\n")

idx = text.find('className="glyph-chip-label"')
assert idx != -1
start_idx = text.rfind('<div', 0, idx)
end_target = "}\n                            </div>\n                          )}"
end_idx = text.find(end_target, idx) + len(end_target)

chips_actual = text[start_idx:end_idx]
print("Found chips_actual, len:", len(chips_actual))

# Update update_app_jsx.py to use chips_actual
script_path = Path("outputs/eval/update_app_jsx.py")
script_text = script_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# Replace chips_old = """...""" with chips_old = chips_actual
import re
script_text = re.sub(r'chips_old = """.*?"""', 'chips_old = ' + repr(chips_actual), script_text, flags=re.DOTALL)
script_path.write_text(script_text, encoding="utf-8")
print("Updated chips_old in update_app_jsx.py")
