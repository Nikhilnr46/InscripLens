# Broader cleaned-data experiment

This tests whether applying the existing pretrained cleaner to more public training images improves hero-stone character recognition. It is not whole-stone transcription or a reproduction of the Halmidi paper.

## Protocol

- Start with the previously retained EpiSAM source-training records. Remove a further 61 characters from the Begur Nagareshwara Temple image: the previous filename rule missed its validation-location prefix. This leaves 9,925 crops from 109 images. The 949-crop hero-only cohort is unchanged.
- Reuse existing hero masks and cache other masks under `work/broad_clean_masks`. Use the same single-scale, overlapping-tile enhancer, without pseudo-labels or manual corrections.
- Keep the fixed median-filter/HOG/RBF-SVM configuration (`C=10`, `gamma=scale`). Retain constant cleaned crops and report their count.
- Reproduce the existing 63/300 hero-only baseline from the extracted features before accepting the new experiment.
- Hold out the established development locations, including longer filename prefixes, for a development check. Report performance on the same 308 hero development examples separately from the expanded development set.
- Fit all retained training records and evaluate the existing 300 source-box validation examples. Rerun the broad original-image control with the same corrected training cohort.
- Check finite features, validation pixel duplicates, mask dimensions and binary values, and saved-model prediction parity.

## Run locally

First prepare the public archive, hero manifest, training-scope records and hero masks following the root README. The small runtime asset pack alone does not contain the full training corpus.

```powershell
work/binarizer_env/Scripts/python.exe outputs/compare_broad_cleaned.py --prepare --device cpu
python outputs/compare_broad_cleaned.py
```

Preparation is resumable. The CPU environment remains the tested default; GPU execution has not been validated. No GPU package was successfully installed during this experiment.

The completed run writes `summary.json`, local predictions and a model bundle in this folder. Mask hashes are saved under `work/broad_clean_masks`. Model binaries and source images are excluded from Git. The app displays the aggregate result and prefers the broader model bundle when present. The existing hero-only bundle is preserved as a fallback.

## Interpretation

Validation has been reused, source labels have not been independently verified, and binarizer pretraining overlap remains incompletely known. The broader corpus spans different inscription types and periods; its script composition needs auditing. Adding data also adds classes, so this is not a pure sample-count comparison. Accuracy on supplied character boxes is not automatic-pipeline accuracy or project completion.

The earlier 9,986-crop original-image result must retain the Begur exclusion caveat. Use this experiment's corrected control for its cleaning comparison. Preserve upstream EpiSAM/Shilalekhya attribution and licenses described in `THIRD_PARTY.md`.

## Completed result — 3 November 2026

| Diagnostic | Correct / reference | Rate |
|---|---:|---:|
| Hero-only cleaned baseline, reproduced | 63/300 | 21.00% |
| Broad original-image control, corrected location split | 43/300 | 14.33% |
| Broad cleaned-image model | 77/300 | 25.67% |
| Automatic localization plus recognition, hero baseline | 42/300 | 14.00% |
| Automatic localization plus recognition, broad model | 52/300 | 17.33% |

On the same 308 hero development examples, correct predictions improved from 50 to 63. The expanded development population scored 78/359. Four of the six validation images improved on supplied boxes, while two worsened; the aggregate gain is not universal. There are 764 training classes, including 299 singletons and 480 classes with fewer than five examples. The 292 constant cleaned crops were retained, not silently dropped.

The app now prefers this model when its bundle is installed, otherwise it uses the existing hero model. This is a modest diagnostic improvement, not statistical proof of generalization or reliable OCR. Automatic matching still uses the same 330 candidates and 196 geometry matches; recognition changed, not detection.

Checks passed: exact baseline reproduction, source-mask dimensions/binary values, original-pixel validation duplicate exclusion, finite features, model reload predictions and separate automatic-region evaluation. Model compression preserved predictions. See `summary.json` and `../broad_pipeline_study/summary.json` for recorded metrics.
