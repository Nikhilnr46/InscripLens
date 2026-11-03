"""Fixed first-pass character classification benchmark, not whole-stone OCR.
Usage: python run_character_benchmark.py DATASET_DIR RESULTS_DIR
Dependencies: numpy, Pillow, scikit-learn, joblib.
"""
import argparse, collections, hashlib, json, platform, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageFilter
import PIL, sklearn, joblib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report

def features(path, variant='original'):
    """32x32 letterbox; gradient orientation histograms; 2x2-cell normalisation."""
    im=path.convert('L') if isinstance(path,Image.Image) else Image.open(path).convert('L')
    if variant=='median':
        im=im.filter(ImageFilter.MedianFilter(3))
    elif variant=='autocontrast':
        im=ImageOps.autocontrast(im,cutoff=1)
    elif variant=='otsu':
        a=np.asarray(im); hist=np.bincount(a.ravel(),minlength=256).astype(float)
        weight=np.cumsum(hist); moment=np.cumsum(hist*np.arange(256)); total=weight[-1]
        denominator=weight*(total-weight)
        score=np.divide((moment[-1]*weight-moment*total)**2,denominator,out=np.zeros(256),where=denominator>0)
        threshold=int(np.argmax(score));im=Image.fromarray(np.where(a>threshold,255,0).astype('uint8'))
    elif variant!='original':
        raise ValueError('Unknown preprocessing variant: '+variant)
    im=ImageOps.contain(im,(32,32),method=Image.Resampling.LANCZOS)
    canvas=Image.new('L',(32,32),int(np.median(np.asarray(im))))
    canvas.paste(im,((32-im.width)//2,(32-im.height)//2))
    a=np.asarray(canvas,dtype=np.float32)/255
    gy,gx=np.gradient(a); magnitude=np.hypot(gx,gy)
    bins=(np.arctan2(gy,gx)%(np.pi))*9/np.pi
    lower=np.floor(bins).astype(int)%9; fraction=bins-np.floor(bins)
    cells=np.zeros((4,4,9),np.float32)
    for y in range(4):
        for x in range(4):
            s=np.s_[y*8:y*8+8,x*8:x*8+8]
            cells[y,x]=np.bincount(lower[s].ravel(),weights=(magnitude[s]*(1-fraction[s])).ravel(),minlength=9)+np.bincount(((lower[s]+1)%9).ravel(),weights=(magnitude[s]*fraction[s]).ravel(),minlength=9)
    blocks=[]
    for y in range(3):
        for x in range(3):
            b=cells[y:y+2,x:x+2].ravel(); b=b/np.sqrt(np.dot(b,b)+1e-6)
            b=np.minimum(b,.2); b=b/np.sqrt(np.dot(b,b)+1e-6);blocks.append(b)
    return np.concatenate(blocks)

def run(data,out):
    out.mkdir(parents=True,exist_ok=True)
    raw=(data/'manifest.json').read_bytes(); records=json.loads(raw)
    train=[r for r in records if r['source_split']=='train']; val=[r for r in records if r['source_split']=='val']
    assert {r['image_id'] for r in train}.isdisjoint(r['image_id'] for r in val)
    assert {r['pixel_sha256'] for r in train}.isdisjoint(r['pixel_sha256'] for r in val)
    X=np.stack([features(data/r['crop_path']) for r in train]); V=np.stack([features(data/r['crop_path']) for r in val])
    y=np.array([r['label'] for r in train]); truth=np.array([r['label'] for r in val])
    assert X.shape==(len(train),324) and np.isfinite(X).all() and np.isfinite(V).all()
    known=np.isin(truth,np.unique(y))
    models={'majority_control':DummyClassifier(strategy='most_frequent'),'knn':KNeighborsClassifier(n_neighbors=3,weights='distance',n_jobs=2),'svm':SVC(C=10,gamma='scale',kernel='rbf'),'random_forest':RandomForestClassifier(n_estimators=150,max_features='sqrt',class_weight='balanced_subsample',random_state=42,n_jobs=2)}
    results={}; predictions=[]
    for name,model in models.items():
        t=time.perf_counter();model.fit(X,y);fit=time.perf_counter()-t
        t=time.perf_counter();pred=model.predict(V);elapsed=time.perf_counter()-t
        report=classification_report(truth,pred,output_dict=True,zero_division=0)
        per_stone={s:{'n':sum(r['image_id']==s for r in val),'accuracy':float(accuracy_score(truth[[r['image_id']==s for r in val]],pred[[r['image_id']==s for r in val]]))} for s in sorted({r['image_id'] for r in val})}
        results[name]={'accuracy':float(accuracy_score(truth,pred)),'correct':int(np.sum(truth==pred)),'n':len(val),'known_label_accuracy':float(accuracy_score(truth[known],pred[known])),'known_label_n':int(known.sum()),'macro_precision':report['macro avg']['precision'],'macro_recall':report['macro avg']['recall'],'macro_f1':report['macro avg']['f1-score'],'weighted_f1':report['weighted avg']['f1-score'],'fit_seconds':fit,'predict_seconds':elapsed,'per_stone':per_stone}
        (out/f'{name}_classification_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        joblib.dump(model,out/f'{name}.joblib')
        restored=joblib.load(out/f'{name}.joblib');assert np.array_equal(restored.predict(V[:5]),pred[:5])
        for r,p in zip(val,pred):predictions.append({'model':name,'crop_path':r['crop_path'],'image_id':r['image_id'],'reference':r['label'],'prediction':str(p),'correct':r['label']==p,'label_seen_in_training':r['label'] in set(y)})
        print(name,json.dumps(results[name]),flush=True)
    summary={'dataset_manifest_sha256':hashlib.sha256(raw).hexdigest(),'training_n':len(train),'validation_n':len(val),'training_classes':len(set(y)),'unseen_validation_n':int((~known).sum()),'feature_dimension':324,'feature_definition':'32x32 grayscale letterbox; 8x8 cells, 9 unsigned orientation bins, overlapping 2x2-cell L2-Hys blocks; no fitted feature transform','validation_protocol':'Original source train/val split, fixed parameters, no validation tuning. Annotation-supplied character boxes. Raw source labels, no Kannada conversion.','macro_definition':'Unweighted mean over labels present in reference or predictions; undefined metrics set to zero.','versions':{'python':platform.python_version(),'numpy':np.__version__,'Pillow':PIL.__version__,'scikit-learn':sklearn.__version__,'joblib':joblib.__version__},'results':results}
    (out/'benchmark_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
    # Metric sanity checks: exact predictions and a deliberately wrong prediction.
    assert accuracy_score(['a','b'],['a','b'])==1 and accuracy_score(['a','b'],['a','a'])==.5
    print('Checks passed: split IDs, exact pixel duplicates, finite features, prediction reload, metric sanity.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.data,a.out)
