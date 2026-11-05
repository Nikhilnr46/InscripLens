# Fixed paired-feature validation

Run `python outputs/validate_paired_features.py` with the existing local dataset, masks and baseline bundle. It shares training-feature extraction with the development experiment. Equal concatenation of mask then original HOG (648 features), median preprocessing and SVC C=10/gamma=scale were fixed before validation. Fit uses 9,925 crops with all six validation locations excluded.

| Measure | Existing mask model | Paired candidate |
|---|---:|---:|
| Correct supplied-box labels / 300 | 77 (25.67%) | 78 (26.00%) |
| Correct automatic localization + labels / 300 | 52 (17.33%) | 50 (16.67%) |

The candidate fixed 15 supplied-box errors and introduced 14. Same 330 automatic boxes and 196 IoU matches. The baseline reproduction assertions passed. Do not promote this candidate: the automatic pipeline regressed, and the one-label supplied-box gain is insufficient evidence. No runtime or production model changed.

This is reused validation from six images, with uncertain binarizer pretraining overlap and unreviewed dataset labels. It is neither full-line accuracy nor modern Kannada transcription. Detailed per-image counts are in summary.json; predictions and experimental weights are local generated artifacts.
