"""Local analysis storage and bounded enhancement worker."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,sqlite3,subprocess,uuid
from contextlib import closing
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'work/app_data'

def connect(data=DATA):
    data.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(data/'history.sqlite3')
    con.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT, filename TEXT, sha256 TEXT, image_path TEXT, mask_path TEXT, details TEXT)')
    return con

def history(data=DATA):
    with closing(connect(data)) as con:
        con.row_factory=sqlite3.Row
        return [dict(r) for r in con.execute('SELECT * FROM runs ORDER BY created DESC')]

def analyse(raw,filename,data=DATA):
    with Image.open(io.BytesIO(raw)) as source:
        if source.width*source.height>20_000_000:raise ValueError('Image exceeds 20 megapixels')
        image=ImageOps.exif_transpose(source).convert('RGB')
    image.thumbnail((1600,1600),Image.Resampling.LANCZOS)
    run_id=uuid.uuid4().hex;folder=data/run_id;folder.mkdir(parents=True)
    src=folder/'input.png';dest=folder/'mask.png';image.save(src)
    result=subprocess.run([str(ROOT/'work/binarizer_env/Scripts/python.exe'),str(ROOT/'outputs/binarizer_core.py'),str(src),str(dest)],capture_output=True,text=True,timeout=300,check=True)
    details=json.loads(result.stdout.strip().splitlines()[-1])
    with Image.open(dest) as mask:
        if mask.size!=image.size:raise ValueError('Output dimensions differ from input')
    record={'id':run_id,'created':datetime.now(timezone.utc).isoformat(),'filename':filename,'sha256':hashlib.sha256(raw).hexdigest(),'image_path':str(src),'mask_path':str(dest),'details':json.dumps(details)}
    with closing(connect(data)) as con:
        con.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',tuple(record[k] for k in ['id','created','filename','sha256','image_path','mask_path','details']))
        con.commit()
    return record
