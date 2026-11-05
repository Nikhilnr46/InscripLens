"""Calibrated character recognition engine for InscripLens Epigraphy Studio.
Supports calibrated single-model prediction (Broad CNN), fallback to SVM,
uncertainty estimation via calibration-split abstain threshold, and model agreement checking.
"""
import io
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure binarizer_env packages (PyTorch with CUDA) are available
ENV_PACKAGES = ROOT / "work/binarizer_env/Lib/site-packages"
if ENV_PACKAGES.is_dir() and str(ENV_PACKAGES) not in sys.path:
    sys.path.insert(0, str(ENV_PACKAGES))

import numpy as np
from PIL import Image, ImageOps
import torch
import joblib

# Paths to models and parameters
SVM_MODELS = [
    ROOT / "outputs/broad_clean_study/mask_svm_bundle.joblib",
    ROOT / "outputs/matched_mask_study/mask_svm_bundle.joblib"
]
CNN_CHECKPOINT = ROOT / "outputs/cnn_study/character_cnn_episam_gpu.pth"
CALIB_PARAMS_FILE = Path(__file__).resolve().parent / "calibration_params.json"

# Import helper functions from outputs
import sys
if str(ROOT / "outputs") not in sys.path:
    sys.path.insert(0, str(ROOT / "outputs"))

from run_character_benchmark import features
from segment_candidates import candidates
from recognition_alternatives import rank_labels, source_examples

# PyTorch Broad CNN Architecture definition
class BroadCharacterCNN(torch.nn.Module):
    def __init__(self, num_classes: int):
        super().__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, 3, padding=1),
            torch.nn.BatchNorm2d(32),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),  # 32 x 32

            torch.nn.Conv2d(32, 64, 3, padding=1),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),  # 16 x 16

            torch.nn.Conv2d(64, 128, 3, padding=1),
            torch.nn.BatchNorm2d(128),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(2),  # 8 x 8
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(128 * 8 * 8, 256),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))

def _softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e_x / np.sum(e_x, axis=axis, keepdims=True)

