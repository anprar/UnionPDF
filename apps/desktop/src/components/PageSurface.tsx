import { useEffect, useRef, useState } from "react";
import { MAX_RENDER_PIXELS, renderPage } from "../api";
import { TextLayer } from "./TextLayer";
import { BitmapCache } from "../viewer/cache";
import type { PageBox } from "../viewer/layout";
import type { PageInfo, TextSpan } from "../types";

interface Props {
  docId: number;
  revision: number;
  page: PageInfo;
  box: PageBox;
  /** CSS pixels per PDF point. */
  cssScale: number;
  cache: BitmapCache;
  /** Text runs of this page (shared cache in the parent). */
  spans?: TextSpan[] | null;
  onSpans?: (pageIndex: number, spans: TextSpan[]) => void;
  onError?: (message: string) => void;
}

/** One page: a placeholder with the exact size from the page metadata plus its bitmap. */
export function PageSurface({ docId, revision, page, box, cssScale, cache, spans, onSpans, onError }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [rendering, setRendering] = useState(false);
  const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;

  // Bitmap resolution is independent of the layout size.
  const maxScale = Math.sqrt(MAX_RENDER_PIXELS / Math.max(1, page.width * page.height));
  const deviceScale = Math.max(0.05, Math.min(cssScale * dpr, 8, maxScale * 0.98));
  const key = BitmapCache.key(docId, revision, page.index, deviceScale, page.rotation);

  useEffect(() => {
    let cancelled = false;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = (bitmap: ImageBitmap) => {
      if (cancelled) return;
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(bitmap, 0, 0);
      }
    };

    const cached = cache.get(key);
    if (cached) {
      draw(cached.bitmap);
      setRendering(false);
      return;
    }
    if (cache.isInflight(key)) {
      setRendering(true);
      return;
    }
    setRendering(true);
    const promise = (async (): Promise<import("../viewer/cache").BitmapCacheEntry | null> => {
      try {
        const r = await renderPage(docId, page.index, deviceScale);
        if (cancelled) return null;
        const bitmap = await createImageBitmap(new ImageData(r.pixels, r.width, r.height));
        const entry = { bitmap, width: r.width, height: r.height };
        cache.set(key, entry);
        draw(bitmap);
        return entry;
      } catch (e) {
        if (!cancelled) onError?.(e instanceof Error ? e.message : String(e));
        return null;
      } finally {
        if (!cancelled) setRendering(false);
      }
    })();
    cache.track(key, promise);
    return () => {
      cancelled = true;
    };
  }, [key, docId, page.index, deviceScale, cache, onError]);

  return (
    <div className="page-surface" data-page={page.index} style={{ width: box.cssWidth, height: box.cssHeight }}>
      <canvas ref={canvasRef} style={{ width: box.cssWidth, height: box.cssHeight }} aria-label={`Halaman ${page.index + 1}`} />
      <TextLayer
        docId={docId}
        revision={revision}
        pageIndex={page.index}
        cssScale={cssScale}
        spans={spans ?? null}
        onSpans={(i, s) => onSpans?.(i, s)}
      />
      {rendering && <div className="page-loading">Merender…</div>}
    </div>
  );
}
