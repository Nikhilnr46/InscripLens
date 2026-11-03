import cv2
from pathlib import Path


# ============================================
# INSCRIPLENS - INSCRIPTION ROI SELECTION
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "datasets" / "veeragallu" / "images"
RESULT_DIR = BASE_DIR / "datasets" / "veeragallu" / "Results"

RESULT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------
# Find the image
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
    print("No Veeragallu image found.")
    exit()


image_path = image_files[0]

print("Opening:", image_path.name)


# --------------------------------------------
# Read original image
# --------------------------------------------

image = cv2.imread(str(image_path))

if image is None:
    print("Could not read image.")
    exit()


# --------------------------------------------
# Select Region of Interest
# --------------------------------------------

print()
print("SELECT THE INSCRIPTION AREA")
print("--------------------------------")
print("Drag a rectangle around the inscription.")
print("Press ENTER after selecting.")
print("Press ESC to cancel.")
print()


roi = cv2.selectROI(
    "Select Inscription Region",
    image,
    showCrosshair=True,
    fromCenter=False
)

cv2.destroyAllWindows()


x, y, width, height = roi


if width == 0 or height == 0:
    print("No region selected.")
    exit()


# --------------------------------------------
# Crop inscription
# --------------------------------------------

cropped = image[
    y:y + height,
    x:x + width
]


# --------------------------------------------
# Save cropped inscription
# --------------------------------------------

output_path = (
    RESULT_DIR /
    f"{image_path.stem}_inscription_roi.jpg"
)

cv2.imwrite(
    str(output_path),
    cropped
)


print()
print("ROI selected successfully.")
print("Saved:", output_path)


# --------------------------------------------
# Display result
# --------------------------------------------

cv2.imshow(
    "Selected Inscription",
    cropped
)

print()
print("Press any key to close.")

cv2.waitKey(0)
cv2.destroyAllWindows()