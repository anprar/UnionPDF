# TEST_RESULTS.md — Hasil Uji Terakhir

**Run:** 2026-10-20 16:49–16:50 WIB (UTC+7)
**Sesi:** `2026-10-20T1624+0700`
**Environment:** Windows 11 build 26300 · x64 · 12 core · Python 3.13.9 ·
pymupdf 1.27.2.2 · PySide6 6.11.0 · pytest 8.3.4 · `QT_QPA_PLATFORM=offscreen`

---

## 1. Ringkasan

| Suite | Perintah | Hasil | Durasi |
|---|---|---|---|
| Unit + integrasi + UI smoke | `.venv\Scripts\python.exe -m pytest tests -q` | **PASS — 55 passed, 0 failed, 0 skipped** | 2,08 s |
| Smoke aplikasi | `.venv\Scripts\python.exe scripts\smoke_app.py` | **PASS — 9/9** | < 1 s |
| Linter workspace | `.venv\Scripts\python.exe scripts\lint.py` | **PASS — 0 temuan** | < 1 s |
| Spike S1–S12 | `.\scripts\run_spikes.ps1` | **9 PASS · 1 PASS bersyarat · 2 NOT AVAILABLE** | ~35 s |

**Status keseluruhan: GREEN.**

## 2. Rincian per area

| Test ID | Area | Uji | Actual | Status |
|---|---|---|---|---|
| T-DOM-01..08 | Domain | PageRange (6 kasus), PageOperation, Document, exception hierarchy | Sesuai | PASS |
| T-ENG-01 | Engine | Buka PDF valid → 5 halaman | 5 halaman | PASS |
| T-ENG-02 | Engine | Berkas hilang → `DocumentError` | DocumentError | PASS |
| T-ENG-03 | Engine | PDF korup → `DocumentError` | DocumentError | PASS |
| T-ENG-04 | Engine | PDF terenkripsi → `PermissionDeniedError` | PermissionDeniedError | PASS |
| T-ENG-05 | Engine | Info dokumen | page_count 5, text layer True | PASS |
| T-ENG-06 | Engine | Render → PNG valid, rasio px/pt ≈ 1 | OK | PASS |
| T-ENG-07 | Engine | Render zoom 0,5 vs 2,0 → rasio 4× | OK | PASS |
| T-ENG-08 | Engine | Render indeks salah → `IndexError` | IndexError | PASS |
| T-ENG-09 | Engine | Ekstraksi teks berisi "Halaman 1" | OK | PASS |
| T-ENG-10 | Engine | Pencarian "Halaman" → 5 hit di 5 halaman | OK | PASS |
| T-ENG-11 | Engine | Pencarian query kosong → 0 | OK | PASS |
| T-ENG-12 | Engine | Rotate: 5→5 halaman, rot 90 | OK | PASS |
| T-ENG-13 | Engine | Rotate **tidak memutasikan sumber** | sumber rot 0 | PASS |
| T-ENG-14 | Engine | Delete 2 halaman → 3 halaman, "Halaman 2" jadi pertama | OK | PASS |
| T-ENG-15 | Engine | Extract (1,3) → 2 halaman, isi sesuai | OK | PASS |
| T-ENG-16 | Engine | Duplicate → 6 halaman | OK | PASS |
| T-ENG-17 | Engine | Reorder → urutan berubah, 5 halaman | OK | PASS |
| T-ENG-18 | Engine | Merge 5+1 → 6 halaman | OK | PASS |
| T-ENG-19 | Engine | Write + verifikasi → passed | OK | PASS |
| T-ENG-20 | Engine | Write dengan expected 99 → verifikasi gagal + notes | OK | PASS |
| T-ENG-21 | Engine | Write ke direktori bertingkat → dibuat | OK | PASS |
| T-INF-01..08 | Infrastruktur | Atomic write (6 kasus), unique path, settings (3 kasus) | Sesuai | PASS |
| T-UI-01..08 | UI | Window, aksi, muat dokumen, kanvas, zoom, fit, cari, tutup | Sesuai | PASS |
| T-SMK-01..09 | Smoke | Jendela terlihat, dokumen termuat, 6 thumbnail, item kanvas, lebar > 0, judul, zoom, navigasi, pencarian | 9/9 | PASS |

## 3. Hasil spike (terukur, bukan estimasi)

| Spike | Metrik | Nilai | Status |
|---|---|---|---|
| S1 | Render median @2× | 33,87 ms/halaman | PASS |
| S2 | Merge / split / rotate+delete | 14/14 · 4/4 · 11 hlm rot 90° | PASS |
| S2 | 500 halaman: buka / render / simpan | 11,69 / 32,51 / 12,34 ms | PASS |
| S3 | Anotasi (highlight, note, freetext, shape) | 3 anot reopen | PASS |
| S4 | Form create→isi→reopen | nilai bertahan | PASS |
| S5 | Redaksi | `secret_still_extractable: false` | PASS |
| S6 | Gambar/watermark/footer | 1 image; teks terbaca | PASS |
| S7 | Ekspor PNG | 21,3 ms/halaman | PASS |
| S8 | Font builtin/TTF + AES-256 + re-auth | semuanya OK | PASS |
| S9 | Cancel saat 15/200 langkah; event loop | dihormati; 661 tick/detik | PASS |
| S10 | Windows OCR | 145,3 ms/halaman; 3/4 baris persis | PASS (bersyarat) |
| S10 | Tesseract / rapidocr | tidak terpasang | NOT AVAILABLE |
| S11 | Qt 6.11 offscreen | widget + processEvents OK | PASS |
| S12 | MuPDF payload | 50,62 MB | PASS |
| S12 | Ukuran EXE final | — | **NOT_MEASURED** |

## 4. Yang TIDAK diuji (NOT_RUN)

| Area | Alasan |
|---|---|
| Interaksi UI manual (DPI, keyboard, drag & drop) | Belum ada display interaktif |
| Redaksi pada dokumen ber-metadata/thumbnail | L-07 — fixture belum dibuat |
| Edit teks existing + reflow | B-04 — spike belum dilakukan |
| Flatten anotasi/form | Belum ada implementasi |
| OCR lewat UI | Belum ada UI |
| Packaging EXE | B-03 — PyInstaller belum dipasang |
| Performa > 5.000 halaman | U-04 |
| Tanda tangan kriptografis | U-06 |
| Office ↔ PDF | U-05 |
| Doku ini sudah Nugini | — |

## 5. Keterbatasan hasil

- Semua pengukuran dilakukan pada **satu** mesin dan **synthetic** fixtures.
  Tidak ada benchmark pada dokumen pengguna.
- Tidak ada perbandingan dengan aplikasi referensi
  (`REA_LIMITATIONS.md` L-06).
- Angka OCRakurasi diukur pada 4 baris teks Latin sintetis; **belum** pada
  dokumen pindai nyata atau bahasa non-Latin.
