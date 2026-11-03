# EpiSAM archive audit — 2 November 2026

## Result

Downloaded and inspected the public EpiSAM archive. It provides a concrete candidate source for segmentation and potentially character-label experiments, including hero-stone records. It does not yet establish a cleaned Kannada recognition benchmark.

Source: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset
Official project: https://ihdia.iiit.ac.in/episam/
Archive: https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset/resolve/main/episam_dataset.zip

Downloaded archive size: 403,767,141 bytes. SHA-256: `91c057c87af5f2fe2442b01faf8d92b521d62f3eea4b5421214cce1b8d84157a`.
ZIP CRC check passed. Original image files decoded successfully in the audit. Archive is in the chat workspace under work/, not installed into the user's capstone project.

## Actual contents

| Item | Count |
|---|---:|
| Original images | 148 |
| Original images in train / val | 117 / 31 |
| PNG binary images paired by exact name | 148 |
| Character polygon JSON files | 148 |
| Character annotation records | 13,498 |
| Distinct character-name strings, including placeholders | 840 |
| Original image names containing hero | 27 |
| Hero-named train / val images | 21 / 6 |
| Character records associated with hero-named images | 1,428 |

The 27 are filename-selected image records, not a verified count of independent hero stones. Multiple views and duplicate identities require grouping. The dataset viewer's 1,911 rows correspond to the archive's total files, not 1,911 stones.

Character JSON fields include char_name, line_number, char_number, bounding boxes and several polygon types. Character names are transliteration-like strings (for example sva, stya and kā), not ready-made full Kannada Unicode transcriptions. Names and their encodings must be audited before any automatic conversion. Existing numeric confidence values must not be interpreted as independently established transcription accuracy.

## Aradeshanahalli finding

The archive includes `Aradeshanahalli 900CE Mumennayaga's Turugol Herostone With Inscription`, a 1371 × 1080 image visibly depicting the stone in the local VG_C001 render. It has 125 character records. Its image and binary file have matching dimensions, all tested boxes are in bounds, and no repeated line/character position was found in this record.

The supplied first-line records begin with siddhaṁ, sva, stya, kā, la, va, rṣa. The overlay `EpiSAM_Aradeshanahalli_line1_labels.png` uses the dataset's coordinates and labels without newly deciphering characters. Visually, the boxes follow the opening text band. This is stronger alignment evidence than our previous unannotated crop, but not a declaration that every supplied label is correct.

The supplied line-5 sequence includes ti, pā, li; the line-14 sequence is ni, kki, si, sa, ttaṁ, NaNl. This supports investigating earlier printed-copy readings while demonstrating why placeholders cannot simply be converted to Kannada. Dataset and historical publication versions may differ, so neither should overwrite the other.

## Quality issues detected

- 14 paired image/binary PNGs have different dimensions. All 27 hero-named records passed the dimension check, but this does not prove pixel alignment or mask correctness.
- One character bounding box falls outside its image bounds across the full dataset.
- 42 excess duplicate (line_number, char_number) positions occur across the full dataset. Two hero-named records have one each: Atturu Ereyamma and Maranayakanahalli.
- The labels include 718 occurrences of NaNl and 76 occurrences represented as None in the audit. Their original meaning needs inspection; treat them as unresolved rather than valid recognition classes.
- An identical decoded RGB image appears in both splits under different names: Mutkur 1500CE Donation Inscription (train) and Mutkur 1400CE Agrahara Inscription (val). Split leakage is therefore demonstrably present in the full release. Other near-duplicates have not yet been exhaustively checked.
- Same-sized binary files are not automatically independent ground-truth stroke masks. The provenance of those binary files must be established before using them to score binarization; the EpiSAM method uses a learned binarizer to generate prompts. Character polygon variants also must be interpreted according to their documented generation process.

## Terms and provenance

The downloaded public repository README declares CC BY-SA 4.0 and credits Mythic Society. No separate licence or README file occurs inside this ZIP (only PNG and JSON files). Preserve the repository licence declaration, attribution, source and requested paper citations. This audit accessed the public release linked from the authors' institutional project, not the restricted Akshara Bhandara website/corpus. The code's separate Apache licence is not the dataset licence.

Overlay attribution: original inscription image and annotations from the EpiSAM public release, authors Arnav Sharma, Pratyush Jena, Amal Joseph and Ravi Kiran Sarvadevabhatla; inscription-image provider credited by the release: Mythic Society Bengaluru, Inscriptions 3D Digital Conservation Project. Source and terms above; https://creativecommons.org/licenses/by-sa/4.0/. Modification: supplied line-1 bounding boxes and labels drawn over image for inspection.

## Recommended next experiment

Build an auditable hero-stone subset manifest, keeping parent-stone grouping, original splits and all exclusions explicit. First inspect several character crops against the supplied labels; separate placeholders and ambiguous labels. Use the subset for a segmentation baseline once annotation semantics are established. Recognition experiments become a possibility only after label conventions and support per class are checked; do not claim that 1,428 records suffice for training a robust recognizer.

No model was trained, no OCR accuracy was calculated, and none of the previous Category C candidate records was silently promoted. The original capstone files remain unchanged.
