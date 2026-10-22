import { useEffect, useMemo, useRef, useState } from "react";
import { textSpans } from "../api";
import { measureRun, spanTransform, transformCss } from "../viewer/geometry";
import type { TextSpan } from "../types";

interface Props {
  docId: number;
  revision: number;
  pageIndex: number;
  /** CSS pixels per PDF point. */
  cssScale: number;
  /** Already loaded spans (cache) - avoids a second backend round trip. */
  spans: TextSpan[] | null;
  onSpans: (pageIndex: number, spans: TextSpan[]) => void;
  /** Draws the measured boxes (debug only, never enabled in a user build). */
  debug?: boolean;
}

/**
 * Transparent text layer above the page bitmap: makes the text selectable and copyable
 * (the bitmap itself is not selectable).
 *
 * The layer never paints glyphs: the text is transparent, also while it is selected, so the
 * rendered page stays the only visible source of writing. Every run is positioned with the
 * box the engine measured in the PDF and corrected with the UI font metrics, so the selection
 * highlight follows the visible text instead of drifting.
 */
export function TextLayer({ docId, revision, pageIndex, cssScale, spans, onSpans, debug }: Props) {
  const [local, setLocal] = useState<TextSpan[] | null>(spans);
  const req = useRef(0);
  const layerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<CanvasRenderingContext2D | null>(null);

  useEffect(() => {
    if (spans) {
      setLocal(spans);
      return;
    }
    const my = ++req.current;
    let cancelled = false;
    textSpans(docId, pageIndex)
      .then((s) => {
        if (cancelled || my !== req.current) return;
        setLocal(s);
        onSpans(pageIndex, s);
      })
      .catch(() => {
        if (!cancelled) setLocal([]);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docId, revision, pageIndex, spans]);

  // One measuring context for the whole layer, using the font the layer actually renders with.
  useEffect(() => {
    const el = layerRef.current;
    if (!el) return;
    const style = window.getComputedStyle(el);
    const ctx = document.createElement("canvas").getContext("2d");
    if (ctx) {
      ctx.font = `${style.fontSize || "13px"} ${style.fontFamily}`;
      canvasRef.current = ctx;
    }
  }, [local]);

  const runs = useMemo(() => {
    if (!local) return [];
    const family = layerRef.current ? window.getComputedStyle(layerRef.current).fontFamily : "Segoe UI";
    return local.map((s) => {
      const box = {
        left: s.left * cssScale,
        top: s.top * cssScale,
        width: s.width * cssScale,
        height: s.height * cssScale,
      };
      const metrics = measureRun(canvasRef.current, s.text, Math.max(1, box.height), family);
      return { span: s, box, transform: spanTransform(box, metrics) };
    });
  }, [local, cssScale]);

  if (!local || local.length === 0) return null;
  return (
    <div className="text-layer" ref={layerRef} data-debug={debug ? "1" : undefined}>
      {runs.map(({ span, box, transform }, i) => (
        <span
          key={`${pageIndex}-${i}`}
          data-target-width={box.width.toFixed(2)}
          data-target-height={box.height.toFixed(2)}
          style={{
            left: box.left,
            top: box.top,
            width: box.width,
            height: box.height,
            fontSize: transform.fontSize,
            transform: transformCss(transform),
            transformOrigin: "0 0",
          }}
        >
          {span.text}
        </span>
      ))}
    </div>
  );
}
