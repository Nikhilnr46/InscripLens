# Training-scope comparison

Both experiments use median preprocessing, the same gradient features and a fixed RBF SVM (C=10, gamma=scale). All source training images from filename-derived validation locations were excluded before training. Exact duplicate validation crop pixels were also excluded. No hyperparameter tuning was performed.

| Training scope | Images | Crops | Label classes | Correct / 300 | Accuracy | Validation crops with unseen labels |
|---|---:|---:|---:|---:|---:|---:|
| Hero-named images only | 17 | 949 | 281 | 45 | 15.00% | 29 |
| Broader source inscription images | 110 | 9,986 | 768 | 47 | 15.67% | 7 |

The broader model improves by two predictions (0.67 percentage points) while increasing label coverage. This is not evidence of a statistically meaningful gain or reliable recognition. The broader training set also increases the class inventory, so this is not a pure sample-count ablation with a fixed set of classes.

These results must be compared with each other, not directly treated as an improvement over the earlier 48/300 run: that run did not apply this additional location exclusion. The same validation set has been examined in earlier experiments and is not a fresh final test.

Source labels, supplied boxes, source-version uncertainty and unverified script/language composition remain limitations. Site grouping is inferred from filenames; it does not establish complete physical-stone identity resolution. No full-stone OCR, segmentation or translation has been measured.

Saved: both model bundles, prediction records, classification reports, training-record provenance and scope_summary.json. Model save/reload prediction checks passed.

Reproduction from this chat workspace:

```powershell
python outputs/compare_training_scope.py work/episam_dataset.zip work/hero_pilot outputs/training_scope_study
```

Source dataset and attribution: EpiSAM, https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset ; public release declares CC BY-SA 4.0. Authors: Arnav Sharma, Pratyush Jena, Amal Joseph, Ravi Kiran Sarvadevabhatla; image source credited by release: Mythic Society Bengaluru.
