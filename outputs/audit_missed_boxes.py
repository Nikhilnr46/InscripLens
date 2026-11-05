"""Development-only audit of unmatched glyph boxes with component-pixel evidence."""
from collections import Counter, defaultdict
import hashlib
import io
import json
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

from evaluate_metadata_context import ROOT, excluded, read
from recognize_regions import match_boxes
from segment_candidates import candidates

DEST = ROOT / "outputs/missed_box_study"


def development_images():
    protocol = read("outputs/matched_mask_study/summary.json")
    ids = {r["source_name"]: r["image_id"] for r in read("work/hero_pilot/manifest.json")}
    groups = defaultdict(list)
    for row in read("outputs/training_scope_study/training_records.json"):
        name = row["source_name"]
        if excluded(name, protocol["development_sites"]) and not excluded(name, protocol["excluded_validation_sites"]):
            groups[name].append(row)
    with zipfile.ZipFile(ROOT / "work/episam_dataset.zip") as archive:
        for name, rows in sorted(groups.items()):
            chars = json.loads(archive.read(f"episam_dataset/chars/train/{name}/character_polygons.json"))
            path = ROOT / "outputs/full_binarizer" / f"{ids.get(name, 'missing')}_mask.png"
            if not path.exists():
                path = ROOT / "work/broad_clean_masks" / (hashlib.sha256(name.encode()).hexdigest() + ".png")
            with Image.open(path) as mask, Image.open(io.BytesIO(archive.read(f"episam_dataset/images/train/{name}.png"))) as raw:
                assert raw.size == mask.size
                boxes = [chars[r["source_key"]]["top_left"] + chars[r["source_key"]]["bottom_right"] for r in rows]
                yield name, raw, mask, boxes, rows


def main():
    records = []
    examples = defaultdict(list)
    matched_count = 0
    for name, raw, mask, boxes, rows in development_images():
        found = candidates(mask)
        matched = {i for i, _, _ in match_boxes(boxes, found)}
        matched_count += len(matched)
        components, _ = ndimage.label(np.asarray(mask.convert("L")) > 127, structure=np.ones((3,3)))
        slices = ndimage.find_objects(components)
        kept = set(map(tuple, found))
        inside = []
        occupants = defaultdict(list)
        for i, (x,y,r,b) in enumerate(boxes):
            ids, counts = np.unique(components[y:b,x:r], return_counts=True)
            pixels = {int(k):int(n) for k,n in zip(ids,counts) if k}
            inside.append(pixels)
            for k,n in pixels.items():
                if n >= max(12, .2 * sum(pixels.values())):
                    occupants[k].append(i)
        for i, box in enumerate(boxes):
            if i in matched:
                continue
            pixels = inside[i]
            amount = sum(pixels.values())
            sizable = [k for k,n in pixels.items() if n >= max(12,.15*amount)]
            retained = []
            for k in pixels:
                yy,xx = slices[k-1]
                if (xx.start,yy.start,xx.stop,yy.stop) in kept:
                    retained.append(k)
            if not amount:
                kind = "empty_mask"
            elif not retained:
                kind = "only_filtered_components"
            elif any(i in occupants[k] and len(occupants[k]) > 1 for k in sizable):
                kind = "component_shared_across_reference_boxes"
            elif len(sizable) >= 2:
                kind = "multiple_substantial_pieces"
            else:
                kind = "other_box_mismatch"
            records.append(dict(source=name,key=rows[i]["source_key"],box=box,kind=kind,foreground=amount,
                                components=len(pixels),substantial=len(sizable)))
            if len(examples[kind]) < 3:
                x,y,r,b = box
                crop = (max(0,x-12),max(0,y-12),min(raw.width,r+12),min(raw.height,b+12))
                pair = []
                for im in (raw,mask):
                    tile = im.crop(crop).convert("RGB")
                    draw = ImageDraw.Draw(tile)
                    draw.rectangle((x-crop[0],y-crop[1],r-1-crop[0],b-1-crop[1]),outline="orange")
                    pair.append(ImageOps.pad(tile,(105,95),color="#333333"))
                examples[kind].append(pair)
    assert matched_count == 254 and len(records) == 105
    totals = Counter(r["kind"] for r in records)
    DEST.mkdir(exist_ok=True)
    (DEST/"development.json").write_text(json.dumps(dict(matched=matched_count,counts=totals,misses=records),indent=2),encoding="utf-8")
    sheet = Image.new("RGB",(650,122*len(examples)),"white")
    for row,(kind, samples) in enumerate(examples.items()):
        ImageDraw.Draw(sheet).text((5,row*122+2),kind,fill="black")
        for j,pair in enumerate(samples):
            for col,tile in enumerate(pair):
                sheet.paste(tile,(215*j+105*col,row*122+22))
    sheet.save(DEST/"examples.png")
    print(totals)


if __name__ == "__main__":
    main()
