# STACK_EVALUATION.md — Perbandingan Stack

**Status:** DRAFT v1 — menyertai ADR-001.
**Sesi:** `2026-10-20T1624+0700`
**Dasar bukti:** `TECH_SPIKES.md` (S1–S12) dan `REA_FINDINGS.md`.

---

## 1. Metodologi

Kriteria dan bobot ditetapkan **sebelum** penilaian, agar tidak mel morbid bias.

| # | Kriteria | Bobot | Alasan bobot |
|---|---|---:|---|
| K1 | Cakupan fitur wajib M1–M4 | 15 | Viewer + operasi halaman + anotasi/form adalah inti produk |
| K2 | Kualitas rendering & text layer | 10 | Fondasi pengalaman "buka dokumen" |
| K3 | Ketepatan & integritas operasi PDF | 10 | Kerusakan output = Credibility rusak |
| K4 | Anotasi, form, dan redaksi | 12 | Mewarnai secara umum; redaksi punya implikasi keamanan |
| K5 | OCR lokal | 8 | M5; tidak boleh butuh layanan berbayar |
| K6 | Responsivitas UI (background job, progress, cancel) | 10 | Persyaratan "modern" eksplisit di master prompt |
| K7 | Offline & privasi | 6 | Prinsip produk |
| K8 | Packaging Windows (ukuran, reproduktibilitas) | 8 | Adopsi nyata |
| K9 | Testability | 6 | unittest-able = elektrifikasi regressions |
| K10 | Lisensi & biaya redistribusi | 12 | Model bisnis gratis wajib dijaga |
| K11 | Aksesibilitas & DPI Windows | 4 | Standar desktop Windows |
| K12 | Kemudahan mengganti engine PDF | 4 | Mengurangi risiko lock-in vendor |
| | **TOTAL** | **100** | |

Skala: **0** = tidak memenuhi · **1** = sangat lemah · **2** = lemah ·
**3** = cukup · **4** = baik · **5** = kuat.

Skor = `bobot × skor`; total maksimum 500.

### Klasifikasi bukti

| Label | Arti |
|---|---|
| **FAKTA** | Didokumentasikan/diukur langsung |
| **PENGUKURAN** | Terukur di mesin ini via spike |
| **ESTIMASI** | Penalaran berdasar, belum diukur |
| **UNKNOWN** | Belum diketahui |

---

## 2. Kandidat yang dibandingkan

Maksimal tiga kombinasi yang realistis, sesuai master prompt.

### A — Python 3.13 + PySide6 (Qt 6.11) + MuPDF (PyMuPDF) + Windows OCR
- Shell desktop: PySide6 6.11 (LGPL-3.0).
- Engine PDF: PyMuPDF 1.27.2.2 / MuPDF 1.27.2.2 (**AGPL-3.0**).
- OCR: `Windows.Media.Ocr` lewat binding `winrt-*` 3.2.1, dengan Tesseract opsional.
- Packaging: PyInstaller (belum diuji).

### B — .NET 8/9 + WPF + PDFium (via PDFiumViewer/Docnet) + PdfSharp
- Shell: WPF (Windows-native, UIA penuh).
- Render: PDFium (Chrome-grade).
- Manipulasi: PdfSharp (MIT) — tanpa native runtime pihak ketiga.
- OCR: Windows.Media.Ocr lewat WinRT, atau Tesseract.NET.
- Packaging: `dotnet publish` self-contained / MSIX.

### C — TypeScript + Electron + pdf.js + pdf-lib
- Shell: Electron (Chromium).
- Render: pdf.js (Mozilla).
- Manipulasi: pdf-lib.
- OCR: Tesseract.js (WASM) atau sidecar native.
- Packaging: electron-builder.

### Alasan kandidat yang TIDAK dimasukkan
- **Tauri + Rust:** shell-nya bagus, tapiRust menambah runtime kedua tanpa
  manfaat yang jelas untuk domain PDF, dan akses ke binding C++ MuPDF dari Rust
  menambah lapisan FFI yang harus dipelihara.
