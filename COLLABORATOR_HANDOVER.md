# InscripLens collaborator handover

Prepared 3 November 2026. Repository: https://github.com/Nikhilnr46/InscripLens , branch `main`.

## Start here: why your clone crashed

`outputs/full_binarizer/HS027_original.png` is a generated demo image. Images, datasets, trained models and environments are excluded from Git, so cloning the repository does not provide them. `ROOT` is computed from the script location; `C:/nikhil` is your checkout root, not an incorrect hardcoded path.

Update: the fresh-clone guards now disable an unavailable demo and show setup guidance. Pull main to receive the fix. Enhancement and recognition still require the runtime assets; missing files disable the relevant action. Dataset explorer handles absent assets, and Setup status lists required files. Do not create an empty PNG or change the path to the original developer's computer.

## Fastest way to run the current demonstration

Ask Nikhil for `InscripLens_runtime_assets.zip`, prepared alongside this handover. Extract it **into the repository root** so its `work/` and `outputs/` folders merge with the clone. Do not extract it inside another nested folder. The archive includes only the public assets and trained model needed by the current app; it excludes private upload history, credentials, virtual environments and the full training corpus.

Expected layout:

```text
InscripLens/
  outputs/inscriplens_app.py
  outputs/full_binarizer/HS027_original.png
  outputs/full_binarizer/*_original.png, *_mask.png, *_comparison.png
  outputs/full_binarizer/recognition_predictions.json
  outputs/matched_mask_study/mask_svm_bundle.joblib
  work/hero_pilot/manifest.json
  work/shilalekhya/Unet/model.py
  work/shilalekhya/LICENSE
  work/shilalekhya/binarizer.pth
```

Python environments cannot simply be shared between laptops. The tested UI environment is Python3.14; the separate inference environment is Python3.12 with CPU torch2.5.1. Your traceback shows Python3.13: that is not the cause of this missing-file error, but the exact dependency set has not been tested there. To reproduce the known environment, install Python3.14 and3.12, then run from the checkout root in PowerShell:

