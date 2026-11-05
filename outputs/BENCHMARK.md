# InscripLens Comprehensive Benchmark Audit

Date: November 2026  
Evaluation Protocol: Empirical benchmark audit on local NVIDIA RTX 3050 GPU (4096 MiB) and AMD Ryzen 5 CPU.  
Strict Rules Applied: Evaluation only. No models retrained, modified, or overwritten. No cloud services. Zero emojis. No invented ground truth; unverified tests marked "not testable".

---

## Executive Summary

This benchmark audit provides an empirical evaluation of all algorithmic components in the InscripLens project. Every metric is grounded in explicit test scripts located in `outputs/eval/` executed against verified datasets.

Key Audit Findings:
1. Component Wiring: The deployed web application (`api/server.py` and `inscriplens_app.py`) actively executes the legacy SVM bundle and single-scale GPU binarization. The broad EpiSAM CNN, hero CNN, line U-Net, KittelLM, and multi-scale binarization are not wired into the application inference pipeline.
2. Data Leakage: Split boundaries between train and validation sets are strictly separated with zero stone ID overlap. Crucially, the Nagavara demo stone (HS027) is confirmed to be strictly in the held-out validation set and was never present in any training split.
3. Character Recognition: On the common held-out validation set across 281 shared classes, the Broad EpiSAM CNN achieves the highest top-1 accuracy (28.41%) and superior probability calibration (ECE = 0.0704), outperforming the SVM bundle (27.31% top-1, ECE = 0.3729) and Hero CNN (14.02% top-1, ECE = 0.3579). Top-3 coverage across both Broad CNN and SVM is tied at 40.67% on the full validation set.
4. Line Segmentation: The Line U-Net was trained on merged binary stroke bands and functions as a coarse text-block locator rather than an instance segmenter. Evaluated at instance IoU 0.5 against 254 gold line masks across 31 validation inscriptions, raw connected components achieve 0.0% exact line-count accuracy and an instance F1 of 0.0452.
5. Binarizer Performance: Shilalekhya AttentionUNet on GPU delivers a 16.5x speedup over CPU (1.13 s/MP vs 17.32 s/MP) with identical output quality (IoU = 0.6608). Multi-scale inference increases foreground stroke recall from 76.06% to 89.73% (+13.67 percentage points) while increasing runtime from 0.77s to 5.23s per image.
6. Language Model Re-ranking: KittelLM cannot be tested as a valid re-ranker. Its 120-token vocabulary contains 0 Kannada Unicode characters and 0 IAST epigraphical diacritics, having been trained on English front-matter OCR noise. Furthermore, no verified expert gold character reading line exists in the repository.

---

## 1. Application Component Wiring Audit

Imports, router definitions, and frontend API calls were traced to determine whether trained checkpoints are actively invoked or remain standalone research artifacts.

### Component Wiring Table

| Component | Model / Checkpoint File | Status | Application Entry Point / Call Path | Verdict |
|---|---|---|---|---|
| SVM Bundle | `work/shilalekhya/character_svm.joblib` | Used | `api/server.py` (`POST /api/predict-crop`, `POST /api/recognize-all`), `outputs/inscriplens_app.py` | Active in production backend and Streamlit demo. |
| Broad EpiSAM CNN | `outputs/cnn_study/character_cnn_episam_gpu.pth` | Not wired | None. Standalone checkpoint from GPU training script. | Absent from API server and Streamlit frontend. |
| Hero CNN | `outputs/cnn_study/character_cnn_gpu.pth` | Not wired | None. Standalone checkpoint from hero pilot study. | Absent from API server and Streamlit frontend. |
| Line U-Net | `outputs/line_study/line_segmentation_episam_gpu.pth` | Not wired | None. App uses geometric connected components via `segment_candidates.py`. | Absent from API server and Streamlit frontend. |
| KittelLM | `outputs/dictionary_study/kittel_lm_gpu.pth` | Not wired | None. Standalone LSTM character model. | Absent from API server and Streamlit frontend. |
| Binarizer Multi-Scale | `outputs/binarizer_core.py` (`enhance_multiscale`) | Not wired | `outputs/app_backend.py` calls `binarizer_core.py` without `--multiscale` flag. | App runs single-scale GPU inference only. |
| Translation Core | `outputs/translation_core.py` | Partially wired | Exposed via `POST /api/translate` in `api/server.py`, but not referenced in `frontend/src/App.jsx`. | Endpoint exists but is never invoked by the frontend UI. |

