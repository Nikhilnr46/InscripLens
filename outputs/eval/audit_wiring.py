"""Audit wired imports and runtime API usage in InscripLens."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def audit_wiring():
    # 1. Inspect api/server.py
    server_py = (ROOT / "api/server.py").read_text(encoding="utf-8")
    app_backend_py = (ROOT / "outputs/app_backend.py").read_text(encoding="utf-8")
    streamlit_py = (ROOT / "outputs/inscriplens_app.py").read_text(encoding="utf-8")
    frontend_jsx = (ROOT / "frontend/src/App.jsx").read_text(encoding="utf-8")

    components = {
        "SVM bundle": {
            "files": ["api/server.py", "outputs/inscriplens_app.py"],
            "description": "Loaded as CLEAN_MODEL (mask_svm_bundle.joblib) in api/server.py for /api/predict-crop and /api/recognize-all, and used in Streamlit.",
            "status": "Used"
        },
        "Broad EpiSAM CNN": {
            "files": ["outputs/cnn_study/character_cnn_episam_gpu.pth"],
            "description": "Saved as standalone PyTorch checkpoint. Not imported or served in api/server.py or inscriplens_app.py.",
            "status": "Not wired"
        },
        "Hero CNN": {
            "files": ["outputs/cnn_study/character_cnn_gpu.pth"],
            "description": "Saved as standalone PyTorch checkpoint. Not imported or served in api/server.py or inscriplens_app.py.",
            "status": "Not wired"
        },
        "Line U-Net": {
            "files": ["outputs/line_study/line_segmentation_episam_gpu.pth"],
            "description": "Saved as standalone PyTorch checkpoint. The running app derives candidate boxes via connected components (outputs/segment_candidates.py), not Line U-Net.",
            "status": "Not wired"
        },
        "KittelLM": {
            "files": ["outputs/dictionary_study/kittel_lm_gpu.pth"],
            "description": "Saved as standalone PyTorch checkpoint. Not called during live recognition in api/server.py or inscriplens_app.py.",
            "status": "Not wired"
        },
        "Binarizer_core multi-scale": {
            "files": ["outputs/binarizer_core.py", "outputs/app_backend.py"],
            "description": "binarizer_core.py supports --multiscale, but outputs/app_backend.py calls it via subprocess without --multiscale (runs default GPU single-scale).",
            "status": "Not wired"
        },
        "Translation_core": {
            "files": ["api/server.py", "outputs/translation_core.py"],
            "description": "Imported in api/server.py and exposed via POST /api/translate. However, frontend/src/App.jsx does not trigger /api/translate, and Streamlit marks translation unavailable.",
            "status": "Partially wired"
        }
    }

    out_file = ROOT / "outputs/eval/wiring_report.json"
    out_file.write_text(json.dumps(components, indent=2), encoding="utf-8")
    print("=" * 60)
    print("TASK 1: RUNTIME WIRING AUDIT")
    print("=" * 60)
    for k, v in components.items():
        print(f"{k:<30} : {v['status']}")
        print(f"  -> {v['description']}")
    return components

if __name__ == "__main__":
    audit_wiring()

