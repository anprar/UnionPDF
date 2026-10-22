import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Logo } from "./Logo";
import {
  IconAutoScroll,
  IconBookmark,
  IconSearch,
  IconSplit,
  IconChevronDown,
  IconConvert,
  IconContinuous,
  IconExtract,
  IconFitPage,
  IconFitWidth,
  IconForm,
  IconHighlight,
  IconMerge,
  IconNext,
  IconNote,
  IconOpen,
  IconPrev,
  IconRotateLeft,
  IconRotateRight,
  IconSave,
  IconSidebar,
  IconSinglePage,
  IconTextBox,
  IconToolbar,
  IconUnderline,
  IconZoomIn,
  IconZoomOut,
} from "./icons";
import type { AnnotationKind, DocInfo } from "../types";
import type { ViewMode } from "./DocumentView";

export type TabId = "file" | "home" | "annotate" | "forms" | "pages";

export interface TabDef {
  id: TabId;
  label: string;
  /** Only tabs with a real function are shown. */
  available: boolean;
}

export function tabsFor(doc: DocInfo | null, authoring: boolean): TabDef[] {
  const hasForm = !!doc?.has_form;
  const all: TabDef[] = [
    { id: "file", label: "File", available: true },
    { id: "home", label: "Beranda", available: true },
    { id: "annotate", label: "Anotasi", available: authoring && !!doc },
    { id: "forms", label: "Form", available: authoring && hasForm },
    { id: "pages", label: "Halaman", available: !!doc },
  ];
  return all.filter((t) => t.available);
}

export interface TitleBarProps {
  doc: DocInfo | null;
  toolbarVisible: boolean;
  onToggleToolbar: () => void;
  /** Technical details (engine, worker) - shown as tooltip, not as user-facing text. */
  detail?: string;
}

/** Title bar: identity, active document, unsaved-changes badge and the toolbar toggle. */
export function TitleBar({ doc, toolbarVisible, onToggleToolbar, detail }: TitleBarProps) {
  return (
    <header className="titlebar" title={detail}>
      <div className="brand">
        <Logo size={18} />
        <span className="brand-name">UnionPDF</span>
      </div>
      <div className="doc-title" title={doc ? doc.path : "Tidak ada dokumen"}>
        {doc ? (
          <>
            <span className="doc-name">{doc.file_name}</span>
            {doc.dirty && (
              <span className="dirty-badge" title="Ada perubahan yang belum disimpan">
                belum disimpan
              </span>
            )}
          </>
        ) : (
          <span className="muted">Tanpa dokumen</span>
        )}
      </div>
      <button
        className={`icon-btn titlebar-toggle ${toolbarVisible ? "" : "off"}`}
        onClick={onToggleToolbar}
        aria-pressed={!toolbarVisible}
        aria-label={toolbarVisible ? "Sembunyikan toolbar perintah" : "Tampilkan toolbar perintah"}
        title={toolbarVisible ? "Sembunyikan toolbar perintah" : "Tampilkan toolbar perintah"}
      >
        <IconToolbar />
      </button>
    </header>
  );
}

export interface TabBarProps {
  tabs: TabDef[];
  active: TabId;
  /** Clicking the active tab collapses the command bar; clicking it again expands it. */
  onSelect: (t: TabId) => void;
}

/** Category tabs. The active tab doubles as the toolbar collapse toggle. */
export function TabBar({ tabs, active, onSelect }: TabBarProps) {
  return (
    <nav className="tabbar" role="tablist" aria-label="Kategori perintah">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={active === t.id}
          className={`tab ${active === t.id ? "active" : ""}`}
          title={active === t.id ? "Klik lagi untuk menyembunyikan toolbar perintah" : t.label}
          onClick={() => onSelect(t.id)}
        >
          {t.label}
        </button>
      ))}
    </nav>
  );
}

function Group({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="cmd-group" role="group" aria-label={label}>
      <span className="cmd-group-label">{label}</span>
      {children}
    </div>
  );
}