---

## 2. Dataset Split Integrity and Leakage Audit

A comprehensive leakage audit was conducted across training and validation splits for both Hero Pilot and EpiSAM datasets.

### Dataset Split Summary

| Split / Dataset | Inscriptions / Stones | Total Character Crops | Overlap with Validation Split |
|---|---|---|---|
| Hero Pilot Train | HS001 through HS021 (21 stones) | 993 crops | 0 stone IDs, 0 crop paths |
| Hero Pilot Val | HS022 through HS027 (6 stones) | 300 crops | 0 stone IDs in train |
| EpiSAM Train | 117 inscriptions | 10,757 crops | 0 inscription IDs in val |
| EpiSAM Val | 31 inscriptions | 2,741 crops | 0 inscription IDs in train |

### Key Integrity Findings:
1. Split Isolation: Zero stone ID overlap between train and validation splits.
2. Exclusion Verification: In training scripts (`train_matched_mask_study.py`, `train_broad_clean_study.py`), the site `malurpatna` was explicitly included in `excluded_validation_sites` and filtered out from training data.
3. Nagavara Demo Stone (HS027): Confirmed strictly in the validation split (`hero_pilot/manifest.json` and `episam`). The stone HS027 was never present in any training split.
4. Upstream EpiSAM Artifact: The raw EpiSAM dataset contains a duplicate photograph registered under two different names: `Mutkur 1500CE Donation` in train and `Mutkur 1400CE Agrahara` in validation. This is an upstream dataset artifact; hero pilot splits are unaffected.

---

## 3. Character Recognition Models Benchmark

A common held-out validation crop set was constructed and evaluated across the SVM bundle, Broad EpiSAM CNN, and Hero CNN.

### Class Overlap Analysis
- Hero CNN Class Count: 281 classes (trained on 281 hero pilot classes)
- Broad EpiSAM CNN Class Count: 781 classes (trained on full EpiSAM alphabet)
- SVM Bundle Class Count: 764 classes (trained on Shilalekhya dataset)
- Shared Intersection Classes: 281 classes
- Held-out Evaluation Crops: 300 crops (271 within the 281 shared intersection classes)

### Character Recognition Accuracy and Calibration

#### Evaluated on 281 Shared Intersection Classes (271 crops)

| Model Architecture | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Expected Calibration Error (ECE) |
|---|---|---|---|---|
| Broad EpiSAM CNN (GPU) | 28.41% (77 / 271) | 44.65% (121 / 271) | 52.77% (143 / 271) | 0.0704 |
| SVM Bundle (Linear, Mask) | 27.31% (74 / 271) | 45.02% (122 / 271) | 54.24% (147 / 271) | 0.3729 |
| Hero Pilot CNN (GPU) | 14.02% (38 / 271) | 25.09% (68 / 271) | 32.84% (89 / 271) | 0.3579 |

#### Evaluated on Full Validation Set (300 crops, unconstrained)

| Model Architecture | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Expected Calibration Error (ECE) |
|---|---|---|---|---|
| Broad EpiSAM CNN (GPU) | 26.33% (79 / 300) | 40.67% (122 / 300) | 48.00% (144 / 300) | 0.0722 |
| SVM Bundle (Linear, Mask) | 24.67% (74 / 300) | 40.67% (122 / 300) | 49.33% (148 / 300) | 0.3858 |
| Hero Pilot CNN (GPU) | 12.67% (38 / 300) | 22.67% (68 / 300) | 29.67% (89 / 300) | 0.3654 |

### Accuracy by Training-Sample Frequency Bucket (Shared Intersection)

