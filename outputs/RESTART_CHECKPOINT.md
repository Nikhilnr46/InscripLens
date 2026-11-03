# InscripLens restart checkpoint — 4 November 2026

## Authoritative workspace

Work in `C:/Users/nikhi/MCA/Capstone-InscripLens`, branch `main`, remote https://github.com/Nikhilnr46/InscripLens. Do not work in the older Documents/Codex copy or the unrelated parent repository. User prioritizes development over frequent friend packaging. No Phase 3 presentation requested yet in this work segment.

## Current result

Streamlit app: `python -m streamlit run outputs/inscriplens_app.py`. New **Published reading review** view displays Kumbalahalli HS024's opening image region, printed Kannada opening, all eight annotation groups, publication links, uncertainties and JSON export. This is reference-assisted review, not automatic transcription. Navigation smoke checks passed. No browser visual QA or full-text reading verification claimed.

Sources: `outputs/context_reading/README.md` and `HS024_reference.json`. EC IX Hoskote 110: Roman p125 / archive n204, English p102 / n419, Kannada p224 / n729. Local scans and crops reside in that directory but are ignored by Git. The Kannada entry has nine lines (1–5 left, 6–9 right); dataset has eight groups and 98 annotated characters. Opening correspondence is a candidate only. Roman Nelmalla differs from dataset nĕlmalli. Do not silently normalize names, historical characters or missing text. Context describes cattle protection and a land grant according to the edition, not a generated translation.

## Evidence and limits

- Broad cleaned HOG/SVM: 77/300 supplied-box exact label matches (25.67%). Automatic detection plus correct label: 52/300 (17.33%).
- Ranked suggestions: top-three inclusion 122/300, not automatic recognition accuracy.
- Fixed date/genre metadata reranking did not improve development: all variants 63/308. See `outputs/metadata_context_study/`.
- Broad CNN and component grouping did not beat selected baselines. Avoid repeating minor model sweeps without a specific hypothesis.
- Validation reused; pretrained enhancement overlap incompletely known. HS024 publication answers cannot become training hints while retaining independent validation claims.
- Rough completion estimate remains ~50% of original scope, not an audited percentage. Reliable full-text recognition, modern Kannada conversion and English translation remain unfinished. No evidence supports 80%.

## Next useful work

Update after reset: `outputs/audit_sequence_data.py` now audits original training annotations without touching validation. `outputs/sequence_data_audit/summary.json` reports 672 fit and 34 development structurally passing line candidates; local ignored `records.json` retains provenance and flags. Candidate fit labels have 661 whole-label types but 54 Roman Unicode codepoints; development has no unseen codepoints. This supports investigating compositional sequence output, not claiming improved recognition. EasyOCR's published Kannada alphabet lacks historical ಱ/ೞ and differs from our Roman labels. See sequence audit README for sources and proposed bounded CNN–BiLSTM–CTC experiment. Next concrete task: export/inspect a deterministic line-crop sample before training; preserve label boundaries and location splits.

1. Verify a tiny printed passage and preserve uncertainty; user can read/enter a few printed characters but cannot decipher stones. Do not request mass manual transcription. The printed opening crop is ready locally.
2. Establish phrase-to-region correspondence before claiming a complete verified example. Current review page is complete as a source-comparison interface, not a verified transcription.
3. Assess sequence-recognition feasibility using primary papers/repos: available pretrained historical-Kannada models, compatible character inventory, usable line-level training data, licenses and realistic compute. No sequence model chosen or improvement promised yet. Train only after a feasible, bounded experiment is defined.
4. Aim for defensible assisted reading: enhancement, extraction, suggestions, correction and linked references. Original fully automatic pipeline remains uncertain.

## Environment / assets

System Python 3.14 provides app/sklearn. Torch inference uses `work/binarizer_env/Scripts/python.exe` (Python 3.12, CPU). CUDA installation was cancelled; do not assume GPU support. Models/data in ignored local paths. Current preferred recognizer: `outputs/broad_clean_study/mask_svm_bundle.joblib`. Existing runtime archive sent to friend; do not spend remaining allowance rebuilding packages unless materially needed.

User's earlier Aradeshanahalli transcription remains tentative; line 14 extra 'si' must not be removed. No expert response received. Keep publication copying separate from stone decipherment. Unrelated legacy untracked reports should not be swept into commits.
