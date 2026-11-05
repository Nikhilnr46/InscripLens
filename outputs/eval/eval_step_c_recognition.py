"""InscripLens Step C: Calibration, Ensembling, and Recognition Evaluation.
Strict evaluation: zero cloud services, zero emojis, no tuning on held-out test data.
"""
import io
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import torch
from scipy.optimize import minimize_scalar
import joblib

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'outputs'))

from run_character_benchmark import features
from train_episam_cnn_gpu import CharacterCNN as BroadCharacterCNN

def site_name(name):
    return re.split(r'\d', name, maxsplit=1)[0].strip().lower()

def softmax(x, axis=-1):
    e = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e / np.sum(e, axis=axis, keepdims=True)

def compute_ece(confidences, predictions, ground_truth, num_bins=10):
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    total = len(ground_truth)
    bin_stats = []

    for i in range(num_bins):
        low = bin_boundaries[i]
        high = bin_boundaries[i + 1]
        if i < num_bins - 1:
            mask = (confidences >= low) & (confidences < high)
        else:
            mask = (confidences >= low) & (confidences <= high)
        cnt = int(np.sum(mask))

        if cnt > 0:
            acc = float(np.mean(predictions[mask] == ground_truth[mask]))
            conf = float(np.mean(confidences[mask]))
            ece += (cnt / total) * abs(acc - conf)
            bin_stats.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "count": cnt,
                "acc": round(acc, 4),
                "conf": round(conf, 4)
            })
        else:
            bin_stats.append({
                "bin": f"[{low:.1f}, {high:.1f}]",
                "count": 0,
                "acc": 0.0,
                "conf": 0.0
            })

    return float(ece), bin_stats

