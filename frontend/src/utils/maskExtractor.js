/**
 * Connected-component bounding box extraction from binarized masks in the browser.
 * Matches outputs/segment_candidates.py behavior:
 * - Pixel intensity threshold > 127
 * - Component pixel area >= 12
 * - Width >= 3 px and Height >= 3 px
 * - Output format: [x1, y1, x2, y2]
 * - Sorted by y1 (top-to-bottom), then x1 (left-to-right)
 */

export async function extractCandidateBoxesFromMask(maskUrl) {
  if (!maskUrl) {
    return { boxes: [], width: 0, height: 0 };
  }

  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      try {
        const w = img.naturalWidth;
        const h = img.naturalHeight;
        if (!w || !h) {
          resolve({ boxes: [], width: 0, height: 0 });
          return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        if (!ctx) {
          resolve({ boxes: [], width: w, height: h });
          return;
        }

        ctx.drawImage(img, 0, 0);
        const imgData = ctx.getImageData(0, 0, w, h);
        const data = imgData.data;

        const visited = new Uint8Array(w * h);
        const boxes = [];
        const queueX = new Int32Array(w * h);
        const queueY = new Int32Array(w * h);

        for (let y = 0; y < h; y++) {
          for (let x = 0; x < w; x++) {
            const idx = y * w + x;
            if (data[idx * 4] > 127 && visited[idx] === 0) {
              let qHead = 0;
              let qTail = 0;
              queueX[qTail] = x;
              queueY[qTail] = y;
              qTail++;
              visited[idx] = 1;

              let minX = x;
              let maxX = x;
              let minY = y;
              let maxY = y;
              let count = 0;

              while (qHead < qTail) {
                const cx = queueX[qHead];
                const cy = queueY[qHead];
                qHead++;
                count++;

                if (cx < minX) minX = cx;
                if (cx > maxX) maxX = cx;
                if (cy < minY) minY = cy;
                if (cy > maxY) maxY = cy;

                // 8-connected neighborhood
                for (let dy = -1; dy <= 1; dy++) {
                  const ny = cy + dy;
                  if (ny < 0 || ny >= h) continue;
                  for (let dx = -1; dx <= 1; dx++) {
                    if (dx === 0 && dy === 0) continue;
                    const nx = cx + dx;
                    if (nx < 0 || nx >= w) continue;
                    const nIdx = ny * w + nx;
                    if (data[nIdx * 4] > 127 && visited[nIdx] === 0) {
                      visited[nIdx] = 1;
                      queueX[qTail] = nx;
                      queueY[qTail] = ny;
                      qTail++;
                    }
                  }
                }
              }

              const bw = maxX - minX + 1;
              const bh = maxY - minY + 1;
              if (count >= 12 && bw >= 3 && bh >= 3) {
                boxes.push([minX, minY, maxX + 1, maxY + 1]);
              }
            }
          }
        }

        boxes.sort((a, b) => (a[1] !== b[1] ? a[1] - b[1] : a[0] - b[0]));
        resolve({ boxes, width: w, height: h });
      } catch (err) {
        console.error('Failed to extract boxes from mask:', err);
        resolve({ boxes: [], width: img.naturalWidth || 0, height: img.naturalHeight || 0 });
      }
    };

    img.onerror = () => {
      resolve({ boxes: [], width: 0, height: 0 });
    };

    img.src = maskUrl;
  });
}

