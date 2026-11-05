from pathlib import Path
import re

app_path = Path("frontend/src/App.jsx")
text = app_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Add import for kannadaConverter
imp_line = "import { formatDisplayLabel, toKannada, toModernKannada } from './utils/kannadaConverter';"
if "kannadaConverter" not in text:
    target = "import { initSiteInteractions } from './utils/interactions.ts';"
    assert target in text, "import target not found"
    text = text.replace(target, f"{target}\n{imp_line}", 1)

# 2. Add states for scriptMode, modernLetters, cropError
state_block = """  // Script display mode (Kannada default vs Roman), saved in localStorage with try/catch
  const [scriptMode, setScriptMode] = useState(() => {
    try {
      return localStorage.getItem('inscriplens_script_mode') || 'kannada';
    } catch {
      return 'kannada';
    }
  });

  const [modernLetters, setModernLetters] = useState(() => {
    try {
      return localStorage.getItem('inscriplens_modern_letters') === 'true';
    } catch {
      return false;
    }
  });

  const [cropError, setCropError] = useState(null);

  useEffect(() => {
    try {
      localStorage.setItem('inscriplens_script_mode', scriptMode);
    } catch {}
  }, [scriptMode]);

  useEffect(() => {
    try {
      localStorage.setItem('inscriplens_modern_letters', String(modernLetters));
    } catch {}
  }, [modernLetters]);
"""

if "inscriplens_script_mode" not in text:
    state_target = "  const [highAccuracy, setHighAccuracy] = useState(false);"
    assert state_target in text, "state_target not found"
    text = text.replace(state_target, f"{state_target}\n{state_block}", 1)

# 3. Update loadDemoStone & handleFileUpload to trigger predictBox(0) if not tiny
load_demo_old = """      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);"""

load_demo_new = """      const data = await res.json();
      setAnalysis(data);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      setCropError(null);
      fetchReviews(data.id);
      if (data.boxes && data.boxes.length > 0) {
        setSelectedBoxIndex(0);
        predictBox(0, data.id, data.boxes[0]);
      } else {
        setSelectedBoxIndex(null);
      }"""

assert load_demo_old in text, "load_demo_old not found"
text = text.replace(load_demo_old, load_demo_new, 1)

handle_upload_old = """      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);"""

handle_upload_new = """      const data = await res.json();
      setAnalysis(data);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      setCropError(null);
      fetchReviews(data.id);
      if (data.boxes && data.boxes.length > 0) {
        setSelectedBoxIndex(0);
        predictBox(0, data.id, data.boxes[0]);
      } else {
        setSelectedBoxIndex(null);
      }"""

assert handle_upload_old in text, "handle_upload_old not found"
text = text.replace(handle_upload_old, handle_upload_new, 1)

# 4. Update predictBox implementation
predict_box_old = """// Predict selected crop region
  const predictBox = async (boxIndex) => {
    if (!analysis || boxIndex === null || !analysis.boxes[boxIndex]) return;
    const bbox = analysis.boxes[boxIndex];
    setSelectedBoxIndex(boxIndex);

    // Immediately clear stale cropPrediction if candidate index differs
    setCropPrediction(prev => (prev?.candidateIndex === boxIndex ? prev : null));
    setPredictingCrop(true);

    const requestId = ++predictRequestIdRef.current;

    try {
      const res = await fetch('/api/predict-crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: analysis.id, bbox })
      });

      // Ignore response if this is not the latest request
      if (requestId !== predictRequestIdRef.current) {
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Character prediction could not be completed.');
      }
      const data = await res.json();

      // Ensure response is still current before setting state
      if (requestId === predictRequestIdRef.current) {
        setCropPrediction({ ...data, candidateIndex: boxIndex });
        setPredictionCache(prev => ({
          ...prev,
          [boxIndex]: {
            prediction: data.prediction,
            confidence: data.confidence,
            uncertain: data.uncertain,
            models_agree: data.models_agree
          }
        }));
      }
    } catch (err) {
      if (requestId === predictRequestIdRef.current) {
        showError(err.message);
      }
    } finally {
      if (requestId === predictRequestIdRef.current) {
        setPredictingCrop(false);
      }
    }
  };"""

