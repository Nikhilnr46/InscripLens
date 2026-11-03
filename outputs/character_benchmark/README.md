# InscripLens: first character-recognition benchmark

## Scope

Classification of supplied EpiSAM character crops using raw source transliteration labels. This does not evaluate automatic detection, full-inscription OCR, Kannada Unicode transcription, or translation.

Training: 1,099 crops from 21 source images, 304 labels. Validation: 300 crops from 6 source images. 23 validation crops have labels absent from training. Filename-based image identities and historical label correctness remain under review.

Three classifiers use the same 324-dimensional gradient-histogram features. Parameters were fixed before this run; no validation tuning was performed. Results are preliminary validation results, not an independent test-set claim.

| Model | Correct / 300 | Accuracy | Macro precision | Macro recall | Macro F1 | Weighted F1 |
|---|---:|---:|---:|---:|---:|---:|
| majority_control | 12 | 4.00% | 0.0003 | 0.0076 | 0.0006 | 0.0031 |
| knn | 15 | 5.00% | 0.0217 | 0.0236 | 0.0208 | 0.0481 |
| svm | 41 | 13.67% | 0.0323 | 0.0466 | 0.0343 | 0.0841 |
| random_forest | 13 | 4.33% | 0.0133 | 0.0072 | 0.0074 | 0.0398 |

Macro averages use labels present in reference or model predictions (the set can differ by model); undefined class metrics are zero. Accuracy is the primary comparison. Individual class reports and per-image results are saved.

## Findings

- SVM: 41/300 overall; 41/277 (14.80%) when reporting only validation labels represented in training. The latter is a secondary diagnostic, not a replacement for the overall score.
- SVM by training support: 0/23 unseen; 0/45 with 1–2 training examples; 1/43 with 3–4; 40/189 with at least 5 examples. These observations do not prove that sample count alone causes the errors.
- Visual inspection of the first two validation crops from each source image shows strong stone texture and variable character shape/contrast. The contact sheet was selected by manifest order, not by favourable predictions.
- Results are weak. They establish a reproducible baseline and testing infrastructure, not a reliable recognizer.

## Checks completed

- No shared image IDs or exact pixel-identical crops between the selected train and validation sets. Near-duplicate views and physical-stone grouping still require review.
- Feature dimensions, finite values, saved-model reload predictions and simple metric sanity checks passed.
- Single-crop prediction CLI ran successfully with the saved SVM.
- Existing capstone environment lacked the OpenCV ML module. Benchmark ran using already-installed system Python packages; no packages were installed and project scripts were not changed.

## Reproduction

From the chat workspace with its existing work/hero_pilot dataset:

```powershell
python outputs/run_character_benchmark.py work/hero_pilot outputs/character_benchmark
python outputs/predict_character.py outputs/character_benchmark/svm.joblib work/hero_pilot/crops/val/HS022_0001.png
```

Environment: {"python": "3.14.6", "numpy": "2.4.6", "Pillow": "12.2.0", "scikit-learn": "1.9.0", "joblib": "1.5.3"}

Training parameters: kNN k=3 with distance weights; RBF SVM C=10 and gamma=scale; random forest 150 trees with balanced_subsample class weights and seed 42. No scaling was fitted on validation data.

## Next development priority

Review label conventions and stone grouping; establish a controlled preprocessing comparison and training-only model selection. Integrate a demo only with explicit supplied-crop mode and visible source/prediction distinction. Do not use an attractive interface to imply that recognition or translation is solved.

## Source attribution

Dataset: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset ; CC BY-SA 4.0 as declared by public release. Authors: Arnav Sharma, Pratyush Jena, Amal Joseph, Ravi Kiran Sarvadevabhatla. Image provider credited by release: Mythic Society Bengaluru. Contact-sheet modifications: cropped, resized, arranged and labelled examples. Licence: https://creativecommons.org/licenses/by-sa/4.0/.