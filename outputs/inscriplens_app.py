"""Local research application. Run: python -m streamlit run outputs/inscriplens_app.py"""
from pathlib import Path
from types import SimpleNamespace
import os, hashlib, io, json, subprocess
import streamlit as st
from PIL import Image, ImageOps
import joblib
from run_character_benchmark import features
from app_backend import analyse, history, save_review, reviews, review_export
from segment_candidates import candidates, overlay
from recognize_regions import recognize
from recognition_alternatives import rank_labels, source_examples

ROOT = Path(__file__).resolve().parent.parent
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MASK_MODELS = [
    ROOT / 'outputs/broad_clean_study/mask_svm_bundle.joblib',
    ROOT / 'outputs/matched_mask_study/mask_svm_bundle.joblib'
]
CLEAN_MODEL = next((p for p in MASK_MODELS if p.is_file()), MASK_MODELS[-1])
DATA = ROOT / 'work/app_data'
DATA.mkdir(parents=True, exist_ok=True)

ADVANCED_MODE = os.environ.get('INSCRIPLENS_ADVANCED', '').strip().lower() in ('1', 'true', 'yes', 'on')

st.set_page_config(page_title='InscripLens', layout='wide')

# Load and inject presentation styles
css_candidates = [ROOT / 'ui/styles.css', ROOT / 'styles.css', ROOT / 'outputs/styles.css', ROOT / '.streamlit/styles.css']
css_path = next((p for p in css_candidates if p.is_file()), None)
css_content = css_path.read_text(encoding='utf-8') if css_path else ""

if not ADVANCED_MODE:
    css_content += """
    #MainMenu {visibility: hidden; display: none !important;}
    footer {visibility: hidden; display: none !important;}
    header {visibility: hidden; display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    [data-testid="stDecoration"] {visibility: hidden; display: none !important;}
    [data-testid="stStatusWidget"] {visibility: hidden; display: none !important;}
    """

if css_content:
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)

# UI demo showcase review page (?ui_demo=1)
if st.query_params.get('ui_demo') == '1':
    from ui.components import render_ui_demo
    render_ui_demo()
    st.stop()

from ui.components import page_header, card, notice

# Main header with title, one-line subtitle, and compact notice
page_header('InscripLens', 'Historical Kannada Inscription Image Analysis')
notice('Research prototype for local epigraphic enhancement and diagnostic character recognition.')

# Long disclaimer moved into an expander named "Limitations of this prototype"
with st.expander('Limitations of this prototype'):
    st.write('Research prototype: enhancement works; character recognition is experimental. Published/source labels are references, not automatic readings. Translation is not yet available in the Studio interface (the API only offers a rule-based draft for reviewer-verified formulaic hero-stone text). All machine translations are unverified drafts requiring expert epigraphic verification.')

# Branded sidebar header: app name and one-line tagline at top
st.sidebar.markdown('''
<div class="sidebar-brand">
    <div class="sidebar-brand-title">InscripLens</div>
    <div class="sidebar-brand-tagline">Historical Kannada Inscription Analysis</div>
</div>
''', unsafe_allow_html=True)

# Grouped navigation: Workspace, Reference, and Advanced (when INSCRIPLENS_ADVANCED is on)
WORKSPACE_PAGES = ['Analyse an image']
REFERENCE_PAGES = ['Published reading review', 'Credits']
ADVANCED_PAGES = ['Dataset explorer', 'Experiment results', 'Saved analyses', 'Setup status']

workspace_pages = WORKSPACE_PAGES + REFERENCE_PAGES + (ADVANCED_PAGES if ADVANCED_MODE else [])

page = st.sidebar.radio(
    'Navigation',
    workspace_pages,
    label_visibility='collapsed'
)

# Sidebar footer note
st.sidebar.markdown('''
<div class="sidebar-footer-note">
    Runs locally. No cloud OCR.
</div>
''', unsafe_allow_html=True)

