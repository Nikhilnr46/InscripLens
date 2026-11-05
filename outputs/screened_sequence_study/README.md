# Screened sequence diagnostic

## 5 November: first larger sequence diagnostic

Fixed10-epoch CNN-BiLSTM-CTC run on124 screened fit lines,7 separate development lines. Alphabet fit-only, source-disjoint splits, image-only resizing height48/minimum width256/max1024. Initial minimum64 failed CTC capacity on a training line, so fixed minimum256 before training. No validation-stone access or model promotion.

Result: greedy0/124 exact training lines and0/7 development, both100% codepoint error. Development beam width10:0/7 exact,131 edits/172 source Roman codepoints=76.16% CER (including separators). Training loss9.74 to3.28. The earlier four-line memorization success does not yet scale to this larger mixed set. Ten epochs is an initial budget, not a convergence or impossibility result. Next investigate training blank collapse/optimization on increasing sample counts, measure training beam accuracy, and compare a frequency-only baseline before claiming visual generalization. Full data remains available; this screened subset is diagnostic.

Reproduce with work/binarizer_env/Scripts/python.exe outputs/train_screened_sequences.py. Local checkpoint sequence_model.pth is ignored by Git. Application remains unchanged; http://127.0.0.1:8001/studio responded during this session.

