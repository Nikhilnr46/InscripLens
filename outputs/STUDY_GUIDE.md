# InscripLens study guide for the next presentation

Study in the order below. For every topic, be able to explain **what it does, why this project needs it, how we used it, and its limitation**. Search phrases are provided so you can learn independently; they are not claims that a particular course has been checked.

## 1. Essential project understanding — learn first

| Topic / search phrase | What to understand | Our use / status |
| --- | --- | --- |
| OCR pipeline: preprocessing, detection, recognition, postprocessing | Finding text is different from identifying it; translation is a further task | Enhancement, candidate detection, experimental labels and review work; dependable full-text recognition and translation do not |
| Historical Kannada OCR challenges | Erosion, low contrast, changing glyph shapes, conjuncts, vowel marks, curved text and limited verified data | These explain why modern printed OCR is not a direct solution |
| Binarization versus thresholding | Foreground/background separation; learned models versus fixed or adaptive intensity thresholds | Shilalekhya pretrained enhancement produces masks; it can also erase strokes |
| Semantic segmentation versus instance segmentation | Pixel classes versus separate character instances | Enhancement masks are not automatically separated character identities; EpiSAM provides character/line annotations |
| Connected components and bounding boxes | How adjacent foreground pixels form candidate regions; broken and merged characters | Current automatic character proposals; grouping experiments did not improve the chosen baseline |
| HOG: Histogram of Oriented Gradients | Local edge direction histograms encode shape | Features for the current character classifier |
| SVM, RBF kernel, C and gamma | Margin-based classification; nonlinear similarity; regularization | Current preferred recognizer is a standard HOG/SVM trained on broader cleaned data |
| Train, development and test splits; data leakage | Tune on development; keep related locations out of fit; repeated validation reduces independence | Location exclusions applied; validation has been reused and enhancement pretraining overlap is incompletely known |
| Exact-label accuracy versus end-to-end accuracy | Supplied boxes remove detection errors; automatic localization adds another failure stage | 77/300 = 25.67% supplied-box recognition; 52/300 = 17.33% correct automatic localization plus label |
| Human-in-the-loop recognition | Alternatives support review; a person may accept, reject or correct | App offers ranked labels, training examples, saved corrections and export; reviewer success has not been measured |

Practice: explain the pipeline from uploaded image to saved result in two minutes without saying the system already translates inscriptions.

## 2. Evaluation — important for panel questions

- **Precision, recall and Intersection over Union (IoU):** explain why a detected box counts as a match, why matching is one-to-one, and how false/missed detections affect results.
- **Top-1 versus top-k inclusion:** top-three inclusion is 122/300 (40.67%). It means the reference label appears among three suggestions, not that OCR accuracy is 40.67%.
- **Class imbalance, rare labels and singleton classes:** current broad classifier has 764 label types, with many rare conjunct labels. More classes do not imply more useful examples per class.
- **Unseen classes and domain shift:** historical period, location, carving style and image quality differ; training performance does not prove transfer.
- **Baseline, controlled comparison and ablation:** change one relevant factor and compare on the same protocol. Negative results are evidence, not an implementation failure to hide.
- **Overfitting and underfitting:** memorizing four examples is a sanity check, not generalization. Low loss is not the same as exact decoded output.
- **Annotation quality versus image quality:** correct positions can coexist with missing labels or blank enhanced pixels. Geometry checks and visual inspection are both needed.
- **CER / edit distance / exact sequence match:** sequence evaluation measures insertions, deletions and substitutions; codepoint errors are not automatically equivalent to errors in Kannada graphemes or whole character labels.

Practice: explain why 25.67%, 40.67% and roughly 50% refer to three different things: character accuracy, suggestion inclusion and a rough project-completion estimate.

## 3. Deep learning and current experiments — learn after the essentials

