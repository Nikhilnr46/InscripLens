/**
 * InscripLens Compare Module
 * Steps R1 & R2: API Client, Coordinate Mapping, Outcome Logic, Comparison Store,
 * and UI Components (RedrawOverlay, RedrawFloatingBar, CompareCard).
 */

export { predictCrop } from './apiClient';
export {
  screenToImage,
  imageToScreen,
  normalizeBbox,
  screenRectToImageBbox,
  imageBboxToScreenRect,
  extractTransform
} from './coordinates';
export {
  evaluateComparisonOutcome,
  findRankInAlternatives,
  normalizeToKannada,
  getAlternativeKannada
} from './outcome';
export {
  saveComparison,
  listComparisons,
  getComparison,
  deleteComparison,
  exportComparisons,
  downloadComparisonsJson,
  clearComparisons,
  getStorageUsage,
  COMPARISONS_STORAGE_KEY,
  CURRENT_SCHEMA_VERSION
} from './store';
export { createCropThumbnail, generateThumbnailFromUrl } from './thumbnail';

export { default as CompareCard } from './CompareCard';
export { default as RedrawOverlay } from './RedrawOverlay';
export { default as RedrawFloatingBar } from './RedrawFloatingBar';
export { default as SavedComparisonsDrawer } from './SavedComparisonsDrawer';
