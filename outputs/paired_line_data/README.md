# Paired line training candidates

Run `python outputs/prepare_sequence_crops.py` if the earlier prepared records are absent, then `python outputs/prepare_paired_lines.py`. Both require the existing EpiSAM archive and local predicted masks. The earlier sequence annotation audit must already have generated records.json. Generated crops/records remain local; scripts and aggregate evidence are tracked.

The new exporter preserves RGB originals and predicted masks in matching coordinates. Its support region is the union of each supplied line polygon and its own supplied character polygons. This avoids cutting those annotated polygons at the original line boundary. Pixels outside support are neutral grey in originals and black in masks. This is annotation-assisted preparation; the application cannot generate these crops without such annotations.

Eligibility requires at least 20 mask foreground pixels per character, no polygon extending outside the image, and no more than 5% overlap with any other annotated character polygon. The neighbour denominator is the whole neighbouring polygon. Overlapping annotations can cause conservative false rejections. Missing annotations can cause contamination to escape detection. Thresholds were fixed as data-quality rules, not tuned on recognition performance.

| Split | Structural candidates | Previously eligible | New stricter eligible | Newly recovered | Previously eligible now flagged |
|---|---:|---:|---:|---:|---:|
| Fit | 672 | 207 | 124 | 62 | 145 |
| Development | 34 | 21 | 7 | 1 | 15 |

This is a smaller, more conservatively screened set, not a claim that dataset size or recognition accuracy increased. The broad training corpus contains different inscription types, not exclusively hero stones. All six validation locations are excluded, fit/development sources are disjoint, and labels retain source Roman transliterations with explicit `|` boundaries. No words, missing characters or translations were invented.

A deterministic six-source contact sheet of newly eligible crops was visually inspected. It confirms preserved target geometry and paired coordinates, but visible mask stroke loss persists in some examples. All 706 exported pairs passed matching-dimension and in-image target-polygon retention checks. These checks cannot verify transcription completeness or correctness.

Next: inspect the stricter subset and repeat the bounded tiny-subset learnability gate with fixed input/model settings. Do not train a large recognizer or claim held-out line accuracy from this audit. Existing earlier CTC result remains 3/4 training examples fitted, with no generalization evidence.

EpiSAM source annotations and images retain their existing CC BY-SA attribution; these crops are derived data, not newly authored ground truth.

## Bounded learnability check

Run `work/binarizer_env/Scripts/python.exe outputs/check_sequence_learning.py --paired-view mask --preserve-height --pack-lengths --max-steps 300` (replace mask with original for the paired comparison). The same four shortest multi-label fit lines, from distinct sources, are selected before training. Full eligible-fit alphabet, same seed/model/optimizer/budget, no development or validation access.

Predicted-mask view: 1/4 exact training sequences after 300 steps. Original grayscale view: 0/4. Both fail the required 4/4 gate. These four examples differ from earlier experiments, so this is not an accuracy comparison with the old 3/4 result. Tiny-subset memorization would still not prove generalization even if successful. No large training run started and no runtime model changed.

Visual comparison against the archive's binary images shows incomplete strokes in some selected examples; even supplied binary images can be sparse. The minimum 20 foreground-pixel filter does not establish glyph completeness. Next investigate source-aligned glyph quality and decoding/optimization controls on a reviewed tiny subset; do not assume adding epochs or more unreviewed images solves the issue.

## 5 November: decoding control passed

The same fixed mask-view four-example training run (seed42,300steps, unchanged CNN/BiLSTM/CTC) was repeated with lexicon-free CTC prefix beam decoding, width10. Greedy still reproduces1/4 sequences; beam decoding reproduces4/4: `0|na`, `a|vi`, `śrī|śrī`, `l̤i|grā`. Decoder receives only model log probabilities, not targets/dictionary/publication context. Prefix-beam implementation was checked against exhaustive aggregation of all CTC paths on32 small random cases, plus repeated-symbol/blank cases.

This passes a tiny-subset memorization gate and establishes decoding as one limitation of the previous check. It does not establish generalization, transcription correctness, or feasibility of reliable arbitrary-stone OCR. No development/validation inference or production sequence-model promotion occurred. Next step is a fixed, bounded training run on the screened fit set with separate development sequence error measurement, preserving all corpus data for other experiments.

Reproduce: `work/binarizer_env/Scripts/python.exe outputs/check_sequence_learning.py --paired-view mask --preserve-height --pack-lengths --beam-width 10`. Report: learnability_mask_beam10.json.
