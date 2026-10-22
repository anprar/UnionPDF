import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { extractPages } from "../api";

type SplitMode = "each" | "every" | "range";

interface Props {
  docId: number;
  docName: string;
  pageCount: number;
  busy: boolean;
  onClose: () => void;
  onDone: (message: string, files: string[]) => void;
  onProgress: (stage: string) => void;
}

/** Split dialog: every page, every N pages or a user range; each part is written as its own file. */
export function SplitDialog({ docId, docName, pageCount, busy, onClose, onDone, onProgress }: Props) {
  const [mode, setMode] = useState<SplitMode>("each");
  const [every, setEvery] = useState(10);
  const [ranges, setRanges] = useState("1-2, 3-4");
  const [outDir, setOutDir] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const base = docName.replace(/\.pdf$/i, "");

  const pickFolder = async () => {
    const dir = await open({ directory: true, multiple: false });
    if (typeof dir === "string") setOutDir(dir);
  };

  const chunks = (): { start: number; end: number }[] => {
    if (mode === "each") return Array.from({ length: pageCount }, (_, i) => ({ start: i + 1, end: i + 1 }));
    if (mode === "every") {
      const n = Math.max(1, every);
      const out: { start: number; end: number }[] = [];
      for (let s = 1; s <= pageCount; s += n) out.push({ start: s, end: Math.min(pageCount, s + n - 1) });
      return out;
    }
    return ranges
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean)
      .map((r) => {
        const m = r.match(/^(\d+)\s*-\s*(\d+)$/);
        if (!m) throw new Error(`rentang tidak valid: "${r}" (contoh: 1-5)`);
        const start = Number(m[1]);
        const end = Number(m[2]);
        if (start < 1 || end < start || end > pageCount) throw new Error(`rentang di luar dokumen: "${r}"`);
        return { start, end };
      });
  };

  const run = async () => {
    setError(null);
    let parts: { start: number; end: number }[];
    try {
      parts = chunks();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return;
    }
    if (parts.length === 0) {
      setError("tidak ada rentang untuk dipisah");
      return;
    }
    if (!outDir) {
      setError("pilih folder keluaran");
      return;
    }
    const files: string[] = [];
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i];
      onProgress(`Memisahkan bagian ${i + 1} dari ${parts.length}`);
      try {
        const res = await extractPages(docId, `${p.start}-${p.end}`, `${outDir}\\${base}-${String(i + 1).padStart(3, "0")}-h${p.start}-${p.end}.pdf`);
        files.push(res.output_path);
      } catch (e) {
        setError(`Gagal memisahkan bagian ${i + 1}: ${e instanceof Error ? e.message : String(e)}`);
        return;
      }
    }
    onDone(`Dipisah menjadi ${files.length} berkas`, files);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Pisahkan dokumen">
        <h2>Pisahkan dokumen</h2>
        <p className="muted small">{pageCount} halaman · setiap bagian menjadi berkas sendiri</p>
        <label className="radio-row">
          <input type="radio" name="splitmode" checked={mode === "each"} onChange={() => setMode("each")} /> Tiap halaman
        </label>
        <label className="radio-row">
          <input type="radio" name="splitmode" checked={mode === "every"} onChange={() => setMode("every")} /> Setiap
          <input
            className="num-input"
            type="number"
            min={1}
            max={pageCount}
            value={every}
            onChange={(e) => setEvery(Math.max(1, Number(e.target.value) || 1))}
            aria-label="Jumlah halaman per bagian"
          />
          halaman
        </label>
        <label className="radio-row">
          <input type="radio" name="splitmode" checked={mode === "range"} onChange={() => setMode("range")} /> Rentang
        </label>
        {mode === "range" && (
          <input value={ranges} onChange={(e) => setRanges(e.target.value)} placeholder="1-5, 6-10" aria-label="Daftar rentang" />
        )}
        <div className="actions">
          <button onClick={pickFolder}>Folder keluaran…</button>
          <input
            className="grow"
            value={outDir}
            placeholder=" atau ketik folder keluaran"
            onChange={(e) => setOutDir(e.target.value)}
            aria-label="Folder keluaran"
          />
        </div>
        <div className="actions">
          <button onClick={onClose}>Batal</button>
          <button className="primary" onClick={run} disabled={busy}>
            Pisahkan
          </button>
        </div>
        {error && <div className="limits">⚠ {error}</div>}
      </div>
    </div>
  );
}
