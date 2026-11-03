"""Build a source-comparison record; never alters OCR labels or evaluation data."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main():
    records = json.loads((ROOT / 'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    records = sorted((r for r in records if r['image_id'] == 'HS024'),
                     key=lambda r: (r['line_number'], r['char_number']))
    lines = []
    for number in sorted({r['line_number'] for r in records}):
        chars = [r for r in records if r['line_number'] == number]
        lines.append({'dataset_line': number, 'labels': [r['label'] for r in chars],
                      'source_keys': [r['source_key'] for r in chars]})
    scans = []
    for index, section, page in [(204, 'Roman transcription', 125),
                                  (419, 'English translation', 102),
                                  (729, 'Kannada reading', 224)]:
        path = OUT / f'EC9_leaf{index}.jpg'
        scans.append({'section': section, 'printed_page': page,
                      'url': f'https://archive.org/download/epigraphiacarnat09myso/page/n{index}.jpg',
                      'local_file': path.name,
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    page = Image.open(OUT / 'EC9_leaf729.jpg')
    page.crop((400, 225, 2500, 980)).save(OUT / 'HS024_Kannada_entry110.png')
    page.crop((435, 530, 1250, 710)).resize((1630, 360)).save(OUT / 'HS024_printed_opening.png')
    opening = [r for r in records if r['line_number'] in (1, 2)]
    boxes = [r['bbox_xyxy'] for r in opening]
    stone = Image.open(ROOT / 'outputs/full_binarizer/HS024_original.png')
    bounds = [max(0, min(b[0] for b in boxes)-12), max(0, min(b[1] for b in boxes)-12),
              min(stone.width, max(b[2] for b in boxes)+12),
              min(stone.height, max(b[3] for b in boxes)+12)]
    stone.crop(bounds).save(OUT / 'HS024_annotated_opening_region.png')
    result = {
        'image_id': 'HS024', 'source_name': records[0]['source_name'],
        'publication': 'Epigraphia Carnatica IX, Hoskote 110',
        'status': 'candidate_reference_alignment_not_expert_verified',
        'allowed_use': 'reference-assisted review only; not independent OCR ground truth',
        'source_annotation_status': 'unreviewed',
        'context_summary': 'The edition describes cattle protection and a subsequent land grant; it dates the inscription approximately 900 CE.',
        'context_origin': 'published English translation, not model-generated translation',
        'scans': scans,
        'printed_line_count': 9, 'dataset_line_count': len(lines),
        'dataset_lines': lines,
        'candidate_opening_alignment': {
            'printed_lines': [1, 2], 'dataset_lines': [1, 2],
            'status': 'phrase-level candidate, character correspondence unverified',
            'anchor': 'opening svasti / sri formula followed by royal-rule wording',
            'stone_crop_bounds_xyxy': bounds},
        'unresolved': ['Printed line numbering differs from dataset grouping.',
                       'Roman publication Nelmalla differs from dataset nĕlmalli.',
                       'Historical characters and vowel conventions need explicit review.',
                       'No missing or uncertain stone characters may be filled from context alone.'],
        'evaluation_changed': False,
    }
    (OUT / 'HS024_reference.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Saved reference comparison: {len(records)} source annotations, {len(lines)} dataset lines; no labels changed.')


if __name__ == '__main__':
    main()
