# TECH_SPIKES.md — Hasil Technical Spike

**Status:** S1–S12 tercatat (S12 = NO-GO untuk klaim packaging). Semua angka berlaku
untuk **stack lama** (Python + PySide6 + PyMuPDF) dan sejak 2026-10-21 berperan sebagai
**benchmark**, bukan bukti untuk kandidat stack baru. Rencana spike restart: **§R**
(belum dieksekusi).
**Sesi:** `2026-10-20T1624+0700`
**Mesin:** Windows 11 build 26300, x64, 12 core, 16 GB (RAM terpasang tidak diverifikasi).
**Python:** 3.13.9 (64-bit) — `D:\dokumentasi\Project\UnionPDF\.venv`
**Library terukur:** PyMuPDF 1.27.2.2 (MuPDF 1.27.2.2), PySide6 6.11.0 (Qt 6.11.0)

Semua skrip berada di `spikes/`, hasil JSON di `spikes/out/`.
Eksperimen **terpisah** dari kode produksi.

---

## Ringkasan status

| ID | Pertanyaan | Hasil | Verdict |
|---|---|---|---|
| S1 | Render + text layer | 33,87 ms/halaman @2×, text layer terbaca | **GO** |
| S2 | Operasi halaman + round-trip | merge/split/rotate/delete lolos, reopen konsisten | **GO** |
| S3 | Anotasi | highlight/note/freetext/shape lolos, 3 anot reopen | **GO** |
| S4 | Form | create → fill → save → reopen, nilai bertahan | **GO** |
| S5 | Redaksi | target **tidak** bisa diekstrak ulang, teks lain utuh | **GO** |
| S6 | Gambar/stempel/watermark/footer | semua lolos | **GO** |
| S7 | Ekspor PNG | 21,3 ms/halaman median | **GO** |
| S8 | Font + enkripsi AES-256 | builtin + TTF embed + enkripsi + re-auth lolos | **GO** |
| S9 | Background job + cancel | cancel dihormati, event loop tetap responsif | **GO** |
| S10 | OCR lokal | Windows OCR: 145,3 ms/halaman, 3/4 baris tepat | **GO (dengan catatan)** |
| S11 | Qt shell offscreen | Qt 6.11.0 jalan, DPR 1,0 | **GO** |
| S12 | Packaging | PyInstaller **belum** diuji | **NO-GO untuk klaim**, blocker |

---

## S1 — Render dan text layer

**Skenario:** PDF 12 halaman, 4 ukuran halaman campuran (A4 potrait/landscape, Letter, A5),
zoom 2× (144 DPI).

| Metrik | Nilai |
|---|---|
| Render median | **33,87 ms/halaman** |
| Render min / max | 17,81 ms / 39,38 ms |
| PNG median | 26.919 byte/halaman |
| Ekstraksi teks | Berhasil — 13 word pada halaman 1 |
| `Page.search_for` | 12 hit pada 12 halaman |

**Kesimpulan:** MuPDF menutup kebutuhan M1 (viewer) secara lengkap: render cepat, text
layer terbaca, pencarian berfungsi. **Tidak ada kebutuhan engine render kedua.**

---

## S2 — Operasi halaman dan round-trip

**Skenario:** sumber 12 halaman → merge dengan 2 halaman lain, split halaman 3–6,
rotate 90° + delete halaman 1, simpan, buka ulang.

| Uji | Expected | Actual | Status |
|---|---|---|---|
| Merge | 14 halaman | 14 halaman | PASS |
| Split (hal. 3–6) | 4 halaman | 4 halaman | PASS |
| Rotate + delete | 11 halaman, rot 90° | 11 halaman, rot 90° | PASS |
| Reopen hasil merge | teks halaman 1 utuh | "UnionPDF fixture page 1" | PASS |

**Dokumen besar (500 halaman, 0,17 MB):**

| Metrik | Nilai |
|---|---|
| Buka | 11,69 ms |
| `page_count` | 0,10 ms |
| Render halaman 0 @2× | 32,51 ms |
| Ekstraksi word | 0,21 ms |
| Simpan 500 halaman (deflate) | 12,34 ms |

**Kesimpulan:** target performa M2/M3 tercapai dengan margin besar. Batas
>5.000 halaman belum diuji → lihat `U-04` di `REA_FINDINGS.md`.

---

## S3 — Anotasi

| Anotasi | API | Hasil reopen |
|---|---|---|
| Highlight | `add_highlight_annot` | type `Highlight` ✓ |
| Note/Text | `add_text_annot` | type `Text` ✓ |
| FreeText | `add_freetext_annot` | type `FreeText` ✓ |
| Bentuk vektor | `draw_rect` / `draw_circle` | tersimpan di content stream (bukan anotasi) ✓ |