predict_box_new = """  // Predict selected crop region with tiny check and error recording
  const predictBox = async (boxIndex, overrideAnalysisId, overrideBbox) => {
    const currentAnalysisId = overrideAnalysisId || analysis?.id;
    const boxes = analysis?.boxes;
    const bbox = overrideBbox || (boxes && boxIndex !== null ? boxes[boxIndex] : null);
    if (!currentAnalysisId || boxIndex === null || !bbox) return;

    setSelectedBoxIndex(boxIndex);

    const w = bbox[2] - bbox[0];
    const h = bbox[3] - bbox[1];
    if (w < 10 || h < 10) {
      setCropPrediction(null);
      setPredictingCrop(false);
      setCropError(null);
      return;
    }

    setCropPrediction(prev => (prev?.candidateIndex === boxIndex ? prev : null));
    setPredictingCrop(true);
    setCropError(null);

    const requestId = ++predictRequestIdRef.current;

    try {
      const res = await fetch('/api/predict-crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: currentAnalysisId, bbox })
      });

      if (requestId !== predictRequestIdRef.current) return;

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Character prediction could not be completed.');
      }
      const data = await res.json();

      if (requestId === predictRequestIdRef.current) {
        setCropPrediction({ ...data, candidateIndex: boxIndex });
        setPredictionCache(prev => ({
          ...prev,
          [boxIndex]: {
            prediction: data.prediction,
            confidence: data.confidence,
            uncertain: data.uncertain,
            models_agree: data.models_agree
          }
        }));
      }
    } catch (err) {
      if (requestId === predictRequestIdRef.current) {
        setCropError(err.message || 'Crop preview could not be loaded.');
      }
    } finally {
      if (requestId === predictRequestIdRef.current) {
        setPredictingCrop(false);
      }
    }
  };"""

assert predict_box_old in text, "predict_box_old not found"
text = text.replace(predict_box_old, predict_box_new, 1)

# 5. Add Script Switch Control to Canvas Toolbar
toolbar_target = """                          <a
                            href={analysis.mask_url}
                            download={`mask_${analysis.id}.png`}
                            className="tool-btn"
                            title="Download enhanced binary mask image"
                            style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Download size={12} /> Mask
                          </a>
                        </div>"""

