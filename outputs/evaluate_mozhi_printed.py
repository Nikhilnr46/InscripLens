"""Fixed 100-word printed Kannada diagnostic, separate from inscription OCR."""
import hashlib,json,shutil,subprocess,unicodedata,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent


def distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]


def main():
    exe=shutil.which('tesseract')
    if not exe:raise SystemExit('Tesseract with kan traineddata is required')
    archive=ROOT/'work/mozhi_kannada/test.zip';out=ROOT/'outputs/mozhi_printed_study';out.mkdir(exist_ok=True)
    crops=ROOT/'work/mozhi_kannada/evaluation';crops.mkdir(exist_ok=True)
    results=[]
    with zipfile.ZipFile(archive) as z:
        rows=[line.split('\t',1) for line in z.read('test/test_gt.txt').decode('utf-8-sig').splitlines() if line.strip()]
        assert len({name for name,_ in rows})==len(rows)
        selected=sorted(rows,key=lambda r:hashlib.sha256(r[0].encode()).hexdigest())[:100]
        for i,(name,truth) in enumerate(selected,1):
            path=crops/Path(name).name;data=z.read('test/'+name);path.write_bytes(data)
            run=subprocess.run([exe,str(path),'stdout','-l','kan','--oem','1','--psm','8'],capture_output=True,encoding='utf-8',check=True,timeout=60)
            truth=unicodedata.normalize('NFC',truth.strip());prediction=unicodedata.normalize('NFC',run.stdout.strip())
            results.append(dict(source_path=name,reference=truth,prediction=prediction,edits=distance(truth,prediction),reference_codepoints=len(truth),exact=truth==prediction,image_sha256=hashlib.sha256(data).hexdigest()))
            if i%25==0:print(f'Processed {i}/100',flush=True)
    edits=sum(r['edits'] for r in results);chars=sum(r['reference_codepoints'] for r in results)
    summary=dict(dataset='Mozhi-Kannada published test split',available_test_pairs=len(rows),evaluated_words=len(results),exact_words=sum(r['exact'] for r in results),
        total_edits=edits,reference_nfc_codepoints=chars,codepoint_error_rate=edits/chars,
        engine=subprocess.run([exe,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
        protocol='First 100 by SHA256(filename); fixed pretrained Tesseract kan, OEM1 PSM8, no tuning/training. NFC and outer whitespace normalization only. Codepoint CER, not grapheme CER.',
        source_url='https://ilocr.iiit.ac.in/dataset/8/',archive_url='https://ilocr.iiit.ac.in/public/printed/phase-0/v0.5/kannada/akshara/test.zip',
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),license='CC BY 4.0 per dataset page',
        limitations=['Modern printed word crops, not historical stone or full-page/line OCR.','Small deterministic sample, not the full benchmark.','Pretrained OCR training overlap unknown.','Published labels used without independent expert review.'],stone_model_changed=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    (out/'predictions.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