Jumlah anotasi setelah reopen: **3** (benar — bentuk vektor bukan objek anotasi).

**Kesimpulan:** M4 (anotasi) layak. Punch/underline/strikeout belum diuji →
dicatat di `TEST_PLAN.md`.

---

## S4 — Form (AcroForm)

**Skenario:** buat widget text field + checkbox → simpan → isi → simpan → buka ulang.

| Tahap | Hasil |
|---|---|
| `Page.add_widget` (text field "nama_lengkap") | Berhasil |
| `Page.add_widget` (checkbox "setuju") | Berhasil |
| Isi ulang: text field | "Diisi Uji" ✓ |
| Isi ulang: checkbox | `True` ✓ |
| Reopen: text field | "Diisi Uji" ✓ |
| Reopen: checkbox | `"Yes"` (label on-state, bukan boolean) ✓ |

**Kesimpulan:** round-trip form bekerja. **Catatan API:** nama method adalah
`add_widget`, bukan `insert_widget`; `field_fontsize` tidak ada di 1.27 —
gunakan `text_fontsize`. Lihat `REA_LIMITATIONS.md` L-08.

---

## S5 — Redaksi (uji keamanan)

**Skenario:** PDF berisi "CONFIDENTIAL PAYLOAD 9999" dan teks publik.
Redact → apply → simpan → **ekstrak ulang seluruh teks**.

| Pemeriksaan | Expected | Actual | Status |
|---|---|---|---|
| Teks target masih bisa diekstrak? | Tidak | **Tidak** (`secret_still_extractable: false`) | **PASS** |
| Teks publik masih ada? | Ya | Ya | PASS |
| Panjang teks sesudah | — | 46 char (hanya teks publik) | PASS |

**Kesimpulan:** redaksi bukan sekadar "kotak hitam"; isi target benar-benar
dihapus dari content stream. Ini membenarkan acceptance criterion M7:
**redaksi wajib diverifikasi dengan ekstraksi ulang, bukan dengan inspeksi visual.**

**Batas yang jujur:** ini dokumen sintetik sederhana. Belum diuji pada dokumen
dengan XMP metadata, thumbnail lama, embedded object, atau layer
→ lihat `REA_LIMITATIONS.md` L-07.

---

## S6 — Gambar, stempel, watermark, footer

| Uji | Hasil |
|---|---|
| `insert_image` (PNG 240×80) | 1 image pada reopen ✓ |
| Teks watermark | "WATERMARK" terbaca ✓ |
| Footer teks | "Footer teks" terbaca ✓ |

**Kesimpulan:** M3 (create & augment) layak.

---

## S7 — Ekspor ke gambar

6 halaman diekspor ke PNG @1,5×: median **21,3 ms/halaman**, max 22,39 ms.
Mendukung fitur "PDF → gambar" pada M9.

---

## S8 — Font dan keamanan

| Uji | Hasil |
|---|---|
| Font bawaan (helv / tiro / cour) | ✓ |
| Embed font eksternal (`arial.ttf`) | ✓ (`insert_font`) |
| Enkripsi **AES-256** | ✓ `PDF_ENCRYPT_AES_256` |
| Reopen terenkripsi | `needs_pass=1` → `authenticate("user")` berhasil ✓ |
| Teks terbaca sesudah autentikasi | "Helvetica built-in / Times built-in / Courier built-in" ✓ |

**Kesimpulan:** M7 (keamanan) punya fondasi enkripsi yang sudah terbukti.

---

## S9 — Background job, progress, cancel

Pola: `QThreadPool` + `QRunnable` + `QObject` terpisah untuk signal (PySide6
tidak mengizinkan `Signal` pada `QRunnable` langsung) + token pembatalan.

| Kasus | Hasil |
|---|---|
| Run penuh (20 langkah × 20 ms) | 20 event progress, selesai normal, 421,8 ms |
| Cancel di tengah (200 langkah, cancel @300 ms) | **Berhenti di langkah 15**, `cancelled: true`, 314,6 ms |
| Cancel seketika (cancel @1 ms) | Berhenti di langkah 1, 29,5 ms |
| Event loop saat worker berjalan | **661 tick/detik** (tetap responsif) |

**Kesimpulan:** M0–M6 punya pola background job + progress + cancel yang terbukti.
Caveat: `QThreadPool` dengan beberapa worker Python **berbagi GIL** → pekerjaan
CPU-bound murni Python tidak akan paralel. Untuk operasi berat, gunakan
`QProcess` ke helper terpisah. Dicatat di `KNOWN_ISSUES.md`.