script_switch_code = """                          <a
                            href={analysis.mask_url}
                            download={`mask_${analysis.id}.png`}
                            className="tool-btn"
                            title="Download enhanced binary mask image"
                            style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Download size={12} /> Mask
                          </a>
                        </div>

                        <div style={{ width: '1px', height: '16px', backgroundColor: '#2A2A30' }} />

                        {/* Script Switch: Kannada / Roman */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.72rem', color: '#A8A29A' }}>Script:</span>
                          <div style={{ display: 'flex', alignItems: 'center', backgroundColor: '#1A1A1E', borderRadius: '5px', padding: '2px', border: '1px solid #28282F' }}>
                            <button
                              type="button"
                              onClick={() => setScriptMode('kannada')}
                              title="Display character labels in Kannada script"
                              style={{
                                padding: '2px 8px',
                                fontSize: '0.74rem',
                                border: 'none',
                                borderRadius: '3px',
                                backgroundColor: scriptMode === 'kannada' ? '#C9A66B' : 'transparent',
                                color: scriptMode === 'kannada' ? '#121214' : '#A8A29A',
                                fontWeight: scriptMode === 'kannada' ? '600' : '400',
                                cursor: 'pointer',
                                fontFamily: "'Noto Sans Kannada', sans-serif"
                              }}
                            >
                              ಕನ್ನಡ
                            </button>
                            <button
                              type="button"
                              onClick={() => setScriptMode('roman')}
                              title="Display character labels in Roman transliteration"
                              style={{
                                padding: '2px 8px',
                                fontSize: '0.74rem',
                                border: 'none',
                                borderRadius: '3px',
                                backgroundColor: scriptMode === 'roman' ? '#C9A66B' : 'transparent',
                                color: scriptMode === 'roman' ? '#121214' : '#A8A29A',
                                fontWeight: scriptMode === 'roman' ? '600' : '400',
                                cursor: 'pointer'
                              }}
                            >
                              Roman
                            </button>
                          </div>

                          {scriptMode === 'kannada' && (
                            <div
                              className="toggle-wrapper"
                              onClick={() => setModernLetters(!modernLetters)}
                              role="switch"
                              aria-checked={modernLetters}
                              tabIndex={0}
                              title="Replace archaic ಱ and ೞ with modern letters ರ and ಳ (marked with lossy tag)"
                              style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                              onKeyDown={(e) => {
                                if (e.key === ' ' || e.key === 'Enter') {
                                  e.preventDefault();
                                  setModernLetters(!modernLetters);
                                }
                              }}
                            >
                              <div className={`toggle-switch ${modernLetters ? 'active' : ''}`} style={{ width: '28px', height: '16px' }}>
                                <div className="toggle-thumb" style={{ width: '10px', height: '10px' }} />
                              </div>
                              <span style={{ fontSize: '0.72rem', color: modernLetters ? '#EDEDEC' : '#A8A29A' }}>
                                Modern letters
                              </span>
                            </div>
                          )}
                        </div>"""

assert toolbar_target in text, "toolbar_target not found"
text = text.replace(toolbar_target, script_switch_code, 1)

# 6. Update Inspector Crop Box to handle tiny regions & cropError
crop_box_old = """                          <div className="inspector-crop-box">
                            {isMatchingPrediction && cropPrediction.crop_url ? (
                              <img
                                src={cropPrediction.crop_url}
                                alt={`Magnified candidate region #${selectedBoxIndex + 1} predicted as transliteration ${cropPrediction.prediction}`}
                                style={{
                                  maxHeight: '160px',
                                  maxWidth: '160px',
                                  width: 'auto',
                                  height: 'auto',
                                  objectFit: 'contain',
                                  imageRendering: 'pixelated',
                                  filter: 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.7))'
                                }}
                              />
                            ) : (
                              <div className="skeleton-pulse" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#7E7A75' }}>
                                <div style={{ width: '56px', height: '56px', borderRadius: '6px', backgroundColor: 'var(--bg-elevated)', border: '1px dashed var(--border-subtle)' }} />
                                <span style={{ fontSize: '0.7rem' }}>Loading crop...</span>
                              </div>
                            )}
                            <span style={{
                              position: 'absolute',
                              bottom: '8px',
                              right: '8px',
                              fontSize: '0.68rem',
                              color: '#7E7A75',
                              backgroundColor: 'rgba(18, 18, 20, 0.85)',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              border: '1px solid #28282F'
                            }}>
                              {selectedBoxW} x {selectedBoxH} px
                            </span>
                          </div>"""

