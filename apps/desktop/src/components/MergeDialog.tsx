import { useState } from "react";
import { open, save } from "@tauri-apps/plugin-dialog";
import { mergeDocuments, preflightMerge } from "../api";
import type { Preflight } from "../types";

const PDF_FILTER = [{ name: "Dokumen PDF", extensions: ["pdf"] }];

interface Props {
  docId: number;
  docName: string;
  /** Path dokumen aktif - lokasi default hasil gabung. */
  docPath?: string;
  busy: boolean;
  onClose: () => void;
  onDone: (message: string, output: string) => void;
}

/** Merge dialog: a list of documents (add/remove/reorder), the output location and the structure preview. */
export function MergeDialog({ docId, docName, docPath, busy, onClose, onDone }: Props) {
  const [files, setFiles] = useState<string[]>([]);
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addFiles = async () => {
    const picked = (await open({ multiple: true, directory: false, filters: PDF_FILTER })) as string[] | null;
    if (!picked) return;
    setFiles((f) => [...f, ...picked]);
    setPreflight(null);
  };
  const move = (i: number, dir: -1 | 1) => {
    setFiles((f) => {
      const next = [...f];
      const j = i + dir;
      if (j < 0 || j >= next.length) return f;
      [next[i], next[j]] = [next[j], next[i]];
      return next;
    });
    setPreflight(null);
  };
  const remove = (i: number) => {
    setFiles((f) => f.filter((_, k) => k !== i));
    setPreflight(null);
  };

  const check = async () => {
    setError(null);
    try {
      const p = await preflightMerge(docId, files, crypto.randomUUID());
      setPreflight(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const run = async () => {
    setError(null);
    const base = docName.replace(/\.pdf$/i, "");
    const dir = docPath ? docPath.slice(0, docPath.length - docName.length) : "";
    const dest = await save({ defaultPath: `${dir}${base}-gabungan.pdf`, filters: PDF_FILTER });
    if (!dest) return;
    try {
      const res = await mergeDocuments(docId, files, dest, crypto.randomUUID());
      onDone(`Gabung selesai: ${files.length + 1} berkas, ${res.page_count} halaman`, res.output_path);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal wide" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Gabung dokumen">
        <h2>Gabung dokumen</h2>
        <p className="muted small">Dokumen aktif diletakkan di depan. Tambahkan berkas lain, atur urutannya.</p>
        <ol className="file-list">
          <li className="file-item current">
            <span className="file-name">{docName}</span>
            <span className="muted small">dokumen aktif</span>
          </li>
          {files.map((f, i) => (
            <li className="file-item" key={f + i}>
              <span className="file-name">{f.split(/[\\/]/).pop()}</span>
              <span className="muted small grow">{f}</span>
              <button className="icon-btn" onClick={() => move(i, -1)} disabled={i === 0} aria-label="Naikkan" title="Naikkan">
                ↑
              </button>
              <button className="icon-btn" onClick={() => move(i, 1)} disabled={i === files.length - 1} aria-label="Turunkan" title="Turunkan">
                ↓
              </button>
              <button className="icon-btn" onClick={() => remove(i)} aria-label={`Hapus ${f.split(/[\\/]/).pop()}`} title="Hapus dari daftar">
                ×
              </button>
            </li>
          ))}
        </ol>
        <div className="actions">
          <button onClick={onClose}>Batal</button>
          <button onClick={addFiles}>Tambah berkas…</button>
          <button onClick={check} disabled={files.length === 0 || busy}>
            Periksa struktur
          </button>
          <button className="primary" onClick={run} disabled={files.length === 0 || busy}>
            Gabung
          </button>
        </div>
        {preflight && (
          <div className="preflight">
            {preflight.changes.map((c) => (
              <div key={c} className="change">
                ℹ {c}
              </div>
            ))}
            {preflight.limitations.map((c) => (
              <div key={c} className="limits">
                ⚠ {c}
              </div>
            ))}
          </div>
        )}
        {error && <div className="limits">⚠ {error}</div>}
      </div>
    </div>
  );
}
