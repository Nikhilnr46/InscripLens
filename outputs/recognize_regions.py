"""Automatic candidate localization plus raw-label recognition, not transcription."""
import numpy as np
from run_character_benchmark import features
from segment_candidates import candidates

def recognize(mask,bundle):
    boxes=candidates(mask)
    if not boxes:return []
    x=np.stack([features(mask.crop(box),bundle['preprocessing']) for box in boxes])
    if not np.isfinite(x).all():raise ValueError('Non-finite recognition features')
    labels=bundle['model'].predict(x)
    return [{'candidate':i+1,'bbox':box,'predicted_source_label':str(label),'verified':False} for i,(box,label) in enumerate(zip(boxes,labels))]

def match_boxes(reference,predicted,threshold=.5):
    from scipy.optimize import linear_sum_assignment
    scores=np.zeros((len(reference),len(predicted)))
    for i,a in enumerate(reference):
        for j,b in enumerate(predicted):
            inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
            scores[i,j]=inter/union if union else 0
    if not scores.size:return []
    ii,jj=linear_sum_assignment(-((scores>=threshold).astype(float)*(min(scores.shape)+1)+scores))
    return [(int(i),int(j),float(scores[i,j])) for i,j in zip(ii,jj) if scores[i,j]>=threshold]

if __name__=='__main__':
    import argparse,hashlib,json,joblib,time
    from pathlib import Path
    from PIL import Image
    root=Path(__file__).resolve().parent.parent
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'outputs/matched_mask_study/mask_svm_bundle.joblib')
    parser.add_argument('--output',type=Path,default=root/'outputs/pipeline_study')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    bundle=joblib.load(args.model)
    rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'));reports=[];records=[]
    for image_id in sorted({r['image_id'] for r in rows if r['source_split']=='val'}):
        start=time.perf_counter()
        with Image.open(root/f'outputs/full_binarizer/{image_id}_mask.png') as mask:pred=recognize(mask,bundle)
        gt=[r for r in rows if r['image_id']==image_id]
        matches=match_boxes([r['bbox_xyxy'] for r in gt],[p['bbox'] for p in pred])
        correct=sum(gt[i]['label']==pred[j]['predicted_source_label'] for i,j,_ in matches)
        reports.append({'image_id':image_id,'reference_n':len(gt),'candidate_n':len(pred),'localized_n':len(matches),'localized_and_correct_n':correct,'seconds':time.perf_counter()-start})
        records.append({'image_id':image_id,'predictions':pred,'matched_pairs':matches})
    ref=sum(r['reference_n'] for r in reports);n=sum(r['candidate_n'] for r in reports);localized=sum(r['localized_n'] for r in reports);correct=sum(r['localized_and_correct_n'] for r in reports)
    assert ref==300 and n==330 and localized==196
    summary={'reference_n':ref,'candidate_n':n,'localized_n':localized,'localized_and_correct_n':correct,'joint_precision':correct/n,'joint_recall':correct/ref,'recognition_accuracy_on_localized_candidates':correct/localized,'per_image':reports,'protocol':'Full-image predicted masks -> fixed connected components -> maskHOG/SVM. No reference boxes used for prediction. Geometry-only one-to-one IoU>=0.5 matching, then exact source-label agreement.','limitations':['Not a line/full-text transcription metric: no verified reading order.','Validation reused and pretrained binarizer overlap incompletely known.','Filtered source annotations may omit legitimate glyphs.','Not directly comparable to recognition using supplied boxes.']}
    summary['model_sha256']=hashlib.sha256(args.model.read_bytes()).hexdigest()
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    (out/'predictions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
