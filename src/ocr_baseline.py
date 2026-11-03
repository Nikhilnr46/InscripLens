import subprocess
from pathlib import Path


# ============================================
# INSCRIPLENS - TESSERACT OCR BASELINE
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

RESULT_DIR = (
    BASE_DIR
    / "datasets"
    / "veeragallu"
    / "Results"
)

OCR_DIR = RESULT_DIR / "ocr_baseline"

OCR_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------
# Input images
# --------------------------------------------

images = [
    "veeragallu_001_inscription_roi.jpg",
    "inscription_gray.jpg",
    "inscription_enhanced.jpg",
    "inscription_otsu.jpg",
    "inscription_adaptive.jpg"
]


# --------------------------------------------
# Tesseract PSM modes
# --------------------------------------------

psm_modes = [
    6,   # Assume a uniform block of text
    11   # Sparse text
]


# --------------------------------------------
# Run experiments
# --------------------------------------------

for image_name in images:

    image_path = RESULT_DIR / image_name

    if not image_path.exists():
        print(f"Skipping missing image: {image_name}")
        continue

    for psm in psm_modes:

        print()
        print("----------------------------------------")
        print(f"Image : {image_name}")
        print(f"PSM   : {psm}")
        print("----------------------------------------")

        command = [
            "tesseract",
            str(image_path),
            "stdout",
            "-l",
            "kan",
            "--psm",
            str(psm)
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        output = result.stdout.strip()

        print(output)

        # Create safe filename
        image_stem = Path(image_name).stem

        output_file = (
            OCR_DIR
            / f"{image_stem}_psm{psm}.txt"
        )

        output_file.write_text(
            output,
            encoding="utf-8"
        )


print()
print("========================================")
print("OCR BASELINE EXPERIMENT COMPLETED")
print("========================================")
print(f"Results saved in:")
print(OCR_DIR)