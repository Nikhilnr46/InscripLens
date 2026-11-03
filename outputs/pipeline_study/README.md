# Automatic localization and recognition — 3 November 2026

Pipeline: pretrained full-image mask, fixed connected components, crop each predicted box, mask-trained HOG/SVM. No reference boxes or labels guide prediction. Output is a set of numbered candidate labels, not a verified reading sequence or sentence.

Six validation images yield330 candidates.196 match reference boxes at IoU>=0.5;42 also have the correct raw source label. Geometry-only one-to-one assignment prevents duplicated detections claiming multiple successes and does not use labels to choose matches.

- Joint localization-and-label recall:42/300=14%.
- Joint precision:42/330=12.73%.
- Label agreement among localized candidates:42/196=21.43%.

These differ from the earlier63/300(21%) recognition score using supplied boxes. No word/character edit-rate or translation score is claimed. Missing, split and merged detections matter. References are filtered annotations and may omit real glyphs. Validation is reused and binarizer pretraining overlap is incompletely known: this is a diagnostic pipeline measurement, not an independent final benchmark.

Application feature: after enhancement, click Predict all detected regions. Results persist per analysis in work/app_data and can be downloaded immediately or from Saved analyses. Export includes model fingerprint, boxes and explicit unverified flags. Manual single-region review remains available.

Run `python outputs/recognize_regions.py` to reproduce evaluation; `python outputs/check_region_recognition.py` checks blank masks, one-to-one matching, disjoint boxes and feature parity. Timing in summary excludes mask generation. Public model/data attribution remains in THIRD_PARTY.md. No new runtime assets required for the application feature; updating code is sufficient when the existing runtime pack is installed.
