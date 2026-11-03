"""Exercise the same upload-analysis function used by the UI, with isolated storage."""
import tempfile,json
from pathlib import Path
from PIL import Image
from app_backend import ROOT,analyse,history
with tempfile.TemporaryDirectory(dir=ROOT/'work') as folder:
    data=Path(folder)
    try:analyse(b'not an image','invalid.png',data)
    except Exception:pass
    else:raise AssertionError('Invalid upload was accepted')
    assert history(data)==[]
    raw=(ROOT/'outputs/pretrained_binarizer_test/input_patch.png').read_bytes()
    record=analyse(raw,'test.png',data)
    saved=history(data);assert len(saved)==1 and saved[0]['sha256']==record['sha256']
    with Image.open(record['mask_path']) as mask:assert mask.size==(512,512) and set(mask.getdata())<={0,255}
    assert json.loads(record['details'])['method']=='single_scale_pretrained_binarization'
    print('PASS: invalid upload, worker inference, output dimensions, binary mask, SQLite persistence/reload.')