| Topic / search phrase | What matters here | Status |
| --- | --- | --- |
| CNN convolution, pooling, feature maps | Extract visual features; pooling may discard important marks | Small character CNN experiments completed; did not beat the selected SVM |
| Transfer learning and pretrained feature extraction | Reuse representations; source-domain performance need not transfer | Frozen pretrained-feature experiment completed; no improvement over selected recognizer |
| U-Net encoder decoder skip connections | Combine broad context with detailed localization | Background for the reused enhancement component, not a new architecture invented by this project |
| LSTM and bidirectional LSTM | Model order and surrounding sequence context | Small experimental sequence recognizer only |
| CRNN: CNN plus recurrent sequence model | Convert an image into a sequence of visual features and symbols | Feasibility investigation; not deployed OCR |
| CTC loss, blank symbol and decoding | Train without explicit symbol-to-timestep alignment; collapse repeats and remove blanks | Tiny-subset sanity experiment; first run failed exact reproduction |
| Variable-width batching, padding and sequence lengths | Prevent padded image regions from influencing sequence interpretation | A diagnostic concern in the prototype |
| Unicode codepoints versus graphemes, transliteration and normalization | One visible conjunct may map to multiple symbols; preserve historical distinctions | Dataset uses Roman transliteration. Sequence candidates have a smaller compositional alphabet; conversion to Kannada is not yet verified |
| Language priors and contextual reranking | Context may help disambiguate but can introduce plausible wrong readings | Date/genre prior experiment showed no gain; published reading is a separate reference, not a hidden answer for OCR |

The initial four-line sequence test achieved 0/4 exact training lines after 300 steps. Later visual inspection found one blank crop and sparse strokes in the others. Therefore do not conclude that CTC cannot work; the test revealed a supervision/input problem as well as possible model limitations.

## 4. Application and engineering

- **Python, NumPy and Pillow:** arrays, image dimensions, masks, crops and resizing.
- **scikit-learn and model persistence:** feature extraction, SVM prediction, saving/loading model bundles.
- **PyTorch:** tensors, forward pass, loss, gradients, optimizer, CPU training and inference.
- **Streamlit:** upload widgets, navigation, tables, image display and downloads.
- **SQLite and JSON:** local history/review storage and portable structured exports.
- **SHA-256 and provenance:** identify exact source files/model versions; retain original predictions when corrections are saved.
- **Git/GitHub, branches and .gitignore:** source code is versioned; large model/data assets remain separate. A code push does not upload ignored images or models.
- **Reproducibility:** fixed seeds, explicit splits, recorded parameters, saved reports and declared preprocessing.
- **Smoke tests versus end-to-end tests:** navigation checks prove views render without exceptions, not that every OCR result is correct.

## 5. Research, sources and honest claims

- Learn the roles separately: **Shilalekhya = reused enhancement research/model; EpiSAM = segmentation research and annotated data; Mythic Society = source imagery attribution; Epigraphia Carnatica = published readings and interpretation.**
- Understand **MIT / Apache-2.0 / CC BY-SA**, attribution and the distinction between code, dataset and weight licensing. Check the actual asset's terms before redistribution.
- **Published reading, dataset annotation and model prediction are three separate records.** Agreement between related sources is not automatically independent verification.
- **Transcription, transliteration, modernization and translation are different tasks.** Do not describe a published English interpretation as an InscripLens translation.
- Your contributions include dataset filtering/provenance, integration, controlled comparisons, detection/review workflows and the local application. Reused components must be acknowledged; no novel neural architecture is claimed.

## Questions to rehearse

1. What problem does InscripLens solve today, and what remains unfinished?
2. Why use HOG/SVM when deep learning is available?
3. Why are published paper accuracies not directly comparable to our results?
4. How did you prevent training and validation locations from mixing?
5. What happens when enhancement removes a stroke or joins two characters?
6. What does the reviewer see, and how are corrections kept separate from predictions?
7. How does the project use published readings without leaking answers into evaluation?
8. Which components did you implement, and which did you reuse?
9. What did the unsuccessful experiments teach you?
10. What evidence would justify adopting the sequence model?

## Short study schedule

If time is limited: first study section 1 and the metrics in section 2. Next rehearse the ten questions using the app. Then study CNN/LSTM/CTC in section 3. Leave advanced architecture derivations until you can explain the current implementation and limitations clearly. The presentation itself will be prepared in the next session as requested.
