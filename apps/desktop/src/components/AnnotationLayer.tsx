import { useRef, useState } from "react";
import { dragToRect, insidePage, noteRect, type PageRect } from "../viewer/annotation";
import type { AnnotationKind } from "../types";

interface Props {
  tool: AnnotationKind;
  /** CSS pixels per PDF point. */
  cssScale: number;
  /** Rectangle in displayed-page points (origin top-left). */
  onRect: (rect: PageRect) => void;
  /** Called when the gesture is cancelled (e.g. it left the page). */
  onCancel?: () => void;
}

/**
 * Transparent layer above one page that turns a drag (or a click for notes) into a page
 * rectangle. The gesture belongs to this page: leaving the page cancels it instead of
 * spilling the annotation onto the neighbouring page.
 */
export function AnnotationLayer({ tool, cssScale, onRect, onCancel }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);
  const [cur, setCur] = useState<{ x: number; y: number } | null>(null);

  const pos = (e: React.PointerEvent) => {
    const r = ref.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  const page = () => {
    const r = ref.current!.getBoundingClientRect();
    return { w: r.width, h: r.height };
  };

  const finish = (end: { x: number; y: number }) => {
    if (!start) return;
    const from = start;
    setStart(null);
    setCur(null);
    const p = page();
    if (!insidePage(end, p.w, p.h)) {
      onCancel?.();
      return;
    }
    if (tool === "note") {
      onRect(noteRect(end, cssScale));
      return;
    }
    const rect = dragToRect(from, end, cssScale);
    if (rect) onRect(rect);
  };

  const box =
    start && cur && tool !== "note"
      ? { left: Math.min(start.x, cur.x), top: Math.min(start.y, cur.y), width: Math.abs(cur.x - start.x), height: Math.abs(cur.y - start.y) }
      : null;

  return (
    <div
      ref={ref}
      className={`annot-layer tool-${tool}`}
      onPointerDown={(e) => {
        e.stopPropagation();
        ref.current?.setPointerCapture(e.pointerId);
        const p = pos(e);
        setStart(p);
        setCur(p);
      }}
      onPointerMove={(e) => {
        if (!start) return;
        const p = pos(e);
        const dims = page();
        if (!insidePage(p, dims.w, dims.h)) {
          setStart(null);
          setCur(null);
          onCancel?.();
          return;
        }
        setCur(p);
      }}
      onPointerUp={(e) => finish(pos(e))}
      onPointerCancel={() => {
        setStart(null);
        setCur(null);
        onCancel?.();
      }}
    >
      {box && <div className="annot-rubber" style={box} />}
    </div>
  );
}
