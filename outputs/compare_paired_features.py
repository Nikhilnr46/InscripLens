"""Fixed development-only test of original-image plus predicted-mask HOG."""
import collections, hashlib, io, json, time, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.svm import SVC
from evaluate_metadata_context import excluded
from run_character_benchmark import features

ROOT=Path(__file__).resolve().parent.parent


def load_training_features():
    read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
    protocol=read('outputs/matched_mask_study/summary.json')
    rows=sorted([r for r in read('outputs/training_scope_study/training_records.json')
                 if not excluded(r['source_name'],protocol['excluded_validation_sites'])],key=lambda r:r['source_name'])
    assert len(rows)==9925
    ids={r['source_name']:r['image_id'] for r in read('work/hero_pilot/manifest.json')}
    groups=collections.defaultdict(list)
    for r in rows:groups[r['source_name']].append(r)
    original=[];masks=[]
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as z:
        for i,(name,group) in enumerate(groups.items(),1):
            chars=json.loads(z.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
            path=ROOT/'outputs/full_binarizer'/f'{ids.get(name,"missing")}_mask.png'
            if not path.exists():path=ROOT/'work/broad_clean_masks'/(hashlib.sha256(name.encode()).hexdigest()+'.png')
            with Image.open(io.BytesIO(z.read(f'episam_dataset/images/train/{name}.png'))) as raw, Image.open(path) as mask:
                assert raw.size==mask.size
                for r in group:
                    c=chars[r['source_key']];assert c['char_name']==r['label']
                    box=c['top_left']+c['bottom_right']
                    original.append(features(raw.crop(box),'median'))
                    masks.append(features(mask.crop(box),'median'))
            if i%25==0:print(f'Features: {i}/{len(groups)} sources',flush=True)
    x=np.asarray(masks);o=np.asarray(original);y=np.array([r['label'] for r in rows])
    dev=np.array([excluded(r['source_name'],protocol['development_sites']) for r in rows])
    hero=np.array([r['hero_filename'] for r in rows])[dev]
    assert dev.sum()==359 and hero.sum()==308
    assert np.isfinite(x).all() and np.isfinite(o).all()
    return x,o,y,rows,dev,hero


def main():
    start=time.perf_counter()
    x,o,y,rows,dev,hero=load_training_features()
    results={};predictions={}
    for name,data in [('mask_only',x),('equal_original_plus_mask',np.concatenate((x,o),axis=1))]:
        print('Fitting '+name,flush=True);t=time.perf_counter()
        model=SVC(C=10,gamma='scale',kernel='rbf').fit(data[~dev],y[~dev])
        pred=model.predict(data[dev]);predictions[name]=pred
        results[name]={'hero_development_correct':int((pred[hero]==y[dev][hero]).sum()),
                       'all_development_correct':int((pred==y[dev]).sum()),'feature_dimension':data.shape[1],
                       'seconds':time.perf_counter()-t}
        print(json.dumps(results[name]),flush=True)
    assert results['mask_only']['hero_development_correct']==63,results
    a=predictions['mask_only'][hero]==y[dev][hero];b=predictions['equal_original_plus_mask'][hero]==y[dev][hero]
    result={'fit_n':int((~dev).sum()),'development_n':int(dev.sum()),'hero_development_n':int(hero.sum()),
            'results':results,'hero_fixed_errors':int((~a & b).sum()),'hero_new_errors':int((a & ~b).sum()),
            'candidate_beats_baseline':int(b.sum())>int(a.sum()),'validation_evaluated':False,
            'production_model_changed':False,'seconds':time.perf_counter()-start,
            'protocol':'Fixed equal concatenation of median-filtered original and predicted-mask HOG; SVC C10 gamma scale. No weight or hyperparameter search. Same location exclusions and development split.',
            'limitations':['Development reused; not fresh evaluation.','Supplied character boxes.','Enhancement pretraining overlap uncertain.','Equal feature blocks do not guarantee equal useful information.']}
    out=ROOT/'outputs/paired_feature_study';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
