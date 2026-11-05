"""Fixed initial 10-epoch sequence experiment; no validation-stone access."""
import json,random,time,itertools
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from check_sequence_learning import SequenceRecognizer
from ctc_prefix_decode import decode
from evaluate_mozhi_printed import distance
ROOT=Path(__file__).resolve().parent.parent


def main():
    random.seed(42);np.random.seed(42);torch.manual_seed(42);torch.set_num_threads(4)
    folder=ROOT/'outputs/paired_line_data';out=ROOT/'outputs/screened_sequence_study';out.mkdir(exist_ok=True)
    rows=[r for r in json.loads((folder/'records.json').read_text(encoding='utf-8')) if r['eligible']]
    fit=[r for r in rows if r['split']=='fit'];dev=[r for r in rows if r['split']=='development']
    assert len(fit)==124 and len(dev)==7
    assert not {r['source_name'] for r in fit}&{r['source_name'] for r in dev}
    alphabet=sorted(set(''.join(r['target'] for r in fit)));enc={c:i+1 for i,c in enumerate(alphabet)}
    assert set(''.join(r['target'] for r in dev))<=set(alphabet)
    for r in rows:
        with Image.open(folder/r['mask_crop']) as im:
            # Image-only sizing, including development; targets never affect input width.
            w=min(1024,max(256,round(im.width*48/im.height)))
            r['tensor']=torch.from_numpy(np.asarray(im.convert('L').resize((w,48)),dtype=np.float32)/255)[None]
            r['steps']=w//2
        required=len(r['target'])+sum(a==b for a,b in zip(r['target'],r['target'][1:]))
        assert r['steps']>=required,(r['source_name'],r['line_number'],'CTC capacity')
    def batch(rs):
        x=torch.zeros(len(rs),1,48,max(r['tensor'].shape[-1] for r in rs))
        for i,r in enumerate(rs):x[i,:,:,:r['tensor'].shape[-1]]=r['tensor']
        return x,torch.tensor([r['steps'] for r in rs])
    model=SequenceRecognizer(len(alphabet)+1,True);opt=torch.optim.Adam(model.parameters(),lr=.003)
    loss_fn=torch.nn.CTCLoss(blank=0,zero_infinity=False);logs=[];start=time.perf_counter()
    for epoch in range(1,11):
        model.train();order=list(fit);random.shuffle(order);loss_sum=0
        for j in range(0,len(order),4):
            rs=order[j:j+4];x,lengths=batch(rs)
            y=torch.tensor([enc[c] for r in rs for c in r['target']]);yl=torch.tensor([len(r['target']) for r in rs])
            opt.zero_grad();loss=loss_fn(model(x,lengths),y,lengths,yl)
            assert torch.isfinite(loss);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5);opt.step();loss_sum+=float(loss.detach())*len(rs)
        log=dict(epoch=epoch,training_loss=loss_sum/len(fit),elapsed_seconds=time.perf_counter()-start);logs.append(log);print(json.dumps(log),flush=True)
    model.eval();reports={};predictions=[]
    for split,group in [('fit',fit),('development',dev)]:
        edits=0;chars=0;exact=0;beam_edits=0;beam_exact=0
        for r in group:
            x,lengths=batch([r])
            with torch.inference_mode():lp=model(x,lengths)[:,0].numpy()
            greedy=''.join(alphabet[c-1] for c,_ in itertools.groupby(lp.argmax(1)) if c)
            beam=''.join(alphabet[c-1] for c in decode(lp,10)) if split=='development' else None
            edits+=distance(r['target'],greedy);chars+=len(r['target']);exact+=greedy==r['target']
            if beam is not None:beam_edits+=distance(r['target'],beam);beam_exact+=beam==r['target']
            predictions.append(dict(split=split,source_name=r['source_name'],line_number=r['line_number'],target=r['target'],greedy=greedy,beam=beam))
        reports[split]=dict(lines=len(group),reference_codepoints=chars,greedy_exact=exact,greedy_edits=edits,greedy_cer=edits/chars)
        if split=='development':reports[split].update(beam_exact=beam_exact,beam_edits=beam_edits,beam_cer=beam_edits/chars)
    summary=dict(reports=reports,history=logs,epochs=10,seed=42,seconds=time.perf_counter()-start,validation_used=False,production_model_changed=False,
        protocol='Fixed initial ten epochs, batch4, Adam .003, packed vertical CNN-BiLSTM-CTC; alphabet from fit only; image-only height48 width256..1024. Final checkpoint evaluated once, no development checkpoint selection.',
        limitations=['Supplied annotation-assisted line crops and unverified source labels.','Only seven development lines.','Roman codepoint error includes label separators; not modern Kannada OCR.','Ten epochs is a diagnostic budget, not convergence or impossibility evidence.'])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'predictions.json').write_text(json.dumps(predictions,ensure_ascii=False,indent=2),encoding='utf-8')
    torch.save(dict(state_dict=model.state_dict(),alphabet=alphabet),out/'sequence_model.pth')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()

