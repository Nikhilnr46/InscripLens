"""Single-scale full-image diagnostic; no annotation-guided inference."""
from pathlib import Path
import sys,json,io,zipfile,time
import numpy as np
from PIL import Image,ImageDraw
import torch
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'work/shilalekhya'))
from Unet.model import AttentionUNet
out=root/'outputs/full_binarizer';out.mkdir(exist_ok=True)
torch.set_num_threads(4)
model=AttentionUNet(3,1,bilinear=False)
model.load_state_dict(torch.load(root/'work/shilalekhya/binarizer.pth',map_location='cpu',weights_only=True));model.eval()
records=json.loads((root/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
images={r['image_id']:r for r in records if r['source_split']=='val'}
reports=[]
with zipfile.ZipFile(root/'work/episam_dataset.zip') as z:
 for image_id,r in images.items():
  im=Image.open(io.BytesIO(z.read(r['source_path']))).convert('RGB');a=np.array(im);h,w=a.shape[:2]
  padded=np.pad(a,((0,max(0,512-h)),(0,max(0,512-w)),(0,0)),mode='edge');ph,pw=padded.shape[:2]
  def positions(n):return sorted(set(list(range(0,n-512+1,448))+[n-512]))
  total=np.zeros((ph,pw),np.float32);count=np.zeros((ph,pw),np.uint16);start=time.perf_counter();n=0
  for y in positions(ph):
   for x in positions(pw):
    t=torch.from_numpy(padded[y:y+512,x:x+512].copy()).permute(2,0,1).float().unsqueeze(0)/255
    with torch.inference_mode():p=torch.sigmoid(model(t))[0,0].numpy()
    assert np.isfinite(p).all()
    total[y:y+512,x:x+512]+=p;count[y:y+512,x:x+512]+=1;n+=1
  assert count.min()>0
  prob=(total/count)[:h,:w];mask=Image.fromarray((prob>.5).astype('uint8')*255)
  mask.save(out/f'{image_id}_mask.png');im.save(out/f'{image_id}_original.png')
  preview=im.copy();preview.thumbnail((480,700));mp=mask.convert('RGB').resize(preview.size)
  sheet=Image.new('RGB',(preview.width*2,preview.height+30),'white');sheet.paste(preview,(0,30));sheet.paste(mp,(preview.width,30));ImageDraw.Draw(sheet).text((8,8),image_id+' original / predicted mask',fill='black');sheet.save(out/f'{image_id}_comparison.png')
  report={'image_id':image_id,'source':r['source_name'],'size':[w,h],'patches':n,'seconds':time.perf_counter()-start,'foreground_fraction':float((prob>.5).mean())};reports.append(report)
  (out/'inference_summary.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
  for c in (c for c in records if c['image_id']==image_id):
   dest=out/c['crop_path'];dest.parent.mkdir(parents=True,exist_ok=True);mask.crop(c['bbox_xyxy']).save(dest)
