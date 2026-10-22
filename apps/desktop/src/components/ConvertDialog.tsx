import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { convertDocument } from "../api";

type Format = "png" | "jpeg" | "txt" | "pdf";

interface Props {
  docId: number | null;
  docName: string;
  pageCount: number;
  busy: boolean;
  onClose: () => void;
  onDone: (message: string, files: string[]) => void;
}

const IMAGE_FILTER = [{ name: "Gambar", extensions: ["png", "jpg", "jpeg", "bmp", "tif", "tiff"] }];

/** Conversion dialog: PDF -> PNG/JPEG/TXT and images -> PDF, with range, resolution and quality. */
export function ConvertDialog({ docId, docName, pageCount, busy, onClose, onDone }: Props) {
  const [format, setFormat] = useState<Format>("png");
  const [range, setRange] = useState("");
  const [dpi, setDpi] = useState(150);
  const [quality, setQuality] = useState(85);
  const [outDir, setOutDir] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const base = docName.replace(/\.pdf$/i, "") || "dokumen";

  const pickFolder = async () => {
    const dir = await open({ directory: true, multiple: false });
    if (typeof dir === "string") setOutDir(dir);
  };
  const pickImages = async () => {
    const picked = (await open({ multiple: true, directory: false, filters: IMAGE_FILTER })) as string[] | null;
    if (picked) setImages(picked);
  };

  const run = async () => {
    setError(null);
    if (!outDir) {
      setError("pilih folder keluaran");
      return;
    }
    if (format === "pdf" && images.length === 0) {
      setError("pilih setidaknya satu berkas gambar");
      return;
    }
    if (format !== "pdf" && !docId) {
      setError("buka dokumen terlebih dahulu");
      return;
    }
    try {
      const res = await convertDocument(docId, format, { range, dpi, quality, baseName: base }, outDir, images);
      onDone(`Konversi selesai: ${res.files.length} berkas`, res.files);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Konversi dokumen">
        <h2>Konversi</h2>
        <label className="radio-row">
          <input type="radio" name="convfmt" checked={format === "png"} onChange={() => setFormat("png")} /> PDF → PNG (gambar)
        </label>
        <label className="radio-row">
          <input type="radio" name="convfmt" checked={format === "jpeg"} onChange={() => setFormat("jpeg")} /> PDF → JPEG (gambar)
        </label>
        <label className="radio-row">
          <input type="radio" name="convfmt" checked={format === "txt"} onChange={() => setFormat("txt")} /> PDF → Teks
        </label>
        <label className="radio-row">
          <input type="radio" name="convfmt" checked={format === "pdf"} onChange={() => setFormat("pdf")} /> Gambar → PDF
        </label>

        {format === "pdf" ? (
          <div className="actions">
            <button onClick={pickImages}>Pilih gambar…</button>
            <span className="muted small grow">{images.length} berkas dipilih</span>
          </div>
        ) : (
          <>
            <label>
              Halaman (kosong = semua, mis. <code>1-3, 5</code>)
              <input value={range} onChange={(e) => setRange(e.target.value)} placeholder={`1-${pageCount}`} aria-label="Rentang halaman" />
            </label>
            {format !== "txt" && (
              <label>
                Resolusi (DPI): {dpi}
                <input type="range" min={72} max={600} step={6} value={dpi} onChange={(e) => setDpi(Number(e.target.value))} aria-label="Resolusi DPI" />
              </label>
            )}
            {format === "jpeg" && (
              <label>
                Kualitas JPEG: {quality}
                <input type="range" min={40} max={100} step={1} value={quality} onChange={(e) => setQuality(Number(e.target.value))} aria-label="Kualitas JPEG" />
              </label>
            )}
          </>
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
            Konversi
          </button>
        </div>
        {error && <div className="limits">⚠ {error}</div>}
      </div>
    </div>
  );
}