export interface CommandBarProps {
  tab: TabId;
  doc: DocInfo | null;
  mode: ViewMode;
  zoomPercent: number;
  fit: "width" | "page" | "custom";
  tool: AnnotationKind | null;
  sidebarOpen: boolean;
  formOpen: boolean;
  busy: boolean;
  pageInput: string;
  onOpen: () => void;
  onSaveAs: () => void;
  onZoom: (dir: 1 | -1) => void;
  onZoomValue: (value: number) => void;
  onFit: (fit: "width" | "page") => void;
  onMode: (mode: ViewMode) => void;
  onTool: (tool: AnnotationKind | null) => void;
  onToggleSidebar: () => void;
  onRotate: (delta: number) => void;
  onExtract: () => void;
  onMerge: () => void;
  onGo: (delta: number) => void;
  onPageInput: (v: string) => void;
  onPageSubmit: () => void;
  onToggleForm: () => void;
  onOpenSearch: () => void;
  onAutoScroll: () => void;
  onBookmarks: () => void;
  onSplit: () => void;
  onConvert: () => void;
}

function Groups(p: CommandBarProps) {
  const noDoc = !p.doc || p.busy;
  const zoom = (
    <div className="zoom-control">
      <button className="icon-btn" onClick={() => p.onZoom(-1)} disabled={noDoc} title="Perkecil (Ctrl+−)" aria-label="Perkecil">
        <IconZoomOut />
      </button>
      <input
        className="zoom-value"
        value={p.zoomPercent}
        disabled={noDoc}
        onChange={(e) => p.onZoomValue(Number(e.target.value.replace(/\D/g, "")) || 100)}
        onBlur={(e) => p.onZoomValue(Number(e.target.value.replace(/\D/g, "")) || 100)}
        aria-label="Nilai zoom dalam persen"
      />
      <button className="icon-btn" onClick={() => p.onZoom(1)} disabled={noDoc} title="Perbesar (Ctrl++)" aria-label="Perbesar">
        <IconZoomIn />
      </button>
    </div>
  );

  if (p.tab === "file") {
    return (
      <>
        <Group label="Berkas">
          <button className="cmd-btn" aria-label="Buka" onClick={p.onOpen} disabled={p.busy} title="Buka PDF (Ctrl+O)">
            <IconOpen /> <span>Buka</span>
          </button>
          <button className="cmd-btn" aria-label="Simpan Sebagai" onClick={p.onSaveAs} disabled={noDoc} title="Simpan sebagai berkas baru (Ctrl+Shift+S)">
            <IconSave /> <span>Simpan Sebagai</span>
          </button>
          <button className="cmd-btn" aria-label="Konversi" onClick={p.onConvert} disabled={noDoc} title="Konversi dokumen ke format lain">
            <IconConvert /> <span>Konversi</span>
          </button>
        </Group>
      </>
    );
  }

  if (p.tab === "annotate") {
    const tools: { kind: AnnotationKind; label: string; icon: ReactNode; title: string }[] = [
      { kind: "highlight", label: "Sorot", icon: <IconHighlight />, title: "Sorot teks (seret di atas teks)" },
      { kind: "underline", label: "Garis bawah", icon: <IconUnderline />, title: "Garis bawahi teks (seret di atas teks)" },
      { kind: "note", label: "Catatan", icon: <IconNote />, title: "Catatan (klik posisi)" },
      { kind: "freetext", label: "Teks", icon: <IconTextBox />, title: "Teks bebas (seret area)" },
    ];
    return (
      <>
        <Group label="Alat anotasi">
          {tools.map((t) => (
            <button
              key={t.kind}
              className={`cmd-btn ${p.tool === t.kind ? "active" : ""}`}
              aria-pressed={p.tool === t.kind}
              disabled={noDoc}
              title={t.title}
              onClick={() => p.onTool(p.tool === t.kind ? null : t.kind)}
            >
              {t.icon} <span>{t.label}</span>
            </button>
          ))}
        </Group>
        <Group label="Catatan">
          <span className="cmd-hint">Sorot dan garis bawah hanya berlaku pada teks. Esc menutup alat.</span>
        </Group>
      </>
    );
  }

  if (p.tab === "forms") {
    return (
      <>
        <Group label="Form">
          <button className={`cmd-btn ${p.formOpen ? "active" : ""}`} aria-pressed={p.formOpen} aria-label={p.formOpen ? "Sembunyikan form" : "Tampilkan form"} onClick={p.onToggleForm} disabled={noDoc} title="Tampilkan panel form">
            <IconForm /> <span>{p.formOpen ? "Sembunyikan form" : "Tampilkan form"}</span>
          </button>
        </Group>
        <Group label="Catatan">
          <span className="cmd-hint">Nilai diisi di panel form, lalu disimpan dengan Simpan Sebagai.</span>
        </Group>
      </>
    );
  }

  if (p.tab === "pages") {
    return (
      <>
        <Group label="Navigasi">
          <button className="icon-btn" onClick={() => p.onGo(-1)} disabled={noDoc} title="Halaman sebelumnya (PageUp)" aria-label="Halaman sebelumnya">
            <IconPrev />
          </button>
          <input
            className="page-input"
            value={p.pageInput}
            disabled={noDoc}
            onChange={(e) => p.onPageInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && p.onPageSubmit()}
            onBlur={() => p.onPageSubmit()}
            aria-label="Nomor halaman"
          />
          <button className="icon-btn" onClick={() => p.onGo(1)} disabled={noDoc} title="Halaman berikutnya (PageDown)" aria-label="Halaman berikutnya">
            <IconNext />
          </button>
        </Group>
        <Group label="Operasi">
          <button className="cmd-btn" aria-label="Putar kiri" onClick={() => p.onRotate(-90)} disabled={noDoc} title="Putar halaman aktif 90° ke kiri (Ctrl+Shift+Left)">
            <IconRotateLeft /> <span>Putar</span>
          </button>
          <button className="cmd-btn" aria-label="Putar kanan" onClick={() => p.onRotate(90)} disabled={noDoc} title="Putar halaman aktif 90° ke kanan (Ctrl+Shift+Right)">
            <IconRotateRight /> <span>Putar</span>
          </button>
          <button className="cmd-btn" aria-label="Ekstrak" onClick={p.onExtract} disabled={noDoc} title="Ekstrak halaman ke PDF baru">
            <IconExtract /> <span>Ekstrak</span>
          </button>
          <button className="cmd-btn" aria-label="Gabung" onClick={p.onMerge} disabled={noDoc} title="Gabungkan PDF lain di belakang dokumen ini">
            <IconMerge /> <span>Gabung</span>
          </button>
          <button className="cmd-btn" aria-label="Pisah" onClick={p.onSplit} disabled={noDoc} title="Pisahkan dokumen menjadi beberapa berkas">
            <IconSplit /> <span>Pisah</span>
          </button>
        </Group>
        <Group label="Navigasi dokumen">
          <button className="cmd-btn" aria-label="Bookmark" onClick={p.onBookmarks} disabled={noDoc} title="Tampilkan bookmark dokumen">
            <IconBookmark /> <span>Bookmark</span>
          </button>
        </Group>
      </>
    );
  }

  // Beranda
  return (
    <>
      <Group label="Tampilan">
        {zoom}
        <button className={`cmd-btn ${p.fit === "width" ? "active" : ""}`} aria-label="Lebar" aria-pressed={p.fit === "width"} onClick={() => p.onFit("width")} disabled={noDoc} title="Lebar halaman">
          <IconFitWidth /> <span>Lebar</span>
        </button>
        <button className={`cmd-btn ${p.fit === "page" ? "active" : ""}`} aria-label="Halaman" aria-pressed={p.fit === "page"} onClick={() => p.onFit("page")} disabled={noDoc} title="Halaman penuh">
          <IconFitPage /> <span>Halaman</span>
        </button>
        <button className="cmd-btn" aria-label="Cari" onClick={p.onOpenSearch} disabled={noDoc} title="Cari teks (Ctrl+F)">
          <IconSearch /> <span>Cari</span>
        </button>
      </Group>
      <Group label="Mode">
        <button className={`cmd-btn ${p.mode === "continuous" ? "active" : ""}`} aria-label="Menyambung" aria-pressed={p.mode === "continuous"} onClick={() => p.onMode("continuous")} disabled={noDoc} title="Gulir vertikal menyambung antar halaman">
          <IconContinuous /> <span>Menyambung</span>
        </button>
        <button className={`cmd-btn ${p.mode === "single" ? "active" : ""}`} aria-label="Satu halaman" aria-pressed={p.mode === "single"} onClick={() => p.onMode("single")} disabled={noDoc} title="Tampilkan satu halaman per layar">
          <IconSinglePage /> <span>Satu halaman</span>
        </button>
      </Group>
      <Group label="Panel">
        <button className={`cmd-btn ${p.sidebarOpen ? "active" : ""}`} aria-label="Thumbnail" aria-pressed={p.sidebarOpen} onClick={p.onToggleSidebar} title="Tampilkan atau sembunyikan panel thumbnail">
          <IconSidebar /> <span>Thumbnail</span>
        </button>
        <button className="cmd-btn" aria-label="Gulir otomatis" onClick={p.onAutoScroll} title="Gulir dokumen secara otomatis">
          <IconAutoScroll /> <span>Gulir otomatis</span>
        </button>
      </Group>
    </>
  );
}