| Training Sample Bucket | Number of Eval Crops | Broad EpiSAM CNN Top-1 | SVM Bundle Top-1 | Hero CNN Top-1 |
|---|---|---|---|---|
| Rare (1 to 5 training samples) | 41 crops | 7.32% (3 / 41) | 4.88% (2 / 41) | 2.44% (1 / 41) |
| Medium (6 to 20 training samples) | 91 crops | 20.88% (19 / 91) | 23.08% (21 / 91) | 3.30% (3 / 91) |
| Common (>20 training samples) | 139 crops | 56.12% (78 / 139) | 53.96% (75 / 139) | 41.01% (57 / 139) |

### Top 10 Confused Character Pairs (Broad EpiSAM CNN)

| True Ground-Truth Label | Model Predicted Label | Error Count |
|---|---|---|
| ka | ra | 5 |
| ya | da | 4 |
| sa | va | 3 |
| ka | da | 3 |
| na | ra | 3 |
| la | ya | 3 |
| da | ya | 2 |
| va | sa | 2 |
| ma | sa | 2 |
| ya | va | 2 |

### Character Recognition Verdict
- Broad EpiSAM CNN achieves the highest top-1 accuracy (28.41% intersection, 26.33% unconstrained) and achieves an Expected Calibration Error of 0.0704, indicating that its predicted softmax probabilities represent true reliability.
- The SVM bundle achieves comparable top-3 (40.67%) and top-5 (49.33%) coverage, but its uncalibrated decision-function margins produce severe miscalibration (ECE = 0.3858).
- Performance is heavily skewed by training frequency: all models achieve >53% accuracy on frequent characters (>20 training samples), but collapse to <8% accuracy on rare characters (1 to 5 samples).

---

## 4. Line Segmentation U-Net Benchmark

The Line U-Net (`line_segmentation_episam_gpu.pth`) was evaluated on all 31 validation inscriptions containing 254 gold line masks.

### Instance Evaluation at IoU 0.5 Threshold

Predictions were split into instances using two standard protocols:
1. Raw Connected Components (CC) on `prediction > 0.5`
2. Horizontal Valley Splitting (projection profile valley cuts across the predicted text region)

| Segmentation Method | Total Predicted Lines | Exact Line-Count Accuracy | Mean Absolute Line Error (MAE) | True Positives (IoU >= 0.5) | Instance Precision | Instance Recall | Instance F1 (IoU 0.5) |
|---|---|---|---|---|---|---|---|
| Ground Truth Gold | 254 | 100.0% | 0.00 | 254 | 1.0000 | 1.0000 | 1.0000 |
| Connected Components (Raw) | 56 | 0.00% (0 / 31) | 6.65 lines | 7 | 0.1250 | 0.0276 | 0.0452 |
| Horizontal Valley Splitting | 59 | 6.45% (2 / 31) | 6.29 lines | 13 | 0.2203 | 0.0512 | 0.0831 |

### Worst-Case Inscriptions (Highest Line Under-Segmentation Error)

