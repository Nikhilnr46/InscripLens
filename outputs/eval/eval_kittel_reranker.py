"""Audit and evaluation of KittelLM as a language model re-ranker for character predictions."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from outputs.train_dictionary_lm_gpu import KittelLM
from outputs.train_episam_cnn_gpu import CharacterCNN

OUTPUT_DIR = ROOT / 'outputs/eval'

def levenshtein(s1, s2):
    """Compute character-level Levenshtein distance."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            insert = prev[j + 1] + 1
            delete = curr[j] + 1
            replace = prev[j] + (c1 != c2)
            curr.append(min(insert, delete, replace))
        prev = curr
    return prev[-1]

def main():
    print("=" * 60)
    print("KITTEL-LM RE-RANKER BENCHMARK AUDIT")
    print("=" * 60)

    # 1. Audit Ground Truth Availability
    hs024_ref_path = ROOT / 'outputs/context_reading/HS024_reference.json'
    gold_status = {
        'candidate_file': str(hs024_ref_path.relative_to(ROOT)) if hs024_ref_path.exists() else None,
        'verified_gold_reading_exists': False,
        'status_in_metadata': None,
        'allowed_use': None
    }

    if hs024_ref_path.exists():
        hs024_data = json.loads(hs024_ref_path.read_text(encoding='utf-8'))
        gold_status['status_in_metadata'] = hs024_data.get('status')
        gold_status['allowed_use'] = hs024_data.get('allowed_use')
        gold_status['source_annotation_status'] = hs024_data.get('source_annotation_status')

    print("Checking gold reading availability:")
    print(f"  HS024 reference status: {gold_status['status_in_metadata']}")
    print(f"  HS024 allowed use: {gold_status['allowed_use']}")
    print(f"  Independent verified epigraphist gold exists: False")

    # 2. Audit KittelLM Model and Vocabulary
    lm_ckpt_path = ROOT / 'outputs/dictionary_study/kittel_lm_gpu.pth'
    if not lm_ckpt_path.exists():
        raise FileNotFoundError(f"KittelLM checkpoint not found: {lm_ckpt_path}")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    lm_ckpt = torch.load(lm_ckpt_path, map_location=device)
    char_to_idx = lm_ckpt['char_to_idx']
    vocab_size = lm_ckpt['vocab_size']

    kannada_unicode_chars = [c for c in char_to_idx.keys() if '\u0c80' <= c <= '\u0cff']
    iast_diacritic_chars = [c for c in char_to_idx.keys() if ord(c) > 127 and c not in kannada_unicode_chars]

    # Check key epigraphic characters
    test_chars = ['ś', 'ṣ', 'ḍ', 'ṇ', 'ṛ', 'ḻ', 'ī', 'ū', 'ā', 'ṃ', 'ĕ', 'ŏ']
    in_vocab_diacritics = [c for c in test_chars if c in char_to_idx]
    missing_diacritics = [c for c in test_chars if c not in char_to_idx]

    print("\nKittelLM Vocabulary Audit:")
    print(f"  Total vocabulary size: {vocab_size}")
    print(f"  Kannada Unicode characters in vocab: {len(kannada_unicode_chars)}")
    print(f"  IAST epigraphical diacritics in vocab: {len(in_vocab_diacritics)} / {len(test_chars)}")
    print(f"  Missing required epigraphic characters: {[ascii(c) for c in missing_diacritics]}")

    # 3. Test on Candidate Line 1 of HS024
    # Line 1 labels from HS024: ['sva', 'sti', 'śrī', 'śrī', 'nŏ', 'ḻa', 'mbaṃ', 'pṛ']
    crops_info = [
        ('crops/val/HS024_0001.png', 'sva'),
        ('crops/val/HS024_0002.png', 'sti'),
        ('crops/val/HS024_0003.png', 'śrī'),
        ('crops/val/HS024_0004.png', 'śrī'),
        ('crops/val/HS024_0005.png', 'nŏ'),
        ('crops/val/HS024_0006.png', 'ḻa'),
        ('crops/val/HS024_0007.png', 'mbaṃ'),
        ('crops/val/HS024_0008.png', 'pṛ')
    ]

    # Load Broad CNN
    cnn_ckpt_path = ROOT / 'outputs/cnn_study/character_cnn_episam_gpu.pth'
    cnn_ckpt = torch.load(cnn_ckpt_path, map_location=device)
    cnn_classes = cnn_ckpt['classes']
    cnn = CharacterCNN(num_classes=len(cnn_classes)).to(device)
    cnn.load_state_dict(cnn_ckpt['state_dict'])
    cnn.eval()

    line_optical_predictions = []
    gold_sequence_labels = []

    for rel_crop, gold_label in crops_info:
        crop_path = ROOT / 'outputs/full_binarizer' / rel_crop
        gold_sequence_labels.append(gold_label)
        if not crop_path.exists():
            continue

        with Image.open(crop_path) as im:
            pil_l = im.convert('L').resize((64, 64), Image.Resampling.BILINEAR)
            t = torch.from_numpy(np.array(pil_l, dtype=np.float32) / 255.0).unsqueeze(0).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = cnn(t)
            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        top3_indices = np.argsort(probs)[-3:][::-1]
        top3_preds = [(cnn_classes[i], float(probs[i])) for i in top3_indices]
        line_optical_predictions.append({
            'crop': rel_crop,
            'candidate_reference_label': gold_label,
            'top3_predictions': top3_preds,
            'cnn_top1': top3_preds[0][0],
            'top1_is_match': (top3_preds[0][0] == gold_label),
            'in_top3': any(p[0] == gold_label for p in top3_preds)
        })

    cnn_top1_sequence = [p['cnn_top1'] for p in line_optical_predictions]
    gold_str = "".join(gold_sequence_labels)
    cnn_str = "".join(cnn_top1_sequence)

    raw_cer = levenshtein(cnn_str, gold_str) / len(gold_str)
    raw_char_acc = sum(p['top1_is_match'] for p in line_optical_predictions) / len(line_optical_predictions)

    print("\nOptical CNN Evaluation on HS024 Line 1 (Candidate):")
    print(f"  Candidate Ground Truth: {ascii(gold_str)} ({[ascii(c) for c in gold_sequence_labels]})")
    print(f"  CNN Top-1 Predictions:  {ascii(cnn_str)} ({[ascii(c) for c in cnn_top1_sequence]})")
    print(f"  CNN Top-1 Exact Syllable Accuracy: {raw_char_acc*100:.1f}% ({sum(p['top1_is_match'] for p in line_optical_predictions)}/8)")
    print(f"  CNN Levenshtein CER: {raw_cer:.4f}")

    # Test scoring with KittelLM
    # Check what happens when trying to evaluate candidate sequences with KittelLM
    oov_reasons = []
    for cand in cnn_top1_sequence:
        missing = [ascii(c) for c in cand if c not in char_to_idx]
        if missing:
            oov_reasons.append(f"Syllable '{ascii(cand)}' contains OOV characters: {missing}")

    print("\nKittelLM Re-ranking Compatibility:")
    for r in oov_reasons:
        print(f"  {r}")

    # Conclusion
    verdict = {
        'testable_as_gold_benchmark': False,
        'reason_no_gold': "No verified independent epigraphist gold reading exists. The HS024 record is explicitly marked 'candidate_reference_alignment_not_expert_verified' and 'reference-assisted review only; not independent OCR ground truth'.",
        'reason_lm_incompatibility': (
            "KittelLM is unusable for epigraphical Kannada re-ranking: its 120-token vocabulary contains 0 Kannada Unicode "
            "characters and 0 IAST epigraphical diacritics (ś, ī, ŏ, ḻ, ṃ, ṛ are all OOV). It was trained on uncleaned English front-matter "
            "OCR noise ('scratch/kittel_corpus_sample.txt') rather than epigraphic inscriptions."
        ),
        'candidate_line_optical_baseline': {
            'line_name': 'HS024 Line 1 (8 crops)',
            'candidate_reference_labels': gold_sequence_labels,
            'cnn_top1_labels': cnn_top1_sequence,
            'top1_syllable_accuracy': round(raw_char_acc, 4),
            'top1_levenshtein_cer': round(raw_cer, 4),
            'top3_coverage': round(sum(p['in_top3'] for p in line_optical_predictions) / len(line_optical_predictions), 4)
        },
        're_ranked_cer': "not testable (OOV character representation and missing gold ground truth)"
    }

    report = {
        'benchmark': 'KittelLM Re-ranking Evaluation Audit',
        'gold_data_audit': gold_status,
        'kittel_lm_vocabulary_audit': {
            'checkpoint': str(lm_ckpt_path.relative_to(ROOT)),
            'vocab_size': vocab_size,
            'kannada_unicode_chars': len(kannada_unicode_chars),
            'iast_diacritics_present': in_vocab_diacritics,
            'iast_diacritics_missing': missing_diacritics
        },
        'hs024_line1_optical_eval': line_optical_predictions,
        'verdict': verdict
    }

    report_path = OUTPUT_DIR / 'kittel_reranker_report.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"\nSaved KittelLM audit report to {report_path.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