---

## S10 — OCR lokal

Empat kandidat diuji. Fixture: PDF "scan" sintetik (gambar grayscale 1240×1754,
4 baris teks, tanpa text layer).

| Kandidat | Hasil | Detail |
|---|---|---|
| **A. Tesseract** | ❌ tidak terpasang | tidak ada di PATH, `TESSDATA_PREFIX` kosong |
| **B. Windows.Media.Ocr** | ✅ **BERHASIL** | 145,3 ms/halaman, 3/4 baris persis |
| **C. rapidocr-onnxruntime** | ❌ tidak diuji | belum dipasang; butuh ±150 MB model |
| **D. MuPDF `get_textpage_ocr`** | ❌ gagal | *"No tessdata specified and Tesseract is not installed"* |

### Detail kandidat B (Windows OCR)

- Binding: `winrt-Windows.Media.Ocr` 3.2.1 (paket `winrt-*`, bukan `winsdk` beta).
- Teks terbaca:
  `"INVOICE NUMBER 2026-0042 Customer: PT Union PDF Nusantara Total Amount: Rp 1.250.OOO Due Date: 30 November 2026"`
- Akurasi: **3 dari 4 baris persis**. Baris "Total Amount: Rp 1.250.000" dibaca
  `"Rp 1.250.OOO"` — nol dibaca sebagai huruf O. **Kesalahan OCR realistis; dicatat
  apa adanya.**
- Tanpa unduhan model, sepenuhnya offline, tanpa biaya.

### Temuan API WinRT (penting untuk implementasi)

| Yang diharapkan | Yang sebenarnya (winrt 3.2.1) |
|---|---|
| `StorageFile.get_file_from_path(path)` | `StorageFile.get_file_from_path_async(path).get()` |
| `file.open_async(FileAccess.READ)` | `file.open_read_async().get()` |
| `FileAccess` | `FileAccessMode` |
| `OcrEngine.get_available_recognizer_languages()` | **tidak diekspos** oleh binding 3.2.1 |
| `OcrEngine.try_create_from_user_profile_languages()` | tersedia ✓ |
| `winrt.windows.storage.streams` | paket terpisah, wajib diinstal |

**Kesimpulan S10:** OCR lokal **mungkin tanpa dependency eksternal** memakai API
Windows bawaan. Tapi: (1) daftar bahasa tidak bisa dienumerasi lewat binding
3.2.1 → daftar bahasa harus ditampilkan dari sumber lain; (2) `winsdk` 1.0.0b10
adalah **beta** dan tidak boleh jadi fondasi; (3) akurasi perlu diukur pada
dokumenscan nyata.

**Rekomendasi:** M5 memakai **Windows OCR sebagai jalur utama** +
**Tesseract sebagai opsi lanjut (pengguna/path kustom)** bila akurasi Windows
OCR kurang pada bahasa tertentu. Opsi C (rapidocr) ditunda sampai ada kebutuhan
dimensi.

---

## S11 — Qt shell

| Metrik | Nilai |
|---|---|
| Qt | 6.11.0 |
| Platform | offscreen (headless) |
| `QApplication` | berhasil, widget dibuat & `processEvents()` jalan |
| DPR primary screen | 1,0 |
| Logical DPI | 96 |

---

## S12 — Packaging

| Metrik | Nilai |
|---|---|
| PyInstaller | ❌ **belum terpasang** di venv |
| MuPDF native payload | **50,62 MB** (`mupdfcpp64.dll` 24,46 MB + `_mupdf.pyd` 11,75 MB) |
| PySide6 addons (uncompressed wheel) | 168,7 MB |

**Status: belum ada klaim packaging.** Ukuran akhir TIDAK diprediksi angka
palsu; `NOT_MEASURED`. Blocker: `B-03` (lihat `BLOCKERS.md`). Wajib build
one-dir lebih dulu untuk mengukur, lalu one-file bila perlu.

---

## Ringkasan bukti yang mendukung keputusan stack

1. **Satu engine (MuPDF) menutup M1–M4 + M7.** Semua kemampuan di atas terukur PASS.
2. **Latensi render ~34 ms/halaman** → zoom & scroll mulus tanpa worker tambahan.
3. **Redaksi terbukti aman** (ekstraksi ulang kosong) → M7 punya acceptance
   criterion yang measurable.
4. **Pola background job + cancel terbukti** → UI tidak akan membeku.
5. **OCR Windows berhasil tanpa model eksternal** → M5 tidak perlu biner pihak
   ketiga sebagai syarat minimum.
