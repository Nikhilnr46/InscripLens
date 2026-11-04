# Printed Kannada diagnostic on additional public data

Official dataset: https://ilocr.iiit.ac.in/dataset/8/ (IIIT-H NLTM OCR, Mozhi-Kannada). The provider lists 100,011 printed word/transcription pairs from 1,000 scanned book pages, including 9,838 test words; CC BY 4.0. This is printed Kannada, not ancient stone lettering. Cite and attribute IIIT-H/Mozhi when using derived material.

Downloaded only the separate test archive from https://ilocr.iiit.ac.in/public/printed/phase-0/v0.5/kannada/akshara/test.zip to work/mozhi_kannada/test.zip. Size 45,595,591 bytes; SHA256 recorded in summary.json. Archive contains 9,838 unique reference filenames. Data remains local and is not included in Git.

Run `python outputs/evaluate_mozhi_printed.py`. Fixed 100 samples by ascending SHA256 of filename; pretrained Tesseract Kannada, OEM1, PSM8 (single word). No image preprocessing or test-set tuning. NFC normalization and outer whitespace stripping only; punctuation and internal spaces preserved.

Result: 29/100 exact word matches; 200 Levenshtein edits /697 reference Unicode codepoints =28.6944% codepoint error rate. This is not grapheme error, full-line accuracy, a full test-set score, or a result from the InscripLens stone classifier. Pretrained OCR overlap is unknown. Predictions are local generated artifacts.

The additional dataset supports a reproducible printed-text benchmark and possible separate pretraining work after acquiring its training split. Never train on this test split. A comparison with an external OCR service must use the identical fixed images, without supplying reference text in prompts; provider output stays unverified until reviewed.
