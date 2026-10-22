import { useCallback, useEffect, useImperativeHandle, useLayoutEffect, useMemo, useRef, useState } from "react";
import { AnnotationLayer } from "./AnnotationLayer";
import { PageSurface } from "./PageSurface";
import { BitmapCache } from "../viewer/cache";
import { useViewStateReporter } from "../viewer/useViewState";
import {
  type Anchor,
  type PageBox,
  PAGE_PADDING,
  anchorScrollTop,
  captureAnchor,
  computeLayout,
  dominantPage,
  visibleRange,
} from "../viewer/layout";
import type { AnnotationKind, DocInfo } from "../types";

export type ViewMode = "continuous" | "single";

export interface DocumentViewHandle {
  /** Scrolls the given page into view (continuous mode). */
  scrollToPage(index: number, align?: "start" | "center"): void;
  /** Scrolls so that a point of a page (displayed page points) is visible. */
  scrollToPoint(pageIndex: number, yPoints: number): void;
  /** Captures the reading position so a zoom can restore it. */
  captureAnchor(): Anchor | null;
  /** Current scroll offset. */
  scrollTop(): number;
  /** The page the viewport is currently on. */
  activePage(): number;
  /** Scrolls by a number of CSS pixels (used by auto-scroll). */
  scrollByPixels(dy: number): void;
  /** True when the viewport is at the top / bottom of the document. */
  atEdge(): "top" | "bottom" | null;
}

interface Props {
  doc: DocInfo;
  mode: ViewMode;
  /** CSS pixels per PDF point. */
  cssScale: number;
  revision: number;
  tool: AnnotationKind | null;
  /** Called when scrolling changes the active page (never triggers a scroll). */
  onActivePage: (index: number) => void;
  onAnnotRect: (pageIndex: number, rect: [number, number, number, number]) => void;
  onError?: (message: string) => void;
  /** Ctrl + wheel asks for a zoom step (positive = zoom out). */
  onZoomWheel?: (deltaY: number) => void;
  /** Search hits to highlight on the visible pages (displayed page space). */
  highlights?: { hits: import("../types").SearchHit[]; activeIndex: number };
  /** Called when the user scrolls or interacts, so auto-scroll can pause. */
  onUserInteract?: () => void;
  /** Reports the actual size of the document area (used for fit calculations). */
  onViewportSize?: (w: number, h: number) => void;
  /** Current zoom in percent (reported for diagnostics). */
  zoomPercent?: number;
  ref?: React.Ref<DocumentViewHandle>;
}

/**
 * Document viewport.
 *
 * "continuous": one vertical scroll container with all pages stacked; only the pages near the
 * viewport are rendered (virtualised), the remaining pages keep their exact size as empty space
 * so the document height never changes when a bitmap arrives.
 * "single": only the active page is shown.
 */