crop_box_new = """                          <div className="inspector-crop-box">
                            {isSelectedTiny ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', color: '#A8A29A', textAlign: 'center' }}>
                                <span className="tiny-tag" style={{ fontSize: '0.72rem', padding: '2px 8px', marginBottom: '6px' }}>
                                  Too small to read
                                </span>
                                <span style={{ fontSize: '0.7rem', color: '#7E7A75' }}>
                                  Region is {selectedBoxW} &times; {selectedBoxH} px (&lt; 10&times;10 px limit)
                                </span>
                              </div>
                            ) : cropError ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', color: '#D97706', textAlign: 'center' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '4px' }}>
                                  Crop preview unavailable
                                </span>
                                <span style={{ fontSize: '0.68rem', color: '#7E7A75' }}>
                                  {cropError}
                                </span>
                              </div>
                            ) : isMatchingPrediction && cropPrediction.crop_url ? (
                              <img
                                src={cropPrediction.crop_url}
                                alt={`Magnified candidate region #${selectedBoxIndex + 1} predicted as transliteration ${cropPrediction.prediction}`}
                                style={{
                                  maxHeight: '160px',
                                  maxWidth: '160px',
                                  width: 'auto',
                                  height: 'auto',
                                  objectFit: 'contain',
                                  imageRendering: 'pixelated',
                                  filter: 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.7))'
                                }}
                              />
                            ) : predictingCrop ? (
                              <div className="skeleton-pulse" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#7E7A75' }}>
                                <div style={{ width: '56px', height: '56px', borderRadius: '6px', backgroundColor: 'var(--bg-elevated)', border: '1px dashed var(--border-subtle)' }} />
                                <span style={{ fontSize: '0.7rem' }}>Loading crop...</span>
                              </div>
                            ) : (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px', color: '#7E7A75' }}>
                                <div style={{ width: '56px', height: '56px', borderRadius: '6px', backgroundColor: 'var(--bg-elevated)', border: '1px dashed var(--border-subtle)' }} />
                                <span style={{ fontSize: '0.7rem' }}>Select region to inspect</span>
                              </div>
                            )}
                            <span style={{
                              position: 'absolute',
                              bottom: '8px',
                              right: '8px',
                              fontSize: '0.68rem',
                              color: '#7E7A75',
                              backgroundColor: 'rgba(18, 18, 20, 0.85)',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              border: '1px solid #28282F'
                            }}>
                              {selectedBoxW} x {selectedBoxH} px
                            </span>
                          </div>"""

assert crop_box_old in text, "crop_box_old not found"
text = text.replace(crop_box_old, crop_box_new, 1)

# 7. Update Predicted Source Transliteration to large Kannada + Roman + handle tiny
pred_section_old = """                          <div style={{ marginTop: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                              <div style={{ fontSize: '0.72rem', color: '#A8A29A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                                Predicted Source Transliteration
                              </div>
                              {cropPrediction?.uncertain && (
                                <span className="uncertain-tag">
                                  Uncertain
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: cropPrediction?.uncertain ? '#D97706' : '#C9A66B', letterSpacing: '-0.01em', lineHeight: 1.2, minHeight: '2.1rem' }}>
                              {isMatchingPrediction ? (
                                cropPrediction.prediction
                              ) : knownCandidateLabel ? (
                                knownCandidateLabel
                              ) : (
                                <span className="skeleton-pulse" style={{ display: 'inline-block', width: '80px', height: '1.8rem', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', verticalAlign: 'middle' }} />
                              )}
                            </div>

                            {/* Subtle Calibrated Confidence Bar in Inspector */}
                            {cropPrediction?.confidence != null && (
                              <div style={{ marginTop: '6px', marginBottom: '6px' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#7E7A75', marginBottom: '2px' }}>
                                  <span>Confidence</span>
                                  <span style={{ color: cropPrediction.uncertain ? '#D97706' : '#C9A66B', fontWeight: '600' }}>
                                    {Math.round(cropPrediction.confidence * 100)}%
                                  </span>
                                </div>
                                <div className="confidence-bar-subtle" style={{ height: '4px' }}>
                                  <div
                                    className="confidence-bar-subtle-fill"
                                    style={{
                                      width: `${Math.round(cropPrediction.confidence * 100)}%`,
                                      backgroundColor: cropPrediction.uncertain ? '#D97706' : '#C9A66B'
                                    }}
                                  />
                                </div>
                              </div>
                            )}

                            <div style={{ fontSize: '0.75rem', color: '#7E7A75', marginTop: '2px', display: 'flex', justifyContent: 'space-between' }}>
                              <span>Model: Calibrated recognizer</span>
                              {cropPrediction?.models_agree != null && (
                                <span style={{ color: cropPrediction.models_agree ? '#76D876' : '#A8A29A', fontSize: '0.7rem' }}>
                                  {cropPrediction.models_agree ? 'Models agree' : 'Models disagree'}
                                </span>
                              )}
                            </div>
                          </div>"""

