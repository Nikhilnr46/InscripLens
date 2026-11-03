# Kumbalahalli reference comparison

Epigraphia Carnatica IX, Hoskote entry 110 has been located in all three sections:

| Section | Printed page | Archive scan |
| --- | --- | --- |
| Roman transcription | 125 | [n204](https://archive.org/download/epigraphiacarnat09myso/page/n204.jpg) |
| English translation | 102 | [n419](https://archive.org/download/epigraphiacarnat09myso/page/n419.jpg) |
| Kannada reading | 224 | [n729](https://archive.org/download/epigraphiacarnat09myso/page/n729.jpg) |

The Kannada entry is at the top of page 224: read numbered lines 1–5 in the left column, then 6–9 in the right column. Its nine lines do **not** correspond one-to-one to the dataset's eight line groups. The opening two lines are a promising phrase-level comparison, not a verified character alignment.

The published English account describes cattle protection and a subsequent land grant, and dates the inscription approximately 900 CE. This is publication context, **not an InscripLens translation**. The Roman reading's Nelmalla differs from the dataset's nĕlmalli; neither has been silently substituted for the other.

`HS024_reference.json` records scan URLs and hashes, all 98 existing annotation labels grouped by their eight dataset lines, candidate opening correspondence, and unresolved differences. Labels retain their unreviewed status. HS024 belongs to validation: this reference must not be used to train or retune the model and then claim independent accuracy on the same stone.

Local inspection images:

- `HS024_Kannada_entry110.png`: full printed entry, with heading.
- `HS024_printed_opening.png`: only the first two printed lines, suitable for a small source-copy check.
- `HS024_annotated_opening_region.png`: stone region enclosing the first two dataset line groups. This region is selected using source annotation boxes, not automatic line detection.

Reproduce with `python outputs/context_reading/build_hs024_reference.py` after obtaining the three linked scans under the filenames recorded in the JSON, the pilot manifest and HS024 original image. Scans and derived images are local assets excluded from Git. Stone imagery is from EpiSAM / Mythic Society; existing third-party attribution applies. The historical publication is public domain.

Next: check a short printed passage, explicitly encode uncertain historical glyphs, then review phrase-to-region correspondence. A student can check printed text without being asked to decipher the stone. No recognition scores, training labels, or application predictions changed in this step.
