/**
 * In-memory file store for temporary handoff between /import and /studio.
 * Strictly in-memory: never serializes to localStorage, sessionStorage, or disk.
 */

let pendingFile: File | null = null;

export function setPendingFile(file: File | null): void {
  pendingFile = file;
}

export function getPendingFile(): File | null {
  return pendingFile;
}

export function clearPendingFile(): void {
  pendingFile = null;
}
