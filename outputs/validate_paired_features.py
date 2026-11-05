"""One fixed paired-HOG validation; does not replace the application model."""
import json, time, hashlib
import joblib
import numpy as np
from PIL import Image
from sklearn.svm import SVC
from compare_paired_features import ROOT, load_training_features
from run_character_benchmark import features
from segment_candidates import candidates
from recognize_regions import match_boxes


def main():
    started=time.perf_counter()
    x,o,y,training,_,_=load_training_features()
    print('Fitting fixed paired candidate on 9925 training crops',flush=True)
    model=SVC(C=10,gamma='scale',kernel='rbf').fit(np.concatenate((x,o),axis=1),y)
    baseline_path=ROOT/'outputs/broad_clean_study/mask_svm_bundle.joblib'
    baseline=joblib.load(baseline_path)['model']
    rows=json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    rows=[r for r in rows if r['source_split']=='val']
    assert not {r['source_name'] for r in training}&{r['source_name'] for r in rows}
    reports=[]; predictions=[]
    for image_id in sorted({r['image_id'] for r in rows}):
        gt=[r for r in rows if r['image_id']==image_id]
        with Image.open(ROOT/f'outputs/full_binarizer/{image_id}_original.png') as raw, Image.open(ROOT/f'outputs/full_binarizer/{image_id}_mask.png') as mask:
            assert raw.size==mask.size
            detected=candidates(mask)
            boxes=[r['bbox_xyxy'] for r in gt]+detected
            xm=np.stack([features(mask.crop(b),'median') for b in boxes])
            xo=np.stack([features(raw.crop(b),'median') for b in boxes])
        assert np.isfinite(xm).all() and np.isfinite(xo).all()
        a=baseline.predict(xm);b=model.predict(np.concatenate((xm,xo),axis=1))
        n=len(gt); truth=np.array([r['label'] for r in gt]);ac=a[:n]==truth;bc=b[:n]==truth
        matches=match_boxes([r['bbox_xyxy'] for r in gt],detected)
        reports.append(dict(image_id=image_id,reference_n=n,candidate_n=len(detected),localized_n=len(matches),
            baseline_reference_correct=int(ac.sum()),paired_reference_correct=int(bc.sum()),
            fixed_errors=int((~ac&bc).sum()),new_errors=int((ac&~bc).sum()),
            baseline_joint_correct=sum(gt[i]['label']==a[n+j] for i,j,_ in matches),
            paired_joint_correct=sum(gt[i]['label']==b[n+j] for i,j,_ in matches)))
        predictions.append(dict(image_id=image_id,boxes=boxes,baseline=a.tolist(),paired=b.tolist(),truth=truth.tolist(),matches=matches))
    totals={k:sum(r[k] for r in reports) for k in reports[0] if k!='image_id'}
    assert (totals['reference_n'],totals['candidate_n'],totals['localized_n'])==(300,330,196)
    assert (totals['baseline_reference_correct'],totals['baseline_joint_correct'])==(77,52),totals
    result=dict(totals=totals,per_image=reports,fit_n=len(y),feature_dimension=648,
        baseline_sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        production_model_changed=False,seconds=time.perf_counter()-started,
        protocol='Fixed median mask HOG then original HOG concatenation; SVC C10 gamma scale. No validation tuning. Automatic boxes are fixed connected components; geometry-only one-to-one IoU >=0.5 matching.',
        limitations=['Reused validation: 300 source annotations on six images, not a fresh test.',
        'Binarizer pretraining overlap uncertain.','Character recognition only; neither full-line OCR nor translation.',
        'Predictions use raw dataset labels, not verified modern Kannada.'])
    out=ROOT/'outputs/paired_feature_validation';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
    joblib.dump(dict(model=model,preprocessing='median',feature_order=['mask','original'],experimental=True),out/'paired_svm_bundle.joblib')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
