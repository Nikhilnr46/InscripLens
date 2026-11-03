"""Cache broad training masks with inference Python, then fit with application Python.

Run --prepare in binarizer_env; run without --prepare in app env.
Uses retained source records with an additional location exclusion, never pseudo-labels.
"""
from pathlib import Path
import argparse, collections, hashlib, io, json, time, zipfile
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT/'work/broad_clean_masks'
OUT = ROOT/'outputs/broad_clean_study'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def mask_path(name):
    return CACHE/(hashlib.sha256(name.encode()).hexdigest()+'.png')

def main(prepare=False, device='cpu'):
    import re
    site=lambda name: re.split(r'\d',name,maxsplit=1)[0].strip().lower()
    records=read(ROOT/'outputs/training_scope_study/training_records.json')
    hero=read(ROOT/'work/hero_pilot/manifest.json')
    val=[r for r in hero if r['source_split']=='val']
    excluded={site(r['source_name']) for r in val}
    val_hashes={v['pixel_sha256'] for v in val}
    assert len(records) in {9986,9925} and len(val)==300
    additional_exclusions=collections.Counter(r['source_name'] for r in records if any(r['source_name'].lower().startswith(s+' ') for s in excluded))
    records=[r for r in records if r['source_name'] not in additional_exclusions]
    assert len(records)==9925
    assert not ({site(r['source_name']) for r in records}&excluded)
    grouped=collections.defaultdict(list)
    for r in records: grouped[r['source_name']].append(r)
    hero_ids={r['source_name']:r['image_id'] for r in hero}
    CACHE.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    if prepare:
        from binarizer_core import load_model,enhance
        model=load_model(device)
    X=[];Xraw=[];labels=[];groups=[];audit=[];hero_flags=[];blank_crops=0
    if not prepare:
        from run_character_benchmark import features
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as z:
        for index,(name,rows) in enumerate(sorted(grouped.items()),1):
            start=time.perf_counter()
            path=mask_path(name)
            existing=ROOT/'outputs/full_binarizer'/f'{hero_ids.get(name,"missing")}_mask.png'
            if existing.exists(): path=existing
            with Image.open(io.BytesIO(z.read(f'episam_dataset/images/train/{name}.png'))) as raw:
                raw=raw.convert('RGB')
                if not path.exists():
                    if not prepare: raise FileNotFoundError(f'Run --prepare first: {name}')
                    mask=enhance(raw,model)
                    temporary=path.with_suffix('.tmp.png');mask.save(temporary);temporary.replace(path)
                with Image.open(path) as mask:
                    assert mask.size==raw.size,(name,mask.size,raw.size)
                    assert set(np.unique(mask)).issubset({0,255}),name
                    if not prepare:
                        chars=json.loads(z.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
                        for r in rows:
                            c=chars[r['source_key']];box=c['top_left']+c['bottom_right']
                            assert c['char_name']==r['label']
                            crop=raw.crop(box)
                            digest=hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest()
                            assert digest not in val_hashes
                            cleaned=mask.crop(box)
                            blank_crops+=int(np.ptp(np.asarray(cleaned))==0)
                            Xraw.append(features(crop,'median'))
                            X.append(features(cleaned,'median'));labels.append(r['label']);groups.append(site(name));hero_flags.append(r['hero_filename'])
            audit.append({'source_name':name,'mask_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crops':len(rows)})
            print(f'{index}/{len(grouped)} {name}: {time.perf_counter()-start:.1f}s',flush=True)
    if prepare:
        (CACHE/'manifest.json').write_text(json.dumps({'device':device,'images':audit},indent=2),encoding='utf-8')
        return
    from sklearn.svm import SVC
    import joblib
    X=np.stack(X);y=np.array(labels);groups=np.array(groups)
    V=np.stack([features(ROOT/'outputs/full_binarizer'/r['crop_path'],'median') for r in val])
    Vraw=np.stack([features(ROOT/'work/hero_pilot'/r['crop_path'],'median') for r in val])
    truth=np.array([r['label'] for r in val])
    assert np.isfinite(X).all() and np.isfinite(V).all()
    hero_flags=np.array(hero_flags,dtype=bool)
    assert hero_flags.sum()==949
    baseline=SVC(C=10,gamma='scale',kernel='rbf').fit(X[hero_flags],y[hero_flags])
    baseline_correct=int((baseline.predict(V)==truth).sum())
    assert baseline_correct==63,('Baseline reproduction failed',baseline_correct)
    print('Matched hero baseline reproduced: 63/300',flush=True)
    devsites=read(ROOT/'outputs/matched_mask_study/summary.json')['development_sites']
    dev=np.array([any(g==s or g.startswith(s+' ') for s in devsites) for g in groups])
    model=SVC(C=10,gamma='scale',kernel='rbf')
    print('Fitting grouped development model',flush=True)
    model.fit(X[~dev],y[~dev]);dp=model.predict(X[dev])
    hero_dev=hero_flags[dev]
    assert hero_dev.sum()==308
    print('Fitting full training model',flush=True)
    model.fit(X,y);pred=model.predict(V)
    joblib.dump({'model':model,'preprocessing':'median','input_type':'mask'},OUT/'mask_svm_bundle.joblib',compress=3)
    assert np.array_equal(joblib.load(OUT/'mask_svm_bundle.joblib')['model'].predict(V),pred)
    print('Fitting corrected broad original-image control',flush=True)
    raw_model=SVC(C=10,gamma='scale',kernel='rbf').fit(np.stack(Xraw),y)
    raw_pred=raw_model.predict(Vraw)
    support=collections.Counter(y)
    summary={'train_n':len(y),'train_images':len(grouped),'train_classes':len(set(y)),
      'hero_baseline_correct':baseline_correct,'constant_mask_crops_retained':blank_crops,
      'additional_location_exclusions':dict(additional_exclusions),
      'singleton_classes':sum(n==1 for n in support.values()),'classes_below_five_examples':sum(n<5 for n in support.values()),
      'checkpoint_sha256':hashlib.sha256((ROOT/'work/shilalekhya/binarizer.pth').read_bytes()).hexdigest(),
      'training_records_sha256':hashlib.sha256((ROOT/'outputs/training_scope_study/training_records.json').read_bytes()).hexdigest(),
      'development_sites':devsites,'development_n':int(dev.sum()),'development_correct':int((dp==y[dev]).sum()),
      'matched_hero_development_n':int(hero_dev.sum()),'matched_hero_development_correct':int((dp[hero_dev]==y[dev][hero_dev]).sum()),
      'corrected_broad_original_validation_correct':int((raw_pred==truth).sum()),
      'validation_n':len(val),'validation_correct':int((pred==truth).sum()),'accuracy':float((pred==truth).mean()),
      'validation_unseen_n':int((~np.isin(truth,y)).sum()),'excluded_validation_sites':sorted(excluded),
      'per_image':{s:{'n':sum(r['image_id']==s for r in val),'correct':sum(str(p)==r['label'] for r,p in zip(val,pred) if r['image_id']==s)} for s in sorted({r['image_id'] for r in val})},
      'protocol':'9925 broad original-training annotations after removing 61 additional Begur-location records missed by the previous filename rule; predicted masks, median HOG, fixed SVM C10. Same development-site names; broader development population. No tuning.',
      'limitations':['Reused validation, not a fresh final test.','Source boxes supplied, not automatic OCR.','Binarizer pretraining overlap incompletely known.','Broad corpus script/period and raw transliteration labels unaudited.','More classes as well as more examples; not a pure sample-count ablation.']}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (OUT/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':str(p)} for r,p in zip(val,pred)],indent=2),encoding='utf-8')
    (CACHE/'training_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--device',choices=['cpu','cuda'],default='cpu');a=p.parse_args()
    main(a.prepare,a.device)