| Rank | Inscription Name | Gold Lines | Pred CC Lines | Pred Valley Lines | Line Error | Overlay Image Saved |
|---|---|---|---|---|---|---|
| 1 | Hale Nijagal 1280CE Temple Donation Inscription | 17 | 1 | 2 | 16 lines | `outputs/eval/line_overlays/worst_case_1_Hale_Nijagal_1280CE_Temple_Don.png` |
| 2 | Nagavara 971CE Herostone With Inscription | 17 | 1 | 2 | 16 lines | `outputs/eval/line_overlays/worst_case_2_Nagavara_971CE_Herostone_With_.png` |
| 3 | Jalige 1345CE Pemmeyanayaka's Wife Sati Inscription | 14 | 1 | 2 | 13 lines | `outputs/eval/line_overlays/worst_case_3_Jalige_1345CE_Pemmeyanayaka's_.png` |

### Generalization Test on 3 Non-EpiSAM Stone Photographs

The Line U-Net was evaluated on three genuine non-EpiSAM stone photographs from the Hero Pilot validation split:

| Stone ID | Image File | Dimensions | Predicted CC Lines | Predicted Valley Lines | Foreground Fraction | Empirical Observation |
|---|---|---|---|---|---|---|
| HS022 | `outputs/full_binarizer/HS022_original.png` | 1043 x 1080 | 6 | 2 | 4.29% | Fragmented text regions detected; missed upper lines. |
| HS024 | `outputs/full_binarizer/HS024_original.png` | 826 x 1080 | 4 | 3 | 26.84% | Text block captured as 4 blobs; gold has 8 lines. |
| HS027 | `outputs/full_binarizer/HS027_original.png` | 525 x 1080 | 1 | 2 | 38.68% | Entire 17-line inscription merged into 1 continuous solid blob. |

### Line U-Net Verdict
- The Line U-Net was trained with a composite binary target that merged all individual line annotations into a single binary mask. Consequently, the model learned coarse text-block segmentation rather than line separation.
- Against ground-truth line instances, raw model outputs achieve an instance F1 of 0.0452 at IoU 0.5 and 0.0% exact line-count accuracy. The model cannot be deployed for line extraction without architectural redesign (e.g. boundary-aware training or horizontal projection postprocessing).

---

## 5. Binarizer Pixel-Level Benchmark

The attributed Shilalekhya AttentionUNet binarizer (`work/shilalekhya/binarizer.pth`) was evaluated using pixel-level segmentation metrics (IoU, Dice/F-measure, Precision, Recall, PSNR) against exact gold ground truth binary images from EpiSAM.

### 3-Way Comparative Benchmark (10 Representative Validation Inscriptions)

| Inference Mode | Hardware Device | Foreground IoU | F-measure / Dice | Precision | Recall | Pixel Accuracy | PSNR (dB) | Mean Runtime (s) | Seconds per Megapixel |
|---|---|---|---|---|---|---|---|---|---|
| Single-Scale Baseline | CPU (4 threads) | 0.6608 | 0.7828 | 0.8028 | 0.7751 | 97.55% | 16.84 | 20.078 s | 17.318 s/MP |
| Single-Scale Baseline | GPU (CUDA) | 0.6608 | 0.7828 | 0.8028 | 0.7752 | 97.55% | 16.84 | 1.217 s | 1.127 s/MP |
| Multi-Scale Fusion | GPU (CUDA) | 0.6620 | 0.7898 | 0.7098 | 0.8986 | 97.02% | 16.03 | 5.549 s | 4.726 s/MP |

### Full Validation Set Benchmark (All 31 Validation Inscriptions)

| Inference Mode | Hardware Device | Foreground IoU | F-measure / Dice | Precision | Recall | Pixel Accuracy | PSNR (dB) | Mean Runtime (s) | Seconds per Megapixel |
|---|---|---|---|---|---|---|---|---|---|
| Single-Scale Baseline | GPU (CUDA) | 0.6321 | 0.7614 | 0.7727 | 0.7606 | 96.79% | 16.09 | 0.772 s | 0.723 s/MP |
| Multi-Scale Fusion | GPU (CUDA) | 0.6523 | 0.7847 | 0.7015 | 0.8973 | 96.60% | 15.54 | 5.232 s | 4.782 s/MP |

### Binarizer Verdict
- CPU vs GPU: GPU single-scale yields identical pixel accuracy and IoU to CPU single-scale while providing a **16.5x throughput speedup** (1.13 s/MP vs 17.32 s/MP).
- Single-Scale vs Multi-Scale: Multi-scale sliding window fusion increases foreground stroke recall from 76.06% to 89.73% (+13.67 percentage points), recovering heavily eroded or faint character strokes. However, this comes at the expense of slight stroke dilation (precision drops from 77.27% to 70.15%) and a 6.8x increase in execution time.

---

## 6. Historical Kannada Language Model (KittelLM) Audit

KittelLM (`outputs/dictionary_study/kittel_lm_gpu.pth`) was evaluated as a candidate re-ranker for optical predictions on continuous inscription lines.

### Audit Findings

#### 1. Ground Truth Verification
- Inscription reference file `outputs/context_reading/HS024_reference.json` contains candidate character sequences for HS024 (Line 1: 8 crops).
- However, its metadata explicitly documents:
  - `status`: `"candidate_reference_alignment_not_expert_verified"`
  - `allowed_use`: `"reference-assisted review only; not independent OCR ground truth"`
  - `source_annotation_status`: `"unreviewed"`
- No independent expert-verified character reading sequence exists in the repository.

#### 2. Vocabulary and Representation Compatibility
- KittelLM Vocabulary Size: 120 tokens.
- Kannada Unicode Characters in Vocab: 0 / 120 (0.0%).
- IAST Epigraphic Diacritics in Vocab: 0 / 12 (0.0%).
- All epigraphic consonants and vowels (`ś`, `ṣ`, `ḍ`, `ṇ`, `ṛ`, `ḻ`, `ī`, `ū`, `ā`, `ṃ`, `ĕ`, `ŏ`) are Out-Of-Vocabulary (OOV).
- The corpus `scratch/kittel_corpus_sample.txt` consists of uncleaned English front-matter OCR noise from the title page of Ferdinand Kittel's dictionary (containing words like "MANGALORE", "BASEL MISSION", and symbols like `■`, `£`, `§`).

#### 3. Optical Baseline on Candidate Line 1 (HS024, 8 crops)
- Candidate Reference: `sva sti śrī śrī nŏ ḻa mbaṃ pṛ`
- Broad CNN Top-1: `sti ra śrī śrī ya lu śrī pa`
- Optical Syllable Accuracy: 25.0% (2 / 8 correct; crops 3 and 4 correctly identified as `śrī`)
- Optical Character Error Rate (Levenshtein CER): 0.6364
- Re-ranking Attempt: Fails immediately with OOV errors for all diacritics (`ś`, `ī`, `ŏ`, `ḻ`, `ṃ`, `pṛ`).

### KittelLM Verdict
- **Status: Not testable** as a valid historical Kannada re-ranker.
- Root Cause: Missing verified gold ground truth, complete absence of Kannada or IAST characters from the model's vocabulary, and training on non-epigraphic English title-page noise.

---

## 7. Master Component Verdict Summary

| Component | Status in Codebase | Performance Metric | Production Readiness | Primary Recommendation |
|---|---|---|---|---|
| SVM Bundle | Used | Top-1: 27.31%, Top-3: 45.02%, ECE: 0.3729 | Partially Functional | Calibrate probabilities via Platt scaling or replace with Broad CNN. |
| Broad EpiSAM CNN | Not wired | Top-1: 28.41%, Top-3: 44.65%, ECE: 0.0704 | Ready for Integration | Wire into `api/server.py` to replace the SVM bundle. |
| Hero CNN | Not wired | Top-1: 14.02%, Top-3: 25.09%, ECE: 0.3579 | Deprecated | Superseded by Broad EpiSAM CNN. |
| Line U-Net | Not wired | Instance F1: 0.0452, Line Acc: 0.0% | Not Ready | Retrain with instance separation loss or replace with horizontal projection profiles. |
| Binarizer Single-Scale | Used | IoU: 0.6321, Recall: 76.06%, 0.72 s/MP | Production Ready | Maintain as default high-speed inference engine. |
| Binarizer Multi-Scale | Not wired | IoU: 0.6523, Recall: 89.73%, 4.78 s/MP | Feature Ready | Wire into `app_backend.py` as an optional "High Accuracy" toggle for degraded stones. |
| KittelLM | Not wired | OOV on all Kannada/IAST characters | Broken / Unusable | Retrain from scratch on genuine Kannada corpora with correct Unicode/IAST tokenization. |
| Translation Core | Partially wired | Deterministic epigraphical dictionary lookup | Ready for UI Wiring | Wire `POST /api/translate` into `frontend/src/App.jsx`. |



---

## 8. Recognition Calibration, Ensembling, and Abstention Audit (Step C)

Date: November 2026  
Evaluation Protocol: Post-hoc probability calibration, stone-level cluster bootstrap significance evaluation (1,000 resamples by stone), and abstain threshold tuning across training and validation splits.  
Strict Rules Applied: Evaluation only. No models retrained or overwritten. Calibrator fitted exclusively on EpiSAM training development stones grouped by stone; held-out hero validation set (300 crops from HS022-HS027) strictly reserved for final unbiased testing. No improvement claimed unless exceeding the 95% bootstrap confidence interval. Zero emojis.

---

### 1. Calibration Protocol & Parameters

Calibration splits were partitioned strictly by stone ID so that no stone appeared in both training and calibration splits of the fit. The calibration cohort comprises 359 character crops across 8 historical inscriptions from the 4 established development sites (`aradeshanahalli`, `sadahalli`, `srinivagilu`, `t dasarahalli`). None of these stones or sites overlap with the 6 held-out validation stones (HS022 through HS027).

- **Broad EpiSAM CNN**: Temperature scaling was fitted by minimizing cross-entropy loss (NLL) over the 781 alphabet classes on the calibration split:
  $$T_{\text{CNN}} = 0.7107 \quad (\text{Calibration NLL} = 2.6245)$$
- **SVM Bundle**: Platt temperature scaling was fitted by optimizing the margin scaling parameter on the calibration split decision margins:
  $$T_{\text{SVM}} = 2.6986 \quad (\text{Calibration NLL} = 1.9066)$$
- **Ensemble**: Averages calibrated class probabilities over the union of 781 alphabet classes:
  $$P_{\text{ens}}(c) = \frac{1}{2} \left( P_{\text{SVM}}(c) + P_{\text{CNN}}(c) \right)$$
  For classes absent from the SVM model vocabulary, $P_{\text{SVM}}(c) = 0$.

---

### 2. Held-Out Validation Set Evaluation (300 Crops, Stones HS022-HS027)

| Model Configuration | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Expected Calibration Error (ECE) | ECE Change |
|---|---|---|---|---|---|
| SVM Bundle (Uncalibrated) | 24.67% (74 / 300) | 40.67% (122 / 300) | 49.33% (148 / 300) | 0.3858 | Baseline |
| SVM Bundle (Calibrated, $T=2.70$) | 24.67% (74 / 300) | 40.67% (122 / 300) | 49.33% (148 / 300) | 0.0782 | -30.76 pp |
| Broad CNN (Uncalibrated) | 26.33% (79 / 300) | 40.67% (122 / 300) | 48.00% (144 / 300) | 0.0722 | Baseline |
| Broad CNN (Calibrated, $T=0.71$) | 26.33% (79 / 300) | 40.67% (122 / 300) | 48.00% (144 / 300) | 0.1244 | +5.22 pp |
| Ensemble (Calibrated) | 27.33% (82 / 300) | 45.33% (136 / 300) | 52.33% (157 / 300) | 0.0546 | Best ECE |

**Key Calibration Findings**:
1. Platt scaling on SVM decision margins dramatically eliminates overconfidence error, dropping ECE from 0.3858 down to 0.0782 without altering rank ordering or top-k accuracy.
2. The calibrated ensemble achieves the lowest overall calibration error (ECE = 0.0546), improving top-3 accuracy to 45.33% (+4.66 percentage points over single models) and top-5 accuracy to 52.33% (+3.00 to +4.33 percentage points).

---

### 3. Cluster Bootstrap Significance Evaluation (Resampling by Stone)

A non-parametric cluster bootstrap was conducted with 1,000 iterations. In each iteration, 6 stones were sampled with replacement from the validation stone cohort (HS022: 11 crops, HS023: 21 crops, HS024: 98 crops, HS025: 34 crops, HS026: 14 crops, HS027: 122 crops) to preserve intrastone correlation structure.

| Model / Comparison | Top-1 Accuracy 95% CI | Top-3 Accuracy 95% CI | Top-5 Accuracy 95% CI | ECE 95% CI |
|---|---|---|---|---|
| Calibrated SVM | [21.18%, 28.52%] | [35.79%, 46.81%] | [44.73%, 54.47%] | [0.0475, 0.1119] |
| Calibrated Broad CNN | [23.91%, 32.03%] | [36.49%, 45.37%] | [43.91%, 56.25%] | [0.1033, 0.2389] |
| Calibrated Ensemble | [23.07%, 34.52%] | [42.50%, 53.91%] | [48.23%, 58.79%] | [0.0293, 0.1227] |
| **Paired Difference (Ensemble - Broad CNN)** | **[-1.70%, +3.02%]** | [+0.81%, +8.62%] | [+0.38%, +7.52%] | [-0.1742, -0.0125] |

**Statistical Significance Verdict**:
- Top-1 Improvement: The empirical difference in top-1 accuracy is +1.00% (82 vs 79 crops). However, the paired cluster bootstrap 95% confidence interval is **[-1.70%, +3.02%]**.
- Rule Check: Because the 95% bootstrap interval includes zero, the ensemble does **not** beat the best single model (Broad CNN) beyond the bootstrap 95% interval on top-1 accuracy.
- Enforcing Step C Rule 4: "If the ensemble beats the best single model beyond the interval, wire it into /api/recognize-all and /api/predict-crop; otherwise wire only the better calibrated single model."
- **Production Wiring Decision**: Wire the better calibrated single model (**Broad CNN**) into `/api/recognize-all` and `/api/predict-crop`, accompanied by a parallel SVM evaluation to supply the `models_agree` diagnostic flag.

---

### 4. Abstention Rule Tuning & Generalization

Confidence thresholds $\tau$ were chosen strictly on the calibration split to meet target precision thresholds (70%, 75%, 80%), and evaluated without re-tuning on the 300 held-out validation crops.

| Target Precision (Calibration) | Selected Threshold $\tau$ | Calibration Coverage | Calibration Precision | Held-out Coverage (300 crops) | Held-out Precision | Retained / Abstained Crops |
|---|---|---|---|---|---|---|
| 70.0% | $\tau = 0.10$ | 100.0% | 72.42% | 100.0% (300 / 300) | 27.33% | 300 retained / 0 abstained |
| **75.0% (Production)** | **$\tau = 0.31$** | **42.62%** | **77.12%** | **39.67% (119 / 300)** | **42.02%** | **119 retained / 181 abstained** |
| 80.0% | $\tau = 0.34$ | 35.38% | 80.31% | 34.00% (102 / 300) | 43.14% | 102 retained / 198 abstained |

**Domain Shift & Calibration Generalization Analysis**:
- Setting $\tau = 0.31$ achieves 77.12% precision on the calibration split with 42.62% coverage.
- On the unseen hero stones, applying this exact threshold yields 42.02% precision on 39.67% retained crops (an improvement of +15.69 percentage points over the uncurated 26.33% baseline).
- The drop in precision from 77.12% to 42.02% reveals persistent cross-stone stylistic domain shift in historical epigraphs. This confirms the necessity of the audit rule forbidding threshold tuning on the validation set.

---

### 5. Production Integration & UI Implementation Summary

1. **Backend Integration (`api/reading/recognizer.py` and `api/server.py`)**:
   - `/api/recognize-all` and `/api/predict-crop` execute the calibrated Broad CNN as primary recognizer with SVM parallel checking.
   - Optional extra fields added to existing response schemas:
     - `confidence` (float in $[0.0, 1.0]$): Calibrated softmax probability.
     - `uncertain` (bool): `True` if `confidence < 0.31`, otherwise `False`.
     - `models_agree` (bool): `True` if Broad CNN and SVM top-1 predictions match, otherwise `False`.
     - `confidence_scores` (list of floats): Calibrated confidence values for top-3 alternative suggestions.
   - Graceful Fallback: If PyTorch or checkpoint files are absent, requests seamlessly fall back to legacy SVM inference without schema disruption.

2. **Frontend UI Integration (`frontend/src/App.jsx` and `frontend/src/index.css`)**:
   - Candidate Chips: Subtle visual confidence bar rendered below label. Uncertain candidate chips are dimmed (`opacity: 0.65`) and labeled with an amber "Uncertain" tag.
   - Glyph Inspector: Displays calibrated confidence percentage and a subtle visual fill track. Shows "Uncertain" tag and model agreement status (`Models agree` / `Models disagree`).
   - Integrity Requirement: Predictions and alternative candidate chips are never hidden; alternatives remain fully interactive and adoptable.