pred_section_new = """                          {(() => {
                            const isSelectedTiny = selectedBoxW < 10 || selectedBoxH < 10;
                            const rawPred = isMatchingPrediction ? cropPrediction.prediction : knownCandidateLabel;
                            const predDisp = formatDisplayLabel(rawPred, scriptMode, modernLetters);

                            return (
                              <div style={{ marginTop: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                                  <div style={{ fontSize: '0.72rem', color: '#A8A29A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                                    Predicted Character
                                  </div>
                                  {cropPrediction?.uncertain && !isSelectedTiny && (
                                    <span className="uncertain-tag">
                                      Uncertain
                                    </span>
                                  )}
                                  {isSelectedTiny && (
                                    <span className="tiny-tag">
                                      Too small to read
                                    </span>
                                  )}
                                </div>

                                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', minHeight: '2.4rem', marginTop: '4px' }}>
                                  {isSelectedTiny ? (
                                    <span style={{ fontSize: '1rem', color: '#7E7A75', fontStyle: 'italic' }}>
                                      Too small to read (&lt; 10&times;10 px)
                                    </span>
                                  ) : rawPred ? (
                                    <>
                                      <span
                                        style={{
                                          fontFamily: (scriptMode === 'kannada' && !predDisp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit',
                                          fontSize: (scriptMode === 'kannada' && !predDisp.isUnmapped) ? '2.4rem' : '1.8rem',
                                          fontWeight: '700',
                                          color: cropPrediction?.uncertain ? '#D97706' : '#C9A66B',
                                          lineHeight: 1
                                        }}
                                      >
                                        {predDisp.primary}
                                      </span>
                                      {predDisp.isLossy && <span className="lossy-tag">lossy</span>}
                                      {predDisp.isUnmapped && <span className="roman-marker-tag">Roman</span>}
                                      {scriptMode === 'kannada' && predDisp.secondary && (
                                        <span style={{ fontSize: '1.05rem', color: '#A8A29A', fontWeight: '500' }}>
                                          ({predDisp.secondary})
                                        </span>
                                      )}
                                    </>
                                  ) : (
                                    <span className="skeleton-pulse" style={{ display: 'inline-block', width: '80px', height: '1.8rem', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', verticalAlign: 'middle' }} />
                                  )}
                                </div>

                                {/* Subtle Calibrated Confidence Bar in Inspector - ONLY when NOT tiny */}
                                {!isSelectedTiny && cropPrediction?.confidence != null && (
                                  <div style={{ marginTop: '6px', marginBottom: '6px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: '#7E7A75', marginBottom: '2px' }}>
                                      <span>Confidence</span>
                                      <span style={{ color: cropPrediction.uncertain ? '#D97706' : '#C9A66B', fontWeight: '600' }}>
                                        {Math.round(cropPrediction.confidence * 100)}%
                                      </span>
                                    </div>
                                    <div className="confidence-bar-subtle" style={{ height: '4px' }}>
                                      <div
                                        className="confidence-bar-subtle-fill"
                                        style={{
                                          width: `${Math.round(cropPrediction.confidence * 100)}%`,
                                          backgroundColor: cropPrediction.uncertain ? '#D97706' : '#C9A66B'
                                        }}
                                      />
                                    </div>
                                  </div>
                                )}

                                <div style={{ fontSize: '0.75rem', color: '#7E7A75', marginTop: '2px', display: 'flex', justifyContent: 'space-between' }}>
                                  <span>Model: Calibrated recognizer</span>
                                  {cropPrediction?.models_agree != null && !isSelectedTiny && (
                                    <span style={{ color: cropPrediction.models_agree ? '#76D876' : '#A8A29A', fontSize: '0.7rem' }}>
                                      {cropPrediction.models_agree ? 'Models agree' : 'Models disagree'}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })()}"""

