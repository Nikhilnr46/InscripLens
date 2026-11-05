with open('outputs/app_backend.py', 'r', encoding='utf-8') as f:
    c = f.read()

target = """def analyse(raw,filename,data=DATA):
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
    return record"""

replacement = """def analyse(raw,filename,data=DATA,mode='standard'):
    with Image.open(io.BytesIO(raw)) as source:
        if source.width*source.height>20_000_000:raise ValueError('Image exceeds 20 megapixels')
        image=ImageOps.exif_transpose(source).convert('RGB')
    image.thumbnail((1600,1600),Image.Resampling.LANCZOS)
    run_id=uuid.uuid4().hex;folder=data/run_id;folder.mkdir(parents=True)
    src=folder/'input.png';dest=folder/'mask.png';image.save(src)

    py_exe=str(ROOT/'work/binarizer_env/Scripts/python.exe')
    core_script=str(ROOT/'outputs/binarizer_core.py')

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
    return record"""

assert target in c, "target not found in app_backend.py"
c = c.replace(target, replacement)
with open('outputs/app_backend.py', 'w', encoding='utf-8') as f:
    f.write(c)

print('Successfully updated analyse in app_backend.py')

