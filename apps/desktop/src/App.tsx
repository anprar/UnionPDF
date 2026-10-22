import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { listen } from "@tauri-apps/api/event";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { ask, open, save } from "@tauri-apps/plugin-dialog";
import * as api from "./api";
import { PX_PER_PT, toApiError } from "./api";
import type { AnnotationKind, DocInfo, EngineStatus, FormField, OpResult, Preflight } from "./types";
import { Logo } from "./components/Logo";
import { CommandBar, StatusBar, TabBar, TitleBar, tabsFor, type TabId } from "./components/Chrome";
import { DocumentView, type DocumentViewHandle, type ViewMode } from "./components/DocumentView";
import { Sidebar } from "./components/Sidebar";
import { SearchBar } from "./components/SearchBar";
import { AutoScrollControl, type ScrollDirection } from "./components/AutoScrollControl";
import { BookmarkPanel } from "./components/BookmarkPanel";
import { MergeDialog } from "./components/MergeDialog";
import { SplitDialog } from "./components/SplitDialog";
import { ConvertDialog } from "./components/ConvertDialog";
import { useSearch } from "./components/SearchHighlights";
import { fitPageScale, fitWidthScale } from "./viewer/layout";
import { collectGeometryDiagnostics, isTransparent } from "./debug";

type FitMode = "width" | "page" | "custom";

interface Notice {
  kind: "error" | "success" | "info";
  title: string;
  checks?: string[];
  changes?: string[];
  limitations?: string[];
}
interface Job {
  id: string;
  label: string;
  stage: string;
}
interface Confirm {
  title: string;
  preflight: Preflight;
  resolve: (ok: boolean) => void;
}
interface TextPrompt {
  kind: AnnotationKind;
  rect: [number, number, number, number];
  page: number;
}

const PDF_FILTER = [{ name: "Dokumen PDF", extensions: ["pdf"] }];
const ZOOM_STEPS = [25, 33, 50, 67, 75, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400, 500];
const VIEW_MODE_KEY = "unionpdf.viewMode";

function suggestName(doc: DocInfo, suffix: string): string {
  const base = doc.file_name.replace(/\.pdf$/i, "");
  const dir = doc.path.slice(0, doc.path.length - doc.file_name.length);
  return `${dir}${base}${suffix}.pdf`;
}

function readStoredViewMode(): ViewMode {
  try {
    const v = localStorage.getItem(VIEW_MODE_KEY);
    return v === "single" ? "single" : "continuous";
  } catch {
    return "continuous";
  }
}

