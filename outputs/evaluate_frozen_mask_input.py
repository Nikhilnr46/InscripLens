"""Test replacing inputs to an unchanged raw-image classifier. No retraining."""
from pathlib import Path
import json
import numpy as np
import joblib
from run_character_benchmark import features
root=Path(__file__).resolve().parent.parent;out=root/'outputs/full_binarizer'
rows=[r for r in json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8')) if r['source_split']=='val']
bundle=joblib.load(root/'outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib')
truth=np.array([r['label'] for r in rows]);results={};predictions=[]
for name,folder in [('original',root/'work/hero_pilot'),('predicted_mask',out)]:
 X=np.stack([features(folder/r['crop_path'],bundle['preprocessing']) for r in rows]);pred=bundle['model'].predict(X)
 results[name]={'correct':int((pred==truth).sum()),'n':len(rows),'accuracy':float((pred==truth).mean()),'per_image':{s:{'correct':sum(p==r['label'] for r,p in zip(rows,pred) if r['image_id']==s),'n':sum(r['image_id']==s for r in rows)} for s in sorted({r['image_id'] for r in rows})}}
 predictions.extend({'input':name,'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':str(p)} for r,p in zip(rows,pred))
assert results['original']['correct']==47
(out/'recognition_comparison.json').write_text(json.dumps({'results':results,'protocol':'Frozen broader SVM, same median/HOG features and 300 supplied boxes. Only inference input changed. Not a matched retraining comparison; domain shift can hurt. Binarizer pretraining overlap incompletely known.'},indent=2),encoding='utf-8')
(out/'recognition_predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,indent=2))
