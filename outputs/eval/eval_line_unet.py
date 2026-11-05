"""Evaluation script for Line-Segmentation U-Net on EpiSAM validation set and non-EpiSAM photographs."""
import json
import time
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import torch
import torch.nn.functional as F
from scipy import ndimage, signal

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from outputs.train_line_segmentation_gpu import LineUNet

ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT / 'outputs/eval'
OVERLAYS_DIR = OUTPUT_DIR / 'line_overlays'

def match_instances(pred_masks, gold_masks, iou_thresh=0.5):
    """Greedy bipartite matching of predicted instances to gold instances at IoU threshold."""
    num_pred = len(pred_masks)
    num_gold = len(gold_masks)
    if num_pred == 0 or num_gold == 0:
        return {'tp': 0, 'fp': num_pred, 'fn': num_gold, 'matches': [], 'mean_matched_iou': 0.0}

    iou_mat = np.zeros((num_pred, num_gold), dtype=np.float32)
    for i, p in enumerate(pred_masks):
        p_bool = p > 0
        p_sum = np.sum(p_bool)
        for j, g in enumerate(gold_masks):
            g_bool = g > 0
            inter = np.sum(p_bool & g_bool)
            union = p_sum + np.sum(g_bool) - inter
            iou_mat[i, j] = inter / union if union > 0 else 0.0

    pairs = []
    for i in range(num_pred):
        for j in range(num_gold):
            if iou_mat[i, j] >= iou_thresh:
                pairs.append((iou_mat[i, j], i, j))
    pairs.sort(reverse=True, key=lambda x: x[0])

    matched_p = set()
    matched_g = set()
    matches = []
    for iou, i, j in pairs:
        if i not in matched_p and j not in matched_g:
            matched_p.add(i)
            matched_g.add(j)
            matches.append({'pred_idx': i, 'gold_idx': j, 'iou': float(iou)})

    tp = len(matches)
    fp = num_pred - tp
    fn = num_gold - tp
    mean_iou = float(np.mean([m['iou'] for m in matches])) if matches else 0.0
    return {'tp': tp, 'fp': fp, 'fn': fn, 'matches': matches, 'mean_matched_iou': mean_iou}

def split_cc(pred_bin, min_area=300):
    """Split into instances via connected components."""
    labeled, num_features = ndimage.label(pred_bin)
    instances = []
    for i in range(1, num_features + 1):
        mask = (labeled == i)
        if np.sum(mask) >= min_area:
            instances.append(mask)
    return instances

