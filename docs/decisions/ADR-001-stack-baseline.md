# ADR-001 — Stack Baseline UnionPDF

- **Status:** Accepted (dengan syarat — lihat "Implikasi")
- **Tanggal:** 2026-10-20
- **Sesi:** `2026-10-20T1624+0700`
- **Hormat:** docs/PROJECT_STATE.md, docs/HANDOFF.md
- **Supersedes:** —
- **Superseded by:** —

## Konteks

Target UnionPDF: aplikasi desktop Windows untuk pengolahan PDF (lihat
`docs/PRODUCT_VISION.md`). Master prompt melarang mengunci stack sebelum
analisis referensi selesai, dan mewajibkan **review teknologi pasca-REA**
sebagai gate sebelum implementasi utama.

Analisis referensi menghasilkan 30+ domain kapabilitas (29 modul engine
`np_*.dll` + integrasi). 12 technical spike mengukur kandidat engine pada
mesin ini. Ringkasan angka di `docs/STACK_EVALUATION.md`.

## Kandidat yang dinilai

| | Kandidat | Skor |
|---|---|---:|
| A | Python 3.13 + PySide6 6.11 + MuPDF 1.27 (PyMuPDF) + Windows OCR | **463/500 (92,6 %)** |
| B | .NET 8/9 + WPF + PDFium + PdfSharp | 384/500 (76,8 %) |
| C | TypeScript + Electron + pdf.js + pdf-lib | 322/500 (64,4 %) |
| B' | .NET + iText 7 | ~320/500 (64,0 %) |

## Keputusan

**UnionPDF memakai Kandidat A.**

| Komponen | Pilihan | Versi | Lisensi |
|---|---|---|---|
| Runtime | Python | 3.13.9 | PSF |
| Desktop shell | PySide6 (Qt Widgets) | 6.11.0 | LGPL-3.0 |
| Engine PDF | PyMuPDF / MuPDF | 1.27.2.2 | **AGPL-3.0** |
| OCR utama | Windows.Media.Ocr via `winrt-*` | 3.2.1 | API OS |
| OCR lanjut | Tesseract (opsional, path kustom) | 5.x | Apache-2.0 |
| Pengujian | pytest | 8.3.4 | MIT |
| Packaging | PyInstaller (belum diuji) | — | GPL + exception |

Prinsip arsitektur: **satu runtime, satu engine PDF**, dengan engine dibungkus
interface `DocumentEngine` agar dapat diganti.

## Alasan

1. **Cakupan fitur M1–M4 + M7 terbukti PASS** pada MuPDF lewat spike
   (render, text layer, operasi halaman, anotasi, form, redaksi aman, enkripsi
   AES-256, gambar/watermark, ekspor gambar). PDFium dan pdf-lib **tidak
   memiliki** API authoring anotasi/form/redaksi — M3–M4 akan menjadi proyek
   tersendiri dengan risiko backside document corruption yang jauh lebih tinggi.
2. **Redaksi terbukti benar-benar menghapus** (S5: `secret_still_extractable:
   false`), bukan sekadar menutupi secara visual. Ini membuat acceptance
   criterion keamanan M7 measurable.
3. **Performa memadai**: render 33,87 ms/halaman @2×; dokumen 500 halaman
   dibuka 11,69 ms dan disimpan 12,34 ms.
4. **Background job + cancel terbukti** (S9): pembatalan dihormati, event loop
   tetap 661 tick/detik.
5. **OCR lokal tanpa unduhan model** berhasil lewat Windows OCR (S10:
   145,3 ms/halaman, 3 dari 4 baris tepat) — memenuhi syarat "tidak
   membutuhkan layanan AI berbayar".
6. **Lizensi AGPL-3.0 adalah biaya yang dapat dikelola**, bukan penghalang:
   produk gratis open-source memang memakai model bisnis ini.

## Konsekuensi

### Positif
- Satu runtime, satu engine → paket lebih sederhana, lebih mudah dipelihara.
- Logika domain mudah diuji (Python murni di balik interface).
- Jalur ke M5–M12 terbuka tanpa ganti stack.

### Negatif / Risiko
- **AGPL-3.0 mewajibkan UnionPDF open-source** dan sumbernya disediakan saat
  distribusi. → `BLOCKERS.md` B-01, **butuh persetujuan pengguna**.
- Ukuran distribusi belum terukur (MuPDF 50,62 MB + PySide6) → B-03.
- GIL Python membatasi paralelisme CPU-bound → pekerjaan berat via `QProcess`.
- Binding `winrt-*` 3.2.1 tidak mengekspos `get_available_recognizer_languages()`
  → daftar bahasa OCR harus dikelola sendiri.
- Aksesibilitas Qt di belakang WPF/UIA.

### Yang tidak berubah
- Master prompt **tidak** mengharuskan UnionPDF mengikuti bahasa/framework
  Nitro. Nol kode Nitro disalin.

## Implikasi (kondisi yang wajib dipenuhi)

1. Lisensi proyek UnionPDF **wajib** AGPL-3.0 selama MuPDF dipakai.
2. Seluruh akses engine PDF **wajib** lewat interface `DocumentEngine`.
3. Operasi berat **wajib** di luar thread UI dengan progress + cancel.
4. Versi dependency **wajib** di-pin (lihat `docs/DEPENDENCIES.md`).
5. Kemampuan engine **wajib** diverifikasi lewat spike/test, bukan asumsi.

## Rute cadangan

Bila pengguna menolak AGPL: susunan **pypdfium2 (render/ekstraksi) + pikepdf
(operasi halaman)**. Konsekuensinya (di `STACK_EVALUATION.md` §7): M3–M4 harus
ditulis manual, redaksi tertunda, dan OCR menjadi wajib Tesseract. Estimasi
biaya +1–2 milestone. Keputusan ini dicatat sebagai **pemicu ADR baru**, bukan
diam-diam mengganti engine.

## Review

Wajib tinjau ulang bila: temuan baru menunjukkan fitur wajib tidak dapat
didempenuhi; ada risiko integritas dokumen; ada masalah performa besar;
ada kegagalan packaging; ada konflik lisensi; ada dependency yang tidak
terawat; atau ada biaya baru yang tidak sesuai tujuan.

Jangan mengganti seluruh stack bila cukup mengganti adapter atau engine
tertentu.
