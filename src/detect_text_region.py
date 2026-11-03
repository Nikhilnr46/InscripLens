import cv2
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================
# INSCRIPLENS - TEXT REGION DETECTION
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "datasets" / "veeragallu" / "images"
RESULT_DIR = BASE_DIR / "datasets" / "veeragallu" / "Results"

RESULT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------
# Find input image
# --------------------------------------------

image_files = []

for extension in [
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.bmp",
    "*.tif",
    "*.tiff"
]:
    image_files.extend(IMAGE_DIR.glob(extension))


if not image_files:
    print("ERROR: No image found.")
    print(IMAGE_DIR)
    exit()


image_path = image_files[0]

print(f"Processing: {image_path.name}")


# --------------------------------------------
# Load preprocessed image
# --------------------------------------------

binary_path = RESULT_DIR / f"{image_path.stem}_binary.jpg"

binary = cv2.imread(
    str(binary_path),
    cv2.IMREAD_GRAYSCALE
)

if binary is None:
    print("ERROR: Binary image not found.")
    print("Run preprocess.py first.")
    exit()


# --------------------------------------------
# Invert image
# --------------------------------------------
# Text becomes white and background becomes black.

inverted = cv2.bitwise_not(binary)


# --------------------------------------------
# Find connected components
# --------------------------------------------

num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
    inverted,
    connectivity=8
)


# --------------------------------------------
# Create candidate text-region image
# --------------------------------------------

region_image = cv2.cvtColor(
    binary,
    cv2.COLOR_GRAY2BGR
)


for i in range(1, num_labels):

    x = stats[i, cv2.CC_STAT_LEFT]
    y = stats[i, cv2.CC_STAT_TOP]
    w = stats[i, cv2.CC_STAT_WIDTH]
    h = stats[i, cv2.CC_STAT_HEIGHT]
    area = stats[i, cv2.CC_STAT_AREA]

    # Ignore extremely small noise
    if area < 20:
        continue

    # Ignore extremely large regions
    if area > 0.40 * binary.shape[0] * binary.shape[1]:
        continue

    # Draw candidate region
    cv2.rectangle(
        region_image,
        (x, y),
        (x + w, y + h),
        (0, 0, 255),
        2
    )


# --------------------------------------------
# Save result
# --------------------------------------------

output_path = RESULT_DIR / f"{image_path.stem}_text_regions.jpg"

cv2.imwrite(
    str(output_path),
    region_image
)


print("Text-region analysis completed.")
print(f"Saved: {output_path}")


# --------------------------------------------
# Display
# --------------------------------------------

plt.figure(figsize=(12, 8))

plt.imshow(
    cv2.cvtColor(region_image, cv2.COLOR_BGR2RGB)
)

plt.title("Candidate Text Regions")

plt.axis("off")

plt.tight_layout()

plt.show()