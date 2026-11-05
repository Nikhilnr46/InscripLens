"""Comprehensive pixel-level benchmark of CPU, GPU single-scale, and GPU multi-scale binarization against gold ground truth."""
import sys
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from outputs.binarizer_core import load_model, enhance, enhance_multiscale

OUTPUT_DIR = ROOT / 'outputs/eval'

def compute_pixel_metrics(pred_bin, gold_bin):
    """Compute standard DIBCO pixel-level binarization metrics."""
    p = pred_bin > 0
    g = gold_bin > 0
    
    tp = np.sum(p & g)
    fp = np.sum(p & (~g))
    fn = np.sum((~p) & g)
    tn = np.sum((~p) & (~g))
    
    # Foreground IoU
    union = tp + fp + fn
    iou = float(tp / union) if union > 0 else 0.0
    
    # Foreground F-measure / Dice
    denom = 2 * tp + fp + fn
    f_measure = float(2 * tp / denom) if denom > 0 else 0.0
    
    # Precision & Recall
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    
    # Overall Pixel Accuracy
    total = p.size
    accuracy = float((tp + tn) / total)
    
    # PSNR
    mse = float(np.mean((p.astype(float) - g.astype(float)) ** 2))
    psnr = float(10.0 * np.log10(1.0 / (mse + 1e-12))) if mse > 0 else 100.0
    
    return {
        'iou': round(iou, 4),
        'f_measure': round(f_measure, 4),
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'pixel_accuracy': round(accuracy, 4),
        'psnr_db': round(psnr, 2)
    }

