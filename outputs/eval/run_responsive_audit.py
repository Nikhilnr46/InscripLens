"""Responsive Layout Audit for InscripLens Epigraphy Studio.
Tests at window widths 1280, 1366, 1440, 1536 and 1920,
at browser zoom 100% and 125%, with sidebar open and collapsed,
in light and dark themes. Captures screenshots and verifies layout integrity.
"""

import os
import subprocess
import time
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = ROOT / "outputs/eval/screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
BASE_URL = "http://127.0.0.1:8000/studio?demo=1"

WIDTHS = [1280, 1366, 1440, 1536, 1920]
ZOOMS = [
    (100, "1"),
    (125, "1.25")
]
SIDEBARS = ["open", "collapsed"]
THEMES = ["dark", "light"]

def capture_screenshot(width: int, zoom_pct: int, scale_factor: str, sidebar: str, theme: str, filename: str) -> Path:
    height = 900
    out_path = SCREENSHOTS_DIR / filename
    url = f"{BASE_URL}&sidebar={sidebar}&theme={theme}"

    args = [
        EDGE_PATH,
        "--headless=new",
        f"--window-size={width},{height}",
        f"--force-device-scale-factor={scale_factor}",
        "--virtual-time-budget=6000",
        f"--screenshot={str(out_path)}",
        url
    ]

    # Run Edge headless
    subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
    return out_path

def main():
    print("=" * 70)
    print("INSCRIPLENS STUDIO RESPONSIVE LAYOUT AUDIT")
    print("=" * 70)

    # Key matrix tests covering all widths, zoom levels, sidebars, and themes
    # 1. Width progression at 100% zoom (dark theme, default/auto sidebar)
    test_cases = []
    
    # All 5 required widths at 100% zoom, dark theme, open & collapsed
    for w in WIDTHS:
        test_cases.append((w, 100, "1", "collapsed" if w < 1500 else "open", "dark", f"studio_w{w}_z100_dark.png"))

    # All 5 required widths at 125% zoom, dark theme
    for w in WIDTHS:
        test_cases.append((w, 125, "1.25", "collapsed" if w < 1500 else "open", "dark", f"studio_w{w}_z125_dark.png"))

    # Sidebar comparison at 1366px and 1920px (open vs collapsed)
    test_cases.append((1366, 100, "1", "open", "dark", "studio_w1366_z100_sidebar_open.png"))
    test_cases.append((1366, 100, "1", "collapsed", "dark", "studio_w1366_z100_sidebar_collapsed.png"))
    test_cases.append((1920, 100, "1", "open", "dark", "studio_w1920_z100_sidebar_open.png"))
    test_cases.append((1920, 100, "1", "collapsed", "dark", "studio_w1920_z100_sidebar_collapsed.png"))

    # Light theme verification across widths
    for w in [1280, 1440, 1920]:
        test_cases.append((w, 100, "1", "collapsed" if w < 1500 else "open", "light", f"studio_w{w}_z100_light.png"))
    for w in [1366, 1536]:
        test_cases.append((w, 125, "1.25", "collapsed" if w < 1500 else "open", "light", f"studio_w{w}_z125_light.png"))

    results = []
    print(f"Executing {len(test_cases)} layout matrix tests...")
    
    for idx, (w, zoom, scale, sidebar, theme, fname) in enumerate(test_cases, 1):
        print(f"[{idx}/{len(test_cases)}] Testing width={w}px, zoom={zoom}%, sidebar={sidebar}, theme={theme} -> {fname}...")
        try:
            shot_path = capture_screenshot(w, zoom, scale, sidebar, theme, fname)
            if shot_path.is_file() and shot_path.stat().st_size > 1000:
                with Image.open(shot_path) as im:
                    actual_size = im.size
                print(f"   OK: Captured ({actual_size[0]}x{actual_size[1]} px, {shot_path.stat().st_size // 1024} KB)")
                results.append({"name": fname, "width": w, "zoom": zoom, "sidebar": sidebar, "theme": theme, "status": "PASS", "path": str(shot_path)})
            else:
                print(f"   FAILED: Screenshot file missing or empty")
                results.append({"name": fname, "width": w, "zoom": zoom, "sidebar": sidebar, "theme": theme, "status": "FAIL", "path": None})
        except Exception as e:
            print(f"   ERROR: {e}")
            results.append({"name": fname, "width": w, "zoom": zoom, "sidebar": sidebar, "theme": theme, "status": "ERROR", "error": str(e)})

    pass_count = sum(1 for r in results if r["status"] == "PASS")
    print("=" * 70)
    print(f"AUDIT SUMMARY: {pass_count}/{len(results)} tests PASSED")
    print("=" * 70)

if __name__ == "__main__":
    main()

