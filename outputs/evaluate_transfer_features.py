"""Select original/mask transfer variant using training-only development."""
from pathlib import Path
import json,re
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn.svm import SVC
import joblib
root=Path(__file__).resolve().parent.parent;out=root/'outputs/transfer_study'
rows=json.loads((out/'records.json').read_text(encoding='utf-8'));protocol=json.loads((root/'outputs/matched_mask_study/summary.json').read_text())
site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
train=np.array([r['source_split']=='train' for r in rows]);dev=np.array([t and site(r) in protocol['development_sites'] for r,t in zip(rows,train)]);fit=train & ~dev;val=~train
y=np.array([r['label'] for r in rows]);scores={};arrays={}
for name in ['original','mask']:
    x=np.load(out/f'{name}_features.npy');arrays[name]=x
    model=make_pipeline(Normalizer(),SVC(C=10,kernel='rbf',gamma='scale'));model.fit(x[fit],y[fit]);p=model.predict(x[dev]);scores[name]=int((p==y[dev]).sum())
selected=max(scores,key=scores.get);x=arrays[selected]
model=make_pipeline(Normalizer(),SVC(C=10,kernel='rbf',gamma='scale'));model.fit(x[train],y[train]);p=model.predict(x[val])
joblib.dump({'model':model,'input':selected,'encoder':'resnet18_IMAGENET1K_V1','preprocessing':'224_letterbox_median_fill_ImageNet_normalization'},out/'selected_head.joblib')
assert np.array_equal(joblib.load(out/'selected_head.joblib')['model'].predict(x[val][:5]),p[:5])
summary={'encoder':'Frozen ImageNet ResNet18, 512 features','development_correct':scores,'development_n':int(dev.sum()),'selected_input':selected,'training_n':int(train.sum()),'validation_correct':int((p==y[val]).sum()),'validation_n':int(val.sum()),'accuracy':float((p==y[val]).mean()),'protocol':'Same949train/300val as maskSVM; fit641/dev308 sites. Fixed L2-normalized features+RBF SVM C10. Choose only original vs mask input on development; evaluate selected variant on reused validation. 224px aspect-preserving letterbox with median fill, ImageNet normalization; differs from standard resize/centre-crop to preserve glyph edges.','limitations':['Generic ImageNet features, not Kannada-pretrained recognition.','Validation reused and binarizer pretraining overlap unknown.','Supplied annotation boxes; source labels unreviewed.']}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
(out/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'reference':r['label'],'prediction':str(pred)} for r,pred in zip([r for r,v in zip(rows,val) if v],p)],ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
