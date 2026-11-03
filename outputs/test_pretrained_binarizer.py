"""Bounded CPU compatibility test, not reproduction of multi-scale refinement."""
import sys, json, io, time, hashlib, zipfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import torch

root=Path(__file__).resolve().parent.parent
vendor=root/'work/shilalekhya'
sys.path.insert(0,str(vendor))
from Unet.model import AttentionUNet

out=root/'outputs/pretrained_binarizer_test';out.mkdir(exist_ok=True)
torch.set_num_threads(4)
model=AttentionUNet(in_channels=3,out_classes=1,bilinear=False)
weights=vendor/'binarizer.pth'
state=torch.load(weights,map_location='cpu',weights_only=True)
model.load_state_dict(state,strict=True);model.eval()
manifest=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
row=next(r for r in manifest if r['source_split']=='val' and r['source_name'].startswith('Nagavara'))
with zipfile.ZipFile(root/'work/episam_dataset.zip') as z:
    original=Image.open(io.BytesIO(z.read(row['source_path']))).convert('RGB')
# Fixed centre patch independent of annotation boxes or predictions.
side=min(512,original.width,original.height)
x=(original.width-side)//2;y=(original.height-side)//2
patch=original.crop((x,y,x+side,y+side)).resize((512,512),Image.Resampling.BILINEAR)
tensor=torch.from_numpy(np.array(patch).copy()).permute(2,0,1).float().unsqueeze(0)/255
start=time.perf_counter()
with torch.inference_mode(): prob=torch.sigmoid(model(tensor))[0,0].numpy()
elapsed=time.perf_counter()-start
assert prob.shape==(512,512) and np.isfinite(prob).all()
mask=Image.fromarray((prob>0.5).astype('uint8')*255)
patch.save(out/'input_patch.png');mask.save(out/'predicted_mask.png')
sheet=Image.new('RGB',(1024,548),'white');sheet.paste(patch,(0,36));sheet.paste(mask.convert('RGB'),(512,36))
d=ImageDraw.Draw(sheet);d.text((12,10),'Nagavara: fixed centre patch',fill='black');d.text((524,10),'Pretrained predicted mask (white = foreground)',fill='black')
sheet.save(out/'comparison.png')
report={'source':row['source_name'],'crop_xyxy':[x,y,x+side,y+side],'input_size':[512,512],'device':'cpu','torch':torch.__version__,'strict_weights_load':True,'seconds':elapsed,'foreground_fraction':float((prob>0.5).mean()),'probability_range':[float(prob.min()),float(prob.max())],'checkpoint_sha256':hashlib.sha256(weights.read_bytes()).hexdigest(),'protocol':'One fixed centre patch, RGB 0..1, sigmoid threshold 0.5. No annotation mask input. Not full multi-scale/refinement inference. No OCR accuracy evaluation. Nagavara appears in upstream test list; upstream train list empty, so complete overlap audit impossible.'}
(out/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)
