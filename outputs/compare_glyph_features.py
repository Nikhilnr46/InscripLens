"""Predeclared crop/feature study; select only with training-site development."""
from pathlib import Path
import json,re
import numpy as np
from PIL import Image,ImageOps,ImageFilter
from sklearn.svm import SVC
import joblib
from run_character_benchmark import features as baseline

def glyph_features(image,variant):
    if variant=='baseline':return baseline(image,'median')
    im=image.convert('L').filter(ImageFilter.MedianFilter(3));a=np.array(im);ys,xs=np.where(a>127)
    if len(xs):im=im.crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
    size=32 if variant=='tight32' else 64
    im=ImageOps.contain(im,(size-4,size-4),Image.Resampling.LANCZOS);canvas=Image.new('L',(size,size),0);canvas.paste(im,((size-im.width)//2,(size-im.height)//2))
    a=np.array(canvas,dtype=np.float32)/255;gy,gx=np.gradient(a);mag=np.hypot(gx,gy);bins=(np.arctan2(gy,gx)%np.pi)*9/np.pi
    low=np.floor(bins).astype(int)%9;fraction=bins-np.floor(bins);nc=size//8;cells=np.zeros((nc,nc,9),np.float32)
    for y in range(nc):
        for x in range(nc):
            s=np.s_[y*8:y*8+8,x*8:x*8+8]
            cells[y,x]=np.bincount(low[s].ravel(),weights=(mag[s]*(1-fraction[s])).ravel(),minlength=9)+np.bincount(((low[s]+1)%9).ravel(),weights=(mag[s]*fraction[s]).ravel(),minlength=9)
    blocks=[]
    for y in range(nc-1):
        for x in range(nc-1):
            b=cells[y:y+2,x:x+2].ravel();b=b/np.sqrt(b@b+1e-6);b=np.minimum(b,.2);blocks.append(b/np.sqrt(b@b+1e-6))
    f=np.concatenate(blocks);f=f/(np.linalg.norm(f)+1e-6)
    if variant=='tight64_pixels':
        pixels=np.array(canvas.resize((16,16)),dtype=np.float32).ravel()/255;pixels/=np.linalg.norm(pixels)+1e-6;f=np.concatenate([f,pixels])
    return f

def main():
    root=Path(__file__).resolve().parent.parent;out=root/'outputs/glyph_feature_study';out.mkdir(exist_ok=True)
    rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'));protocol=json.loads((root/'outputs/matched_mask_study/summary.json').read_text())
    site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
    train=[r for r in rows if r['source_split']=='train' and site(r) not in protocol['excluded_validation_sites']];val=[r for r in rows if r['source_split']=='val']
    dev=np.array([site(r) in protocol['development_sites'] for r in train]);y=np.array([r['label'] for r in train]);truth=np.array([r['label'] for r in val]);scores={};cache={}
    def matrix(records,variant):
        result=[]
        for r in records:
            with Image.open(root/'outputs/full_binarizer'/r['crop_path']) as im:result.append(glyph_features(im,variant))
        return np.stack(result)
    for variant in ['baseline','tight32','tight64','tight64_pixels']:
        x=matrix(train,variant);cache[variant]=x;assert np.isfinite(x).all()
        model=SVC(C=10,gamma='scale');model.fit(x[~dev],y[~dev]);scores[variant]=int((model.predict(x[dev])==y[dev]).sum());print(variant,scores[variant],'/308',flush=True)
    assert scores['baseline']==50
    selected=max(scores,key=scores.get);model=SVC(C=10,gamma='scale');model.fit(cache[selected],y);v=matrix(val,selected);pred=model.predict(v)
    joblib.dump({'model':model,'variant':selected,'input_type':'predicted_mask'},out/'selected_model.joblib')
    assert np.array_equal(joblib.load(out/'selected_model.joblib')['model'].predict(v[:5]),pred[:5])
    summary={'variants_development_correct':scores,'development_n':308,'selected_variant':selected,'train_n':len(train),'validation_correct':int((pred==truth).sum()),'validation_n':len(val),'accuracy':float((pred==truth).mean()),'protocol':'Same949train and300reused validation; training-site development641/308. Four predeclared variants, fixed SVM C10. Earliest maximum development score selects variant; only winner evaluated on validation.','limitations':['Supplied reference boxes; no independent test.','Source labels unreviewed and binarizer pretraining overlap unknown.','Inspired by preprocessing/feature-fusion research, not a reproduction of published SIFT+HOG retrieval.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));(out/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'reference':r['label'],'prediction':str(p)} for r,p in zip(val,pred)],ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
