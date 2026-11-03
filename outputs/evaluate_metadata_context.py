"""Bounded date/genre-prior test; excludes held-out locations from prior learning."""
from pathlib import Path
import collections,hashlib,io,json,re,zipfile
import joblib,numpy as np
from PIL import Image
from sklearn.svm import SVC
from run_character_benchmark import features
from recognition_alternatives import rank_labels

ROOT=Path(__file__).resolve().parent.parent
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
site=lambda n:re.split(r'\d',n,maxsplit=1)[0].strip().lower()
def excluded(name,sites):return any(site(name)==s or site(name).startswith(s+' ') for s in sites)
def year(name):
    match=re.search(r'\b(\d{3,4})CE\b',name)
    return int(match.group(1)) if match else None

def rerank(ranked,queries,training,mode):
    if mode=='none':return [r[0] for r in ranked]
    cache={};result=[]
    for alternatives,q in zip(ranked,queries):
        date=year(q['source_name']);hero='hero' in q['source_name'].lower();key=(date,hero)
        if date is None:result.append(alternatives[0]);continue
        if key not in cache:
            eligible=[r for r in training if year(r['source_name']) is not None and abs(year(r['source_name'])-date)<=150 and (mode=='period' or r['hero_filename']==hero)]
            cache[key]=collections.Counter(r['label'] for r in eligible)
        count=cache[key]
        # Fixed rank penalty and fixed prior weight. This is not a probability.
        scores=[-rank+.25*np.log(count[label]+1) for rank,label in enumerate(alternatives)]
        result.append(alternatives[int(np.argmax(scores))])
    return result

def main():
    protocol=read('outputs/matched_mask_study/summary.json')
    rows=sorted([r for r in read('outputs/training_scope_study/training_records.json') if not excluded(r['source_name'],protocol['excluded_validation_sites'])],key=lambda r:r['source_name'])
    assert len(rows)==9925
    hero=read('work/hero_pilot/manifest.json');ids={r['source_name']:r['image_id'] for r in hero}
    model=joblib.load(ROOT/'outputs/broad_clean_study/mask_svm_bundle.joblib')['model']
    assert [rows[i]['label'] for i in model.support_]==list(np.repeat(model.classes_,model.n_support_))
    # Stored support vectors are the original deterministic, unfitted HOG features.
    # Reconstruct the remaining training vectors from their source masks.
    x=np.empty((len(rows),324),np.float64);x[model.support_]=model.support_vectors_
    missing=sorted(set(range(len(rows)))-set(model.support_))
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as z:
        for i in missing:
            r=rows[i];name=r['source_name']
            c=json.loads(z.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))[r['source_key']]
            path=ROOT/'outputs/full_binarizer'/f'{ids.get(name,"missing")}_mask.png'
            if not path.exists():path=ROOT/'work/broad_clean_masks'/(hashlib.sha256(name.encode()).hexdigest()+'.png')
            with Image.open(path) as mask:x[i]=features(mask.crop(c['top_left']+c['bottom_right']),'median')
    assert np.isfinite(x).all()
    y=np.array([r['label'] for r in rows]);dev=np.array([excluded(r['source_name'],protocol['development_sites']) for r in rows])
    target=np.array([d and r['hero_filename'] for r,d in zip(rows,dev)])
    assert dev.sum()==359 and target.sum()==308
    fit_rows=[r for r,d in zip(rows,dev) if not d];queries=[r for r,t in zip(rows,target) if t]
    print('Fit one development classifier; no new enhancement or neural training',flush=True)
    development_model=SVC(C=10,gamma='scale',kernel='rbf').fit(x[~dev],y[~dev])
    ranked=rank_labels(development_model,x[target],3)
    modes=('none','period','period_and_genre')
    development={mode:sum(p==r['label'] for p,r in zip(rerank(ranked,queries,fit_rows,mode),queries)) for mode in modes}
    assert development['none']==63,development
    selected=max(modes,key=lambda m:development[m])
    summary={'development_n':308,'development_correct':development,'selected':selected,'period_window_years':150,'prior_weight':.25,
       'context_source':'Year and hero/non-hero type from source filenames; approximate metadata, not independently dated or classified by this project.',
       'protocol':'Fixed three-label candidate list, two fixed metadata priors and unchanged baseline. Prior counts and development SVM exclude development locations and all validation locations. Select on 308 hero development examples; no stone names or published readings used as answer hints.',
       'limitations':['This tests coarse date/genre priors, not verified historical narratives or a language model.','SVM scores and rank penalties are not calibrated probabilities.','Filename dates and categories may be approximate.','Validation reused and binarizer pretraining overlap uncertain.']}
    if selected=='none':summary['decision']='Do not adopt metadata reranking; no validation retuning. Existing validation baseline remains77/300.'
    else:
        val=[r for r in hero if r['source_split']=='val']
        v=np.stack([features(ROOT/'outputs/full_binarizer'/r['crop_path'],'median') for r in val])
        ranked=rank_labels(model,v,3);pred=rerank(ranked,val,rows,selected)
        summary['validation_n']=300;summary['validation_correct']=sum(p==r['label'] for p,r in zip(pred,val))
        summary['baseline_validation_correct']=77;summary['decision']='Evaluated candidate; no automatic app change.'
    out=ROOT/'outputs/metadata_context_study';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