def pixels_64(pil_img):
    im = ImageOps.contain(pil_img.convert('L'), (64, 64), Image.Resampling.BILINEAR)
    canvas = Image.new('L', (64, 64), 0)
    canvas.paste(im, ((64 - im.width) // 2, (64 - im.height) // 2))
    return np.array(canvas, dtype=np.float32)[None] / 255.0

def load_calibration_dataset(episam_root, devsites):
    records = []
    chars_train = sorted((episam_root / 'chars/train').iterdir())
    for p in chars_train:
        if site_name(p.name) not in devsites:
            continue
        mask_file = episam_root / 'binary_images/train' / (p.name + '.png')
        if not mask_file.exists():
            continue
        jf = p / 'character_polygons.json'
        if not jf.exists():
            continue
        data = json.loads(jf.read_text(encoding='utf-8'))
        with Image.open(mask_file) as mask:
            w, h = mask.size
            for k, v in data.items():
                if not isinstance(v, dict):
                    continue
                lbl = str(v.get('char_name', '')).strip()
                if not lbl or lbl in ('NaNl', 'None', 'nan', 'null'):
                    continue
                tl, br = v.get('top_left'), v.get('bottom_right')
                if not tl or not br or len(tl) != 2 or len(br) != 2:
                    continue
                x1 = max(0, min(tl[0], w - 2))
                y1 = max(0, min(tl[1], h - 2))
                x2 = max(x1 + 1, min(br[0], w))
                y2 = max(y1 + 1, min(br[1], h))
                crop = mask.crop((x1, y1, x2, y2))
                feat = features(crop, 'median')
                arr = pixels_64(crop)
                records.append({
                    'stone': p.name,
                    'label': lbl,
                    'feat': feat,
                    'tensor': arr
                })
    return records

def load_validation_dataset(manifest_path, binarizer_root):
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    val_records = [r for r in manifest if r.get('source_split') == 'val']
    records = []
    for r in val_records:
        crop_file = binarizer_root / r['crop_path']
        with Image.open(crop_file) as crop:
            feat = features(crop, 'median')
            arr = pixels_64(crop)
            records.append({
                'stone': r.get('image_id', 'unknown'),
                'source_name': r.get('source_name', ''),
                'label': r['label'],
                'feat': feat,
                'tensor': arr,
                'crop_path': r['crop_path']
            })
    return records

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 70)
    print("INSCRIPLENS STEP C: CALIBRATION, ENSEMBLING, AND RECOGNITION AUDIT")
    print(f"Device: {device}")
    print("=" * 70)

    # 1. Load Models
    svm_path = ROOT / 'outputs/broad_clean_study/mask_svm_bundle.joblib'
    svm_bundle = joblib.load(svm_path)
    svm_model = svm_bundle['model']
    svm_classes = list(svm_model.classes_)
    svm_c2i = {c: i for i, c in enumerate(svm_classes)}

    cnn_path = ROOT / 'outputs/cnn_study/character_cnn_episam_gpu.pth'
    ckpt = torch.load(cnn_path, map_location=device, weights_only=True)
    cnn_classes = list(ckpt['classes'])
    cnn_c2i = {c: i for i, c in enumerate(cnn_classes)}
    cnn_model = BroadCharacterCNN(len(cnn_classes)).to(device)
    cnn_model.load_state_dict(ckpt['state_dict'])
    cnn_model.eval()

    print(f"SVM classes: {len(svm_classes)}")
    print(f"CNN classes: {len(cnn_classes)}")

    # 2. Extract / Cache Datasets
    cache_file = ROOT / 'outputs/eval/step_c_features_cache.npz'
    devsites = {'aradeshanahalli', 'sadahalli', 'srinivagilu', 't dasarahalli'}

    if cache_file.exists():
        print(f"Loading cached features from {cache_file.name}...")
        data = np.load(cache_file, allow_pickle=True)
        calib_feats = data['calib_feats']
        calib_tensors = data['calib_tensors']
        calib_labels = data['calib_labels']
        calib_stones = data['calib_stones']

        val_feats = data['val_feats']
        val_tensors = data['val_tensors']
        val_labels = data['val_labels']
        val_stones = data['val_stones']
        val_paths = data['val_paths']
    else:
        print("Extracting calibration crops (devsites: 8 stones)...")
        t0 = time.perf_counter()
        calib_recs = load_calibration_dataset(
            ROOT / 'episam/episam_dataset/episam_dataset',
            devsites
        )
        print(f"Extracted {len(calib_recs)} calibration crops in {time.perf_counter() - t0:.2f}s")

        print("Extracting held-out validation crops (300 crops)...")
        t1 = time.perf_counter()
        val_recs = load_validation_dataset(
            ROOT / 'work/hero_pilot/manifest.json',
            ROOT / 'outputs/full_binarizer'
        )
        print(f"Extracted {len(val_recs)} validation crops in {time.perf_counter() - t1:.2f}s")

        calib_feats = np.stack([r['feat'] for r in calib_recs])
        calib_tensors = np.stack([r['tensor'] for r in calib_recs])
        calib_labels = np.array([r['label'] for r in calib_recs])
        calib_stones = np.array([r['stone'] for r in calib_recs])

        val_feats = np.stack([r['feat'] for r in val_recs])
        val_tensors = np.stack([r['tensor'] for r in val_recs])
        val_labels = np.array([r['label'] for r in val_recs])
        val_stones = np.array([r['stone'] for r in val_recs])
        val_paths = np.array([r['crop_path'] for r in val_recs])

        np.savez_compressed(
            cache_file,
            calib_feats=calib_feats,
            calib_tensors=calib_tensors,
            calib_labels=calib_labels,
            calib_stones=calib_stones,
            val_feats=val_feats,
            val_tensors=val_tensors,
            val_labels=val_labels,
            val_stones=val_stones,
            val_paths=val_paths
        )
        print(f"Saved feature cache to {cache_file.name}")

    print(f"Calibration crops: {len(calib_labels)} across {len(set(calib_stones))} stones")
    print(f"Validation crops: {len(val_labels)} across {len(set(val_stones))} stones")

    # 3. Model Inference on Calibration Split
    print("\nRunning model inference on calibration split...")
    calib_svm_dec = svm_model.decision_function(calib_feats)
    with torch.inference_mode():
        calib_cnn_t = torch.from_numpy(calib_tensors).to(device)
        calib_cnn_logits = cnn_model(calib_cnn_t).cpu().numpy()

    # 4. Model Inference on Held-out Validation Split
    print("Running model inference on validation split...")
    val_svm_dec = svm_model.decision_function(val_feats)
    with torch.inference_mode():
        val_cnn_t = torch.from_numpy(val_tensors).to(device)
        val_cnn_logits = cnn_model(val_cnn_t).cpu().numpy()

    # Union of classes
    union_classes = sorted(list(set(svm_classes).union(set(cnn_classes))))
    union_c2i = {c: i for i, c in enumerate(union_classes)}
    svm_indices_in_union = np.array([union_c2i[c] for c in svm_classes])
    cnn_indices_in_union = np.array([union_c2i[c] for c in cnn_classes])

    print(f"Union classes count: {len(union_classes)}")

    # 5. Fit Calibrators on Calibration Split
    print("\nFitting Calibrators on Calibration Split:")
    # A. CNN Temperature Scaling
    calib_cnn_y_idx = np.array([cnn_c2i[l] for l in calib_labels])
    def cnn_nll_obj(T):
        if T <= 0.01:
            return 1e9
        scaled = calib_cnn_logits / T
        lse = np.log(np.sum(np.exp(scaled - np.max(scaled, axis=1, keepdims=True)), axis=1)) + np.max(scaled, axis=1)
        true_l = scaled[np.arange(len(calib_cnn_y_idx)), calib_cnn_y_idx]
        return float(np.mean(lse - true_l))

    res_cnn = minimize_scalar(cnn_nll_obj, bounds=(0.05, 10.0), method='bounded')
    T_cnn = float(res_cnn.x)
    print(f"  Optimal Broad CNN Temperature T: {T_cnn:.4f} (NLL: {res_cnn.fun:.4f})")

    # B. SVM Platt Scaling (Temperature / Scale on Decision Margins)
    calib_svm_y_idx = np.array([svm_c2i[l] for l in calib_labels])
    def svm_nll_obj(T):
        if T <= 0.01:
            return 1e9
        scaled = calib_svm_dec / T
        lse = np.log(np.sum(np.exp(scaled - np.max(scaled, axis=1, keepdims=True)), axis=1)) + np.max(scaled, axis=1)
        true_l = scaled[np.arange(len(calib_svm_y_idx)), calib_svm_y_idx]
        return float(np.mean(lse - true_l))

    res_svm = minimize_scalar(svm_nll_obj, bounds=(0.05, 10.0), method='bounded')
    T_svm = float(res_svm.x)
    print(f"  Optimal SVM Temperature / Platt Scale T: {T_svm:.4f} (NLL: {res_svm.fun:.4f})")

    # Save calibration parameters
    calib_params_dir = ROOT / 'api/reading'
    calib_params_dir.mkdir(parents=True, exist_ok=True)
    calib_params_file = calib_params_dir / 'calibration_params.json'
    calib_params = {
        "svm_temperature": T_svm,
        "cnn_temperature": T_cnn,
        "calibration_stones": sorted(list(set(calib_stones.tolist()))),
        "calibration_samples": int(len(calib_labels)),
        "union_classes_count": len(union_classes)
    }
    calib_params_file.write_text(json.dumps(calib_params, indent=2), encoding='utf-8')
    print(f"Saved calibration parameters to {calib_params_file}")

    # Probability mapping function to union space
    def get_calibrated_probs(svm_dec_mat, cnn_logits_mat, t_svm, t_cnn):
        N = len(svm_dec_mat)
        K = len(union_classes)

        # SVM probs
        svm_raw_probs = softmax(svm_dec_mat / t_svm, axis=1)
        svm_union = np.zeros((N, K), dtype=np.float32)
        svm_union[:, svm_indices_in_union] = svm_raw_probs

        # CNN probs
        cnn_raw_probs = softmax(cnn_logits_mat / t_cnn, axis=1)
        cnn_union = np.zeros((N, K), dtype=np.float32)
        cnn_union[:, cnn_indices_in_union] = cnn_raw_probs

        # Ensemble
        ens_union = 0.5 * (svm_union + cnn_union)

        return svm_union, cnn_union, ens_union

    calib_svm_p, calib_cnn_p, calib_ens_p = get_calibrated_probs(
        calib_svm_dec, calib_cnn_logits, T_svm, T_cnn
    )
    val_svm_p, val_cnn_p, val_ens_p = get_calibrated_probs(
        val_svm_dec, val_cnn_logits, T_svm, T_cnn
    )

    # Also compute uncalibrated validation probabilities for baseline comparison
    val_svm_uncal_p, val_cnn_uncal_p, val_ens_uncal_p = get_calibrated_probs(
        val_svm_dec, val_cnn_logits, 1.0, 1.0
    )

    # Evaluation helper for a probability matrix over union_classes
    def evaluate_predictions(probs_mat, true_labels):
        N = len(true_labels)
        top1_idx = probs_mat.argmax(axis=1)
        top1_preds = [union_classes[i] for i in top1_idx]
        top1_confs = probs_mat.max(axis=1)

        top3_idx = np.argsort(-probs_mat, axis=1)[:, :3]
        top5_idx = np.argsort(-probs_mat, axis=1)[:, :5]

        top3_preds = [[union_classes[i] for i in row] for row in top3_idx]
        top5_preds = [[union_classes[i] for i in row] for row in top5_idx]

        top1_corr = np.array([p == t for p, t in zip(top1_preds, true_labels)])
        top3_corr = np.array([t in p for p, t in zip(top3_preds, true_labels)])
        top5_corr = np.array([t in p for p, t in zip(top5_preds, true_labels)])

        ece, bin_stats = compute_ece(top1_confs, np.array(top1_preds), true_labels)

        return {
            "top1_accuracy": float(np.mean(top1_corr)),
            "top3_accuracy": float(np.mean(top3_corr)),
            "top5_accuracy": float(np.mean(top5_corr)),
            "ece": float(ece),
            "top1_corr": top1_corr,
            "top3_corr": top3_corr,
            "top5_corr": top5_corr,
            "confs": top1_confs,
            "preds": top1_preds,
            "bin_stats": bin_stats
        }

    # Evaluate on held-out validation set
    metrics_svm_cal = evaluate_predictions(val_svm_p, val_labels)
    metrics_cnn_cal = evaluate_predictions(val_cnn_p, val_labels)
    metrics_ens_cal = evaluate_predictions(val_ens_p, val_labels)

    metrics_svm_uncal = evaluate_predictions(val_svm_uncal_p, val_labels)
    metrics_cnn_uncal = evaluate_predictions(val_cnn_uncal_p, val_labels)

    print("\n" + "=" * 70)
    print("HELD-OUT VALIDATION SET EVALUATION (300 CROPS):")
    print(f"{'Model':20s} | {'Top-1':8s} | {'Top-3':8s} | {'Top-5':8s} | {'ECE':8s}")
    print("-" * 70)
    print(f"{'SVM (Uncalibrated)':20s} | {metrics_svm_uncal['top1_accuracy']*100:6.2f}% | {metrics_svm_uncal['top3_accuracy']*100:6.2f}% | {metrics_svm_uncal['top5_accuracy']*100:6.2f}% | {metrics_svm_uncal['ece']:.4f}")
    print(f"{'SVM (Calibrated)':20s} | {metrics_svm_cal['top1_accuracy']*100:6.2f}% | {metrics_svm_cal['top3_accuracy']*100:6.2f}% | {metrics_svm_cal['top5_accuracy']*100:6.2f}% | {metrics_svm_cal['ece']:.4f}")
    print(f"{'CNN (Uncalibrated)':20s} | {metrics_cnn_uncal['top1_accuracy']*100:6.2f}% | {metrics_cnn_uncal['top3_accuracy']*100:6.2f}% | {metrics_cnn_uncal['top5_accuracy']*100:6.2f}% | {metrics_cnn_uncal['ece']:.4f}")
    print(f"{'CNN (Calibrated)':20s} | {metrics_cnn_cal['top1_accuracy']*100:6.2f}% | {metrics_cnn_cal['top3_accuracy']*100:6.2f}% | {metrics_cnn_cal['top5_accuracy']*100:6.2f}% | {metrics_cnn_cal['ece']:.4f}")
    print(f"{'Ensemble (Calibrated)':20s} | {metrics_ens_cal['top1_accuracy']*100:6.2f}% | {metrics_ens_cal['top3_accuracy']*100:6.2f}% | {metrics_ens_cal['top5_accuracy']*100:6.2f}% | {metrics_ens_cal['ece']:.4f}")
    print("=" * 70)

    # 6. Cluster Bootstrap by Stone (1,000 iterations)
    print("\nRunning Cluster Bootstrap by Stone (1,000 iterations)...")
    unique_val_stones = sorted(list(set(val_stones)))
    stone_to_indices = {s: np.where(val_stones == s)[0] for s in unique_val_stones}
    print(f"Validation stones ({len(unique_val_stones)}): {[(s, len(idx)) for s, idx in stone_to_indices.items()]}")

    np.random.seed(42)
    B = 1000
    boot_stats = {
        "svm": {"top1": [], "top3": [], "top5": [], "ece": []},
        "cnn": {"top1": [], "top3": [], "top5": [], "ece": []},
        "ens": {"top1": [], "top3": [], "top5": [], "ece": []},
        "diff_ens_vs_svm": {"top1": [], "top3": [], "top5": [], "ece": []},
        "diff_ens_vs_cnn": {"top1": [], "top3": [], "top5": [], "ece": []},
        "diff_ens_vs_best_single": {"top1": [], "top3": [], "top5": []}
    }

    best_single_name = "cnn" if metrics_cnn_cal['top1_accuracy'] >= metrics_svm_cal['top1_accuracy'] else "svm"

    for b in range(B):
        # Sample stones with replacement
        sampled_stones = np.random.choice(unique_val_stones, size=len(unique_val_stones), replace=True)
        sample_idx = np.concatenate([stone_to_indices[s] for s in sampled_stones])

        sub_true = val_labels[sample_idx]
        eval_svm_b = evaluate_predictions(val_svm_p[sample_idx], sub_true)
        eval_cnn_b = evaluate_predictions(val_cnn_p[sample_idx], sub_true)
        eval_ens_b = evaluate_predictions(val_ens_p[sample_idx], sub_true)

        for m in ["top1", "top3", "top5", "ece"]:
            v_svm = eval_svm_b[f"{m}_accuracy" if m != "ece" else "ece"]
            v_cnn = eval_cnn_b[f"{m}_accuracy" if m != "ece" else "ece"]
            v_ens = eval_ens_b[f"{m}_accuracy" if m != "ece" else "ece"]

            boot_stats["svm"][m].append(v_svm)
            boot_stats["cnn"][m].append(v_cnn)
            boot_stats["ens"][m].append(v_ens)

            boot_stats["diff_ens_vs_svm"][m].append(v_ens - v_svm)
            boot_stats["diff_ens_vs_cnn"][m].append(v_ens - v_cnn)

        best_single_val = eval_cnn_b["top1_accuracy"] if best_single_name == "cnn" else eval_svm_b["top1_accuracy"]
        boot_stats["diff_ens_vs_best_single"]["top1"].append(eval_ens_b["top1_accuracy"] - best_single_val)

    def ci95(arr):
        return float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))

    bootstrap_results = {}
    for model_key in ["svm", "cnn", "ens"]:
        bootstrap_results[model_key] = {}
        for m in ["top1", "top3", "top5", "ece"]:
            mean_v = float(np.mean(boot_stats[model_key][m]))
            low, high = ci95(boot_stats[model_key][m])
            bootstrap_results[model_key][m] = {
                "mean": round(mean_v, 4),
                "ci95_low": round(low, 4),
                "ci95_high": round(high, 4)
            }

    diff_ci_best_single = ci95(boot_stats["diff_ens_vs_best_single"]["top1"])
    ensemble_beats_best_single = diff_ci_best_single[0] > 0.0

    print("\nBOOTSTRAP 95% CONFIDENCE INTERVALS (CLUSTER RESAMPLED BY STONE):")
    for model_key, label in [("svm", "Calibrated SVM"), ("cnn", "Calibrated Broad CNN"), ("ens", "Calibrated Ensemble")]:
        r = bootstrap_results[model_key]
        print(f"  {label:24s}: Top-1: [{r['top1']['ci95_low']*100:5.2f}%, {r['top1']['ci95_high']*100:5.2f}%] | ECE: [{r['ece']['ci95_low']:.4f}, {r['ece']['ci95_high']:.4f}]")

    print(f"\nPaired Difference (Ensemble - Best Single [{best_single_name.upper()}]) Top-1 95% CI: [{diff_ci_best_single[0]*100:+.2f}%, {diff_ci_best_single[1]*100:+.2f}%]")
    print(f"Does Ensemble beat best single model beyond 95% bootstrap interval? {ensemble_beats_best_single}")

    # 7. Abstain Threshold Tuning on Calibration Split
    print("\n" + "=" * 70)
    print("TASK 3: ABSTAIN THRESHOLD TUNING & EVALUATION")
    # Evaluate abstention on calibration split for stated precision targets (e.g. 70% and 80%)
    calib_confs = calib_ens_p.max(axis=1)
    calib_preds = np.array([union_classes[i] for i in calib_ens_p.argmax(axis=1)])
    calib_corr = (calib_preds == calib_labels)

    # Sweep thresholds on calibration split
    target_precisions = [0.70, 0.75, 0.80]
    chosen_thresholds = {}

    for target in target_precisions:
        best_tau = None
        best_cov = 0.0
        best_prec = 0.0
        # Search candidate thresholds
        for tau in np.arange(0.10, 0.99, 0.01):
            mask = calib_confs >= tau
            if np.sum(mask) == 0:
                continue
            prec = float(np.mean(calib_corr[mask]))
            cov = float(np.mean(mask))
            if prec >= target:
                best_tau = float(tau)
                best_cov = cov
                best_prec = prec
                break  # Pick the minimum threshold that meets the target
        chosen_thresholds[target] = {
            "tau": best_tau,
            "calib_coverage": best_cov,
            "calib_precision": best_prec
        }
        print(f"Target Precision {target*100:.0f}% -> Selected Threshold tau = {best_tau} (Calib Cov: {best_cov*100:.2f}%, Calib Prec: {best_prec*100:.2f}%)")

    # Evaluate chosen threshold on held-out validation set
    val_confs = val_ens_p.max(axis=1)
    val_preds = np.array([union_classes[i] for i in val_ens_p.argmax(axis=1)])
    val_corr = (val_preds == val_labels)

    abstain_eval_results = {}
    for target, info in chosen_thresholds.items():
        tau = info["tau"]
        if tau is None:
            continue
        mask = val_confs >= tau
        retained_cnt = int(np.sum(mask))
        abstained_cnt = len(val_labels) - retained_cnt
        val_cov = float(retained_cnt / len(val_labels))
        val_prec = float(np.mean(val_corr[mask])) if retained_cnt > 0 else 0.0

        abstain_eval_results[str(target)] = {
            "target_precision": target,
            "threshold_tau": tau,
            "calibration_split": {
                "coverage": round(info["calib_coverage"], 4),
                "precision": round(info["calib_precision"], 4)
            },
            "held_out_validation": {
                "total_crops": len(val_labels),
                "retained_crops": retained_cnt,
                "abstained_crops": abstained_cnt,
                "coverage": round(val_cov, 4),
                "precision": round(val_prec, 4)
            }
        }
        print(f"Held-out Test of tau={tau} (Target {target*100:.0f}%):")
        print(f"  Retained: {retained_cnt}/{len(val_labels)} ({val_cov*100:.2f}%) | Precision: {val_prec*100:.2f}% | Abstained: {abstained_cnt}")

    # Primary chosen abstain threshold for API deployment: target 75% or 70%
    primary_target = 0.75 if "0.75" in abstain_eval_results else 0.70
    primary_tau = abstain_eval_results[str(primary_target)]["threshold_tau"]

    # 8. Compile Master Report
    master_report = {
        "calibration": {
            "calibration_stones_count": len(set(calib_stones)),
            "calibration_crops_count": len(calib_labels),
            "svm_calibrated_temperature": round(T_svm, 4),
            "cnn_calibrated_temperature": round(T_cnn, 4),
            "svm_ece_uncalibrated": round(metrics_svm_uncal['ece'], 4),
            "svm_ece_calibrated": round(metrics_svm_cal['ece'], 4),
            "cnn_ece_uncalibrated": round(metrics_cnn_uncal['ece'], 4),
            "cnn_ece_calibrated": round(metrics_cnn_cal['ece'], 4),
            "ensemble_ece_calibrated": round(metrics_ens_cal['ece'], 4)
        },
        "held_out_validation_metrics": {
            "svm_calibrated": {
                "top1_accuracy": round(metrics_svm_cal['top1_accuracy'], 4),
                "top3_accuracy": round(metrics_svm_cal['top3_accuracy'], 4),
                "top5_accuracy": round(metrics_svm_cal['top5_accuracy'], 4),
                "ece": round(metrics_svm_cal['ece'], 4),
                "bootstrap_ci95": bootstrap_results["svm"]
            },
            "cnn_calibrated": {
                "top1_accuracy": round(metrics_cnn_cal['top1_accuracy'], 4),
                "top3_accuracy": round(metrics_cnn_cal['top3_accuracy'], 4),
                "top5_accuracy": round(metrics_cnn_cal['top5_accuracy'], 4),
                "ece": round(metrics_cnn_cal['ece'], 4),
                "bootstrap_ci95": bootstrap_results["cnn"]
            },
            "ensemble_calibrated": {
                "top1_accuracy": round(metrics_ens_cal['top1_accuracy'], 4),
                "top3_accuracy": round(metrics_ens_cal['top3_accuracy'], 4),
                "top5_accuracy": round(metrics_ens_cal['top5_accuracy'], 4),
                "ece": round(metrics_ens_cal['ece'], 4),
                "bootstrap_ci95": bootstrap_results["ens"]
            }
        },
        "significance_test": {
            "best_single_model": best_single_name,
            "paired_diff_top1_ci95": [round(diff_ci_best_single[0], 4), round(diff_ci_best_single[1], 4)],
            "ensemble_beats_best_single_beyond_ci": ensemble_beats_best_single,
            "wiring_decision": "ensemble" if ensemble_beats_best_single else f"better_calibrated_single_{best_single_name}"
        },
        "abstain_rules": abstain_eval_results,
        "selected_production_threshold": {
            "target_precision": primary_target,
            "threshold_tau": primary_tau
        }
    }

    report_path = ROOT / 'outputs/eval/recognition_step_c_report.json'
    report_path.write_text(json.dumps(master_report, indent=2), encoding='utf-8')
    print(f"\nSaved comprehensive benchmark report to {report_path}")

if __name__ == '__main__':
    main()