```powershell
git pull --ff-only origin main
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
py -3.12 -m venv work/binarizer_env
.\work\binarizer_env\Scripts\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
.\work\binarizer_env\Scripts\python.exe -m pip install "numpy>=2.2" "Pillow>=11"
.\.venv\Scripts\python.exe -m streamlit run outputs/inscriplens_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501 . If using this UI environment, prefer the explicit command above: the existing CMD launcher uses whichever `python` is on PATH. Enhancement executes `work/binarizer_env/Scripts/python.exe`; that exact environment location matters.

Run `Test-Path outputs/full_binarizer/HS027_original.png` and `Test-Path work/shilalekhya/binarizer.pth` before trying the demo. Both should return True. Models serialized by joblib must only be loaded from the trusted project owner; do not accept arbitrary uploaded model files.

## What the project does and does not do

Working: image upload/demo, pretrained stroke enhancement, connected-component candidate boxes, rectangle adjustment, experimental single-crop classification, JSON/mask downloads, saved SQLite analyses, dataset/experiment exploration.

Not working as a reliable product: complete historical Kannada transcription, historical-to-modern Kannada conversion, English interpretation. No verified full-stone reading order or line transcription. Do not replace these missing stages with stored readings and call them OCR.

Results on the same300 source-labelled validation crops:

| Experiment | Correct |
|---|---:|
| Original-image HOG/SVM,949 training crops |45/300 (15%)|
| Predicted-mask HOG/SVM, same cohort |63/300 (21%)|
| Small CNN on masks |44/300 (14.67%)|
| Frozen ImageNet ResNet18 features, selected mask input |46/300 (15.33%)|

The app currently uses the mask-SVM. Automatic candidate detection:196 matches among330 candidates against300 filtered reference boxes at IoU0.5, precision59.39%,recall65.33%. Recognition scores use supplied reference boxes, not automatically detected boxes. These are separate metrics. Validation has been reused, source labels are not expert-verified by this project, and enhancement-model training overlap is incompletely known. No80% project-completion claim is justified; last rough planning estimate was45–50% of original scope.

## Code map

Latest addition: `app_backend.py` stores append-only character review records in SQLite. The app preserves original predictions separately from optional user suggestions and exports source hash, analysis coordinates and model fingerprint. `python outputs/check_review_storage.py` checks Unicode, invalid bounds, persistence and provenance. The new table is created automatically without replacing existing history. No new runtime assets are needed; `git pull --ff-only origin main` and restart Streamlit. User suggestions are not verified ground truth and are not automatically used for training.

- `outputs/inscriplens_app.py`: Streamlit views and user interactions.
- `outputs/app_backend.py`: image preparation, inference subprocess and SQLite history.
- `outputs/binarizer_core.py`: single-scale tiled pretrained inference on CPU.
- `outputs/segment_candidates.py`: connected components and localization evaluation.
- `outputs/run_character_benchmark.py`: HOG features and classical baselines.
- `outputs/train_matched_masks.py`: matched original/mask training comparison.
- `outputs/train_small_cnn.py`: bounded scratch-CNN experiment.
- `outputs/extract_transfer_features.py`, `evaluate_transfer_features.py`: frozen encoder experiment.
- `src/`: earlier image-processing scripts; preserve them.

`work/app_data` is private local analysis history. Never commit it. The `outputs` name contains both source scripts and artifacts for historical reasons; do not move files without adjusting relative paths/tests.

## Fresh-clone reliability work

Items1–3 below and the asset-status view are now implemented. `python outputs/check_fresh_clone.py` tests an isolated source-only copy without moving real assets. Automated archive import/download remains future work; use the supplied pack and manual setup for now.

1. Disable the demo checkbox with an explanation when its sample is absent; guard Dataset explorer against missing manifest, images and predictions.
2. Check the worker executable, vendor model source and checkpoint before allowing enhancement. Give actionable setup messages.
3. Check classifier availability before recognition. Upload/enhancement must not crash just because recognition assets are absent.
4. Add a setup/asset-status view and a reproducible asset-download or archive-import workflow with checksums. Keep private histories excluded.
5. Test a **clean clone without assets**, then a clone with runtime assets. Avoid testing only the original developer's fully populated folder.

Use a separate branch such as `fix/fresh-clone-setup`, commit only intended changes and open a pull request. Do not force-push main, add virtual environments/weights to Git, or run `git add .` without inspecting status. Coordinate ownership of files with Nikhil to avoid conflicting simultaneous edits.

Existing tests: `python outputs/check_app.py`, `python outputs/check_fresh_clone.py` and `python outputs/check_app_backend.py`. The latter requires `outputs/pretrained_binarizer_test/input_patch.png` (included in the runtime pack) and executes real inference. Tests run on the original machine; the friend-laptop setup must still be verified locally.

## Rebuilding rather than using the pack

Follow root README's dataset preparation and experiment commands. The runtime pack is not enough to reproduce training: obtain the public EpiSAM archive separately and generate crops/masks. Preserve upstream filenames and source splits, exclude validation locations from recognizer training, and retain uncertainty/attribution. Do not access the restricted Akshara Bhandara corpus.

## Attribution and contribution

Shilalekhya code is MIT, copyright2025 ihdia; retain its LICENSE. Public EpiSAM data and checkpoint repository declare CC BY-SA4.0. Authors: Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla; imagery acknowledged to The Mythic Society Bengaluru. Derived previews/masks in the pack retain CC BY-SA4.0 attribution/share-alike terms. See THIRD_PARTY.md and outputs/EpiSAM_source_README.md. The project integrates and evaluates established methods; it does not claim to have invented the pretrained enhancer. Preserve truthful assistance and authorship disclosures.
