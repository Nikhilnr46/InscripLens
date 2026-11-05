"""Pretrain the line CNN on source-labelled glyphs from fit locations only."""
import hashlib
import json
import zipfile
from collections import defaultdict, Counter
from itertools import chain
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import torch
from torch import nn

from check_sequence_learning import SequenceRecognizer
import re


def excluded(name, sites):
    site = re.split(r"\d", name, maxsplit=1)[0].strip().lower()
    return any(site == entry or site.startswith(entry + " ") for entry in sites)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'outputs/glyph_encoder_study'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def main():
    torch.manual_seed(42)
    torch.set_num_threads(4)
    groups = defaultdict(list)
    protocol = read('outputs/matched_mask_study/summary.json')
    for row in read('outputs/training_scope_study/training_records.json'):
        if not excluded(row['source_name'], protocol['excluded_validation_sites']):
            groups[row['source_name']].append(row)
    ids = {r['source_name']: r['image_id'] for r in read('work/hero_pilot/manifest.json')}
    samples = {'fit': [], 'dev': []}
    labels = {'fit': [], 'dev': []}
    with zipfile.ZipFile(ROOT / 'work/episam_dataset.zip') as archive:
        for name, rows in sorted(groups.items()):
            split = 'dev' if excluded(name, protocol['development_sites']) else 'fit'
            path = ROOT / 'outputs/full_binarizer' / f'{ids.get(name, "missing")}_mask.png'
            if not path.exists():
                path = ROOT / 'work/broad_clean_masks' / (hashlib.sha256(name.encode()).hexdigest() + '.png')
            annotations = json.loads(archive.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
            with Image.open(path) as mask:
                for row in rows:
                    char = annotations[row['source_key']]
                    assert char['char_name'] == row['label']
                    crop = mask.crop(char['top_left'] + char['bottom_right']).convert('L')
                    tile = ImageOps.pad(crop, (32, 32), method=Image.Resampling.BILINEAR, color=0)
                    samples[split].append(np.array(tile))
                    labels[split].append(row['label'])
    assert (len(labels['fit']), len(labels['dev'])) == (9566, 359)
    classes = sorted(set(labels['fit']))
    index = {c: i for i, c in enumerate(classes)}
    x = {s: torch.from_numpy(np.stack(v))[:, None].float()/255 for s,v in samples.items()}
    y = torch.tensor([index[c] for c in labels['fit']])
    encoder = SequenceRecognizer(2, True).cnn
    model = nn.Sequential(encoder, nn.AdaptiveAvgPool2d((4,4)), nn.Flatten(), nn.Linear(512, len(classes)))
    opt = torch.optim.Adam(model.parameters(), lr=.001)
    for epoch in range(6):
        for batch in torch.randperm(len(y)).split(64):
            opt.zero_grad()
            loss = nn.functional.cross_entropy(model(x['fit'][batch]), y[batch])
            loss.backward(); opt.step()
        print(f'Glyph epoch {epoch+1}/6', flush=True)
    with torch.inference_mode():
        predicted = list(chain.from_iterable(model(batch).argmax(1).tolist() for batch in x['dev'].split(64)))
    common = Counter(labels['fit']).most_common(1)[0][0]
    result = dict(fit=len(y), development=len(predicted), epochs=6, classes=len(classes),
                  correct=sum(classes[i]==c for i,c in zip(predicted,labels['dev'])),
                  frequency_control_correct=labels['dev'].count(common))
    OUT.mkdir(exist_ok=True)
    torch.save(encoder.state_dict(), OUT/'encoder.pth')
    (OUT/'glyph_summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result, flush=True)


if __name__ == '__main__':
    main()
