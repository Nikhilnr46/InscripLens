# Full-image pretrained binarization diagnostic

3 November 2026. All six hero validation images processed successfully on CPU. Native-resolution 512px tiles, stride 448, edge padding only for undersized dimensions, probability averaging in overlaps and threshold 0.5. No annotation-guided mask prediction. This implements single-scale tiled inference, not the authors' complete multiscale/refinement algorithm. Every pixel has coverage; all probabilities checked finite. Total recorded inference time approximately 108 seconds; individual images 15–24 seconds.

Begur and Nagavara comparison images were visually inspected: substantial background suppression and retention of inscription-like strokes. This is not expert validation of recovered letter shapes. All six original/mask/comparison files are saved, including failures or omissions that may be visible.

## Frozen recognition comparison

Same saved broader-corpus SVM, same median/HOG features, same 300 validation annotation boxes:

| Input | Matches against source labels | Accuracy |
|---|---:|---:|
| Original crops | 47/300 | 15.67% |
| Predicted-mask crops | 42/300 | 14.00% |

Baseline reproduced exactly. Direct input replacement did not improve this classifier. It was trained on original images, not predicted masks; this comparison cannot establish whether matched training on masks would improve performance. The next meaningful experiment is matched preprocessing of training and validation images, with settings chosen on training-only development data, followed by a learned recognizer if warranted. Do not tune against these 300 repeatedly and call them a fresh test.

Boxes are still supplied annotations: this is not an end-to-end automatic OCR result. Binarizer training overlap remains unresolved for five validation images; Nagavara matches the published test list by normalized name, and the published training list is empty. No new independent accuracy claim. Character labels remain source transliterations, not verified Unicode Kannada readings.

## Reproduction

Run from the chat workspace:

```powershell
& work/binarizer_env/Scripts/python.exe outputs/run_full_binarizer.py
python outputs/evaluate_frozen_mask_input.py
```

See inference_summary.json, recognition_comparison.json and recognition_predictions.json for timings, protocols and per-image results. No jobs remain running.

## Attribution

Model/code: [Shilalekhya](https://github.com/ihdia/shilalekhya-binarization), copyright 2025 ihdia, MIT code license retained in work/shilalekhya/LICENSE. [Public checkpoint](https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project), repository license CC BY-SA 4.0. Checkpoint hash is recorded in ../pretrained_binarizer_test/result.json.

Images and derived crops/masks/comparisons: [EpiSAM public dataset](https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset), Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla; source imagery acknowledged to The Mythic Society Bengaluru. Derived images retain [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) attribution/share-alike terms. Changes: predicted binarization, annotation-based cropping, and resized side-by-side previews. No restricted archive accessed.
