import { useEffect, useState } from "react";
import { documentOutline } from "../api";
import { IconBookmark } from "./icons";

export interface OutlineNode {
  title: string;
  page: number | null;
  children: OutlineNode[];
}

/** Personal bookmarks (UnionPDF) - stored locally, never written into the PDF. */
export interface PersonalMark {
  id: string;
  name: string;
  page: number;
}

const STORAGE_KEY = "unionpdf.personalMarks";

export function loadPersonalMarks(docPath: string): PersonalMark[] {
  try {
    const all = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]") as (PersonalMark & { doc: string })[];
    return all.filter((m) => m.doc === docPath).map(({ doc: _doc, ...rest }) => rest);
  } catch {
    return [];
  }
}

export function savePersonalMarks(docPath: string, marks: PersonalMark[]): void {
  try {
    const all = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]") as (PersonalMark & { doc: string })[];
    const kept = all.filter((m) => m.doc !== docPath);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...kept, ...marks.map((m) => ({ ...m, doc: docPath }))]));
  } catch {
    /* storage not available */
  }
}

interface Props {
  docId: number | null;
  docPath: string;
  currentPage: number;
  onGoToPage: (page: number) => void;
}

function Tree({
  nodes,
  depth,
  onGoToPage,
}: {
  nodes: OutlineNode[];
  depth: number;
  onGoToPage: (page: number) => void;
}) {
  return (
    <>
      {nodes.map((n, i) => (
        <div key={`${n.title}-${i}`}>
          <button
            className="outline-item"
            aria-label={n.title}
            style={{ paddingLeft: 8 + depth * 12 }}
            onClick={() => n.page !== null && onGoToPage(n.page)}
            disabled={n.page === null}
            title={n.page === null ? "Tujuan bookmark tidak dapat ditampilkan" : `Ke halaman ${n.page + 1}`}
          >
            <span className="outline-title">{n.title}</span>
            {n.page === null ? <span className="muted small">tanpa tujuan</span> : <span className="muted small">{n.page + 1}</span>}
          </button>
          {n.children.length > 0 && <Tree nodes={n.children} depth={depth + 1} onGoToPage={onGoToPage} />}
        </div>
      ))}
    </>
  );
}

/** Right-hand panel: PDF bookmarks (hierarchy) and personal marks (add/remove/rename). */
export function BookmarkPanel({ docId, docPath, currentPage, onGoToPage }: Props) {
  const [outline, setOutline] = useState<OutlineNode[] | null>(null);
  const [marks, setMarks] = useState<PersonalMark[]>([]);
  const [name, setName] = useState("");

  useEffect(() => {
    setMarks(loadPersonalMarks(docPath));
  }, [docPath]);

  useEffect(() => {
    if (!docId) {
      setOutline(null);
      return;
    }
    documentOutline(docId)
      .then(setOutline)
      .catch(() => setOutline([]));
  }, [docId]);

  const addMark = () => {
    const label = name.trim() || `Tanda halaman ${currentPage + 1}`;
    const mark: PersonalMark = { id: crypto.randomUUID(), name: label, page: currentPage };
    const next = [...marks, mark];
    setMarks(next);
    savePersonalMarks(docPath, next);
    setName("");
  };

  const removeMark = (id: string) => {
    const next = marks.filter((m) => m.id !== id);
    setMarks(next);
    savePersonalMarks(docPath, next);
  };

  const renameMark = (id: string, label: string) => {
    const next = marks.map((m) => (m.id === id ? { ...m, name: label } : m));
    setMarks(next);
    savePersonalMarks(docPath, next);
  };

  return (
    <div className="bookmark-panel">
      <div className="panel-title">
        <IconBookmark /> <span>Bookmark</span>
      </div>
      <section>
        <h3 className="panel-subtitle">Bookmark dokumen</h3>
        {outline === null && <p className="muted small">Membaca…</p>}
        {outline && outline.length === 0 && <p className="muted small">Dokumen ini tidak memiliki bookmark.</p>}
        {outline && outline.length > 0 && (
          <div className="outline-tree">
            <Tree nodes={outline} depth={0} onGoToPage={onGoToPage} />
          </div>
        )}
      </section>
      <section>
        <h3 className="panel-subtitle">Tanda baca saya</h3>
        <p className="muted small">Disimpan di komputer ini, tidak ditulis ke berkas PDF.</p>
        <div className="mark-add">
          <input
            value={name}
            placeholder={`Tanda halaman ${currentPage + 1}`}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && addMark()}
            aria-label="Nama tanda baca"
          />
          <button className="cmd-btn" onClick={addMark} title="Tambah tanda baca pada halaman aktif">
            Tambah
          </button>
        </div>
        <ul className="mark-list">
          {marks.map((m) => (
            <li key={m.id}>
              <button className="mark-name" onClick={() => onGoToPage(m.page)} title={`Ke halaman ${m.page + 1}`}>
                {m.name}
              </button>
              <span className="muted small">{m.page + 1}</span>
              <button className="icon-btn" onClick={() => renameMark(m.id, prompt("Nama tanda baca", m.name) ?? m.name)} aria-label={`Ubah nama ${m.name}`} title="Ubah nama">
                ✎
              </button>
              <button className="icon-btn" onClick={() => removeMark(m.id)} aria-label={`Hapus ${m.name}`} title="Hapus tanda baca">
                ×
              </button>
            </li>
          ))}
          {marks.length === 0 && <li className="muted small">Belum ada tanda baca.</li>}
        </ul>
      </section>
    </div>
  );
}