assert pred_section_old in text, "pred_section_old not found"
text = text.replace(pred_section_old, pred_section_new, 1)

# 8. Update Alternatives chips to show Kannada with Roman tooltip
alts_old = """                          <div className="alt-chips-container">
                            {isMatchingPrediction && Array.isArray(cropPrediction.alternatives) ? (
                              cropPrediction.alternatives.map((alt, idx) => {
                                const labelStr = typeof alt === 'object' ? alt.label : alt;
                                const isChosen = suggestion === labelStr;
                                const confVal = typeof alt === 'object' && alt.confidence != null
                                  ? alt.confidence
                                  : (cropPrediction.confidence_scores?.[idx] ?? null);

                                return (
                                  <div
                                    key={idx}
                                    className={`alt-chip ${isChosen ? 'selected' : ''}`}
                                    onClick={() => setSuggestion(labelStr)}
                                    title={`Click to select '${labelStr}' as suggestion`}
                                  >
                                    <span>{labelStr}</span>
                                    {confVal != null && (
                                      <div className="alt-confidence-track">
                                        <div
                                          className="alt-confidence-fill"
                                          style={{ width: `${Math.round(confVal * 100)}%` }}
                                        />
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : ("""

alts_new = """                          <div className="alt-chips-container">
                            {isMatchingPrediction && Array.isArray(cropPrediction.alternatives) ? (
                              cropPrediction.alternatives.map((alt, idx) => {
                                const labelStr = typeof alt === 'object' ? alt.label : alt;
                                const isChosen = suggestion === labelStr;
                                const confVal = typeof alt === 'object' && alt.confidence != null
                                  ? alt.confidence
                                  : (cropPrediction.confidence_scores?.[idx] ?? null);
                                const altDisp = formatDisplayLabel(labelStr, scriptMode, modernLetters);

                                return (
                                  <div
                                    key={idx}
                                    className={`alt-chip ${isChosen ? 'selected' : ''}`}
                                    onClick={() => setSuggestion(labelStr)}
                                    title={scriptMode === 'kannada' ? `${labelStr} (Click to adopt '${labelStr}' as suggestion)` : `Click to select '${labelStr}' as suggestion`}
                                  >
                                    <span style={{
                                      fontFamily: (scriptMode === 'kannada' && !altDisp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit',
                                      fontSize: (scriptMode === 'kannada' && !altDisp.isUnmapped) ? '1.15rem' : '0.9rem'
                                    }}>
                                      {altDisp.primary}
                                    </span>
                                    {altDisp.isLossy && <span className="lossy-tag">lossy</span>}
                                    {altDisp.isUnmapped && <span className="roman-marker-tag">Roman</span>}
                                    {confVal != null && (
                                      <div className="alt-confidence-track">
                                        <div
                                          className="alt-confidence-fill"
                                          style={{ width: `${Math.round(confVal * 100)}%` }}
                                        />
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : ("""

assert alts_old in text, "alts_old not found"
text = text.replace(alts_old, alts_new, 1)

# 9. Update Review Form with Live Kannada Preview
form_old = """                            <div style={{ marginBottom: '10px' }}>
                              <label style={{ fontSize: '0.75rem', color: '#A8A29A', display: 'block', marginBottom: '4px' }}>
                                Suggested Correction (optional)
                              </label>
                              <input
                                type="text"
                                value={suggestion}
                                onChange={(e) => setSuggestion(e.target.value)}
                                placeholder="e.g. ko"
                                style={{
                                  width: '100%',
                                  padding: '8px 10px',
                                  borderRadius: '6px',
                                  border: '1px solid #2A2A30',
                                  backgroundColor: '#161619',
                                  color: '#EDEDEC',
                                  fontSize: '0.85rem'
                                }}
                              />
                            </div>"""

