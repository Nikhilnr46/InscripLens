"""Reproduce diagnostics and an offline visual report; does not train or alter labels."""
import argparse
import base64
import collections
import html
import io
import json
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def run(hero, results, out):
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((hero / 'manifest.json').read_text(encoding='utf-8'))
    lookup = {r['crop_path']: r for r in manifest}
    training = json.loads((results / 'training_records.json').read_text(encoding='utf-8'))
    predictions = json.loads((results / 'predictions.json').read_text(encoding='utf-8'))
    rows = [r for r in predictions if r['model'] == 'broader_inscriptions']
    support = collections.Counter(r['label'] for r in training)
    labels = set(support) | {r['reference'] for r in rows}
    canonical = collections.defaultdict(list)
    for label in sorted(labels):
        canonical[unicodedata.normalize('NFC', label).strip()].append(label)
    collisions = [v for v in canonical.values() if len(v) > 1]
    per_image = collections.defaultdict(lambda: {'n': 0, 'correct': 0})
    buckets = collections.defaultdict(lambda: {'n': 0, 'correct': 0})
    confusions = collections.Counter()
    normalized_correct = 0
    for r in rows:
        m = lookup[r['crop_path']]
        assert m['source_split'] == 'val' and m['label'] == r['reference']
        n = support[r['reference']]
        bucket = 'unseen' if n == 0 else '1–4' if n < 5 else '5–19' if n < 20 else '20+'
        for aggregate in (per_image[m['source_name']], buckets[bucket]):
            aggregate['n'] += 1
            aggregate['correct'] += int(r['correct'])
        normalized_correct += int(unicodedata.normalize('NFC', r['reference']).strip() == unicodedata.normalize('NFC', r['prediction']).strip())
        if not r['correct']:
            confusions[(r['reference'], r['prediction'])] += 1
    assert len(rows) == 300 and len({r['crop_path'] for r in rows}) == 300
    summary = {
        'model': 'broader_inscriptions', 'n': len(rows), 'correct': sum(r['correct'] for r in rows),
        'nfc_strip_correct': normalized_correct, 'nfc_strip_label_collisions': collisions,
        'training_class_support': {'classes': len(support), 'singletons': sum(n == 1 for n in support.values()), 'below_five': sum(n < 5 for n in support.values())},
        'validation_by_training_support': dict(buckets), 'validation_by_image': dict(per_image),
        'top_confusions': [{'reference': a, 'prediction': b, 'count': n} for (a, b), n in confusions.most_common(20)],
        'protocol': 'All 300 existing validation predictions, no retraining. NFC plus outer whitespace only; no merging of distinct transliteration symbols. Source labels unreviewed.',
    }
    (out / 'diagnostics.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    cards = []
    for r in rows:
        m = lookup[r['crop_path']]
        with Image.open(hero / r['crop_path']) as im:
            im = im.convert('RGB'); im.thumbnail((180, 150))
            buf = io.BytesIO(); im.save(buf, format='PNG')
        uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
        esc = html.escape
        status = 'match' if r['correct'] else 'mismatch'
        cards.append(f'''<article data-status="{status}" data-stone="{esc(m['image_id'])}">
        <img src="{uri}" alt="Source character crop {esc(Path(r['crop_path']).stem)}">
        <h3>{esc(Path(r['crop_path']).stem)} · {status}</h3>
        <p>Source label: <b>{esc(r['reference'])}</b><br>Model prediction: <b>{esc(r['prediction'])}</b></p>
        <p>Training examples for source label: {support[r['reference']]}<br>Source line {m['line_number']}, character {m['char_number']}</p>
        <details><summary>Source and bounding box</summary>{esc(m['source_name'])}<br>{esc(str(m['bbox_xyxy']))}<br>{esc(m['source_key'])}</details></article>''')
    options = ''.join(f'<option value="{html.escape(k)}">{html.escape(k)} — {html.escape(v)}</option>' for k, v in sorted({lookup[r['crop_path']]['image_id']: lookup[r['crop_path']]['source_name'] for r in rows}.items()))
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>InscripLens recognition diagnostics</title>
    <style>body{font:16px system-ui;margin:24px;background:#f3f5f7;color:#17202a}header{max-width:1050px}h1{margin-bottom:8px}select{padding:9px;max-width:100%;margin:6px}#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}article{background:white;border:1px solid #ccd3da;border-top:4px solid #b55c2b;padding:16px;border-radius:8px}article[data-status=match]{border-top-color:#168165}article img{width:100%;height:150px;object-fit:contain;background:#e9ecef}h3{font-size:15px}details{font-size:13px;overflow-wrap:anywhere}p{line-height:1.5}[hidden]{display:none!important}.note{padding:12px;background:#fff3cd}</style>
    <header><h1>InscripLens · Recognition error explorer</h1><p>Broader training corpus · median preprocessing + HOG/SVM · <b>47 / 300 source-label matches (15.67%)</b></p>
    <p class="note">Research diagnostic, not a working full-stone OCR demonstration. Crops use supplied annotation boxes. Source labels are unreviewed transliterations, not verified Kannada text. A match means agreement with that source label only.</p>
    <p>All 300 validation crops are included. Filter to inspect successes and failures; these are saved predictions, not new inference. The validation set has been reused for experiments.</p>
    <label>Result <select id="status"><option value="all">All results</option><option value="mismatch">Mismatches</option><option value="match">Matches</option></select></label>
    <label>Image <select id="stone"><option value="all">All six images</option>OPTIONS</select></label><p id="count" aria-live="polite"></p></header><main id="grid">CARDS</main>
    <footer><p>Derived crops: EpiSAM dataset, Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla; source imagery acknowledged to The Mythic Society Bengaluru. <a href="https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset">Public dataset and attribution</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/">CC BY-SA 4.0</a>. Crops resized for display; original labels preserved. This report does not use the restricted corpus.</p></footer>
    <script>const statusFilter=document.getElementById('status'),stoneFilter=document.getElementById('stone');function filter(){let n=0;document.querySelectorAll('article').forEach(c=>{c.hidden=!((statusFilter.value==='all'||c.dataset.status===statusFilter.value)&&(stoneFilter.value==='all'||c.dataset.stone===stoneFilter.value));if(!c.hidden)n++;});document.getElementById('count').textContent=n+' of 300 crops shown';}statusFilter.addEventListener('change',filter);stoneFilter.addEventListener('change',filter);filter();</script></html>'''
    rendered = page.replace('OPTIONS', options).replace('CARDS', '\n'.join(cards))
    class CardCheck(HTMLParser):
        def __init__(self):
            super().__init__(); self.counts = collections.Counter()
        def handle_starttag(self, tag, attrs):
            if tag == 'article':
                self.counts[dict(attrs)['data-status']] += 1
    check = CardCheck(); check.feed(rendered)
    assert check.counts == {'match': 47, 'mismatch': 253}
    assert sum(v['n'] for v in per_image.values()) == 300
    (out / 'error_explorer.html').write_text(rendered, encoding='utf-8')
    # A fixed-position sample: first, middle and last crop from each image.
    groups = collections.defaultdict(list)
    for r in rows:
        groups[r['image_id']].append(r)
    sheet = Image.new('RGB', (1080, 6 * 230), 'white')
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    for row_index, (image_id, group) in enumerate(sorted(groups.items())):
        for col, idx in enumerate((0, len(group) // 2, len(group) - 1)):
            r = group[idx]; x = col * 360; y = row_index * 230
            with Image.open(hero / r['crop_path']) as im:
                im = im.convert('RGB'); im.thumbnail((330, 160))
                sheet.paste(im, (x + (360-im.width)//2, y+5))
            draw.text((x+8, y+170), f'{image_id} #{idx+1} ref: {r["reference"]}', fill='black', font=font)
            draw.text((x+8, y+196), f'pred: {r["prediction"]} | {"match" if r["correct"] else "mismatch"}', fill='black', font=font)
    sheet.save(out / 'systematic_sample.png')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('hero', type=Path); p.add_argument('results', type=Path); p.add_argument('out', type=Path)
    a = p.parse_args(); run(a.hero, a.results, a.out)
