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
  ChevronLeft,
  ChevronDown,
  Download
} from 'lucide-react';
import LandingPage from './pages/LandingPage.jsx';
import ThemeToggle from './components/ThemeToggle.tsx';
import { SITE } from './config/site.ts';
import { initSiteInteractions } from './utils/interactions.ts';
import { formatDisplayLabel } from './utils/kannadaConverter';

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

  // Collapsible sidebar state (auto-collapses below 1500px, remembers user manual preference, supports url override)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      if (sp.get('sidebar') === 'open') return false;
      if (sp.get('sidebar') === 'collapsed') return true;
      const saved = localStorage.getItem('inscriplens_sidebar_collapsed');
      if (saved !== null) {
        return saved === 'true';
      }
    } catch {}
    return typeof window !== 'undefined' ? window.innerWidth < 1500 : true;
  });

  // URL theme override support for testing and direct linking
  useEffect(() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      const t = sp.get('theme');
      if (t === 'light' || t === 'dark') {
        document.documentElement.setAttribute('data-theme', t);
      }
    } catch {}
  }, []);

  const toggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('inscriplens_sidebar_collapsed', String(next));
        localStorage.setItem('inscriplens_sidebar_manual', 'true');
      } catch {}
      return next;
    });
  };

  // Auto-collapse sidebar below 1500px unless user manually chose a preference
  useEffect(() => {
    const handleResize = () => {
      try {
        const hasManual = localStorage.getItem('inscriplens_sidebar_manual') === 'true';
        if (!hasManual) {
          setSidebarCollapsed(window.innerWidth < 1500);
        }
      } catch {}
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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
  const [highAccuracy, setHighAccuracy] = useState(false);
  // Script display mode (Kannada default vs Roman), saved in localStorage with try/catch
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
  const inspectorRef = useRef(null);
  const predictRequestIdRef = useRef(0);
  const autoPredictedAnalysisIdRef = useRef(null);
  const isDraggingCurtain = useRef(false);
  const panStartRef = useRef(null);

  const canvasPanelRef = useRef(null);
  const [panelWidth, setPanelWidth] = useState(1200);
  const [viewDropdownOpen, setViewDropdownOpen] = useState(false);
  const viewDropdownRef = useRef(null);

  const [cropTimedOut, setCropTimedOut] = useState(false);
  const cropTimeoutRef = useRef(null);
  const cropAbortControllerRef = useRef(null);

  // Measure canvas panel container width for responsive toolbar
  useEffect(() => {
    if (!canvasPanelRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect) {
          setPanelWidth(entry.contentRect.width);
        }
      }
    });
    observer.observe(canvasPanelRef.current);
    return () => observer.disconnect();
  }, [analysis]);

  // Close view dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (viewDropdownRef.current && !viewDropdownRef.current.contains(e.target)) {
        setViewDropdownOpen(false);
      }
    };
    if (viewDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [viewDropdownOpen]);

  const isCompactView = panelWidth < 1100;
  const isUltraCompactView = panelWidth < 900;

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

    let uncertain = false;
    let modelsAgree = null;

    if (review) {
      if (review.suggested_label && review.suggested_label.trim() !== '') {
        status = 'corrected';
        label = review.suggested_label;
      } else {
        status = 'reviewed';
        label = review.prediction || 'Reviewed';
      }
      confidence = review.confidence ?? null;
      uncertain = review.uncertain ?? false;
      modelsAgree = review.models_agree ?? null;
    } else {
      const batchMatch = batchRegions.find(r => r.candidate === idx + 1);
      const cached = predictionCache[idx];
      const activeCrop = (selectedBoxIndex === idx && cropPrediction) ? cropPrediction.prediction : null;
      const pred = batchMatch ? batchMatch.predicted_source_label : (typeof cached === 'object' ? cached?.prediction : (cached || activeCrop));

      if (pred) {
        status = 'predicted';
        label = pred;
        confidence = batchMatch?.confidence ?? (selectedBoxIndex === idx ? cropPrediction?.confidence : (typeof cached === 'object' ? cached?.confidence : null));
        uncertain = batchMatch?.uncertain ?? (selectedBoxIndex === idx ? cropPrediction?.uncertain : (typeof cached === 'object' ? cached?.uncertain : false));
        modelsAgree = batchMatch?.models_agree ?? (selectedBoxIndex === idx ? cropPrediction?.models_agree : (typeof cached === 'object' ? cached?.models_agree : null));
      } else {
        status = 'unpredicted';
        label = null;
        confidence = null;
        uncertain = false;
        modelsAgree = null;
      }
    }

    return { idx, bbox, w, h, isTiny, status, label, confidence, uncertain, modelsAgree, review };
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
      }
      if (data.fallback_note) {
        showError(data.fallback_note);
      }
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Auto-load demo stone on mount if url contains demo=1
  useEffect(() => {
    if (window.location.search.includes('demo=1') && !analysis) {
      loadDemoStone();
    }
  }, []);

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
      }
      if (data.fallback_note) {
        showError(data.fallback_note);
      }
    } catch (err) {
      showError(err.message);
    } finally {
      setLoading(false);
    }
  };

    // Predict selected crop region with tiny check and 8s timeout guard
  const predictBox = async (boxIndex, overrideAnalysisId, overrideBbox) => {
    const currentAnalysisId = overrideAnalysisId || analysis?.id;
    const boxes = analysis?.boxes;
    const bbox = overrideBbox || (boxes && boxIndex !== null ? boxes[boxIndex] : null);
    if (!currentAnalysisId || boxIndex === null || !bbox) return;

    setSelectedBoxIndex(boxIndex);

    // Clear any previous crop timeout timer and in-flight abort controller
    if (cropTimeoutRef.current) {
      clearTimeout(cropTimeoutRef.current);
      cropTimeoutRef.current = null;
    }
    if (cropAbortControllerRef.current) {
      cropAbortControllerRef.current.abort();
      cropAbortControllerRef.current = null;
    }

    const w = bbox[2] - bbox[0];
    const h = bbox[3] - bbox[1];
    if (w < 10 || h < 10) {
      setCropPrediction(null);
      setPredictingCrop(false);
      setCropError(null);
      setCropTimedOut(false);
      return;
    }

    setCropPrediction(prev => (prev?.candidateIndex === boxIndex ? prev : null));
    setPredictingCrop(true);
    setCropError(null);
    setCropTimedOut(false);

    const requestId = ++predictRequestIdRef.current;
    const controller = new AbortController();
    cropAbortControllerRef.current = controller;

    // 8-second timeout guard: cancel skeleton and display retry button
    cropTimeoutRef.current = setTimeout(() => {
      if (requestId === predictRequestIdRef.current) {
        controller.abort();
        setPredictingCrop(false);
        setCropTimedOut(true);
        setCropError('Character preview took longer than 8 seconds to respond.');
      }
    }, 8000);

    try {
      const res = await fetch('/api/predict-crop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: currentAnalysisId, bbox }),
        signal: controller.signal
      });

      if (cropTimeoutRef.current) {
        clearTimeout(cropTimeoutRef.current);
        cropTimeoutRef.current = null;
      }

      if (requestId !== predictRequestIdRef.current) return;

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Character prediction could not be completed.');
      }
      const data = await res.json();

      if (requestId === predictRequestIdRef.current) {
        setCropTimedOut(false);
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
        if (err.name !== 'AbortError') {
          setCropError(err.message || 'Crop preview could not be loaded.');
        }
      }
    } finally {
      if (cropTimeoutRef.current) {
        clearTimeout(cropTimeoutRef.current);
        cropTimeoutRef.current = null;
      }
      if (requestId === predictRequestIdRef.current) {
        setPredictingCrop(false);
      }
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

  // Auto-scroll Glyph Inspector to top on candidate selection change
  useEffect(() => {
    if (inspectorRef.current) {
      if (typeof inspectorRef.current.scrollTo === 'function') {
        inspectorRef.current.scrollTo({ top: 0, behavior: 'auto' });
      } else {
        inspectorRef.current.scrollTop = 0;
      }
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
    if (analysis && selectedBoxIndex !== null && autoPredictedAnalysisIdRef.current !== analysis.id) {
      autoPredictedAnalysisIdRef.current = analysis.id;
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

      // Refresh inspector alternatives for focused candidate
      if (selectedBoxIndex !== null) {
        predictBox(selectedBoxIndex);
      }
    } catch (err) {
      clearInterval(progressTimer);
      showError(err.message);
    } finally {
      setIsClassifying(false);
    }
  };

  // Derived state for Glyph Inspector
  const selectedBox = (analysis?.boxes && selectedBoxIndex !== null) ? analysis.boxes[selectedBoxIndex] : null;
  const selectedBoxW = selectedBox ? selectedBox[2] - selectedBox[0] : 0;
  const selectedBoxH = selectedBox ? selectedBox[3] - selectedBox[1] : 0;
  const isSelectedTiny = selectedBox ? (selectedBoxW < 10 || selectedBoxH < 10) : false;

  // Active review for current inspector view
  const currentSelectedReview = selectedBox ? findReviewForBox(selectedBox) : null;

  const knownCandidateLabel = (() => {
    if (selectedBoxIndex === null) return null;
    if (currentSelectedReview) {
      return currentSelectedReview.suggested_label || currentSelectedReview.prediction || 'Reviewed';
    }
    const batchMatch = batchRegions.find(r => r.candidate === selectedBoxIndex + 1);
    if (batchMatch?.predicted_source_label) {
      return batchMatch.predicted_source_label;
    }
    const cachedVal = predictionCache[selectedBoxIndex];
    return (typeof cachedVal === 'object' ? cachedVal?.prediction : cachedVal) || null;
  })();

  const isMatchingPrediction = Boolean(
    cropPrediction &&
    cropPrediction.candidateIndex === selectedBoxIndex &&
    selectedBoxIndex !== null
  );

  // Save character review (behaviour unchanged)
  const handleSaveReview = async (e) => {
    e.preventDefault();
    if (!analysis || selectedBoxIndex === null || !analysis.boxes[selectedBoxIndex]) return;
    const currentBox = analysis.boxes[selectedBoxIndex];
    const currentPrediction = isMatchingPrediction ? cropPrediction.prediction : knownCandidateLabel;
    const modelSha = isMatchingPrediction ? cropPrediction.model_sha256 : (status?.model_sha256 || '');
    if (!currentPrediction) return;

    try {
      const res = await fetch('/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          run_id: analysis.id,
          bbox: currentBox,
          prediction: currentPrediction,
          model: 'Experimental recognizer',
          model_sha256: modelSha,
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0, overflow: 'hidden', whiteSpace: 'nowrap' }}>
          <a
            href="/#overview"
            className="btn-secondary"
            onClick={(e) => {
              e.preventDefault();
              navigateToSection('overview');
            }}
            style={{ padding: '4px 8px', fontSize: '0.75rem', gap: '5px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', flexShrink: 0, whiteSpace: 'nowrap' }}
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
            style={{ padding: '4px 8px', fontSize: '0.75rem', gap: '5px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', flexShrink: 0, whiteSpace: 'nowrap' }}
            title="About & Documentation"
          >
            About
          </a>
          <div
            className="brand-logo-shimmer"
            style={{ fontWeight: '700', fontSize: '1.15rem', color: 'var(--text-primary)', letterSpacing: '-0.02em', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', flexShrink: 0, whiteSpace: 'nowrap' }}
            onClick={navigateToHome}
            title="Return to Landing Page"
          >
            <span className="brand-title">InscripLens</span> <span className="brand-tag" style={{ color: 'var(--accent-sandstone)', fontSize: '0.85rem', fontWeight: '500' }}>Studio</span>
          </div>

          {/* Merged Single Subtle Status Line with Truncated Stone Name */}
          <div className="header-status-line">
            {analysis ? (
              <>
                <span className="status-dot-active" style={{ flexShrink: 0 }} />
                <span
                  className="header-status-name"
                  style={{ fontWeight: '600', color: 'var(--text-primary)' }}
                  title={analysis.display_name}
                >
                  {analysis.display_name}
                </span>
                <span className="status-sep" style={{ flexShrink: 0 }}>&middot;</span>
                <span style={{ flexShrink: 0 }}>{analysis.width} &times; {analysis.height} px</span>
                <span className="status-sep" style={{ flexShrink: 0 }}>&middot;</span>
                <span style={{ flexShrink: 0 }}>Local Workspace</span>
              </>
            ) : (
              <>
                <span className="status-dot-idle" style={{ flexShrink: 0 }} />
                <span style={{ flexShrink: 0 }}>Local Research Workspace</span>
                <span className="status-sep" style={{ flexShrink: 0 }}>&middot;</span>
                <span style={{ color: 'var(--text-subtle)', flexShrink: 0 }}>No stone loaded</span>
              </>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0, whiteSpace: 'nowrap' }}>
          {/* High accuracy mode switch with single-row layout and info tooltip */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
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
              style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <div className={`toggle-switch ${highAccuracy ? 'active' : ''}`} style={{ width: '28px', height: '16px' }}>
                <div className="toggle-thumb" style={{ width: '10px', height: '10px' }} />
              </div>
              <span style={{ fontSize: '0.76rem', color: highAccuracy ? 'var(--accent-sandstone)' : 'var(--text-muted)', fontWeight: highAccuracy ? '600' : '500', whiteSpace: 'nowrap' }}>
                High accuracy
              </span>
            </div>
            <span
              title="Finds more faint strokes. Slower, and may add a few false strokes."
              aria-label="Finds more faint strokes. Slower, and may add a few false strokes."
              style={{ display: 'inline-flex', alignItems: 'center', color: 'var(--text-subtle)', cursor: 'help' }}
            >
              <Info size={13} />
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
            style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
          >
            <Upload size={14} /> Upload Photograph
          </button>
          <button
            className="btn-primary btn-magnetic"
            onClick={loadDemoStone}
            disabled={loading}
            style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
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
                  {/* Central Canvas Panel with container query ref */}
                  <div className="canvas-panel" ref={canvasPanelRef}>
                    {/* Canvas Toolbar with directly visible Kannada script switch */}
                    <div className="canvas-toolbar">
                      {/* Left Group: Curtain, Boxes toggle, Mode badge, Mask */}
                      <div className="toolbar-group-left">
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap', minWidth: '95px' }}>
                          <Sliders size={13} color="#C9A66B" />
                          <span>Curtain: <strong style={{ color: 'var(--text-primary)' }}>{Math.round(sliderPos)}%</strong></span>
                        </div>

                        <div className="toolbar-sep" />

                        {/* Toggle Switch for Candidate Boxes */}
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
                          style={{ minWidth: '95px', whiteSpace: 'nowrap' }}
                        >
                          <div className={`toggle-switch ${showBoxes ? 'active' : ''}`}>
                            <div className="toggle-thumb" />
                          </div>
                          <span style={{ fontSize: '0.78rem', color: showBoxes ? 'var(--text-primary)' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                            Boxes ({analysis.boxes.length})
                          </span>
                        </div>

                        <div className="toolbar-sep" />

                        {/* Mode badge */}
                        <span
                          className={`pill ${analysis.mode === 'high_accuracy' ? 'pill-sandstone' : 'pill-neutral'}`}
                          style={{ fontSize: '0.68rem', padding: '2px 8px', minWidth: '65px', textAlign: 'center', whiteSpace: 'nowrap' }}
                          title={analysis.mode === 'high_accuracy' ? 'Enhanced with multi-scale sliding window' : 'Enhanced with standard single-scale GPU'}
                        >
                          {analysis.mode_label || (analysis.mode === 'high_accuracy' ? 'High accuracy' : 'Standard')}
                        </span>

                        {/* Mask download button */}
                        <a
                          href={analysis.mask_url}
                          download={`mask_${analysis.id}.png`}
                          className="tool-btn"
                          title="Download enhanced binary mask image"
                          style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px', minWidth: '60px', whiteSpace: 'nowrap' }}
                        >
                          <Download size={12} /> Mask
                        </a>
                      </div>

                      {/* Middle Group: Kannada Script Toggle & Modern letters (ALWAYS DIRECTLY VISIBLE ON TOOLBAR) */}
                      <div className="toolbar-group-middle">
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: '500' }}>Script:</span>
                        <div style={{ display: 'flex', alignItems: 'center', backgroundColor: 'var(--bg-base)', borderRadius: '5px', padding: '2px', border: '1px solid var(--border-subtle)' }}>
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
                              color: scriptMode === 'kannada' ? '#121214' : 'var(--text-muted)',
                              fontWeight: scriptMode === 'kannada' ? '600' : '400',
                              cursor: 'pointer',
                              fontFamily: "'Noto Sans Kannada', sans-serif"
                            }}
                          >
                            Kannada
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
                              color: scriptMode === 'roman' ? '#121214' : 'var(--text-muted)',
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
                            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', minWidth: '105px', whiteSpace: 'nowrap' }}
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
                            <span style={{ fontSize: '0.72rem', color: modernLetters ? 'var(--text-primary)' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                              Modern letters
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Right Group: Fit & Zoom Controls (Always visible) */}
                      <div className="toolbar-group-right">
                        <button
                          className="tool-btn"
                          onClick={() => fitToViewport(true)}
                          title="Fit stone to available panel height"
                          style={{ minWidth: '45px', whiteSpace: 'nowrap' }}
                        >
                          <Maximize2 size={12} /> Fit
                        </button>
                        <button
                          className="tool-btn"
                          onClick={zoomTo100}
                          title="View at 100% original scale"
                          style={{ minWidth: '45px', whiteSpace: 'nowrap' }}
                        >
                          100%
                        </button>
                        <button
                          className="tool-btn"
                          onClick={zoomOut}
                          title="Zoom Out (-)"
                          style={{ minWidth: '28px' }}
                        >
                          <ZoomOut size={13} />
                        </button>
                        <span style={{ fontSize: '0.75rem', minWidth: '42px', textAlign: 'center', color: 'var(--text-primary)', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                          {Math.round(scale * 100)}%
                        </span>
                        <button
                          className="tool-btn"
                          onClick={zoomIn}
                          title="Zoom In (+)"
                          style={{ minWidth: '28px' }}
                        >
                          <ZoomIn size={13} />
                        </button>
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
                  <aside className="inspector-panel card-spotlight" ref={inspectorRef}>
                    <div className="inspector-header">
                      <div style={{ fontSize: '0.75rem', fontWeight: '700', textTransform: 'uppercase', color: '#A8A29A', letterSpacing: '0.05em' }}>
                        GLYPH INSPECTOR
                      </div>
                      <div style={{ fontSize: '1.1rem', fontWeight: '600', color: '#EDEDEC', marginTop: '2px' }}>
                        {selectedBoxIndex !== null ? `Candidate #${selectedBoxIndex + 1}` : 'Select a Region'}
                      </div>
                    </div>

                    {selectedBoxIndex !== null ? (
                      <div>
                        {/* Larger Glyph Crop Box (>= 160px with padding) */}
                        <div className="inspector-section" style={{ paddingBottom: '12px' }}>
                          <div className="inspector-crop-box">
                            {isSelectedTiny ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', color: '#A8A29A', textAlign: 'center' }}>
                                <span className="tiny-tag" style={{ fontSize: '0.72rem', padding: '2px 8px', marginBottom: '6px' }}>
                                  Too small to read
                                </span>
                                <span style={{ fontSize: '0.7rem', color: '#7E7A75' }}>
                                  Region is {selectedBoxW} &times; {selectedBoxH} px (&lt; 10&times;10 px limit)
                                </span>
                              </div>
                            ) : cropTimedOut ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', color: '#D97706', textAlign: 'center' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '4px' }}>
                                  Crop preview timed out
                                </span>
                                <span style={{ fontSize: '0.68rem', color: '#7E7A75', marginBottom: '8px' }}>
                                  Request took longer than 8 seconds.
                                </span>
                                <button
                                  className="btn-secondary"
                                  onClick={() => predictBox(selectedBoxIndex)}
                                  style={{ padding: '3px 10px', fontSize: '0.72rem', gap: '4px', height: '24px' }}
                                >
                                  <RotateCcw size={11} /> Retry
                                </button>
                              </div>
                            ) : cropError ? (
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', color: '#D97706', textAlign: 'center' }}>
                                <span style={{ fontSize: '0.75rem', fontWeight: '600', marginBottom: '4px' }}>
                                  Crop preview unavailable
                                </span>
                                <span style={{ fontSize: '0.68rem', color: '#7E7A75', marginBottom: '8px' }}>
                                  {cropError}
                                </span>
                                <button
                                  className="btn-secondary"
                                  onClick={() => predictBox(selectedBoxIndex)}
                                  style={{ padding: '3px 10px', fontSize: '0.72rem', gap: '4px', height: '24px' }}
                                >
                                  <RotateCcw size={11} /> Retry
                                </button>
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
                          </div>

                          {(() => {
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
                          })()}
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
                            ) : predictingCrop ? (
                              <div className="skeleton-pulse" style={{ display: 'flex', gap: '8px', width: '100%' }}>
                                <div className="alt-chip" style={{ width: '64px', height: '34px', backgroundColor: 'var(--bg-elevated)', opacity: 0.6, cursor: 'default' }}>
                                  <span style={{ visibility: 'hidden' }}>---</span>
                                </div>
                                <div className="alt-chip" style={{ width: '64px', height: '34px', backgroundColor: 'var(--bg-elevated)', opacity: 0.6, cursor: 'default' }}>
                                  <span style={{ visibility: 'hidden' }}>---</span>
                                </div>
                                <div className="alt-chip" style={{ width: '64px', height: '34px', backgroundColor: 'var(--bg-elevated)', opacity: 0.6, cursor: 'default' }}>
                                  <span style={{ visibility: 'hidden' }}>---</span>
                                </div>
                              </div>
                            ) : (
                              <div style={{ padding: '8px 12px', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', border: '1px dashed var(--border-subtle)', color: 'var(--text-subtle)', fontSize: '0.75rem', width: '100%' }}>
                                Alternatives unavailable
                              </div>
                            )}
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

                              {currentSelectedReview.suggested_label && (() => {
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
                              })()}

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

                    {/* Right: Classification status, Re-run, Hide tiny, and arrow navigation */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', whiteSpace: 'nowrap' }}>
                      {/* Classification Status / Classify All / Re-run moved from toolbar */}
                      {isClassifying ? (
                        <div className="progress-container" style={{ minWidth: '160px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#C9A66B' }}>
                            <span>Classifying...</span>
                            <span style={{ fontWeight: '600' }}>{classifyProgress} of {analysis.boxes.length}</span>
                          </div>
                          <div className="progress-track" style={{ height: '3px' }}>
                            <div
                              className="progress-fill"
                              style={{ width: `${(classifyProgress / analysis.boxes.length) * 100}%` }}
                            />
                          </div>
                        </div>
                      ) : classifyComplete && batchRegions.length > 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span className="pill pill-success" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                            <CheckCircle size={11} /> {batchRegions.length} regions classified
                          </span>
                          <button
                            className="btn-secondary"
                            style={{ padding: '2px 8px', fontSize: '0.7rem', height: '22px', gap: '4px' }}
                            onClick={runBatchRecognize}
                            title="Re-run batch recognition"
                          >
                            <RotateCcw size={10} /> Re-run
                          </button>
                        </div>
                      ) : (
                        <button
                          className="btn-primary"
                          style={{ padding: '3px 10px', fontSize: '0.74rem', height: '24px', whiteSpace: 'nowrap', gap: '5px' }}
                          onClick={runBatchRecognize}
                          disabled={loading}
                        >
                          <Sparkles size={12} /> Classify All ({analysis.boxes.length})
                        </button>
                      )}

                      <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-subtle)' }} />

                      {/* Hide tiny regions toggle */}
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
                        <div className={`toggle-switch ${hideTiny ? 'active' : ''}`} style={{ width: '28px', height: '16px' }}>
                          <div className="toggle-thumb" style={{ width: '10px', height: '10px' }} />
                        </div>
                        <span style={{ fontSize: '0.74rem', color: hideTiny ? 'var(--text-primary)' : 'var(--text-subtle)', whiteSpace: 'nowrap' }}>
                          Hide tiny &lt;10px ({counts.tiny})
                        </span>
                      </div>

                      <div style={{ width: '1px', height: '14px', backgroundColor: 'var(--border-subtle)' }} />

                      <span style={{ fontSize: '0.7rem', color: 'var(--text-subtle)', whiteSpace: 'nowrap' }}>
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

                          {(() => {
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
                          })()}

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', fontSize: '0.62rem', color: '#7E7A75' }}>
                            <span>{cand.w}x{cand.h}</span>
                            {cand.confidence != null && (
                              <span style={{ color: cand.uncertain ? '#D97706' : '#C9A66B', fontWeight: '600' }}>
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
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
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
                        {item.mode_label && ` · Mode: ${item.mode_label}`}
                      </div>
                      {item.fallback_note && (
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
                    </div>
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
