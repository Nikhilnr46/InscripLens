"""Fixed matched cohort comparison, no validation parameter selection."""
from pathlib import Path
import json,re,collections
import numpy as np
import joblib
from sklearn.svm import SVC
from sklearn.model_selection import GroupShuffleSplit
from run_character_benchmark import features
root=Path(__file__).resolve().parent.parent;out=root/'outputs/matched_mask_study';out.mkdir(exist_ok=True)
rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
val=[r for r in rows if r['source_split']=='val'];excluded={site(r) for r in val}
train=[r for r in rows if r['source_split']=='train' and site(r) not in excluded]
assert len(train)==949 and len(val)==300
y=np.array([r['label'] for r in train]);truth=np.array([r['label'] for r in val]);groups=np.array([site(r) for r in train])
fit,dev=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(np.zeros(len(y)),y,groups))
assert set(groups[fit]).isdisjoint(groups[dev])
results={};predictions=[]
for name,folder in [('original',root/'work/hero_pilot'),('mask',root/'outputs/full_binarizer')]:
    X=np.stack([features(folder/r['crop_path'],'median') for r in train]);V=np.stack([features(folder/r['crop_path'],'median') for r in val])
    assert np.isfinite(X).all() and np.isfinite(V).all()
    model=SVC(C=10,gamma='scale',kernel='rbf');model.fit(X[fit],y[fit]);devpred=model.predict(X[dev]);model.fit(X,y);pred=model.predict(V)
    joblib.dump({'model':model,'preprocessing':'median','input_type':name},out/f'{name}_svm_bundle.joblib')
    assert np.array_equal(joblib.load(out/f'{name}_svm_bundle.joblib')['model'].predict(V[:5]),pred[:5])
    results[name]={'development_correct':int((devpred==y[dev]).sum()),'development_n':len(dev),'validation_correct':int((pred==truth).sum()),'validation_n':len(val),'accuracy':float((pred==truth).mean()),'per_image':{s:{'n':sum(r['image_id']==s for r in val),'correct':sum(p==r['label'] for r,p in zip(val,pred) if r['image_id']==s)} for s in sorted({r['image_id'] for r in val})}}
    predictions.extend({'input':name,'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':str(p)} for r,p in zip(val,pred))
    print(name,json.dumps(results[name]),flush=True)
assert results['original']['validation_correct']==45
summary={'train_n':len(train),'train_classes':len(set(y)),'excluded_validation_sites':sorted(excluded),'development_sites':sorted(set(groups[dev])),'results':results,'protocol':'Fixed median+HOG+SVM(C10), identical 949 hero training crops and 300 validation crops. Grouped training-only development, seed42. Both variants evaluated; no hyperparameter sweep. Annotation boxes used.','limitations':['Validation reused, not a fresh final test.','Binarizer pretraining overlap incompletely known, including training-only development.','Raw source labels unreviewed.','No automatic segmentation or translation tested.']}
(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(out/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
