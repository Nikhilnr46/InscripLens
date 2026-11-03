"""Generate predicted masks for training images; validation masks already saved."""
import json,io,zipfile,time
from PIL import Image
from binarizer_core import ROOT,load_model,enhance
rows=json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
out=ROOT/'outputs/full_binarizer';model=load_model()
images={r['image_id']:r for r in rows if r['source_split']=='train'}
with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as z:
    for image_id,r in images.items():
        path=out/f'{image_id}_mask.png';start=time.perf_counter()
        if not path.exists():
            with Image.open(io.BytesIO(z.read(r['source_path']))) as im:mask=enhance(im,model)
            mask.save(path)
        else:mask=Image.open(path)
        for c in (c for c in rows if c['image_id']==image_id):
            dest=out/c['crop_path'];dest.parent.mkdir(parents=True,exist_ok=True);mask.crop(c['bbox_xyxy']).save(dest)
        print(image_id,round(time.perf_counter()-start,2),'seconds',flush=True)