def _pixels_64(pil_img: Image.Image) -> np.ndarray:
    im = ImageOps.contain(pil_img.convert('L'), (64, 64), Image.Resampling.BILINEAR)
    canvas = Image.new('L', (64, 64), 0)
    canvas.paste(im, ((64 - im.width) // 2, (64 - im.height) // 2))
    return np.array(canvas, dtype=np.float32)[None] / 255.0

class RecognizerEngine:
    """Manages calibrated character recognition inference with graceful fallbacks."""

    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.svm_bundle = None
        self.svm_classes = []
        self.cnn_model = None
        self.cnn_classes = []

        # Default calibration parameters
        self.t_svm = 2.6986
        self.t_cnn = 0.7107
        self.abstain_tau = 0.31  # Target precision 75% on calibration split

        self._load_calibration_params()
        self._load_models()

    def _load_calibration_params(self):
        if CALIB_PARAMS_FILE.is_file():
            try:
                data = json.loads(CALIB_PARAMS_FILE.read_text(encoding='utf-8'))
                self.t_svm = float(data.get("svm_temperature", self.t_svm))
                self.t_cnn = float(data.get("cnn_temperature", self.t_cnn))
            except Exception:
                pass

    def _load_models(self):
        # 1. Load SVM Bundle
        for path in SVM_MODELS:
            if path.is_file():
                try:
                    self.svm_bundle = joblib.load(path)
                    self.svm_classes = list(self.svm_bundle['model'].classes_)
                    break
                except Exception:
                    self.svm_bundle = None

        # 2. Load Broad CNN Checkpoint
        if CNN_CHECKPOINT.is_file():
            try:
                ckpt = torch.load(CNN_CHECKPOINT, map_location=self.device, weights_only=True)
                self.cnn_classes = list(ckpt['classes'])
                model = BroadCharacterCNN(len(self.cnn_classes)).to(self.device)
                model.load_state_dict(ckpt['state_dict'])
                model.eval()
                self.cnn_model = model
            except Exception:
                self.cnn_model = None

    @property
    def is_available(self) -> bool:
        return self.svm_bundle is not None or self.cnn_model is not None

    def predict_crop(self, crop: Image.Image) -> Dict[str, Any]:
        """Predict character label, confidence, uncertainty, and agreement for a single crop."""
        svm_pred = None
        cnn_pred = None
        confidence = None
        uncertain = False
        models_agree = None
        alts = []
        confidence_scores = []

        # 1. Broad CNN Prediction (better calibrated single model)
        if self.cnn_model is not None:
            try:
                tensor = torch.from_numpy(_pixels_64(crop))[None].to(self.device)
                with torch.inference_mode():
                    logits = self.cnn_model(tensor).cpu().numpy()[0]
                calib_probs = _softmax(logits / self.t_cnn)
                top_indices = np.argsort(-calib_probs)[:5]
                cnn_pred = self.cnn_classes[top_indices[0]]
                confidence = float(calib_probs[top_indices[0]])
                alts = [self.cnn_classes[i] for i in top_indices[:3]]
                confidence_scores = [round(float(calib_probs[i]), 4) for i in top_indices[:3]]
                uncertain = bool(confidence < self.abstain_tau)
            except Exception:
                cnn_pred = None

        # 2. SVM Prediction (for agreement check or fallback)
        if self.svm_bundle is not None:
            try:
                feat = features(crop, self.svm_bundle.get('preprocessing', 'median'))
                dec = self.svm_bundle['model'].decision_function([feat])[0]
                calib_svm_probs = _softmax(dec / self.t_svm)
                svm_top_idx = np.argsort(-calib_svm_probs)[:5]
                svm_pred = self.svm_classes[svm_top_idx[0]]

                # If CNN was unavailable, use SVM as fallback
                if cnn_pred is None:
                    confidence = float(calib_svm_probs[svm_top_idx[0]])
                    alts = [self.svm_classes[i] for i in svm_top_idx[:3]]
                    confidence_scores = [round(float(calib_svm_probs[i]), 4) for i in svm_top_idx[:3]]
                    uncertain = bool(confidence < self.abstain_tau)
            except Exception:
                svm_pred = None

        # Agreement
        if svm_pred is not None and cnn_pred is not None:
            models_agree = bool(svm_pred == cnn_pred)
        elif svm_pred is not None or cnn_pred is not None:
            models_agree = True

        final_pred = cnn_pred if cnn_pred is not None else svm_pred
        if final_pred is None:
            final_pred = "Unknown"

        return {
            "prediction": final_pred,
            "confidence": round(confidence, 4) if confidence is not None else None,
            "uncertain": uncertain,
            "models_agree": models_agree,
            "alternatives": alts,
            "confidence_scores": confidence_scores
        }

    def recognize_all_regions(self, mask: Image.Image) -> List[Dict[str, Any]]:
        """Run batch recognition on all candidate regions detected in the mask."""
        boxes = candidates(mask)
        if not boxes:
            return []

        # Fallback to pure SVM if CNN not available
        if self.cnn_model is None:
            if self.svm_bundle is None:
                return []
            x = np.stack([features(mask.crop(box), self.svm_bundle.get('preprocessing', 'median')) for box in boxes])
            labels = self.svm_bundle['model'].predict(x)
            return [
                {
                    'candidate': i + 1,
                    'bbox': box,
                    'predicted_source_label': str(lbl),
                    'verified': False
                }
                for i, (box, lbl) in enumerate(zip(boxes, labels))
            ]

        # Extract crops for batch
        crops = [mask.crop(box) for box in boxes]

        # Batch CNN forward
        tensors = np.stack([_pixels_64(c) for c in crops])
        torch_tensors = torch.from_numpy(tensors).to(self.device)
        with torch.inference_mode():
            logits = self.cnn_model(torch_tensors).cpu().numpy()
        cnn_probs = _softmax(logits / self.t_cnn, axis=1)
        cnn_preds = [self.cnn_classes[i] for i in cnn_probs.argmax(axis=1)]
        cnn_confs = cnn_probs.max(axis=1)

        # Batch SVM forward for agreement check
        svm_preds = None
        if self.svm_bundle is not None:
            try:
                x_feat = np.stack([features(c, self.svm_bundle.get('preprocessing', 'median')) for c in crops])
                svm_preds = self.svm_bundle['model'].predict(x_feat)
            except Exception:
                svm_preds = None

        regions = []
        for i, box in enumerate(boxes):
            pred = cnn_preds[i]
            conf = float(cnn_confs[i])
            is_uncertain = bool(conf < self.abstain_tau)
            agree = bool(svm_preds[i] == pred) if svm_preds is not None else True

            regions.append({
                'candidate': i + 1,
                'bbox': box,
                'predicted_source_label': str(pred),
                'verified': False,
                'confidence': round(conf, 4),
                'uncertain': is_uncertain,
                'models_agree': agree
            })

        return regions

# Global singleton
_ENGINE: Optional[RecognizerEngine] = None

def get_engine() -> RecognizerEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = RecognizerEngine()
    return _ENGINE
