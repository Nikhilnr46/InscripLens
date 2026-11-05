import { useRef, useState } from 'react';
import { formatDisplayLabel } from './utils/kannadaConverter';

async function predict(run, bbox) {
  const response = await fetch('/api/predict-crop', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: run, bbox })
  });
  if (!response.ok) throw new Error('Prediction failed. Please retry.');
  const data = await response.json();
  return { bbox, prediction: data.prediction, alternatives: data.alternatives,
    model: data.model, model_sha256: data.model_sha256 };
}

export default function RedrawComparison({ analysis, box, scriptMode, modernLetters }) {
  const key = 'inscriplens:crop-comparisons:' + analysis.id + ':' + box.join(',');
  const [open, setOpen] = useState(false);
  const [adjusted, setAdjusted] = useState(null);
  const [reading, setReading] = useState('');
  const [attempts, setAttempts] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key)) || []; } catch { return []; }
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const start = useRef(null);
  const [x,y,r,b] = box;
  const margin = Math.max(36, r-x, b-y);
  const left = Math.max(0,x-margin), top = Math.max(0,y-margin);
  const width = Math.min(analysis.width,r+margin)-left;
  const height = Math.min(analysis.height,b+margin)-top;
  function point(e) {
    const svg = e.currentTarget;
    const p = new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.getScreenCTM().inverse());
    return [Math.round(Math.max(left,Math.min(left+width,p.x))),Math.round(Math.max(top,Math.min(top+height,p.y)))];
  }
  function move(e) {
    if (!start.current) return;
    const [a,b] = start.current, [c,d] = point(e);
    setAdjusted([Math.min(a,c),Math.min(b,d),Math.max(a,c),Math.max(b,d)]);
  }
  async function compare() {
    setBusy(true); setError('');
    try {
      const [automatic, manual] = await Promise.all([predict(analysis.id,box),predict(analysis.id,adjusted)]);
      const entry = {run_id:analysis.id, time:new Date().toISOString(), reading:reading.trim(), verified:false, automatic, manual};
      const next = [...attempts,entry];
      setAttempts(next);
      try { localStorage.setItem(key,JSON.stringify(next)); }
      catch { setError('Browser storage unavailable. Download the comparison to keep it.'); }
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  function download() {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([JSON.stringify(attempts,null,2)],{type:'application/json'}));
    a.download = 'crop-comparisons-'+analysis.id+'-'+box.join('-')+'.json'; a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }
  function outline(coords,color) {
    return <rect x={coords[0]} y={coords[1]} width={coords[2]-coords[0]} height={coords[3]-coords[1]}
      fill="none" stroke={color} strokeWidth="2" vectorEffect="non-scaling-stroke"/>;
  }
  return <section className="inspector-section">
    <button type="button" className="toolbar-btn" aria-expanded={open} onClick={()=>setOpen(!open)}>Redraw box and compare</button>
    {open && <div>
      <p>Drag around the full glyph. Gold shows the automatic box. Blue shows yours.</p>
      <svg viewBox={[left,top,width,height].join(' ')} style={{width:'100%',aspectRatio:width/height,touchAction:'none',cursor:'crosshair'}}
        aria-label="Draw an adjusted glyph box" onPointerDown={e=>{if(busy)return; e.currentTarget.setPointerCapture(e.pointerId);start.current=point(e);setAdjusted(null);}}
        onPointerMove={move} onPointerUp={e=>{move(e);start.current=null;}} onPointerCancel={()=>{start.current=null;setAdjusted(null);}}>
        <image href={analysis.image_url} width={analysis.width} height={analysis.height}/>
        {outline(box,'#e5ac51')}{adjusted && outline(adjusted,'#48d9ed')}
      </svg>
      <label>Proposed reading (optional) <input value={reading} disabled={busy} onChange={e=>setReading(e.target.value)}/></label>
      <button type="button" disabled={busy||!adjusted||adjusted[2]<=adjusted[0]||adjusted[3]<=adjusted[1]} onClick={compare}>
        {busy?'Comparing…':'Compare and save'}</button>
      {error && <p role="alert">{error}</p>}
      {attempts.length>0 && <><table><thead><tr><th>Attempt</th><th>Automatic</th><th>Redrawn</th></tr></thead>
        <tbody>{attempts.map((a,i)=><tr key={i}><td>{i+1}</td>{[a.automatic,a.manual].map((v,j)=><td key={j}>{formatDisplayLabel(v.prediction,scriptMode,modernLetters).primary}</td>)}</tr>)}</tbody></table>
        <button type="button" onClick={download}>Download comparisons</button></>}
    </div>}
  </section>;
}