/**
 * Contextual command bar. When the available width is too small the groups move into an
 * overflow menu instead of shrinking the buttons.
 */
export function CommandBar(p: CommandBarProps) {
  const barRef = useRef<HTMLDivElement>(null);
  const [overflow, setOverflow] = useState(false);
  const [open, setOpen] = useState(false);

  useLayoutEffect(() => {
    const el = barRef.current;
    if (!el) return;
    const check = () => {
      const need = el.scrollWidth;
      const have = el.clientWidth;
      setOverflow(need > have + 4);
      if (need <= have + 4) setOpen(false);
    };
    check();
    const ro = new ResizeObserver(check);
    ro.observe(el);
    return () => ro.disconnect();
  }, [p.tab, p.doc, p.mode, p.fit, p.zoomPercent, p.tool, p.formOpen, p.sidebarOpen]);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (barRef.current && !barRef.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div className={`commandbar ${overflow ? "overflow" : ""}`} ref={barRef}>
      {overflow ? (
        <>
          <button className="cmd-btn" aria-label="Perintah lainnya" aria-expanded={open} onClick={() => setOpen((v) => !v)} title="Tampilkan perintah lainnya">
            <IconChevronDown /> <span>Perintah</span>
          </button>
          {open && (
            <div className="overflow-menu" role="menu">
              <Groups {...p} />
            </div>
          )}
        </>
      ) : (
        <Groups {...p} />
      )}
    </div>
  );
}