def split_valleys(pred_bin, min_area=300):
    """Split into instances using horizontal projection profile valley detection."""
    h, w = pred_bin.shape
    proj = np.sum(pred_bin, axis=1).astype(float)
    if np.sum(proj) < min_area:
        return []

    # Smooth profile
    sigma = max(2.0, h / 80.0)
    smoothed = ndimage.gaussian_filter1d(proj, sigma=sigma)
    
    # Text vertical extent
    active_y = np.where(smoothed > np.max(smoothed) * 0.1)[0]
    if len(active_y) < 10:
        return split_cc(pred_bin, min_area)
    
    y_min, y_max = active_y[0], active_y[-1]
    sub_smoothed = smoothed[y_min:y_max+1]
    
    # Invert to find valleys
    inv = np.max(sub_smoothed) - sub_smoothed
    valleys, _ = signal.find_peaks(inv, distance=max(10, int(h / 30)), prominence=np.max(sub_smoothed) * 0.15)
    
    if len(valleys) == 0:
        return split_cc(pred_bin, min_area)

    split_y = sorted([y_min + v for v in valleys])
    bands = []
    prev_y = 0
    for sy in split_y:
        band_mask = np.zeros_like(pred_bin)
        band_mask[prev_y:sy, :] = pred_bin[prev_y:sy, :]
        if np.sum(band_mask) >= min_area:
            bands.append(band_mask)
        prev_y = sy
    
    # Final band
    band_mask = np.zeros_like(pred_bin)
    band_mask[prev_y:h, :] = pred_bin[prev_y:h, :]
    if np.sum(band_mask) >= min_area:
        bands.append(band_mask)

    return bands

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 60)
    print("LINE U-NET BENCHMARK AUDIT")
    print(f"Device: {device}")
    print("=" * 60)

    ckpt_path = ROOT / 'outputs/line_study/line_segmentation_episam_gpu.pth'
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    ckpt = torch.load(ckpt_path, map_location=device)
    model = LineUNet(1, 1).to(device)
    model.load_state_dict(ckpt['state_dict'])
    model.eval()

    val_dir = ROOT / 'episam/episam_dataset/episam_dataset/lines/val'
    bin_dir = ROOT / 'episam/episam_dataset/episam_dataset/binary_images/val'
    folders = sorted([f for f in val_dir.iterdir() if f.is_dir()])
    print(f"Loaded {len(folders)} validation inscriptions.")

    OVERLAYS_DIR.mkdir(parents=True, exist_ok=True)

    results_cc = []
    results_valleys = []
    per_image_audit = []

    for idx, folder in enumerate(folders):
        mask_file = bin_dir / (folder.name + '.png')
        gold_files = sorted(list(folder.glob('line_*_mask.png')))
        if not mask_file.exists() or not gold_files:
            continue

        with Image.open(mask_file) as im:
            orig_w, orig_h = im.size
            in_pil = im.convert('L').resize((256, 256), Image.Resampling.BILINEAR)

        in_tensor = torch.from_numpy(np.array(in_pil, dtype=np.float32)[None, None] / 255.0).to(device)
        with torch.no_grad():
            pred_tensor = model(in_tensor)
            pred_upsampled = F.interpolate(pred_tensor, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
            pred_orig = pred_upsampled.squeeze().cpu().numpy()

        pred_bin = (pred_orig > 0.5).astype(np.uint8)

        # Load gold line masks
        gold_masks = []
        for gf in gold_files:
            with Image.open(gf) as gim:
                g_arr = (np.array(gim.convert('L')) > 128).astype(np.uint8)
                gold_masks.append(g_arr)

        num_gold = len(gold_masks)

        # Split instances
        inst_cc = split_cc(pred_bin)
        inst_valleys = split_valleys(pred_bin)

        eval_cc = match_instances(inst_cc, gold_masks, iou_thresh=0.5)
        eval_valleys = match_instances(inst_valleys, gold_masks, iou_thresh=0.5)

        results_cc.append({
            'num_gold': num_gold,
            'num_pred': len(inst_cc),
            'tp': eval_cc['tp'],
            'fp': eval_cc['fp'],
            'fn': eval_cc['fn'],
            'exact_count': int(len(inst_cc) == num_gold),
            'count_error': abs(len(inst_cc) - num_gold)
        })

        results_valleys.append({
            'num_gold': num_gold,
            'num_pred': len(inst_valleys),
            'tp': eval_valleys['tp'],
            'fp': eval_valleys['fp'],
            'fn': eval_valleys['fn'],
            'exact_count': int(len(inst_valleys) == num_gold),
            'count_error': abs(len(inst_valleys) - num_gold)
        })

        per_image_audit.append({
            'name': folder.name,
            'dimensions': [orig_w, orig_h],
            'gold_lines': num_gold,
            'cc_pred_lines': len(inst_cc),
            'cc_tp': eval_cc['tp'],
            'cc_count_error': abs(len(inst_cc) - num_gold),
            'valley_pred_lines': len(inst_valleys),
            'valley_tp': eval_valleys['tp'],
            'valley_count_error': abs(len(inst_valleys) - num_gold),
            'pred_bin': pred_bin,
            'gold_masks': gold_masks,
            'mask_file': mask_file
        })

    def aggregate_metrics(res_list):
        tot_gold = sum(r['num_gold'] for r in res_list)
        tot_pred = sum(r['num_pred'] for r in res_list)
        tot_tp = sum(r['tp'] for r in res_list)
        tot_fp = sum(r['fp'] for r in res_list)
        tot_fn = sum(r['fn'] for r in res_list)
        exact_acc = sum(r['exact_count'] for r in res_list) / len(res_list)
        mae = sum(r['count_error'] for r in res_list) / len(res_list)
        prec = tot_tp / (tot_tp + tot_fp) if (tot_tp + tot_fp) > 0 else 0.0
        rec = tot_tp / (tot_tp + tot_fn) if (tot_tp + tot_fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return {
            'total_gold_lines': tot_gold,
            'total_pred_lines': tot_pred,
            'exact_line_count_accuracy': round(exact_acc, 4),
            'mean_absolute_line_count_error': round(mae, 2),
            'instance_true_positives': tot_tp,
            'instance_false_positives': tot_fp,
            'instance_false_negatives': tot_fn,
            'instance_precision_iou50': round(prec, 4),
            'instance_recall_iou50': round(rec, 4),
            'instance_f1_iou50': round(f1, 4)
        }

    agg_cc = aggregate_metrics(results_cc)
    agg_valleys = aggregate_metrics(results_valleys)

    print("\n--- RESULTS: CONNECTED COMPONENTS (RAW MODEL OUTPUT) ---")
    for k, v in agg_cc.items():
        print(f"  {k}: {v}")

    print("\n--- RESULTS: HORIZONTAL VALLEY SPLITTING POSTPROCESS ---")
    for k, v in agg_valleys.items():
        print(f"  {k}: {v}")

    # Generate overlays for the 3 worst cases (sorted by cc_count_error descending)
    worst_cases = sorted(per_image_audit, key=lambda x: x['cc_count_error'], reverse=True)[:3]
    overlay_records = []

    for rank, case in enumerate(worst_cases, 1):
        name = case['name']
        w, h = case['dimensions']
        pred_b = case['pred_bin']
        golds = case['gold_masks']

        # Create overlay visualization
        # RGB base: 3-channel grayscale of input mask
        with Image.open(case['mask_file']) as im:
            base_rgb = ImageOps_gray_to_rgb = Image.new('RGB', (w, h), (240, 240, 240))
            draw = ImageDraw.Draw(base_rgb)
            in_arr = np.array(im.convert('L'))
            # Draw strokes in dark gray
            base_rgb.paste(Image.fromarray(in_arr).convert('RGB'), (0, 0))

        # Red tint for predicted U-Net mask
        overlay_arr = np.array(base_rgb)
        pred_mask_bool = pred_b > 0
        overlay_arr[pred_mask_bool, 0] = np.clip(overlay_arr[pred_mask_bool, 0].astype(int) + 80, 0, 255)
        overlay_arr[pred_mask_bool, 1] = np.clip(overlay_arr[pred_mask_bool, 1].astype(int) // 2, 0, 255)
        overlay_arr[pred_mask_bool, 2] = np.clip(overlay_arr[pred_mask_bool, 2].astype(int) // 2, 0, 255)

        # Green bounding outlines for gold lines
        res_pil = Image.fromarray(overlay_arr)
        draw = ImageDraw.Draw(res_pil)
        for g_idx, g in enumerate(golds):
            ys, xs = np.where(g > 0)
            if len(ys) > 0:
                y0, y1 = np.min(ys), np.max(ys)
                x0, x1 = np.min(xs), np.max(xs)
                draw.rectangle([x0, y0, x1, y1], outline='green', width=3)
                draw.text((x0 + 4, y0 + 4), f"Gold L{g_idx+1}", fill='green')

        overlay_filename = f"worst_case_{rank}_{name[:30].replace(' ', '_')}.png"
        overlay_path = OVERLAYS_DIR / overlay_filename
        res_pil.save(overlay_path)

        overlay_records.append({
            'rank': rank,
            'inscription': name,
            'gold_lines': case['gold_lines'],
            'raw_pred_cc_lines': case['cc_pred_lines'],
            'valley_pred_lines': case['valley_pred_lines'],
            'overlay_path': str(overlay_path.relative_to(ROOT))
        })
        print(f"Saved worst-case overlay {rank}: {overlay_filename}")

    # Run on 3 non-EpiSAM photographs
    non_episam_photos = [
        ROOT / 'outputs/full_binarizer/HS022_original.png',
        ROOT / 'outputs/full_binarizer/HS024_original.png',
        ROOT / 'outputs/full_binarizer/HS027_original.png'
    ]
    non_episam_masks = [
        ROOT / 'outputs/full_binarizer/HS022_mask.png',
        ROOT / 'outputs/full_binarizer/HS024_mask.png',
        ROOT / 'outputs/full_binarizer/HS027_mask.png'
    ]

    non_episam_results = []
    print("\n--- LINE U-NET ON 3 NON-EPISAM PHOTOGRAPHS ---")
    for photo_path, mask_path in zip(non_episam_photos, non_episam_masks):
        stone_id = photo_path.stem.split('_')[0]
        with Image.open(mask_path) as im:
            orig_w, orig_h = im.size
            in_pil = im.convert('L').resize((256, 256), Image.Resampling.BILINEAR)

        in_tensor = torch.from_numpy(np.array(in_pil, dtype=np.float32)[None, None] / 255.0).to(device)
        with torch.no_grad():
            pred_tensor = model(in_tensor)
            pred_upsampled = F.interpolate(pred_tensor, size=(orig_h, orig_w), mode='bilinear', align_corners=False)
            pred_orig = pred_upsampled.squeeze().cpu().numpy()

        pred_bin = (pred_orig > 0.5).astype(np.uint8)
        cc_inst = split_cc(pred_bin)
        valley_inst = split_valleys(pred_bin)

        rec = {
            'stone_id': stone_id,
            'photo_file': str(photo_path.relative_to(ROOT)),
            'mask_file': str(mask_path.relative_to(ROOT)),
            'image_dimensions': [orig_w, orig_h],
            'pred_foreground_fraction': round(float(np.mean(pred_bin)), 4),
            'predicted_line_instances_cc': len(cc_inst),
            'predicted_line_instances_valleys': len(valley_inst)
        }
        non_episam_results.append(rec)
        print(f"Stone {stone_id}: size={orig_w}x{orig_h}, CC lines={len(cc_inst)}, Valley lines={len(valley_inst)}, FG fraction={rec['pred_foreground_fraction']}")

    # Save complete benchmark report
    summary = {
        'model': 'LineUNet (line_segmentation_episam_gpu.pth)',
        'eval_dataset': 'episam/lines/val',
        'num_eval_inscriptions': len(results_cc),
        'metrics_connected_components_raw': agg_cc,
        'metrics_horizontal_valley_splitting': agg_valleys,
        'worst_cases_evaluated': overlay_records,
        'non_episam_photographs_eval': non_episam_results
    }

    report_path = OUTPUT_DIR / 'line_unet_report.json'
    # Clean per_image_audit from non-serializable fields before saving
    for p in per_image_audit:
        del p['pred_bin']
        del p['gold_masks']
        p['mask_file'] = str(p['mask_file'].relative_to(ROOT))
    summary['per_image_results'] = per_image_audit

    report_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f"\nSaved complete report to {report_path.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
