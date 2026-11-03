# Paired original-image and mask features

Run `python outputs/compare_paired_features.py` with the existing local training archive, manifests and cached masks.

This is a fixed development-only comparison, not a new production model. Both runs use the same 9,566 fit characters and 359 development characters, including the same 308 hero-stone development examples. All six validation locations are excluded. No validation images or labels are used for scoring. Original and predicted-mask crops use the same source boxes and median-filtered HOG extraction. The paired representation concatenates equal 324-element blocks (648 total). Both classifiers use RBF SVC C=10, gamma=scale; no weight or hyperparameter search.

| Representation | Hero development correct / 308 | All development correct / 359 |
| --- | ---: | ---: |
| Mask HOG | 63 (20.45%) | 78 |
| Original + mask HOG | 67 (21.75%) | 82 |

The candidate fixes 13 hero-subset errors and introduces nine, giving a net gain of four (1.30 percentage points). This is a small descriptive improvement on reused development data; statistical reliability and generalization are not established. It supports further checking of complementary visual evidence, not a claim that the dataset or recognition problem is solved. Gamma=scale is automatically recalculated for each feature representation.

The original baseline was reproduced exactly. Mask/image dimensions, source-label correspondence, finite features and split counts were checked. Prior mask-only HOG+pixel experiments were different from this original-image plus mask comparison.

No validation evaluation, full-training refit, saved production candidate or application change occurred. Existing deployed supplied-box accuracy remains 77/300. Next: freeze this configuration, refit on the full allowed training set, and compare once on the existing validation set with explicit reused-validation caveats. Do not report development gain as improved deployed accuracy.
