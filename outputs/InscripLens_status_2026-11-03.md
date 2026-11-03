# Implementation checkpoint — 3 November 2026

Rough planning assessment: around halfway (approximately45–50%) against the broad original scope, with substantial uncertainty. This is not a university-approved completion percentage or a weighted requirements audit. Do not claim above50% or80% from this estimate. Application implementation has advanced; reliable recognition and language interpretation remain central unresolved requirements.

## New completed work

- Matched preprocessing experiment: 949 training crops,300 validation; original45/300 versus predicted-mask63/300. Training-only grouped development also improves35/308 to50/308. Fixed classifier settings and save/reload checks.
- Automatic candidate boxes: 196/300 reference matches among330 predictions, IoU0.5; precision59.39%,recall65.33%. Separate from recognition, which still uses reference boxes in evaluation.
- Local Streamlit application: upload/public demo, pretrained enhancement, side-by-side results, candidate box selection/adjustment, experimental character prediction, downloads, dataset explorer, experiment reports, SQLite history/reload.
- Tested navigation and demo enhancement→candidate→prediction→history through Streamlit AppTest. Backend tested invalid input, real inference, binary output, dimensions and persistence; SQLite close bug fixed. Health endpoint200.

## Remaining

- Recognition21% is too weak for dependable transcription. A bounded small CNN experiment now completed:44/300(14.67%), below the mask-SVM63/300(21%). Development-only epoch selection chose11epochs. Pretrained recognition transfer remains untested; adding a small CNN did not resolve the bottleneck.
- Candidate detector is preliminary; no validated end-to-end line/stone transcription.
- Historical-to-modern Kannada and English interpretation unavailable; no verified evaluation corpus established for them.
- Independent final evaluation and full pretraining-overlap audit unavailable.
- Original capstone repository has not been overwritten; development remains in this workspace. Packaging/installation and visual browser QA remain pending.
- Phase3 slides not created. There is now enough real implementation to show a credible partial prototype, but the80% requirement is not met. A scope/feasibility discussion remains appropriate; do not delay solely to force a percentage threshold.

Feasibility: an assisted, evaluated analysis prototype is demonstrable. Reliable automatic stone-to-Kannada-to-English remains unproven. App and database progress must not be mistaken for resolution of the recognition research risk.
