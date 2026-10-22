/**
 * Layout of a document in continuous mode.
 *
 * All functions are pure so they can be unit tested without a browser
 * (`node --test src/viewer/layout.test.ts`).
 */

export interface PageSize {
  /** Displayed width in PDF points (after /Rotate). */
  width: number;
  /** Displayed height in PDF points (after /Rotate). */
  height: number;
}

export interface PageBox extends PageSize {
  index: number;
  /** Offset of the page inside the document, in CSS pixels. */
  top: number;
  left: number;
  cssWidth: number;
  cssHeight: number;
}

export interface Layout {
  boxes: PageBox[];
  /** Total height of the document (CSS pixels), including gaps. */
  totalHeight: number;
  /** Width of the widest page (CSS pixels). */
  contentWidth: number;
  /** Gap between pages (CSS pixels). */
  gap: number;
  scale: number;
}

export const PAGE_GAP = 16;
export const PAGE_PADDING = 24;

export function computeLayout(
  pages: PageSize[],
  scale: number,
  gap: number = PAGE_GAP,
): Layout {
  const boxes: PageBox[] = [];
  let top = 0;
  let contentWidth = 0;
  for (let i = 0; i < pages.length; i++) {
    const p = pages[i];
    const cssWidth = Math.max(1, Math.round(p.width * scale));
    const cssHeight = Math.max(1, Math.round(p.height * scale));
    boxes.push({ index: i, width: p.width, height: p.height, top, left: 0, cssWidth, cssHeight });
    top += cssHeight + gap;
    contentWidth = Math.max(contentWidth, cssWidth);
  }
  const totalHeight = pages.length > 0 ? top - gap : 0;
  return { boxes, totalHeight, contentWidth, gap, scale };
}

/** Index of the page that contains `y` (document coordinates), or -1 outside the document. */
export function pageAt(boxes: PageBox[], y: number): number {
  if (boxes.length === 0) return -1;
  if (y < 0) return 0;
  for (const b of boxes) {
    if (y < b.top + b.cssHeight) return b.index;
  }
  return boxes[boxes.length - 1].index;
}

/**
 * The page that dominates the viewport: the page containing the vertical centre of the
 * viewport. When the centre falls into the gap between two pages the page above the gap
 * wins, so the indicator never flickers while scrolling slowly.
 */
export function dominantPage(boxes: PageBox[], scrollTop: number, viewportHeight: number): number {
  if (boxes.length === 0) return -1;
  const centre = scrollTop + viewportHeight / 2;
  const idx = pageAt(boxes, centre);
  if (idx < 0) return 0;
  const box = boxes[idx];
  // The centre is in the gap above this page -> keep the page above active.
  if (centre < box.top) return Math.max(0, idx - 1);
  return idx;
}

/** Page range that should be rendered, including `overscan` pages on each side. */
export function visibleRange(boxes: PageBox[], scrollTop: number, viewportHeight: number, overscan = 1): [number, number] {
  if (boxes.length === 0) return [0, -1];
  const first = Math.max(0, pageAt(boxes, scrollTop) - overscan);
  const last = Math.min(boxes.length - 1, pageAt(boxes, scrollTop + viewportHeight) + overscan);
  return [first, last];
}

export interface Anchor {
  page: number;
  /** Relative position inside the page (0 = top, 1 = bottom). */
  ratio: number;
}

/** Captures the reading position as (page, relative offset) so it can be restored after a zoom. */
export function captureAnchor(boxes: PageBox[], scrollTop: number): Anchor | null {
  if (boxes.length === 0) return null;
  const idx = pageAt(boxes, scrollTop);
  const box = boxes[idx];
  if (!box) return null;
  const ratio = box.cssHeight > 0 ? (scrollTop - box.top) / box.cssHeight : 0;
  return { page: idx, ratio };
}

/** Scroll offset that keeps the anchored position at the same place. */
export function anchorScrollTop(boxes: PageBox[], anchor: Anchor): number {
  const box = boxes[anchor.page];
  if (!box) return 0;
  return Math.max(0, box.top + anchor.ratio * box.cssHeight);
}

/** Scale that makes a page of `width` points fit into `available` CSS pixels. */
export function fitWidthScale(pages: PageSize[], available: number): number {
  const widest = pages.reduce((m, p) => Math.max(m, p.width), 0);
  if (widest <= 0 || available <= 0) return 1;
  return available / widest;
}

/** Scale that makes the largest page fit into the given area. */
export function fitPageScale(pages: PageSize[], availableWidth: number, availableHeight: number): number {
  let scale = Infinity;
  for (const p of pages) {
    if (p.width <= 0 || p.height <= 0) continue;
    scale = Math.min(scale, availableWidth / p.width, availableHeight / p.height);
  }
  return Number.isFinite(scale) && scale > 0 ? scale : 1;
}
