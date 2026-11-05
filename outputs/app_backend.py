"""Local analysis storage and bounded enhancement worker."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,sqlite3,subprocess,uuid,sys
from contextlib import closing
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'work/app_data'

def connect(data=DATA):
    data.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(data/'history.sqlite3')
    con.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT, filename TEXT, sha256 TEXT, image_path TEXT, mask_path TEXT, details TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS character_reviews (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, created TEXT NOT NULL, bbox TEXT NOT NULL, prediction TEXT NOT NULL, model TEXT NOT NULL, model_sha256 TEXT NOT NULL, suggested_label TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT NOT NULL, status TEXT NOT NULL, FOREIGN KEY(run_id) REFERENCES runs(id))')
    con.execute('PRAGMA foreign_keys=ON')
    return con

def history(data=DATA):
    with closing(connect(data)) as con:
        con.row_factory=sqlite3.Row
        return [dict(r) for r in con.execute('SELECT * FROM runs ORDER BY created DESC')]

def analyse(raw,filename,data=DATA,mode='standard'):
    with Image.open(io.BytesIO(raw)) as source:
        if source.width*source.height>20_000_000:raise ValueError('Image exceeds 20 megapixels')
        image=ImageOps.exif_transpose(source).convert('RGB')
    image.thumbnail((1600,1600),Image.Resampling.LANCZOS)
    run_id=uuid.uuid4().hex;folder=data/run_id;folder.mkdir(parents=True)
    src=folder/'input.png';dest=folder/'mask.png';image.save(src)

    # Resolve inference Python environment (work/binarizer_env, .venv, or active environment)
    py_candidates = [
        ROOT / 'work/binarizer_env/Scripts/python.exe',
        ROOT / 'work/binarizer_env/bin/python',
        ROOT / '.venv/Scripts/python.exe',
        ROOT / '.venv/bin/python',
    ]
    py_exe = None
    for p in py_candidates:
        if p.is_file():
            py_exe = str(p)
            break
    if not py_exe:
        py_exe = sys.executable

    core_script = str(ROOT / 'outputs/binarizer_core.py')

    effective_mode='standard'
    fallback_note=None
    details={}
    requested_high=str(mode).strip().lower() in ('high_accuracy','high-accuracy','highaccuracy')

    if requested_high:
        try:
            res=subprocess.run([py_exe,core_script,str(src),str(dest),'--multiscale'],capture_output=True,text=True,timeout=300)
            if res.returncode==0:
                details=json.loads(res.stdout.strip().splitlines()[-1])
                effective_mode='high_accuracy'
            else:
                fallback_note='High accuracy mode was unavailable or exceeded GPU memory. Completed using standard mode.'
        except Exception:
            fallback_note='High accuracy mode was unavailable or exceeded GPU memory. Completed using standard mode.'

    if effective_mode=='standard':
        res=subprocess.run([py_exe,core_script,str(src),str(dest)],capture_output=True,text=True,timeout=300,check=True)
        details=json.loads(res.stdout.strip().splitlines()[-1])

    with Image.open(dest) as mask:
        if mask.size!=image.size:raise ValueError('Output dimensions differ from input')

    mode_label='High accuracy' if effective_mode=='high_accuracy' else 'Standard'
    details['mode']=effective_mode
    details['mode_label']=mode_label
    if fallback_note:
        details['fallback_note']=fallback_note

    record={
        'id':run_id,
        'created':datetime.now(timezone.utc).isoformat(),
        'filename':filename,
        'sha256':hashlib.sha256(raw).hexdigest(),
        'image_path':str(src),
        'mask_path':str(dest),
        'details':json.dumps(details),
        'mode':effective_mode,
        'mode_label':mode_label,
        'fallback_note':fallback_note
    }
    with closing(connect(data)) as con:
        con.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',tuple(record[k] for k in ['id','created','filename','sha256','image_path','mask_path','details']))
        con.commit()
    return record

def save_review(run_id,bbox,prediction,model,model_sha256,suggested_label='',reviewer='',note='',data=DATA):
    if len(bbox)!=4 or any(type(v) is not int for v in bbox):raise ValueError('Box must contain four integers')
    with closing(connect(data)) as con:
        row=con.execute('SELECT image_path FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise ValueError('Analysis does not exist')
        with Image.open(row[0]) as im:w,h=im.size
        x1,y1,x2,y2=bbox
        if not (0<=x1<x2<=w and 0<=y1<y2<=h):raise ValueError('Box outside analysis image')
        suggestion=suggested_label.strip()
        status='user_suggestion_unverified' if suggestion else 'model_prediction_unverified'
        record={'id':uuid.uuid4().hex,'run_id':run_id,'created':datetime.now(timezone.utc).isoformat(),'bbox':json.dumps(bbox),'prediction':str(prediction),'model':str(model),'model_sha256':str(model_sha256),'suggested_label':suggestion,'reviewer':reviewer.strip(),'note':note.strip(),'status':status}
        con.execute('INSERT INTO character_reviews VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(record.values()));con.commit()
        return record['id']

def reviews(run_id,data=DATA):
    with closing(connect(data)) as con:
        con.row_factory=sqlite3.Row
        result=[dict(r) for r in con.execute('SELECT * FROM character_reviews WHERE run_id=? ORDER BY created',(run_id,))]
    for r in result:r['bbox']=json.loads(r['bbox'])
    return result

def review_export(run_id,data=DATA):
    with closing(connect(data)) as con:
        con.row_factory=sqlite3.Row
        row=con.execute('SELECT id,created,filename,sha256,details FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise ValueError('Analysis does not exist')
        source=dict(row);source['details']=json.loads(source['details'])
    return {'schema_version':1,'analysis':source,'coordinates':'xyxy in EXIF-oriented, possibly resized analysis input; not original-upload pixels','verified_ground_truth':False,'reviews':reviews(run_id,data)}
