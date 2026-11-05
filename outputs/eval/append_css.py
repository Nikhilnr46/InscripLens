from pathlib import Path

css_path = Path("frontend/src/index.css")
content = css_path.read_text(encoding="utf-8")

additions = """

/* --------------------------------------------------------------------------
   Kannada Script & Lossy/Marker Tags
   -------------------------------------------------------------------------- */
.lossy-tag {
  display: inline-block;
  font-size: 0.58rem;
  font-weight: 600;
  color: #D97706;
  background-color: rgba(217, 119, 6, 0.15);
  border: 1px solid rgba(217, 119, 6, 0.35);
  padding: 0 4px;
  border-radius: 3px;
  vertical-align: middle;
  line-height: 1.2;
  margin-left: 4px;
  text-transform: lowercase;
  letter-spacing: 0.02em;
  font-family: 'Inter', -apple-system, sans-serif;
}

.roman-marker-tag {
  display: inline-block;
  font-size: 0.58rem;
  font-weight: 600;
  color: #94A3B8;
  background-color: rgba(148, 163, 184, 0.15);
  border: 1px solid rgba(148, 163, 184, 0.35);
  padding: 0 4px;
  border-radius: 3px;
  vertical-align: middle;
  line-height: 1.2;
  margin-left: 4px;
  letter-spacing: 0.02em;
  font-family: 'Inter', -apple-system, sans-serif;
}

.tiny-tag {
  display: inline-block;
  font-size: 0.58rem;
  color: #A8A29A;
  background-color: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 500;
}

.kannada-text {
  font-family: 'Noto Sans Kannada', 'Inter', sans-serif;
}
"""

if ".lossy-tag" not in content:
    content += additions
    css_path.write_text(content, encoding="utf-8")
    print("Appended CSS rules successfully")
else:
    print("CSS rules already present")

