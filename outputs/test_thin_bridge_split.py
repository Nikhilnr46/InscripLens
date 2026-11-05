"""Test a fixed thin-bridge split on unusually large connected components."""
import argparse
import json

import numpy as np
from PIL import Image
from scipy import ndimage

from audit_missed_boxes import DEST, development_images
from evaluate_metadata_context import ROOT, read
from recognize_regions import match_boxes
from segment_candidates import candidates


def split_boxes(mask):
    boxes = candidates(mask)
    if not boxes:
        return boxes
    components, _ = ndimage.label(np.asarray(mask.convert("L")) > 127, structure=np.ones((3,3)))
    ids = {}
    for k, (yy,xx) in enumerate(ndimage.find_objects(components),1):
        ids[(xx.start,yy.start,xx.stop,yy.stop)] = k
    widths = [r-x for x,y,r,b in boxes]
    heights = [b-y for x,y,r,b in boxes]
    w,h = np.median(widths),np.median(heights)
    result = []
    for box in boxes:
        x,y,r,b = box
        if r-x <= 1.5*w and b-y <= 1.5*h:
            result.append(box)
            continue
        region = components[y:b,x:r] == ids[tuple(box)]
        radius = max(1, round(.04 * min(w,h)))
        core = ndimage.binary_erosion(region, iterations=radius)
        seeds,count = ndimage.label(core, structure=np.ones((3,3)))
        sizes = np.bincount(seeds.ravel(),minlength=count+1)
        eligible = np.flatnonzero(sizes[1:] >= max(12,.08*region.sum()))+1
        if len(eligible) < 2:
            result.append(box)
            continue
        nearest = ndimage.distance_transform_edt(~np.isin(seeds,eligible), return_indices=True, return_distances=False)
        assigned = seeds[tuple(nearest)]
        for k in eligible:
            yy,xx = np.nonzero((assigned==k) & region)
            result.append([int(xx.min()+x),int(yy.min()+y),int(xx.max()+x+1),int(yy.max()+y+1)])
    return sorted(result,key=lambda box:(box[1],box[0]))


def evaluate(validation):
    rows = []
    def check(name, mask, truth, labels, model=None):
        from run_character_benchmark import features
        row = dict(source=name, references=len(truth))
        for mode, propose in (("baseline",candidates),("split",split_boxes)):
            boxes = propose(mask)
            matches = match_boxes(truth,boxes)
            row[mode] = dict(boxes=len(boxes),matched=len(matches))
            if model is not None:
                pred = model.predict([features(mask.crop(box),"median") for box in boxes])
                row[mode]["joint"] = sum(labels[i] == pred[j] for i,j,_ in matches)
        rows.append(row)
    if validation:
        import joblib
        model = joblib.load(ROOT/"outputs/broad_clean_study/mask_svm_bundle.joblib")["model"]
        manifest = [r for r in read("work/hero_pilot/manifest.json") if r["source_split"] == "val"]
        for name in sorted({r["image_id"] for r in manifest}):
            group = [r for r in manifest if r["image_id"]==name]
            with Image.open(ROOT/f"outputs/full_binarizer/{name}_mask.png") as mask:
                check(name,mask,[r["bbox_xyxy"] for r in group],[r["label"] for r in group],model)
    else:
        for name, _, mask, boxes, group in development_images():
            check(name,mask,boxes,[r["label"] for r in group])
    total = sum(r["references"] for r in rows)
    scores = {}
    for mode in ("baseline","split"):
        stats = {k:sum(r[mode][k] for r in rows) for k in rows[0][mode]}
        stats["f1"] = 2*stats["matched"]/(total+stats["boxes"])
        scores[mode] = stats
    assert scores["baseline"]["matched"] == (196 if validation else 254)
    split = "validation" if validation else "development"
    DEST.mkdir(exist_ok=True)
    (DEST/f"thin_bridge_{split}.json").write_text(json.dumps(dict(references=total,scores=scores,rows=rows),indent=2),encoding="utf-8")
    print(scores)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation",action="store_true")
    evaluate(parser.parse_args().validation)
