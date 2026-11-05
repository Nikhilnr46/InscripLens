with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update lucide-react imports: add Download
t_imp = """  Maximize2,
  ArrowLeft,
  ChevronLeft
} from 'lucide-react';"""

r_imp = """  Maximize2,
  ArrowLeft,
  ChevronLeft,
  Download
} from 'lucide-react';"""

assert t_imp in c, "t_imp not found"
c = c.replace(t_imp, r_imp)

# 2. Add highAccuracy state
t_state = """  const [activeTab, setActiveTab] = useState('studio'); // 'studio', 'history', 'credits'
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);"""

r_state = """  const [activeTab, setActiveTab] = useState('studio'); // 'studio', 'history', 'credits'
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [highAccuracy, setHighAccuracy] = useState(false);"""

assert t_state in c, "t_state not found"
c = c.replace(t_state, r_state)

# 3. Update loadDemoStone and handleFileUpload
t_load = """  // Load demonstration stone
  const loadDemoStone = async () => {
    setLoading(true);
    setLoadingMessage('Loading Nagavara demonstration stone...');
    try {
      const res = await fetch('/api/analyse?use_demo=true', { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Enhancement analysis could not be completed.');
      }
      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Upload user photograph
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setLoadingMessage('Enhancing inscription photograph...');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/analyse', { method: 'POST', body: formData });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Image enhancement could not be completed.');
      }
      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };"""

r_load = """  // Load demonstration stone
  const loadDemoStone = async () => {
    setLoading(true);
    setLoadingMessage(highAccuracy ? 'Running high accuracy multi-scale enhancement...' : 'Loading Nagavara demonstration stone...');
    try {
      const modeParam = highAccuracy ? 'high_accuracy' : 'standard';
      const res = await fetch(`/api/analyse?use_demo=true&mode=${modeParam}`, { method: 'POST' });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Enhancement analysis could not be completed.');
      }
      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);
      if (data.fallback_note) {
        showError(data.fallback_note);
      }
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Upload user photograph
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setLoadingMessage(highAccuracy ? 'Running high accuracy multi-scale enhancement...' : 'Enhancing inscription photograph...');
    try {
      const modeParam = highAccuracy ? 'high_accuracy' : 'standard';
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', modeParam);
      const res = await fetch(`/api/analyse?mode=${modeParam}`, { method: 'POST', body: formData });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Image enhancement could not be completed.');
      }
      const data = await res.json();
      setAnalysis(data);
      setSelectedBoxIndex(data.boxes.length > 0 ? 0 : null);
      setBatchRegions([]);
      setPredictionCache({});
      setClassifyComplete(false);
      setClassifyProgress(0);
      setCropPrediction(null);
      fetchReviews(data.id);
      if (data.fallback_note) {
        showError(data.fallback_note);
      }
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };"""

assert t_load in c, "t_load not found"
c = c.replace(t_load, r_load)

# 4. Header toolbar: Add switch and note
t_hdr = """        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ThemeToggle />
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileUpload}
          />
          <button
            className="btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            <Upload size={14} /> Upload Photograph
          </button>
          <button
            className="btn-primary btn-magnetic"
            onClick={loadDemoStone}
            disabled={loading}
          >
            <Sparkles size={14} /> Try Demo Stone (Nagavara)
          </button>
        </div>"""

r_hdr = """        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* High accuracy mode switch with note */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', textAlign: 'right' }}>
            <div
              className="toggle-wrapper"
              onClick={() => setHighAccuracy(!highAccuracy)}
              role="switch"
              aria-checked={highAccuracy}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === ' ' || e.key === 'Enter') {
                  e.preventDefault();
                  setHighAccuracy(!highAccuracy);
                }
              }}
              title="Toggle High accuracy mode"
              style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <div className={`toggle-switch ${highAccuracy ? 'active' : ''}`} style={{ width: '30px', height: '16px' }}>
                <div className="toggle-thumb" style={{ width: '10px', height: '10px' }} />
              </div>
              <span style={{ fontSize: '0.76rem', color: highAccuracy ? '#C9A66B' : 'var(--text-muted)', fontWeight: highAccuracy ? '600' : '500' }}>
                High accuracy mode
              </span>
            </div>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-subtle)', maxWidth: '240px', lineHeight: 1.15, marginTop: '2px' }}>
              Finds more faint strokes. Slower, and may add a few false strokes.
            </span>
          </div>

          <ThemeToggle />
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept="image/png,image/jpeg,image/jpg"
            onChange={handleFileUpload}
          />
          <button
            className="btn-secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            <Upload size={14} /> Upload Photograph
          </button>
          <button
            className="btn-primary btn-magnetic"
            onClick={loadDemoStone}
            disabled={loading}
          >
            <Sparkles size={14} /> Try Demo Stone (Nagavara)
          </button>
        </div>"""