form_new = """                            <div style={{ marginBottom: '10px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <label style={{ fontSize: '0.75rem', color: '#A8A29A' }}>
                                  Suggested Correction (Roman transliteration)
                                </label>
                                {suggestion && suggestion.trim() && (
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <span style={{ fontSize: '0.68rem', color: '#A8A29A' }}>Kannada preview:</span>
                                    <span
                                      style={{
                                        fontFamily: "'Noto Sans Kannada', sans-serif",
                                        fontSize: '1.05rem',
                                        fontWeight: '600',
                                        color: '#C9A66B',
                                        backgroundColor: '#1E1E23',
                                        padding: '1px 6px',
                                        borderRadius: '4px',
                                        border: '1px solid #2A2A30',
                                        lineHeight: 1.2
                                      }}
                                    >
                                      {formatDisplayLabel(suggestion.trim(), 'kannada', modernLetters).primary}
                                    </span>
                                  </div>
                                )}
                              </div>
                              <input
                                type="text"
                                value={suggestion}
                                onChange={(e) => setSuggestion(e.target.value)}
                                placeholder="e.g. ko, ya, sva, śrī"
                                style={{
                                  width: '100%',
                                  padding: '8px 10px',
                                  borderRadius: '6px',
                                  border: '1px solid #2A2A30',
                                  backgroundColor: '#161619',
                                  color: '#EDEDEC',
                                  fontSize: '0.85rem'
                                }}
                              />
                            </div>"""

assert form_old in text, "form_old not found"
text = text.replace(form_old, form_new, 1)

# 10. Update Review Card to show Kannada + Roman
rev_card_old = """                              {currentSelectedReview.suggested_label && (
                                <div style={{ fontSize: '0.82rem', color: '#EDEDEC', marginBottom: '4px' }}>
                                  <span style={{ color: '#A8A29A' }}>Corrected Label: </span>
                                  <strong style={{ color: '#64B4F0', fontSize: '1rem' }}>{currentSelectedReview.suggested_label}</strong>
                                </div>
                              )}"""

rev_card_new = """                              {currentSelectedReview.suggested_label && (() => {
                                const revDisp = formatDisplayLabel(currentSelectedReview.suggested_label, scriptMode, modernLetters);
                                return (
                                  <div style={{ fontSize: '0.82rem', color: '#EDEDEC', marginBottom: '4px' }}>
                                    <span style={{ color: '#A8A29A' }}>Corrected Label: </span>
                                    <strong style={{ color: '#64B4F0', fontSize: '1.1rem', fontFamily: (scriptMode === 'kannada' && !revDisp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit' }}>
                                      {revDisp.primary}
                                    </strong>
                                    {scriptMode === 'kannada' && revDisp.secondary && (
                                      <span style={{ color: '#A8A29A', fontSize: '0.82rem', marginLeft: '6px' }}>
                                        ({revDisp.secondary})
                                      </span>
                                    )}
                                  </div>
                                );
                              })()}"""

assert rev_card_old in text, "rev_card_old not found"
text = text.replace(rev_card_old, rev_card_new, 1)

# 11. Update Candidate Chips in gallery strip
chips_old = ''

