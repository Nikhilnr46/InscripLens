# Full reading rank API handoff

POST /api/predict-crop accepts an optional proposed_reading string (Kannada or Roman, max 256 characters). Send the same reading for both automatic and redrawn boxes.

Request example
{
  "run_id": "<active run>",
  "bbox": [185, 65, 226, 125],
  "proposed_reading": "ಸ್ತಿ"
}

The existing prediction and three alternatives remain available. The additional proposed_reading_rank object contains reading, normalized_reading, rank (1-based integer or null), matched_label, total_labels, and status.

Status ranked means the reading exists in the full model vocabulary. Display rank, including positions beyond three. Status absent_from_vocabulary means the classifier cannot output that reading. Omitted or blank reading returns proposed_reading_rank: null. Kannada equivalences use the existing converter and NFC normalization. Multiple Roman labels mapping to the same Kannada text use the earliest rank.

Frontend integration
- Pass proposed_reading through compare/apiClient.js and preserve proposed_reading_rank in its returned result.
- Store the reading rank with each crop prediction, saved comparison, JSON export and PDF report.
- If the reading changes after prediction, request updated ranks for both boxes. Avoid pairing a new reading with the previous reading's rank.
- Use full ranks when both results contain them. For older saved comparisons or older APIs, retain the existing top-three outcome logic and describe its scope.
- Compute outcomes only when both ranks are integers. Handle absent vocabulary and unavailable rank as distinct unknown cases.
- Three visible alternatives can stay as designed.
- Restart the backend after pulling. Rebuild the frontend after integration.
