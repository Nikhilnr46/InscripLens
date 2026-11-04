import React, { useState, useEffect, useRef } from 'react';
import {
  Layers,
  Sparkles,
  Sliders,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle,
  FileText,
  Info,
  Upload,
  Cpu,
  History,
  ShieldCheck,
  ChevronRight,
  Eye,
  Save,
  Tag,
  AlertCircle,
  Maximize2,
  ArrowLeft,
  ChevronLeft
} from 'lucide-react';
import LandingPage from './pages/LandingPage.jsx';
import ThemeToggle from './components/ThemeToggle.tsx';
import { SITE } from './config/site.ts';
import { initSiteInteractions } from './utils/interactions.ts';

export default function App() {
  // Routing: '/' for single-page landing site, '/studio' for epigraphic workspace
  const [route, setRoute] = useState(() => {
    const p = window.location.pathname.replace(/\/+$/, '') || '/';
    // Redirect old separate routes to matching /#section
    if (p === '/about' || p === '/workflow' || p === '/limitations' || p === '/overview') {
      const section = p.replace(/^\//, '');
      window.history.replaceState(null, '', `/#${section}`);
      return '/';
    }
    if (p === '/studio' || window.location.search.includes('studio=1') || window.location.search.includes('demo=1')) {
      return '/studio';
    }
    return '/';
  });

  // Collapsible sidebar state (remembered in localStorage)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('inscriplens_sidebar_collapsed') === 'true';
  });

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      localStorage.setItem('inscriplens_sidebar_collapsed', String(next));
      return next;
    });
  };

  const navigateToStudio = (autoDemo = false) => {
    const target = autoDemo ? '/studio?demo=1' : '/studio';
    window.history.pushState(null, '', target);
    setRoute('/studio');
    if (autoDemo) {
      loadDemoStone();
    }
  };

  const navigateToSection = (sectionId = 'overview') => {
    const hash = sectionId === 'overview' ? '' : `#${sectionId}`;
    window.history.pushState(null, '', `/${hash}`);
    setRoute('/');
    setTimeout(() => {
      const isReduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (!sectionId || sectionId === 'overview') {
        window.scrollTo({ top: 0, behavior: isReduced ? 'auto' : 'smooth' });
      } else {
        const el = document.getElementById(sectionId);
        if (el) {
          el.scrollIntoView({ behavior: isReduced ? 'auto' : 'smooth' });
        }
      }
    }, 100);
  };

  const navigateToHome = () => {
    navigateToSection('overview');
  };

  const navigateToAbout = () => {
    navigateToSection('about');
  };

  useEffect(() => {
    const onPopState = () => {
      const p = window.location.pathname.replace(/\/+$/, '') || '/';
      if (p === '/about' || p === '/workflow' || p === '/limitations' || p === '/overview') {
        const section = p.replace(/^\//, '');
        window.history.replaceState(null, '', `/#${section}`);
        setRoute('/');
        return;
      }
      setRoute(p === '/studio' ? '/studio' : '/');
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  // Update dynamic document title & meta description per route
  useEffect(() => {
    let title = `${SITE.name}`;
    let desc = 'Offline computational workspace for historical Kannada epigraphy and character study.';
    if (route === '/studio') {
      title = `${SITE.name} - Workspace`;
      desc = 'Offline interactive analysis workspace for historical Kannada stone inscriptions.';
    } else if (route === '/about') {
      title = `${SITE.name} - About & Documentation`;
      desc = 'Research documentation, pipeline architecture, and attribution for InscripLens Studio.';
    } else {
      title = `${SITE.name} - Read the stone before it fades`;
      desc = 'A local research workspace for studying photographs of historical Kannada stone inscriptions.';
    }
    document.title = title;

    let metaDesc = document.querySelector('meta[name="description"]');
    if (!metaDesc) {
      metaDesc = document.createElement('meta');
      metaDesc.name = 'description';
      document.head.appendChild(metaDesc);
    }
    metaDesc.content = desc;
  }, [route]);

  const [activeTab, setActiveTab] = useState('studio'); // 'studio', 'history', 'credits'
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  
  // Active analysis record
  const [analysis, setAnalysis] = useState(null);
  const [sliderPos, setSliderPos] = useState(50); // percentage 0 - 100 for curtain
  const [showBoxes, setShowBoxes] = useState(true);
  const [selectedBoxIndex, setSelectedBoxIndex] = useState(null);

  // Zoom & Pan Canvas Stage State
  const [scale, setScale] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Batch recognition state & progress
  const [isClassifying, setIsClassifying] = useState(false);
  const [classifyProgress, setClassifyProgress] = useState(0);
  const [classifyComplete, setClassifyComplete] = useState(false);
  
  // Single-crop prediction & cache
  const [cropPrediction, setCropPrediction] = useState(null);
  const [predictingCrop, setPredictingCrop] = useState(false);
  const [predictionCache, setPredictionCache] = useState({});
  
  // Batch regions
  const [batchRegions, setBatchRegions] = useState([]);

  // Candidate strip filters & tiny regions
  const [filterTab, setFilterTab] = useState('all'); // 'all', 'predicted', 'reviewed'
  const [hideTiny, setHideTiny] = useState(false);
  
  // Reviews loaded from SQLite
  const [reviewsList, setReviewsList] = useState([]);
  
  // Review form
  const [suggestion, setSuggestion] = useState('');
  const [reviewer, setReviewer] = useState('');
  const [note, setNote] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // History & Credits
  const [historyList, setHistoryList] = useState([]);
  const [credits, setCredits] = useState(null);

  const fileInputRef = useRef(null);
  const containerRef = useRef(null);
  const viewportRef = useRef(null);
  const galleryStripRef = useRef(null);
  const isDraggingCurtain = useRef(false);
  const panStartRef = useRef(null);

  const showError = (msg) => {
    setErrorMessage(msg);
    setTimeout(() => setErrorMessage(''), 4000);
  };

  // Load system status on mount
  useEffect(() => {
    fetch('/api/status')
      .then(res => res.json())
      .then(data => setStatus(data))
      .catch(() => console.error('Status fetch failed'));

    fetch('/api/credits')
      .then(res => res.json())
      .then(data => setCredits(data))
      .catch(() => console.error('Credits fetch failed'));
  }, []);

  // Initialize shared rAF-throttled hover and scroll-reveal interactions
  useEffect(() => {
    const cleanup = initSiteInteractions();
    return cleanup;
  }, [route, activeTab]);

  // Load history when switching to history tab
  useEffect(() => {
    if (activeTab === 'history') {
      fetch('/api/history')
        .then(res => res.json())
        .then(data => setHistoryList(data))
        .catch(() => showError('Unable to load analysis history.'));
    }
  }, [activeTab]);

  // Fetch reviews for current analysis
  const fetchReviews = async (runId) => {
    if (!runId) return;
    try {
      const res = await fetch(`/api/reviews/${runId}`);
      if (res.ok) {
        const data = await res.json();
        setReviewsList(data || []);
      }
    } catch {
      console.error('Failed to load reviews');
    }
  };

  // Match review record to a candidate bounding box [x1, y1, x2, y2]
  const findReviewForBox = (bbox) => {
    if (!bbox || !reviewsList || !reviewsList.length) return null;
    return reviewsList.find(r =>
      Array.isArray(r.bbox) &&
      r.bbox[0] === bbox[0] &&
      r.bbox[1] === bbox[1] &&
      r.bbox[2] === bbox[2] &&
      r.bbox[3] === bbox[3]
    );
  };

  // Calculate candidate metadata: status, labels, dimensions, and confidence
  const getCandidateInfo = (idx, bbox) => {
    const w = bbox[2] - bbox[0];
    const h = bbox[3] - bbox[1];
    const isTiny = w < 10 && h < 10;
    const review = findReviewForBox(bbox);

    let status = 'unpredicted';
    let label = null;
    let confidence = null;

    if (review) {
      if (review.suggested_label && review.suggested_label.trim() !== '') {
        status = 'corrected';
        label = review.suggested_label;
      } else {
        status = 'reviewed';
        label = review.prediction || 'Reviewed';
      }
      confidence = review.confidence ?? null;
    } else {
      const batchMatch = batchRegions.find(r => r.candidate === idx + 1);
      const cached = predictionCache[idx];
      const activeCrop = (selectedBoxIndex === idx && cropPrediction) ? cropPrediction.prediction : null;
      const pred = batchMatch ? batchMatch.predicted_source_label : (cached || activeCrop);

      if (pred) {
        status = 'predicted';
        label = pred;
        confidence = batchMatch?.confidence ?? (selectedBoxIndex === idx ? cropPrediction?.confidence : null);
      } else {
        status = 'unpredicted';
        label = null;
        confidence = null;
      }
    }

    return { idx, bbox, w, h, isTiny, status, label, confidence, review };
  };

  // Derive candidate lists and counts
  const allCandidatesInfo = (analysis?.boxes || []).map((b, idx) => getCandidateInfo(idx, b));

  const counts = {
    all: allCandidatesInfo.length,
    predicted: allCandidatesInfo.filter(c => c.status === 'predicted').length,
    reviewed: allCandidatesInfo.filter(c => c.status === 'reviewed' || c.status === 'corrected').length,
    tiny: allCandidatesInfo.filter(c => c.isTiny).length
  };

  const visibleCandidates = allCandidatesInfo.filter(c => {
    if (hideTiny && c.isTiny) return false;
    if (filterTab === 'predicted') return c.status === 'predicted';
    if (filterTab === 'reviewed') return c.status === 'reviewed' || c.status === 'corrected';
    return true;
  });

  // Fit image to available panel height and width
  const fitToViewport = (animate = false) => {
    if (!viewportRef.current || !analysis) return;
    const vpRect = viewportRef.current.getBoundingClientRect();
    const padding = 32; // 16px buffer
    const availW = Math.max(50, vpRect.width - padding);
    const availH = Math.max(50, vpRect.height - padding);

    // Fit to panel height by default while respecting bounds
    const fitScale = Math.min(availH / analysis.height, availW / analysis.width);
    const targetScale = Math.max(0.1, Math.min(3.0, fitScale));

    const targetPanX = (vpRect.width - analysis.width * targetScale) / 2;
    const targetPanY = (vpRect.height - analysis.height * targetScale) / 2;

    if (animate) {
      setIsTransitioning(true);
      setTimeout(() => setIsTransitioning(false), 350);
    }
    setScale(targetScale);
    setPan({ x: targetPanX, y: targetPanY });
  };

  // 100% scale button
  const zoomTo100 = () => {
    if (!viewportRef.current || !analysis) return;
    const vpRect = viewportRef.current.getBoundingClientRect();
    const targetScale = 1.0;
    const targetPanX = (vpRect.width - analysis.width) / 2;
    const targetPanY = (vpRect.height - analysis.height) / 2;

    setIsTransitioning(true);
    setScale(targetScale);
    setPan({ x: targetPanX, y: targetPanY });
    setTimeout(() => setIsTransitioning(false), 300);
  };

  // Zoom In button
  const zoomIn = () => {
    if (!viewportRef.current || !analysis) return;
    const vpRect = viewportRef.current.getBoundingClientRect();
    const centerX = vpRect.width / 2;
    const centerY = vpRect.height / 2;
    const newScale = Math.min(5.0, scale * 1.25);
    const newPanX = centerX - (centerX - pan.x) * (newScale / scale);
    const newPanY = centerY - (centerY - pan.y) * (newScale / scale);

    setIsTransitioning(true);
    setScale(newScale);
    setPan({ x: newPanX, y: newPanY });
    setTimeout(() => setIsTransitioning(false), 200);
  };

  // Zoom Out button
  const zoomOut = () => {
    if (!viewportRef.current || !analysis) return;
    const vpRect = viewportRef.current.getBoundingClientRect();
    const centerX = vpRect.width / 2;
    const centerY = vpRect.height / 2;
    const newScale = Math.max(0.1, scale / 1.25);
    const newPanX = centerX - (centerX - pan.x) * (newScale / scale);
    const newPanY = centerY - (centerY - pan.y) * (newScale / scale);

    setIsTransitioning(true);
    setScale(newScale);
    setPan({ x: newPanX, y: newPanY });
    setTimeout(() => setIsTransitioning(false), 200);
  };

  // Automatically fit image when a new analysis loads
  useEffect(() => {
    if (analysis) {
      const timer = setTimeout(() => {
        fitToViewport(false);
      }, 60);
      return () => clearTimeout(timer);
    }
  }, [analysis?.id]);

  // Non-passive scroll wheel listener centered on cursor
  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return;

    const onWheelNative = (e) => {
      e.preventDefault();
      const rect = vp.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
      setScale((prevScale) => {
        const newScale = Math.max(0.1, Math.min(5.0, prevScale * zoomFactor));
        setPan((prevPan) => {
          const newPanX = mouseX - (mouseX - prevPan.x) * (newScale / prevScale);
          const newPanY = mouseY - (mouseY - prevPan.y) * (newScale / prevScale);
          return { x: newPanX, y: newPanY };
        });
        return newScale;
      });
      setIsTransitioning(false);
    };

    vp.addEventListener('wheel', onWheelNative, { passive: false });
    return () => {
      vp.removeEventListener('wheel', onWheelNative);
    };
  }, [analysis]);

  // Drag-pan handling on viewport
  const handleViewportMouseDown = (e) => {
    if (e.button !== 0) return;
    if (
      e.target.closest('.curtain-handle') ||
      e.target.closest('.svg-box') ||
      e.target.closest('.svg-box-selected')
    ) {
      return;
    }
    setIsPanning(true);
    panStartRef.current = {
      x: e.clientX - pan.x,
      y: e.clientY - pan.y
    };

    const handleGlobalMouseMove = (moveEvent) => {
      if (!panStartRef.current) return;
      setPan({
        x: moveEvent.clientX - panStartRef.current.x,
        y: moveEvent.clientY - panStartRef.current.y
      });
    };

    const handleGlobalMouseUp = () => {
      setIsPanning(false);
      panStartRef.current = null;
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleGlobalMouseUp);
    };

    window.addEventListener('mousemove', handleGlobalMouseMove);
    window.addEventListener('mouseup', handleGlobalMouseUp);
  };

  // Curtain slider drag handling
  const handleCurtainHandleMouseDown = (e) => {
    e.stopPropagation();
    e.preventDefault();
    isDraggingCurtain.current = true;

    const handleGlobalMouseMove = (moveEvent) => {
      if (!isDraggingCurtain.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const clientX = moveEvent.clientX;
      const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
      setSliderPos(pct);
    };

    const handleGlobalMouseUp = () => {
      isDraggingCurtain.current = false;
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleGlobalMouseUp);
    };

    window.addEventListener('mousemove', handleGlobalMouseMove);
    window.addEventListener('mouseup', handleGlobalMouseUp);
  };

  // Keyboard navigation for curtain wipe slider
  const handleCurtainKeyDown = (e) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
      e.preventDefault();
      setSliderPos(prev => Math.max(0, prev - (e.shiftKey ? 10 : 2)));
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
      e.preventDefault();
      setSliderPos(prev => Math.min(100, prev + (e.shiftKey ? 10 : 2)));
    } else if (e.key === 'Home') {
      e.preventDefault();
      setSliderPos(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      setSliderPos(100);
    }
  };

  // Load demonstration stone
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
  };

  // Predict selected crop region
  const predictBox = async (boxIndex) => {
    if (!analysis || boxIndex === null || !analysis.boxes[boxIndex]) return;
    const bbox = analysis.boxes[boxIndex];
    setSelectedBoxIndex(boxIndex);
    setPredictingCrop(true);
    try {
      const res = await fetch('/api/predict-crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: analysis.id, bbox })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Character prediction could not be completed.');
      }
      const data = await res.json();
      setCropPrediction(data);
      setPredictionCache(prev => ({ ...prev, [boxIndex]: data.prediction }));
    } catch (err) {
      showError(err.message);
    } finally {
      setPredictingCrop(false);
    }
  };

  // Smoothly zoom and pan to selected candidate box
  const focusOnBox = (boxIndex) => {
    if (!analysis || !analysis.boxes[boxIndex] || !viewportRef.current) return;
    const bbox = analysis.boxes[boxIndex];
    const vpRect = viewportRef.current.getBoundingClientRect();

    const boxCenterX = (bbox[0] + bbox[2]) / 2;
    const boxCenterY = (bbox[1] + bbox[3]) / 2;

    // Pick comfortable zoom target for character focus
    const targetScale = Math.max(1.6, Math.min(2.8, scale < 1.2 ? 1.8 : scale));

    const targetPanX = (vpRect.width / 2) - (boxCenterX * targetScale);
    const targetPanY = (vpRect.height / 2) - (boxCenterY * targetScale);

    setIsTransitioning(true);
    setScale(targetScale);
    setPan({ x: targetPanX, y: targetPanY });
    setTimeout(() => setIsTransitioning(false), 350);
  };

  // Handle box click from canvas or bottom gallery chips
  const handleSelectAndFocusBox = (boxIndex) => {
    setSelectedBoxIndex(boxIndex);
    predictBox(boxIndex);
    focusOnBox(boxIndex);
  };

  // Arrow key navigation between candidates
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is in an input, textarea or interacting with curtain slider
      const active = document.activeElement;
      if (
        active &&
        (active.tagName === 'INPUT' ||
          active.tagName === 'TEXTAREA' ||
          active.classList?.contains('curtain-handle'))
      ) {
        return;
      }

      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        if (!visibleCandidates.length) return;
        e.preventDefault();

        const currentPos = visibleCandidates.findIndex(c => c.idx === selectedBoxIndex);
        let nextCandidate;

        if (e.key === 'ArrowRight') {
          if (currentPos === -1 || currentPos >= visibleCandidates.length - 1) {
            nextCandidate = visibleCandidates[0];
          } else {
            nextCandidate = visibleCandidates[currentPos + 1];
          }
        } else {
          if (currentPos <= 0) {
            nextCandidate = visibleCandidates[visibleCandidates.length - 1];
          } else {
            nextCandidate = visibleCandidates[currentPos - 1];
          }
        }

        if (nextCandidate) {
          handleSelectAndFocusBox(nextCandidate.idx);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [visibleCandidates, selectedBoxIndex]);

  // Auto-scroll gallery strip to selected candidate chip
  useEffect(() => {
    if (selectedBoxIndex === null || !galleryStripRef.current) return;
    const chipEl = galleryStripRef.current.querySelector(`[data-chip-idx="${selectedBoxIndex}"]`);
    if (chipEl) {
      chipEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [selectedBoxIndex]);

  // Synchronize review form with existing review record on candidate selection
  useEffect(() => {
    if (analysis && selectedBoxIndex !== null && analysis.boxes[selectedBoxIndex]) {
      const existing = findReviewForBox(analysis.boxes[selectedBoxIndex]);
      if (existing) {
        setSuggestion(existing.suggested_label || '');
        setReviewer(existing.reviewer || '');
        setNote(existing.note || '');
      } else {
        setSuggestion('');
        setNote('');
        // Keep reviewer name remembered if already entered
      }
    }
  }, [selectedBoxIndex, reviewsList]);

  // Auto-predict first box when analysis completes
  useEffect(() => {
    if (analysis && selectedBoxIndex !== null && !cropPrediction) {
      predictBox(selectedBoxIndex);
    }
  }, [analysis, selectedBoxIndex]);

  // Batch recognize all candidate regions with progress tracking
  const runBatchRecognize = async () => {
    if (!analysis) return;
    setIsClassifying(true);
    setClassifyComplete(false);
    setClassifyProgress(0);

    const total = analysis.boxes.length;
    // Animate progress counting up towards total
    const progressTimer = setInterval(() => {
      setClassifyProgress((prev) => {
        if (prev >= total - 3) return prev;
        const step = Math.max(1, Math.floor(Math.random() * 8) + 3);
        return Math.min(total - 3, prev + step);
      });
    }, 60);

    try {
      const res = await fetch('/api/recognize-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: analysis.id })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Batch recognition could not be completed.');
      }
      const data = await res.json();
      clearInterval(progressTimer);
      setClassifyProgress(total);
      setBatchRegions(data.regions || []);
      setClassifyComplete(true);
    } catch (err) {
      clearInterval(progressTimer);
      showError(err.message);
    } finally {
      setIsClassifying(false);
    }
  };

  // Save character review (behaviour unchanged)
  const handleSaveReview = async (e) => {
    e.preventDefault();
    if (!analysis || !cropPrediction) return;
    try {
      const res = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: analysis.id,
          bbox: cropPrediction.bbox,
          prediction: cropPrediction.prediction,
          model: 'Experimental recognizer',
          model_sha256: cropPrediction.model_sha256,
          suggestion,
          reviewer,
          note
        })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Review record could not be saved.');
      }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      await fetchReviews(analysis.id);
    } catch (err) {
      showError(err.message);
    }
  };

  // Active review for current inspector view
  const currentSelectedReview = (analysis && selectedBoxIndex !== null && analysis.boxes[selectedBoxIndex])
    ? findReviewForBox(analysis.boxes[selectedBoxIndex])
    : null;

  // Render Landing Page if on route '/'
  if (route === '/') {
    return (
      <LandingPage
        onEnterStudio={() => navigateToStudio(false)}
        onTryDemo={() => navigateToStudio(true)}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Studio Header */}
      <header className="studio-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <a
            href="/#overview"
            className="btn-secondary"
            onClick={(e) => {
              e.preventDefault();
              navigateToSection('overview');
            }}
            style={{ padding: '4px 8px', fontSize: '0.75rem', gap: '5px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
            title="Return to Landing Page"
          >
            <ArrowLeft size={13} /> Home
          </a>
          <a
            href="/#about"
            className="btn-secondary"
            onClick={(e) => {
              e.preventDefault();
              navigateToSection('about');
            }}
            style={{ padding: '4px 8px', fontSize: '0.75rem', gap: '5px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
            title="About & Documentation"
          >
            About
          </a>
          <div
            className="brand-logo-shimmer"
            style={{ fontWeight: '700', fontSize: '1.15rem', color: 'var(--text-primary)', letterSpacing: '-0.02em', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            onClick={navigateToHome}
            title="Return to Landing Page"
          >
            <span className="brand-title">InscripLens</span> <span className="brand-tag" style={{ color: 'var(--accent-sandstone)', fontSize: '0.85rem', fontWeight: '500' }}>Studio</span>
          </div>
          {/* Merged Single Subtle Status Line */}
          <div className="header-status-line">
            {analysis ? (
              <>
                <span className="status-dot-active" />
                <span style={{ fontWeight: '600', color: 'var(--text-primary)' }}>{analysis.display_name}</span>
                <span className="status-sep">&middot;</span>
                <span>{analysis.width} &times; {analysis.height} px</span>
                <span className="status-sep">&middot;</span>
                <span>Local Workspace</span>
              </>
            ) : (
              <>
                <span className="status-dot-idle" />
                <span>Local Research Workspace</span>
                <span className="status-sep">&middot;</span>
                <span style={{ color: 'var(--text-subtle)' }}>No stone loaded</span>
              </>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
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
        </div>
      </header>

      {/* Main Studio Body */}
      <div className="studio-main">
        {/* Collapsible Sidebar (Icon rail when collapsed, state remembered) */}
        <nav className={`studio-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <button
            type="button"
            className="sidebar-toggle-btn"
            onClick={toggleSidebar}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          </button>

          <div className="sidebar-header-label" style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', letterSpacing: '0.08em', marginBottom: '8px' }}>
            NAVIGATION
          </div>

          <button
            className={`btn-secondary sidebar-nav-btn ${activeTab === 'studio' ? 'selected' : ''}`}
            style={{
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '6px',
              backgroundColor: activeTab === 'studio' ? 'var(--accent-subtle)' : 'transparent',
              borderColor: activeTab === 'studio' ? 'var(--accent-sandstone)' : 'transparent',
              color: activeTab === 'studio' ? 'var(--accent-sandstone)' : 'var(--text-primary)'
            }}
            onClick={() => setActiveTab('studio')}
            title="Epigraphy Studio"
          >
            <Layers size={15} />
            <span className="sidebar-text" style={{ marginLeft: '8px' }}>Epigraphy Studio</span>
          </button>

          <button
            className={`btn-secondary sidebar-nav-btn ${activeTab === 'history' ? 'selected' : ''}`}
            style={{
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '6px',
              backgroundColor: activeTab === 'history' ? 'var(--accent-subtle)' : 'transparent',
              borderColor: activeTab === 'history' ? 'var(--accent-sandstone)' : 'transparent',
              color: activeTab === 'history' ? 'var(--accent-sandstone)' : 'var(--text-primary)'
            }}
            onClick={() => setActiveTab('history')}
            title="Run History"
          >
            <History size={15} />
            <span className="sidebar-text" style={{ marginLeft: '8px' }}>Run History</span>
          </button>

          <button
            className={`btn-secondary sidebar-nav-btn ${activeTab === 'credits' ? 'selected' : ''}`}
            style={{
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '6px',
              backgroundColor: activeTab === 'credits' ? 'var(--accent-subtle)' : 'transparent',
              borderColor: activeTab === 'credits' ? 'var(--accent-sandstone)' : 'transparent',
              color: activeTab === 'credits' ? 'var(--accent-sandstone)' : 'var(--text-primary)'
            }}
            onClick={() => setActiveTab('credits')}
            title="Project Credits"
          >
            <FileText size={15} />
            <span className="sidebar-text" style={{ marginLeft: '8px' }}>Project Credits</span>
          </button>

          <a
            href="/#about"
            className="btn-secondary sidebar-nav-btn"
            style={{
              justifyContent: sidebarCollapsed ? 'center' : 'flex-start',
              marginBottom: '6px',
              backgroundColor: 'transparent',
              borderColor: 'transparent',
              color: 'var(--text-primary)',
              textDecoration: 'none',
              display: 'flex',
              alignItems: 'center'
            }}
            onClick={(e) => {
              e.preventDefault();
              navigateToSection('about');
            }}
            title="About & Documentation"
          >
            <Info size={15} />
            <span className="sidebar-text" style={{ marginLeft: '8px' }}>About & Docs</span>
          </a>

          <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.78rem', color: 'var(--text-muted)', justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }} title="Local Python Worker - No cloud OCR service used.">
              <Cpu size={14} className="text-sandstone" />
              <span className="sidebar-text">Local Worker</span>
            </div>
            <div className="sidebar-footer-text" style={{ fontSize: '0.72rem', color: 'var(--text-subtle)', marginTop: '6px', lineHeight: 1.4 }}>
              Developed by {SITE.developer}, {SITE.college} &middot; {SITE.year}
            </div>
          </div>
        </nav>

        {/* Center Content Area */}
        <main className="studio-content">
          {/* Friendly Error Banner */}
          {errorMessage && (
            <div style={{
              padding: '12px 20px',
              backgroundColor: '#241819',
              borderBottom: '1px solid #E06C75',
              color: '#EDEDEC',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <AlertCircle size={16} color="#E06C75" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Loading Banner */}
          {loading && (
            <div style={{
              padding: '12px 20px',
              backgroundColor: '#1E1B15',
              borderBottom: '1px solid #C9A66B',
              color: '#C9A66B',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#C9A66B' }}></span>
              {loadingMessage}
            </div>
          )}

          {activeTab === 'studio' && (
            analysis ? (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                <div className="studio-workspace">
                  {/* Central Canvas Panel */}
                  <div className="canvas-panel">
                    {/* Canvas Toolbar with controls */}
                    <div className="canvas-toolbar">
                      {/* Left: Wipe percentage & Candidate boxes toggle switch */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Sliders size={13} color="#C9A66B" />
                          <span>Curtain: <strong style={{ color: '#EDEDEC' }}>{Math.round(sliderPos)}%</strong></span>
                        </div>

                        <div style={{ width: '1px', height: '16px', backgroundColor: '#2A2A30' }} />

                        {/* Modern Toggle Switch for Candidate Boxes */}
                        <div
                          className="toggle-wrapper"
                          onClick={() => setShowBoxes(!showBoxes)}
                          role="switch"
                          aria-checked={showBoxes}
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === ' ' || e.key === 'Enter') {
                              e.preventDefault();
                              setShowBoxes(!showBoxes);
                            }
                          }}
                        >
                          <div className={`toggle-switch ${showBoxes ? 'active' : ''}`}>
                            <div className="toggle-thumb" />
                          </div>
                          <span style={{ fontSize: '0.78rem', color: showBoxes ? '#EDEDEC' : '#A8A29A' }}>
                            Boxes ({analysis.boxes.length})
                          </span>
                        </div>
                      </div>

                      {/* Center: Zoom & Fit Controls */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <button
                          className="tool-btn"
                          onClick={() => fitToViewport(true)}
                          title="Fit stone to available panel height"
                        >
                          <Maximize2 size={12} /> Fit
                        </button>
                        <button
                          className="tool-btn"
                          onClick={zoomTo100}
                          title="View at 100% original scale"
                        >
                          100%
                        </button>
                        <button
                          className="tool-btn"
                          onClick={zoomOut}
                          title="Zoom Out (-)"
                        >
                          <ZoomOut size={13} />
                        </button>
                        <span style={{ fontSize: '0.75rem', minWidth: '42px', textAlign: 'center', color: '#EDEDEC', fontFamily: 'monospace' }}>
                          {Math.round(scale * 100)}%
                        </span>
                        <button
                          className="tool-btn"
                          onClick={zoomIn}
                          title="Zoom In (+)"
                        >
                          <ZoomIn size={13} />
                        </button>
                      </div>

                      {/* Right: Primary Classify All Action & Progress */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {isClassifying ? (
                          <div className="progress-container">
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#C9A66B' }}>
                              <span>Classifying candidate regions...</span>
                              <span style={{ fontWeight: '600' }}>{classifyProgress} of {analysis.boxes.length}</span>
                            </div>
                            <div className="progress-track">
                              <div
                                className="progress-fill"
                                style={{ width: `${(classifyProgress / analysis.boxes.length) * 100}%` }}
                              />
                            </div>
                          </div>
                        ) : classifyComplete && batchRegions.length > 0 ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span className="pill pill-success">
                              <CheckCircle size={12} /> {batchRegions.length} Regions Classified
                            </span>
                            <button
                              className="btn-secondary"
                              style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                              onClick={runBatchRecognize}
                              title="Re-run batch recognition"
                            >
                              <RotateCcw size={11} /> Re-run
                            </button>
                          </div>
                        ) : (
                          <button
                            className="btn-primary"
                            style={{ padding: '5px 12px', fontSize: '0.78rem' }}
                            onClick={runBatchRecognize}
                            disabled={loading}
                          >
                            <Sparkles size={13} /> Classify All ({analysis.boxes.length} Regions)
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Interactive Zoom/Pan Viewport */}
                    <div
                      className={`canvas-viewport ${isPanning ? 'panning' : ''}`}
                      ref={viewportRef}
                      onMouseDown={handleViewportMouseDown}
                    >
                      {/* Transformed Stage */}
                      <div
                        className="canvas-stage"
                        style={{
                          transform: `translate(${pan.x}px, ${pan.y}px) scale(${scale})`,
                          transition: isTransitioning ? 'transform 0.3s cubic-bezier(0.2, 0, 0, 1)' : 'none',
                          width: `${analysis.width}px`,
                          height: `${analysis.height}px`
                        }}
                      >
                        <div
                          className="curtain-container"
                          ref={containerRef}
                          style={{
                            width: `${analysis.width}px`,
                            height: `${analysis.height}px`
                          }}
                        >
                          {/* Base: Raw Original Photograph */}
                          <img
                            src={analysis.image_url}
                            alt={`Raw photograph of historical inscription: ${analysis.display_name}`}
                            className="curtain-base-img"
                            width={analysis.width}
                            height={analysis.height}
                            style={{ width: `${analysis.width}px`, height: `${analysis.height}px` }}
                          />

                          {/* Overlay: Shilalekhya Mask */}
                          <div
                            className="curtain-overlay"
                            style={{ width: `${sliderPos}%` }}
                          >
                            <img
                              src={analysis.mask_url}
                              alt={`Binarized inscription mask generated by Shilalekhya U-Net for ${analysis.display_name}`}
                              className="curtain-overlay-img"
                              width={analysis.width}
                              height={analysis.height}
                              style={{ width: `${analysis.width}px`, height: `${analysis.height}px` }}
                            />
                          </div>

                          {/* Floating Labels */}
                          <div className="curtain-label curtain-label-mask">Mask</div>
                          <div className="curtain-label curtain-label-original">Original</div>

                          {/* Slider Handle (Keyboard Accessible & Draggable) */}
                          <div
                            className="curtain-handle"
                            style={{ left: `${sliderPos}%` }}
                            tabIndex={0}
                            role="slider"
                            aria-label="Mask and original image curtain comparison"
                            aria-valuenow={Math.round(sliderPos)}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            onMouseDown={handleCurtainHandleMouseDown}
                            onKeyDown={handleCurtainKeyDown}
                          >
                            <div className="curtain-handle-knob">
                              <Sliders size={14} />
                            </div>
                          </div>

                          {/* Candidate Boxes as Scalable SVG Overlay with Status Styling */}
                          {showBoxes && (
                            <svg
                              viewBox={`0 0 ${analysis.width} ${analysis.height}`}
                              className="svg-overlay"
                              style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                width: `${analysis.width}px`,
                                height: `${analysis.height}px`,
                                pointerEvents: 'none'
                              }}
                            >
                              {allCandidatesInfo.map((cand) => {
                                const isSelected = selectedBoxIndex === cand.idx;
                                const isHiddenByFilter = hideTiny && cand.isTiny;
                                if (isHiddenByFilter) return null;

                                const x = cand.bbox[0];
                                const y = cand.bbox[1];
                                const w = cand.w;
                                const h = cand.h;

                                let strokeColor = 'rgba(201, 166, 107, 0.65)';
                                let fillColor = 'rgba(201, 166, 107, 0.08)';

                                if (isSelected) {
                                  strokeColor = '#C9A66B';
                                  fillColor = 'rgba(201, 166, 107, 0.35)';
                                } else if (cand.status === 'corrected') {
                                  strokeColor = '#64B4F0';
                                  fillColor = 'rgba(100, 180, 240, 0.12)';
                                } else if (cand.status === 'reviewed') {
                                  strokeColor = '#5CB85C';
                                  fillColor = 'rgba(92, 184, 92, 0.12)';
                                } else if (cand.status === 'unpredicted') {
                                  strokeColor = 'rgba(168, 162, 154, 0.28)';
                                  fillColor = 'transparent';
                                }

                                return (
                                  <rect
                                    key={cand.idx}
                                    x={x}
                                    y={y}
                                    width={w}
                                    height={h}
                                    className={isSelected ? 'svg-box-selected' : 'svg-box'}
                                    opacity={cand.isTiny ? 0.38 : 1}
                                    style={{
                                      fill: fillColor,
                                      stroke: strokeColor,
                                      strokeWidth: isSelected ? Math.max(1.8, 2.5 / scale) : Math.max(1.0, 1.4 / scale),
                                      cursor: 'pointer',
                                      pointerEvents: 'all'
                                    }}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleSelectAndFocusBox(cand.idx);
                                    }}
                                  >
                                    <title>{`Candidate #${cand.idx + 1} (${cand.status})`}</title>
                                  </rect>
                                );
                              })}
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Inspector Panel */}
                  <aside className="inspector-panel card-spotlight">
                    <div className="inspector-header">
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', color: '#A8A29A', letterSpacing: '0.05em' }}>
                        GLYPH INSPECTOR
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#EDEDEC', marginTop: '2px' }}>
                        {selectedBoxIndex !== null ? `Candidate #${selectedBoxIndex + 1}` : 'Select a Region'}
                      </div>
                    </div>

                    {cropPrediction ? (
                      <div>
                        {/* Larger Glyph Crop Box (>= 160px with padding) */}
                        <div className="inspector-section" style={{ paddingBottom: '12px' }}>
                          <div className="inspector-crop-box">
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
                              {analysis.boxes[selectedBoxIndex][2] - analysis.boxes[selectedBoxIndex][0]} x {analysis.boxes[selectedBoxIndex][3] - analysis.boxes[selectedBoxIndex][1]} px
                            </span>
                          </div>

                          <div style={{ marginTop: '8px' }}>
                            <div style={{ fontSize: '0.72rem', color: '#A8A29A', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                              Predicted Source Transliteration
                            </div>
                            <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#C9A66B', letterSpacing: '-0.01em', lineHeight: 1.2 }}>
                              {cropPrediction.prediction}
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#7E7A75', marginTop: '2px' }}>
                              Model: Experimental recognizer
                            </div>
                          </div>
                        </div>

                        {/* Selectable Alternative Chips with Confidence Bars if Available */}
                        <div className="inspector-section">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <span style={{ fontSize: '0.78rem', fontWeight: '600', color: '#EDEDEC' }}>
                              Top Ranked Label Alternatives
                            </span>
                            <span style={{ fontSize: '0.68rem', color: '#7E7A75' }}>
                              Click to adopt as suggestion
                            </span>
                          </div>

                          <div className="alt-chips-container">
                            {cropPrediction.alternatives.map((alt, idx) => {
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
                            })}
                          </div>
                        </div>

                        {/* Verification & Expert Review Section */}
                        <div className="inspector-section">
                          <div style={{ fontSize: '0.78rem', fontWeight: '600', color: '#EDEDEC', marginBottom: '12px' }}>
                            Verification & Expert Review
                          </div>

                          {/* Clear Reviewed State Banner if already saved */}
                          {currentSelectedReview && (
                            <div className={`review-card ${currentSelectedReview.suggested_label ? 'reviewed-corrected' : 'reviewed-confirmed'}`}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600' }}>
                                  <CheckCircle size={14} color={currentSelectedReview.suggested_label ? '#64B4F0' : '#5CB85C'} />
                                  <span style={{ color: currentSelectedReview.suggested_label ? '#64B4F0' : '#5CB85C' }}>
                                    {currentSelectedReview.suggested_label ? 'Correction Recorded' : 'Verified Without Correction'}
                                  </span>
                                </div>
                                <span style={{ fontSize: '0.7rem', color: '#7E7A75' }}>
                                  {currentSelectedReview.created ? new Date(currentSelectedReview.created).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Saved'}
                                </span>
                              </div>

                              {currentSelectedReview.suggested_label && (
                                <div style={{ fontSize: '0.82rem', color: '#EDEDEC', marginBottom: '4px' }}>
                                  <span style={{ color: '#A8A29A' }}>Corrected Label: </span>
                                  <strong style={{ color: '#64B4F0', fontSize: '1rem' }}>{currentSelectedReview.suggested_label}</strong>
                                </div>
                              )}

                              {currentSelectedReview.reviewer && (
                                <div style={{ fontSize: '0.75rem', color: '#A8A29A' }}>
                                  Reviewer: <strong style={{ color: '#EDEDEC' }}>{currentSelectedReview.reviewer}</strong>
                                </div>
                              )}

                              {currentSelectedReview.note && (
                                <div style={{ fontSize: '0.75rem', color: '#7E7A75', marginTop: '4px', fontStyle: 'italic' }}>
                                  "{currentSelectedReview.note}"
                                </div>
                              )}
                            </div>
                          )}

                          {/* Review Form (Behaviour unchanged) */}
                          <form onSubmit={handleSaveReview}>
                            <div style={{ marginBottom: '10px' }}>
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
                            </div>

                            <div style={{ marginBottom: '10px' }}>
                              <label style={{ fontSize: '0.75rem', color: '#A8A29A', display: 'block', marginBottom: '4px' }}>
                                Reviewer Initials / Name
                              </label>
                              <input
                                type="text"
                                value={reviewer}
                                onChange={(e) => setReviewer(e.target.value)}
                                placeholder="e.g. Epigraphist"
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
                            </div>

                            <button
                              type="submit"
                              className="btn-primary"
                              style={{ width: '100%', marginTop: '8px' }}
                            >
                              <Save size={14} /> Save Review Record
                            </button>

                            {saveSuccess && (
                              <div style={{ color: '#5CB85C', fontSize: '0.78rem', marginTop: '8px', textAlign: 'center' }}>
                                Review record saved to local database.
                              </div>
                            )}
                          </form>
                        </div>
                      </div>
                    ) : (
                      <div style={{ padding: '32px 16px', textAlign: 'center', color: '#A8A29A', fontSize: '0.85rem' }}>
                        Click any detected bounding box on the inscription canvas to inspect character predictions.
                      </div>
                    )}
                  </aside>
                </div>

                {/* Bottom Glyph Gallery Strip with Filters, Tiny Region Toggle & Status Chips */}
                <div className="gallery-strip">
                  <div className="gallery-strip-header">
                    {/* Left: Filter Buttons */}
                    <div className="filter-group">
                      <span style={{ fontSize: '0.72rem', fontWeight: '700', color: '#7E7A75', textTransform: 'uppercase', marginRight: '4px' }}>
                        Filter:
                      </span>
                      <button
                        className={`filter-chip ${filterTab === 'all' ? 'active' : ''}`}
                        onClick={() => setFilterTab('all')}
                      >
                        All ({counts.all})
                      </button>
                      <button
                        className={`filter-chip ${filterTab === 'predicted' ? 'active' : ''}`}
                        onClick={() => setFilterTab('predicted')}
                      >
                        Predicted ({counts.predicted})
                      </button>
                      <button
                        className={`filter-chip ${filterTab === 'reviewed' ? 'active' : ''}`}
                        onClick={() => setFilterTab('reviewed')}
                      >
                        Reviewed ({counts.reviewed})
                      </button>
                    </div>

                    {/* Right: Hide tiny regions toggle and keyboard navigation guide */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div
                        className="toggle-wrapper"
                        onClick={() => setHideTiny(!hideTiny)}
                        role="switch"
                        aria-checked={hideTiny}
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === ' ' || e.key === 'Enter') {
                            e.preventDefault();
                            setHideTiny(!hideTiny);
                          }
                        }}
                      >
                        <div className={`toggle-switch ${hideTiny ? 'active' : ''}`} style={{ width: '32px', height: '18px' }}>
                          <div className="toggle-thumb" style={{ width: '12px', height: '12px' }} />
                        </div>
                        <span style={{ fontSize: '0.74rem', color: hideTiny ? '#EDEDEC' : '#7E7A75' }}>
                          Hide tiny &lt;10px ({counts.tiny})
                        </span>
                      </div>

                      <div style={{ width: '1px', height: '14px', backgroundColor: '#28282F' }} />

                      <span style={{ fontSize: '0.7rem', color: '#7E7A75' }}>
                        Arrow keys to navigate
                      </span>
                    </div>
                  </div>

                  {/* Horizontal Scrollable Gallery Chips */}
                  <div className="gallery-chips" ref={galleryStripRef}>
                    {visibleCandidates.map((cand) => {
                      const isSelected = selectedBoxIndex === cand.idx;

                      return (
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
                      );
                    })}

                    {visibleCandidates.length === 0 && (
                      <div style={{ color: '#7E7A75', fontSize: '0.8rem', padding: '16px' }}>
                        No candidate regions match the current filter.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              /* Empty State */
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                padding: '40px'
              }}>
                <div style={{
                  maxWidth: '520px',
                  backgroundColor: '#1B1B1F',
                  border: '1px dashed #2A2A30',
                  borderRadius: '12px',
                  padding: '40px',
                  textAlign: 'center'
                }}>
                  <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'rgba(201, 166, 107, 0.15)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#C9A66B', marginBottom: '16px' }}>
                    <Layers size={24} />
                  </div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#EDEDEC', marginBottom: '8px' }}>
                    Historical Inscription Studio
                  </h2>
                  <p style={{ fontSize: '0.88rem', color: '#A8A29A', lineHeight: 1.5, marginBottom: '24px' }}>
                    Begin by loading the public Nagavara demonstration stone (8th-century hero stone with 133 candidate regions) or uploading an inscription photograph.
                  </p>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '12px' }}>
                    <button className="btn-primary" onClick={loadDemoStone} disabled={loading}>
                      <Sparkles size={14} /> Try Demo Stone (Nagavara)
                    </button>
                    <button className="btn-secondary" onClick={() => fileInputRef.current?.click()} disabled={loading}>
                      <Upload size={14} /> Upload Image
                    </button>
                  </div>
                </div>
              </div>
            )
          )}

          {/* History View */}
          {activeTab === 'history' && (
            <div style={{ padding: '32px', overflowY: 'auto', flex: 1, backgroundColor: 'var(--bg-base)' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: '600', marginBottom: '16px', color: 'var(--text-primary)' }}>
                Local Analysis History
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {historyList.map(item => (
                  <div
                    key={item.id}
                    className="history-row card-spotlight"
                    style={{
                      padding: '16px',
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '600', color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                        {item.display_name}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Analysis Record · {item.created ? new Date(item.created).toLocaleDateString() : 'Recorded'}
                      </div>
                    </div>
                    <span className="pill pill-sandstone">Analyzed Locally</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Credits View */}
          {activeTab === 'credits' && (
            <div style={{ padding: '32px', maxWidth: '800px', overflowY: 'auto', flex: 1, backgroundColor: 'var(--bg-base)' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: '600', marginBottom: '16px', color: 'var(--text-primary)' }}>
                Project Credits & Licence Attribution
              </h2>

              <div style={{ padding: '20px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '10px', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
                  Engineering Contributions
                </h3>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '12px' }}>
                  InscripLens contributes dataset filtering and provenance records, controlled model comparisons, candidate-region detection, expert review workflows, and local analysis history. No new OCR architecture is claimed.
                </p>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                  The Shilalekhya pretrained model performs binarization enhancement. EpiSAM supplies public images and annotations. Standard libraries provide classifier and interface components.
                </p>
              </div>

              {credits && credits.components.map((comp, idx) => (
                <div key={idx} className="credit-row card-spotlight" style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: '8px', marginBottom: '12px' }}>
                  <div style={{ fontWeight: '600', color: 'var(--accent-sandstone)', fontSize: '0.95rem' }}>
                    {comp.name}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    License: {comp.license} {comp.author ? `· Author: ${comp.author}` : ''}
                  </div>
                  {comp.acknowledgement && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-subtle)', marginTop: '4px' }}>
                      {comp.acknowledgement}
                    </div>
                  )}
                  <a
                    href={comp.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '0.8rem', color: 'var(--accent-sandstone)', display: 'inline-block', marginTop: '8px' }}
                  >
                    View Source Repository →
                  </a>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