6. **Risiko utama yang tersisa:** lisensi AGPL (bukan teknis), ukuran distribusi,
   dan kemampuan edit teks in-place (M8).

## Yang BELUM terbukti (jangan diklaim)

- Edit teks existing dengan reflow (M8) — **belum diuji sama sekali**.
- Flattening anotasi/form.
- Redaksi pada dokumen dengan metadata & thumbnail (L-07).
- XFA form.
- Text embedding lengkap / subset font.
- Performa pada >5.000 halaman (U-04).
- Ukuran EXE final.
- Signer kriptografis (M10).
- Office → PDF (M9).

---

## R. Rencana spike restart (2026-10-21) — PERENCANAAN SAJA

| Field | Nilai |
|---|---|
| Status | **PLANNED** — tidak ada spike yang dibuat, di-scaffold, atau dijalankan |
| Sesi | `2026-10-21T1057+0700` |
| Persetujuan eksekusi | **Belum ada** (K-5 = perencanaan saja; K-6 instalasi belum disetujui) |
| Baseline | A = PDFium + QPDF · B = PDFium + Java/PDFBox · C = MuPDF/PyMuPDF worker (semua di bawah Tauri + React/TS + Rust) |
| Benchmark | Implementasi lama + S1–S12 (fixture yang sama dijalankan juga pada implementasi lama bila relevan) |

### R.1 Lokasi dan aturan (usulan, belum dibuat)

- Lokasi usulan: `experiments/restart/<RS-ID>-<baseline>/`, terpisah dari `src/`,
  `tests/`, dan `spikes/` lama. Folder output diusulkan di-gitignore.
- Fixture **sintetis** dibuat oleh generator yang dicatat (nama alat, versi, parameter);
  tidak memakai dokumen pribadi atau dokumen referensi proprietary.
- **Hindari bias satu engine:** fixture yang dipakai menguji engine X dibuat oleh engine
  lain; verifikasi output memakai minimal **satu pembaca independen** selain engine yang
  diuji.
- Pembaca independen yang **sudah ada** di mesin ini tanpa instalasi baru: PyMuPDF
  1.27.2.2 di `.venv` (berguna untuk memverifikasi A dan B; untuk C dibutuhkan pembaca
  lain, mis. PDFium).
- Semua angka dicatat apa adanya; target performa **tidak** dikarang. Toleransi ukuran
  ditetapkan pengguna sebelum RS-09.
- Format catatan tiap spike: pertanyaan · input · langkah · go · no-go · hasil · bukti ·
  keterbatasan · keputusan.

### R.2 Daftar spike dan kriteria

