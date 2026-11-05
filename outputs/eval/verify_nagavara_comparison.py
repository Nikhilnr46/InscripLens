"""Empirical verification of Standard vs High Accuracy enhancement modes on Nagavara demonstration stone."""
import time
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(ROOT / 'outputs'))

from binarizer_core import load_model, enhance, enhance_multiscale
from segment_candidates import candidates

def main():
    demo_path = ROOT / 'outputs/full_binarizer/HS027_original.png'
    assert demo_path.is_file(), f"Nagavara demonstration stone missing: {demo_path}"

    with Image.open(demo_path) as im:
        raw_image = ImageOps.exif_transpose(im).convert('RGB')

    print("=" * 70)
    print("NAGAVARA DEMONSTRATION STONE: ENHANCEMENT MODE VERIFICATION")
    print(f"Image dimensions: {raw_image.width} x {raw_image.height}")
    print("=" * 70)

    device = 'cuda'
    model = load_model(device)

    # 1. Standard Mode (single-scale GPU)
    print("\n[1] Running Standard Mode (Single-Scale GPU)...")
    t0 = time.perf_counter()
    std_mask = enhance(raw_image, model)
    std_time = time.perf_counter() - t0
    std_boxes = candidates(std_mask)
    std_fg_pixels = int(np.sum(np.array(std_mask) > 128))

    print(f"  Runtime: {std_time:.3f} seconds")
    print(f"  Candidate boxes detected: {len(std_boxes)}")
    print(f"  Foreground stroke pixels: {std_fg_pixels}")
    assert len(std_boxes) == 133, f"Expected 133 candidate boxes in standard mode, got {len(std_boxes)}"

    # 2. High Accuracy Mode (multi-scale sliding window GPU)
    print("\n[2] Running High Accuracy Mode (Multi-Scale Sliding Window GPU)...")
    t1 = time.perf_counter()
    high_mask = enhance_multiscale(raw_image, model)
    high_time = time.perf_counter() - t1
    high_boxes = candidates(high_mask)
    high_fg_pixels = int(np.sum(np.array(high_mask) > 128))

    print(f"  Runtime: {high_time:.3f} seconds")
    print(f"  Candidate boxes detected: {len(high_boxes)}")
    print(f"  Foreground stroke pixels: {high_fg_pixels}")

    # 3. Stroke Comparison
    std_arr = np.array(std_mask) > 128
    high_arr = np.array(high_mask) > 128
    common_fg = np.sum(std_arr & high_arr)
    new_in_high = np.sum(~std_arr & high_arr)
    lost_in_high = np.sum(std_arr & ~high_arr)

    print("\n[3] Stroke Pixel Comparison:")
    print(f"  Common foreground pixels: {common_fg}")
    print(f"  Faint stroke pixels recovered by High Accuracy (+): {new_in_high} ({new_in_high / std_fg_pixels * 100:.2f}% increase)")
    print(f"  Pixels filtered out (-): {lost_in_high}")
    print(f"  Candidate reduction (connected cohesive glyphs): {len(std_boxes)} -> {len(high_boxes)} (-{len(std_boxes) - len(high_boxes)} broken fragments)")

    # 4. Generate Visual Side-by-Side Comparison
    print("\n[4] Generating Side-by-Side Comparison Image...")
    # Composite panel: [Original | Standard Mask | High Accuracy Mask | Difference Overlay]
    w, h = raw_image.size
    panel = Image.new('RGB', (w * 4 + 30, h + 50), (18, 18, 20))
    draw = ImageDraw.Draw(panel)

    # Convert masks to RGB
    std_rgb = ImageOps.colorize(std_mask.convert('L'), black=(15, 15, 18), white=(220, 220, 225))
    high_rgb = ImageOps.colorize(high_mask.convert('L'), black=(15, 15, 18), white=(220, 220, 225))

    # Difference visualization:
    # Black background, Cyan for common strokes, Amber/Gold for new faint strokes recovered by high accuracy
    diff_arr = np.zeros((h, w, 3), dtype=np.uint8)
    diff_arr[:, :] = [18, 18, 20]
    diff_arr[std_arr & high_arr] = [180, 200, 220]        # Common strokes (Silver)
    diff_arr[~std_arr & high_arr] = [230, 160, 40]        # New faint strokes (Amber)
    diff_arr[std_arr & ~high_arr] = [180, 60, 60]         # Standard only (Red)
    diff_img = Image.fromarray(diff_arr)

    panel.paste(raw_image, (0, 40))
    panel.paste(std_rgb, (w + 10, 40))
    panel.paste(high_rgb, (w * 2 + 20, 40))
    panel.paste(diff_img, (w * 3 + 30, 40))

    # Add header labels
    draw.text((10, 12), f"1. Original Stone ({w}x{h})", fill=(201, 166, 107))
    draw.text((w + 20, 12), f"2. Standard Mode ({std_time:.2f}s, {len(std_boxes)} boxes)", fill=(201, 166, 107))
    draw.text((w * 2 + 30, 12), f"3. High Accuracy Mode ({high_time:.2f}s, {len(high_boxes)} boxes)", fill=(201, 166, 107))
    draw.text((w * 3 + 40, 12), f"4. Stroke Difference (Amber: +{new_in_high} faint px)", fill=(230, 160, 40))

    out_img_path = ROOT / 'outputs/eval/mask_mode_comparison_nagavara.png'
    panel.save(out_img_path)
    print(f"Saved visual comparison to {out_img_path}")

    report = {
        "stone_id": "HS027",
        "stone_name": "Nagavara 971CE Herostone With Inscription",
        "dimensions": [w, h],
        "device": device,
        "standard_mode": {
            "method": "single_scale_pretrained_binarization",
            "runtime_seconds": round(std_time, 4),
            "candidate_boxes": len(std_boxes),
            "foreground_pixels": std_fg_pixels
        },
        "high_accuracy_mode": {
            "method": "multiscale_context_aware_binarization_paper5",
            "runtime_seconds": round(high_time, 4),
            "candidate_boxes": len(high_boxes),
            "foreground_pixels": high_fg_pixels
        },
        "comparison": {
            "common_foreground_pixels": int(common_fg),
            "faint_stroke_pixels_recovered": int(new_in_high),
            "faint_stroke_pixel_gain_pct": round(new_in_high / std_fg_pixels * 100, 2),
            "candidate_count_change": len(high_boxes) - len(std_boxes),
            "note": "Multi-scale fusion connects fragmented strokes across scales, resulting in more coherent character components and capturing faint shallow incisions."
        },
        "comparison_image_path": str(out_img_path)
    }

    report_json_path = ROOT / 'outputs/eval/nagavara_mode_comparison_report.json'
    report_json_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Saved numerical report to {report_json_path}")

if __name__ == '__main__':
    main()