export interface StatusBarProps {
  doc: DocInfo | null;
  page: number;
  /** Size of the active page in points (and its rotation). */
  pageSize?: { width: number; height: number; rotation: number };
  mode: ViewMode;
  zoomPercent: number;
  fit: "width" | "page" | "custom";
  /** Technical details shown in the tooltip (engine, worker) - not in the visible text. */
  detail?: string;
  authoring: boolean;
  jobStage?: string | null;
  searchInfo?: string | null;
  /** Diagnostics of the text layer geometry (development builds only). */
  geoInfo?: string;
}

export function StatusBar(p: StatusBarProps) {
  return (
    <footer className="statusbar" title={p.detail}>
      <span className="status-cell">{p.doc ? `Halaman ${p.page + 1} dari ${p.doc.page_count}` : "Tidak ada dokumen"}</span>
      {p.pageSize && (
        <span className="status-cell">
          {Math.round(p.pageSize.width)}×{Math.round(p.pageSize.height)} pt{p.pageSize.rotation ? ` · rotasi ${p.pageSize.rotation}°` : ""}
        </span>
      )}
      <span className="status-cell">{p.doc ? (p.mode === "continuous" ? "Menyambung" : "Satu halaman") : ""}</span>
      <span className="status-cell">Zoom {p.doc ? `${p.zoomPercent}%` : "—"}</span>
      <span className="status-cell">{p.fit === "width" ? "Sesuai lebar" : p.fit === "page" ? "Sesuai halaman" : ""}</span>
      {p.searchInfo && <span className="status-cell">{p.searchInfo}</span>}
      {p.geoInfo && <span className="status-cell geo">{p.geoInfo}</span>}
      {p.jobStage && <span className="status-cell job">{p.jobStage}</span>}
      <span className="spacer" />
      <span className="status-cell muted">{p.authoring ? "Anotasi & form aktif" : "Anotasi & form tidak aktif"}</span>
    </footer>
  );
}
