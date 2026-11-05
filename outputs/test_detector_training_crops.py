"""Test extra training crops from the same detector used by Classify All."""
from collections import defaultdict
import argparse
import hashlib
import json
import zipfile

import numpy as np
from PIL import Image
from sklearn.svm import SVC

from evaluate_metadata_context import ROOT, excluded, read
from recognize_regions import match_boxes
from segment_candidates import candidates
from run_character_benchmark import features


def measure(model, reference, labels, detected, matches):
    ref_pred = model.predict(reference)
    box_pred = model.predict(detected)
    return dict(reference=int(np.sum(ref_pred == labels)),
                joint=sum(int(labels[i] == box_pred[j]) for i, j in matches))


def load_crops(validation, include_extra=True):
    protocol = read("outputs/matched_mask_study/summary.json")
    manifest = read("work/hero_pilot/manifest.json")
    ids = {r["source_name"]: r["image_id"] for r in manifest}
    groups = defaultdict(list)
    for row in read("outputs/training_scope_study/training_records.json"):
        if not excluded(row["source_name"], protocol["excluded_validation_sites"]):
            groups[row["source_name"]].append(row)
    if validation:
        for row in manifest:
            if row["source_split"] == "val":
                groups[row["source_name"]].append(row)
    original, truth, extra, extra_labels = [], [], [], []
    evaluation = []
    with zipfile.ZipFile(ROOT / "work/episam_dataset.zip") as archive:
        for name, rows in sorted(groups.items()):
            val = rows[0].get("source_split") == "val"
            evaluate = val or (not validation and excluded(name, protocol["development_sites"]))
            if val:
                boxes = [r["bbox_xyxy"] for r in rows]
            else:
                chars = json.loads(archive.read(f"episam_dataset/chars/train/{name}/character_polygons.json"))
                boxes = [chars[r["source_key"]]["top_left"] + chars[r["source_key"]]["bottom_right"] for r in rows]
            labels = np.array([r["label"] for r in rows])
            path = ROOT / "outputs/full_binarizer" / f"{ids.get(name, 'missing')}_mask.png"
            if not path.exists():
                path = ROOT / "work/broad_clean_masks" / (hashlib.sha256(name.encode()).hexdigest() + ".png")
            with Image.open(path) as mask:
                found = candidates(mask) if evaluate or include_extra else []
                ref = [features(mask.crop(b), "median") for b in boxes]
                matches = match_boxes(boxes, found, threshold=.5 if evaluate else .65)
                if evaluate:
                    query = [features(mask.crop(b), "median") for b in found]
                    evaluation.append((name, ref, labels, query, [(i,j) for i,j,_ in matches]))
                else:
                    original.extend(ref)
                    truth.extend(labels)
                    for i,j,_ in matches:
                        if boxes[i] != found[j]:
                            extra.append(features(mask.crop(found[j]), "median"))
                            extra_labels.append(labels[i])
    assert len(truth) == (9925 if validation else 9566)
    return original, truth, extra, extra_labels, evaluation


def run(validation):
    original, truth, extra, extra_labels, evaluation = load_crops(validation)
    report = dict(training=len(truth), extra=len(extra), per_source={})
    for variant in ("baseline", "augmented"):
        print(f"Fitting {variant}, {len(extra)} additional crops available", flush=True)
        augmented = variant == "augmented"
        model = SVC(C=10, gamma="scale", cache_size=550).fit(original + (extra if augmented else []),
                                                             truth + (extra_labels if augmented else []))
        totals = defaultdict(int)
        for name, ref, labels, query, matches in evaluation:
            values = measure(model, ref, labels, query, matches)
            values.update(total=len(labels), matched=len(matches), detected=len(query))
            report["per_source"].setdefault(name, {})[variant] = values
            for k,v in values.items():
                totals[k] += v
        report[variant] = dict(totals)
        print(variant, dict(totals), flush=True)
    assert report["baseline"]["reference"] == (77 if validation else 78)
    if validation:
        assert report["baseline"]["joint"] == 52
    report["protocol"] = "Fixed mask HOG/SVC. Add each nonidentical fit detection matched 1:1 at IoU >= .65. Score all evaluation annotations with detector matches at IoU >= .50."
    split = "validation" if validation else "development"
    dest = ROOT / "outputs/detector_crop_study"
    dest.mkdir(exist_ok=True)
    (dest / (split + ".json")).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", action="store_true")
    run(parser.parse_args().validation)
