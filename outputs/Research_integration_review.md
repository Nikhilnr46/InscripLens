# InscripLens research integration review

Checked 3 November 2026 against the twelve literature entries in phase2.pptx, slides 8–19. This is a reuse assessment, not a claim of replication. Abstract-only evidence is explicitly limited. No new model has been installed or evaluated in this review. Missing public assets means not located in the inspected sources, not proof they do not exist.

## Review of the twelve entries

| Entry | Evidence checked | Reusable idea and decision |
|---|---|---|
| 1. Preprocessing techniques for recognition of ancient Kannada epigraphs | [Author publication record and PDF listing](https://zenodo.org/records/10460339) | Binarization, smoothing, edges and segmentation. Implementable baseline operations; use controlled comparisons instead of stacking filters without measuring recognition. No trained model located. |
| 2. Hybrid method for enhancement of low-resolution ancient Kannada Stone Inscription images | [Publisher abstract](https://www.sciencedirect.com/science/article/abs/pii/S2212054824000705) | 110-image enhancement study. Consider an enhancement comparator after obtaining complete parameter details. No reusable checkpoint established. Enhancement performance is not OCR accuracy. |
| 3. Digitization and Recognition of Kannada Inscription Dynasty | [Publisher](https://scientifictemper.com/index.php/tst/article/view/2130) | Predicts inscription era. Defer: a separate task requiring era labels, with no immediate solution to character recognition. |
| 4. Kannada Stone Inscription Image Enhancement…YOLO Models | [Publisher methodology summary](https://ijettjournal.org/archive/ijett-v74i4p112) | CLAHE/threshold/morphology and supervised text-region detection. Potential region detector; generic YOLO weights do not recognise historical letters. Need labelled text-region boxes and own training if paper weights unavailable. Reported 85.20% concerns detection, not transcription. |
| 5. SIFT and HOG features for retrieval of ancient Kannada epigraphs | [Publisher full text](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/iet-ipr.2020.0715) | Connected components, SIFT/HOG fusion, PCA, K-D-tree ranked retrieval. Useful for showing similar reference glyphs in an assisted interface. The study describes 100 examples per class and ranked retrieval; it is not equivalent to our single-label classification experiment. Prior HOG/SVM baseline is not a reproduction of this method. |
| 6. Impact of Total Variation Regularization… | [Publisher abstract](https://link.springer.com/article/10.1134/S1054661821010041) | TV denoising plus connected-component segmentation. Tested on digitized estampages, reporting 79.2% character segmentation. A low-cost comparator, but requires testing on rendered stone images; full algorithm parameters not obtained. |
| 7. Kannada Manuscript Digitization through OCR and Machine Learning | [IEEE record](https://ieeexplore.ieee.org/abstract/document/10486458) | Historical Kannada recognition lead; manuscript-to-stone transfer remains untested. Full training recipe/assets not established by the accessible record. Do not claim a reproduction. |
| 8. Optical Character Recognition for Sanskrit Using CNNs | [IEEE abstract](https://ieeexplore.ieee.org/document/8395237/) | CNN recognition and compound characters as classes. Architectural idea transferable; Devanagari label weights cannot directly output historical Kannada. Our many rare compound labels make class design a real concern. |
| 9. Improving Kannada OCR Using a Stroke-Based Approach | [IEEE abstract](https://ieeexplore.ieee.org/abstract/document/8929606) | Generated stroke sequences supplement character images. Promising later experiment for cracks; not an off-the-shelf stroke repair tool. Need complete model/training details before implementation. |
| 10. AI Powered OCR Solution for Tamil Historical Document | [IEEE abstract](https://ieeexplore.ieee.org/abstract/document/11453612) | ResNet50 + BiLSTM, augmentation and pseudo-labeling. Reuse the learned visual-feature/sequence architecture idea, not Tamil output classes. Defer pseudo-labeling while our predictions remain weak; it could multiply label errors. |
| 11. Advanced Deep Learning OCR…Chola Period Tamil Inscriptions | [IEEE abstract](https://ieeexplore.ieee.org/abstract/document/11412629/) | Detection/recognition integration lead. Reported 94.7% is on their task. No public compatible Kannada checkpoint established; TensorFlow/PyTorch are frameworks, not sufficiently specified model architectures. |
| 12. AI-Powered Ancient Inscription Analysis and Translation (Halmidi) | [Publisher full text hosted at ResearchGate](https://www.researchgate.net/publication/400035070_AI-Powered_Ancient_Inscription_Analysis_and_Translation_Halmidi) | Modular OCR/correction/translation architecture. Reusable design, but no downloadable training corpus, weights or sufficiently detailed split/training recipe found in the inspected paper. Treat reported results as author claims, not a reproducible target on our data. |

## Stronger immediate reuse candidates

**Shilalekhya binarization**: [official code](https://github.com/ihdia/shilalekhya-binarization), [project](https://ihdia.iiit.ac.in/shilalekhya-binarization/), [weights listing](https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project/tree/main). The listing includes binarizer.pth (126 MB) and episam.pth (376 MB). Code is MIT; the model repository declares CC BY-SA 4.0. Preserve both notices separately. Checkpoint compatibility and execution are not yet tested. Start with binarization inference, not training from scratch.

**EpiSAM segmentation**: the same release supplies segmentation weights and our existing annotation dataset. Inspect official inference requirements and prompts before calling it automatic segmentation. Annotation-assisted or prompted results must be labelled accordingly. Cropping with supplied boxes is still a separate, diagnostic recognition experiment.

These assets make reuse concrete, but they do not supply a verified historical-Kannada-to-modern-Kannada translator.

## Integration order and acceptance tests

1. Freeze current baselines and record source versions/licenses. Inspect official inference code; create an isolated compatible Python environment. Test one image with a small batch on the 4 GB GPU and record peak memory/runtime.
2. Run Shilalekhya on a predetermined sample covering all validation images. Save original and inferred masks side by side; avoid selecting only attractive outputs. Check published training/test identities against ours first. If overlap is unknown, label this diagnostic inference, not independent generalization.
3. Compare recognition using original versus predicted-mask-derived crops with unchanged annotations and the same data split. Choose preprocessing/settings on training-only grouped development data. Supplied reference masks are not valid inference inputs for a claimed end-to-end result.
4. Train or adapt a small learned visual encoder, initially for the existing character labels. Compare top-1 recognition and optional top-k retrieval separately. Keep the source-label inventory and unseen-class counts explicit.
5. Evaluate actual segmentation separately against annotation boxes/polygons, then evaluate recognition on predicted crops. Source annotations may help prepare training data; validation annotations must not silently guide inference.
6. Use line numbers/character positions to prepare candidate ordered line references for future CRNN training. First audit duplicates, missing labels and sequence conventions. Do not silently join uncertain fragments into verified Kannada sentences.
7. Add correction and interpretation only with explicit provenance and evaluation. Retrieval of a published reading can be useful in the app, but must be displayed as a source reference rather than a model translation.

A small set of measured components is preferable to implementing every cited technique. Current priority: pretrained binarization, learned recognition, then segmentation integration. TV/CLAHE remain comparators; ranked glyph retrieval is an optional review feature. Dynasty prediction and stroke-generation training are deferred.

## Presentation corrections to retain

- SIFT/HOG publisher citation is **IET Image Processing, December 2020**, not IEEE Transactions on Image Processing (2021).
- Digital Applications in Archaeology and Cultural Heritage is not an IEEE journal; remove the IEEE tag on slide 9.
- Dynasty paper DOI contains SCIENTIFICTEMPER: 10.58414/SCIENTIFICTEMPER.2025.16.10.03. The deck omits a C.
- Keep enhancement, segmentation, retrieval, recognition and translation results in separate columns with their datasets/protocols. Do not combine their percentages into a projected pipeline accuracy.
- Slide 22's two Rajithkumar rows require independent bibliographic verification before reuse; they are not identified among the twelve extracted detailed entries.

Original presentation remains unchanged. No accuracy improvement or completion-percentage increase is claimed from this review.
