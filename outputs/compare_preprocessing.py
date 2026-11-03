"""Select preprocessing using site-grouped training-development data only."""
from pathlib import Path
import argparse,json,re,collections,time
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score,classification_report
import joblib
from run_character_benchmark import features

def run(data,out):
    out.mkdir(parents=True,exist_ok=True)
    records=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    train=[r for r in records if r['source_split']=='train'];val=[r for r in records if r['source_split']=='val']
    y=np.array([r['label'] for r in train]);truth=np.array([r['label'] for r in val])
    groups=np.array([re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower() for r in train])
    fit,dev=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(np.zeros(len(train)),y,groups))
    assert set(groups[fit]).isdisjoint(groups[dev])
    variants=['original','median','autocontrast','otsu'];results=[];cached={}
    for variant in variants:
        X=np.stack([features(data/r['crop_path'],variant) for r in train]);assert np.isfinite(X).all();cached[variant]=X
        model=SVC(C=10,gamma='scale',kernel='rbf');model.fit(X[fit],y[fit]);pred=model.predict(X[dev])
        row={'variant':variant,'dev_correct':int(np.sum(y[dev]==pred)),'dev_n':len(dev),'dev_accuracy':float(accuracy_score(y[dev],pred))};results.append(row);print(json.dumps(row),flush=True)
    # First variant wins ties; original is first. Do not inspect validation to choose.
    chosen=max(results,key=lambda x:x['dev_accuracy'])['variant']
    model=SVC(C=10,gamma='scale',kernel='rbf');model.fit(cached[chosen],y)
    V=np.stack([features(data/r['crop_path'],chosen) for r in val]);pred=model.predict(V)
    report=classification_report(truth,pred,output_dict=True,zero_division=0)
    summary={'selection_protocol':'Four predeclared preprocessing variants; fixed SVM; GroupShuffleSplit of training data by filename-derived site, seed 42; validation not used to choose variant.','fit_crop_n':len(fit),'dev_crop_n':len(dev),'fit_sites':sorted(set(groups[fit])),'dev_sites':sorted(set(groups[dev])),'dev_unseen_label_n':int(sum(label not in set(y[fit]) for label in y[dev])),'experiments':results,'selected_variant':chosen,'validation_correct':int(np.sum(truth==pred)),'validation_n':len(val),'validation_accuracy':float(accuracy_score(truth,pred)),'validation_macro_f1':report['macro avg']['f1-score'],'validation_weighted_f1':report['weighted avg']['f1-score'],'limitations':['Validation is the same set used for the earlier baseline, not a fresh final test.','Site groups are inferred from names, not verified physical-stone IDs.','Feature and classifier parameters remain fixed.','Labels and bounding boxes come from source annotations.']}
    (out/'preprocessing_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':str(p),'correct':r['label']==p} for r,p in zip(val,pred)],ensure_ascii=False,indent=2),encoding='utf-8')
    joblib.dump({'model':model,'preprocessing':chosen},out/'selected_svm_bundle.joblib')
    b=joblib.load(out/'selected_svm_bundle.joblib');assert np.array_equal(b['model'].predict(V[:5]),pred[:5])
    print(json.dumps(summary,ensure_ascii=True),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('data',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.data,a.out)
