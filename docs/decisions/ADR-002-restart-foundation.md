# ADR-002 — Fondasi controlled restart: Tauri 2 + React/TS + Rust, PDFium renderer, PDFBox authoring awal

- Status: **Accepted** (fondasi) — persetujuan pengguna 2026-10-21 (sesi `2026-10-21T1215+0700`)
- Tanggal: 2026-10-21
- Rujukan: `experiments/restart/results/SUMMARY.md` §9, `experiments/restart/deps/PROVENANCE.md` §1–7,
  `docs/STACK_EVALUATION.md` §10.2b (urutan kriteria K2-1…K2-8, G-1 disetujui)
- Tidak menggantikan ADR-001 secara diam-diam: implementasi Python/PySide6/PyMuPDF lama tetap
  ada sebagai benchmark (`src/`, `tests/`, `spikes/` tidak disentuh). Cleanup tetap butuh
  persetujuan terpisah.

## Konteks

Pengguna menerima hasil spike sebagai hasil sementara dan menyetujui fondasi aplikasi baru di
`apps/desktop/`. Pembandingan engine pada fixture v2 (SUMMARY §9) menunjukkan PDFium layak
sebagai renderer tetapi lemah untuk authoring; PDFBox dan MuPDF kuat untuk authoring.

## Keputusan

| Lapisan | Pilihan | Status |
|---|---|---|
| Shell desktop | Tauri 2 (`tauri =2.12.4`) | Disetujui pengguna |
| UI | React 19 + TypeScript + Vite | Disetujui pengguna |
| Host/orchestrator | Rust | Disetujui pengguna |
| Renderer | PDFium `chromium/7881` (bblanchon/pdfium-binaries) via `pdfium-render 0.9.4` | Disetujui pengguna |
| Penyimpanan | JSON/config file, tanpa database wajib | Disetujui pengguna |
| Authoring | Apache PDFBox 3.0.8 (Java) — **pilihan awal** | Diotorisasi pengguna bila terbukti layak; lolos RS-02 (kecuali stamp), RS-03, RS-04, merge, signature minimal |
| Redaksi | **Terbuka** | PDFium/PDFBox tanpa API; MuPDF lengkap tetapi AGPL/komersial → butuh keputusan lisensi |

Vertical slice pertama (viewer + Save As/rotate/extract/merge) memakai PDFium in-process;
operasi menulis ke salinan dan memverifikasi output dengan membuka ulang sebelum mengganti
berkas tujuan. Integrasi worker PDFBox (sidecar Java) dijadwalkan untuk fitur authoring.

## Alasan

- PDFium: render RS-01 PASS, operasi halaman in-place RS-05 PASS, in-process, lisensi permisif.
- PDFBox: hasil authoring terbaik di antara opsi berlisensi Apache-2.0 (SUMMARY §9.1).
- Batas engine berupa trait `PdfEngine`/`PdfDoc` (`apps/desktop/src-tauri/src/engine.rs`) agar
  engine dapat diganti tanpa menyentuh UI.

## Konsekuensi

- Positif: viewer berjalan sekarang; authoring tidak memblokir viewer.
- Negatif: dua engine (C++ native + JVM) → ukuran distribusi bertambah (JRE belum diukur);
  extract via PDFium belum memangkas bookmark; merge kehilangan bookmark/field dokumen kedua;
  ekstraksi teks RTL PDFium berurutan visual.
- Tidak berubah: `LICENSE`/`NOTICE`; tidak ada commit/push; tidak ada instalasi global.

## Rute cadangan

- Authoring: MuPDF sebagai worker opsional bila keputusan lisensi diambil.
- Renderer: pdf.js atau MuPDF bila PDFium bermasalah (belum diuji di aplikasi).

## Review

Tinjau ulang bila: ukuran JRE melampaui anggaran A-2, PDFBox gagal pada fitur wajib berikutnya,
atau keputusan lisensi redaksi diambil.
