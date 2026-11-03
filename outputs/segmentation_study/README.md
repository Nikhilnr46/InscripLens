# Automatic candidate-region baseline

Predicted masks are processed with 8-connected components; discard area below 12 pixels or width/height below 3. No reference boxes guide detection. Reading order and character completeness are not inferred.

Six validation images: 330 candidate boxes, 300 filtered reference boxes, 196 one-to-one matches at IoU >=0.5. Precision 59.39%, recall 65.33%. Assignment maximizes valid matches, with IoU as tie-breaker. Fixed rules, no threshold search.

These are candidate-region localization metrics, not recognition accuracy. References exclude placeholders and invalid/duplicate annotations; actual but unlabelled symbols may count as false positives. Disconnected strokes may split one letter into multiple components; touching letters may merge. Binarizer pretraining overlap is not fully documented.

The app displays numbered candidates and allows a user to adjust the rectangle before requesting a character prediction. Cropped recognition accuracy of21% was measured using supplied boxes, not these predicted candidates. No end-to-end transcription score has been established.

Run `python outputs/segment_candidates.py`. JSON contains all predicted boxes and per-image metrics. Overlays are derived from EpiSAM images; CC BY-SA4.0 attribution and source details are in ../full_binarizer/README.md and ../EpiSAM_source_README.md.
