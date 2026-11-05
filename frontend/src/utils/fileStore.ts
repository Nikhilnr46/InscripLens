/**
 * In-memory file store for temporary handoff between /import and /studio.
 * Strictly in-memory: never serializes to localStorage, sessionStorage, or disk.
 */

export interface RegionSelectionData {
  x: number;
  y: number;
  width: number;
  height: number;
  imageWidth: number;
  imageHeight: number;
  isWholeImage: boolean;
}

export interface HandoffPayload {
  file: File;
  originalFile?: File;
  selection?: RegionSelectionData;
  originalSize?: { width: number; height: number };
}

let pendingFile: File | null = null;
let originalFile: File | null = null;
let selectionData: RegionSelectionData | null = null;
let originalSize: { width: number; height: number } | null = null;

export function setPendingFile(file: File | null): void {
  pendingFile = file;
  originalFile = file;
  selectionData = null;
  originalSize = null;
}

export function setPendingHandoff(payload: HandoffPayload): void {
  pendingFile = payload.file;
  originalFile = payload.originalFile || payload.file;
  selectionData = payload.selection || null;
  originalSize = payload.originalSize || null;
}

export function getPendingFile(): File | null {
  return pendingFile;
}

export function getOriginalFile(): File | null {
  return originalFile;
}

export function getSelectionData(): RegionSelectionData | null {
  return selectionData;
}

export function getOriginalSize(): { width: number; height: number } | null {
  return originalSize;
}

export function clearPendingFile(): void {
  pendingFile = null;
}

export function clearHandoffStore(): void {
  pendingFile = null;
  originalFile = null;
  selectionData = null;
  originalSize = null;
}
