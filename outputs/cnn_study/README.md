# Bounded learned-recognition experiment — 3 November 2026

Result: small CNN trained from scratch matches44/300 validation labels (14.67%). Matched mask-SVM remains better at63/300 (21%). Keep the SVM as the application's default. This experiment does not justify a higher readiness or completion estimate.

Training cohort:949 predicted-mask character crops,281 raw labels, excluding all six validation locations. Same training-only site development split as matched-mask study:641 fit,308 development. Model: three convolution/ReLU/max-pool blocks (16/32/64channels),64px grayscale letterbox,128-unit hidden layer,dropout0.2. Adam lr0.001,weight decay0.0001,batch32,seed42. No augmentation or pretrained recognizer.

A predeclared30-epoch development run selected epoch11 (39/308 correct), choosing the earliest maximum. Model was reinitialized and fitted to all949 crops for11epochs before evaluating300 validation examples. The SVM's comparable development result was50/308. Declining training loss with unstable/lower development performance suggests overfitting; this is not proof of a unique cause.

Validation29/300 references have classes absent from recognizer training. Source labels/boxes are unreviewed, validation has been reused, and pretrained-binarizer training overlap is incompletely known. This is a diagnostic comparison, not an independent end-to-end OCR benchmark. The result does not rule out a pretrained recognition encoder, more consistent labels, or larger training data; it does show that simply adding a small CNN did not solve the problem.

Checkpoint load/reload predictions were verified. Runtime54.36seconds on CPU for development+refit+evaluation. Code outputs/train_small_cnn.py; weights character_cnn.pth; complete development trajectory development.json; final metrics summary.json; per-crop predictions predictions.json. Application Experiment results includes this result; inference still uses the better mask-SVM.

Reproduce from workspace:

```powershell
& work/binarizer_env/Scripts/python.exe outputs/train_small_cnn.py
```

Decision: retain enhancement/candidate detection/assisted review as working modules. Reliable full-stone recognition and historical conversion/translation remain unproven. Do not promise imminent full automation from the current evidence. Any further recognition experiment should target a specific remaining hypothesis, such as pretrained feature transfer, rather than repeat unconstrained tuning.
