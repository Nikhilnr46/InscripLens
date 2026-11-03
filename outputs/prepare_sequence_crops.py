"""Export candidate line rectangles from existing masks with provenance."""
import hashlib
import json
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'outputs/sequence_data_audit'


def main():
    records = json.loads((OUT/'records.json').read_text(encoding='utf-8'))
    hero = json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    ids = {r['source_name']: r['image_id'] for r in hero}
    crops = OUT/'crops'; crops.mkdir(exist_ok=True)
    exported = []
    archive = zipfile.ZipFile(ROOT/'work/episam_dataset.zip')
    character_cache = {}
    for r in records:
        if r['flags']: continue
        name = r['source_name']
        if name not in character_cache:
            character_cache[name]=json.loads(archive.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
        mask = ROOT/'outputs/full_binarizer'/f'{ids.get(name,"missing")}_mask.png'
        if not mask.is_file(): mask = ROOT/'work/broad_clean_masks'/(hashlib.sha256(name.encode()).hexdigest()+'.png')
        polygon = r['line_polygon']
        with Image.open(mask) as im:
            box = [max(0,min(p[0] for p in polygon)-4),max(0,min(p[1] for p in polygon)-4),
                   min(im.width,max(p[0] for p in polygon)+5),min(im.height,max(p[1] for p in polygon)+5)]
            crop = im.convert('L').crop(box)
            region = Image.new('L',crop.size,0)
            ImageDraw.Draw(region).polygon([(p[0]-box[0],p[1]-box[1]) for p in polygon],fill=255)
            crop = ImageChops.multiply(crop,region)
            coverage=[]
            for source_key in r['source_keys']:
                c=character_cache[name][source_key]
                points=c['polygon_original']
                x0=min(p[0] for p in points);y0=min(p[1] for p in points)
                x1=max(p[0] for p in points)+1;y1=max(p[1] for p in points)+1
                cm=Image.new('L',(x1-x0,y1-y0),0)
                ImageDraw.Draw(cm).polygon([(p[0]-x0,p[1]-y0) for p in points],fill=255)
                lm=Image.new('L',cm.size,0)
                ImageDraw.Draw(lm).polygon([(p[0]-x0,p[1]-y0) for p in polygon],fill=255)
                area=sum(cm.histogram()[1:])
                coverage.append(sum(ImageChops.multiply(cm,lm).histogram()[1:])/max(area,1))
            key = hashlib.sha256(f'{name}|{r["line_number"]}'.encode()).hexdigest()[:20]
            crop.save(crops/f'{key}.png')
            exported.append({**r,'crop_path': f'crops/{key}.png','bbox_xyxy':box,
                             'width':crop.width,'height':crop.height,
                             'minimum_character_polygon_coverage':min(coverage),
                             'target':'|'.join(r['labels']),
                             'mask_path':mask.relative_to(ROOT).as_posix(),
                             'localization':'supplied line polygon; neighboring pixels zeroed'})
    (OUT/'prepared_records.json').write_text(json.dumps(exported,ensure_ascii=False,indent=2),encoding='utf-8')
    audit={s:{'candidate_lines':sum(r['split']==s for r in exported),
              'lines_with_every_character_polygon_at_least_95_percent_inside':sum(r['split']==s and r['minimum_character_polygon_coverage']>=.95 for r in exported)} for s in ['fit','development']}
    audit['note']='Polygon geometry agreement only, not proof of complete or correct transcription.'
    (OUT/'crop_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    archive.close()
    # Deterministic varied sample: first source per split, then each next distinct source.
    sample=[]
    for split in ['fit','development']:
        seen=set()
        for r in exported:
            if r['split']!=split or r['source_name'] in seen: continue
            seen.add(r['source_name']); sample.append(r)
            if len(seen)==4:break
    canvas=Image.new('RGB',(1200, len(sample)*170),'white');draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(sample):
        draw.text((8,i*170+5),f'{i+1}. {r["split"]} / {r["source_name"]} / line {r["line_number"]}',fill='black')
        with Image.open(OUT/r['crop_path']) as im:
            im=ImageOps.contain(im.convert('RGB'),(1180,130));canvas.paste(im,(10,i*170+30))
    canvas.save(OUT/'sample_contact_sheet.png')
    (OUT/'sample_records.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Exported {len(exported)} crops; sample contains {len(sample)} lines.')
    print(json.dumps(audit))


if __name__=='__main__':main()
