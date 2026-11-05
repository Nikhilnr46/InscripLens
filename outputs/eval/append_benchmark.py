import sys

section_8 = """

---

## 8. Recognition Calibration, Ensembling, and Abstention Audit (Step C)

Date: November 2026  
Evaluation Protocol: Post-hoc probability calibration, stone-level cluster bootstrap significance evaluation (1,000 resamples by stone), and abstain threshold tuning across training and validation splits.  
Strict Rules Applied: Evaluation only. No models retrained or overwritten. Calibrator fitted exclusively on EpiSAM training development stones grouped by stone; held-out hero validation set (300 crops from HS022-HS027) strictly reserved for final unbiased testing. No improvement claimed unless exceeding the 95% bootstrap confidence interval. Zero emojis.

---

### 1. Calibration Protocol & Parameters

Calibration splits were partitioned strictly by stone ID so that no stone appeared in both training and calibration splits of the fit. The calibration cohort comprises 359 character crops across 8 historical inscriptions from the 4 established development sites (`aradeshanahalli`, `sadahalli`, `srinivagilu`, `t dasarahalli`). None of these stones or sites overlap with the 6 held-out validation stones (HS022 through HS027).

- **Broad EpiSAM CNN**: Temperature scaling was fitted by minimizing cross-entropy loss (NLL) over the 781 alphabet classes on the calibration split:
  $$T_{\\text{CNN}} = 0.7107 \\quad (\\text{Calibration NLL} = 2.6245)$$
- **SVM Bundle**: Platt temperature scaling was fitted by optimizing the margin scaling parameter on the calibration split decision margins:
  $$T_{\\text{SVM}} = 2.6986 \\quad (\\text{Calibration NLL} = 1.9066)$$
- **Ensemble**: Averages calibrated class probabilities over the union of 781 alphabet classes:
  $$P_{\\text{ens}}(c) = \\frac{1}{2} \\left( P_{\\text{SVM}}(c) + P_{\\text{CNN}}(c) \\right)$$
  For classes absent from the SVM model vocabulary, $P_{\\text{SVM}}(c) = 0$.

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

Confidence thresholds $\\tau$ were chosen strictly on the calibration split to meet target precision thresholds (70%, 75%, 80%), and evaluated without re-tuning on the 300 held-out validation crops.

| Target Precision (Calibration) | Selected Threshold $\\tau$ | Calibration Coverage | Calibration Precision | Held-out Coverage (300 crops) | Held-out Precision | Retained / Abstained Crops |
|---|---|---|---|---|---|---|
| 70.0% | $\\tau = 0.10$ | 100.0% | 72.42% | 100.0% (300 / 300) | 27.33% | 300 retained / 0 abstained |
| **75.0% (Production)** | **$\\tau = 0.31$** | **42.62%** | **77.12%** | **39.67% (119 / 300)** | **42.02%** | **119 retained / 181 abstained** |
| 80.0% | $\\tau = 0.34$ | 35.38% | 80.31% | 34.00% (102 / 300) | 43.14% | 102 retained / 198 abstained |

**Domain Shift & Calibration Generalization Analysis**:
- Setting $\\tau = 0.31$ achieves 77.12% precision on the calibration split with 42.62% coverage.
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
"""

for file_path in ['BENCHMARK.md', 'outputs/BENCHMARK.md']:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '## 8. Recognition Calibration, Ensembling, and Abstention Audit (Step C)' not in content:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(section_8)
        print(f'Appended Section 8 to {file_path}')
    else:
        print(f'Section 8 already present in {file_path}')

