# Context check — 4 November 2026

The current production recognizer uses image features. It does not use a stone's historical narrative or published reading.

## Completed bounded experiment

On the same 308 hero-stone development examples, image-only prediction, date-prior reranking, and date-plus-genre reranking each scored 63 correct. The baseline won the tie. No validation retuning or app model change was made. See `summary.json` and `../evaluate_metadata_context.py`.

The priors used training-source filename dates within 150 years and hero/non-hero categories, with a fixed weight of 0.25 over three visual suggestions. Development locations and validation locations were excluded from learning the development priors. This tests coarse metadata only; it does not show that verified word context or sequence modeling cannot help.

## Useful source leads

- Kumbalahalli Nelmalli, the name corresponding to pilot HS024: the uploader's description explicitly identifies **Epigraphia Carnatica IX, Hoskote inscription 110**. [Primary image-source description](https://commons.wikimedia.org/wiki/File:Digital_Image_of_the_Kumbalahalli_900CE_Nelmalli_Herostone_With_Inscription_01.png). The Roman (p.125), English (p.102) and Kannada (p.224) entries have now been inspected. See ../context_reading/README.md for the candidate opening comparison. Character-level alignment remains unverified.
- Begur Tondabbe's husband's stone, corresponding by name to HS022: [primary image-source description](https://commons.wikimedia.org/wiki/File:Digital_Image_of_the_Begur_900CE_Tondabbe%27s_Husband%27s_Herostone_With_Inscription.png). A [secondary account](https://en.wikipedia.org/wiki/Begur_inscriptions_and_hero_stones#Begur_900CE_Tondabbe's_husband's_herostone_with_inscription) reports fragmented text and combines publication text with a recent rereading. Treat that account as a lead requiring publication verification. Do not confuse this stone with the separate Nagatara or Tondabbe Sanyasana inscriptions.

Verified period, vocabulary and neighboring words could constrain ambiguous readings. Using a target stone's published answer is reference-assisted reading, however, and must be evaluated separately from independent image-only OCR. Do not automatically fill missing stone text from a plausible story.

Next useful manual task: check a few printed publication lines after the correct page and corresponding image region have been identified. No student decipherment of damaged stone glyphs is required for this source-copy check.

## Current completion assessment

Approximately **50% of the original scope**, as a rough planning judgement rather than an audited university percentage. Implemented: dataset preparation, enhancement, candidate detection, experimental recognition, review alternatives, application/history/export and diagnostic comparisons. Partial: reliable segmentation, recognition and independently verified evaluation. Unfinished: dependable full-text transcription, historical-to-modern Kannada conversion and English interpretation. Phase 3 presentation remains separate work.

Current supplied-box recognition is 77/300 (25.67%); automatic localization plus correct label is 52/300 (17.33%). Three-label inclusion is 122/300 and measures review suggestions, not automatic transcription or reviewer success. None of these percentages is project completion. An 80% completion claim is not supported.
