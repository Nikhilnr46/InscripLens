import cv2
from pathlib import Path


# ============================================
# INSCRIPLENS - VEERAGALLU PREPROCESSING
# ============================================

# Find the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Veeragallu dataset folders
IMAGE_DIR = BASE_DIR / "datasets" / "veeragallu" / "images"
RESULT_DIR = BASE_DIR / "datasets" / "veeragallu" / "Results"

# Create Results folder if it doesn't exist
RESULT_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_image(image_path):

    print(f"\nProcessing: {image_path.name}")

    # ----------------------------------------
    # 1. Read image
    # ----------------------------------------

    image = cv2.imread(str(image_path))

    if image is None:
        print("ERROR: Could not read image.")
        return

    # ----------------------------------------
    # 2. Convert to grayscale
    # ----------------------------------------

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ----------------------------------------
    # 3. Noise reduction
    # ----------------------------------------

    denoised = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # ----------------------------------------
    # 4. Contrast enhancement
    # ----------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(denoised)

    # ----------------------------------------
    # 5. Adaptive thresholding
    # ----------------------------------------

    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    # ----------------------------------------
    # 6. Morphological processing
    # ----------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (3, 3)
    )

    final_image = cv2.morphologyEx(
        binary,
        cv2.MORPH_CLOSE,
        kernel
    )

    # ----------------------------------------
    # 7. Save results
    # ----------------------------------------

    name = image_path.stem

    cv2.imwrite(
        str(RESULT_DIR / f"{name}_gray.jpg"),
        gray
    )

    cv2.imwrite(
        str(RESULT_DIR / f"{name}_denoised.jpg"),
        denoised
    )

    cv2.imwrite(
        str(RESULT_DIR / f"{name}_enhanced.jpg"),
        enhanced
    )

    cv2.imwrite(
        str(RESULT_DIR / f"{name}_binary.jpg"),
        binary
    )

    cv2.imwrite(
        str(RESULT_DIR / f"{name}_final.jpg"),
        final_image
    )

    print("✓ Preprocessing completed")
    print(f"✓ Results saved to: {RESULT_DIR}")


def main():

    # Supported image formats
    extensions = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.bmp",
        "*.tif",
        "*.tiff"
    ]

    image_files = []

    for extension in extensions:
        image_files.extend(
            IMAGE_DIR.glob(extension)
        )

    if not image_files:
        print("\nNo images found!")
        print(f"Check this folder:")
        print(IMAGE_DIR)
        return

    print("======================================")
    print("   INSCRIPLENS PREPROCESSING")
    print("======================================")

    print(f"Images found: {len(image_files)}")

    for image_path in image_files:
        preprocess_image(image_path)

    print("\n======================================")
    print("   ALL IMAGES PROCESSED")
    print("======================================")


if __name__ == "__main__":
    main()