assert t_hdr in c, "t_hdr not found"
c = c.replace(t_hdr, r_hdr)

# 5. Canvas Toolbar: Mode badge and Mask download
t_bar = """                          <span style={{ fontSize: '0.78rem', color: showBoxes ? '#EDEDEC' : '#A8A29A' }}>
                            Boxes ({analysis.boxes.length})
                          </span>
                        </div>
                      </div>"""

r_bar = """                          <span style={{ fontSize: '0.78rem', color: showBoxes ? '#EDEDEC' : '#A8A29A' }}>
                            Boxes ({analysis.boxes.length})
                          </span>
                        </div>

                        {/* Mode badge & Mask download button */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span
                            className={`pill ${analysis.mode === 'high_accuracy' ? 'pill-sandstone' : 'pill-neutral'}`}
                            style={{ fontSize: '0.68rem', padding: '2px 8px' }}
                            title={analysis.mode === 'high_accuracy' ? 'Enhanced with multi-scale sliding window' : 'Enhanced with standard single-scale GPU'}
                          >
                            {analysis.mode_label || (analysis.mode === 'high_accuracy' ? 'High accuracy' : 'Standard')}
                          </span>

                          <a
                            href={analysis.mask_url}
                            download={`mask_${analysis.id}.png`}
                            className="tool-btn"
                            title="Download enhanced binary mask image"
                            style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
                          >
                            <Download size={12} /> Mask
                          </a>
                        </div>
                      </div>"""

assert t_bar in c, "t_bar not found"
c = c.replace(t_bar, r_bar)

# 6. Empty State: High accuracy switch with note
t_empty = """                  <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                    <button className="btn-primary" onClick={loadDemoStone} disabled={loading}>
                      <Sparkles size={14} /> Try Demo Stone (Nagavara)
                    </button>
                    <button className="btn-secondary" onClick={() => fileInputRef.current?.click()} disabled={loading}>
                      <Upload size={14} /> Upload Image
                    </button>
                  </div>"""

r_empty = """                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
                    <div
                      className="toggle-wrapper"
                      onClick={() => setHighAccuracy(!highAccuracy)}
                      role="switch"
                      aria-checked={highAccuracy}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === ' ' || e.key === 'Enter') {
                          e.preventDefault();
                          setHighAccuracy(!highAccuracy);
                        }
                      }}
                      style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                    >
                      <div className={`toggle-switch ${highAccuracy ? 'active' : ''}`} style={{ width: '32px', height: '18px' }}>
                        <div className="toggle-thumb" style={{ width: '12px', height: '12px' }} />
                      </div>
                      <span style={{ fontSize: '0.82rem', color: highAccuracy ? '#C9A66B' : 'var(--text-primary)', fontWeight: '600' }}>
                        High accuracy mode
                      </span>
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', maxWidth: '360px', lineHeight: 1.3 }}>
                      Finds more faint strokes. Slower, and may add a few false strokes.
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                    <button className="btn-primary" onClick={loadDemoStone} disabled={loading}>
                      <Sparkles size={14} /> Try Demo Stone (Nagavara)
                    </button>
                    <button className="btn-secondary" onClick={() => fileInputRef.current?.click()} disabled={loading}>
                      <Upload size={14} /> Upload Image
                    </button>
                  </div>"""

assert t_empty in c, "t_empty not found"
c = c.replace(t_empty, r_empty)

# 7. History View: Mode and Export
t_hist = """                    <div>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                        {item.display_name}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Analysis Record · {item.created ? new Date(item.created).toLocaleDateString() : 'Recorded'}
                      </div>
                    </div>
                    <span className="pill pill-sandstone">Analyzed Locally</span>"""

r_hist = """                    <div>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                        {item.display_name}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Analysis Record · {item.created ? new Date(item.created).toLocaleDateString() : 'Recorded'}
                        {item.mode_label && ` · Mode: ${item.mode_label}`}
                      </div>
                      {item.fallback_note && (
                        <div style={{ fontSize: '0.72rem', color: '#D97706', marginTop: '2px' }}>
                          {item.fallback_note}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className={`pill ${item.mode === 'high_accuracy' ? 'pill-sandstone' : 'pill-neutral'}`}>
                        {item.mode_label || (item.mode === 'high_accuracy' ? 'High accuracy' : 'Standard')}
                      </span>
                      <span className="pill pill-sandstone">Analyzed Locally</span>
                      <a
                        href={`/api/export/${item.id}`}
                        download={`inscriplens_export_${item.id}.json`}
                        className="tool-btn"
                        title="Export analysis metadata and reviews as JSON"
                        style={{ textDecoration: 'none', fontSize: '0.75rem', padding: '3px 8px' }}
                      >
                        Export
                      </a>
                    </div>"""

assert t_hist in c, "t_hist not found"
c = c.replace(t_hist, r_hist)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(c)

print('Successfully updated frontend/src/App.jsx for High accuracy mode')

