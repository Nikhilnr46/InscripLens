import cv2
import matplotlib.pyplot as plt
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "datasets" / "veeragallu" / "images"
RESULT_DIR = BASE_DIR / "datasets" / "veeragallu" / "Results"


# Find the first image automatically
image_files = []

for extension in ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff"]:
    image_files.extend(IMAGE_DIR.glob(extension))


if not image_files:
    print("ERROR: No image found in:")
    print(IMAGE_DIR)
    exit()


original_path = image_files[0]

print("Opening:")
print(original_path)


# Read images
original = cv2.imread(str(original_path))

gray = cv2.imread(
    str(RESULT_DIR / f"{original_path.stem}_gray.jpg"),
    cv2.IMREAD_GRAYSCALE
)

enhanced = cv2.imread(
    str(RESULT_DIR / f"{original_path.stem}_enhanced.jpg"),
    cv2.IMREAD_GRAYSCALE
)

binary = cv2.imread(
    str(RESULT_DIR / f"{original_path.stem}_binary.jpg"),
    cv2.IMREAD_GRAYSCALE
)

final = cv2.imread(
    str(RESULT_DIR / f"{original_path.stem}_final.jpg"),
    cv2.IMREAD_GRAYSCALE
)


# Check that files loaded correctly
if original is None:
    print("ERROR: Could not read original image.")
    exit()

if gray is None or enhanced is None or binary is None or final is None:
    print("ERROR: One or more processed images could not be read.")
    print("Run preprocess.py first.")
    exit()


# Display comparison
plt.figure(figsize=(15, 10))


plt.subplot(2, 3, 1)
plt.imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
plt.title("Original")
plt.axis("off")


plt.subplot(2, 3, 2)
plt.imshow(gray, cmap="gray")
plt.title("Grayscale")
plt.axis("off")


plt.subplot(2, 3, 3)
plt.imshow(enhanced, cmap="gray")
plt.title("Contrast Enhanced")
plt.axis("off")


plt.subplot(2, 3, 4)
plt.imshow(binary, cmap="gray")
plt.title("Binary")
plt.axis("off")


plt.subplot(2, 3, 5)
plt.imshow(final, cmap="gray")
plt.title("Final Preprocessed")
plt.axis("off")


plt.tight_layout()
plt.show()