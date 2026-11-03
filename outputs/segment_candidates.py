"""Connected-component candidates from predicted masks; not verified characters."""
import numpy as np
from scipy import ndimage
from PIL import ImageDraw

def candidates(mask):
    a=np.asarray(mask.convert('L'))>127
    labelled,n=ndimage.label(a,structure=np.ones((3,3),int))
    sizes=np.bincount(labelled.ravel());boxes=[]
    for i,slices in enumerate(ndimage.find_objects(labelled),1):
        if slices is None or sizes[i]<12:continue
        ys,xs=slices;x1,x2=xs.start,xs.stop;y1,y2=ys.start,ys.stop
        if x2-x1<3 or y2-y1<3:continue
        boxes.append([x1,y1,x2,y2])
    return sorted(boxes,key=lambda b:(b[1],b[0]))

def overlay(image,boxes):
    result=image.convert('RGB').copy();draw=ImageDraw.Draw(result)
    for i,box in enumerate(boxes,1):
        draw.rectangle(box,outline='red',width=2);draw.text((box[0],box[1]),str(i),fill='yellow')
    return result

if __name__=='__main__':
    from pathlib import Path
    import json
    from PIL import Image
    from scipy.optimize import linear_sum_assignment
    root=Path(__file__).resolve().parent.parent;out=root/'outputs/segmentation_study';out.mkdir(exist_ok=True)
    rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'));report=[]
    for image_id in sorted({r['image_id'] for r in rows if r['source_split']=='val'}):
        with Image.open(root/f'outputs/full_binarizer/{image_id}_mask.png') as mask:boxes=candidates(mask)
        gt=[r['bbox_xyxy'] for r in rows if r['image_id']==image_id]
        scores=np.zeros((len(gt),len(boxes)))
        for i,a in enumerate(gt):
            for j,b in enumerate(boxes):
                inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
                union=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter
                scores[i,j]=inter/union if union else 0
        # Maximize number of valid one-to-one matches; IoU breaks ties.
        ii,jj=linear_sum_assignment(-((scores>=.5).astype(float)*1000+scores))
        matches=int((scores[ii,jj]>=.5).sum())
        report.append({'image_id':image_id,'reference_boxes':len(gt),'candidate_boxes':len(boxes),'matched_iou_05':matches,'precision':matches/len(boxes) if boxes else 0,'recall':matches/len(gt),'boxes':boxes})
        with Image.open(root/f'outputs/full_binarizer/{image_id}_original.png') as im:overlay(im,boxes).save(out/f'{image_id}_overlay.png')
    matched=sum(r['matched_iou_05'] for r in report);pred=sum(r['candidate_boxes'] for r in report);ref=sum(r['reference_boxes'] for r in report)
    summary={'matched':matched,'candidates':pred,'references':ref,'precision':matched/pred,'recall':matched/ref,'iou_threshold':.5,'protocol':'8-connected components, area>=12,width/height>=3. Fixed rules, no tuning. One-to-one matches. References are filtered pilot boxes; excluded placeholders and unlabeled symbols can count as false positives. Binarizer training overlap unresolved.','per_image':report}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k!='per_image'},indent=2))