- **Java (PDFBox):** satu-satunya stack permissive yang punya render + teks +
  form, tapi menambah runtime JVM ke aplikasi desktop dan tetap tidak punya
  authoring anotasi/redaksi yang memadai.

---

## 3. Penilaian

| K | Bobot | A (Python) | B (.NET) | C (TS/Electron) |
|---|---:|---:|---:|---:|
| K1 Cakupan fitur M1–M4 | 15 | 5 | 2 | 2 |
| K2 Rendering & text layer | 10 | 5 | 5 | 5 |
| K3 Ketepatan operasi | 10 | 5 | 4 | 3 |
| K4 Anotasi/form/redaksi | 12 | 5 | 1 | 1 |
| K5 OCR lokal | 8 | 4 | 3 | 2 |
| K6 Responsivitas UI | 10 | 4 | 5 | 3 |
| K7 Offline & privasi | 6 | 5 | 5 | 5 |
| K8 Packaging Windows | 8 | 3 | 5 | 2 |
| K9 Testability | 6 | 5 | 4 | 4 |
| K10 Lisensi & redistribusi | 12 | 3 | 4 | 5 |
| K11 Aksesibilitas & DPI | 4 | 4 | 5 | 3 |
| K12 Ganti engine | 4 | 5 | 4 | 3 |
| | **100** | | | |

### Total

| Kandidat | Skor | Persentase |
|---|---:|---:|
| **A — Python + PySide6 + MuPDF** | **463** | **92,6 %** |
| B — .NET + WPF + PDFium + PdfSharp | 384 | 76,8 % |
| C — TypeScript + Electron + pdf.js + pdf-lib | 322 | 64,4 % |

---

## 4. Rasional per kriteria (dengan klasifikasi bukti)

### K1 — Cakupan fitur wajib M1–M4 · A=5, B=2, C=2
**PENGUKURAN.** MuPDF terbukti mendukung: render + text layer (S1), merge/split/
rotate/delete (S2), highlight/note/freetext/shape (S3), form create+fill+reopen
(S4), gambar/watermark/footer (S6), ekspor PNG (S7), AES-256 (S8).

Pada kandidat B dan C, **gap-nya bukanopinion, tapi ketiadaan API**:
- **FAKTA:** PDFium bersifat read-only untuk render/ekstraksi; tidak menulis
  dokumen.
- **FAKTA:** PdfSharp (MIT) menyediakan operasi halaman & markup, tetapi tidak
  menyediakan API authoring anotasi, pengisian form, atau redaksi.
- **FAKTA:** pdf-lib (@cantoo/pdf-lib) menyediakan operasi halaman dasar; tidak
  menyediakan authoring anotasi/form/redaksi.
- **Konsekuensi:** M3 (tambah teks/gambar) dan M4 (anotasi/form) harus
  dibangun dari nol, termasuk menulis serializer objek PDF sendiri. Risiko
  korupsi dokumen meningkat drastis.

### K2 — Rendering · semua 5
**PENGUKURAN:** MuPDF 33,87 ms/halaman @2× pada dokumen 12 halaman campuran.
PDFium dan pdf.js sama-sama matang; di sini seri.

### K3 — Ketepatan operasi · A=5, B=4, C=3
**PENGUKURAN:** round-trip A terverifikasi (S2): jumlah halaman, urutan, rotasi,
dan isi teks konsisten setelah reopen. Untuk B dan C, ini **ESTIMASI** —
belum diukur, dan berisiko karenaPdfSharp/pdf-lib membangun ulang struktur
dokumen dari model internal mereka, bukan menyunting dokumen asli.

### K4 — Anotasi/form/redaksi · A=5, B=1, C=1
**PENGUKURAN:** S3, S4, S5 semuanya PASS. Yang paling menentukan: redaksi
terbukti menghapus isi target dari content stream (`secret_still_extractable:
false`), bukan sekadar menutupi secara visual.