chips_new = """                          {(() => {
                            const chipDisp = formatDisplayLabel(cand.label, scriptMode, modernLetters);

                            if (cand.isTiny) {
                              return (
                                <div style={{ margin: '6px 0', minHeight: '30px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                  <span className="tiny-tag">Too small to read</span>
                                </div>
                              );
                            }

                            return (
                              <>
                                <div style={{ margin: '2px 0', minHeight: '34px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                                  <div
                                    className="glyph-chip-label"
                                    style={{
                                      fontFamily: (scriptMode === 'kannada' && !chipDisp.isUnmapped) ? "'Noto Sans Kannada', sans-serif" : 'inherit',
                                      fontSize: (scriptMode === 'kannada' && !chipDisp.isUnmapped) ? '1.25rem' : '0.95rem',
                                      lineHeight: 1.1,
                                      color: isSelected
                                        ? '#C9A66B'
                                        : cand.status === 'corrected'
                                        ? '#64B4F0'
                                        : cand.status === 'reviewed'
                                        ? '#76D876'
                                        : cand.status === 'predicted'
                                        ? (cand.uncertain ? '#A8A29A' : '#EDEDEC')
                                        : '#6A6A72'
                                    }}
                                  >
                                    {chipDisp.primary || '·'}
                                    {chipDisp.isLossy && <span className="lossy-tag">lossy</span>}
                                    {chipDisp.isUnmapped && <span className="roman-marker-tag">Roman</span>}
                                  </div>
                                  {scriptMode === 'kannada' && chipDisp.secondary && (
                                    <div style={{ fontSize: '0.62rem', color: '#A8A29A', lineHeight: 1 }}>
                                      {chipDisp.secondary}
                                    </div>
                                  )}
                                </div>

                                {/* Subtle Confidence Bar on Chip - only shown for non-tiny */}
                                {cand.confidence != null && (
                                  <div className="confidence-bar-subtle">
                                    <div
                                      className="confidence-bar-subtle-fill"
                                      style={{
                                        width: `${Math.round(cand.confidence * 100)}%`,
                                        backgroundColor: cand.uncertain ? '#D97706' : '#C9A66B'
                                      }}
                                    />
                                  </div>
                                )}
                              </>
                            );
                          })()}"""

assert chips_old in text, "chips_old not found"
text = text.replace(chips_old, chips_new, 1)

# 12. Update History Row to show reviews with both Roman and Kannada text
hist_view_old = """                      {item.fallback_note && (
                        <div style={{ fontSize: '0.72rem', color: '#D97706', marginTop: '2px' }}>
                          {item.fallback_note}
                        </div>
                      )}
                    </div>"""

hist_view_new = """                      {item.fallback_note && (
                        <div style={{ fontSize: '0.72rem', color: '#D97706', marginTop: '2px' }}>
                          {item.fallback_note}
                        </div>
                      )}
                      {item.reviews && item.reviews.length > 0 && (
                        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.72rem', color: '#A8A29A', fontWeight: '500' }}>
                            Reviews ({item.reviews.length}):
                          </span>
                          {item.reviews.slice(0, 5).map((rev, rIdx) => {
                            const pDisp = formatDisplayLabel(rev.prediction, scriptMode, modernLetters);
                            const sDisp = rev.suggested_label ? formatDisplayLabel(rev.suggested_label, scriptMode, modernLetters) : null;
                            return (
                              <span
                                key={rIdx}
                                className="pill pill-neutral"
                                style={{ fontSize: '0.7rem', padding: '2px 6px' }}
                              >
                                {sDisp ? (
                                  <>
                                    <span style={{ fontFamily: "'Noto Sans Kannada', sans-serif" }}>{sDisp.primary}</span> ({rev.suggested_label})
                                  </>
                                ) : (
                                  <>
                                    <span style={{ fontFamily: "'Noto Sans Kannada', sans-serif" }}>{pDisp.primary}</span> ({rev.prediction})
                                  </>
                                )}
                              </span>
                            );
                          })}
                          {item.reviews.length > 5 && (
                            <span style={{ fontSize: '0.68rem', color: '#7E7A75' }}>
                              +{item.reviews.length - 5} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>"""

assert hist_view_old in text, "hist_view_old not found"
text = text.replace(hist_view_old, hist_view_new, 1)

with open(app_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)
print("Updated frontend/src/App.jsx successfully")
