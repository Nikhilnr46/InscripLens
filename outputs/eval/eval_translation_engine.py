"""Benchmark evaluation script for the translation engine strictly on the held-out TEST set.
Lists every token and formula mismatch individually rather than returning only a percentage.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from outputs.translation_core import analyze_inscription_text, RULES_DATA

def main():
    template_path = ROOT / 'gold_translation_template.json'
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    data = json.loads(template_path.read_text(encoding='utf-8'))
    all_entries = data.get('entries', [])
    test_entries = [e for e in all_entries if e.get('split') == 'test']

    print("=" * 60)
    print("HELD-OUT TEST SET EVALUATION REPORT")
    print(f"Total entries in gold template: {len(all_entries)}")
    print(f"Dev split entries (excluded):   {len(all_entries) - len(test_entries)}")
    print(f"Test split entries (evaluated): {len(test_entries)}")
    print("=" * 60)

    total_test_tokens = 0
    token_mismatches = []
    formula_mismatches = []
    detailed_test_results = []

    for idx, entry in enumerate(test_entries, 1):
        test_text = entry.get('dataset_normalized_passage') or entry.get('published_roman_transcription')
        published_eng = entry.get('published_english_translation', '')
        
        analysis = analyze_inscription_text(test_text, reviewer_verified=True)
        tokens = analysis['token_analysis']
        total_test_tokens += len(tokens)

        # Token-level mismatch check
        for t_idx, t in enumerate(tokens):
            if t.get('status') != 'matched':
                token_mismatches.append({
                    'entry_id': entry['id'],
                    'token_position': t_idx + 1,
                    'input_token': t['original'],
                    'engine_modern': t['modern'],
                    'status': t['status'],
                    'reason': 'No documented rule matched; passed through untranslated'
                })

        # Formula / Translation mismatch check
        engine_eng = analysis['english_translation'].strip()
        pub_eng_clean = published_eng.strip()
        is_formula_match = (engine_eng.lower() == pub_eng_clean.lower())
        
        if not is_formula_match:
            formula_mismatches.append({
                'entry_id': entry['id'],
                'input_passage': test_text,
                'published_expected': pub_eng_clean,
                'engine_draft': engine_eng,
                'detected_formulas': [f['formula_key'] for f in analysis.get('detected_formulas', [])]
            })

        detailed_test_results.append({
            'entry_id': entry['id'],
            'stone_id': entry.get('stone_id'),
            'token_count': len(tokens),
            'input_text': test_text,
            'published_english': pub_eng_clean,
            'engine_draft': engine_eng,
            'token_mismatch_count': sum(1 for t in tokens if t.get('status') != 'matched'),
            'tokens': tokens
        })

    report = {
        'evaluation_split': 'test',
        'total_test_entries': len(test_entries),
        'total_test_tokens': total_test_tokens,
        'token_mismatch_count': len(token_mismatches),
        'formula_mismatch_count': len(formula_mismatches),
        'token_mismatches': token_mismatches,
        'formula_mismatches': formula_mismatches,
        'entries_detail': detailed_test_results
    }

    report_path = ROOT / 'outputs/eval/translation_test_eval_report.json'
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f"\nTotal Test Tokens Evaluated: {total_test_tokens}")
    print(f"Total Token Mismatches:      {len(token_mismatches)}")
    print(f"Total Formula Mismatches:    {len(formula_mismatches)}")
    print(f"\nSaved held-out test evaluation report to {report_path.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
