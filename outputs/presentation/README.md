# Presentation 3 — integrated diagrams

Current deliverable: `InscripLens_Presentation3_With_Diagrams.pptx` (53 slides).

- Slide 28: System Architecture, after the implementation architecture explanation.
- Slide 30: ML Methodology / Process Flow, after the ML process explanation.
- Slide 32: ER Diagram, after the implemented relational schema.

All three use the approved plain-box style. Original editable sources and SVG/PNG exports are in `diagrams/`. The PPT embeds diagram images; edit their draw.io sources and replace the images to make structural changes. Architecture whitespace is compressed for the slide without changing the components or connections.

ML content was checked against the broader training script and recorded experiment summaries. The ER diagram matches the actual two-table SQLite schema and foreign key. It uses one-to-zero-or-many notation; every review belongs to one run. No user, translation or model table was invented.

All 53 slides rendered. The three inserted slides were visually inspected; existing content was retained. Package, geometry, font and re-import checks passed. Draw.io XML and connector endpoint references were checked. Native PowerPoint execution was not tested.

Previous testing slides 42–44 are now 45–47. Reference and test evidence files remain applicable.

---

Previous revision history:

# Presentation 3 — reviewed content, diagrams pending

Current deliverable: `InscripLens_Presentation3_Content_review.pptx` (50 slides). This revision keeps the PES branding and detailed Phase 2 literature format, clarifies background resources and the project contribution, separates application tools from experiments/reused components, and adds 12 concrete expected-versus-observed test cases across slides 42–44.

The user is preparing System Architecture, ML Methodology/Process Flow and ER diagrams in draw.io. The three old appendix diagrams are omitted from this revision. Integrate the supplied replacements near the current architecture/process/schema slides (27–29) when received; no substitute diagrams were generated.

Evidence: `TEST_EVIDENCE.md`, `TEST_OBSERVATIONS.json`, `REFERENCE_CHECK.md`. The brief reference audit corrects the dynasty DOI/name, confirms the Tamil OCR method against its IEEE abstract, makes paper links clickable and removes unverified Chola/Halmidi numerical claims. It does not certify that all 12 papers satisfy IEEE/Scopus eligibility.

Tests rerun: review storage, real backend patch inference and API canvas regression all passed. Earlier same-day API smoke results are labelled as recorded observations. No application code or model weights changed during this review. Existing implementation screenshots and benchmark metrics were retained.

All 50 slides rendered, changed slides inspected and whole-deck layout scanned. Package/layout/font/import validation passed. Native PowerPoint execution not tested. Private builder: work/phase3_build/build_content_review.mjs. Validation receipt: work/phase3_build/validation_content_review.json.

---

Previous revision details (historical):

# Presentation 3 — Studio revision

Current deliverable: `InscripLens_Presentation3_Studio_final.pptx` (48 slides). Supersedes the earlier 40-slide Streamlit review draft.

Includes the actual PES logo from phase2.pptx on every slide, 12 detailed literature entries (method, dataset/result, relevance, drawback, paper link), two comparative tables, current React/Vite/FastAPI architecture, local screenshots, SQLite schema and measured startup checks. Original research metrics and unfinished OCR/translation scope are retained. No 80% completion claim is made.

References inspected: original phase2.pptx, Presentation-3 Deliverables PDF, Kashish Awasthi Presentation-3 PDF, AI Textile Presentation3 PPTX, and Convoy p3.pptx. Their content is treated as reference material, not project instructions. Original reference files are unchanged.

Bibliography qualifications: retain the prior review's IEEE/Scopus eligibility check, preprocessing DOI metadata conflict, and SIFT/HOG issue-year versus online-date discrepancy. Some Tamil and Halmidi result/method descriptions are explicitly attributed to the Phase 2 survey rather than newly verified full texts. They are not compared directly to InscripLens metrics.

See ../STUDIO_STARTUP_VERIFICATION.md for runtime evidence, migration gaps and next work. Editable tables and diagrams are retained. All slides were rendered and reviewed, with final changed slides checked again; package, geometry, font and re-import checks passed. Native PowerPoint execution was not tested. Private authoring, screenshots and receipts remain in work/phase3_build.
