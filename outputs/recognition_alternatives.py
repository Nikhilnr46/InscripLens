"""Ranked review suggestions and provenance-linked training support examples."""
import hashlib,json,zipfile
from pathlib import Path
import numpy as np

def rank_labels(model,x,k=3):
    if k<1:raise ValueError('k must be positive')
    x=np.atleast_2d(x)
    first=model.predict(x)
    scores=model.decision_function(x)
    if scores.ndim==1:scores=np.column_stack((-scores,scores))
    order=np.argsort(-scores,axis=1,kind='stable')
    # SVC.predict can resolve vote ties differently from decision_function.
    # Preserve the actual prediction as the first suggestion.
    return [[str(p)]+[str(model.classes_[j]) for j in row if model.classes_[j]!=p][:k-1] for p,row in zip(first,order)]

def source_examples(model,feature,labels,model_path,library):
    library=Path(library)
    if not library.is_file():return []
    with zipfile.ZipFile(library) as z:
        index=json.loads(z.read('index.json'))
        if index['model_sha256']!=hashlib.sha256(Path(model_path).read_bytes()).hexdigest():return []
        records=index['examples'];result=[]
        for label in labels:
            eligible=[r for r in records if r['label']==label]
            if not eligible:continue
            ids=np.array([r['support_index'] for r in eligible])
            distance=np.sum((model.support_vectors_[ids]-feature)**2,axis=1)
            chosen=eligible[int(np.argmin(distance))]
            result.append({**chosen,'image_bytes':z.read(chosen['image_path'])})
        return result
