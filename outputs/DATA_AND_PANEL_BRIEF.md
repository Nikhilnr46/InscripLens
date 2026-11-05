# Current bottlenecks, additional data and panel explanation

Checked 4 November 2026. No new stone accuracy gain is claimed.

## What we actually have locally

- 9,925 training character crops across 109 inscription images, with 764 raw source-label classes. These are image crops, not 9,925 distinct stones.
- 299 classes have one training example; 480 have fewer than five. Historical forms and conjunct labels are highly unevenly represented.
- Reused validation: 300 labelled crops across six images. Current deployed mask classifier:77/300 supplied-box labels (25.67%); automatic localization+correct-label recovery:52/300 (17.33%). Not full-line accuracy.
- Line audit:672 fit/34 development structural candidates; stricter geometry, neighbour and foreground screening leaves124/7 annotation-assisted candidates. They remain unverified line readings. Filters are conservative and can reject legitimate overlapping annotations.
- Four-line training-only check failed:1/4 mask,0/4 original at300 steps. This tests whether the current small model can memorize a tiny subset; it is not a held-out accuracy test. Failure alone does not distinguish bad supervision from model/optimization/decoding weaknesses.
- Newly downloaded Mozhi-Kannada test split:9,838 printed word images with matching Kannada transcriptions. Fixed100 sample: pretrained Tesseract29 exact words,28.69% codepoint CER. Separate book/printed domain.

## The actual problem

We are not starting without data. We lack enough reliably aligned, representative and verified historical line-image/transcription pairs for dependable full-line OCR. Missing/duplicate annotation positions, crops that cut glyphs or include neighbours, sparse enhancement output, uncommon letter forms and many rare label classes all contribute. More photographs without matching readings would increase collection size but not supervised recognition coverage.

Segmentation and recognition are separate errors: supplied-box accuracy is already low, and automatic localization adds another failure source. The Roman source labels also need a verified mapping to historical/modern Kannada; translation then requires correct readings and historical language interpretation. Modern Kannada translation support does not establish Old Kannada translation accuracy.

We cannot claim that no suitable data exists anywhere, or that this audit proves all excluded lines unusable. We can say our current usable, checked set is insufficient to demonstrate reliable full-line OCR. The application, preprocessing, diagnostic classification and review/provenance workflow work; recognition remains experimental.

## Additional sources and APIs verified

1. EpiSAM official dataset: https://ihdia.iiit.ac.in/episam/dataset.html and https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset — inscription images, binary images, character and line masks. Already used locally; downloading it again would not add independent data. CC BY-SA4.0 per dataset card.
2. Mozhi-Kannada: https://ilocr.iiit.ac.in/dataset/8/ — provider lists100,011 printed word/transcription pairs, train80,085/validation10,088/test9,838, CC BY4.0. Test archive acquired; training/validation not acquired. Useful printed OCR benchmark or separate pretraining, not replacement stone labels.
3. IndicSTR12-Kannada: https://ilocr.iiit.ac.in/dataset/31/ — modern scene-text words with transcriptions. The page has inconsistent split counts, so counts should be verified from downloads before reporting. Not downloaded; historical domain mismatch remains.
4. Google Cloud Vision: https://docs.cloud.google.com/vision/docs/languages — Kannada kn listed. Candidate baseline for printed publications. Requires configured service access; no inference run here, and no evidence of ancient-stone accuracy.
5. Sarvam Vision: https://docs.sarvam.ai/api/api-guides-tutorials/models/sarvam-vision and https://docs.sarvam.ai/api/api-guides-tutorials/document-intelligence/languages-formats-limits — Kannada kn-IN document OCR and image/PDF input. Candidate printed-source draft service. No inference run here; benchmark on our fixed inputs before integration. Provider promotional benchmark claims are not our results.
6. IIIT-H/NLTM/Bhashini: https://ilocr.iiit.ac.in/api_list/ — lists Kannada printed, handwritten and scene-text services. Specific Kannada service-detail page returned errors during this check; operational endpoint/access not verified.

APIs return predictions, not ground truth. A useful workflow is publication scan -> OCR draft -> human comparison with printed reading -> match to stone/line -> provenance-labelled training candidate. Do not feed the reference answer to an OCR prompt, assume two models agreeing makes a reading correct, or train on held-out benchmark labels. Context can help review but must not silently fill damaged glyphs.

## Suggested panel explanation

“We have implemented the inscription-processing and review workflow and evaluated an experimental character recognizer. The main limitation is obtaining reliable, aligned supervision for historical line recognition: the data contains rare characters, incomplete annotations and difficult segmentation. We already have9,925 character training crops, but these do not translate into a large verified line-reading dataset. We are auditing the existing data and evaluating external Kannada OCR for printed reference pages. Reliable full-line transcription and translation are not yet completed.”

If asked why not just use an API: “Kannada document OCR can accelerate copying printed readings. Whether it can read ancient carved forms has to be measured. Its output still needs verification before we call it training ground truth.”

## Next concrete work

1. Diagnose the failed tiny-subset experiment with reviewed image/label alignment and a decoding/optimization control before expanding training.
2. Compare one external OCR provider against the fixed printed-word set and independently checked publication lines once service credentials are configured locally; do not paste secrets into chat.
3. Prioritize a small verified set of publication-to-stone line pairs and missing/rare glyph coverage over more unlabelled images. User review of readable printed Kannada helps here; expert stone decipherment should not be assigned to the user.

New scripts, reports and documentation are tracked; large datasets/crops remain local. No paid API use, external inference or model replacement occurred in this step.
