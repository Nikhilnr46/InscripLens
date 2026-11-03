import cv2
import matplotlib.pyplot as plt
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RESULT_DIR = BASE_DIR / "datasets" / "veeragallu" / "Results"

# Find the ROI automatically
roi_files = list(RESULT_DIR.glob("*_inscription_roi.jpg"))

if not roi_files:
    print("ERROR: No inscription ROI found.")
    print("Run select_inscription.py first.")
    exit()

roi_path = roi_files[0]

print("Processing:", roi_path.name)

image = cv2.imread(str(roi_path))

if image is None:
    print("ERROR: Could not read ROI.")
    exit()


# 1. Grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# 2. Local contrast enhancement
clahe = cv2.createCLAHE(
    clipLimit=2.0,
    tileGridSize=(8, 8)
)

enhanced = clahe.apply(gray)


# 3. Gentle noise reduction
denoised = cv2.GaussianBlur(
    enhanced,
    (3, 3),
    0
)


# 4. Otsu threshold
_, otsu = cv2.threshold(
    denoised,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)


# 5. Adaptive threshold
adaptive = cv2.adaptiveThreshold(
    denoised,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,
    7
)


# Save results
cv2.imwrite(
    str(RESULT_DIR / "inscription_gray.jpg"),
    gray
)

cv2.imwrite(
    str(RESULT_DIR / "inscription_enhanced.jpg"),
    enhanced
)

cv2.imwrite(
    str(RESULT_DIR / "inscription_otsu.jpg"),
    otsu
)

cv2.imwrite(
    str(RESULT_DIR / "inscription_adaptive.jpg"),
    adaptive
)


# --------------------------------------------
# Display comparison
# --------------------------------------------

fig, axes = plt.subplots(
    2,
    3,
    figsize=(18, 12),
    layout="constrained"
)

# Original
axes[0, 0].imshow(
    cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
)
axes[0, 0].set_title(
    "Original Inscription ROI",
    fontsize=14,
    pad=12
)
axes[0, 0].axis("off")


# Grayscale
axes[0, 1].imshow(
    gray,
    cmap="gray"
)
axes[0, 1].set_title(
    "Grayscale",
    fontsize=14,
    pad=12
)
axes[0, 1].axis("off")


# CLAHE
axes[0, 2].imshow(
    enhanced,
    cmap="gray"
)
axes[0, 2].set_title(
    "CLAHE Enhanced",
    fontsize=14,
    pad=12
)
axes[0, 2].axis("off")


# Otsu
axes[1, 0].imshow(
    otsu,
    cmap="gray"
)
axes[1, 0].set_title(
    "Otsu Threshold",
    fontsize=14,
    pad=12
)
axes[1, 0].axis("off")


# Adaptive
axes[1, 1].imshow(
    adaptive,
    cmap="gray"
)
axes[1, 1].set_title(
    "Adaptive Threshold",
    fontsize=14,
    pad=12
)
axes[1, 1].axis("off")


# Empty sixth panel
axes[1, 2].axis("off")


fig.suptitle(
    "InscripLens - Inscription Preprocessing Comparison",
    fontsize=18
)

plt.show()

print()
print("Inscription preprocessing completed.")
print("Results saved in:")
print(RESULT_DIR)