enhancement_files = ['work/binarizer_env/Scripts/python.exe', 'work/shilalekhya/Unet/model.py', 'work/shilalekhya/binarizer.pth']
missing_enhancement = [p for p in enhancement_files if not (ROOT / p).is_file()]

def setup_message(message):
    if ADVANCED_MODE:
        st.warning(message)
        st.markdown('Open **Setup status** and follow the [collaborator setup guide](https://github.com/Nikhilnr46/InscripLens/blob/main/COLLABORATOR_HANDOVER.md). Runtime assets must be extracted into the repository root.')
    else:
        st.warning('Required analysis assets are not installed locally. Please contact the administrator.')

if page == 'Analyse an image':
    # Container for the 3-step indicator placed before the upload area
    step_indicator_placeholder = st.container()

    sample = ROOT / 'outputs/full_binarizer/HS027_original.png'
    demo_available = sample.is_file()
    if not demo_available:
        setup_message('The optional demonstration image is not installed. You can still upload your own image.')

    # Upload area with "Try the demo stone" button beside Upload
    up_col1, up_col2 = st.columns([3, 2])
    with up_col1:
        upload = st.file_uploader('Upload a stone image', type=['png', 'jpg', 'jpeg'])
    with up_col2:
        st.write('Sample demonstration image:')
        if st.button('Try the demo stone', disabled=not demo_available):
            st.session_state.use_demo = True
        use_demo_cb = st.checkbox('Use the public Nagavara demonstration image', value=st.session_state.get('use_demo', False), disabled=not demo_available)
        if use_demo_cb != st.session_state.get('use_demo', False):
            st.session_state.use_demo = use_demo_cb

    if (st.session_state.get('use_demo') or use_demo_cb) and demo_available and not upload:
        upload = SimpleNamespace(name='Nagavara_public_demo.png', getvalue=sample.read_bytes)
    
    # 3-step indicator reflecting existing state
    record = st.session_state.get('run')
    has_pred = bool(record and st.session_state.get('character_prediction'))
    s1_cls = "completed" if upload else "current"
    s2_cls = "completed" if record else ("current" if upload else "pending")
    s3_cls = "completed" if has_pred else ("current" if record else "pending")

    with step_indicator_placeholder:
        st.markdown(f'''
        <div class="step-container">
            <div class="step-item step-{s1_cls}">
                <span class="step-num step-badge-{s1_cls}">1</span>
                <span class="step-text-{s1_cls}">Upload</span>
            </div>
            <div class="step-item step-{s2_cls}">
                <span class="step-num step-badge-{s2_cls}">2</span>
                <span class="step-text-{s2_cls}">Enhance</span>
            </div>
            <div class="step-item step-{s3_cls}">
                <span class="step-num step-badge-{s3_cls}">3</span>
                <span class="step-text-{s3_cls}">Recognise</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # 2. Empty state for when no image is uploaded
    if not upload:
        st.info('Upload an image to begin, or select the demonstration stone.')

    if upload:
        try:
            raw = upload.getvalue()
            digest = hashlib.sha256(raw).hexdigest()
            image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
            if image.width * image.height > 20_000_000:
                raise ValueError('Please use an image below 20 megapixels.')
        except Exception as exc:
            if ADVANCED_MODE:
                st.error(f'Cannot open image: {exc}')
            else:
                st.error('Cannot open image. Please check that the file is a valid image below 20 megapixels.')
            st.stop()
            
        if st.session_state.get('digest') != digest:
            st.session_state.digest = digest
            st.session_state.pop('run', None)
            st.session_state.pop('character_prediction', None)
            
        st.image(image, caption=f'Uploaded original - {image.width} x {image.height}', width=600)
        st.caption('Analysis uses a copy with longest side at most 1600 pixels. Enhancement predicts foreground strokes; it may omit or alter damaged strokes.')
        
        if missing_enhancement:
            setup_message('Enhancement runtime is incomplete: ' + ', '.join(missing_enhancement))
            
        # 1. Wrap enhancement in spinner with plain message
        if st.button('Enhance inscription', type='primary', disabled=bool(missing_enhancement)):
            try:
                with st.spinner('Separating likely inscription strokes from background...'):
                    record = analyse(raw, upload.name)
                st.session_state.run = record
                st.session_state.pop('character_prediction', None)
            except (subprocess.SubprocessError, ValueError, OSError) as exc:
                st.error('Enhancement could not finish. No successful analysis was saved.')
                if ADVANCED_MODE:
                    st.code(str(exc))
                
        record = st.session_state.get('run')

        # 2. Empty state when image is uploaded but not enhanced yet
        if upload and not record:
            st.info('Image ready. Click "Enhance inscription" above to begin foreground stroke analysis.')

        if record:
            if not all(Path(record[k]).is_file() for k in ['image_path', 'mask_path']):
                if ADVANCED_MODE:
                    setup_message('This saved analysis refers to image files that are no longer available. Run enhancement again.')
                else:
                    st.warning('The image files for this saved analysis are no longer available.')
                st.stop()
                
            st.success('Enhancement saved locally.')
            mask = Image.open(record['mask_path'])
            original = Image.open(record['image_path'])
            
            # Original and enhanced image side by side
            left, right = st.columns(2)
            left.image(original, caption='Analysis input', width='stretch')
            right.image(mask, caption='Predicted foreground mask', width='stretch')
            
            # Mask and detected regions in st.tabs
            tab_mask, tab_regions = st.tabs(['Predicted Mask', 'Detected Regions'])

            with tab_mask:
                st.subheader('Predicted Mask & Downloads')
                dl_col1, dl_col2 = st.columns(2)
                dl_col1.download_button('Download predicted mask', Path(record['mask_path']).read_bytes(), 'inscriplens_mask.png', 'image/png')
                if ADVANCED_MODE:
                    dl_col2.download_button('Download analysis record', json.dumps(record, indent=2), 'inscriplens_analysis.json', 'application/json')
                st.caption('Foreground mask highlights likely inscription strokes extracted from the stone surface.')

            with tab_regions:
                st.subheader('Experimental character recognition')
                if CLEAN_MODEL.is_file():
                    if ADVANCED_MODE:
                        st.caption('Recognizer: ' + ('broader cleaned-data model' if CLEAN_MODEL == MASK_MODELS[0] else 'hero-only baseline'))
                    else:
                        st.caption('Recognizer: Experimental recognizer')
                boxes = candidates(mask)
                st.markdown(f'<div style="font-size: 1.25rem; font-weight: 600; color: #F3F4F6; margin: 0.5rem 0;">{len(boxes)} candidate regions</div>', unsafe_allow_html=True)
                st.caption('Automatic connected-component detector. These may split a letter or combine several; their order is not a verified reading order.')
                st.image(overlay(original, boxes), caption='Automatic candidate boxes', width=600)
                if ADVANCED_MODE:
                    st.download_button('Download candidate boxes', json.dumps({'boxes_xyxy': boxes, 'verified': False, 'method': 'connected_components'}), 'candidate_boxes.json')
                
                batch_model = CLEAN_MODEL
                # 1. Wrap batch region prediction in spinner with plain message
                if st.button('Predict all detected regions', type='primary', disabled=not batch_model.is_file()):
                    with st.spinner('Predicting detected candidate labels...'):
                        batch = recognize(mask, joblib.load(batch_model))
                    payload = {
                        'run_id': record['id'],
                        'method': 'predicted_mask_components_mask_svm',
                        'model_sha256': hashlib.sha256(batch_model.read_bytes()).hexdigest(),
                        'verified_transcription': False,
                        'reading_order_verified': False,
                        'regions': batch
                    }
                    path = DATA / record['id'] / 'automatic_regions.json'
                    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
                    
                batch_path = DATA / record['id'] / 'automatic_regions.json'
                if batch_path.exists():
                    payload = json.loads(batch_path.read_text(encoding='utf-8'))
                    st.caption('Automatic region predictions: no reference boxes supplied. These labels are not a verified sentence or reading order.')
                    st.dataframe(payload['regions'], hide_index=True)
                    st.download_button('Download automatic region predictions', json.dumps(payload, ensure_ascii=False, indent=2), 'automatic_regions.json', 'application/json')
                
                with st.expander('Advanced: pick a region manually'):
                    chosen = st.selectbox('Start from a detected region', range(len(boxes) + 1), format_func=lambda i: 'Manual rectangle' if i == 0 else f'Candidate {i}')
                    initial = boxes[chosen - 1] if chosen else [0, 0, min(original.width, 100), min(original.height, 100)]
                    st.write('Review or adjust the rectangle before predicting. A candidate is not necessarily one complete character.')
                    w, h = original.size

                    # Live crop preview of chosen rectangle (display only, read-only use of image)
                    cur_x1 = int(st.session_state.get(f'left_{chosen}', initial[0]))
                    cur_y1 = int(st.session_state.get(f'top_{chosen}', initial[1]))
                    cur_x2 = int(st.session_state.get(f'right_{chosen}', initial[2]))
                    cur_y2 = int(st.session_state.get(f'bottom_{chosen}', initial[3]))
                    if cur_x2 > cur_x1 and cur_y2 > cur_y1 and cur_x1 >= 0 and cur_y1 >= 0 and cur_x2 <= w and cur_y2 <= h:
                        clean_preview = CLEAN_MODEL.exists()
                        live_preview_crop = (mask if clean_preview else original).crop((cur_x1, cur_y1, cur_x2, cur_y2))
                        st.image(live_preview_crop, caption=f'Live crop preview: {cur_x2 - cur_x1} x {cur_y2 - cur_y1} px', width=140)

                    recognizer_available = CLEAN_MODEL.is_file() or (ROOT / 'outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib').is_file()
                    if not recognizer_available:
                        setup_message('No recognition model is installed. Enhancement and candidate downloads remain available.')
                        
                    with st.form('crop'):
                        cols = st.columns(4)
                        x1 = cols[0].number_input('Left', 0, w - 1, initial[0], key=f'left_{chosen}')
                        y1 = cols[1].number_input('Top', 0, h - 1, initial[1], key=f'top_{chosen}')
                        x2 = cols[2].number_input('Right', 1, w, initial[2], key=f'right_{chosen}')
                        y2 = cols[3].number_input('Bottom', 1, h, initial[3], key=f'bottom_{chosen}')
                        submitted = st.form_submit_button('Predict this character', disabled=not recognizer_available)
                        
                    if submitted:
                        if x2 <= x1 or y2 <= y1:
                            st.error('Right and bottom must exceed left and top.')
                        else:
                            # 1. Wrap single-character prediction in spinner with plain message
                            with st.spinner('Predicting candidate character label...'):
                                model_path = CLEAN_MODEL
                                clean = model_path.exists()
                                if not clean:
                                    model_path = ROOT / 'outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib'
                                crop = (mask if clean else original).crop((x1, y1, x2, y2))
                                path = DATA / record['id'] / 'character.png'
                                crop.save(path)
                                bundle = joblib.load(model_path)
                                feature = features(path, bundle['preprocessing'])
                                alternatives = rank_labels(bundle['model'], feature, 3)[0]
                                pred = alternatives[0]
                                examples = source_examples(bundle['model'], feature, alternatives, model_path, ROOT / 'outputs/recognition_references.zip')
                                st.session_state.reference_examples = examples
                            st.image(crop, caption='Selected model input', width=180)
                            st.write('**Unverified predicted source label:**', pred)
                            st.caption('Raw transliteration label, not a verified Kannada transcription. No calibrated confidence is available.')
                            st.session_state.character_prediction = {
                                'run_id': record['id'],
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'prediction': pred,
                                'alternatives': alternatives,
                                'reference_examples': [{k: v for k, v in e.items() if k != 'image_bytes'} for e in examples],
                                'model': model_path.name,
                                'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
                                'verified': False
                            }
                            
                prediction = st.session_state.get('character_prediction')
                if prediction and prediction['run_id'] == record['id']:
                    st.write('Latest prediction:', prediction['prediction'], '- rectangle', prediction['bbox'])
                    if prediction.get('alternatives'):
                        st.write('Ranked labels to inspect:', ', '.join(prediction['alternatives']))
                        st.caption('Alternatives are suggestions, not calibrated confidence or verified readings. The original first-choice prediction is preserved.')
                        examples = st.session_state.get('reference_examples', [])
                        if examples:
                            st.write('Annotated training examples for visual comparison')
                            columns = st.columns(len(examples))
                            for column, example in zip(columns, examples):
                                column.image(example['image_bytes'], caption=example['label'], width=140)
                                column.caption(example['source_name'])
                            st.caption('These source-labelled training crops are not independent confirmation. Image similarity alone cannot verify an inscription reading.')
                    st.download_button('Download character prediction', json.dumps(prediction, ensure_ascii=False, indent=2), 'character_prediction.json')
                    
                    with st.form('review_' + record['id']):
                        st.write('Save this prediction or add a suggested correction. Suggestions are unverified and are not added to training automatically.')
                        suggestion = st.text_input('Suggested label (optional)')
                        reviewer = st.text_input('Reviewer name or initials (optional)')
                        note = st.text_area('Source or review note (optional)')
                        save = st.form_submit_button('Save review record')
                    if save:
                        save_review(record['id'], prediction['bbox'], prediction['prediction'], prediction['model'], prediction['model_sha256'], suggestion, reviewer, note)
                        st.success('Review record saved. The original model prediction is preserved.')
                if ADVANCED_MODE:
                    st.download_button('Export saved reviews', json.dumps(review_export(record['id']), ensure_ascii=False, indent=2), 'inscriplens_reviews.json', 'application/json')

elif page == 'Dataset explorer':
    required = ['work/hero_pilot/manifest.json', 'outputs/full_binarizer/recognition_predictions.json']
    missing = [p for p in required if not (ROOT / p).is_file()]
    if missing:
        setup_message('Dataset explorer assets are missing: ' + ', '.join(missing))
        st.stop()
    rows = json.loads((ROOT / 'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    names = {r['image_id']: r['source_name'] for r in rows if r['source_split'] == 'val'}
    # 2. Empty state when no validation images exist
    if not names:
        st.info('Upload an image to begin. The manifest contains no validation images.')
        st.stop()
    selected = st.selectbox('Validation image', list(names), format_func=lambda x: names[x])
    comparison = ROOT / f'outputs/full_binarizer/{selected}_comparison.png'
    if comparison.is_file():
        st.image(str(comparison), caption='Original / predicted mask')
    else:
        setup_message('The comparison image is not installed for this entry. Saved prediction records are shown below.')
    predictions = json.loads((ROOT / 'outputs/full_binarizer/recognition_predictions.json').read_text(encoding='utf-8'))
    subset = [r for r in predictions if r['image_id'] == selected]
    st.caption('Saved frozen-model experiment. Reference labels and crop boxes come from EpiSAM annotations; they are not independently verified readings.')
    st.dataframe(subset, width='stretch')
    st.download_button('Download displayed comparison', json.dumps(subset, ensure_ascii=False, indent=2), 'source_label_comparison.json')

elif page == 'Published reading review':
    st.subheader('Kumbalahalli: published reading comparison')
    folder = ROOT / 'outputs/context_reading'
    reference = folder / 'HS024_reference.json'
    if not reference.is_file():
        st.info('The reference comparison is not installed. Pull the latest project code and reports.')
        st.stop()
    document = json.loads(reference.read_text(encoding='utf-8'))
    st.warning('Candidate alignment, not expert verified. The displayed labels are existing dataset annotations, not model predictions.')
    st.write(document['publication'])
    st.write(document['context_summary'])
    st.caption('Context is summarized from the published English translation. InscripLens has not translated this inscription.')
    left, right = st.columns(2)
    for column, filename, caption in [
        (left, 'HS024_annotated_opening_region.png', 'Stone region selected from annotation boxes for dataset groups 1-2'),
        (right, 'HS024_printed_opening.png', 'Published Kannada lines 1-2: candidate phrase correspondence')
    ]:
        with column:
            if (folder / filename).is_file():
                st.image(str(folder / filename), caption=caption)
            else:
                st.info(caption + ' - local preview unavailable; publication links remain available below.')
    st.write('The publication has nine numbered lines; the dataset has eight groups. Line numbers cannot be matched automatically.')
    st.dataframe([{'Dataset group': line['dataset_line'], 'Source annotation labels (unreviewed)': ' | '.join(line['labels'])} for line in document['dataset_lines']], hide_index=True, width='stretch')
    st.subheader('Publication sources')
    for source in document['scans']:
        st.markdown(f"[{source['section']} - printed page {source['printed_page']}]({source['url']})")
    with st.expander('Full printed Kannada entry'):
        if (folder / 'HS024_Kannada_entry110.png').is_file():
            st.image(str(folder / 'HS024_Kannada_entry110.png'))
        else:
            st.caption('Use the Kannada publication link above.')
    st.subheader('Still to verify')
    book_result = ROOT / 'outputs/book_ocr_study/result.json'
    if book_result.is_file():
        with st.expander('Printed-page OCR draft - separate Tesseract baseline'):
            draft = json.loads(book_result.read_text(encoding='utf-8'))
            st.warning('Unverified draft with visible recognition errors. This uses pretrained Tesseract Kannada OCR, not the InscripLens stone classifier. Editing does not make the text independently verified.')
            st.caption('Saved run on manually cropped publication columns; this is not live OCR of an uploaded book.')
            edited = {}
            for region in draft['regions']:
                if region['region'] == 'opening_two_lines':
                    continue
                edited[region['region']] = st.text_area(region['region'].replace('_', ' ').title(), region['text'], height=180, key='book_draft_' + region['region'])
            export = {
                'source': draft['source'],
                'source_url': draft['source_url'],
                'engine': draft['engine'],
                'status': 'user-editable unverified draft',
                'original_ocr': draft['regions'],
                'edited_columns': edited
            }
            st.download_button('Download edited printed-source draft', json.dumps(export, ensure_ascii=False, indent=2), 'printed_source_review.json', 'application/json')
            st.caption('Edits remain in this session until downloaded. Stone annotations and evaluation results are unchanged.')
    for issue in document['unresolved']:
        st.write('- ' + issue)
    st.caption('HS024 is a validation image. Published answers must not be used to retune the recognizer and then claim independent accuracy on this stone.')
    st.download_button('Download source comparison and uncertainties', reference.read_bytes(), 'HS024_reference_comparison.json', 'application/json')

elif page == 'Experiment results':
    st.subheader('Recorded experiments')
    st.write('Recognition accuracy counts exact agreement with raw source labels. It is not project completion.')
    for title, path in [
        ('Automatic localization plus recognition - hero baseline', 'pipeline_study/summary.json'),
        ('Automatic localization plus recognition - broader model', 'broad_pipeline_study/summary.json'),
        ('Original versus mask inputs, unchanged classifier', 'full_binarizer/recognition_comparison.json'),
        ('Matched training experiment', 'matched_mask_study/summary.json'),
        ('Broader cleaned training experiment', 'broad_clean_study/summary.json'),
        ('Learned CNN experiment', 'cnn_study/summary.json'),
        ('Broader CNN development test', 'broad_cnn_study/summary.json'),
        ('Component grouping test', 'component_grouping_study/summary.json'),
        ('Ranked review suggestions', 'review_alternatives_study/summary.json'),
        ('Frozen pretrained features', 'transfer_study/summary.json')
    ]:
        p = ROOT / 'outputs' / path
        if p.exists():
            st.write('**' + title + '**')
            st.json(json.loads(p.read_text(encoding='utf-8')))
    st.warning('Validation has been reused. Pretrained-binarizer training overlap is incompletely known. These are diagnostic results, not a fresh independent benchmark.')

elif page == 'Saved analyses':
    records = history()
    # 2. Empty state when no saved analyses exist
    if not records:
        st.info('Upload an image to begin. No saved analyses are currently recorded.')
    else:
        selected = st.selectbox('Saved analysis', records, format_func=lambda r: r['created'] + ' - ' + r['filename'])
        if Path(selected['mask_path']).is_file():
            st.image(selected['mask_path'], caption='Saved predicted mask')
        else:
            st.warning('The saved mask file is missing. The analysis record is still available.')
        st.json({k: v for k, v in selected.items() if k not in ['image_path', 'mask_path']})
        saved = reviews(selected['id'])
        batch_path = DATA / selected['id'] / 'automatic_regions.json'
        if batch_path.exists():
            st.download_button('Download saved automatic region predictions', batch_path.read_bytes(), 'automatic_regions.json', 'application/json')
        st.subheader('Saved character reviews')
        if saved:
            st.dataframe(saved, hide_index=True)
        else:
            st.info('No character reviews saved for this analysis.')
        if ADVANCED_MODE:
            st.download_button('Export analysis and reviews', json.dumps(review_export(selected['id']), ensure_ascii=False, indent=2), 'inscriplens_reviews.json', 'application/json')

elif page == 'Setup status':
    st.subheader('Local setup status')
    paths = enhancement_files + [
        'outputs/broad_clean_study/mask_svm_bundle.joblib',
        'outputs/full_binarizer/HS027_original.png',
        'outputs/matched_mask_study/mask_svm_bundle.joblib',
        'work/hero_pilot/manifest.json',
        'outputs/full_binarizer/recognition_predictions.json'
    ]
    st.dataframe([{'Asset': p, 'Status': 'Present' if (ROOT / p).is_file() else 'Missing'} for p in paths], hide_index=True)
    st.caption('Presence checks do not verify installed Python packages or model compatibility. Actual enhancement tests those at runtime.')
    st.markdown('[Setup instructions and runtime-pack guidance](https://github.com/Nikhilnr46/InscripLens/blob/main/COLLABORATOR_HANDOVER.md)')
    st.code('git pull --ff-only origin main', language='powershell')
    st.write('Pulling updates code and reports. It does not download ignored datasets, model weights or virtual environments.')

# Dedicated Credits page in the sidebar with full attribution
elif page == 'Credits':
    page_header('Project Credits & Attribution', 'Licence attribution, model provenance, and reused research')
    with card('About InscripLens: project work and reused components'):
        st.write('Project implementation: dataset filtering and provenance records, controlled model comparisons, candidate-region detection, review workflow, downloads and local analysis history. These are engineering and evaluation contributions; no new OCR architecture is claimed.')
        st.write('Reused research: the Shilalekhya pretrained model performs enhancement. EpiSAM supplies public images and annotations. Standard libraries provide classifier and interface components. Reuse is credited below; source models and data were not created by this project.')
    st.divider()
    st.write('**External components and datasets:**')
    st.caption('Enhancement: Shilalekhya, IIIT Hyderabad (MIT code). Public EpiSAM images/checkpoints: CC BY-SA 4.0; imagery acknowledged to The Mythic Society Bengaluru. Dataset previews are derived works. See project attribution in the application README.')
    st.markdown('[EpiSAM source](https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset) · [Shilalekhya code](https://github.com/ihdia/shilalekhya-binarization) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)')

else:
    st.info('Select a workspace from the sidebar.')
