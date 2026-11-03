# Research recheck and targeted experiments — 3 November 2026

Update: the broader cleaned-data experiment subsequently improved supplied-box accuracy to77/300 (25.67%) and automatic localized-and-correct reference recall to52/300 (17.33%). Earlier negative experiments remain below. These reused diagnostic results do not establish reliable full-text OCR.

## What the papers support

[SIFT/HOG retrieval paper](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-ipr.2020.0715) combines descriptors/PCA and ranked retrieval. It supports testing feature representation and retrieval, not assuming its reported90% is transferable to our classification task. This experiment is inspired by representation/normalization ideas, not a reproduction of SIFT+HOG.

[EpiSAM](https://ihdia.iiit.ac.in/episam/) uses sparse prompts and neighboring-character context to improve instance segmentation. It is a more relevant candidate for split/merged glyphs than replacing the classifier alone. A prompted result must disclose prompt origin; reference centres cannot be used at evaluation time and presented as automatic detection.

The historical Tamil OCR abstract previously checked describes augmentation and sequence modeling. Our pilot test below uses only mild rotation; it is not a reproduction of that CNN/BiLSTM system. Current sequence references still need auditing. Do not use weak pseudo-labels to manufacture a large training corpus.

## Experiments completed

Same949train/300validation cohort,641fit/308development sites, fixed SVM C10. Variant selection uses development only. Validation remains reused and binarizer pretraining overlap incompletely known.

1. Feature/crop study: baseline50/308 development, tight32=50, tight64=52, tight64+pixels=49. Development winner tight64 scored56/300 (18.67%) on validation, below baseline63/300. Do not adopt. Source `compare_glyph_features.py`, summary `glyph_feature_study/summary.json`.
2. Augmentation study: baseline50/308 development, +/-7degree rotations49, rotations+balanced class weights49. Baseline selected and reproduced63/300 (21%). No mirroring, no validation augmentation, no automatic labels generated. Source `compare_training_augmentation.py`, summary `augmentation_study/summary.json`.

Both saved models pass reload prediction checks. Failed hypotheses retained rather than omitted. Small development differences did not transfer reliably; further repeated tuning on this split would be weak evidence.

## Next substantive hypothesis

Use broader public training annotations **after applying the same pretrained cleaning**, with conservative location exclusions and an audited label inventory. We tested broad noisy originals previously, not broad cleaned training. This is a specific missing combination, not a promise of improvement. It requires generating masks for roughly110training images, retaining script/period caveats, and evaluating on the same diagnostic protocol before a fresh independent test can be claimed. If attempted, first cache masks and bound runtime; do not relabel validation or treat synthetic variants as independent samples.

For localization, separately evaluate EpiSAM using automatically generated prompts versus explicit user prompts. Its public weights alone do not establish an automatic, accurate pipeline.

Bibliographic clarification: the Wiley page displays first-online24February2021 while its volume/citation metadata uses2020. Earlier notes calling2021 simply incorrect were too categorical. Use the publisher's exported citation consistently; the journal is IET Image Processing, not IEEE Transactions on Image Processing.

## Broader cleaned-data experiment completed

After correcting the Begur filename exclusion, trained on9,925 crops/109 images/764 classes. Hero baseline reproduced63/300 exactly; broader cleaned model77/300, corrected broad originals43/300. Matched hero development improved50/308 to63/308. Automatic-region evaluation improved42/300 to52/300 with unchanged detection. The app prefers the new model when installed. All masks are cached; no new manual transcriptions or pseudo-labels were used. See `broad_clean_study/README.md` and summaries for details and limitations.
