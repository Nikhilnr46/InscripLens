with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# Part 4: Inspector Transliteration & subtle confidence bar
t4 = """                          <div style={{ marginTop: '8px' }}>
                            <div style={{ fontSize: '0.72rem', color: '#A8A29A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Predicted Source Transliteration
                            </div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#C9A66B', letterSpacing: '-0.01em', lineHeight: 1.2, minHeight: '2.1rem' }}>
                              {isMatchingPrediction ? (
                                cropPrediction.prediction
                              ) : knownCandidateLabel ? (
                                knownCandidateLabel
                              ) : (
                                <span className="skeleton-pulse" style={{ display: 'inline-block', width: '80px', height: '1.8rem', backgroundColor: 'var(--bg-elevated)', borderRadius: '4px', verticalAlign: 'middle' }} />
                              )}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#7E7A75', marginTop: '2px' }}>
                              Model: Experimental recognizer
                            </div>
                          </div>"""

r4 = """                          <div style={{ marginTop: '8px' }}>
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

assert t4 in c, 't4 not found in c'
c = c.replace(t4, r4)

# Part 5: Candidate Chip rendering in gallery strip
t5 = """                      return (
                        <div
                          key={cand.idx}
                          data-chip-idx={cand.idx}
                          className={`glyph-chip status-${cand.status} ${isSelected ? 'selected' : ''} ${cand.isTiny ? 'is-tiny' : ''}`}
                          onClick={() => handleSelectAndFocusBox(cand.idx)}
                          title={`Candidate #${cand.idx + 1} (${cand.w}x${cand.h}px) - ${cand.status}`}
                        >
                          <div className="glyph-chip-tooltip">
                            #{cand.idx + 1} &middot; {cand.w}&times;{cand.h}px &middot; {cand.status}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                            <span style={{ fontSize: '0.65rem', color: '#A8A29A', fontWeight: '600' }}>
                              #{cand.idx + 1}
                            </span>
                            <span className={`status-dot dot-${cand.status}`} />
                          </div>

                          <div
                            className="glyph-chip-label"
                            style={{
                              color: isSelected
                                ? '#C9A66B'
                                : cand.status === 'corrected'
                                ? '#64B4F0'
                                : cand.status === 'reviewed'
                                ? '#76D876'
                                : cand.status === 'predicted'
                                ? '#EDEDEC'
                                : '#6A6A72'
                            }}
                          >
                            {cand.label || '—'}
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', fontSize: '0.62rem', color: '#7E7A75' }}>
                            <span>{cand.w}x{cand.h}</span>
                            {cand.confidence != null && (
                              <span style={{ color: '#C9A66B', fontWeight: '600' }}>
                                {Math.round(cand.confidence * 100)}%
                              </span>
                            )}
                          </div>
                        </div>
                      );"""

r5 = """                      return (
                        <div
                          key={cand.idx}
                          data-chip-idx={cand.idx}
                          className={`glyph-chip status-${cand.status} ${isSelected ? 'selected' : ''} ${cand.isTiny ? 'is-tiny' : ''} ${cand.uncertain ? 'is-uncertain' : ''}`}
                          onClick={() => handleSelectAndFocusBox(cand.idx)}
                          title={`Candidate #${cand.idx + 1} (${cand.w}x${cand.h}px) - ${cand.status}${cand.uncertain ? ' (Uncertain)' : ''}`}
                        >
                          <div className="glyph-chip-tooltip">
                            #{cand.idx + 1} &middot; {cand.w}&times;{cand.h}px &middot; {cand.status}
                            {cand.uncertain && ' (Uncertain)'}
                            {cand.confidence != null && ` (${Math.round(cand.confidence * 100)}% conf)`}
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                            <span style={{ fontSize: '0.65rem', color: '#A8A29A', fontWeight: '600' }}>
                              #{cand.idx + 1}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                              {cand.uncertain && (
                                <span className="uncertain-tag">
                                  Uncertain
                                </span>
                              )}
                              <span className={`status-dot dot-${cand.status}`} />
                            </div>
                          </div>

                          <div
                            className="glyph-chip-label"
                            style={{
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
                            {cand.label || '—'}
                          </div>

                          {/* Subtle Confidence Bar on Chip */}
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

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', fontSize: '0.62rem', color: '#7E7A75' }}>
                            <span>{cand.w}x{cand.h}</span>
                            {cand.confidence != null && (
                              <span style={{ color: cand.uncertain ? '#D97706' : '#C9A66B', fontWeight: '600' }}>
                                {Math.round(cand.confidence * 100)}%
                              </span>
                            )}
                          </div>
                        </div>
                      );"""

assert t5 in c, 't5 not found in c'
c = c.replace(t5, r5)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Successfully updated Inspector panel and candidate chip gallery in App.jsx')

