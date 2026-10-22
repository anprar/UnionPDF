/**
 * Local geometry diagnostics (development builds only).
 *
 * Enabled with the build flag VITE_UNIONPDF_DEBUG=1; the shipping build has no flag, so the
 * helper is never registered and nothing is shown. The result is a compact summary that the
 * automated UI test can read from the status bar, so the text layer can be checked without a
 * human eye: the layer must stay invisible (also while selected) and every run must sit on
 * the box the engine measured in the PDF.
 */

export interface GeometryDiagnostics {
  /** Computed color of the text layer (must be fully transparent). */
  layerColor: string;
  /** Computed color of the selection inside the layer (must be fully transparent). */
  selectionColor: string;
  /** Background of the selection (must be translucent, so the page below stays readable). */
  selectionBackground: string;
  /** Number of text runs in the layer. */
  runs: number;
  /** Largest horizontal deviation between the run box and the engine box, in percent. */
  maxWidthErrorPct: number;
  /** Largest vertical deviation between the run box and the engine box, in percent. */
  maxHeightErrorPct: number;
}

const TRANSPARENT = /rgba\(\s*0,\s*0,\s*0,\s*0\s*\)|transparent/;

export async function collectGeometryDiagnostics(): Promise<GeometryDiagnostics> {
  const layer = document.querySelector<HTMLElement>(".text-layer");
  const empty: GeometryDiagnostics = {
    layerColor: "none",
    selectionColor: "none",
    selectionBackground: "none",
    runs: 0,
    maxWidthErrorPct: 0,
    maxHeightErrorPct: 0,
  };
  if (!layer) return empty;

  const cs = getComputedStyle(layer);
  const span = layer.querySelector<HTMLElement>("span");
  const spanCs = span ? getComputedStyle(span) : null;

  // The ::selection rule is not reachable through getComputedStyle; read it from the sheets.
  let selColor = "none";
  let selBackground = "none";
  for (const sheet of Array.from(document.styleSheets)) {
    let rules: CSSRuleList | null = null;
    try {
      rules = sheet.cssRules;
    } catch {
      continue; // cross-origin sheet
    }
    if (!rules) continue;
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSStyleRule && rule.selectorText.includes("::selection")) {
        const s = rule.style;
        selColor = s.color || selColor;
        selBackground = s.backgroundColor || selBackground;
      }
    }
  }

  // Compare the run boxes with the boxes the engine delivered (kept as data attributes).
  let maxWidthErrorPct = 0;
  let maxHeightErrorPct = 0;
  const spans = Array.from(layer.querySelectorAll<HTMLElement>("span"));
  for (const s of spans) {
    const w = parseFloat(s.dataset.targetWidth ?? "0");
    const h = parseFloat(s.dataset.targetHeight ?? "0");
    const r = s.getBoundingClientRect();
    if (w > 0 && r.width > 0) {
      maxWidthErrorPct = Math.max(maxWidthErrorPct, Math.abs(r.width - w) / w * 100);
    }
    if (h > 0 && r.height > 0) {
      maxHeightErrorPct = Math.max(maxHeightErrorPct, Math.abs(r.height - h) / h * 100);
    }
  }

  return {
    layerColor: cs.color,
    selectionColor: selColor === "none" ? spanCs?.color ?? "none" : selColor,
    selectionBackground: selBackground,
    runs: spans.length,
    maxWidthErrorPct,
    maxHeightErrorPct,
  };
}

export function isTransparent(color: string): boolean {
  return TRANSPARENT.test(color.trim());
}