def main():
    print("=" * 60)
    print("BINARIZER PIXEL-LEVEL BENCHMARK AUDIT")
    print("=" * 60)

    val_img_dir = ROOT / 'episam/episam_dataset/episam_dataset/images/val'
    val_gold_dir = ROOT / 'episam/episam_dataset/episam_dataset/binary_images/val'

    img_files = sorted(list(val_img_dir.glob('*.png')))
    print(f"Found {len(img_files)} validation images with gold binarization.")

    # Select representative 10-image subset for full CPU vs GPU comparison
    # (CPU single-scale takes ~13-25s per image)
    eval_subset = img_files[:10]
    print(f"Benchmarking 3-way CPU vs GPU Single vs GPU Multi on {len(eval_subset)} validation images...")

    print("Loading models...")
    model_cuda = load_model('cuda')
    model_cpu = load_model('cpu')

    three_way_records = []

    for idx, img_path in enumerate(eval_subset, 1):
        gold_path = val_gold_dir / img_path.name
        if not gold_path.exists():
            continue

        with Image.open(img_path) as im:
            w, h = im.size
            mp = (w * h) / 1e6

            with Image.open(gold_path) as gim:
                gold_arr = (np.array(gim.convert('L')) > 128).astype(np.uint8)

            print(f"[{idx:2d}/{len(eval_subset)}] Processing {img_path.stem[:30]} ({w}x{h}, {mp:.2f} MP)...", flush=True)

            # 1. GPU Single-Scale
            t0 = time.perf_counter()
            pred_gpu = enhance(im, model_cuda)
            t_gpu = time.perf_counter() - t0
            arr_gpu = (np.array(pred_gpu.convert('L')) > 128).astype(np.uint8)
            metrics_gpu = compute_pixel_metrics(arr_gpu, gold_arr)

            # 2. GPU Multi-Scale
            t0 = time.perf_counter()
            pred_multi = enhance_multiscale(im, model_cuda)
            t_multi = time.perf_counter() - t0
            arr_multi = (np.array(pred_multi.convert('L')) > 128).astype(np.uint8)
            metrics_multi = compute_pixel_metrics(arr_multi, gold_arr)

            # 3. CPU Single-Scale
            t0 = time.perf_counter()
            pred_cpu = enhance(im, model_cpu)
            t_cpu = time.perf_counter() - t0
            arr_cpu = (np.array(pred_cpu.convert('L')) > 128).astype(np.uint8)
            metrics_cpu = compute_pixel_metrics(arr_cpu, gold_arr)

            three_way_records.append({
                'name': img_path.name,
                'width': w,
                'height': h,
                'megapixels': round(mp, 3),
                'cpu_single': {
                    'seconds': round(t_cpu, 3),
                    'seconds_per_mp': round(t_cpu / mp, 3),
                    **metrics_cpu
                },
                'gpu_single': {
                    'seconds': round(t_gpu, 3),
                    'seconds_per_mp': round(t_gpu / mp, 3),
                    **metrics_gpu
                },
                'gpu_multi': {
                    'seconds': round(t_multi, 3),
                    'seconds_per_mp': round(t_multi / mp, 3),
                    **metrics_multi
                }
            })

    # Also evaluate GPU Single vs GPU Multi across all 31 validation images
    print(f"\nEvaluating GPU Single vs Multi on all {len(img_files)} validation images...", flush=True)
    all_gpu_records = []
    for idx, img_path in enumerate(img_files, 1):
        gold_path = val_gold_dir / img_path.name
        if not gold_path.exists():
            continue
        with Image.open(img_path) as im:
            w, h = im.size
            mp = (w * h) / 1e6
            with Image.open(gold_path) as gim:
                gold_arr = (np.array(gim.convert('L')) > 128).astype(np.uint8)

            t0 = time.perf_counter()
            pred_gpu = enhance(im, model_cuda)
            t_gpu = time.perf_counter() - t0
            metrics_gpu = compute_pixel_metrics((np.array(pred_gpu.convert('L')) > 128).astype(np.uint8), gold_arr)

            t0 = time.perf_counter()
            pred_multi = enhance_multiscale(im, model_cuda)
            t_multi = time.perf_counter() - t0
            metrics_multi = compute_pixel_metrics((np.array(pred_multi.convert('L')) > 128).astype(np.uint8), gold_arr)

            all_gpu_records.append({
                'name': img_path.name,
                'megapixels': round(mp, 3),
                'gpu_single': {'seconds': round(t_gpu, 3), **metrics_gpu},
                'gpu_multi': {'seconds': round(t_multi, 3), **metrics_multi}
            })

    def summarize(rec_key, records):
        ious = [r[rec_key]['iou'] for r in records]
        fms = [r[rec_key]['f_measure'] for r in records]
        precs = [r[rec_key]['precision'] for r in records]
        recs = [r[rec_key]['recall'] for r in records]
        psnrs = [r[rec_key]['psnr_db'] for r in records]
        accs = [r[rec_key]['pixel_accuracy'] for r in records]
        secs = [r[rec_key]['seconds'] for r in records]
        sec_mp = [r[rec_key].get('seconds_per_mp', r[rec_key]['seconds'] / r['megapixels']) for r in records]
        return {
            'mean_iou': round(float(np.mean(ious)), 4),
            'mean_f_measure': round(float(np.mean(fms)), 4),
            'mean_precision': round(float(np.mean(precs)), 4),
            'mean_recall': round(float(np.mean(recs)), 4),
            'mean_pixel_accuracy': round(float(np.mean(accs)), 4),
            'mean_psnr_db': round(float(np.mean(psnrs)), 2),
            'mean_runtime_seconds': round(float(np.mean(secs)), 3),
            'mean_seconds_per_megapixel': round(float(np.mean(sec_mp)), 3)
        }

    summary_3way = {
        'num_eval_images': len(three_way_records),
        'cpu_single_scale': summarize('cpu_single', three_way_records),
        'gpu_single_scale': summarize('gpu_single', three_way_records),
        'gpu_multi_scale': summarize('gpu_multi', three_way_records)
    }

    summary_all_31 = {
        'num_eval_images': len(all_gpu_records),
        'gpu_single_scale': summarize('gpu_single', all_gpu_records),
        'gpu_multi_scale': summarize('gpu_multi', all_gpu_records)
    }

    print("\n" + "=" * 60)
    print("3-WAY COMPARISON SUMMARY (10 validation images):")
    print(json.dumps(summary_3way, indent=2))
    print("\nALL 31 VALIDATION IMAGES SUMMARY (GPU Single vs Multi):")
    print(json.dumps(summary_all_31, indent=2))
    print("=" * 60)

    report = {
        'benchmark': 'InscripLens Attributed Shilalekhya Binarizer Benchmark',
        'checkpoint': 'work/shilalekhya/binarizer.pth (Jena et al., ICVGIP 2025)',
        'evaluation_mode': 'Pixel-level segmentation against gold binary ground truth',
        'ten_image_three_way_summary': summary_3way,
        'all_31_images_gpu_summary': summary_all_31,
        'detailed_per_image_10_way': three_way_records,
        'detailed_per_image_31_gpu': all_gpu_records
    }

    out_file = OUTPUT_DIR / 'binarizer_benchmark_report.json'
    out_file.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Saved benchmark report to {out_file.relative_to(ROOT)}")

if __name__ == '__main__':
    main()

