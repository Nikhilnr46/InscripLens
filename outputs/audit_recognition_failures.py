"""Describe frozen validation errors; do not tune or retrain against them."""
import collections
import json
import re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent


def main():
    read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
    protocol=read('outputs/broad_clean_study/summary.json')
    def blocked(name):
        site=re.split(r'\d',name,maxsplit=1)[0].strip().lower()
        return any(site==s or site.startswith(s+' ') for s in protocol['excluded_validation_sites'])
    training=[r for r in read('outputs/training_scope_study/training_records.json') if not blocked(r['source_name'])]
    assert len(training)==9925
    support=collections.Counter(r['label'] for r in training)
    rows=read('outputs/broad_clean_study/predictions.json')
    buckets=collections.defaultdict(collections.Counter)
    categories=collections.Counter();details=[]
    for r in rows:
        n=support[r['reference']];correct=r['reference']==r['prediction']
        bucket='unseen' if n==0 else '1-4' if n<5 else '5-19' if n<20 else '20+'
        with Image.open(ROOT/'outputs/full_binarizer'/r['crop_path']) as im:
            histogram=im.convert('L').histogram();foreground=sum(histogram[128:]);total=im.width*im.height
        constant=foreground in (0,total)
        buckets[bucket]['examples']+=1;buckets[bucket]['correct']+=int(correct)
        if not correct:
            # Disjoint attribution groups are descriptive, not causal proof.
            category='unseen_reference_label' if n==0 else 'constant_mask' if constant else 'seen_label_1_to_4_examples' if n<5 else 'seen_label_5_to_19_examples' if n<20 else 'seen_label_at_least_20_examples'
            categories[category]+=1
        details.append({**r,'training_support':n,'constant_mask':constant,'foreground_fraction':foreground/total})
    assert sum(r['reference']==r['prediction'] for r in rows)==77
    result={'frozen_model':'broad_clean_study','validation_n':len(rows),'correct':77,
            'errors':len(rows)-77,'by_training_support':dict(buckets),
            'disjoint_error_groups':dict(categories),
            'all_constant_mask_examples':sum(r['constant_mask'] for r in details),
            'limits':['Descriptive reused-validation audit, not fresh evaluation or causal attribution.',
                      'Nonconstant masks can still lose important strokes.',
                      'Raw labels and source annotations may contain inconsistencies.',
                      'No retraining, tuning or source-label edits performed.']}
    out=ROOT/'outputs/recognition_failure_audit';out.mkdir(exist_ok=True)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (out/'records.json').write_text(json.dumps(details,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
