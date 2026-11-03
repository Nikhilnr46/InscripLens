"""Smoke-check navigable application views and saved-analysis rendering."""
from pathlib import Path
import sys
from streamlit.testing.v1 import AppTest
root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root/'outputs'))
app=AppTest.from_file(str(root/'outputs/inscriplens_app.py'),default_timeout=30).run()
assert not app.exception,list(app.exception)
for page in ['Dataset explorer','Experiment results','Saved analyses','Analyse an image']:
    app.sidebar.radio[0].set_value(page).run()
    assert not app.exception,(page,list(app.exception))
    print('PASS',page)
print('Application navigation checked. Upload subprocess tested separately; not browser end-to-end.')
