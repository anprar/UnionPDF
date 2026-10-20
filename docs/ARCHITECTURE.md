# ARCHITECTURE.md — Struktur UnionPDF

**Status:** DRAFT v1 — mengikuti ADR-001.
**Prinsip:** satu runtime, satu engine PDF, batas modul yang jelas.

---

## 1. Peta lapisan

```
┌──────────────────────────────────────────────────────────┐
│  Presentation  (PySide6)                                 │
│  MainWindow · ThumbnailPane · PageCanvas · Toolbar       │
│  StatusBar · JobProgressDialog · CommandPalette          │
└───────────────────────────┬──────────────────────────────┘
                            │.use case calls
┌───────────────────────────▼──────────────────────────────┐
│  Application  (use cases, tanpa GUI)                     │
│  OpenDocument · RotatePages · MergeDocuments ·           │
│  ApplyRedaction · OptimizeDocument · RunOcr · ExportImages│
│  EditSession (undo/redo) · JobScheduler                 │
└───────────────────────────┬──────────────────────────────┘
                            │ interface (protocol)
┌───────────────────────────▼──────────────────────────────┐
│  Domain  (model dokumen, murni, tanpa engine)            │
│  Document · PageRef · Annotation · FormField ·           │
│  PageRange · Selection · Operation · JobResult           │
└───────────────────────────┬──────────────────────────────┘
                            │ adapter
┌───────────────────────────▼──────────────────────────────┐
│  Engine adapters                                          │
│  MupdfDocumentEngine · WindowsOcrEngine · TesseractOcr   │
│  (semua di balik interface → bisa diganti)               │
└───────────────────────────┬──────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────┐
│  Infrastructure                                          │
│  FileStore (atomic write, temp+finalize) · Settings      │
│  Logger (tanpa isi dokumen) · JobRunner (QThreadPool)    │
└──────────────────────────────────────────────────────────┘
```

Aturan dependensi: **ketiktur hanya boleh mengarah ke bawah.** Domain tidak
boleh tahu-menahu MuPDF maupun PySide6.

## 2. Kontrak batas (wajib diimplementasikan, bukan opsional)

### 2.1 `DocumentEngine`

```python
class DocumentEngine(Protocol):
    def open(self, path: Path) -> DocumentHandle: ...
    def page_count(self, handle) -> int: ...
    def render_page(self, handle, index: int, zoom: float) -> RenderedPage: ...
    def extract_text(self, handle, index: int) -> str: ...
    def search(self, handle, query: str) -> list[SearchHit]: ...
    def apply_page_ops(self, handle, ops: PageOperation) -> DocumentHandle: ...
    def write(self, handle, dest: Path, options: WriteOptions) -> WriteReport: ...
    def close(self, handle) -> None: ...
```

`RenderedPage`: `width_px`, `height_px`, `width_pt`, `height_pt`, `pixels` (bytes RGBA/Qt).
`WriteReport`: `pages_written`, `bytes_written`, `warnings: list[str]`, `verification: VerificationResult`.

`VerificationResult` **wajib** ada: setiap operasi menulis harus memverifikasi
hasil (jumlah halaman, urutan, elemen yang harus dipertahankan). Lihat
`docs/TEST_PLAN.md` §Page operations.

### 2.2 `OcrEngine`

```python
class OcrEngine(Protocol):
    name: str
    def available_languages(self) -> list[str]: ...
    def recognize(self, page_image, language: str) -> OcrResult: ...
```

`OcrResult`: `text`, `words: list[OcrWord]` (kotak kata untuk layer teks).

### 2.3 Kontrak job

| Aspek | Aturan |
|---|---|
| Input | `JobSpec` (tipe operasi + parameter + target) |
| Output | `JobResult` (status, output, ringkasan, warning) |
| Error | exception ter typed (`DocumentError`, `EngineError`, `PermissionDeniedError`, `DiskFullError`) |
| Progress | `progress(current, total, label)` — total boleh `-1` bila tidak diketahui |
| Cancellation | `CancelToken` yang di-check di dalam loop; operasi harus berhenti **promptly** (< 1 detik) |
| Cleanup | file sementara milik job dihapus padafinally, baik sukses maupun gagal |

