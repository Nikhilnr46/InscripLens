"""Reproduce the SVC vote/score discrepancy and check the runtime fallback."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'api/reading'))
from recognizer import RecognizerEngine
from run_character_benchmark import features


def main():
    engine=RecognizerEngine()
    # Isolate the SVM fallback even when optional CNN assets are installed.
    engine.cnn_model=None
    model=engine.svm_bundle['model']
    rows=[r for r in json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8')) if r['source_split']=='val']
    crops=[]
    for r in rows:
        with Image.open(ROOT/'outputs/full_binarizer'/r['crop_path']) as im:crops.append(im.copy())
    x=np.stack([features(c,'median') for c in crops]);truth=np.array([r['label'] for r in rows])
    predicted=model.predict(x);argmax=model.classes_[model.decision_function(x).argmax(1)]
    mismatches=np.flatnonzero(predicted!=argmax)
    for i in mismatches:
        result=engine.predict_crop(crops[i])
        assert result['prediction']==predicted[i]
        assert result['alternatives'][0]==predicted[i]
        assert result['models_agree'] is None
        assert result['confidence'] is None and result['uncertain']
    result=dict(reference_n=len(rows),svm_predict_correct=int((predicted==truth).sum()),
        decision_argmax_correct=int((argmax==truth).sum()),disagreements=len(mismatches),runtime_disagreement_cases_checked=len(mismatches),
        protocol='Same saved model and 300 predicted-mask reference crops; no retraining. Runtime SVM uses predict(), alternatives preserve that choice. Unvalidated probability omitted.')
    assert result['svm_predict_correct']==77
    out=ROOT/'outputs/integration_review';out.mkdir(exist_ok=True)
    (out/'recognizer_consistency.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
