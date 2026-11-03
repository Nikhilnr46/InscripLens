"""Exercise ranked review in an isolated app, using real model/reference assets."""
from pathlib import Path
import os,shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(dir=ROOT/'work') as temp:
    root=Path(temp);out=root/'outputs';out.mkdir()
    for name in ('inscriplens_app.py','app_backend.py','segment_candidates.py','run_character_benchmark.py','recognize_regions.py','recognition_alternatives.py'):
        shutil.copy2(ROOT/'outputs'/name,out/name)
    for name in ('outputs/full_binarizer/HS027_original.png','outputs/full_binarizer/HS027_mask.png','outputs/broad_clean_study/mask_svm_bundle.joblib','outputs/recognition_references.zip'):
        dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(ROOT/name,dest)
    code=r'''
import hashlib,json,sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'outputs'))
from app_backend import connect,history
folder=root/'work/app_data/review-test';folder.mkdir(parents=True)
original=root/'outputs/full_binarizer/HS027_original.png'
mask=root/'outputs/full_binarizer/HS027_mask.png'
record=('review-test','2026-11-03T00:00:00Z','review-test.png',hashlib.sha256(original.read_bytes()).hexdigest(),str(original),str(mask),'{}')
with connect() as con:con.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',record)
app=AppTest.from_file(str(root/'outputs/inscriplens_app.py'),default_timeout=60).run()
app.checkbox[0].set_value(True).run()
app.session_state.run=history()[0]
app.run()
assert not app.exception,list(app.exception)
app.selectbox[0].set_value(1).run()
next(b for b in app.button if b.label=='Predict this character').click().run()
assert not app.exception,list(app.exception)
p=app.session_state.character_prediction
assert p['alternatives'][0]==p['prediction'] and len(set(p['alternatives']))==3
assert len(p['reference_examples'])==3
assert all(e['source_split']=='train' and not e['verified_by_project'] for e in p['reference_examples'])
json.dumps(p)
# The reference library must not attach examples to a different model identity.
import joblib,numpy as np
from recognition_alternatives import source_examples
model=joblib.load(root/'outputs/broad_clean_study/mask_svm_bundle.joblib')['model']
fake=root/'wrong-model';fake.write_bytes(b'different model')
assert source_examples(model,np.zeros(324),p['alternatives'],fake,root/'outputs/recognition_references.zip')==[]
assert source_examples(model,np.zeros(324),p['alternatives'],fake,root/'missing.zip')==[]
print('PASS real UI prediction, three ranked alternatives, training-source examples, JSON export, model mismatch and missing library')
'''
    subprocess.run([sys.executable,'-c',code,str(root)],check=True)