### 2.4 Aturan atomicitas file

1. Tulis ke `<dest>.unionpdf-tmp-<id>` di direktori yang sama.
2. Tutup & flush handle.
3. Verifikasi output (buka ulang, cek jumlah halaman/isi).
4. `os.replace` → final. (atomik di NTFS bila volume sama)
5. Hapus file sementara bila langkah 1–3 gagal.

Input **tidak pernah** ditimpa tanpa konfirmasi eksplisit.

## 3. Struktur direktori (sesuai stack terpilih)

```
src/unionpdf/
  __init__.py
  app.py                     # bootstrap QApplication
  domain/
    document.py              # Document, PageRef, PageRange
    annotations.py           # Annotation, FormField, Selection
    operations.py            # PageOperation, WriteOptions
    errors.py                # exception hierarchy
  application/
    session.py               # EditSession: dokumen + undo/redo
    use_cases/
      open_document.py
      page_operations.py
      annotate.py
      forms.py
      redaction.py
      optimize.py
      ocr.py
      export.py
    jobs.py                  # JobSpec, JobResult, JobRunner
  engine/
    protocol.py              # DocumentEngine, OcrEngine, RenderedPage
    mupdf_engine.py          # implementasi MuPDF
    mupdf_ocr.py             # Windows OCR via winrt
    tesseract_ocr.py         # opsi lanjut
  infrastructure/
    file_store.py            # atomic write, temp+finalize
    settings.py              # konfigurasi lokal (JSON)
    logging_setup.py         # logger tanpa isi dokumen
  ui/
    main_window.py
    thumbnail_pane.py
    page_canvas.py
    toolbar.py
    job_progress.py
    command_palette.py
    theme.py                 # token desain + QSS
  resources/
    icons/                   # ikon UnionPDF sendiri (bukan aset Nitro)
```

> Struktur ini baru dibuat setelah ADR-001 diterima. Aturan: **tidak** ada
> folder source yang terikat framework sebelum keputusan stack.

## 4. Prinsip UI

- Layout: toolbar atas → (thumbnail pane | canvas) → status bar bawah.
- Canvas: `QGraphicsView` + `QGraphicsScene` per halaman, render on-demand
  dengan cache LRU berbasis zoom level.
- Thumbnail: render @~120 px, di-cache; regenerate setelah page op.
- Keyboard: navigasi halaman, zoom, pencarian, command palette.
- Status bar: jumlah halaman, ukuran dokumen, zoom, status job.
- Aksibilitas: semua aksi punya teks aksesibilitas + shortcut; focus order
  logis; dukungan DPI fractional scaling.
- **Tidak ada tombol mati.** Fitur yang belum ada → disembunyikan atau diberi
  label status eksplisit.

## 5. Strategi pengujian

| Lapisan | Tools | Cakupan |
|---|---|---|
| Unit | pytest | Domain, page range, perhitungan ukuran, validasi |
| Integrasi engine | pytest + fixture sintetis | Open/render/ops/annotate/form/redact/encrypt |
| UI | pytest + `QTest` (offscreen) | Interaksi inti; sisanya manual (NOT_RUN) |
| Regresi | pytest | Fixture golden: output harus menghasilkan jumlah halaman & teks yang sama |
| Manual | checklist | DPI, keyboard, file terkunci, disk penuh, dokumen besar |

Semua fixture **sintetis** (dibuat oleh skrip di `tests/fixtures/`) → tidak ada
dokumen pengguna atau-berlisensi pihak ketiga.

## 6. Yang sengaja TIDAK ada

- Tidak ada database (tidak ada kebutuhan spesifik yang terbukti).
- Tidak ada message broker.
- Tidak ada microservice.
- Tidak ada runtime kedua.
- Tidak ada telemetry.
- Tidak ada modul AI (fitur inti tidak boleh bergantung padanya).
