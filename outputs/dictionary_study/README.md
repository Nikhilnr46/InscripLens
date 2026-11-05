# Kittel Historical Kannada Language Model (KittelLM)

This study trains a neural sequence language model on the historical Kannada lexicon extracted from Rev. Ferdinand Kittel's landmark *A Kannada-English Dictionary* (1894, Basel Mission Press, Mangalore).

---

## 1. Motivation & OCR Integration
In historical epigraphy, single-character optical classifiers face severe visual degradation, producing ambiguous top-k alternatives (e.g., distinguishing between visually similar archaic letters *ga*, *pa*, and *da* on weathered stone).

While optical classifiers only observe pixel geometry, a **Neural Language Model** trained on classical Kannada literature and lexicography evaluates the transition prior:
$$P(c_1, c_2, \dots, c_n)$$

By measuring sequence **Perplexity (PPL)**, the language model can re-rank optical candidates during beam search:
- Authentic historical epigraphic sequences receive low perplexity scores ($\text{PPL} \approx 9 - 25$).
- Random or degraded character combinations receive extremely high perplexity ($\text{PPL} > 700$).

---

## 2. Model Architecture & Training Protocol
- **Source Corpus:** 1,464,120 characters across 300 pages of Rev. F. Kittel's dictionary text layer.
- **Vocabulary:** 120 unique characters (Kannada Unicode, historical transliteration markers $\bar{a}, \bar{\imath}, \bar{u}, \d{r}, \bar{e}, \bar{o}, \d{l}, \underline{l}, \underline{r}$, Latin script, and punctuation).
- **Sequences:** 41,176 training sequences and 2,286 validation sequences ($L = 64$ characters).
- **Architecture:** 2-layer Recurrent Neural Network (LSTM) with Dropout ($p=0.2$):
  - Embedding dimension: 128
  - Hidden dimension: 256
  - Output linear projection: $256 \rightarrow 120$
- **Optimization:** AdamW ($\text{lr} = 0.002$, weight decay $10^{-4}$), Cosine Annealing learning rate schedule across 15 epochs.
- **Hardware Acceleration:** Native PyTorch CUDA on NVIDIA GeForce RTX 3050 Laptop GPU.

---

## 3. Training & Validation Results

```json
{
  "model": "Historical Kannada KittelLM (GPU accelerated)",
  "source_text": "Rev. F. Kittel's A Kannada-English Dictionary (1894)",
  "corpus_characters": 1464120,
  "vocab_size": 120,
  "train_sequences": 41176,
  "val_sequences": 2286,
  "sequence_length": 64,
  "device": "cuda",
  "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU",
  "peak_vram_mb": 217.87,
  "best_val_loss": 2.3149,
  "best_val_perplexity": 10.12,
  "best_val_char_accuracy": 0.4247,
  "epochs": 15,
  "total_training_seconds": 88.75,
  "checkpoint_path": "outputs/dictionary_study/kittel_lm_gpu.pth"
}
```

### Empirical Disambiguation Test (Perplexity Scoring)
| Candidate String | Historical Epigraphic Meaning | KittelLM Perplexity | Classification |
| :--- | :--- | :--- | :--- |
| `kalla` | Memorial stone (ಕಲ್ಲ) | **9.97** | High Confidence Classical Kannada |
| `svasti sri` | Auspicious invocation (ಸ್ವಸ್ತಿ ಶ್ರೀ) | **17.21** | High Confidence Classical Kannada |
| `kalagado` | In battle (ಕಾಳಗದೊಳ್) | **23.29** | High Confidence Classical Kannada |
| `balgaccu` | Sword-cleansing grant (ಬಾಳ್ಗಚ್ಚು) | **25.50** | High Confidence Classical Kannada |
| `turugol` | Cattle raid defense (ತುರುಗscore) | **50.93** | Valid Historical Term |
| `xyzqwfp` | Random permutation | **735.06** | Reject / Noise Artefact |
| `qzxjkvm` | Random permutation | **704.64** | Reject / Noise Artefact |