export default function App() {
  const [engine, setEngine] = useState<EngineStatus | null>(null);
  const [doc, setDoc] = useState<DocInfo | null>(null);
  const [current, setCurrent] = useState(0);
  const [mode, setMode] = useState<ViewMode>(readStoredViewMode);
  const [fit, setFit] = useState<FitMode>("width");
  const [zoom, setZoom] = useState(100);
  const [viewport, setViewport] = useState({ w: 800, h: 600 });
  const [notice, setNotice] = useState<Notice | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [extractOpen, setExtractOpen] = useState(false);
  const [selection, setSelection] = useState("");
  const [pageInput, setPageInput] = useState("1");
  const [confirm, setConfirm] = useState<Confirm | null>(null);
  const [tool, setTool] = useState<AnnotationKind | null>(null);
  const [textPrompt, setTextPrompt] = useState<TextPrompt | null>(null);
  const [promptText, setPromptText] = useState("");
  const [tab, setTab] = useState<TabId>("file");
  const [toolbarVisible, setToolbarVisible] = useState(true);
  const [searchOpen, setSearchOpen] = useState(false);
  const [autoScrollOpen, setAutoScrollOpen] = useState(false);
  const [autoScrollRunning, setAutoScrollRunning] = useState(false);
  const [autoScrollDir, setAutoScrollDir] = useState<ScrollDirection>("down");
  const [autoScrollSpeed, setAutoScrollSpeed] = useState(1);
  const [autoScrollPaused, setAutoScrollPaused] = useState(false);
  const [autoScrollAtEdge, setAutoScrollAtEdge] = useState(false);
  const autoScrollTimer = useRef<number | null>(null);
  const userScrollAt = useRef(0);
  // Auto-scroll IGNORES user interaction for a short window after its own scroll
  // (the scroll event arrives asynchronously, so a simple flag is not enough).
  const autoScrollUntil = useRef(0);
  const [bookmarksOpen, setBookmarksOpen] = useState(false);
  const [splitOpen, setSplitOpen] = useState(false);
  const [convertOpen, setConvertOpen] = useState(false);
  const [mergeOpen, setMergeOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [fields, setFields] = useState<FormField[] | null>(null);
  const [fieldsLoading, setFieldsLoading] = useState(false);
  const viewRef = useRef<DocumentViewHandle>(null);
  const dirtyRef = useRef(false);
  dirtyRef.current = !!doc?.dirty;
  const suppressScrollSync = useRef(false);

  const authoring = !!engine?.authoring_available;
  const search = useSearch(doc?.doc_id ?? null, doc?.revision ?? 0);
  const tabs = useMemo(() => tabsFor(doc, authoring), [doc, authoring]);

  const startupHandled = useRef(false);
  useEffect(() => {
    api
      .engineStatus()
      .then(async (st) => {
        setEngine(st);
        if (!st.available || startupHandled.current) return;
        startupHandled.current = true;
        const path = await api.startupFile();
        if (path) await openFile(path);
      })
      .catch((e) => setNotice({ kind: "error", title: toApiError(e).message }));
  }, []);

  useEffect(() => {
    const un = listen<{ job_id: string; stage: string }>("job-progress", (ev) => {
      setJob((j) => (j && j.id === ev.payload.job_id ? { ...j, stage: ev.payload.stage } : j));
    });
    return () => {
      un.then((f) => f());
    };
  }, []);

  useEffect(() => {
    const un = getCurrentWindow().onCloseRequested(async (event) => {
      if (dirtyRef.current && !(await confirmDiscard("Tutup UnionPDF"))) event.preventDefault();
    });
    return () => {
      un.then((f) => f());
    };
  }, []);

  // The active page follows the scroll; explicit navigation is marked so the two never fight.
  const onActivePage = useCallback((index: number) => {
    if (suppressScrollSync.current) {
      suppressScrollSync.current = false;
      return;
    }
    setCurrent(index);
  }, []);

  const page = doc?.pages[current];

  const cssScale = useMemo(() => {    if (!doc) return 1;
    const pad = 48;
    if (fit === "width") return Math.max(0.05, fitWidthScale(doc.pages, Math.max(120, viewport.w - pad)));
    if (fit === "page") return Math.max(0.05, fitPageScale(doc.pages, Math.max(120, viewport.w - pad), Math.max(120, viewport.h - pad)));
    return (zoom / 100) * PX_PER_PT;
  }, [doc, fit, zoom, viewport]);

  const zoomPercent = Math.round((cssScale / PX_PER_PT) * 100);
  useEffect(() => setPageInput(String(current + 1)), [current]);

  const showError = useCallback((e: unknown, title?: string) => {
    const err = toApiError(e);
    setNotice({ kind: "error", title: title ?? err.message, limitations: title ? [err.message] : undefined });
  }, []);

  const onRenderError = useCallback((m: string) => setNotice({ kind: "error", title: "Gagal merender halaman", limitations: [m] }), []);

  async function confirmDiscard(action: string): Promise<boolean> {
    if (!dirtyRef.current) return true;
    return ask(`Dokumen memiliki perubahan yang belum disimpan.\n\n${action} tanpa menyimpan? Perubahan akan hilang.`, {
      title: "Perubahan belum disimpan",
      kind: "warning",
      okLabel: "Buang perubahan",
      cancelLabel: "Batal",
    });
  }

  function confirmPreflight(title: string, preflight: Preflight): Promise<boolean> {
    return new Promise((resolve) => setConfirm({ title, preflight, resolve }));
  }

  async function runTask<T>(label: string, fn: (jobId: string) => Promise<T>, errorTitle?: string): Promise<T | null> {
    const id = crypto.randomUUID();
    setJob({ id, label, stage: "Memulai" });
    try {
      return await fn(id);
    } catch (e) {
      const err = toApiError(e);
      if (err.code === "cancelled") setNotice({ kind: "info", title: `${label} dibatalkan.`, changes: [err.message] });
      else showError(e, errorTitle ?? `${label} gagal`);
      return null;
    } finally {
      setJob(null);
    }
  }

  function showResult(label: string, res: OpResult) {
    setNotice({
      kind: "success",
      title: `${label} selesai: ${res.output_path}`,
      checks: [...res.checks, `Engine: ${res.engine}`],
      changes: res.changes,
      limitations: res.limitations,
    });
  }

  async function openFile(path?: string) {
    try {
      if (!path && !(await confirmDiscard("Buka dokumen lain"))) return;
      const chosen = path ?? ((await open({ multiple: false, directory: false, filters: PDF_FILTER })) as string | null);
      if (!chosen) return;
      const info = await api.openDocument(chosen);
      if (doc) await api.closeDocument(doc.doc_id).catch(() => undefined);
      setDoc(info);
      setCurrent(0);
      setFit("width");
      setTool(null);
      setFields(null);
      setFormOpen(false);
      setNotice(null);
      setTab("file");
    } catch (e) {
      showError(e, "Gagal membuka dokumen");
    }
  }

  async function saveAsFile() {
    if (!doc) return;
    const dest = await save({ defaultPath: suggestName(doc, "-salinan"), filters: PDF_FILTER });
    if (!dest) return;
    const res = await runTask("Simpan Sebagai", (id) => api.saveAs(doc.doc_id, dest, id));
    if (res) {
      showResult("Simpan Sebagai", res);
      const name = res.output_path.split(/[\\/]/).pop() ?? res.output_path;
      setDoc({ ...doc, path: res.output_path, file_name: name, dirty: false });
    }
  }

  async function rotate(delta: number) {
    if (!doc) return;
    try {
      setDoc(await api.rotatePages(doc.doc_id, [current], delta));
    } catch (e) {
      showError(e, "Gagal memutar halaman");
    }
  }

  async function doExtract() {
    if (!doc) return;
    setExtractOpen(false);
    const pre = await runTask("Memeriksa struktur dokumen", (id) => api.preflightExtract(doc.doc_id, selection, id), "Ekstrak halaman gagal");
    if (!pre) return;
    if (pre.requires_confirmation && !(await confirmPreflight("Ekstrak halaman", pre))) {
      setNotice({ kind: "info", title: "Ekstrak dibatalkan; tidak ada berkas yang dibuat." });
      return;
    }
    const dest = await save({ defaultPath: suggestName(doc, "-ekstrak"), filters: PDF_FILTER });
    if (!dest) return;
    const res = await runTask("Ekstrak halaman", (id) => api.extractPages(doc.doc_id, selection, dest, id));
    if (res) showResult("Ekstrak halaman", res);
  }

  function openMerge() {
    setMergeOpen(true);
  }

  async function submitAnnotation(kind: AnnotationKind, rect: [number, number, number, number], pageIndex: number, contents: string | null) {
    if (!doc) return;
    const info = await runTask("Menambah anotasi", (id) => api.addAnnotation(doc.doc_id, { page: pageIndex, kind, rect, contents }, id));
    if (info) {
      setDoc(info);
      setNotice({ kind: "success", title: `Anotasi ditambahkan ke halaman ${pageIndex + 1} (dokumen di memori) — simpan dengan Simpan Sebagai.` });
    }
  }

  async function loadFields() {
    if (!doc) return;
    setFieldsLoading(true);
    const f = await runTask("Membaca form", (id) => api.formFields(doc.doc_id, id));
    setFieldsLoading(false);
    setFields(f ?? []);
  }

  async function applyForm(values: Record<string, string | boolean>) {
    if (!doc) return;
    const info = await runTask("Mengisi form", (id) => api.fillForm(doc.doc_id, values, id));
    if (info) {
      setDoc(info);
      setNotice({ kind: "success", title: `${Object.keys(values).length} field diisi di dokumen di memori — simpan dengan Simpan Sebagai.` });
      await loadFields();
    }
  }

  /** Explicit navigation (thumbnail, page number, prev/next): moves the viewport. */
  const gotoHit = useCallback(
    (index: number) => {
      const hit = search.hits[index];
      if (!hit) return;
      search.setActiveIndex(index);
      viewRef.current?.scrollToPoint(hit.page, hit.top);
    },
    [search],
  );

  const navigateTo = useCallback(
    (index: number) => {
      if (!doc) return;
      const target = Math.min(Math.max(0, index), doc.page_count - 1);
      setCurrent(target);
      if (mode === "continuous") {
        suppressScrollSync.current = true;
        viewRef.current?.scrollToPage(target);
      }
    },
    [doc, mode],
  );

  function changeScale(next: { fit?: FitMode; zoom?: number }) {
    // Keep the reading position across zoom changes.
    viewRef.current?.captureAnchor();
    if (next.fit) setFit(next.fit);
    if (next.zoom !== undefined) {
      setZoom(next.zoom);
      setFit("custom");
    }
  }

  function zoomStep(dir: 1 | -1) {
    const now = zoomPercent;
    const next =
      dir > 0
        ? ZOOM_STEPS.find((z) => z > now) ?? ZOOM_STEPS[ZOOM_STEPS.length - 1]
        : [...ZOOM_STEPS].reverse().find((z) => z < now) ?? ZOOM_STEPS[0];
    changeScale({ zoom: next });
  }

  /** Clicking the active category tab collapses the command bar; clicking it again restores it. */
  function selectTab(next: TabId) {
    if (next === tab) {
      setToolbarVisible((v) => !v);
      return;
    }
    setTab(next);
    setToolbarVisible(true);
  }

  function setViewMode(next: ViewMode) {
    setMode(next);
    try {
      localStorage.setItem(VIEW_MODE_KEY, next);
    } catch {
      /* storage not available */
    }
    if (next === "single") {
      // Show the page that was active in continuous mode.
      const idx = current;
      requestAnimationFrame(() => viewRef.current?.scrollToPage(idx));
    }
  }

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (e.key === "Escape") {
        setTool(null);
        setAutoScrollRunning(false);
      } else if (e.ctrlKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        openFile();
      } else if (e.ctrlKey && e.key.toLowerCase() === "f") {
        e.preventDefault();
        setSearchOpen(true);
      } else if (e.key === "Escape" && searchOpen) {
        setSearchOpen(false);
      } else if (!doc) {
        return;
      } else if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        saveAsFile();
      } else if (e.ctrlKey && (e.key === "=" || e.key === "+")) {
        e.preventDefault();
        zoomStep(1);
      } else if (e.ctrlKey && e.key === "-") {
        e.preventDefault();
        zoomStep(-1);
      } else if (e.ctrlKey && e.key === "0") {
        e.preventDefault();
        changeScale({ fit: "width" });
      } else if (e.key === "PageDown" || e.key === "ArrowRight") {
        navigateTo(current + 1);
      } else if (e.key === "PageUp" || e.key === "ArrowLeft") {
        navigateTo(current - 1);
      } else if (e.key === "Home") {
        navigateTo(0);
      } else if (e.key === "End") {
        navigateTo(doc.page_count - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // Auto-scroll: a single time-based timer (pixels per second), paused by user interaction,
  // dialogs, annotation tools and the selection; it stops at the document edges.
  useEffect(() => {
    if (!autoScrollRunning) {
      if (autoScrollTimer.current) {
        window.clearInterval(autoScrollTimer.current);
        autoScrollTimer.current = null;
      }
      return;
    }
    const pxPerSec = 120 * autoScrollSpeed;
    autoScrollTimer.current = window.setInterval(() => {
      const pausedByUser = Date.now() - userScrollAt.current < 1200;
      const paused = pausedByUser || !!job || !!tool || !!confirm || !!textPrompt || !!extractOpen;
      setAutoScrollPaused(paused);
      if (paused) return;
      const view = viewRef.current;
      if (!view) return;
      const edge = view.atEdge();
      const dir = autoScrollDir === "down" ? 1 : -1;
      const blocked = (dir > 0 && edge === "bottom") || (dir < 0 && edge === "top");
      setAutoScrollAtEdge(blocked);
      if (blocked) {
        setAutoScrollRunning(false);
        return;
      }
      autoScrollUntil.current = Date.now() + 250;
      view.scrollByPixels(dir * pxPerSec * 0.05);
    }, 50);
    return () => {
      if (autoScrollTimer.current) {
        window.clearInterval(autoScrollTimer.current);
        autoScrollTimer.current = null;
      }
    };
  }, [autoScrollRunning, autoScrollSpeed, autoScrollDir, job, tool, confirm, textPrompt, extractOpen]);

  // Diagnostik geometri (hanya build dev: VITE_UNIONPDF_DEBUG=1).
  const [geo, setGeo] = useState("");
  useEffect(() => {
    if (!import.meta.env.VITE_UNIONPDF_DEBUG) return;
    let alive = true;
    const tick = async () => {
      try {
        const d = await collectGeometryDiagnostics();
        if (!alive) return;
        setGeo(
          `geo runs=${d.runs} layer=${isTransparent(d.layerColor) ? "transparan" : d.layerColor} ` +
            `sel=${isTransparent(d.selectionColor) ? "transparan" : d.selectionColor} ` +
            `wErr=${d.maxWidthErrorPct.toFixed(1)}% hErr=${d.maxHeightErrorPct.toFixed(1)}%`,
        );
      } catch {
        /* diagnostics are best effort */
      }
    };
    void tick();
    const t = window.setInterval(tick, 2000);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [doc?.doc_id, doc?.revision, current]);

  const busy = job !== null;

  return (
    <div className="app">
      <TitleBar
        doc={doc}
        toolbarVisible={toolbarVisible}
        onToggleToolbar={() => setToolbarVisible((v) => !v)}
        detail={engine ? `${engine.engine ?? ""}${engine.authoring_available ? " · anotasi & form aktif" : " · anotasi & form tidak aktif"}` : undefined}
      />
      <TabBar tabs={tabs} active={tab} onSelect={selectTab} />
      {toolbarVisible && (
      <CommandBar
        tab={tab}
        doc={doc}
        mode={mode}
        zoomPercent={zoomPercent}
        fit={fit}
        tool={tool}
        sidebarOpen={sidebarOpen}
        busy={busy}
        formOpen={formOpen}
        pageInput={pageInput}
        onOpen={() => openFile()}
        onSaveAs={saveAsFile}
        onZoom={zoomStep}
        onZoomValue={(v) => changeScale({ zoom: Math.min(800, Math.max(10, v)) })}
        onFit={(f) => changeScale({ fit: f })}
        onMode={setViewMode}
        onTool={setTool}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        onRotate={rotate}
        onExtract={() => {
          setSelection(String(current + 1));
          setExtractOpen(true);
        }}
        onMerge={openMerge}
        onGo={(d) => navigateTo(current + d)}
        onPageInput={setPageInput}
        onPageSubmit={() => {
          const n = parseInt(pageInput, 10);
          if (!Number.isNaN(n)) navigateTo(n - 1);
        }}
        onToggleForm={() => {
          const next = !formOpen;
          setFormOpen(next);
          if (next) loadFields();
        }}
        onOpenSearch={() => setSearchOpen(true)}
        onAutoScroll={() => {
          setAutoScrollOpen((v) => !v);
          setAutoScrollRunning(false);
        }}
        onBookmarks={() => setBookmarksOpen((v) => !v)}
        onSplit={() => setSplitOpen(true)}
        onConvert={() => setConvertOpen(true)}
      />
      )}

      {engine && !engine.available && (
        <div className="notice error">
          <strong>Engine PDF tidak tersedia.</strong> {engine.error}
          <div className="muted">Jalankan <code>apps/desktop/scripts/prepare-pdfium.ps1</code> lalu mulai ulang aplikasi.</div>
        </div>
      )}
      {notice && (
        <div className={`notice ${notice.kind}`} role={notice.kind === "error" ? "alert" : "status"} aria-label="Pemberitahuan">
          <button className="close" onClick={() => setNotice(null)} aria-label="Tutup pemberitahuan">×</button>
          <strong>{notice.title}</strong>
          {notice.checks?.map((l) => <div key={l}>✓ {l}</div>)}
          {notice.changes?.map((l) => <div key={l} className="change">ℹ {l}</div>)}
          {notice.limitations && notice.limitations.length > 0 && (
            <div className="limits">
              {notice.limitations.map((l) => <div key={l}>{notice.kind === "error" ? "" : "⚠ "}{l}</div>)}
            </div>
          )}
        </div>
      )}
      {tool && (
        <div className="notice info tool-hint" role="status">
          Alat aktif: <strong>{tool}</strong> · seret di atas halaman yang dikehendaki · Esc untuk berhenti
        </div>
      )}

      {searchOpen && (
        <SearchBar
          open={searchOpen}
          query={search.query}
          hits={search.hits}
          activeIndex={search.activeIndex}
          searching={search.searching}
          caseSensitive={search.caseSensitive}
          onQuery={search.setQuery}
          onNext={() => gotoHit(search.hits.length ? (search.activeIndex + 1) % search.hits.length : 0)}
          onPrevious={() => gotoHit(search.hits.length ? (search.activeIndex - 1 + search.hits.length) % search.hits.length : 0)}
          onClose={() => setSearchOpen(false)}
          onToggleCase={() => search.setCaseSensitive((v: boolean) => !v)}
          onCancel={() => void search.cancel()}
        />
      )}

      <AutoScrollControl
        open={autoScrollOpen}
        running={autoScrollRunning}
        direction={autoScrollDir}
        speed={autoScrollSpeed}
        paused={autoScrollPaused}
        onToggle={() => setAutoScrollRunning((v) => !v)}
        onDirection={setAutoScrollDir}
        atEdge={autoScrollAtEdge}
        onSpeed={setAutoScrollSpeed}
        onClose={() => {
          setAutoScrollOpen(false);
          setAutoScrollRunning(false);
        }}
      />

      <main className="body">
        {doc ? (
          <>
            <Sidebar
              open={sidebarOpen}
              doc={doc}
              current={current}
              revision={doc.revision}
              formOpen={formOpen}
              fields={fields}
              fieldsLoading={fieldsLoading}
              busy={busy}
              onSelectPage={navigateTo}
              onApplyForm={applyForm}
              onGoToPage={navigateTo}
            />
            {bookmarksOpen && (
              <aside className="sidebar right" aria-label="Panel bookmark">
                <BookmarkPanel
                  docId={doc.doc_id}
                  docPath={doc.path}
                  currentPage={current}
                  onGoToPage={navigateTo}
                />
              </aside>
            )}
            <DocumentView
              ref={viewRef}
              doc={doc}
              mode={mode}
              cssScale={cssScale}
              revision={doc.revision}
              tool={tool}
              onActivePage={onActivePage}
              onAnnotRect={(pageIndex, rect) => {
                if (tool === "note" || tool === "freetext") {
                  setPromptText("");
                  setTextPrompt({ kind: tool, rect, page: pageIndex });
                } else if (tool) {
                  submitAnnotation(tool, rect, pageIndex, null);
                }
              }}
              onError={onRenderError}
              zoomPercent={zoomPercent}
              onZoomWheel={(delta) => zoomStep(delta > 0 ? -1 : 1)}
              highlights={{ hits: search.hits, activeIndex: search.activeIndex }}
              onUserInteract={() => {
                if (Date.now() < autoScrollUntil.current) return; // scroll otomatis bukan interaksi pengguna
                userScrollAt.current = Date.now();
              }}
              onViewportSize={(w, h) => setViewport((v) => (Math.abs(v.w - w) > 1 || Math.abs(v.h - h) > 1 ? { w, h } : v))}
            />
          </>
        ) : (
          <div className="empty">
            <Logo size={64} />
            <h1>UnionPDF</h1>
            <p>Penampil & pengolah PDF lokal. Dokumen tidak pernah dikirim ke mana pun.</p>
            <button className="primary" onClick={() => openFile()} disabled={!engine?.available}>
              Buka PDF…
            </button>
            <p className="muted small">Ctrl+O membuka · PageUp/PageDown berpindah halaman · Ctrl+ +/− mengubah zoom · Ctrl+0 sesuaikan lebar</p>
          </div>
        )}
      </main>

      <StatusBar
        doc={doc}
        page={current}
        pageSize={page ? { width: page.width, height: page.height, rotation: page.rotation } : undefined}
        mode={mode}
        zoomPercent={zoomPercent}
        fit={fit}
        detail={engine ? `${engine.engine ?? ""} · ${engine.authoring_available ? "anotasi & form aktif" : "anotasi & form tidak aktif"}` : undefined}
        authoring={authoring}
        jobStage={job?.stage ?? null}
        geoInfo={geo}
        searchInfo={
          searchOpen && search.query
            ? search.searching
              ? "Mencari…"
              : search.hits.length
                ? `Hasil ${search.activeIndex + 1}/${search.hits.length}`
                : "Tidak ada hasil"
            : null
        }
      />

      {extractOpen && doc && (
        <div className="modal-backdrop" onClick={() => setExtractOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Ekstrak halaman">
            <h2>Ekstrak halaman</h2>
            <label>
              Halaman (mis. <code>1-3, 5, 8-</code>)
              <input autoFocus value={selection} onChange={(e) => setSelection(e.target.value)} onKeyDown={(e) => e.key === "Enter" && doExtract()} aria-label="Pilihan halaman" />
            </label>
            <p className="muted small">Hasil disimpan sebagai berkas baru; dokumen ini tidak diubah.</p>
            <div className="actions">
              <button onClick={() => setExtractOpen(false)}>Batal</button>
              <button className="primary" onClick={doExtract} disabled={!selection.trim()}>Lanjut</button>
            </div>
          </div>
        </div>
      )}

      {mergeOpen && doc && (
        <MergeDialog
          docId={doc.doc_id}
          docName={doc.file_name}
          docPath={doc.path}
          busy={busy}
          onClose={() => setMergeOpen(false)}
          onDone={(message, output) => {
            setMergeOpen(false);
            setNotice({ kind: "success", title: message, changes: [output] });
          }}
        />
      )}

      {splitOpen && doc && (
        <SplitDialog
          docId={doc.doc_id}
          docName={doc.file_name}
          pageCount={doc.page_count}
          busy={busy}
          onClose={() => setSplitOpen(false)}
          onProgress={(stage) => setJob({ id: "split", label: "Memisahkan dokumen", stage })}
          onDone={(message, files) => {
            setSplitOpen(false);
            setJob(null);
            setNotice({ kind: "success", title: message, changes: files.slice(0, 5) });
          }}
        />
      )}

      {convertOpen && doc && (
        <ConvertDialog
          docId={doc.doc_id}
          docName={doc.file_name}
          pageCount={doc.page_count}
          busy={busy}
          onClose={() => setConvertOpen(false)}
          onDone={(message, files) => {
            setConvertOpen(false);
            setNotice({ kind: "success", title: message, changes: files.slice(0, 5) });
          }}
        />
      )}

      {confirm && (
        <div className="modal-backdrop">
          <div className="modal wide" role="dialog" aria-label={`Konfirmasi ${confirm.title}`}>
            <h2>{confirm.title}: periksa dampak pada struktur dokumen</h2>
            <p className="muted small">Hasil pemeriksaan ({confirm.preflight.engine}). Berkas input tidak diubah.</p>
            {confirm.preflight.changes.map((c) => <div key={c} className="change">ℹ {c}</div>)}
            {confirm.preflight.limitations.map((c) => <div key={c} className="limits">⚠ {c}</div>)}
            <div className="actions">
              <button
                onClick={() => {
                  confirm.resolve(false);
                  setConfirm(null);
                }}
              >
                Batal
              </button>
              <button
                className="primary"
                onClick={() => {
                  confirm.resolve(true);
                  setConfirm(null);
                }}
              >
                Lanjutkan
              </button>
            </div>
          </div>
        </div>
      )}

      {textPrompt && (
        <div className="modal-backdrop">
          <div className="modal" role="dialog" aria-label={textPrompt.kind === "note" ? "Isi catatan" : "Isi teks bebas"}>
            <h2>{textPrompt.kind === "note" ? "Catatan" : "Teks bebas"}</h2>
            <p className="muted small">Halaman {textPrompt.page + 1}</p>
            <textarea autoFocus rows={4} value={promptText} onChange={(e) => setPromptText(e.target.value)} aria-label="Teks anotasi" />
            {textPrompt.kind === "freetext" && <p className="muted small">Teks bebas memakai font standar Helvetica (karakter Latin).</p>}
            <div className="actions">
              <button onClick={() => setTextPrompt(null)}>Batal</button>
              <button
                className="primary"
                disabled={!promptText.trim()}
                onClick={() => {
                  const p = textPrompt;
                  setTextPrompt(null);
                  submitAnnotation(p.kind, p.rect, p.page, promptText);
                }}
              >
                Tambahkan
              </button>
            </div>
          </div>
        </div>
      )}

      {job && (
        <div className="modal-backdrop">
          <div className="modal small" role="dialog" aria-label="Operasi berjalan">
            <h2>{job.label}</h2>
            <p>{job.stage}…</p>
            <div className="actions">
              <button onClick={() => api.cancelJob(job.id)}>Batalkan</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
