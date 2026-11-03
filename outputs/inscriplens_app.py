"""Local research application. Run: python -m streamlit run outputs/inscriplens_app.py"""
from pathlib import Path
from types import SimpleNamespace
import hashlib, io, json, subprocess
import streamlit as st
from PIL import Image, ImageOps
import joblib
from run_character_benchmark import features
from app_backend import analyse,history,save_review,reviews,review_export
from segment_candidates import candidates,overlay
from recognize_regions import recognize

ROOT=Path(__file__).resolve().parent.parent
MASK_MODELS=[ROOT/'outputs/broad_clean_study/mask_svm_bundle.joblib',ROOT/'outputs/matched_mask_study/mask_svm_bundle.joblib']
CLEAN_MODEL=next((p for p in MASK_MODELS if p.is_file()),MASK_MODELS[-1])
DATA=ROOT/'work/app_data';DATA.mkdir(parents=True,exist_ok=True)
st.set_page_config(page_title='InscripLens',layout='wide')
st.title('InscripLens')
st.write('Historical Kannada inscription image analysis')
st.info('Research prototype: enhancement works; character recognition is experimental. Published/source labels are references, not automatic readings. Modern Kannada conversion and English translation are not available.')
page=st.sidebar.radio('Workspace',['Analyse an image','Dataset explorer','Experiment results','Saved analyses','Setup status'])
st.sidebar.caption('Images and analysis history stay on this computer. No cloud OCR service is used.')
enhancement_files=['work/binarizer_env/Scripts/python.exe','work/shilalekhya/Unet/model.py','work/shilalekhya/binarizer.pth']
missing_enhancement=[p for p in enhancement_files if not (ROOT/p).is_file()]
def setup_message(message):
    st.warning(message)
    st.markdown('Open **Setup status** and follow the [collaborator setup guide](https://github.com/Nikhilnr46/InscripLens/blob/main/COLLABORATOR_HANDOVER.md). Runtime assets must be extracted into the repository root.')

