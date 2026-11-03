"""Audit candidate sequence supervision without reading validation annotations."""
import collections
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def blocked(name, sites):
    location = re.split(r'\d', name, maxsplit=1)[0].strip().lower()
    return any(location == s or location.startswith(s + ' ') for s in sites)


def main():
    protocol = json.loads((ROOT/'outputs/matched_mask_study/summary.json').read_text())
    out = ROOT/'outputs/sequence_data_audit'
    out.mkdir(exist_ok=True)
    totals = collections.Counter()
    issues = collections.Counter()
    candidates = []
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as archive:
        for path in sorted(archive.namelist()):
            if not path.startswith('episam_dataset/chars/train/') or not path.endswith('/character_polygons.json'):
                continue
            name = path.split('/')[3]
            if blocked(name, protocol['excluded_validation_sites']):
                continue
            split = 'development' if blocked(name, protocol['development_sites']) else 'fit'
            totals[split+'_images'] += 1
            chars = json.loads(archive.read(path))
            groups = collections.defaultdict(list)
            for key, char in chars.items():
                groups[char['line_number']].append((key, char))
            line_path = f'episam_dataset/lines/train/{name}/line_polygons.json'
            polygons = json.loads(archive.read(line_path))['line_polygons'] if line_path in archive.namelist() else {}
            for line, members in sorted(groups.items(), key=lambda kv: str(kv[0])):
                members.sort(key=lambda kv: kv[1]['char_number'] if isinstance(kv[1]['char_number'], int) else -1)
                numbers = [c['char_number'] for _, c in members]
                labels = [c['char_name'] for _, c in members]
                reasons = []
                if len(set(numbers)) != len(numbers): reasons.append('duplicate_position')
                if line is None or any(not isinstance(n, int) for n in numbers):
                    reasons.append('missing_line_or_character_number')
                elif numbers != list(range(1, max(numbers)+1)): reasons.append('missing_positions_or_non_one_start')
                if any(not isinstance(s, str) or not s.strip() or '?' in s or '[' in s or ']' in s for s in labels): reasons.append('empty_or_uncertainty_marker')
                if str(line) not in polygons: reasons.append('missing_line_polygon')
                centers = [(c['top_left'][0]+c['bottom_right'][0])/2 for _, c in members]
                if any(a>b for a,b in zip(centers, centers[1:])): reasons.append('horizontal_order_reversal')
                totals[split+'_lines'] += 1
                totals[split+'_annotations'] += len(members)
                for reason in reasons: issues[split+'_'+reason] += 1
                if not reasons: totals[split+'_structural_candidates'] += 1
                candidates.append({'source_name': name, 'split': split, 'line_number': line,
                                   'labels': labels, 'source_keys': [k for k,_ in members],
                                   'flags': reasons, 'status': 'unreviewed_source_sequence',
                                   'line_polygon': polygons.get(str(line))})
    fit_labels = [s for row in candidates if row['split']=='fit' and not row['flags'] for s in row['labels']]
    dev_labels = [s for row in candidates if row['split']=='development' and not row['flags'] for s in row['labels']]
    fit_alphabet = set(''.join(fit_labels))
    summary = {'counts': dict(totals), 'flag_counts': dict(issues),
               'candidate_fit_label_types': len(set(fit_labels)),
               'candidate_fit_unicode_codepoints': len(fit_alphabet),
               'candidate_development_unseen_codepoints': sorted(set(''.join(dev_labels))-fit_alphabet),
               'validation_annotations_read': False,
               'warning': 'Structural candidates are not verified complete transcriptions. Missing unannotated glyphs and unknown token conventions require inspection.',
               'excluded_validation_sites': protocol['excluded_validation_sites'],
               'development_sites': protocol['development_sites']}
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    (out/'records.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
