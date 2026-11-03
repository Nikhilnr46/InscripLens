"""Bounded learned-feature baseline; epoch selection on training-only sites."""
import json,re,time,random
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
import torch
from torch import nn
ROOT=Path(__file__).resolve().parent.parent

class CharacterCNN(nn.Module):
    def __init__(self,classes):
        super().__init__()
        self.layers=nn.Sequential(nn.Conv2d(1,16,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),nn.Conv2d(16,32,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),nn.Conv2d(32,64,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),nn.Flatten(),nn.Linear(64*8*8,128),nn.ReLU(),nn.Dropout(.2),nn.Linear(128,classes))
    def forward(self,x):return self.layers(x)

def pixels(path):
    with Image.open(path) as im:
        im=ImageOps.contain(im.convert('L'),(64,64),Image.Resampling.BILINEAR)
        canvas=Image.new('L',(64,64),0);canvas.paste(im,((64-im.width)//2,(64-im.height)//2))
        return np.array(canvas,dtype=np.float32)[None]/255

def seed():
    random.seed(42);np.random.seed(42);torch.manual_seed(42)

def predict(model,x):
    model.eval()
    with torch.inference_mode():return torch.cat([model(b).argmax(1) for b in x.split(64)]).numpy()

def fit(x,y,classes,epochs,dev=None):
    seed();model=CharacterCNN(classes);optimizer=torch.optim.Adam(model.parameters(),lr=.001,weight_decay=.0001)
    loader=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y),batch_size=32,shuffle=True,num_workers=0)
    logs=[]
    for epoch in range(1,epochs+1):
        model.train();loss_sum=0
        for images,labels in loader:
            optimizer.zero_grad();loss=nn.functional.cross_entropy(model(images),labels)
            if not torch.isfinite(loss):raise ValueError('Non-finite training loss')
            loss.backward();optimizer.step();loss_sum+=loss.item()*len(labels)
        row={'epoch':epoch,'train_loss':loss_sum/len(y)}
        if dev is not None:row['dev_correct']=int((predict(model,dev[0])==dev[1]).sum())
        logs.append(row)
        if epoch%5==0:print(json.dumps(row),flush=True)
    return model,logs

def main():
    torch.set_num_threads(4);start=time.perf_counter()
    out=ROOT/'outputs/cnn_study';out.mkdir(exist_ok=True)
    rows=json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    site=lambda r:re.split(r'\d',r['source_name'],maxsplit=1)[0].strip().lower()
    protocol=json.loads((ROOT/'outputs/matched_mask_study/summary.json').read_text())
    train=[r for r in rows if r['source_split']=='train' and site(r) not in protocol['excluded_validation_sites']]
    val=[r for r in rows if r['source_split']=='val'];devsites=set(protocol['development_sites'])
    classes=sorted({r['label'] for r in train});index={c:i for i,c in enumerate(classes)}
    x=torch.from_numpy(np.stack([pixels(ROOT/'outputs/full_binarizer'/r['crop_path']) for r in train]));y=torch.tensor([index[r['label']] for r in train])
    dev=np.array([site(r) in devsites for r in train]);assert dev.sum()==308 and len(train)==949
    assert {site(r) for r,d in zip(train,dev) if d}.isdisjoint(site(r) for r,d in zip(train,dev) if not d)
    model,logs=fit(x[~dev],y[~dev],len(classes),30,(x[dev],y[dev].numpy()))
    best=max(logs,key=lambda r:r['dev_correct']);epochs=best['epoch']
    (out/'development.json').write_text(json.dumps(logs,indent=2))
    print('Refitting all training crops for',epochs,'epochs',flush=True)
    model,refit=fit(x,y,len(classes),epochs)
    v=torch.from_numpy(np.stack([pixels(ROOT/'outputs/full_binarizer'/r['crop_path']) for r in val]))
    pred=predict(model,v);truth=[r['label'] for r in val];labels=[classes[i] for i in pred]
    checkpoint=out/'character_cnn.pth';torch.save({'state_dict':model.state_dict(),'classes':classes,'input':'predicted_mask_64_letterbox'},checkpoint)
    saved=torch.load(checkpoint,map_location='cpu',weights_only=True);restored=CharacterCNN(len(saved['classes']));restored.load_state_dict(saved['state_dict']);assert np.array_equal(predict(restored,v[:5]),pred[:5])
    summary={'model':'Small three-convolution CNN trained from scratch','training_n':len(train),'classes':len(classes),'development_n':int(dev.sum()),'development_best_correct':best['dev_correct'],'selected_epochs':epochs,'validation_correct':sum(a==b for a,b in zip(truth,labels)),'validation_n':len(val),'validation_accuracy':sum(a==b for a,b in zip(truth,labels))/len(val),'unseen_validation_labels_n':sum(t not in index for t in truth),'seconds':time.perf_counter()-start,'seed':42,'torch':torch.__version__,'protocol':'Same excluded-site949 training crops and300 validation crops as matched SVM. Epoch budget30; earliest maximum development correctness selects refit duration. Architecture/optimizer fixed before validation. No pretrained recognition backbone.','limitations':['Validation reused; not fresh final test.','Pretrained binarizer training overlap incompletely known.','Source labels unreviewed; supplied boxes used.','Single seed and small training set; this does not rule out stronger pretrained recognition models.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    (out/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':p} for r,p in zip(val,labels)],ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
