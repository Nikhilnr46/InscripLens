"""Create source-linked review examples from the trained SVM's support vectors."""
from pathlib import Path
import collections,hashlib,io,json,re,zipfile
import joblib,numpy as np
from PIL import Image
from run_character_benchmark import features
from recognition_alternatives import rank_labels

ROOT=Path(__file__).resolve().parent.parent
read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
hero=read('work/hero_pilot/manifest.json');ids={r['source_name']:r['image_id'] for r in hero}
blocked=read('outputs/matched_mask_study/summary.json')['excluded_validation_sites']
def excluded(name):
    group=re.split(r'\d',name,maxsplit=1)[0].strip().lower()
    return any(group==s or group.startswith(s+' ') for s in blocked)
rows=sorted([r for r in read('outputs/training_scope_study/training_records.json') if not excluded(r['source_name'])],key=lambda r:r['source_name'])
assert len(rows)==9925
model_path=ROOT/'outputs/broad_clean_study/mask_svm_bundle.joblib'
model=joblib.load(model_path)['model']
expected=np.repeat(model.classes_,model.n_support_)
assert [rows[i]['label'] for i in model.support_]==list(expected)
grouped=collections.defaultdict(list)
for support_index,original_index in enumerate(model.support_):grouped[rows[original_index]['source_name']].append((support_index,rows[original_index]))
library=ROOT/'outputs/recognition_references.zip';records=[]
with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as source,zipfile.ZipFile(library,'w',compression=zipfile.ZIP_DEFLATED) as output:
    for name,items in sorted(grouped.items()):
        path=ROOT/'outputs/full_binarizer'/f'{ids.get(name,"missing")}_mask.png'
        if not path.exists():path=ROOT/'work/broad_clean_masks'/(hashlib.sha256(name.encode()).hexdigest()+'.png')
        annotations=json.loads(source.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
        with Image.open(path) as mask:
            for i,r in items:
                c=annotations[r['source_key']];box=c['top_left']+c['bottom_right'];crop=mask.crop(box)
                assert np.allclose(features(crop,'median'),model.support_vectors_[i],rtol=0,atol=1e-7)
                blob=io.BytesIO();crop.save(blob,format='PNG');filename=f'glyphs/{i:05}.png';output.writestr(filename,blob.getvalue())
                records.append({'support_index':i,'label':r['label'],'source_name':name,'source_key':r['source_key'],'bbox_xyxy':box,'image_path':filename,'source_split':'train','verified_by_project':False})
    output.writestr('index.json',json.dumps({'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'examples':records,'attribution':'EpiSAM authors; imagery acknowledged to The Mythic Society Bengaluru. Masks generated with Shilalekhya. CC BY-SA 4.0; see THIRD_PARTY.md.'},ensure_ascii=False))
    output.write(ROOT/'THIRD_PARTY.md','THIRD_PARTY.md')
with zipfile.ZipFile(library) as z:assert z.testzip() is None
val=[r for r in hero if r['source_split']=='val']
x=np.stack([features(ROOT/'outputs/full_binarizer'/r['crop_path'],'median') for r in val])
ranked=rank_labels(model,x,5)
result={'validation_n':len(val),'reference_label_in_suggestions':{str(k):sum(r['label'] in a[:k] for r,a in zip(val,ranked)) for k in (1,3,5)},'training_reference_examples':len(records),'library_bytes':library.stat().st_size,
    'protocol':'Preserve SVM top-1 prediction, rank remaining labels by its uncalibrated decision scores. Examples are nearest training support vectors within each proposed label, using the existing HOG feature distance. No validation examples enter the reference library.',
    'limitations':['Top-k inclusion is not automatic transcription accuracy or reviewer success.','Reference examples inherit unverified source labels.','Reused validation and uncertain enhancer pretraining overlap.','Visual similarity is not proof of character identity.']}
assert result['reference_label_in_suggestions']['1']==77
out=ROOT/'outputs/review_alternatives_study';out.mkdir(exist_ok=True)
(out/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