export function DocumentView({ doc, mode, cssScale, revision, tool, onActivePage, onAnnotRect, onError, onZoomWheel, onViewportSize, zoomPercent, highlights, onUserInteract, ref }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const cacheRef = useRef<BitmapCache | null>(null);
  if (!cacheRef.current) cacheRef.current = new BitmapCache(48);
  const cache = cacheRef.current;
  // Text runs are cached per document revision and page: re-fetching on every scroll is wasteful
  // and a stale run would keep an old selection box alive.
  const spanCacheRef = useRef<Map<string, import("../types").TextSpan[]>>(new Map());
  const spanCache = spanCacheRef.current;

  const [viewport, setViewport] = useState({ w: 800, h: 600 });
  const [scrollTop, setScrollTop] = useState(0);
  const anchorRef = useRef<Anchor | null>(null);
  const activeRef = useRef(0);
  const rafRef = useRef(0);
  const modeRef = useRef(mode);
  modeRef.current = mode;
  const zoomWheelRef = useRef(onZoomWheel);
  zoomWheelRef.current = onZoomWheel;

  const layout = useMemo(() => computeLayout(doc.pages, cssScale), [doc.pages, cssScale]);
  const boxes = layout.boxes;

  // The caches must not survive a document or revision change.
  useEffect(() => {
    cache.clear();
    spanCache.clear();
  }, [doc.doc_id, revision, cache, spanCache]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setViewport({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setViewport({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, [doc.doc_id, mode]);

  useEffect(() => {
    onViewportSize?.(viewport.w, viewport.h);
  }, [viewport.w, viewport.h, onViewportSize]);

  // Report the active page while scrolling (rAF throttled, without scrolling back).
  const reportActive = useCallback(
    (top: number) => {
      if (modeRef.current !== "continuous") return;
      const idx = dominantPage(boxes, top, viewport.h);
      if (idx >= 0 && idx !== activeRef.current) {
        activeRef.current = idx;
        onActivePage(idx);
      }
    },
    [boxes, viewport.h, onActivePage],
  );

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      onUserInteract?.();
      if (rafRef.current) return;
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = 0;
        const top = el.scrollTop;
        setScrollTop(top);
        reportActive(top);
      });
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("scroll", onScroll);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [reportActive]);

  // Restore the reading position after a zoom (anchor = page + relative offset).
  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    if (!anchor) return;
    anchorRef.current = null;
    const el = scrollRef.current;
    if (!el) return;
    const next = anchorScrollTop(boxes, anchor);
    el.scrollTop = next;
    setScrollTop(next);
    reportActive(next);
  }, [cssScale, boxes, reportActive]);

  const scrollToPage = useCallback(
    (index: number, align: "start" | "center" = "start") => {
      const box = boxes[index];
      if (!box) return;
      if (modeRef.current === "single") {
        activeRef.current = index;
        onActivePage(index);
        return;
      }
      const el = scrollRef.current;
      if (!el) return;
      const target = align === "center" ? box.top - Math.max(0, (viewport.h - box.cssHeight) / 2) : box.top - PAGE_PADDING;
      const clamped = Math.max(0, target);
      el.scrollTop = clamped;
      setScrollTop(clamped);
      reportActive(clamped);
    },
    [boxes, viewport.h, onActivePage, reportActive],
  );

  /** Scrolls so that a position (in displayed page points) of a page is visible. */
  const scrollToPoint = useCallback(
    (pageIndex: number, yPoints: number) => {
      const box = boxes[pageIndex];
      if (!box) return;
      const el = scrollRef.current;
      if (!el) return;
      const target = box.top + PAGE_PADDING + yPoints * cssScale - viewport.h * 0.4;
      const clamped = Math.max(0, target);
      el.scrollTop = clamped;
      setScrollTop(clamped);
      reportActive(clamped);
    },
    [boxes, cssScale, viewport.h, reportActive],
  );

  const scrollByPixels = useCallback((dy: number) => {
    const el = scrollRef.current;
    if (!el) return;
    const next = Math.max(0, Math.min(el.scrollHeight - el.clientHeight, el.scrollTop + dy));
    el.scrollTop = next;
    setScrollTop(next);
  }, []);

  const atEdge = useCallback((): "top" | "bottom" | null => {
    const el = scrollRef.current;
    if (!el) return null;
    if (el.scrollTop <= 1) return "top";
    if (el.scrollTop >= el.scrollHeight - el.clientHeight - 1) return "bottom";
    return null;
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      scrollToPage,
      scrollToPoint,
      scrollByPixels,
      atEdge,
      captureAnchor: () => captureAnchor(boxes, scrollRef.current?.scrollTop ?? 0),
      scrollTop: () => scrollRef.current?.scrollTop ?? 0,
      activePage: () => activeRef.current,
    }),
    [scrollToPage, scrollToPoint, scrollByPixels, atEdge, boxes],
  );

  // Report the viewport state (throttled) for diagnostics and automated UI tests.
  useViewStateReporter(scrollRef, () => {
    const el = scrollRef.current;
    const rendered = mode === "continuous" ? visible.map((b) => b.index) : singleIndex >= 0 ? [singleIndex] : [];
    return {
      mode,
      scrollTop: el?.scrollTop ?? 0,
      scrollHeight: el?.scrollHeight ?? 0,
      clientWidth: el?.clientWidth ?? 0,
      clientHeight: el?.clientHeight ?? 0,
      pageCount: doc.page_count,
      renderedPages: rendered,
      zoomPercent: zoomPercent ?? 0,
      activePage: activeRef.current,
    };
  }, true);

  // Ctrl + wheel zooms; plain wheel keeps the normal scrolling behaviour.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey || !zoomWheelRef.current) return;
      e.preventDefault();
      zoomWheelRef.current(e.deltaY);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const [rangeFirst, rangeLast] = useMemo(
    () => (mode === "continuous" ? visibleRange(boxes, scrollTop, viewport.h, 1) : [0, -1]),
    [mode, boxes, scrollTop, viewport.h],
  );

  const visible: PageBox[] = [];
  for (let i = Math.max(0, rangeFirst); i <= rangeLast && i < boxes.length; i++) visible.push(boxes[i]);
  const singleIndex = Math.min(Math.max(0, activeRef.current), Math.max(0, boxes.length - 1));
  const singleBox = mode === "single" ? boxes[singleIndex] : undefined;

  return (
    <div className={`doc-view mode-${mode}`} ref={scrollRef} tabIndex={0} aria-label="Area dokumen">
      {mode === "continuous" ? (
        <div className="doc-canvas" style={{ height: layout.totalHeight + PAGE_PADDING * 2, width: layout.contentWidth + PAGE_PADDING * 2 }}>
          {visible.map((box) => (
            <div
              key={box.index}
              className="page-slot"
              style={{ top: box.top + PAGE_PADDING, left: PAGE_PADDING, width: box.cssWidth, height: box.cssHeight }}
            >
              <PageSurface
                docId={doc.doc_id}
                revision={revision}
                page={doc.pages[box.index]}
                box={box}
                cssScale={cssScale}
                cache={cache}
                spans={spanCache.get(`${doc.doc_id}:${revision}:${box.index}`) ?? null}
                onSpans={(i, s) => {
                  if (spanCache.size > 400) spanCache.clear();
                  spanCache.set(`${doc.doc_id}:${revision}:${i}`, s);
                }}
                onError={onError}
              />
              {tool && <AnnotationLayer tool={tool} cssScale={cssScale} onRect={(rect) => onAnnotRect(box.index, rect)} />}
              {highlights && highlights.hits.some((h) => h.page === box.index) && (
                <div className="search-layer">
                  {highlights.hits
                    .map((h, i) => ({ h, i }))
                    .filter(({ h }) => h.page === box.index)
                    .map(({ h, i }) => (
                      <div
                        key={`${i}-${h.left}`}
                        className={`search-hit ${i === highlights.activeIndex ? "active" : ""}`}
                        style={{ left: h.left * cssScale, top: h.top * cssScale, width: h.width * cssScale, height: h.height * cssScale }}
                      />
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        singleBox && (
          <div className="doc-canvas single" style={{ width: layout.contentWidth + PAGE_PADDING * 2 }}>
            <div className="page-slot" style={{ left: PAGE_PADDING, width: singleBox.cssWidth, height: singleBox.cssHeight }}>
              <PageSurface
                docId={doc.doc_id}
                revision={revision}
                page={doc.pages[singleBox.index]}
                box={singleBox}
                cssScale={cssScale}
                cache={cache}
                spans={spanCache.get(`${doc.doc_id}:${revision}:${singleBox.index}`) ?? null}
                onSpans={(i, s) => {
                  if (spanCache.size > 400) spanCache.clear();
                  spanCache.set(`${doc.doc_id}:${revision}:${i}`, s);
                }}
                onError={onError}
              />
              {tool && <AnnotationLayer tool={tool} cssScale={cssScale} onRect={(rect) => onAnnotRect(singleBox.index, rect)} />}
            </div>
          </div>
        )
      )}
    </div>
  );
}
