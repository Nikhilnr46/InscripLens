"""Fixed third-suggestion experiment. Score automatically located glyphs separately."""
import argparse
import json
import joblib
import numpy as np
from sklearn.svm import SVC

from evaluate_shared_glyph_parts import parts
from evaluate_metadata_context import ROOT, read
from recognition_alternatives import rank_labels
from test_detector_training_crops import load_crops


def main(validation):
    x, labels, _, _, evaluation = load_crops(validation, include_extra=False)
    dest = ROOT / "outputs/shared_glyph_parts"
    if validation:
        whole = joblib.load(ROOT / "outputs/broad_clean_study/mask_svm_bundle.joblib")["model"]
        heads = joblib.load(dest / "part_heads.joblib")
    else:
        x = np.asarray(x)
        pieces = [parts(label) for label in labels]
        usable = [i for i, value in enumerate(pieces) if value is not None]
        whole = SVC(C=10, cache_size=512).fit(x, labels)
        heads = [SVC(C=10, cache_size=512).fit(x[usable], [pieces[i][k] for i in usable]) for k in (0, 1)]
    rows = []
    for name, reference, truth, query, matches in evaluation:
        glyphs = np.vstack([reference, query])
        ranked = rank_labels(whole, glyphs, 10)
        votes = list(zip(*(head.predict(glyphs) for head in heads)))
        revised = []
        for choices, vote in zip(ranked, votes):
            match = next((label for label in choices if parts(label) == vote), None)
            third = match if match and match not in choices[:2] else choices[2]
            revised.append([*choices[:2], third])
        n = len(truth)
        for kind, pairs in (("reference", enumerate(range(n))), ("automatic", ((i,n+j) for i,j in matches))):
            original = candidate = fixed = lost = first = changed = 0
            for i,j in pairs:
                expected = truth[i]
                before, after = expected in ranked[j][:3], expected in revised[j]
                original += before
                candidate += after
                fixed += after and not before
                lost += before and not after
                first += ranked[j][0] == expected
                changed += ranked[j][:3] != revised[j]
            rows.append(dict(source=name, kind=kind, n=n, matches=len(matches), first=first, baseline=original,
                             candidate=candidate, fixed=fixed, lost=lost, changed=changed))
    totals = {kind:{k:sum(row[k] for row in rows if row["kind"] == kind)
                    for k in ("n","matches","first","baseline","candidate","fixed","lost","changed")}
              for kind in ("automatic","reference")}
    split = "validation" if validation else "development"
    assert totals["automatic"]["first"] == read("outputs/detector_crop_study/"+split+".json")["baseline"]["joint"]
    print(totals, flush=True)
    (dest / ("suggestions_"+split+".json")).write_text(json.dumps(dict(totals=totals, rows=rows,
        rule="Preserve first two; use best top-ten label matching both part heads as third unless already in first two; otherwise retain third."), indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", action="store_true")
    main(parser.parse_args().validation)
