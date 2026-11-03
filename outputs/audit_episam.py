from pathlib import Path
from PIL import Image, ImageDraw
import zipfile, json, collections, hashlib, io

z=zipfile.ZipFile('work/episam_dataset.zip')
names=set(z.namelist())
images=sorted(n for n in names if '/images/' in n and n.endswith('.png'))
records=[]; labels=collections.Counter(); hashes=collections.defaultdict(list)
for n in images:
    split=n.split('/')[2]; stem=Path(n).stem
    im=Image.open(io.BytesIO(z.read(n))).convert('RGB'); im.load()
    h=hashlib.sha256(im.tobytes()).hexdigest(); hashes[h].append(n)
    cp=f'episam_dataset/chars/{split}/{stem}/character_polygons.json'
    bp=f'episam_dataset/binary_images/{split}/{stem}.png'
    chars=json.loads(z.read(cp)) if cp in names else {}
    mask=Image.open(io.BytesIO(z.read(bp))) if bp in names else None
    bad=[]; positions=collections.Counter()
    for key,c in chars.items():
        labels[str(c.get('char_name'))]+=1
        positions[(c.get('line_number'),c.get('char_number'))]+=1
        box=c.get('top_left',[])+c.get('bottom_right',[])
        if len(box)!=4 or not (0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height): bad.append(key)
    rec={'name':stem,'split':split,'width':im.width,'height':im.height,'character_count':len(chars),'char_json_present':cp in names,'binary_present':bp in names,'binary_same_size':mask is not None and mask.size==im.size,'bad_box_count':len(bad),'duplicate_line_character_positions':sum(v-1 for v in positions.values() if v>1),'hero_filename': 'hero' in stem.lower()}
    records.append(rec)
    if 'Mumennayaga' in stem:
        im.save('work/episam_aradeshanahalli.png')
        Path('work/episam_aradeshanahalli_characters.json').write_text(json.dumps(chars,ensure_ascii=False,indent=2),encoding='utf-8')
        overlay=im.copy(); d=ImageDraw.Draw(overlay)
        for key,c in chars.items():
            if c.get('line_number')==1:
                b=c['top_left']+c['bottom_right'];d.rectangle(b,outline='red',width=2)
                d.text((b[0],max(0,b[1]-12)),str(c['char_number'])+':'+str(c['char_name']),fill='yellow',stroke_width=1,stroke_fill='black')
        overlay.save('outputs/EpiSAM_Aradeshanahalli_line1_labels.png')
        print('Aradeshanahalli:',rec)
        lines=collections.defaultdict(list)
        for c in chars.values(): lines[c['line_number']].append((c['char_number'],c['char_name']))
        print('Label sequences:',json.dumps({k:sorted(v) for k,v in lines.items()}))

duplicates=[v for v in hashes.values() if len(v)>1]
binary=sorted(n for n in names if '/binary_images/' in n and n.endswith('.png'))
expected={n.replace('/images/','/binary_images/') for n in images}
summary={'archive_sha256':hashlib.file_digest(open('work/episam_dataset.zip','rb'),'sha256').hexdigest(),'image_count':len(images),'split_counts':dict(collections.Counter(x['split'] for x in records)),'hero_filename_count':sum(x['hero_filename'] for x in records),'hero_split_counts':dict(collections.Counter(x['split'] for x in records if x['hero_filename'])),'character_record_count':sum(x['character_count'] for x in records),'distinct_label_strings':len(labels),'binary_count':len(binary),'orphan_binary_paths':sorted(set(binary)-expected),'image_mask_size_mismatch_count':sum(not x['binary_same_size'] for x in records),'out_of_bounds_box_count':sum(x['bad_box_count'] for x in records),'duplicate_position_count':sum(x['duplicate_line_character_positions'] for x in records),'identical_pixel_groups':duplicates,'embedded_text_or_license_files':[n for n in names if Path(n).suffix.lower() in ['.txt','.md','.pdf','.yml','.yaml']],'label_counts':dict(labels.most_common()),'images':records}
Path('outputs/EpiSAM_archive_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('SUMMARY',json.dumps({k:v for k,v in summary.items() if k not in ['images','label_counts']},ensure_ascii=True))
print('CRC check:',z.testzip())
