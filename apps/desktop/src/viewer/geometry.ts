/**
 * Geometry of the page text layer.
 *
 * The text layer is invisible; it only exists so the user can select and copy text. For the
 * selection highlight to line up with the rendered page, the DOM box of every text run must
 * match the box the engine measured in the PDF. The DOM uses the UI font, so its metrics
 * differ from the PDF font - we measure the UI font with a canvas and correct the run with a
 * horizontal scale and a vertical offset. Both corrections are relative (no fixed pixel
 * offsets), so they stay correct at every zoom level and device pixel ratio.
 */

/** Target box of a text run, in CSS pixels. */
export interface TargetBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** Metrics of the UI font, measured with a canvas at the run's font size. */
export interface FontMetrics {
  /** Width of the run text when rendered with the UI font, in CSS pixels. */
  measuredWidth: number;
  /** Ascent above the baseline, in CSS pixels. */
  ascent: number;
  /** Descent below the baseline, in CSS pixels. */
  descent: number;
  /** Line box height used by the layer (font-size * line-height). */
  lineHeight: number;
}

export interface SpanTransform {
  /** Horizontal scale applied to the run (1 = the UI font already matches). */
  scaleX: number;
  /** Vertical offset in CSS pixels (negative = move up). */
  dy: number;
  /** Font size to render the run with. */
  fontSize: number;
}

/**
 * Computes the transform for one text run.
 *
 * - `scaleX` stretches the (invisible) run so its advance width equals the measured PDF width.
 * - `dy` centres the run's ink box on the target box: the DOM line box is taller than the ink
 *   box, so the ink box has to be shifted up by half of the difference.
 */
export function spanTransform(box: TargetBox, metrics: FontMetrics): SpanTransform {
  const fontSize = Math.max(1, box.height);
  // Without real measurements (no canvas, empty run) we cannot correct anything.
  if (metrics.measuredWidth <= 0.5 || metrics.ascent + metrics.descent <= 0) {
    return { scaleX: 1, dy: 0, fontSize };
  }
  const scaleX = box.width / metrics.measuredWidth;
  const inkHeight = metrics.ascent + metrics.descent;
  const leading = (metrics.lineHeight - inkHeight) / 2;
  return { scaleX, dy: -leading, fontSize };
}

/** CSS transform string for a run (scale about the left edge, vertical offset in px). */
export function transformCss(t: SpanTransform): string {
  const parts: string[] = [];
  if (Math.abs(t.dy) > 0.01) parts.push(`translateY(${t.dy.toFixed(2)}px)`);
  if (Math.abs(t.scaleX - 1) > 0.005) parts.push(`scaleX(${t.scaleX.toFixed(4)})`);
  return parts.length ? parts.join(" ") : "none";
}

/**
 * Measures a text run with the UI font.
 * Returns zero metrics when no canvas is available (then the run is rendered unscaled).
 */
export function measureRun(
  ctx: CanvasRenderingContext2D | null,
  text: string,
  fontSize: number,
  fontFamily: string,
): FontMetrics {
  if (!ctx) return { measuredWidth: 0, ascent: 0, descent: 0, lineHeight: fontSize };
  ctx.font = `${fontSize}px ${fontFamily}`;
  const m = ctx.measureText(text);
  const ascent = m.actualBoundingBoxAscent || fontSize * 0.8;
  const descent = m.actualBoundingBoxDescent || fontSize * 0.2;
  return {
    measuredWidth: m.width,
    ascent,
    descent,
    lineHeight: fontSize,
  };
}
