# Explaining InscripLens honestly

The project reuses a published pretrained enhancement model and public annotations. It does not claim to have invented or trained that enhancement model. Its current contribution is application engineering and a measured study of how these components perform on a hero-stone pilot. A guide may reasonably require more algorithmic novelty; acceptance cannot be guaranteed from attribution alone.

## What belongs to whom

| Component | Origin | What this project did |
|---|---|---|
| Stone images and supplied character annotations | EpiSAM authors and credited imagery provider | Audited records, filtered pilot, tracked sources/exclusions and checked split problems |
| Shilalekhya Attention U-Net and weights | IIIT Hyderabad authors | Adapted CPU execution, tiled full-image inference, integrated outputs and measured downstream recognition |
| HOG/SVM, CNN, connected components | Established techniques | Implemented/combined standard methods and evaluated fixed experiments; no novel architecture claim |
| InscripLens application | Implementation developed in this project with coding assistance | Upload, enhancement, candidate review, predictions, downloads and SQLite history |
| Historical conversion and translation | Not implemented | Do not present them as delivered functionality |

## A possible answer to the panel

“I used a published pretrained enhancement model because training an equivalent model would require substantial pixel-level annotation. I credit that component explicitly. My work focuses on preparing and auditing a hero-stone pilot, integrating enhancement with detection and recognition, comparing approaches, and building an application for review. The tests also show the limits: cleaned-image training improved our SVM from15% to21%, but reliable full transcription remains unresolved. I am not claiming a new enhancement architecture.”

Use this only if you can explain the code and experiment yourself. Describe AI assistance according to your university's requirements; do not imply that assisted implementation was independently authored or that you performed expert epigraphic verification.

## What to understand before demonstrating

- Binarization predicts which pixels are foreground strokes. It does not assign Kannada letters or translate language.
- Connected components group touching foreground pixels. Broken glyphs can split; touching glyphs can merge.
- Recognition assigns a raw source label to a supplied crop. Reference-box recognition scores omit automatic-segmentation errors.
- Validation used to select settings can inflate estimates. Our settings are chosen on training-only development sites, but the final validation has been reused and binarizer pretraining overlap is incomplete.
- Accuracy measures exact source-label matches; it does not measure project completion.

## Credit placement

Keep the short credits and source links. The app now has an expandable About section distinguishing project implementation from reused components. More detailed attribution stays in the README and research report. Removing credit would not create originality or resolve a novelty requirement.

Sources: https://github.com/ihdia/shilalekhya-binarization (MIT code); https://huggingface.co/keyfinder08/EpiSAM_Inscriptions_Project and https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset (repository declarations CC BY-SA4.0). These notices and ownership statements are distinct from any institutional assessment of academic contribution.
