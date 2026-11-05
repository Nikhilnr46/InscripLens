"""End-to-end regression and verification test suite for Kannada script display and API integrity.
Verifies demo loading, candidate localization, crop predictions, review persistence,
JSON export schemas, and history tracking.
"""

import urllib.request
import json
import sys
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"


def request_json(path, data=None, method="GET"):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data is not None else {}
    body = json.dumps(data).encode("utf-8") if isinstance(data, dict) else (data if isinstance(data, bytes) else None)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_tests():
    print("=" * 60)
    print("INSCRIPLENS KANNADA SCRIPT DISPLAY & REGRESSION VERIFICATION")
    print("=" * 60)

    # 1. Status Check
    print("\n[1] Verifying /api/status...")
    status = request_json("/api/status")
    assert status.get("ready") is True, f"Status not ready: {status}"
    assert status.get("demo_available") is True
    print(f"  Status OK: ready={status['ready']}, demo={status['demo_available']}")

    # 2. Standard Demo Stone Enhancement
    print("\n[2] Testing Standard Mode Demo Analysis (/api/analyse?use_demo=true)...")
    t0 = time.time()
    std_res = request_json("/api/analyse?use_demo=true", data=b"", method="POST")
    std_time = time.time() - t0
    run_id = std_res["id"]
    boxes = std_res["boxes"]
    candidate_count = std_res["candidate_count"]
    assert candidate_count == 133, f"Expected 133 candidates, got {candidate_count}"
    assert std_res.get("mode") == "standard"
    print(f"  Standard analysis completed in {std_time:.2f}s: {candidate_count} candidates, run_id={run_id}")

    # 3. Predict Tiny Candidate (#1: 7x4 px)
    print("\n[3] Testing Predict Crop on Tiny Candidate #1...")
    b0 = boxes[0]
    w0 = b0[2] - b0[0]
    h0 = b0[3] - b0[1]
    print(f"  Candidate #1 bbox: {b0} ({w0}x{h0} px)")
    crop_res_0 = request_json("/api/predict-crop", data={"run_id": run_id, "bbox": b0}, method="POST")
    assert "prediction" in crop_res_0
    assert "prediction_kannada" in crop_res_0
    print(f"  Candidate #1 Roman: {ascii(crop_res_0['prediction'])}, Kannada: {ascii(crop_res_0['prediction_kannada'])}")

    # 4. Predict Normal Candidate (#5)
    print("\n[4] Testing Predict Crop on Normal Candidate #5...")
    b4 = boxes[4]
    w4 = b4[2] - b4[0]
    h4 = b4[3] - b4[1]
    print(f"  Candidate #5 bbox: {b4} ({w4}x{h4} px)")
    crop_res_4 = request_json("/api/predict-crop", data={"run_id": run_id, "bbox": b4}, method="POST")
    assert "prediction" in crop_res_4
    assert "prediction_kannada" in crop_res_4
    print(f"  Candidate #5 Roman: {ascii(crop_res_4['prediction'])}, Kannada: {ascii(crop_res_4['prediction_kannada'])}")

    # 5. Save Character Review
    print("\n[5] Saving Review Correction with Roman suggestion...")
    rev_payload = {
        "run_id": run_id,
        "bbox": b4,
        "prediction": crop_res_4["prediction"],
        "model": "Experimental recognizer",
        "model_sha256": crop_res_4.get("model_sha256", ""),
        "suggestion": "ko",  # Roman input
        "reviewer": "TestEpigraphist",
        "note": "Regression test verification"
    }
    save_res = request_json("/api/review", data=rev_payload, method="POST")
    assert save_res.get("status") == "saved"
    print("  Review successfully saved to SQLite.")

    # 6. Verify Saved Reviews
    print("\n[6] Verifying saved reviews (/api/reviews/{run_id})...")
    saved_revs = request_json(f"/api/reviews/{run_id}")
    assert len(saved_revs) > 0
    latest_rev = saved_revs[-1]
    assert latest_rev["suggested_label"] == "ko"
    assert latest_rev["reviewer"] == "TestEpigraphist"
    print(f"  Stored review confirmed: suggestion={latest_rev['suggested_label']} (Roman), reviewer={latest_rev['reviewer']}")

    # 7. Verify JSON Export with both Roman and Kannada text
    print("\n[7] Verifying /api/export/{run_id}...")
    export_data = request_json(f"/api/export/{run_id}")
    assert "reviews" in export_data
    exp_revs = export_data["reviews"]
    assert len(exp_revs) > 0
    exp_latest = exp_revs[-1]
    assert exp_latest["suggested_label"] == "ko"
    assert exp_latest["suggested_label_kannada"] == "\u0c95\u0ccb"  # ಕೋ (ko is long o)
    print(f"  Export verified: Roman='{exp_latest['suggested_label']}', Kannada='{ascii(exp_latest['suggested_label_kannada'])}'")

    # 8. Verify Run History with Reviews
    print("\n[8] Verifying /api/history...")
    hist_items = request_json("/api/history")
    assert len(hist_items) > 0
    matched_run = next((h for h in hist_items if h["id"] == run_id), None)
    assert matched_run is not None, f"Run {run_id} not found in history"
    assert "reviews" in matched_run
    assert matched_run["review_count"] >= 1
    hist_rev = matched_run["reviews"][-1]
    assert hist_rev["suggested_label"] == "ko"
    assert hist_rev["suggested_label_kannada"] == "\u0c95\u0ccb"  # ಕೋ (ko is long o)
    print(f"  History item verified: review_count={matched_run['review_count']}, Roman='{hist_rev['suggested_label']}', Kannada='{ascii(hist_rev['suggested_label_kannada'])}'")

    # 9. Batch Classification Verification
    print("\n[9] Verifying /api/recognize-all...")
    rec_res = request_json("/api/recognize-all", data={"run_id": run_id}, method="POST")
    assert rec_res["candidate_count"] == 133
    assert len(rec_res["regions"]) == 133
    r0 = rec_res["regions"][0]
    assert ("predicted_source_label" in r0 or "prediction" in r0)
    assert "prediction_kannada" in r0
    print(f"  Batch recognize verified: 133 regions classified, sample Kannada='{ascii(r0['prediction_kannada'])}'")

    print("\n" + "=" * 60)
    print("ALL 9 REGRESSION TESTS PASSED CLEANLY")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
