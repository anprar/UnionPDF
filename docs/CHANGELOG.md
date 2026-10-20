# CHANGELOG.md

Format: [Keeps a Changelog](https://keepachangelog.com/id/1.1.0/).
Versi mengikuti [SemVer](https://semver.org/lang/id/).

---

## [Unreleased] — 0.1.0.dev0

Status: **Fase M0 — Foundation.** Belum ada rilis publik.

### Ditambahkan
- **Lisensi proyek ditetapkan: AGPL-3.0** + berkas `LICENSE` (661 baris) dan
  `NOTICE` di root workspace.
- **Analisis biner read-only mendalam** aplikasi referensi (izin pengguna):
  14.452 string UI dari 35 berkas `.mui`, 783 kontrol ribbon (14 tab +
  90 toolbar kontekstual), 10.284 identifier fitur dari 30 modul, analisis
  native Ghidra atas `np_pdfa.dll` (1.852 prosedur).
  → `docs/REA_FINDINGS.md` v2, `docs/research/V14_RIBBON_STRUCTURE.md`,
  `docs/research/V14_UI_EVIDENCE.md`.
- Skrip analisis: `extract_mui_strings.py`, `extract_native_strings.py`,
  `build_ribbon_map.py`, `analyze_ui_evidence.py`.
- Struktur dokumentasi kontinuitas lengkap (33 dokumen di `docs/`).
- Analisis aplikasi referensi Nitro PDF Pro 14.41.0.15: inventaris read-only
  install tree + dokumentasi publik → `docs/REA_FINDINGS.md`.
- Batas analisis → `docs/REA_LIMITATIONS.md`.
- Indeks bukti `E-001`…`E-413` → `docs/EVIDENCE_INDEX.md`.
- Matriks 97 fitur dengan keputusan KEEP/IMPROVE/REPLACE/DEFER/REJECT →
  `docs/FEATURE_MATRIX.md`.
- Review teknologi pasca-REA (gate) → `docs/POST_REA_TECH_REVIEW.md`.
- Evaluasi stack 4 kandidat berbobot (A=463, B=384, C=322, B'=320) →
  `docs/STACK_EVALUATION.md`.
- 12 technical spike terukur → `docs/TECH_SPIKES.md`, `spikes/`.
- ADR-001 stack baseline → `docs/decisions/ADR-001-stack-baseline.md`.
- Arsitektur berlapis + kontrak engine → `docs/ARCHITECTURE.md`.
- Audit lisensi dependency → `docs/LICENSE_REVIEW.md`.
- Skeleton aplikasi `src/unionpdf/` (domain, application, engine, infrastructure, ui).
- Vertical slice M1: open, render, zoom, fit, navigasi, thumbnail, cari, simpan.
- 55 pytest (unit, integrasi engine, UI smoke) + smoke app 9/9.
- Skrip: `setup.ps1`, `run.ps1`, `test.ps1`, `run_spikes.ps1`, `smoke_app.py`,
  `lint.py`, `repair_docs.py`.

### Keputusan
- Lisensi proyek **AGPL-3.0** (B-01 selesai) — open source, sesuai tujuan produk.
- Inspeksi biner read-only **diizinkan & dilakukan** (B-02 selesai).
- Stack: Python 3.13 + PySide6 6.11 + MuPDF 1.27 + Windows OCR (ADR-001).
  Analisis v2 **menguatkan** keputusan ini; tidak ada temuan yang membatalkannya.

### Diperbaiki
- Semantik `apply_page_operations`: ROTATE / DELETE / DUPLICATE kini
  mempertahankan seluruh halaman; dokumen sumber tidak lagi dimutasi.
- API MuPDF 1.27: `Page.add_widget` (bukan `insert_widget`),
  `Widget.text_fontsize` (bukan `field_fontsize`).
- API PySide6 6.11: `qVersion()` (bukan `QT_VERSION_STR`).
- `JobSignals` dipisah ke `QObject` agar `Signal` dapat di-connect.
- Jalur import paket pada pytest (`pythonpath = src`).
- Parser resource PE sendiri: offset subdirektori relatif terhadap root
  resource directory.

### Diketahui (bukan bug)
- Ukuran distribusi belum terukur (B-03).
- Edit teks existing + reflow belum dibuktikan (B-04).
- Daftar bahasa OCR tidak dapat dienumerasi lewat binding winrt 3.2.1 (B-05).
- Ghidra gagal mengimpor `NitroPDF.exe` (16 MB CEF) → `U-08`; analisis native
  dilakukan pada modul kecil.
- Perilaku runtime Nitro tidak pernah diamati (aplikasi tidak dieksekusi).

### Perilaku yang berubah
Tidak ada — belum ada rilis.

---

## RENCANA

- `0.1.0` — M0 + M1 selesai: viewer stabil, packaging one-dir terukur.
- `0.2.0` — M2: operasi halaman + undo/redo.
- `0.3.0` — M3 + M4: create/augment, anotasi, form.
- `0.4.0` — M5: OCR.
- `0.5.0` — M6 + M7: optimasi/batch, keamanan.
