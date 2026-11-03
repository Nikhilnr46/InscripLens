# Matched preprocessing experiment — 3 November 2026

Same 949 training crops from hero-named images, 281 raw source classes, same 300 validation crops. All validation locations excluded from recognizer training using filename-derived sites. Fixed median preprocessing, HOG features, RBF SVM C=10/gamma=scale. No parameter sweep. Both conditions evaluated on a training-only site-grouped development split before refitting the full training cohort.

| Condition | Development | Reused validation |
|---|---:|---:|
| Original images for training and prediction | 35/308 | 45/300 (15%) |
| Predicted masks for training and prediction | 50/308 | 63/300 (21%) |

Improvement: 18 additional matches, 6 percentage points, on this diagnostic validation set. Mask results improve on five images and decline on Begur. Source labels remain unreviewed. This is not 21% project completion or adequate full-text OCR. Existing broader-corpus 47/300 result used a different training pool; compare 45 and 63 here.

Saved models pass prediction reload checks. Original baseline reproduced exactly. Input masks generated for all 27 pilot images. Source annotation boxes still supply crops: automatic segmentation errors are not included in these recognition scores. Pretrained-binarizer training overlap remains unknown for most images, including training-only development; this prevents a clean end-to-end independent-generalization claim.

Reproduce: first run outputs/prepare_clean_training.py in work/binarizer_env, then system Python outputs/train_matched_masks.py. The application uses mask_svm_bundle.joblib for its experimental predictions.

Next recognition milestone: learned visual features, with a defined training/development protocol and an independent final test if available. Current results support retaining the enhancement module, but do not establish feasibility of reliable full-stone transcription or historical-language translation.