if page=='Analyse an image':
    upload=st.file_uploader('Upload a stone image',type=['png','jpg','jpeg'])
    sample=ROOT/'outputs/full_binarizer/HS027_original.png'
    if not sample.is_file():setup_message('The optional demonstration image is not installed. You can still upload your own image.')
    if st.checkbox('Use the public Nagavara demonstration image',disabled=not sample.is_file()):
        upload=SimpleNamespace(name='Nagavara_public_demo.png',getvalue=sample.read_bytes)
    if upload:
        try:
            raw=upload.getvalue();digest=hashlib.sha256(raw).hexdigest()
            image=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
            if image.width*image.height>20_000_000:raise ValueError('Please use an image below 20 megapixels.')
        except Exception as exc:
            st.error(f'Cannot open image: {exc}');st.stop()
        if st.session_state.get('digest')!=digest:
            st.session_state.digest=digest;st.session_state.pop('run',None);st.session_state.pop('character_prediction',None)
        st.image(image,caption=f'Uploaded original · {image.width} × {image.height}',width=600)
        st.caption('Analysis uses a copy with longest side at most 1600 pixels. Enhancement predicts foreground strokes; it may omit or alter damaged strokes.')
        if missing_enhancement:setup_message('Enhancement runtime is incomplete: '+', '.join(missing_enhancement))
        if st.button('Enhance inscription',type='primary',disabled=bool(missing_enhancement)):
            try:
                with st.spinner('Separating likely inscription strokes from the background…'):
                    record=analyse(raw,upload.name)
                st.session_state.run=record;st.session_state.pop('character_prediction',None)
            except (subprocess.SubprocessError,ValueError,OSError) as exc:
                st.error('Enhancement could not finish. No successful analysis was saved.')
                st.code(str(exc))
        record=st.session_state.get('run')
        if record:
            if not all(Path(record[k]).is_file() for k in ['image_path','mask_path']):
                setup_message('This saved analysis refers to image files that are no longer available. Run enhancement again.');st.stop()
            st.success('Enhancement saved locally.')
            mask=Image.open(record['mask_path']);original=Image.open(record['image_path'])
            left,right=st.columns(2);left.image(original,caption='Analysis input');right.image(mask,caption='Predicted foreground mask')
            st.download_button('Download predicted mask',Path(record['mask_path']).read_bytes(),'inscriplens_mask.png','image/png')
            st.download_button('Download analysis record',json.dumps(record,indent=2),'inscriplens_analysis.json','application/json')
            st.subheader('Experimental character recognition')
            if CLEAN_MODEL.is_file():st.caption('Recognizer: '+('broader cleaned-data model' if CLEAN_MODEL==MASK_MODELS[0] else 'hero-only baseline'))
            boxes=candidates(mask)
            st.write(f'Automatic connected-component detector found {len(boxes)} candidate regions. These may split a letter or combine several; their order is not a verified reading order.')
            st.image(overlay(original,boxes),caption='Automatic candidate boxes',width=600)
            st.download_button('Download candidate boxes',json.dumps({'boxes_xyxy':boxes,'verified':False,'method':'connected_components'}),'candidate_boxes.json')
            batch_model=CLEAN_MODEL
            if st.button('Predict all detected regions',disabled=not batch_model.is_file()):
                with st.spinner('Predicting detected candidate labels…'):
                    batch=recognize(mask,joblib.load(batch_model))
                payload={'run_id':record['id'],'method':'predicted_mask_components_mask_svm','model_sha256':hashlib.sha256(batch_model.read_bytes()).hexdigest(),'verified_transcription':False,'reading_order_verified':False,'regions':batch}
                path=DATA/record['id']/'automatic_regions.json';path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
            batch_path=DATA/record['id']/'automatic_regions.json'
            if batch_path.exists():
                payload=json.loads(batch_path.read_text(encoding='utf-8'))
                st.caption('Automatic region predictions: no reference boxes supplied. These labels are not a verified sentence or reading order.')
                st.dataframe(payload['regions'],hide_index=True)
                st.download_button('Download automatic region predictions',json.dumps(payload,ensure_ascii=False,indent=2),'automatic_regions.json','application/json')
            chosen=st.selectbox('Start from a detected region',range(len(boxes)+1),format_func=lambda i:'Manual rectangle' if i==0 else f'Candidate {i}')
            initial=boxes[chosen-1] if chosen else [0,0,min(original.width,100),min(original.height,100)]
            st.write('Review or adjust the rectangle before predicting. A candidate is not necessarily one complete character.')
            w,h=original.size
            recognizer_available=CLEAN_MODEL.is_file() or (ROOT/'outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib').is_file()
            if not recognizer_available:setup_message('No recognition model is installed. Enhancement and candidate downloads remain available.')
            with st.form('crop'):
                cols=st.columns(4)
                x1=cols[0].number_input('Left',0,w-1,initial[0],key=f'left_{chosen}');y1=cols[1].number_input('Top',0,h-1,initial[1],key=f'top_{chosen}')
                x2=cols[2].number_input('Right',1,w,initial[2],key=f'right_{chosen}');y2=cols[3].number_input('Bottom',1,h,initial[3],key=f'bottom_{chosen}')
                submitted=st.form_submit_button('Predict this character',disabled=not recognizer_available)
            if submitted:
                if x2<=x1 or y2<=y1:st.error('Right and bottom must exceed left and top.')
                else:
                    model_path=CLEAN_MODEL
                    clean=model_path.exists()
                    if not clean:model_path=ROOT/'outputs/training_scope_study/broader_inscriptions_svm_bundle.joblib'
                    crop=(mask if clean else original).crop((x1,y1,x2,y2));path=DATA/record['id']/'character.png';crop.save(path)
                    bundle=joblib.load(model_path);pred=str(bundle['model'].predict([features(path,bundle['preprocessing'])])[0])
                    st.image(crop,caption='Selected model input',width=180)
                    st.write('**Unverified predicted source label:**',pred)
                    st.caption('Raw transliteration label, not a verified Kannada transcription. No calibrated confidence is available.')
                    st.session_state.character_prediction={'run_id':record['id'],'bbox':[int(x1),int(y1),int(x2),int(y2)],'prediction':pred,'model':model_path.name,'model_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest(),'verified':False}
            prediction=st.session_state.get('character_prediction')
            if prediction and prediction['run_id']==record['id']:
                st.write('Latest prediction:',prediction['prediction'],'— rectangle',prediction['bbox'])
                st.download_button('Download character prediction',json.dumps(prediction,ensure_ascii=False,indent=2),'character_prediction.json')
                with st.form('review_'+record['id']):
                    st.write('Save this prediction or add a suggested correction. Suggestions are unverified and are not added to training automatically.')
                    suggestion=st.text_input('Suggested label (optional)')
                    reviewer=st.text_input('Reviewer name or initials (optional)')
                    note=st.text_area('Source or review note (optional)')
                    save=st.form_submit_button('Save review record')
                if save:
                    save_review(record['id'],prediction['bbox'],prediction['prediction'],prediction['model'],prediction['model_sha256'],suggestion,reviewer,note)
                    st.success('Review record saved. The original model prediction is preserved.')
            st.download_button('Export saved reviews',json.dumps(review_export(record['id']),ensure_ascii=False,indent=2),'inscriplens_reviews.json','application/json')

elif page=='Dataset explorer':
    required=['work/hero_pilot/manifest.json','outputs/full_binarizer/recognition_predictions.json']
    missing=[p for p in required if not (ROOT/p).is_file()]
    if missing:setup_message('Dataset explorer assets are missing: '+', '.join(missing));st.stop()
    rows=json.loads((ROOT/'work/hero_pilot/manifest.json').read_text(encoding='utf-8'))
    names={r['image_id']:r['source_name'] for r in rows if r['source_split']=='val'}
    if not names:st.info('The manifest contains no validation images.');st.stop()
    selected=st.selectbox('Validation image',list(names),format_func=lambda x:names[x])
    comparison=ROOT/f'outputs/full_binarizer/{selected}_comparison.png'
    if comparison.is_file():st.image(str(comparison),caption='Original / predicted mask')
    else:setup_message('The comparison image is not installed for this entry. Saved prediction records are shown below.')
    predictions=json.loads((ROOT/'outputs/full_binarizer/recognition_predictions.json').read_text(encoding='utf-8'))
    subset=[r for r in predictions if r['image_id']==selected]
    st.caption('Saved frozen-model experiment. Reference labels and crop boxes come from EpiSAM annotations; they are not independently verified readings.')
    st.dataframe(subset,width='stretch')
    st.download_button('Download displayed comparison',json.dumps(subset,ensure_ascii=False,indent=2),'source_label_comparison.json')

elif page=='Experiment results':
    st.subheader('Recorded experiments')
    st.write('Recognition accuracy counts exact agreement with raw source labels. It is not project completion.')
    for title,path in [('Automatic localization plus recognition — hero baseline','pipeline_study/summary.json'),('Automatic localization plus recognition — broader model','broad_pipeline_study/summary.json'),('Original versus mask inputs, unchanged classifier','full_binarizer/recognition_comparison.json'),('Matched training experiment','matched_mask_study/summary.json'),('Broader cleaned training experiment','broad_clean_study/summary.json'),('Learned CNN experiment','cnn_study/summary.json'),('Frozen pretrained features','transfer_study/summary.json')]:
        p=ROOT/'outputs'/path
        if p.exists():
            st.write('**'+title+'**');st.json(json.loads(p.read_text(encoding='utf-8')))
    st.warning('Validation has been reused. Pretrained-binarizer training overlap is incompletely known. These are diagnostic results, not a fresh independent benchmark.')

elif page=='Saved analyses':
    records=history()
    if not records:st.write('No uploaded images have been analysed yet.')
    else:
        selected=st.selectbox('Saved analysis',records,format_func=lambda r:r['created']+' · '+r['filename'])
        if Path(selected['mask_path']).is_file():st.image(selected['mask_path'],caption='Saved predicted mask')
        else:st.warning('The saved mask file is missing. The analysis record is still available.')
        st.json({k:v for k,v in selected.items() if k not in ['image_path','mask_path']})
        saved=reviews(selected['id'])
        batch_path=DATA/selected['id']/'automatic_regions.json'
        if batch_path.exists():
            st.download_button('Download saved automatic region predictions',batch_path.read_bytes(),'automatic_regions.json','application/json')
        st.subheader('Saved character reviews')
        if saved:st.dataframe(saved,hide_index=True)
        else:st.info('No character reviews saved for this analysis.')
        st.download_button('Export analysis and reviews',json.dumps(review_export(selected['id']),ensure_ascii=False,indent=2),'inscriplens_reviews.json','application/json')

else:
    st.subheader('Local setup status')
    paths=enhancement_files+['outputs/broad_clean_study/mask_svm_bundle.joblib','outputs/full_binarizer/HS027_original.png','outputs/matched_mask_study/mask_svm_bundle.joblib','work/hero_pilot/manifest.json','outputs/full_binarizer/recognition_predictions.json']
    st.dataframe([{'Asset':p,'Status':'Present' if (ROOT/p).is_file() else 'Missing'} for p in paths],hide_index=True)
    st.caption('Presence checks do not verify installed Python packages or model compatibility. Actual enhancement tests those at runtime.')
    st.markdown('[Setup instructions and runtime-pack guidance](https://github.com/Nikhilnr46/InscripLens/blob/main/COLLABORATOR_HANDOVER.md)')
    st.code('git pull --ff-only origin main',language='powershell')
    st.write('Pulling updates code and reports. It does not download ignored datasets, model weights or virtual environments.')

st.divider()
with st.expander('About InscripLens: project work and reused components'):
    st.write('Project implementation: dataset filtering and provenance records, controlled model comparisons, candidate-region detection, review workflow, downloads and local analysis history. These are engineering and evaluation contributions; no new OCR architecture is claimed.')
    st.write('Reused research: the Shilalekhya pretrained model performs enhancement. EpiSAM supplies public images and annotations. Standard libraries provide classifier and interface components. Reuse is credited below; source models and data were not created by this project.')
st.caption('Enhancement: Shilalekhya, IIIT Hyderabad (MIT code). Public EpiSAM images/checkpoints: CC BY-SA 4.0; imagery acknowledged to The Mythic Society Bengaluru. Dataset previews are derived works. See project attribution in the application README.')
st.markdown('[EpiSAM source](https://huggingface.co/datasets/keyfinder08/EpiSAM_Inscriptions_Dataset) · [Shilalekhya code](https://github.com/ihdia/shilalekhya-binarization) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)')
