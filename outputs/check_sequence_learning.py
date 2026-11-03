"""Bounded training-only CTC overfit check; not a recognition benchmark."""
import itertools
import argparse
import json
import random
import time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/sequence_data_audit'


class SequenceRecognizer(nn.Module):
    def __init__(self, classes, preserve_height=False):
        super().__init__()
        self.preserve_height=preserve_height
        self.cnn=nn.Sequential(nn.Conv2d(1,16,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
                               nn.Conv2d(16,32,3,padding=1),nn.ReLU(),nn.MaxPool2d((2,1)))
        self.rnn=nn.LSTM(32*12 if preserve_height else 32,64,bidirectional=True,batch_first=True)
        self.head=nn.Linear(128,classes)

    def forward(self,x,lengths=None):
        x=self.cnn(x)
        x=x.flatten(1,2).transpose(1,2) if self.preserve_height else x.mean(2).transpose(1,2)
        if lengths is None:
            x,_=self.rnn(x)
        else:
            packed=nn.utils.rnn.pack_padded_sequence(x,lengths.cpu(),batch_first=True,enforce_sorted=False)
            packed,_=self.rnn(packed)
            x,_=nn.utils.rnn.pad_packed_sequence(packed,batch_first=True)
        return self.head(x).log_softmax(-1).transpose(0,1)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--require-foreground',action='store_true')
    parser.add_argument('--preserve-height',action='store_true')
    parser.add_argument('--pack-lengths',action='store_true')
    parser.add_argument('--max-steps',type=int,default=300)
    args=parser.parse_args()
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
    rows=json.loads((OUT/'prepared_records.json').read_text(encoding='utf-8'))
    eligible=[r for r in rows if r['split']=='fit' and r['minimum_character_polygon_coverage']>=.95]
    if args.require_foreground:
        eligible=[r for r in eligible if r['minimum_character_foreground_pixels']>=20]
    # Fixed four shortest sequences, distinct sources, before seeing model output.
    chosen=[];seen=set()
    for r in sorted(eligible,key=lambda r:(len(r['target']),r['source_name'],r['line_number'])):
        if r['source_name'] in seen or len(r['labels'])<2:continue
        chosen.append(r);seen.add(r['source_name'])
        if len(chosen)==4:break
    alphabet=sorted(set(''.join(r['target'] for r in eligible)))
    encode={s:i+1 for i,s in enumerate(alphabet)}
    inputs=[];lengths=[]
    for r in chosen:
        with Image.open(OUT/r['crop_path']) as im:
            width=max(64,round(im.width*48/im.height))
            required=len(r['target'])+sum(a==b for a,b in zip(r['target'],r['target'][1:]))
            width=max(width,2*(required+4));width=min(width,512)
            assert width//2>=required,'CTC target cannot fit output timesteps'
            inputs.append(torch.from_numpy(np.array(im.resize((width,48)),dtype=np.float32)/255)[None])
            lengths.append(width//2)
    x=torch.zeros(len(inputs),1,48,max(t.shape[-1] for t in inputs))
    for i,t in enumerate(inputs):x[i,:,:,:t.shape[-1]]=t
    y=torch.tensor([encode[c] for r in chosen for c in r['target']],dtype=torch.long)
    target_lengths=torch.tensor([len(r['target']) for r in chosen])
    lengths=torch.tensor(lengths)
    model=SequenceRecognizer(len(alphabet)+1,args.preserve_height);opt=torch.optim.Adam(model.parameters(),lr=.003)
    criterion=nn.CTCLoss(blank=0,zero_infinity=False)
    history=[];started=time.perf_counter()
    if args.max_steps<25 or args.max_steps%25:raise ValueError('max-steps must be a positive multiple of 25')
    for step in range(1,args.max_steps+1):
        model.train();opt.zero_grad();p=model(x,lengths if args.pack_lengths else None);loss=criterion(p,y,lengths,target_lengths)
        assert torch.isfinite(loss),'Nonfinite CTC loss'
        loss.backward();nn.utils.clip_grad_norm_(model.parameters(),5);opt.step()
        if step%25==0:
            model.eval()
            with torch.inference_mode():ids=model(x,lengths if args.pack_lengths else None).argmax(-1).transpose(0,1)
            predictions=[''.join(alphabet[v-1] for v,_ in itertools.groupby(row[:n].tolist()) if v) for row,n in zip(ids,lengths)]
            exact=sum(p==r['target'] for p,r in zip(predictions,chosen))
            log={'step':step,'loss':float(loss.detach()),'training_exact':exact,'total':len(chosen)}
            history.append(log);print(json.dumps(log),flush=True)
            if exact==len(chosen):break
    result={'purpose':'training-only tiny-subset learnability check, not generalization',
            'minimum_foreground_pixels_per_character':20 if args.require_foreground else None,
            'preserve_vertical_features':args.preserve_height,
            'packed_sequence_lengths':args.pack_lengths,
            'passed':exact==len(chosen),'seconds':time.perf_counter()-started,
            'maximum_steps':args.max_steps,'history':history,'validation_used':False,'development_used':False,
            'samples':[{'source_name':r['source_name'],'line_number':r['line_number'],
                        'target':r['target'],'prediction':p} for r,p in zip(chosen,predictions)]}
    filename='overfit_foreground_check.json' if args.require_foreground else 'overfit_check.json'
    if args.preserve_height:filename=filename.replace('.json','_vertical.json')
    if args.pack_lengths:filename=filename.replace('.json','_packed.json')
    if args.max_steps!=300:filename=filename.replace('.json',f'_{args.max_steps}steps.json')
    (OUT/filename).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Training-only check passed:',result['passed'],flush=True)


if __name__=='__main__':main()
