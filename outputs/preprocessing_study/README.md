# InscripLens preprocessing experiment

Fixed RBF SVM (C=10, gamma=scale) with the same 324-dimensional gradient features as the initial benchmark. Compared four preprocessing choices before feature extraction. Hyperparameters were not tuned.

For selection, the original training split was divided by filename-derived location, with random seed 42: 820 fit crops and 279 development crops. No location occurred in both groups. Development sites were Aradeshanahalli, Maranayakanahalli, Sakalavara and T Dasarahalli. This is conservative location grouping, not verified physical-stone identification. 62 development labels were absent from the fit labels.

| Preprocessing | Correct / 279 | Development accuracy |
|---|---:|---:|
| Original grayscale | 36 | 12.90% |
| 3×3 median filter | 39 | 13.98% |
| Autocontrast, 1% cutoff | 34 | 12.19% |
| Otsu threshold | 37 | 13.26% |

Median was selected on development accuracy. It was then refitted on all 1,099 training crops and evaluated on the existing 300-crop validation set: **48/300 = 16.00%**, compared with **41/300 = 13.67%** for the original baseline. This is seven additional correct predictions, a 2.33 percentage-point increase. It is not established as statistically significant and the validation set is not a fresh test set.

Macro F1: 0.0483; weighted F1: 0.1045. Macro averaging uses the union of labels in reference and predictions, with undefined values set to zero. The outcome remains weak and cannot support reliable full-inscription transcription.

Artifact: selected_svm_bundle.joblib includes both the model and its preprocessing choice. It is compatible with ../predict_character.py. Load only trusted project-produced joblib files.

Reproduce from the chat workspace:

```powershell
python outputs/compare_preprocessing.py work/hero_pilot outputs/preprocessing_study
python outputs/predict_character.py outputs/preprocessing_study/selected_svm_bundle.joblib work/hero_pilot/crops/val/HS022_0001.png
```

Checks: fit/development location disjointness, finite features and saved-model prediction reload passed. Labels and character boxes remain source annotations; classification assumes supplied character crops. No full-stone OCR or translation is evaluated.
