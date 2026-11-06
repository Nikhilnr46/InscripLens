/**
 * SavedComparisonsDrawer: Slide-over drawer presenting saved glyph comparisons.
 *
 * Provides:
 * - Tabs: "This run" and "All runs" with count badges
 * - Summary bar: Outcome counts (Improved, Worse, Unchanged, Unknown)
 * - Items: Candidate number, dual thumbnails, dual first predictions (Script-aware),
 *   outcome badge, tentative reading, timestamp, "Open", and "Delete" (with confirmation)
 * - "Download JSON" split menu ("This run" or "All saved")
 * - Storage usage warning banner with "Download JSON now" suggestion
 */

import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  X,
  Download,
  Trash2,
  FolderOpen,
  AlertTriangle,
  ChevronDown,
  Layers,
  ArrowRight,
  Check
} from 'lucide-react';
import {
  listComparisons,
  deleteComparison,
  downloadComparisonsJson,
  getStorageUsage
} from './store';
import { formatDisplayLabel } from '../utils/kannadaConverter';
import './compare.css';

export default function SavedComparisonsDrawer({
  isOpen,
  onClose,
  currentRunId,
  scriptMode = 'kannada',
  modernLetters = false,
  onOpenCandidate
}) {
  const [activeTab, setActiveTab] = useState('thisRun'); // 'thisRun' | 'allRuns'
  const [comparisons, setComparisons] = useState([]);
  const [downloadMenuOpen, setDownloadMenuOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [storageStatus, setStorageStatus] = useState({ isNearlyFull: false, usedBytes: 0 });
  const menuRef = useRef(null);

  // Reload comparisons list whenever drawer opens or active tab/currentRunId changes
  const reloadData = () => {
    try {
      const all = listComparisons();
      setComparisons(all);
      const usage = getStorageUsage();
      setStorageStatus(usage);
    } catch {
      setComparisons([]);
    }
  };

  useEffect(() => {
    if (isOpen) {
      reloadData();
      setConfirmDeleteId(null);
      setDownloadMenuOpen(false);
    }
  }, [isOpen, currentRunId]);

  // Close download menu on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setDownloadMenuOpen(false);
      }
    };
    if (downloadMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [downloadMenuOpen]);

  // Handle Escape key to close drawer
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Filter comparisons according to active tab
  const filteredList = useMemo(() => {
    if (activeTab === 'thisRun') {
      return comparisons.filter((c) => c.run_id === currentRunId);
    }
    return comparisons;
  }, [comparisons, activeTab, currentRunId]);

  const thisRunCount = useMemo(() => {
    return comparisons.filter((c) => c.run_id === currentRunId).length;
  }, [comparisons, currentRunId]);

  const allRunsCount = comparisons.length;

  // Outcome statistics for the active tab
  const outcomeCounts = useMemo(() => {
    const counts = { improved: 0, worse: 0, unchanged: 0, unknown: 0 };
    filteredList.forEach((c) => {
      const outcome = c.outcome || 'unknown';
      if (counts[outcome] != null) {
        counts[outcome]++;
      } else {
        counts.unknown++;
      }
    });
    return counts;
  }, [filteredList]);

  // Deletion handler
  const handleDelete = (id) => {
    deleteComparison(id);
    setConfirmDeleteId(null);
    reloadData();
  };

  if (!isOpen) return null;

  return (
    <div
      className="saved-drawer-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="Saved comparisons drawer"
      onClick={onClose}
    >
      <aside
        className="saved-drawer"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="saved-drawer-header">
          <div className="saved-drawer-title">
            <Layers size={16} color="var(--accent-sandstone, #C9A66B)" />
            <span>Saved Comparisons</span>
          </div>

          <div className="saved-drawer-header-actions">
            {/* Download JSON split dropdown */}
            <div className="download-dropdown-wrap" ref={menuRef}>
              <button
                type="button"
                className="btn-secondary saved-download-btn"
                onClick={() => setDownloadMenuOpen(!downloadMenuOpen)}
                title="Download comparisons as clean JSON"
                aria-haspopup="true"
                aria-expanded={downloadMenuOpen}
              >
                <Download size={13} />
                <span>Download JSON</span>
                <ChevronDown size={12} />
              </button>

              {downloadMenuOpen && (
                <div className="download-dropdown-menu" role="menu">
                  <button
                    type="button"
                    role="menuitem"
                    className="download-menu-item"
                    onClick={() => {
                      setDownloadMenuOpen(false);
                      downloadComparisonsJson(currentRunId);
                    }}
                    disabled={thisRunCount === 0}
                  >
                    <span>This run ({thisRunCount})</span>
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    className="download-menu-item"
                    onClick={() => {
                      setDownloadMenuOpen(false);
                      downloadComparisonsJson(null);
                    }}
                    disabled={allRunsCount === 0}
                  >
                    <span>All saved ({allRunsCount})</span>
                  </button>
                </div>
              )}
            </div>

            {/* Close Drawer Button */}
            <button
              type="button"
              className="saved-drawer-close-btn"
              onClick={onClose}
              title="Close saved comparisons (Esc)"
              aria-label="Close drawer"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Storage Warning if Nearly Full (>4MB) */}
        {storageStatus.isNearlyFull && (
          <div className="saved-storage-warning">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={14} color="#D97706" />
              <span>Storage nearly full. Download your comparisons as JSON to prevent data loss.</span>
            </div>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => downloadComparisonsJson(null)}
              style={{ height: '24px', fontSize: '0.7rem', padding: '0 8px', marginTop: '4px' }}
            >
              <Download size={11} /> Download JSON now
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="saved-tabs-row" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'thisRun'}
            className={`saved-tab ${activeTab === 'thisRun' ? 'active' : ''}`}
            onClick={() => setActiveTab('thisRun')}
          >
            <span>This run</span>
            <span className="saved-tab-badge">{thisRunCount}</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'allRuns'}
            className={`saved-tab ${activeTab === 'allRuns' ? 'active' : ''}`}
            onClick={() => setActiveTab('allRuns')}
          >
            <span>All runs</span>
            <span className="saved-tab-badge">{allRunsCount}</span>
          </button>
        </div>

        {/* Outcome Summary Bar */}
        <div className="saved-summary-bar" aria-label="Outcome statistics">
          <span className="summary-item improved">
            <span className="summary-dot improved" /> Improved: {outcomeCounts.improved}
          </span>
          <span className="summary-item worse">
            <span className="summary-dot worse" /> Worse: {outcomeCounts.worse}
          </span>
          <span className="summary-item unchanged">
            <span className="summary-dot unchanged" /> Unchanged: {outcomeCounts.unchanged}
          </span>
          <span className="summary-item unknown">
            <span className="summary-dot unknown" /> Unknown: {outcomeCounts.unknown}
          </span>
        </div>

        {/* Comparison Cards List / Empty State */}
        <div className="saved-cards-scroll">
          {filteredList.length === 0 ? (
            <div className="saved-empty-container">
              <Layers size={32} color="var(--border-subtle, #333)" />
              <div className="saved-empty-title">No comparisons saved yet</div>
              <p className="saved-empty-desc">
                {activeTab === 'thisRun'
                  ? 'Redraw and compare candidate glyphs to build a comparison history for this inscription.'
                  : 'No comparisons saved in this browser. Use the glyph inspector to redraw boxes and compare model predictions.'}
              </p>
            </div>
          ) : (
            filteredList.map((item) => {
              const autoDisp = formatDisplayLabel(
                item.automatic?.prediction || '',
                scriptMode,
                modernLetters
              );
              const redrawnDisp = formatDisplayLabel(
                item.redrawn?.prediction || '',
                scriptMode,
                modernLetters
              );

              const isCurrentRun = item.run_id === currentRunId;
              const isConfirmingDelete = confirmDeleteId === item.id;

              return (
                <div key={item.id} className="saved-card">
                  {/* Card Header */}
                  <div className="saved-card-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="saved-candidate-pill">
                        Candidate #{item.candidate_number}
                      </span>
                      <span className={`compare-outcome-badge outcome-${item.outcome}`}>
                        {item.outcome}
                      </span>
                      {!isCurrentRun && (
                        <span className="saved-run-tag" title={`Run ID: ${item.run_id}`}>
                          Other run
                        </span>
                      )}
                    </div>
                    <span className="saved-card-timestamp">
                      {item.saved_at
                        ? new Date(item.saved_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            month: 'short',
                            day: 'numeric'
                          })
                        : ''}
                    </span>
                  </div>

                  {/* Dual Comparison Grid */}
                  <div className="saved-card-grid">
                    {/* Automatic Column */}
                    <div className="saved-card-col">
                      <div className="saved-col-label automatic">Automatic</div>
                      <div className="saved-card-crop">
                        {item.automatic_thumbnail ? (
                          <img
                            src={item.automatic_thumbnail}
                            alt={`Automatic crop for candidate #${item.candidate_number}`}
                          />
                        ) : (
                          <div className="saved-card-crop-placeholder">
                            <span>{item.automatic?.bbox ? `${item.automatic.bbox[2] - item.automatic.bbox[0]}x${item.automatic.bbox[3] - item.automatic.bbox[1]}` : 'Auto'}</span>
                          </div>
                        )}
                      </div>
                      <div className="saved-col-pred">
                        <span className="saved-glyph">{autoDisp.primary}</span>
                        {autoDisp.secondary && (
                          <span className="saved-sub-glyph">({autoDisp.secondary})</span>
                        )}
                      </div>
                      {item.automatic?.confidence != null && (
                        <div className="saved-conf-tag">
                          {Math.round(item.automatic.confidence * 100)}%
                        </div>
                      )}
                    </div>

                    <div className="saved-col-arrow">
                      <ArrowRight size={14} color="var(--text-subtle, #7E7A75)" />
                    </div>

                    {/* Redrawn Column */}
                    <div className="saved-card-col">
                      <div className="saved-col-label redrawn">Redrawn</div>
                      <div className="saved-card-crop">
                        {item.redrawn_thumbnail ? (
                          <img
                            src={item.redrawn_thumbnail}
                            alt={`Redrawn crop for candidate #${item.candidate_number}`}
                          />
                        ) : (
                          <div className="saved-card-crop-placeholder">
                            <span>{item.redrawn?.bbox ? `${item.redrawn.bbox[2] - item.redrawn.bbox[0]}x${item.redrawn.bbox[3] - item.redrawn.bbox[1]}` : 'Redrawn'}</span>
                          </div>
                        )}
                      </div>
                      <div className="saved-col-pred">
                        <span className="saved-glyph">{redrawnDisp.primary}</span>
                        {redrawnDisp.secondary && (
                          <span className="saved-sub-glyph">({redrawnDisp.secondary})</span>
                        )}
                      </div>
                      {item.redrawn?.confidence != null && (
                        <div className="saved-conf-tag">
                          {Math.round(item.redrawn.confidence * 100)}%
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Tentative Reading Line */}
                  <div className="saved-reading-row">
                    <span className="saved-reading-label">Reading:</span>
                    {item.proposed_reading?.text ? (
                      <span className="saved-reading-val">
                        &lsquo;{item.proposed_reading.text}&rsquo;
                        {item.proposed_reading.script === 'roman' && (
                          <span style={{ color: 'var(--text-subtle)', marginLeft: '4px', fontSize: '0.68rem' }}>
                            (Roman)
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="saved-reading-empty">No tentative reading entered</span>
                    )}
                  </div>

                  {/* Actions Footer */}
                  <div className="saved-card-footer">
                    {isConfirmingDelete ? (
                      <div className="saved-delete-confirm">
                        <span style={{ fontSize: '0.72rem', color: '#E06C75' }}>
                          Delete this comparison?
                        </span>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            type="button"
                            className="btn-danger saved-action-btn"
                            onClick={() => handleDelete(item.id)}
                          >
                            Delete
                          </button>
                          <button
                            type="button"
                            className="btn-secondary saved-action-btn"
                            onClick={() => setConfirmDeleteId(null)}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="btn-secondary saved-action-btn"
                          onClick={() => {
                            if (isCurrentRun && onOpenCandidate) {
                              onOpenCandidate(item.candidate_index, item);
                              onClose();
                            }
                          }}
                          disabled={!isCurrentRun}
                          title={
                            isCurrentRun
                              ? `Open candidate #${item.candidate_number} in Studio`
                              : 'Cannot open candidate from a different run'
                          }
                        >
                          <FolderOpen size={12} /> Open
                        </button>

                        <button
                          type="button"
                          className="btn-secondary saved-action-btn"
                          onClick={() => setConfirmDeleteId(item.id)}
                          title="Delete this comparison record"
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </div>
  );
}
