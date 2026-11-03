"""Reusable CPU inference for the attributed Shilalekhya checkpoint."""
from pathlib import Path
import sys, argparse, json, time
import numpy as np
from PIL import Image, ImageOps
import torch
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'work/shilalekhya'))
from Unet.model import AttentionUNet

def load_model(device='cpu'):
    torch.set_num_threads(4)
    model=AttentionUNet(3,1,bilinear=False)
    model.load_state_dict(torch.load(ROOT/'work/shilalekhya/binarizer.pth',map_location='cpu',weights_only=True),strict=True)
    return model.to(device).eval()

def enhance(image, model):
    device=next(model.parameters()).device
    image=ImageOps.exif_transpose(image).convert('RGB')
    a=np.array(image); h,w=a.shape[:2]
    padded=np.pad(a,((0,max(0,512-h)),(0,max(0,512-w)),(0,0)),mode='edge')
    ph,pw=padded.shape[:2]
    def positions(n):return sorted(set(list(range(0,n-512+1,448))+[n-512]))
    total=np.zeros((ph,pw),np.float32);count=np.zeros((ph,pw),np.uint16)
    for y in positions(ph):
        for x in positions(pw):
            t=torch.from_numpy(padded[y:y+512,x:x+512].copy()).permute(2,0,1).float().unsqueeze(0)/255
            with torch.inference_mode():p=torch.sigmoid(model(t.to(device)))[0,0].cpu().numpy()
            if not np.isfinite(p).all():raise ValueError('Non-finite model output')
            total[y:y+512,x:x+512]+=p;count[y:y+512,x:x+512]+=1
    assert count.min()>0
    return Image.fromarray(((total/count)[:h,:w]>.5).astype('uint8')*255)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('input',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    start=time.perf_counter()
    with Image.open(args.input) as im:result=enhance(im,load_model())
    args.output.parent.mkdir(parents=True,exist_ok=True);result.save(args.output)
    print(json.dumps({'seconds':time.perf_counter()-start,'size':result.size,'method':'single_scale_pretrained_binarization'}))
