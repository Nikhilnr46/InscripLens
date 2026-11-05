"""Comprehensive evaluation of SVM bundle, Broad CNN, and Hero CNN on common held-out validation crops."""
import json
import collections
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn
import joblib

ROOT = Path(__file__).resolve().parent.parent.parent

# Import feature extractor for SVM
import sys
sys.path.insert(0, str(ROOT / 'outputs'))
from run_character_benchmark import features

# Model definitions
from train_character_cnn_gpu import CharacterCNN as HeroCharacterCNN
from train_episam_cnn_gpu import CharacterCNN as BroadCharacterCNN

def pixels_64(path):
    with Image.open(path) as im:
        im = ImageOps.contain(im.convert('L'), (64, 64), Image.Resampling.BILINEAR)
        canvas = Image.new('L', (64, 64), 0)
        canvas.paste(im, ((64 - im.width) // 2, (64 - im.height) // 2))
        return np.array(canvas, dtype=np.float32)[None] / 255.0

def softmax(x, axis=-1):
    e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e_x / np.sum(e_x, axis=axis, keepdims=True)

def compute_ece(confidences, predictions, ground_truth, num_bins=10):
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    total_samples = len(ground_truth)
    bin_stats = []

    for i in range(num_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        mask = (confidences >= bin_lower) & (confidences < bin_upper) if i < num_bins - 1 else (confidences >= bin_lower) & (confidences <= bin_upper)
        bin_count = np.sum(mask)

        if bin_count > 0:
            bin_acc = np.mean(predictions[mask] == ground_truth[mask])
            bin_conf = np.mean(confidences[mask])
            ece += (bin_count / total_samples) * np.abs(bin_acc - bin_conf)
            bin_stats.append({
                "bin": f"[{bin_lower:.1f}, {bin_upper:.1f}]",
                "count": int(bin_count),
                "acc": round(float(bin_acc), 4),
                "conf": round(float(bin_conf), 4)
            })
        else:
            bin_stats.append({
                "bin": f"[{bin_lower:.1f}, {bin_upper:.1f}]",
                "count": 0,
                "acc": 0.0,
                "conf": 0.0
            })

    return float(ece), bin_stats

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print("=" * 70)
    print("TASK 3: CHARACTER RECOGNITION BENCHMARK EVALUATION")
    print(f"Device: {device}")
    print("=" * 70)

    # 1. Load Validation Crops
    manifest = json.loads((ROOT / 'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    val_records = [r for r in manifest if r.get('source_split') == 'val']
    print(f"Total Validation Crops in Manifest: {len(val_records)}")

    # 2. Load Models
    # A. SVM Bundle (Broad clean)
    svm_path = ROOT / 'outputs/broad_clean_study/mask_svm_bundle.joblib'
    if not svm_path.exists():
        svm_path = ROOT / 'outputs/matched_mask_study/mask_svm_bundle.joblib'
    svm_bundle = joblib.load(svm_path)
    svm_model = svm_bundle['model']
    svm_classes = list(svm_model.classes_)
    print(f"Loaded SVM Model: {len(svm_classes)} classes ({svm_path.name})")

    # B. Hero CNN
    hero_cnn_path = ROOT / 'outputs/cnn_study/character_cnn_gpu.pth'
    ckpt_hero = torch.load(hero_cnn_path, map_location=device, weights_only=True)
    hero_classes = ckpt_hero['classes']
    hero_model = HeroCharacterCNN(len(hero_classes)).to(device)
    hero_model.load_state_dict(ckpt_hero['state_dict'])
    hero_model.eval()
    print(f"Loaded Hero CNN: {len(hero_classes)} classes")

    # C. Broad CNN
    broad_cnn_path = ROOT / 'outputs/cnn_study/character_cnn_episam_gpu.pth'
    ckpt_broad = torch.load(broad_cnn_path, map_location=device, weights_only=True)
    broad_classes = ckpt_broad['classes']
    broad_model = BroadCharacterCNN(len(broad_classes)).to(device)
    broad_model.load_state_dict(ckpt_broad['state_dict'])
    broad_model.eval()
    print(f"Loaded Broad CNN: {len(broad_classes)} classes")

    # Class Overlap Analysis
    set_svm = set(svm_classes)
    set_hero = set(hero_classes)
    set_broad = set(broad_classes)

    shared_classes = sorted(list(set_svm.intersection(set_hero).intersection(set_broad)))
    print("-" * 70)
    print("LABEL OVERLAP ANALYSIS:")
    print(f"  SVM classes   : {len(set_svm)}")
    print(f"  Broad CNN     : {len(set_broad)}")
    print(f"  Hero CNN      : {len(set_hero)}")
    print(f"  Shared intersection across all 3: {len(shared_classes)} classes")
    shared_set = set(shared_classes)

    # Class frequencies in training data (for frequency buckets)
    # Using hero training set frequencies
    hero_train_records = [r for r in manifest if r.get('source_split') == 'train']
    train_counts = collections.Counter(r['label'] for r in hero_train_records)

    # Filter validation set to common intersection set
    val_shared_records = [r for r in val_records if r['label'] in shared_set]
    print(f"Validation crops whose label is in shared intersection: {len(val_shared_records)} / {len(val_records)}")

    # Extract features and images for validation set
    print("Extracting features and 64x64 tensors for evaluation crops...", flush=True)
    y_true_all = []
    hog_feats_all = []
    cnn_tensors_all = []

    for r in val_records:
        crop_file = ROOT / 'outputs/full_binarizer' / r['crop_path']
        y_true_all.append(r['label'])
        with Image.open(crop_file) as im:
            hog_feats_all.append(features(im, 'median'))
        cnn_tensors_all.append(pixels_64(crop_file))

    y_true_np = np.array(y_true_all)
    hog_feats_np = np.stack(hog_feats_all)
    cnn_tensors_torch = torch.from_numpy(np.stack(cnn_tensors_all)).to(device)

    # Run inference for all models
    print("Running model inferences...", flush=True)
    # 1. SVM inference
    svm_decisions = svm_model.decision_function(hog_feats_np)
    svm_probs = softmax(svm_decisions, axis=1)

    # 2. Hero CNN inference
    with torch.inference_mode():
        hero_logits = hero_model(cnn_tensors_torch).cpu().numpy()
        hero_probs = softmax(hero_logits, axis=1)

    # 3. Broad CNN inference
    with torch.inference_mode():
        broad_logits = broad_model(cnn_tensors_torch).cpu().numpy()
        broad_probs = softmax(broad_logits, axis=1)

    # Evaluation function
    def evaluate_model_performance(name, probs, model_classes, subset_indices=None):
        if subset_indices is not None:
            sub_probs = probs[subset_indices]
            sub_true = y_true_np[subset_indices]
        else:
            sub_probs = probs
            sub_true = y_true_np

        N = len(sub_true)
        # Predictions
        top1_idx = sub_probs.argmax(axis=1)
        top1_preds = [model_classes[i] for i in top1_idx]
        top1_confs = sub_probs.max(axis=1)

        # Top-3 and Top-5
        top3_idx = np.argsort(-sub_probs, axis=1)[:, :3]
        top5_idx = np.argsort(-sub_probs, axis=1)[:, :5]

        top3_preds = [[model_classes[i] for i in row] for row in top3_idx]
        top5_preds = [[model_classes[i] for i in row] for row in top5_idx]

        top1_matches = [t == p for t, p in zip(sub_true, top1_preds)]
        top3_matches = [t in p for t, p in zip(sub_true, top3_preds)]
        top5_matches = [t in p for t, p in zip(sub_true, top5_preds)]

        top1_acc = sum(top1_matches) / N
        top3_acc = sum(top3_matches) / N
        top5_acc = sum(top5_matches) / N

        # Accuracy by training frequency bucket
        # Rare: count <= 5, Medium: 6 to 20, Common: > 20
        bucket_stats = collections.defaultdict(lambda: {"correct": 0, "total": 0})
        for t, m in zip(sub_true, top1_matches):
            cnt = train_counts.get(t, 0)
            if cnt <= 5:
                b = "Rare (1-5 samples)"
            elif cnt <= 20:
                b = "Medium (6-20 samples)"
            else:
                b = "Common (>20 samples)"
            bucket_stats[b]["total"] += 1
            if m:
                bucket_stats[b]["correct"] += 1

        bucket_report = {}
        for b, s in bucket_stats.items():
            acc = s["correct"] / s["total"] if s["total"] > 0 else 0.0
            bucket_report[b] = {
                "correct": s["correct"],
                "total": s["total"],
                "accuracy": round(acc, 4)
            }

        # 20 most confused pairs
        confusion_counts = collections.Counter()
        for t, p in zip(sub_true, top1_preds):
            if t != p:
                confusion_counts[(t, p)] += 1

        top_20_confused = [
            {"true_label": pair[0], "predicted_label": pair[1], "count": count}
            for pair, count in confusion_counts.most_common(20)
        ]

        # Calibration Error (ECE)
        ece, bin_details = compute_ece(top1_confs, np.array(top1_preds), sub_true)

        return {
            "model_name": name,
            "samples_evaluated": N,
            "top1_correct": sum(top1_matches),
            "top1_accuracy": round(top1_acc, 4),
            "top3_correct": sum(top3_matches),
            "top3_accuracy": round(top3_acc, 4),
            "top5_correct": sum(top5_matches),
            "top5_accuracy": round(top5_acc, 4),
            "expected_calibration_error": round(ece, 4),
            "frequency_buckets": bucket_report,
            "top_20_confused_pairs": top_20_confused,
            "calibration_bins": bin_details
        }

    # Evaluate on Common Intersection Subset (271 crops)
    inter_indices = np.array([i for i, r in enumerate(val_records) if r['label'] in shared_set])

    # To strictly evaluate on the shared set, we restrict each model's output distribution to shared_classes
    def restrict_probs(probs, model_classes):
        class_to_col = {c: i for i, c in enumerate(model_classes)}
        cols = [class_to_col[c] for c in shared_classes]
        sub_p = probs[:, cols]
        return sub_p / np.sum(sub_p, axis=1, keepdims=True)

    svm_probs_inter = restrict_probs(svm_probs, svm_classes)
    hero_probs_inter = restrict_probs(hero_probs, hero_classes)
    broad_probs_inter = restrict_probs(broad_probs, broad_classes)

    results_inter = {
        "evaluation_subset": "Shared Intersection Subset",
        "total_crops": len(inter_indices),
        "classes_evaluated": len(shared_classes),
        "svm_bundle": evaluate_model_performance("SVM Bundle (Mask)", svm_probs_inter, shared_classes, inter_indices),
        "hero_cnn": evaluate_model_performance("Hero CNN (GPU)", hero_probs_inter, shared_classes, inter_indices),
        "broad_cnn": evaluate_model_performance("Broad EpiSAM CNN (GPU)", broad_probs_inter, shared_classes, inter_indices)
    }

    # Also evaluate on Full Validation Set (300 crops, unconstrained)
    results_full = {
        "evaluation_subset": "Full Validation Set (Unconstrained)",
        "total_crops": len(val_records),
        "svm_bundle": evaluate_model_performance("SVM Bundle (Broad Mask)", svm_probs, svm_classes),
        "hero_cnn": evaluate_model_performance("Hero CNN", hero_probs, hero_classes),
        "broad_cnn": evaluate_model_performance("Broad EpiSAM CNN", broad_probs, broad_classes)
    }

    full_report = {
        "shared_intersection_eval": results_inter,
        "full_validation_eval": results_full
    }

    out_file = ROOT / 'outputs/eval/character_benchmark_report.json'
    out_file.write_text(json.dumps(full_report, indent=2), encoding='utf-8')
    print(f"Report successfully saved to {out_file}")

    print("=" * 70)
    print("BENCHMARK RESULTS ON SHARED INTERSECTION (271 crops, 281 classes):")
    print("=" * 70)
    for k in ["svm_bundle", "hero_cnn", "broad_cnn"]:
        res = results_inter[k]
        print(f"Model: {res['model_name']}")
        print(f"  Top-1 Accuracy : {res['top1_correct']}/{res['samples_evaluated']} ({res['top1_accuracy']*100:.2f}%)")
        print(f"  Top-3 Accuracy : {res['top3_correct']}/{res['samples_evaluated']} ({res['top3_accuracy']*100:.2f}%)")
        print(f"  Top-5 Accuracy : {res['top5_correct']}/{res['samples_evaluated']} ({res['top5_accuracy']*100:.2f}%)")
        print(f"  Calibration ECE: {res['expected_calibration_error']:.4f}")
        print("  Frequency Buckets:")
        for b, s in res['frequency_buckets'].items():
            print(f"    {b:<24}: {s['correct']}/{s['total']} ({s['accuracy']*100:.1f}%)")
        conf_ascii = [(f"{p['true_label']}->{p['predicted_label']}".encode('ascii', 'replace').decode('ascii'), p['count']) for p in res['top_20_confused_pairs'][:5]]
        print("  Top 5 Confusions:", conf_ascii)
        print("-" * 70)

    print("=" * 70)
    print("BENCHMARK RESULTS ON FULL VALIDATION SET (300 crops, unconstrained):")
    print("=" * 70)
    for k in ["svm_bundle", "hero_cnn", "broad_cnn"]:
        res = results_full[k]
        print(f"Model: {res['model_name']}")
        print(f"  Top-1 Accuracy : {res['top1_correct']}/{res['samples_evaluated']} ({res['top1_accuracy']*100:.2f}%)")
        print(f"  Top-3 Accuracy : {res['top3_correct']}/{res['samples_evaluated']} ({res['top3_accuracy']*100:.2f}%)")
        print(f"  Top-5 Accuracy : {res['top5_correct']}/{res['samples_evaluated']} ({res['top5_accuracy']*100:.2f}%)")
        print(f"  Calibration ECE: {res['expected_calibration_error']:.4f}")
        print("-" * 70)

if __name__ == '__main__':
    main()
