# What is blocking current recognition?

Reproducible command: `python outputs/audit_recognition_failures.py`. This audits saved predictions from the frozen broad cleaned SVM; no model or labels changed.

| Training examples for reference label | Validation examples | Correct |
| --- | ---: | ---: |
| None | 7 | 0 |
| 1–4 | 23 | 0 |
| 5–19 | 61 | 4 |
| 20 or more | 209 | 73 |

There are 223 incorrect predictions. Disjoint descriptive groups: 7 unseen labels; 7 constant masks; 22 nonconstant masks with 1–4 training examples; 56 with 5–19; **131 with at least 20**. Categories prioritize unseen labels, then constant masks, then support. Nonconstant does not imply a good mask, and training support does not guarantee similar carving styles or correct source labels.

## Decision

The evidence does **not** support treating a missing dataset as the sole blocker. The project has usable data, though sparse classes, annotation quality and cross-inscription variation remain limitations. Large numbers of familiar-label errors point to a recognition/input representation problem worth investigating. This is descriptive evidence, not causal proof of which component is responsible.

Stop broad dataset hunting and stop treating printed-book OCR as proof of stone-model improvement. The user's printed heading is the checked reference for that particular comparison. Keep the separate Tesseract draft-review feature as supporting functionality.

Next bounded stone experiment should preserve more visual evidence: compare paired original-image and predicted-mask features against mask-only features, using the existing training/development location split. Preserve baseline preprocessing, fit the comparison without validation labels, and decide on development before any new validation run. Earlier original-only results were worse, but that does not test complementary original-plus-mask evidence. First inspect existing scripts to avoid repeating an already completed fusion experiment. Do not claim this will improve performance in advance.

The sequence recognizer remains experimental and has not passed its four-example sanity gate. It should not displace the working SVM. No change in project completion or deployed accuracy follows from this audit.
