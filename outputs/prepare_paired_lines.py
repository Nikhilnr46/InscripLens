"""Training-only paired line crops with explicit geometry repair and contamination audit.

These use supplied annotations: they are not automatically localized OCR inputs.
No labels are corrected or inferred, and no validation images are accessed.
"""
import collections, hashlib, io, json, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from prepare_sequence_crops import ROOT, OUT
from evaluate_metadata_context import excluded


def main():
    previous=json.loads((OUT/'prepared_records.json').read_text(encoding='utf-8'))
    protocol=json.loads((ROOT/'outputs/matched_mask_study/summary.json').read_text())
    assert all(not excluded(r['source_name'],protocol['excluded_validation_sites']) for r in previous)
    assert all(r['split'] in ('fit','development') for r in previous)
    assert not {r['source_name'] for r in previous if r['split']=='fit'} & {r['source_name'] for r in previous if r['split']=='development'}
    dest=ROOT/'outputs/paired_line_data';dest.mkdir(exist_ok=True)
    crops=dest/'crops';crops.mkdir(exist_ok=True)
    groups=collections.defaultdict(list)
    for r in previous:groups[r['source_name']].append(r)
    records=[]
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as archive:
        for name,rows in groups.items():
            chars=json.loads(archive.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
            with Image.open(io.BytesIO(archive.read(f'episam_dataset/images/train/{name}.png'))) as image, Image.open(ROOT/rows[0]['mask_path']) as mask:
                raw=image.convert('RGB');binary=mask.convert('L')
                assert raw.size==binary.size
                for r in rows:
                    keys=set(r['source_keys'])
                    polygons=[r['line_polygon']]+[chars[k]['polygon_original'] for k in r['source_keys']]
                    points=[p for polygon in polygons for p in polygon]
                    box=[max(0,min(p[0] for p in points)-4),max(0,min(p[1] for p in points)-4),min(raw.width,max(p[0] for p in points)+5),min(raw.height,max(p[1] for p in points)+5)]
                    size=(box[2]-box[0],box[3]-box[1])
                    def region(polygon):
                        im=Image.new('L',size,0)
                        ImageDraw.Draw(im).polygon([(p[0]-box[0],p[1]-box[1]) for p in polygon],fill=255)
                        return np.asarray(im)>0
                    support=np.logical_or.reduce([region(p) for p in polygons])
                    bm=np.asarray(binary.crop(box));foreground=[];coverage=[]
                    for k in r['source_keys']:
                        p=chars[k]['polygon_original'];cm=region(p)
                        foreground.append(int(((bm>127)&cm&support).sum()))
                        coverage.append(float((cm&support).sum()/max(1,cm.sum())))
                    overlaps=[]
                    for k,c in chars.items():
                        if k in keys:continue
                        p=c['polygon_original']
                        if max(q[0] for q in p)<box[0] or min(q[0] for q in p)>=box[2] or max(q[1] for q in p)<box[1] or min(q[1] for q in p)>=box[3]:continue
                        # Denominator is the whole neighbouring polygon, not its clipped crop.
                        xs=[q[0] for q in p];ys=[q[1] for q in p]
                        full=Image.new('L',(max(xs)-min(xs)+1,max(ys)-min(ys)+1),0)
                        ImageDraw.Draw(full).polygon([(q[0]-min(xs),q[1]-min(ys)) for q in p],fill=255)
                        fraction=float((region(p)&support).sum()/max(1,np.count_nonzero(full)))
                        if fraction:overlaps.append({'source_key':k,'fraction':fraction})
                    key=hashlib.sha256(f'{name}|{r["line_number"]}'.encode()).hexdigest()[:20]
                    selection=Image.fromarray((support*255).astype('uint8'))
                    Image.composite(raw.crop(box),Image.new('RGB',size,(127,127,127)),selection).save(crops/f'{key}_original.png')
                    Image.fromarray(np.where(support,bm,0).astype('uint8')).save(crops/f'{key}_mask.png')
                    old_ok=r['minimum_character_polygon_coverage']>=.95 and r['minimum_character_foreground_pixels']>=20
                    flags=[]
                    if min(foreground)<20:flags.append('sparse_predicted_mask')
                    if any(o['fraction']>.05 for o in overlaps):flags.append('neighbour_annotation_overlap')
                    if any(not (0<=p[0]<raw.width and 0<=p[1]<raw.height) for p in points):flags.append('polygon_outside_image')
                    records.append(dict(source_name=name,line_number=r['line_number'],split=r['split'],target=r['target'],source_keys=r['source_keys'],
                        bbox_xyxy=box,original_crop=f'crops/{key}_original.png',mask_crop=f'crops/{key}_mask.png',
                        previous_eligible=old_ok,previous_minimum_coverage=r['minimum_character_polygon_coverage'],
                        minimum_visible_coverage=min(coverage),character_foreground_pixels=foreground,
                        neighbour_overlaps=overlaps,flags=flags,eligible=not flags))
    summary={s:dict(total=sum(r['split']==s for r in records),previous_eligible=sum(r['split']==s and r['previous_eligible'] for r in records),
        eligible=sum(r['split']==s and r['eligible'] for r in records),newly_eligible=sum(r['split']==s and r['eligible'] and not r['previous_eligible'] for r in records),
        previously_eligible_now_flagged=sum(r['split']==s and not r['eligible'] and r['previous_eligible'] for r in records),
        flags=dict(collections.Counter(f for r in records if r['split']==s for f in r['flags']))) for s in ['fit','development']}
    summary.update(protocol='Union of supplied line polygon and its supplied character polygons; preserve original RGB and predicted mask. Reject any annotated neighbour overlap >5%, out-of-image polygon, or any character with <20 foreground pixels. Fixed geometry/quality thresholds, no model-result selection.',
        limitations=['Annotation-assisted localization, not inference-time segmentation.','Labels remain unverified Roman dataset strings with | separators.',
        'Unannotated neighbours and missing characters cannot be detected by this audit.','Geometry repair cannot recover strokes absent from the predicted mask.'],validation_used=False)
    (dest/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    chosen=[];seen=set()
    for r in records:
        if r['eligible'] and not r['previous_eligible'] and r['source_name'] not in seen:
            chosen.append(r);seen.add(r['source_name'])
        if len(chosen)==6:break
    canvas=Image.new('RGB',(1200,max(1,len(chosen))*230),'white');draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(chosen):
        draw.text((8,i*230+4),f'{r["split"]}: {r["source_name"][:105]} / line {r["line_number"]}',fill='black')
        for j,field in enumerate(['original_crop','mask_crop']):
            with Image.open(dest/r[field]) as im:canvas.paste(ImageOps.contain(im.convert('RGB'),(1180,95)),(10,i*230+25+j*100))
    canvas.save(dest/'repair_contact_sheet.png')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
