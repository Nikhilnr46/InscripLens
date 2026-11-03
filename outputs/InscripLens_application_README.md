# InscripLens local application

Start from this workspace with `python -m streamlit run outputs/inscriplens_app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false`, or double-click Launch_InscripLens.cmd. If already running, open http://127.0.0.1:8501 instead of starting a second copy.

## Implemented workflow

Update: automatic connected-component candidate boxes are now displayed and selectable, with manual adjustment. A public Nagavara demo option exercises the same enhancement flow as an upload. The matched-mask model is now available and used; its diagnostic character accuracy is21%. Candidate-region precision/recall is59.39%/65.33%, evaluated separately. See matched_mask_study and segmentation_study reports.

Additional validation: Streamlit AppTest selected the public demo, invoked real enhancement, selected an automatic candidate, requested a prediction, and opened Saved analyses without exceptions. That run intentionally saved one public demo analysis in local history. This exercises UI application logic but is not a visual browser-layout audit.

- Upload JPEG/PNG, validate decoding, orient using EXIF and resize a working copy to at most 1600px on its longest side. Original uploaded bytes are hashed; the processed copy is stored locally.
- Run pretrained single-scale tiled enhancement in a separate Python 3.12 worker. Display original/mask side by side and download mask/analysis JSON.
- Save successful analyses to SQLite and reload them from Saved analyses. Local storage is work/app_data. Failed jobs do not enter successful history; partial files may remain for debugging.
- Enter a rectangle for one character and run the saved SVM. Display a raw transliteration prediction with an explicit unverified label. This is manual cropping, not automatic segmentation. Character prediction JSON can be downloaded; character predictions are not indexed in history.
- Explore six public validation images, annotation references, and saved model predictions. View exact recorded experiment results separately.

The application selects the matched-mask SVM when available, otherwise the original-trained broader SVM with original crops. Neither model is an accurate production OCR system. App model choice is for demonstration, not evidence of independent performance.

## Validation

`python outputs/check_app.py`: Streamlit AppTest navigation through all four views without exceptions.

`python outputs/check_app_backend.py`: invalid image rejection, actual subprocess enhancement, output shape/binary pixel checks, SQLite insertion/reload and connection cleanup. Test storage uses a temporary workspace directory, not the user's history. This caught and fixed an open SQLite connection on Windows.

Local HTTP health endpoint checked. No full browser upload/crop interaction automation has been performed. Application is a research prototype; multi-user deployment has not been tested. SQLite history is persistent, not a backup system. Stop the server with Ctrl+C in its launch terminal.

## Dependencies and limits

UI/classifier uses system Python with streamlit, Pillow, numpy, joblib and scikit-learn. Inference uses work/binarizer_env/Scripts/python.exe with torch 2.5.1+cpu and the downloaded checkpoint in work/shilalekhya. Paths are relative to this workspace, so move the work folder with outputs if relocating. This is not yet a standalone packaged installer or integration into C:/Users/nikhi/MCA/Capstone-InscripLens.

Uploads over 20 megapixels are rejected. Worker timeout is 300 seconds. CPU performance depends on size. No GPU execution configured. Model masks may omit or alter strokes; no historical text restoration claim. Translation and historical-to-modern Kannada conversion remain unavailable. No external messaging or cloud OCR used.

## Attribution

Shilalekhya implementation: https://github.com/ihdia/shilalekhya-binarization , MIT, copyright 2025 ihdia. License retained in work/shilalekhya/LICENSE. Public model repository: https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project , CC BY-SA 4.0.

Public dataset/derived previews: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset , CC BY-SA 4.0. Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla; imagery acknowledged to The Mythic Society Bengaluru. Retain attribution and share-alike terms when distributing derived previews: https://creativecommons.org/licenses/by-sa/4.0/ . See EpiSAM_source_README.md for supplied citations. No restricted corpus accessed.
