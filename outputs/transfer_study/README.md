# Frozen pretrained recognition features — 3 November 2026

ResNet18 ImageNet features with a fixed SVM produced46/300 source-label matches (15.33%). This is below the mask-HOG/SVM63/300 (21%). Application default remains unchanged. Generic pretraining alone did not solve recognition in this bounded setup; fine-tuning or script-specific pretraining has not been tested.

Source encoder: torchvision0.20.1+cpu ResNet18 IMAGENET1K_V1, torch2.5.1+cpu. Official documentation: https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.resnet18.html . Downloaded weights cached under work/torch_cache. No historical-Kannada pretraining claim.

Input:224px aspect-preserving letterbox with median RGB fill, ImageNet mean/std normalization. This deliberately differs from standard resize/centre-crop to avoid truncating glyph edges. Frozen512-dimensional features, L2 normalization, fixed RBF SVM C10 gamma scale. Same949training/300validation cohort and641fit/308development sites as prior experiments. Original input development20/308, mask37/308; mask selected solely on development. Only selected variant evaluated on validation. Feature extraction about58seconds CPU total. Saved head reload predictions checked.

Limitations: source annotation boxes and unreviewed raw labels; reused validation; incompletely known binarizer pretraining overlap. This is neither an independent final test nor an end-to-end transcription score. No accuracy improvement or completion increase claimed.

Reproduce: work/binarizer_env/Scripts/python.exe outputs/extract_transfer_features.py, then system python outputs/evaluate_transfer_features.py. Features, exact records, predictions, selected classifier and summary saved here. Encoder weights remain in workspace cache; no training job remains active.

Credit: ResNet architecture and torchvision pretrained encoder are external components. Project contribution here is the controlled comparison and integration/evaluation code, not inventing ResNet. Data and mask provenance remain as documented in ../EpiSAM_source_README.md and ../full_binarizer/README.md.
