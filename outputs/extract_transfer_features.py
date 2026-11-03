"""Frozen ImageNet ResNet18 features; not pretrained historical Kannada OCR."""
from pathlib import Path
import json,re,time
import numpy as np
from PIL import Image,ImageOps
import torch
from torchvision.models import resnet18,ResNet18_Weights
from torchvision.transforms import functional as TF
root=Path(__file__).resolve().parent.parent;out=root/'outputs/transfer_study';out.mkdir(exist_ok=True)
torch.hub.set_dir(str(root/'work/torch_cache'));torch.set_num_threads(4)
model=resnet18(weights=ResNet18_Weights.IMAGENET1K_V1);model.fc=torch.nn.Identity();model.eval()
rows=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
protocol=json.loads((root/'outputs/matched_mask_study/summary.json').read_text())
site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
rows=[r for r in rows if r['source_split']=='val' or site(r) not in protocol['excluded_validation_sites']]
assert len(rows)==1249
(out/'records.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for name,folder in [('original',root/'work/hero_pilot'),('mask',root/'outputs/full_binarizer')]:
    features=[];start=time.perf_counter()
    for offset in range(0,len(rows),16):
        tensors=[]
        for r in rows[offset:offset+16]:
            with Image.open(folder/r['crop_path']) as im:
                im=im.convert('RGB');fill=tuple(int(v) for v in np.median(np.array(im).reshape(-1,3),axis=0))
                im=ImageOps.contain(im,(224,224),Image.Resampling.BILINEAR);canvas=Image.new('RGB',(224,224),fill);canvas.paste(im,((224-im.width)//2,(224-im.height)//2))
                tensors.append(TF.normalize(TF.to_tensor(canvas),[.485,.456,.406],[.229,.224,.225]))
        with torch.inference_mode():features.append(model(torch.stack(tensors)).numpy())
        if offset%320==0:print(name,offset,'/',len(rows),flush=True)
    x=np.concatenate(features);assert x.shape==(1249,512) and np.isfinite(x).all()
    np.save(out/f'{name}_features.npy',x);print(name,'seconds',time.perf_counter()-start,flush=True)