| ID | Pertanyaan | Baseline | Input | Go | No-go | Butuh instalasi (belum disetujui) |
|---|---|---|---|---|---|---|
| RS-00 | Biner PDFium mana yang provenance-nya dapat diterima? | A, B (C bila memakai PDFium) | Metadata rilis: upstream revision, pembangun, patch, workflow run, checksum penerbit, atestasi | Provenance tercatat lengkap dan diterima pengguna | Provenance tidak dapat ditelusuri atau ditolak pengguna | Unduh biner PDFium (atau toolchain build) |
| RS-01 | Apakah render, zoom, thumbnail, ekstraksi & pencarian teks benar dan dapat dibatalkan? | A, B (PDFium); C (MuPDF) | 5 fixture: ukuran halaman campuran, Latin, Unicode/Arab, gambar, 500 halaman | Semua halaman dirender; teks = ground truth; permintaan render usang dapat dibatalkan; waktu halaman pertama & RAM **dicatat** | Crash, teks salah pada fixture Latin, atau render tidak dapat dibatalkan | `pdfium-render` (crate), PDFium |
| RS-02 | Apakah anotasi yang dibuat tersimpan dan terbaca ulang dengan benar? | A (PDFium), B (PDFium & PDFBox), C (MuPDF) | Halaman kosong + halaman teks; subtipe CR-07 (+ CR-08 untuk B/C) | Setelah Save As & buka ulang: subtipe, rect, warna, isi sama di engine sendiri **dan** pembaca independen; area anotasi tidak kosong saat dirender | Subtipe P0 hilang/berbeda, atau tanpa appearance di pembaca independen tanpa jalur perbaikan | sama dengan RS-01; PDFBox (B) |
| RS-03 | Apakah form dapat diisi dan disimpan? | A, B, C | AcroForm sintetis: text, checkbox, radio, choice (dibuat engine lain) | Nilai & appearance bertahan setelah buka ulang di dua engine | Nilai hilang, appearance basi, atau struktur field rusak | idem |
| RS-04 | Apakah **field form baru** dapat dibuat? (dinilai terpisah dari RS-03) | A (kustom tingkat rendah, time-box), B (PDFBox), C (MuPDF) | Halaman kosong | Field text + checkbox dikenali sebagai field (nama, tipe, rect) oleh dua engine dan dapat diisi | Field tidak dikenali/tidak dapat diisi; untuk A: biaya kustom melampaui time-box yang ditetapkan | idem |
| RS-05 | Apakah page ops mempertahankan struktur sesuai scope? | A (PDFium/QPDF), B (PDFium/PDFBox), C (MuPDF) | Fixture dengan bookmark, link internal, anotasi, field form, 3 ukuran halaman | Jumlah/urutan/rotasi benar; teks per halaman utuh; item struktur **dalam scope yang ditetapkan sebelum uji** tetap valid; pemeriksa struktur tanpa error | Halaman/teks salah, atau item dalam scope rusak tanpa jalur perbaikan | idem; pemeriksa struktur (mis. QPDF) |
| RS-06 | Apakah Save As atomik dan kegagalan ditangani jujur? | Host (independen baseline) + engine | Fixture biasa; injeksi kegagalan: file tujuan terkunci, folder read-only, error tulis tersimulasi, cancel di tengah, proses worker dimatikan | Hash input tidak berubah; tidak ada file parsial di lokasi akhir; temp milik job dibersihkan; pesan error spesifik | Input berubah, file parsial dilaporkan sukses, atau error generik | Shell Tauri minimal (**scaffold butuh persetujuan**) |
| RS-07 | Apakah redaksi benar-benar menghapus data? | A (kustom), B (kustom), C (`apply_redactions`) | Fixture dengan rahasia di: teks, teks dalam XObject, gambar, vektor, anotasi, nilai field, metadata Info/XMP, teks tersembunyi | Rahasia **tidak** ditemukan oleh ekstraksi dua engine dan pemindaian stream terdekompresi pada channel yang dicakup; piksel area kosong; konten di luar area utuh; channel yang tidak dicakup didaftar | Kebocoran pada channel yang diklaim tercakup | idem |
| RS-08 | Adakah jalur signature kriptografis dengan library terpelihara? | A (cari library; bila tidak ada → `BLOCKED`), B (PDFBox + Bouncy Castle), C (`UNPROVEN`) | Sertifikat uji buatan sendiri (mis. `keytool` dari JDK/JRE yang ada — keberadaan alat belum diperiksa) | Tanda tangan valid menurut validator independen; perubahan pasca-tanda-tangan terdeteksi; kunci privat tidak dicatat | Tidak ada library terpelihara, atau validasi independen gagal | PDFBox + Bouncy Castle (B); library lain (A/C) |
| RS-09 | Berapa ukuran dan resource usage paket, dan apakah berjalan tanpa toolchain dev? | A, B, C | Build rilis per baseline | Ukuran installer, ukuran terpasang, runtime eksternal, RAM idle & setelah buka fixture, waktu startup & halaman pertama **dicatat**; aplikasi berjalan dengan PATH tanpa toolchain dev | Gagal berjalan tanpa toolchain, atau melampaui toleransi ukuran pengguna | Tauri CLI, bundler; JRE/jlink (B); bundler Python (C) |
| RS-10 | Apakah kegagalan worker ditangani tanpa merusak dokumen atau membekukan UI? | B (JVM), C (Python); A bila ada proses terpisah | Worker dimatikan, hang, respons rusak | UI tetap responsif; job gagal dengan status jelas; worker dapat dimulai ulang; tidak ada file rusak | UI membeku, file rusak, atau job "sukses" palsu | idem |

### R.3 Urutan yang diusulkan

| Fase | Spike | Alasan |
|---|---|---|
| 1 | RS-00, RS-01, RS-02 (bagian PDFium), RS-03 (bagian PDFium), RS-05 (bagian PDFium) | Dipakai A dan B; menentukan apakah A layak dilanjutkan |
| 2 | RS-04, RS-07, RS-08 untuk B dan C (A: penilaian kelayakan saja) | Pembeda utama antar-baseline |
| 3 | RS-06, RS-10 | Butuh shell host minimal (scaffold → persetujuan terpisah) |
| 4 | RS-09 | Butuh build per baseline; toleransi ukuran ditetapkan dulu |

Tidak semua spike harus selesai dalam satu sesi. Bila spike menunjukkan perubahan
teknologi material, pekerjaan **berhenti** dan meminta persetujuan baru.
