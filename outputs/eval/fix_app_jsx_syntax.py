from pathlib import Path

app_path = Path("frontend/src/App.jsx")
text = app_path.read_text(encoding="utf-8").replace("\r\n", "\n")

# 1. Strip misplaced snippet from the very top before 'import React'
idx_imp = text.find("import React")
assert idx_imp != -1, "import React not found"
if idx_imp > 0:
    print(f"Stripping {idx_imp} characters from top of App.jsx")
    text = text[idx_imp:]

# 2. Locate the old chip label and confidence bar inside visibleCandidates.map
idx_map = text.find("visibleCandidates.map")
assert idx_map != -1, "visibleCandidates.map not found"

idx_chip_start = text.find('<div\n                            className="glyph-chip-label"', idx_map)
assert idx_chip_start != -1, "chip label start not found"

conf_target = """                          {/* Subtle Confidence Bar on Chip */}
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
                          )}"""

idx_conf = text.find(conf_target, idx_chip_start)
assert idx_conf != -1, "conf_target not found"
idx_chip_end = idx_conf + len(conf_target)

old_chip_slice = text[idx_chip_start:idx_chip_end]

new_chip_block = """{(() => {
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

text = text[:idx_chip_start] + new_chip_block + text[idx_chip_end:]

with open(app_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(text)

print("Cleaned and fixed frontend/src/App.jsx successfully")

