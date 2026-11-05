# Presentation test evidence — 4 November 2026

The slide IDs T01–T12 identify behaviours, not a percentage of total test coverage. A successful classifier request is not evidence that its label is correct.

| ID | Expected result | Actual observed result | Evidence and timing |
|---|---|---|---|
| T01 | Status/demo/root/Studio return 200 and readiness flags true | Passed | Recorded onboarding responses; STUDIO_STARTUP_VERIFICATION.md |
| T02 | Demo analysis returns mask and candidate boxes | 133 regions; one measured run 23.37 s | Recorded real inference during onboarding |
| T03 | One prediction per demo candidate | 133 predictions | Recorded batch endpoint response |
| T04 | Missing image, missing batch ID, reversed crop geometry are rejected | All three HTTP 400 | Recorded negative API checks during onboarding |
| T05 | Saving and retrieving QA review preserves unverified status | Passed; empty suggestion and model_prediction_unverified | Recorded API round-trip; reviewer STARTUP_QA |
| T06 | Kannada correction and original prediction remain separate | Passed; Kannada suggestion retained alongside original ka | check_review_storage.py rerun for this review |
| T07 | Unknown run, negative and out-of-bounds review boxes rejected | All three raised ValueError | check_review_storage.py rerun |
| T08 | Non-image input rejected without saving analysis | Exception; empty history | check_app_backend.py rerun |
| T09 | 512 x 512 patch produces same-size binary mask and persisted run | Passed: 512 x 512; values limited to 0/255; history reload/hash check | check_app_backend.py rerun with real worker inference |
| T10 | API dimensions match processed 1600 x 800 canvas | Passed | check_studio_api.py rerun, mocked analysis return; not a full inference resize test |
| T11 | Export retains two reviews and marks ground truth false | Passed; source prediction retained and machine image_path omitted | check_review_storage.py rerun |
| T12 | Four-example sequence memorization reaches 4/4 before scaling | Gate not met: 3/4 after 600 steps | Prior recorded sequence_data_audit experiment; not rerun |

## Commands rerun
```powershell
.\work\studio_env\Scripts\python.exe outputs/check_review_storage.py
.\work\studio_env\Scripts\python.exe outputs/check_studio_api.py
.\work\studio_env\Scripts\python.exe outputs/check_app_backend.py
```

All three exited successfully. The backend script emitted a Pillow getdata deprecation warning; no assertion failed. No model weights, application behaviour or test implementation were changed in this presentation review.

## Recorded outputs
- Review: PASS review persistence, Unicode, validation, original prediction preservation and portable export.
- Canvas: Ran 1 test; OK.
- Backend: PASS invalid upload, worker inference, output dimensions, binary mask, SQLite persistence/reload.

The API evidence is from the same day's preceding onboarding run, not a new API rerun. Raw health and sanitized workflow summaries are in `TEST_OBSERVATIONS.json`. Private run IDs and image paths are not needed for the presentation.
