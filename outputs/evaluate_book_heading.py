"""Measure a printed heading only when an independently checked copy is supplied."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unicodedata
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/book_ocr_study'


def edit_distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]


def normalize(text):
    # Canonical Unicode and whitespace only; retain all spelling and punctuation.
    return ' '.join(unicodedata.normalize('NFC',text).split())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference',type=Path,help='UTF-8 checked transcription, not copied from engine output')
    args=parser.parse_args()
    exe=shutil.which('tesseract')
    if not exe:raise SystemExit('Tesseract with kan language data is required.')
    source=ROOT/'outputs/context_reading/EC9_leaf729.jpg'
    crop=OUT/'printed_heading111.png';box=(660,1095,2130,1210)
    with Image.open(source) as im:im.crop(box).save(crop)
    command=[exe,str(crop),'stdout','-l','kan','--oem','1','--psm','7']
    result=subprocess.run(command,capture_output=True,encoding='utf-8',timeout=90,check=True)
    report={'source':'EC IX Kannada p224, prose heading above entry111',
            'source_url':'https://archive.org/download/epigraphiacarnat09myso/page/n729.jpg',
            'bbox_xyxy':box,'crop_sha256':hashlib.sha256(crop.read_bytes()).hexdigest(),
            'engine':'Tesseract pretrained Kannada LSTM, separate from stone model',
            'parameters':{'language':'kan','oem':1,'psm':7},
            'ocr_text':result.stdout.strip(),
            'reference_status':'pending independent copy check','metrics':None,
            'limits':'One manually selected prose heading; not a book benchmark or historical inscription accuracy.'}
    if args.reference:
        reference=args.reference.read_text(encoding='utf-8-sig').strip()
        if not reference or '[unclear]' in reference.lower():
            raise SystemExit('Reference is empty or uncertain; resolve uncertainty before scoring the complete heading.')
        truth=normalize(reference);prediction=normalize(result.stdout)
        distance=edit_distance(truth,prediction)
        report.update(reference_text=reference,reference_status='user-supplied checked transcription',
                      reference_sha256=hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                      normalization='NFC and collapsed whitespace; punctuation retained',
                      metrics={'reference_codepoints':len(truth),'codepoint_edits':distance,
                               'codepoint_error_rate':distance/len(truth),
                               'exact_heading_match':truth==prediction})
    (OUT/'heading_evaluation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Saved heading evaluation. Reference status:',report['reference_status'])
    if report['metrics']:print(json.dumps(report['metrics']))


if __name__=='__main__':main()
