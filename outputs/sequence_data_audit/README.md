# Sequence recognition feasibility — 4 November 2026

## Local audit

Run `python outputs/audit_sequence_data.py`. The script reads original training character annotations and line polygons from the existing EpiSAM archive. All six validation locations are excluded, including filename-prefix variants; development locations remain separate. It does not inspect validation labels. Raw annotation totals exceed the classifier's filtered crop totals because this audit deliberately retains incomplete annotations to flag them.

Of 862 fit line groups, 672 pass initial structural checks; 34 of 46 development groups pass. Checks reject missing/noncontiguous positions, duplicate positions, missing line polygons, empty/uncertain labels, and horizontal center-order reversal. These are candidate sequences, not verified complete readings: absent terminal glyphs, unlabeled regions, unusual layouts and source transcription errors can escape these checks. Flags can also reject legitimate layouts.

The candidate fit labels contain 661 distinct whole-label types but only 54 Unicode codepoints in their existing Roman transliterations. All codepoints in the candidate development labels occur in fit. This motivates testing compositional sequence output rather than treating every conjunct as an unrelated class. It does not establish learnability or accuracy. Preserve original label boundaries with an explicit separator if training character-level output; do not invent word spaces or convert to Kannada without a verified mapping.

## Primary-source checks

- [EpiSAM dataset description](https://ihdia.iiit.ac.in/episam/dataset.html) lists character and line masks. Local archive confirms line polygons plus character order and labels. These assets make candidate line preparation possible without retyping all inscriptions. Existing EpiSAM CC BY-SA attribution applies.
- [EasyOCR model hub](https://jaided.ai/easyocr/modelhub/) provides Kannada pretrained weights. Its [model configuration](https://github.com/JaidedAI/EasyOCR/blob/master/easyocr/config.py) lists an alphabet lacking historical Kannada ಱ and ೞ. It outputs Kannada/Latin characters, while our labels use Roman transliteration with diacritics. Off-the-shelf exact label evaluation is therefore incompatible without a verified mapping or adapted output head. Its [repository](https://github.com/JaidedAI/EasyOCR) identifies Apache-2.0 licensing; checkpoint redistribution terms should be checked before packaging weights. No checkpoint downloaded or tested in this step.
- [EpiSAM project](https://ihdia.iiit.ac.in/episam/) describes neighbor-aware segmentation, not a pretrained historical Kannada text recognizer. Do not present segmentation weights as a solution to recognition.

No ready-to-use historical Kannada sequence checkpoint was verified in this bounded search. That is not evidence none exists. Modern printed/scene-text Kannada performance does not establish performance on ancient carved glyphs.

## Proposed bounded experiment

1. Export original and existing predicted-mask crops for structurally passing training/development lines, preserving source polygons, labels and location split. Inspect a small deterministic sample for missing glyphs and wrapped/curved layout before training.
2. Test a small CNN–BiLSTM–CTC recognizer that emits the existing Roman codepoints plus an explicit label separator. Check output timestep capacity against label length, including repeated symbols. The source labels are unreviewed supervision, not expert truth.
3. Fix architecture and a bounded CPU training budget; select only on development. Compare sequence edit error against the current classifier applied in source annotation order. Report that this baseline has supplied boxes/order and is not automatic full-page OCR. Report exact line accuracy separately; keep codepoint error separate from whole-label accuracy.
4. Stop if data inspection or a tiny-subset overfit check fails. Do not use HS024's published reading, validation labels or plausible historical stories to repair training supervision. Do not change the app recognizer until a measurable development benefit is demonstrated.

Current result: data feasibility audit completed, model training not begun, existing recognition scores unchanged.
