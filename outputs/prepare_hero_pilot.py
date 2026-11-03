"""Prepare a research pilot from the public EpiSAM ZIP; preserve source labels.
Run: python prepare_hero_pilot.py ARCHIVE.zip OUTPUT_DIRECTORY
Requires Pillow. Source annotations are not independently verified readings.
"""
import argparse, collections, hashlib, io, json, re, zipfile
from pathlib import Path
from PIL import Image

def prepare(archive, out):
    out.mkdir(parents=True, exist_ok=True)
    records=[]; exclusions=[]; counts=collections.Counter()
    with zipfile.ZipFile(archive) as z:
        images=sorted(n for n in z.namelist() if '/images/' in n and n.endswith('.png') and 'hero' in n.lower())
        for idx,n in enumerate(images,1):
            split=n.split('/')[2]; name=Path(n).stem; image_id=f'HS{idx:03d}'
            im=Image.open(io.BytesIO(z.read(n))).convert('RGB')
            annotations=json.loads(z.read(f'episam_dataset/chars/{split}/{name}/character_polygons.json'))
            positions=collections.Counter((c.get('line_number'),c.get('char_number')) for c in annotations.values())
            for j,(key,c) in enumerate(annotations.items(),1):
                label=c.get('char_name'); box=c.get('top_left',[])+c.get('bottom_right',[])
                reason=None
                if label is None or str(label).strip().lower() in {'','none','nan','nanl','null','unknown'}: reason='placeholder_label'
                elif positions[(c.get('line_number'),c.get('char_number'))]>1: reason='duplicate_line_character_position'
                elif len(box)!=4 or not(0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height): reason='invalid_box'
                if reason:
                    exclusions.append({'image_id':image_id,'source_key':key,'reason':reason,'source_label':label});continue
                crop=im.crop(tuple(box)); rel=Path('crops')/split/f'{image_id}_{j:04d}.png'
                (out/rel).parent.mkdir(parents=True,exist_ok=True);crop.save(out/rel)
                records.append({'image_id':image_id,'source_name':name,'source_path':n,'source_key':key,'source_split':split,'label':label,'line_number':c.get('line_number'),'char_number':c.get('char_number'),'bbox_xyxy':box,'crop_path':rel.as_posix(),'pixel_sha256':hashlib.sha256(str(crop.size).encode()+crop.tobytes()).hexdigest(),'status':'source_annotation_unreviewed'})
            counts[split]+=1
    train=collections.Counter(r['label'] for r in records if r['source_split']=='train')
    val=collections.Counter(r['label'] for r in records if r['source_split']=='val')
    th={r['pixel_sha256'] for r in records if r['source_split']=='train'}
    overlap=[r['crop_path'] for r in records if r['source_split']=='val' and r['pixel_sha256'] in th]
    summary={'source_images':len(images),'source_image_splits':dict(counts),'usable_crop_count':len(records),'crop_splits':dict(collections.Counter(r['source_split'] for r in records)),'exclusion_reasons':dict(collections.Counter(r['reason'] for r in exclusions)),'train_classes':len(train),'val_classes':len(val),'shared_classes':len(set(train)&set(val)),'validation_samples_with_unseen_label':sum(v for k,v in val.items() if k not in train),'train_classes_with_at_least_5_examples':sum(v>=5 for v in train.values()),'exact_cross_split_crop_duplicates':overlap,'limitations':['Filename-selected hero-stone subset; identities and multi-view grouping require review.','Original train/val split is preserved; val is not a new untouched test set.','Raw transliteration-like labels retained; no automatic conversion to Kannada.','Cropping from supplied boxes evaluates recognition with supplied segmentation, not end-to-end OCR.','Published annotations may contain mistakes; excluded placeholders are logged.']}
    (out/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'exclusions.json').write_text(json.dumps(exclusions,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all((out/r['crop_path']).is_file() for r in records)
    assert len(records)+len(exclusions)==1428, 'Source version differs: review counts before proceeding.'
    print(json.dumps(summary,ensure_ascii=True,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('output',type=Path);a=p.parse_args();prepare(a.archive,a.output)
