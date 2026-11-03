# InscripLens

An experimental local application for analysing historical Kannada inscription images, with a hero-stone pilot dataset. It connects pretrained enhancement, candidate-region detection, experimental character recognition and review/storage.

## Current capabilities

- Upload a PNG/JPEG or select a public demonstration image.
- Predict foreground strokes with the credited Shilalekhya model.
- Inspect automatically proposed regions, adjust a character box and obtain an unverified transliteration-label prediction.
- Predict all detected regions in one action and save/export their labels and boxes. This is not sentence transcription. The combined localization-and-label diagnostic recovers42/300 reference characters (14%).
- Download masks, candidate boxes and analysis records; reopen saved analyses from SQLite.
- Save character predictions with optional reviewer suggestions/notes and export them with model/source provenance. Suggestions remain unverified and never automatically enter training.
- Explore source annotations and recorded experiments separately from predictions.

Reliable full-stone OCR, historical-to-modern Kannada conversion and English translation are **not implemented**. Current diagnostic recognition is weak: matched cleaned-image HOG/SVM63/300 (21%), small CNN44/300 (14.67%), frozen ResNet18-feature classifier46/300 (15.33%). These use supplied reference boxes, reused validation, and incompletely documented binarizer pretraining overlap. They are not independent end-to-end accuracy results.

## Local start

On the development computer, runtime assets have been migrated into this project. Double-click `outputs/Launch_InscripLens.cmd`, or run:

```powershell
python -m streamlit run outputs/inscriplens_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501 . This serves only on localhost. Analysis history stays in `work/app_data`.

## Fresh-clone setup

This repository contains source and aggregate reports. It intentionally excludes virtual environments, datasets, images, weights, generated model binaries and private analysis history. A fresh clone is **not** a ready-to-run deployment.

1. Install the application dependencies in `requirements.txt` in your chosen Python environment.
2. Create a Python3.12 environment at `work/binarizer_env`; install `requirements-inference.txt` there (CPU torch wheels may be obtained from the official PyTorch index).
3. Obtain the public assets listed in `THIRD_PARTY.md`. The binarizer requires `work/shilalekhya/Unet/model.py`, its LICENSE and `work/shilalekhya/binarizer.pth`.
4. Put the public EpiSAM archive at `work/episam_dataset.zip`. Generate pilot records using `python outputs/prepare_hero_pilot.py work/episam_dataset.zip work/hero_pilot`.
5. Generate masks with inference-environment Python: `outputs/run_full_binarizer.py` for validation and `outputs/prepare_clean_training.py` for training.
6. With application-environment Python, run `outputs/compare_training_scope.py work/episam_dataset.zip work/hero_pilot outputs/training_scope_study`, then `outputs/train_matched_masks.py` and `outputs/evaluate_frozen_mask_input.py`. These supply the current app model and displayed comparison records. This preparation involves actual computation; do not substitute stored reference labels for predictions.

Original preprocessing scripts remain in `src/`. New application and experiment scripts remain in `outputs/` to preserve their existing relative-path contracts. Historical notes may describe earlier states; newer experiment summaries supersede them.

## Checks

```powershell
python outputs/check_app.py
python outputs/check_app_backend.py
```

These require prepared local assets. The backend test runs real inference in temporary storage. Streamlit AppTest additionally exercised demo enhancement, candidate selection, prediction and saved-history views during development. Visual browser QA and multi-user deployment have not been completed.

## Contribution and attribution

Project work covers data auditing/filtering, controlled comparisons, candidate detection and application integration. It does not claim a new enhancement architecture. The pretrained enhancer and public data are credited to their authors. See `THIRD_PARTY.md`, `outputs/Contribution_and_reuse.md` and the experiment READMEs. This project was developed with AI coding assistance; the student should understand and verify the implementation and follow institutional disclosure requirements.
