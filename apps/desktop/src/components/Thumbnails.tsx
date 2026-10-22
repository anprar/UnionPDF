import { useEffect, useRef, useState } from "react";
import { renderPage } from "../api";
import type { PageInfo } from "../types";

const THUMB_CSS_WIDTH = 118;

function Thumb({ docId, page, revision, active, onSelect }: {
  docId: number;
  page: PageInfo;
  revision: number;
  active: boolean;
  onSelect: (i: number) => void;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [visible, setVisible] = useState(false);
  const cssH = Math.round((page.height / page.width) * THUMB_CSS_WIDTH);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver((entries) => setVisible(entries.some((e) => e.isIntersecting)), {
      rootMargin: "200px",
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return;
    let cancelled = false;
    const scale = (THUMB_CSS_WIDTH * (window.devicePixelRatio || 1)) / page.width;
    renderPage(docId, page.index, Math.max(0.05, scale))
      .then((r) => {
        const c = canvasRef.current;
        if (cancelled || !c) return;
        c.width = r.width;
        c.height = r.height;
        c.getContext("2d")?.putImageData(new ImageData(r.pixels, r.width, r.height), 0, 0);
      })
      .catch(() => {
        /* thumbnail failures are non-fatal; the main view reports errors */
      });
    return () => {
      cancelled = true;
    };
  }, [visible, docId, page.index, page.width, page.height, revision]);

  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ block: "nearest" });
  }, [active]);

  return (
    <button ref={ref} className={`thumb ${active ? "active" : ""}`} onClick={() => onSelect(page.index)} title={`Halaman ${page.index + 1}`}>
      <canvas ref={canvasRef} style={{ width: THUMB_CSS_WIDTH, height: cssH }} />
      <span>{page.index + 1}</span>
    </button>
  );
}

export function Thumbnails({ docId, pages, current, revision, onSelect }: {
  docId: number;
  pages: PageInfo[];
  current: number;
  revision: number;
  onSelect: (i: number) => void;
}) {
  return (
    <nav className="thumbnails" aria-label="Thumbnail halaman">
      {pages.map((p) => (
        <Thumb key={p.index} docId={docId} page={p} revision={revision} active={p.index === current} onSelect={onSelect} />
      ))}
    </nav>
  );
}
