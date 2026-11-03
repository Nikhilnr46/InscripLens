# Character-review workflow

After enhancement and a single-character prediction, save the prediction alone or add a suggested label, reviewer identifier and source note. Each save appends a record; it never overwrites the model output. This supports review and collection of candidate examples, not automatic correction of inscriptions.

The SQLite character_reviews table links to an analysis and stores the bounding box, UTC timestamp, original prediction, model filename and SHA256, suggestion, reviewer/note and unverified status. Bounds must fit the analysis image. Analysis images may be EXIF-oriented and resized; coordinates do not refer to original-upload pixels.

Saved analyses show review records and export a JSON package with source image hash and processing details. Absolute image paths are excluded from that export. Review names and notes are intentionally included: check them before sharing. Images themselves are not embedded in the JSON. No automatic training import or expert-verification claim.

Run `python outputs/check_review_storage.py` for Unicode, persistence, original-output preservation, validation and portable-export checks. `check_fresh_clone.py` and `check_app.py` verify startup/navigation remains functional. The review table is added on connection; existing analysis rows are retained. No new downloadable assets are required.