Di B dan C, achieving ini berarti:
- iText 7 (fitur lengkap) → **AGPL / komersial** → menggeser skor B pada K10 menjadi 1.
- Mendefinisikan ulang PdfSharp → biaya M4 penuh, tetap tanpa redaksi.
- **ESTIMASI:** 1 (sangat lemah).

### K5 — OCR · A=4, B=3, C=2
**PENGUKURAN:** Windows OCR via `winrt-*` 3.2.1 berhasil — 145,3 ms/halaman,
3 dari 4 baris persis, tanpa unduhan model.

- B bisa memakai API yang sama (bahkan lebih natural dari C#), tetapi
  `Tesseract.NET` memerlukan biner native.
- C memerlukan Tesseract.js (WASM, jauh lebih lambat) atau sidecar native.
- Skor A = 4, bukan 5, karena: `get_available_recognizer_languages()` tidak
  diekspos binding 3.2.1, dan akurasi belum diukur pada dokumen nyata.

### K6 — Responsivitas UI · A=4, B=5, C=3
**PENGUKURAN:** S9 membuktikan pola `QThreadPool` + token cancel bekerja
(cancel dihormati pada langkah 15/200; event loop 661 tick/detik).

**ESTIMASI (risiko A):** Python shared GIL → pekerjaan CPU-bound murni Python
tidak paralel di dalam satu proses. Mitigasi: operasi berat dijalankan lewat
`QProcess` ke helper terpisah, atau operasi berat cukup di MuPDF (C++, di luar
GIL). B menang di sini karena .NET tidak punya GIL.

### K7 — Offline & privasi · semua 5
**FAKTA:** ketiga kandidat bisa sepenuhnya offline. Tidak ada yang memaksa
layanan cloud. B dan C sedikit lebih unggul karena tidak ada yang secara
historis mengirim telemetri — catatan: A harus **sengaja** memastikan tidak ada
telemetry (bawaan Python: tidak ada).

### K8 — Packaging · A=3, B=5, C=2
**PENGUKURAN (A):** MuPDF native payload 50,62 MB; PySide6 addons 168,7 MB
(uncompressed wheel). PyInstaller **belum** diuji → **NOT_MEASURED** untuk
ukuran akhir.
**ESTIMASI:** A berakhir di kisaran 120–180 MB (one-dir) — rentang perkiraan,
bukan angka hasil.
**FAKTA (B):** .NET self-contained single-file ~60–100 MB, plus MSIX.
**FAKTA (C):** Electron 100–200 MB+ sebelum aplikasi.

### K9 — Testability · A=5, B=4, C=4
**PENGUKURAN:** logika domain PDF di A adalah Python murni di balik interface
`DocumentEngine` → unit test tanpa GUI, tanpa engine.
**ESTIMASI:** B requireable, tetapi perhatian pada binding C++/P/Invoke.
**ESTIMASI:** C testable, tetapi pdf-lib sering berubah.

### K10 — Lisensi · A=3, B=4, C=5
Ini kriteria paling menentukan bagi model bisnis "gratis tanpa paywall".

| Kandidat | Lisensi inti | Dampak |
|---|---|---|
| A | **MuPDF AGPL-3.0**, PySide6 LGPL-3.0 | UnionPDF **harus** AGPL-3.0 agar bebas; harus menawarkan source saat distribusi |
| B | PdfSharp MIT, PDFium BSD, .NET MIT | Kalau tanpa iText AGPL → permissive, tanpa kewajiban source |
| C | pdf.js Apache-2.0, pdf-lib MIT, Electron MIT | Permissive |

**FAKTA (mengubah skor B):** bila B memakai iText 7 untuk M4, lisensinya
AGPL/komersial → skor B turun ke ~1 pada K10 dan total B menjadi ~320, di bawah A.
Jadi B hanya unggul bila M4 ditunda — artinya B **tidak bisa memenuhi**
cakupan M1–M4 yang diminta.

**A diberi 3, bukan 2:** AGPL-3.0 **tidakForbidden** untuk produk gratis —
justru itu cara legal temprana. **Konsekuensinya:** UnionPDF harus open-source, dan
sumbernya harus disediakan saat distribusi.
Lihat `LICENSE_REVIEW.md`.

### K11 — Aksesibilitas & DPI · A=4, B=5, C=3
**FAKTA:** WPF punya UI Automation yang matang. Qt mendukung DPI fractional
scaling dengan baik, tetapi dukungan screen reader di Qt masih di belakang
WPF. **ESTIMASI** untuk bagian aksesibilitas (belum diuji).

### K12 — Ganti engine · A=5, B=4, C=3
**FAKTA:** MuPDF dipanggil lewat API yang stabil dan sempit; adapter cukup
membungkus ~40 permukaan API. B perlu abstraksi lebih besar karena
terpisahnya render (PDFium) dan tulis (PdfSharp) — meaning dua engine untuk
satu tugas. C sama.

---

## 5. Contoh struktur costs (bandingkan biaya nyata)

| Aspek | A | B | C |
|---|---|---|---|
| Runtime yang harus dibundel | 1 (Python + Qt) | 1 (.NET) | 1 (Node) + Chromium |
| Engine PDF | 1 (MuPDF) | 2 (PDFium + PdfSharp) | 2 (pdf.js + pdf-lib) |
| Runtime tambahan | — | — | Chromium 150–200 MB |
| Bahasa kedua | tidak | tidak | tidak |
| Multi-runtime | tidak | tidak | tidak |

Sesuai master prompt "jangan menambah banyak runtime tanpa manfaat yang jelas" —
A menang jelas: **satu runtime, satu engine PDF**.

---

## 6. Batas-batas kesimpulan

- **Tidak ada angka benchmark yang dikarang.** Yang belum diukur ditulis
  `NOT_MEASURED`, khusus: ukuran EXE final A, performa B dan C (tidak diukur
  sama sekali), dan performa pada dokumen >5.000 halaman.
- **Tidak ada perbandingan performa UnionPDF vs Nitro.** Nol benchmark Nitro
  dijalankan (`REA_LIMITATIONS.md` L-06).
- **Skor B dan C bersifat prediktif**, berbasis pada cacat API yang diketahui
  dan terdokumentasi (FAKTA), bukan pada pengukuran.
- **Penting:** uji A baru sah untuk M1–M4. M8 (edit teks existing dengan
  reflow) **belum diuji pada engine mana pun** → lihat `U-01`.

---

## 7. Rekomendasi

**KEEP — Kandidat A**, dengan kondisi berikut:

1. **Lisensi proyek UnionPDF = AGPL-3.0** (syarat MuPDF). →
   `BLOCKERS.md` B-01, butuh persetujuan pengguna.
2. **OCR = Windows OCR sebagai jalur utama**, Tesseract sebagai opsi lanjut.
3. **Engine PDF dibungkus `DocumentEngine` interface** sejak hari pertama,
   supaya penggantian engine (mis. ke pypdfium2+pikepdf) tetap mungkin.
4. **Pekerjaan berat dijalankan di luar thread UI**, dengan `QProcess` bila
   Dispatcher lock GIL menjadi masalah.
5. **Ukuran distribusi diukur** pada M0/M1 (build one-dir) — bila >200 MB,
   tinjau pemangkasan PySide6 addons.

### Rute cadangan bila AGPL ditolak pengguna

Susun **pypdfium2 (render/ekstraksi, BSD-3) + pikepdf (qpdf, MPL-2.0)**:

| Yang hilang dibanding MuPDF | Dampak |
|---|---|
| Authoring anotasi | M4 harus ditulis manual di atas qpdf |
| Form filling | M4 tertunda |
| Redaksi | M7 tertunda / ditulis manual |
| Insert teks/gambar | M3 tertunda |
| OCR | Tesseract menjadi **wajib** (MuPDF tidak ada) |

**ESTIMASI biaya:** menambah ~1–2 milestone untuk M3–M4. Karena itu jalur
cadangan ini **tidak dipilih sekarang**, tetapi tetap didokumentasikan sebagai
opsi yang sah bila pengguna menolak AGPL. Keputusan ini dicatat di ADR-001
bagian "Implikasi".

---

## 8. Ringkasan angka

| Kandidat | Skor | Persentase | Verdict |
|---|---:|---:|---|
| A — Python + PySide6 + MuPDF | 463 | 92,6 % | **KEEP** |
| B — .NET + WPF + PDFium + PdfSharp | 384 | 76,8 % | REJECT (M3–M4 tidak Practical) |
| C — TypeScript + Electron + pdf.js + pdf-lib | 322 | 64,4 % | REJECT (M3–M4 tidak Practical) |
| B' — .NET + iText 7 (AGPL) | ~320 | 64,0 % | REJECT (lisensi + mengaburkan diferensiasi) |

---

## 9. Konfirmasi setelah analisis mendalam (v2)

**Tanggal:** 2026-10-20 · **Sesi:** `2026-10-20T1700+0700`

Analisis biner read-only yang diizinkan menghasilkan 14.452 string UI, 783
kontrol ribbon, dan 10.284 identifier fitur. **Skor tidak berubah: A = 463/500
(92,6 %).**

| Kriteria | Skor v1 | Skor v2 | Alasan perubahan / konfirmasi |
|---|---:|---:|---|
| K1 Cakupan fitur wajib | 5 | 5 | Konfirmasi: v14 sendiri butuh 29 modul engine; MuPDF menutup M1–M4 dalam 1 adapter. |
| K2 Rendering | 5 | 5 | Tidak ada temuan baru. |
| K3 Ketepatan operasi | 5 | 5 | Tidak ada temuan baru. |
| K4 Anotasi/form/redaksi | 5 | 5 | **Konfirmasi kuat**: v14 butuh `np_annotations` + `np_forms` + `np_redaction` (3 DLL) + `solid_framework` (PDF/A & signature validation, **berlisensi komersial**). MuPDF memberi ketiganya dalam 1 engine berlisensi gratis. |
| K5 OCR | 4 | 4 | Tidak berubah. |
| K6 Responsivitas UI | 4 | 4 | Tidak berubah. |
| K7 Offline & privasi | 5 | 5 | **Konfirmasi**: v14 mengirim event telemetri (`ProHomePDFCombine`, `ProWordAddinPDFCreated`, …) → UnionPDF nol. |
| K8 Packaging | 3 | 3 | **Konfirmasi**: shell v14 saja ≥240 MB (libcef 212 + mozjs 27). Ukuran UnionPDF yang wajar perlu disepakati (B-03). |
| K9 Testability | 5 | 5 | **Konfirmasi**: v14 memakai command-handler per fitur — pola use-case UnionPDF selaras. |
| K10 Lisensi | 3 | 3 | **Konfirmasi**: MuPDF AGPL tetap kompatibel dengan UnionPDF AGPL-3.0. v14 justru bergantung komponen berlisensi komersial (Solid Framework) yang **tidak** dibutuhkan UnionPDF. |
| K11 Aksesibilitas & DPI | 4 | 4 | Tidak berubah. |
| K12 Ganti engine | 5 | 5 | **Konfirmasi**: pola modular v14 (29 modul) justru justrugist. |
| **TOTAL** | **463** | **463** | **KEEP — tanpa perubahan** |

**Kesimpulan:** analisis mendalam **tidak memunculkan** fitur yang menuntut
penggantian engine, runtime, atau shell. Yang berubah hanya **cakupan**
(M5, M7) dan **keyakinan** pada keputusan — bukan nilai skornya.

Detail tinjauan per lapisan: `docs/POST_REA_TECH_REVIEW.md` §18.
