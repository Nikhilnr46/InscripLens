"""Bounded training-scope comparison; median preprocessing and fixed SVM.
Usage: python compare_training_scope.py ARCHIVE.zip HERO_DATA_DIR RESULTS_DIR
"""
import argparse, collections, hashlib, io, json, re, time, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report
import joblib
from run_character_benchmark import features

def site(name):
    return re.split(r'\d',name,maxsplit=1)[0].strip().lower()

def run(archive,hero,out):
    out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((hero/'manifest.json').read_text(encoding='utf-8'))
    val=[r for r in rows if r['source_split']=='val'];sites={site(r['source_name']) for r in val}
    val_hashes={r['pixel_sha256'] for r in val}
    V=np.stack([features(hero/r['crop_path'],'median') for r in val]);truth=np.array([r['label'] for r in val])
    X=[];y=[];is_hero=[];metadata=[];excluded=collections.Counter();excluded_images=[]
    tmp=out/'temporary_crop.png'
    with zipfile.ZipFile(archive) as z:
        files=sorted(n for n in z.namelist() if '/images/train/' in n and n.endswith('.png'))
        for k,n in enumerate(files,1):
            stem=Path(n).stem
            if site(stem) in sites:
                excluded_images.append(stem);continue
            im=Image.open(io.BytesIO(z.read(n))).convert('RGB')
            chars=json.loads(z.read(f'episam_dataset/chars/train/{stem}/character_polygons.json'))
            positions=collections.Counter((c.get('line_number'),c.get('char_number')) for c in chars.values())
            for key,c in chars.items():
                label=c.get('char_name');box=c.get('top_left',[])+c.get('bottom_right',[])
                if label is None or str(label).strip().lower() in {'','none','nan','nanl','null','unknown'}:excluded['placeholder']+=1;continue
                if positions[(c.get('line_number'),c.get('char_number'))]>1:excluded['duplicate_position']+=1;continue
                if len(box)!=4 or not(0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height):excluded['invalid_box']+=1;continue
                crop=im.crop(tuple(box));digest=hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest()
                if digest in val_hashes:excluded['validation_pixel_duplicate']+=1;continue
                crop.save(tmp);X.append(features(tmp,'median'));y.append(label);is_hero.append('hero' in stem.lower())
                metadata.append({'source_name':stem,'source_key':key,'label':label,'hero_filename':'hero' in stem.lower()})
            if k%20==0:print(f'Processed {k}/{len(files)} train images; {len(y)} crops',flush=True)
    tmp.unlink(missing_ok=True)
    X=np.stack(X);y=np.array(y);is_hero=np.array(is_hero);results={};predictions=[]
    assert np.isfinite(X).all()
    for name,selected in [('hero_only',is_hero),('broader_inscriptions',np.ones(len(y),dtype=bool))]:
        print('Training',name,int(selected.sum()),flush=True)
        model=SVC(C=10,gamma='scale',kernel='rbf');start=time.perf_counter();model.fit(X[selected],y[selected]);elapsed=time.perf_counter()-start
        pred=model.predict(V);report=classification_report(truth,pred,output_dict=True,zero_division=0)
        support=collections.Counter(y[selected]);known=np.isin(truth,list(support))
        results[name]={'train_crops':int(selected.sum()),'train_images':len({r['source_name'] for r,keep in zip(metadata,selected) if keep}),'train_classes':len(support),'validation_correct':int(np.sum(truth==pred)),'validation_n':len(val),'accuracy':float(accuracy_score(truth,pred)),'validation_unseen_n':int((~known).sum()),'known_label_accuracy':float(accuracy_score(truth[known],pred[known])),'macro_f1':report['macro avg']['f1-score'],'weighted_f1':report['weighted avg']['f1-score'],'fit_seconds':elapsed}
        joblib.dump({'model':model,'preprocessing':'median'},out/f'{name}_svm_bundle.joblib')
        assert np.array_equal(joblib.load(out/f'{name}_svm_bundle.joblib')['model'].predict(V[:5]),pred[:5])
        (out/f'{name}_classification_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        predictions.extend({'model':name,'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':str(p),'correct':r['label']==p} for r,p in zip(val,pred))
        print(name,json.dumps(results[name]),flush=True)
    summary={'protocol':'Source train only; exclude all six validation sites using filename-derived site. Exact validation crop pixels excluded. Median + fixed RBF SVM C10 gamma scale for both models. No hyperparameter tuning.','excluded_validation_sites':sorted(sites),'excluded_training_images':excluded_images,'excluded_annotations':dict(excluded),'results':results,'limitations':['Same 300 validation crops reused; not a fresh final test.','Site groups are conservative filename-derived groups, not verified stone identities.','Broader corpus script/language composition and label conventions remain unaudited.','Source annotation boxes supplied; no automatic segmentation tested.','Recognition labels are raw source transliteration strings.']}
    (out/'scope_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'training_records.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Finished; results saved.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('hero',type=Path);p.add_argument('out',type=Path);a=p.parse_args();run(a.archive,a.hero,a.out)
