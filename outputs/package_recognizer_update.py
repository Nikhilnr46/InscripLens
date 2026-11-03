"""Build a small, checksummed model update; excludes private analysis history."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parent.parent
FILES=['outputs/broad_clean_study/mask_svm_bundle.joblib','outputs/broad_clean_study/summary.json','outputs/broad_pipeline_study/summary.json','THIRD_PARTY.md']
destination=ROOT/'outputs/InscripLens_recognizer_update.zip'
manifest={name:{'bytes':(ROOT/name).stat().st_size,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in FILES}
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in FILES:z.write(ROOT/name,name)
    z.writestr('recognizer_update_checksums.json',json.dumps(manifest,indent=2))
    z.writestr('README_RECOGNIZER_UPDATE.txt','InscripLens recognizer update, 3 November 2026\n\nFirst pull the latest main branch. Extract this ZIP into the repository root, preserving paths, then restart Streamlit. Keep the earlier runtime asset pack: this update does not include the enhancer or demonstration images.\n\nThe app prefers the broader cleaned-data model when installed and falls back to the hero-only model otherwise. Supplied-box diagnostic: 77/300 (25.67%); automatic localized-and-correct diagnostic: 52/300 (17.33%). Reused validation, unverified source labels, uncertain enhancer pretraining overlap. This is not reliable full-text OCR or translation.\n\nThe model was trained using public EpiSAM annotations and masks derived using Shilalekhya. Preserve THIRD_PARTY.md attribution and upstream CC BY-SA 4.0 notices. No private analysis history is included.\n')
with zipfile.ZipFile(destination) as z:
    assert z.testzip() is None
    for name,entry in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==entry['sha256']
print(json.dumps({'path':str(destination),'bytes':destination.stat().st_size,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'checked_files':len(FILES)},indent=2))
