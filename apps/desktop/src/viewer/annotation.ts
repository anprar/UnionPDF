/**
 * Geometry of the annotation gesture.
 *
 * The gesture happens in CSS pixels inside one page; the result must be a rectangle in
 * *displayed page space* (origin top-left, PDF points, /Rotate already applied) so the
 * backend can convert it to PDF user space. The functions are pure so they can be unit
 * tested (`node --test src/viewer/annotation.test.ts`).
 */

export type PageRect = [number, number, number, number];

export interface DragPoint {
  x: number;
  y: number;
}

/** True when the pointer is still inside the page (with a small tolerance). */
export function insidePage(point: DragPoint, pageWidth: number, pageHeight: number, tolerance = 2): boolean {
  return (
    point.x >= -tolerance &&
    point.y >= -tolerance &&
    point.x <= pageWidth + tolerance &&
    point.y <= pageHeight + tolerance
  );
}

/**
 * Converts a drag into a page rectangle in points.
 * Returns null when the gesture is too small (a click, not a drag).
 */
export function dragToRect(start: DragPoint, end: DragPoint, cssScale: number): PageRect | null {
  if (!(cssScale > 0)) return null;
  const x0 = Math.min(start.x, end.x) / cssScale;
  const y0 = Math.min(start.y, end.y) / cssScale;
  const x1 = Math.max(start.x, end.x) / cssScale;
  const y1 = Math.max(start.y, end.y) / cssScale;
  if (x1 - x0 <= 2 / cssScale || y1 - y0 <= 2 / cssScale) return null;
  return [x0, y0, x1, y1];
}

/** A note is a small square anchored at the click position. */
export function noteRect(point: DragPoint, cssScale: number, sizePoints = 20): PageRect {
  const x = point.x / cssScale;
  const y = point.y / cssScale;
  return [x, y - sizePoints, x + sizePoints, y];
}
