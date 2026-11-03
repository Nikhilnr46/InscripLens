"""Training-only mild geometric augmentation, inspired by historical OCR work."""
from pathlib import Path
import json,re
import numpy as np
from PIL import Image
from sklearn.svm import SVC
import joblib
from run_character_benchmark import features
root=Path(__file__).resolve().parent.parent;out=root/'outputs/augmentation_study';out.mkdir(exist_ok=True)
rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'));protocol=json.loads((root/'outputs/matched_mask_study/summary.json').read_text())
site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
train=[r for r in rows if r['source_split']=='train' and site(r) not in protocol['excluded_validation_sites']];val=[r for r in rows if r['source_split']=='val']
dev=np.array([site(r) in protocol['development_sites'] for r in train]);y=np.array([r['label'] for r in train]);x=[];aug=[];ay=[];adev=[]
for i,r in enumerate(train):
 with Image.open(root/'outputs/full_binarizer'/r['crop_path']) as source:
  im=source.convert('L');f=features(im,'median');x.append(f)
  for angle in [0,-7,7]:
   rotated=im if angle==0 else im.rotate(angle,resample=Image.Resampling.BILINEAR,expand=True,fillcolor=0)
   aug.append(features(rotated,'median'));ay.append(r['label']);adev.append(dev[i])
x=np.stack(x);aug=np.stack(aug);ay=np.array(ay);adev=np.array(adev);scores={}
variants=['baseline','rotation','rotation_balanced']
for name in variants:
 model=SVC(C=10,gamma='scale',class_weight='balanced' if name=='rotation_balanced' else None)
 xx,yy,dd=(x,y,dev) if name=='baseline' else (aug,ay,adev)
 model.fit(xx[~dd],yy[~dd]);scores[name]=int((model.predict(x[dev])==y[dev]).sum());print(name,scores[name],flush=True)
assert scores['baseline']==50
chosen=max(scores,key=scores.get);xx,yy=(x,y) if chosen=='baseline' else (aug,ay)
model=SVC(C=10,gamma='scale',class_weight='balanced' if chosen=='rotation_balanced' else None);model.fit(xx,yy)
v=[]
for r in val:
 with Image.open(root/'outputs/full_binarizer'/r['crop_path']) as im:v.append(features(im,'median'))
v=np.stack(v);p=model.predict(v);truth=np.array([r['label'] for r in val])
joblib.dump({'model':model,'preprocessing':'median','input_type':'mask'},out/'selected_model.joblib')
assert np.array_equal(joblib.load(out/'selected_model.joblib')['model'].predict(v[:5]),p[:5])
summary={'development_correct':scores,'development_n':308,'selected_variant':chosen,'original_training_n':949,'fitted_examples':len(yy),'validation_correct':int((p==truth).sum()),'validation_n':300,'accuracy':float((p==truth).mean()),'protocol':'Three predeclared conditions; mild +/-7degree rotation of training crops only; no mirrored characters; optional balanced SVM weights. Same training-site development and validation. Select earliest best development condition before validation.','limitations':['Synthetic rotations are not new independent inscriptions.','Validation reused, source labels unreviewed, binarizer overlap unknown.','Supplied boxes, not full pipeline score.']}
(out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
