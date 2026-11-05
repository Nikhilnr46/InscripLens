"""Development gate for a visual consonant/vowel agreement reranker."""
import argparse
import json
import re
import unicodedata

import numpy as np
from sklearn.svm import SVC

from evaluate_metadata_context import ROOT, read
from kannada_converter import CONSONANTS, INDEPENDENT_VOWELS
from recognition_alternatives import rank_labels
from test_detector_training_crops import load_crops

VOWEL = re.compile("|".join(re.escape(v) for v, _ in INDEPENDENT_VOWELS))
CLUSTER = re.compile("(?:" + "|".join(re.escape(c) for c, _ in CONSONANTS) + ")*")


def parts(label):
    normalized = unicodedata.normalize("NFC", label)
    vowel = VOWEL.search(normalized)
    if vowel and CLUSTER.fullmatch(normalized[:vowel.start()]):
        return normalized[:vowel.start()] or "<independent>", normalized[vowel.start():]
    return None


def main(validation):
    x, labels, _, _, evaluation = load_crops(validation, include_extra=False)
    parsed = [parts(label) for label in labels]
    usable = [i for i, entry in enumerate(parsed) if entry is not None]
    X = np.asarray(x)
    def train(features, targets):
        return SVC(C=10, gamma="scale", cache_size=512).fit(features, targets)
    whole = train(X, labels)
    heads = [train(X[usable], [parsed[i][k] for i in usable]) for k in (0, 1)]
    rows = []
    for name, reference, truth, query, matches in evaluation:
        glyphs = np.vstack([reference, query])
        ranked = rank_labels(whole, glyphs, 3)
        votes = list(zip(*(head.predict(glyphs) for head in heads)))
        base = [r[0] for r in ranked]
        candidate = [next((label for label in choices if parts(label) == vote), choices[0])
                     for choices, vote in zip(ranked, votes)]
        n = len(truth)
        row = dict(source=name, n=n, matches=len(matches))
        for method, guesses in (("baseline", base), ("candidate", candidate)):
            row[method + "_reference"] = sum(a == b for a,b in zip(truth, guesses[:n]))
            row[method + "_joint"] = sum(truth[i] == guesses[n+j] for i,j in matches)
        row["joint_fixed"] = sum(base[n+j] != truth[i] and candidate[n+j] == truth[i] for i,j in matches)
        row["joint_lost"] = sum(base[n+j] == truth[i] and candidate[n+j] != truth[i] for i,j in matches)
        rows.append(row)
    totals = {k:sum(row[k] for row in rows) for k in rows[0] if k != "source"}
    split = "validation" if validation else "development"
    control = read("outputs/detector_crop_study/" + split + ".json")["baseline"]
    assert (totals["baseline_reference"], totals["baseline_joint"]) == (control["reference"], control["joint"])
    dest = ROOT / "outputs/shared_glyph_parts"
    dest.mkdir(exist_ok=True)
    (dest/(split + ".json")).write_text(json.dumps(dict(totals=totals, rows=rows, training=len(labels),
        usable=len(usable), protocol="First of three whole-glyph SVM labels matching both visual predictions (consonant prefix and vowel-led remainder); otherwise retain baseline."), indent=2), encoding="utf-8")
    if validation and totals["candidate_joint"] > totals["baseline_joint"]:
        import joblib
        joblib.dump(heads, dest / "part_heads.joblib", compress=3)
    print(totals, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", action="store_true")
    main(parser.parse_args().validation)
