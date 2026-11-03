"""Bounded broad-data CNN comparison; select using held-out training locations."""
import collections,hashlib,io,json,re,time,zipfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
import torch
from torch import nn
from train_small_cnn import CharacterCNN,predict,seed,pixels

ROOT=Path(__file__).resolve().parent.parent

def image_pixels(im):
    im=ImageOps.contain(im.convert('L'),(64,64),Image.Resampling.BILINEAR)
    canvas=Image.new('L',(64,64),0);canvas.paste(im,((64-im.width)//2,(64-im.height)//2))
    return np.asarray(canvas,dtype=np.float32)[None]/255

def fit(x,y,classes,epochs,development=None):
    seed();model=CharacterCNN(classes)
    optimizer=torch.optim.Adam(model.parameters(),lr=.001,weight_decay=.0001)
    loader=torch.utils.data.DataLoader(torch.utils.data.TensorDataset(x,y),batch_size=32,shuffle=True,num_workers=0)
    logs=[]
    for epoch in range(1,epochs+1):
        start=time.perf_counter();model.train();total=0
        for images,labels in loader:
            optimizer.zero_grad();loss=nn.functional.cross_entropy(model(images),labels)
            if not torch.isfinite(loss):raise ValueError('Non-finite loss')
            loss.backward();optimizer.step();total+=loss.item()*len(labels)
        row={'epoch':epoch,'loss':total/len(y),'seconds':time.perf_counter()-start}
        if development is not None:
            correct=predict(model,development[0])==development[1]
            row['hero_development_correct']=int(correct[development[2]].sum())
            row['all_development_correct']=int(correct.sum())
        logs.append(row);print(json.dumps(row),flush=True)
    return model,logs

def main():
    torch.set_num_threads(4);start=time.perf_counter()
    out=ROOT/'outputs/broad_cnn_study';out.mkdir(exist_ok=True)
    read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
    protocol=read('outputs/matched_mask_study/summary.json')
    site=lambda n:re.split(r'\d',n,maxsplit=1)[0].strip().lower()
    blocked=lambda n,sites:any(site(n)==s or site(n).startswith(s+' ') for s in sites)
    records=[r for r in read('outputs/training_scope_study/training_records.json') if not blocked(r['source_name'],protocol['excluded_validation_sites'])]
    assert len(records)==9925
    hero=read('work/hero_pilot/manifest.json');hero_ids={r['source_name']:r['image_id'] for r in hero}
    grouped=collections.defaultdict(list)
    for r in records:grouped[r['source_name']].append(r)
    xs=[];labels=[];dev=[];hero_flags=[]
    with zipfile.ZipFile(ROOT/'work/episam_dataset.zip') as z:
        for name,rows in sorted(grouped.items()):
            path=ROOT/'outputs/full_binarizer'/f'{hero_ids.get(name,"missing")}_mask.png'
            if not path.exists():path=ROOT/'work/broad_clean_masks'/(hashlib.sha256(name.encode()).hexdigest()+'.png')
            chars=json.loads(z.read(f'episam_dataset/chars/train/{name}/character_polygons.json'))
            with Image.open(path) as mask:
                for r in rows:
                    c=chars[r['source_key']];assert r['label']==c['char_name']
                    xs.append(image_pixels(mask.crop(c['top_left']+c['bottom_right'])))
                    labels.append(r['label']);dev.append(blocked(name,protocol['development_sites']));hero_flags.append(r['hero_filename'])
    classes=sorted(set(labels));index={c:i for i,c in enumerate(classes)}
    x=torch.from_numpy(np.stack(xs));y=torch.tensor([index[c] for c in labels]);dev=np.array(dev);hero_flags=np.array(hero_flags)
    assert len(classes)==764 and dev.sum()==359 and hero_flags[dev].sum()==308
    assert np.isfinite(x.numpy()).all()
    # Verify preprocessing parity with the previous CNN, before training.
    check=ROOT/'outputs/full_binarizer'/next(r['crop_path'] for r in hero if r['source_split']=='val')
    with Image.open(check) as im:assert np.array_equal(image_pixels(im),pixels(check))
    print('Training development CNN: 9566 fit, 359 development; budget 20 epochs',flush=True)
    model,logs=fit(x[~dev],y[~dev],len(classes),20,(x[dev],y[dev].numpy(),hero_flags[dev]))
    best=max(logs,key=lambda r:r['hero_development_correct'])
    (out/'development.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
    summary={'training_n':len(labels),'classes':len(classes),'fit_n':int((~dev).sum()),'development_n':int(dev.sum()),'hero_development_n':308,
      'best_hero_development_correct':best['hero_development_correct'],'selected_epochs':best['epoch'],'svm_hero_development_correct':63,
      'protocol':'Same broad cleaned cohort and previous 3-convolution architecture. Fixed Adam configuration, seed42, 20-epoch budget. Earliest maximum hero development correctness selects epoch. Refit/validation only if development exceeds broad SVM63/308.',
      'limitations':['Single seed and reused diagnostic validation.','Unreviewed source labels, supplied reference boxes.','Binarizer pretraining overlap unresolved.','No sequence model or translation.']}
    if best['hero_development_correct']<=63:
        summary['decision']='Do not adopt: development did not beat broad SVM. No validation evaluation or full-data refit.'
    else:
        print('Development improved; refitting all training data',flush=True)
        model,refit=fit(x,y,len(classes),best['epoch'])
        val=[r for r in hero if r['source_split']=='val']
        v=torch.from_numpy(np.stack([pixels(ROOT/'outputs/full_binarizer'/r['crop_path']) for r in val]))
        pred=predict(model,v);pred_labels=[classes[i] for i in pred]
        torch.save({'state_dict':model.state_dict(),'classes':classes,'input':'predicted_mask_64_letterbox'},out/'character_cnn.pth')
        saved=torch.load(out/'character_cnn.pth',map_location='cpu',weights_only=True)
        restored=CharacterCNN(len(classes));restored.load_state_dict(saved['state_dict'])
        assert np.array_equal(predict(restored,v),pred)
        correct=sum(p==r['label'] for r,p in zip(val,pred_labels))
        summary.update(validation_correct=correct,validation_n=len(val),validation_accuracy=correct/len(val),decision='Candidate evaluated; app unchanged pending comparison and automatic-region evaluation.')
        (out/'predictions.json').write_text(json.dumps([{'image_id':r['image_id'],'crop_path':r['crop_path'],'reference':r['label'],'prediction':p} for r,p in zip(val,pred_labels)],indent=2),encoding='utf-8')
        (out/'refit.json').write_text(json.dumps(refit,indent=2),encoding='utf-8')
    summary['seconds']=time.perf_counter()-start
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':main()
