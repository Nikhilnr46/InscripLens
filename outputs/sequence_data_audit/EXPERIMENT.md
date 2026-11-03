# Crop inspection and bounded CTC check

## What was run

`prepare_sequence_crops.py` exported all 706 structurally passing candidate line groups from existing predicted masks. A deterministic eight-source sample was visually inspected. Plain rectangles contained neighboring lines. Applying supplied line polygons removed neighboring text, but several inspected polygons also visibly clipped target strokes. No source text was manually corrected.

A second audit measures how much of each original character polygon falls inside its supplied line polygon. Requiring at least 95% containment for every character leaves **253 fit and 23 development lines**, down from 672 and 34. This is geometry agreement, not verified transcription or recognition accuracy. Both annotation types can be inaccurate, and even a passing polygon can truncate meaningful strokes. Crops use supplied localization, not automatic detection.

`check_sequence_learning.py` ran a fixed-seed, CPU, four-line overfit check using only fit locations. It selected the shortest eligible sequences with at least two labels from four distinct sources. The model is a small CNN, bidirectional LSTM and CTC output over Roman codepoints plus a label separator. Images have height 48; target timestep feasibility and finite loss are checked. Maximum budget: 300 steps with a 4/4 exact-training-sequence pass criterion.

## Result

**Failed the pre-training gate: 0/4 exact training sequences at step 300.** Loss decreased from 2.819 at step 25 to 0.563 at step 300. Predictions remained incomplete. See `overfit_check.json` for exact targets, predictions and trace. No development or validation recognition was run; no production model changed. This is a failure of this bounded configuration, not proof that sequence models cannot work.

## Next diagnosis

Inspect these exact four crops against their labels before extending the budget. The CNN currently averages over image height, potentially discarding vertical mark information; test preserving vertical features only after checking supervision. Check the effect of padded sequence lengths on the bidirectional LSTM. Any revised sanity experiment must save its own report and pass the same four-sequence gate before a larger run. Longer training alone is not yet justified by held-out evidence.

The initial data audit was necessary but insufficient. The useful outcome here is identifying geometric supervision problems before expensive training. No project completion or OCR accuracy increase is claimed.
