"""Check Veeragallu files and references without changing them.

Run from the project folder:
    .\.venv\Scripts\python.exe src\validate_dataset.py
A candidate with no checked transcription is NOT ready for OCR scoring.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import cv2

PROJECT = Path(__file__).resolve().parents[1]
DATASET = PROJECT / 'datasets' / 'Veeragallu'


def local_path(root, name):
    """Metadata paths must stay inside the Veeragallu folder."""
    if not name:
        return None
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path is outside the Veeragallu folder')
    return path


def inspect(root, rows):
    reports = []
    seen_ids = set()
    hashes = {}
    stone_splits = {}
    required = ['image_id', 'image_path', 'category', 'groundtruth_status', 'stone_id']
    for row in rows:
        errors, warnings = [], []
        item_id = row.get('image_id', '')
        for field in required:
            if not row.get(field, '').strip():
                errors.append('Missing field: ' + field)
        if item_id in seen_ids:
            errors.append('Duplicate image_id')
        seen_ids.add(item_id)
        if row.get('category') not in ['A', 'B', 'C', 'D']:
            errors.append('Category must be A, B, C, or D')
        image = None
        dimensions = None
        try:
            image_path = local_path(root, row.get('image_path', ''))
            if image_path and image_path.is_file():
                image = cv2.imread(str(image_path))
                if image is None:
                    errors.append('Image cannot be decoded')
                else:
                    dimensions = {'width': int(image.shape[1]), 'height': int(image.shape[0])}
                digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
                if digest in hashes:
                    warnings.append('Identical image bytes also used by ' + hashes[digest])
                hashes[digest] = item_id
            else:
                warnings.append('Image file not downloaded or missing')
        except ValueError as error:
            errors.append(str(error))
        licensed = all(row.get(f, '').strip() for f in ['image_source_url', 'image_license', 'attribution'])
        if not licensed:
            warnings.append('Image source, licence, or attribution needs verification')
        checked = row.get('groundtruth_status') in ['verified_complete', 'verified_partial']
        reference_ok = False
        gt_name = row.get('groundtruth_path', '')
        if gt_name:
            try:
                gt_path = local_path(root, gt_name)
                if not gt_path.is_file():
                    (errors if checked else warnings).append('Transcription file missing')
                else:
                    text = gt_path.read_text(encoding='utf-8-sig')
                    reference_ok = bool(text.strip()) and any('\u0c80' <= c <= '\u0cff' for c in text)
                    if not reference_ok:
                        (errors if checked else warnings).append('Reference is empty or has no Kannada characters')
            except (ValueError, UnicodeError) as error:
                errors.append('Invalid reference: ' + str(error))
        elif checked:
            errors.append('Verified status requires a transcription file')
        else:
            warnings.append('No verified Kannada ground truth yet')
        if row.get('category') == 'A' and row.get('groundtruth_status') != 'verified_complete':
            errors.append('Category A requires a complete checked reference')
        if row.get('category') == 'B' and row.get('groundtruth_status') != 'verified_partial':
            errors.append('Category B requires a checked partial reference')
        if checked:
            for f in ['text_source_url', 'page_or_entry', 'transcription_reviewer', 'review_date']:
                if not row.get(f, '').strip():
                    errors.append('Verified reference requires ' + f)
        if row.get('category') == 'B' and not row.get('evaluation_scope', '').strip():
            errors.append('Partial reference requires an evaluation_scope describing the visible crop')
        split, stone = row.get('split', ''), row.get('stone_id', '')
        if split and stone:
            stone_splits.setdefault(stone, set()).add(split)
        ready = bool(image is not None and licensed and checked and reference_ok
                     and row.get('category') in ['A', 'B'] and not errors)
        reports.append(dict(image_id=item_id, category=row.get('category'),
                            image_present=image is not None, dimensions=dimensions,
                            ready_for_scoring=ready, errors=errors, warnings=warnings))
    leakage = [stone for stone, splits in stone_splits.items() if len(splits) > 1]
    return dict(total_records=len(rows), category_counts=dict(Counter(r.get('category') for r in rows)),
                readable_images=sum(r['image_present'] for r in reports),
                ready_for_scoring=sum(r['ready_for_scoring'] for r in reports),
                split_leakage_stone_ids=leakage, items=reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, default=DATASET / 'metadata.csv')
    parser.add_argument('--require-ready', action='store_true', help='Exit with code 2 if no checked sample is ready')
    args = parser.parse_args()
    with args.metadata.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    report = inspect(args.metadata.parent, rows)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    if report['split_leakage_stone_ids'] or any(x['errors'] for x in report['items']):
        return 1
    return 2 if args.require_ready and not report['ready_for_scoring'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
