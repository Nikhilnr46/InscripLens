"""Select a bounded component-grouping variant on training locations only."""
from pathlib import Path
import json,re
import numpy as np
from PIL import Image
from scipy import ndimage
from segment_candidates import candidates
from recognize_regions import match_boxes

ROOT=Path(__file__).resolve().parent.parent
MODES=('none','horizontal','vertical','square')

def propose(mask,mode='none'):
    if mode=='none':return candidates(mask)
    shapes={'horizontal':(1,3),'vertical':(3,1),'square':(3,3)}
    if mode not in shapes:raise ValueError(mode)
    # Pad before closing so image-edge strokes are not erased by the operation.
    a=np.pad(np.asarray(mask.convert('L'))>127,1)
    grouped=ndimage.binary_closing(a,structure=np.ones(shapes[mode],bool))[1:-1,1:-1]
    return candidates(Image.fromarray(grouped.astype('uint8')*255))

def evaluate(rows,mode,bundle=None):
    per_image=[];predictions=[]
    for image_id in sorted({r['image_id'] for r in rows}):
        gt=[r for r in rows if r['image_id']==image_id]
        with Image.open(ROOT/f'outputs/full_binarizer/{image_id}_mask.png') as mask:
            boxes=propose(mask,mode)
            matches=match_boxes([r['bbox_xyxy'] for r in gt],boxes)
            item={'image_id':image_id,'references':len(gt),'candidates':len(boxes),'matched':len(matches)}
            if bundle is not None:
                from run_character_benchmark import features
                # Recognition still sees the original predicted mask, not the closing.
                pred=bundle['model'].predict(np.stack([features(mask.crop(b),'median') for b in boxes])) if boxes else []
                item['localized_and_correct']=sum(gt[i]['label']==pred[j] for i,j,_ in matches)
                predictions.append({'image_id':image_id,'boxes':boxes,'labels':[str(p) for p in pred]})
            per_image.append(item)
    ref=sum(r['references'] for r in per_image);n=sum(r['candidates'] for r in per_image);matched=sum(r['matched'] for r in per_image)
    result={'references':ref,'candidates':n,'matched':matched,'precision':matched/n if n else 0,'recall':matched/ref,'f1':2*matched/(ref+n),'per_image':per_image}
    if bundle is not None:
        correct=sum(r['localized_and_correct'] for r in per_image)
        result.update(localized_and_correct=correct,joint_recall=correct/ref,joint_precision=correct/n if n else 0)
    return result,predictions

def audit(rows):
    counts={'references':len(rows),'no_predicted_foreground':0,'multiple_foreground_components':0}
    for image_id in sorted({r['image_id'] for r in rows}):
        with Image.open(ROOT/f'outputs/full_binarizer/{image_id}_mask.png') as mask:
            for r in (r for r in rows if r['image_id']==image_id):
                a=np.asarray(mask.crop(r['bbox_xyxy']).convert('L'))>127
                _,n=ndimage.label(a,structure=np.ones((3,3),int))
                counts['no_predicted_foreground']+=int(n==0)
                counts['multiple_foreground_components']+=int(n>1)
    return counts

def main():
    import joblib
    rows=json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    sites=json.loads((ROOT/'outputs/matched_mask_study/summary.json').read_text())['development_sites']
    dev=[r for r in rows if r['source_split']=='train' and re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower() in sites]
    val=[r for r in rows if r['source_split']=='val']
    assert len(dev)==308 and len(val)==300
    development={mode:evaluate(dev,mode)[0] for mode in MODES}
    # Fixed four configurations; baseline wins any exact tie. Validation is not selection input.
    selected=max(MODES,key=lambda m:development[m]['f1'])
    bundle=joblib.load(ROOT/'outputs/broad_clean_study/mask_svm_bundle.joblib')
    validation={};predictions={}
    for mode in dict.fromkeys(['none',selected]):
        validation[mode],predictions[mode]=evaluate(val,mode,bundle)
    assert validation['none']['matched']==196 and validation['none']['localized_and_correct']==52
    summary={'development':development,'development_foreground_audit':audit(dev),'selected':selected,'validation':validation,
        'protocol':'Four fixed closing configurations; select geometry F1 on 308 training-location development references. Evaluate baseline and selected variant on reused 300 validation references. Recognition uses unmodified predicted masks and frozen broad SVM. No labels or reference geometry used to propose boxes.',
        'limitations':['Filtered references omit some visible symbols.','Disconnected components are not necessarily errors: a character may naturally have several pieces.','Fixed pixel-scale morphology may merge neighboring characters.','Validation reused; enhancer pretraining overlap unresolved.','Recognition model includes development locations, so recognition was not used for development selection.']}
    out=ROOT/'outputs/component_grouping_study';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps(predictions,indent=2),encoding='utf-8')
    print(json.dumps({'development':{m:{k:v for k,v in r.items() if k!='per_image'} for m,r in development.items()},'selected':selected,'audit':summary['development_foreground_audit'],'validation':{m:{k:v for k,v in r.items() if k!='per_image'} for m,r in validation.items()}},indent=2))

if __name__=='__main__':main()
