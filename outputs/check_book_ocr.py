"""Separate printed-source OCR baseline; does not use the stone recognizer."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs/book_ocr_study'


def main():
    exe=shutil.which('tesseract')
    if not exe:raise SystemExit('Install Tesseract with Kannada language data first.')
    OUT.mkdir(exist_ok=True)
    page=ROOT/'outputs/context_reading/EC9_leaf729.jpg'
    # Manually selected publication regions, not automatic page layout detection.
    regions=[('opening_two_lines',(435,530,1250,710)),
             ('left_column',(435,530,1250,965)),
             ('right_column',(1500,530,2490,965))]
    results=[]
    with Image.open(page) as im:
        for name,box in regions:
            path=OUT/f'{name}.png';im.crop(box).save(path)
            command=[exe,str(path),'stdout','-l','kan','--oem','1','--psm','6']
            completed=subprocess.run(command,capture_output=True,encoding='utf-8',timeout=90,check=True)
            results.append({'region':name,'bbox_xyxy':box,'text':completed.stdout.strip(),
                            'stderr':completed.stderr.strip(),
                            'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    result={'engine':'Tesseract Kannada LSTM, separate pretrained engine',
            'version':subprocess.run([exe,'--version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],
            'source':'Epigraphia Carnatica IX, Kannada p224, Hoskote entry110',
            'source_url':'https://archive.org/download/epigraphiacarnat09myso/page/n729.jpg',
            'source_sha256':hashlib.sha256(page.read_bytes()).hexdigest(),
            'parameters':{'language':'kan','oem':1,'psm':6},
            'status':'unreviewed OCR drafts; no accuracy measured',
            'stone_model_used':False,'regions':results}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
