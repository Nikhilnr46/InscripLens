"""Test missing assets in an isolated copy, without touching real project assets."""
from pathlib import Path
import tempfile,shutil,subprocess,sys
root=Path(__file__).resolve().parent.parent
(root/'work').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root/'work') as temp:
    dest=Path(temp)/'outputs';dest.mkdir()
    for name in ['inscriplens_app.py','app_backend.py','segment_candidates.py','run_character_benchmark.py']:
        shutil.copy2(root/'outputs'/name,dest/name)
    code='''
import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
sys.path.insert(0,sys.argv[1])
app=AppTest.from_file(str(Path(sys.argv[1])/'inscriplens_app.py'),default_timeout=30).run()
assert not app.exception,list(app.exception)
assert app.checkbox[0].disabled
for page in ['Dataset explorer','Experiment results','Saved analyses','Setup status']:
 app.sidebar.radio[0].set_value(page).run()
 assert not app.exception,(page,list(app.exception))
print('PASS fresh clone: unavailable demo disabled; all views handle missing assets')
'''
    subprocess.run([sys.executable,'-c',code,str(dest)],check=True)
