# POST_REA_TECH_REVIEW.md — Review Teknologi Pasca-Analisis

**Status:** selesai untuk M0 · **Gate:** WAJIB lolos sebelum implementasi utama
**Sesi:** `2026-10-20T1624+0700`
**Keputusan:** `docs/decisions/ADR-001-stack-baseline.md`

---

## 1. Ringkasan hasil REA

- Referensi: **Nitro PDF Pro 14.41.0.15** (1.014 berkas, 854,6 MB).
- Analisis **v1**: inventaris modul engine (29 domain `np_*.dll`) + dokumentasi
  publik v14.
- Analisis **v2** (2026-10-20, setelah izin inspeksi biner read-only):
  14.452 string UI dari 35 berkas `.mui`, 783 kontrol ribbon, 10.284 identifier
  fitur, analisis native Ghidra atas `np_pdfa.dll` (1.852 prosedur).
  → `docs/REA_FINDINGS.md` v2, `docs/research/V14_*.md`.
- Bukti teknis: 12 spike (`TECH_SPIKES.md`), 9 di antaranya PASS penuh.
- Konfirmasi ulang setelah v2: **§18** — stack **KEEP**, tanpa perubahan.

---

## 2. Kebutuhan yang sudah terbukti

| Kebutuhan | Bukti | Konsekuensi teknis |
|---|---|---|
| Render cepat + text layer | S1 (33,87 ms/hlm @2×) | Engine + cache render; QPixmap pada UI thread |
| Operasi halaman(round-trip aman) | S2 (merge/split/rotate/delete, reopen konsisten) | Operasi Via adapter, bukan Via UI |
| Anotasi & form | S3, S4 | Objek anotasi punya model sendiri |
| Redaksi yang benar-benar menghapus | S5 (target tidak ter-ekstrak) | Acceptance criterion berbasis ekstraksi |
| Font & enkripsi | S8 (AES-256 + re-auth) | Writer terpisah dari reader |
| Background job + cancel | S9 (cancel dihormati, loop responsif) | Job runner + token pembatalan |
| OCR lokal tanpa model eksternal | S10 (Windows OCR, 145,3 ms/hlm) | Adapter OCR, Tesseract opsional |

## 3. Kebutuhan yang masih belum pasti

| # | Kebutuhan | Status |
|---|---|---|
| U-01 | Edit teks existing + reflow tingkat paragraf | **UNKNOWN** — belum diuji di engine mana pun |
| U-04 | Performa >5.000 halaman | **UNKNOWN** |
| U-05 | Office→PDF (COM vs LibreOffice) | **UNKNOWN** |
| U-06 | Tanda tangan kriptografis | **UNKNOWN** |
| U-07 | Perilaku UI Nitro v14 | **UNKNOWN** (tidak relevanan untuk keputusan stack) |

## 4. Fitur berisiko tinggi

| Fitur | Risiko | Mitigasi |
|---|---|---|
| **Redaksi** | Klaim "terhapus" padahal masih di metadata/thumbnail | Verifikasi wajib lewat ekstraksi ulang **dan** pemeriksaan channel (L-07) |
| **Edit teks existing** | Content-stream surgery bisa merusak dokumen | DEFER ke M8; di M0–M7 sediakan overlay + redaksi-reinsert dengan label jujur |
| **OCR** | Windows OCR tidak bisa enumerasi bahasa; akurasi vary | Tesseract sebagai opsi lanjut; daftar bahasa dari sumber sendiri |
| **Dokumen rusak** | File salah urutan/terenkripsi/tidak lengkap | Error handling terpusat; jangan menimpa input |
| **Form XFA** | Format kompleks | DEFER total |

## 5. Implikasi terhadap UI

- Shell **native Windows** (bukan CEF): Qt 6.11, bobot 168 MB `pyside6-addons`
  diAvoid lewat build minimal.
- Fokus: panel thumbnail + canvas + toolbar + status bar.
- **Setiap kontrol hanya tampil jika benar-benar berfungsi.** Kalau engine tidak
  mendukung, sembunyikan atau beri label status jujur.
- Bedakan secara visual: overlay teks vs edit teks asli · searchable OCR vs
  rekonstruksi editable · kotak hitam vs redaksi aman · gambar tanda tangan vs
  signature kriptografis.
- Progress + cancel pada setiap operasi yang bisa lama.
- Error message harus informatif (yaitu + apa yang gagal + apa yang bisa dilakukan).

## 6. Implikasi terhadap engine PDF

- **Satu engine: MuPDF** (PyMuPDF 1.27.2.2). Tidak perlu engine kedua untuk
  render — dibuktikan S1.
- Semua akses engine lewat **interface `DocumentEngine`** agar dapat diganti
  (kriteria K12).
- Writer dan reader harus memakai **dokumen yang sama** yang di-copy/serialized,
  bukan membuat ulang dari model internal (mengurangi risiko kehilangan
  struktur).
- API beware: `add_widget` bukan `insert_widget`; `text_fontsize` bukan
  `field_fontsize` (L-08). Kunci versi.

## 7. Implikasi terhadap OCR

- **Jalur utama: `Windows.Media.Ocr`** (bawaan Windows, offline, tanpa model
  unduhan) → S10.
- **Jalur lanjut: Tesseract** (opsional;akibat Users/system) → dipakai bila
  Windows OCR tidak cukup atau bahasa tidak didukung.
- `rapidocr-onnxruntime` ditunda — hanya relevan bila butuh offline lintas
  platform atau bahasa non-Latin dengan model sendiri.
- Kontrak: `OcrEngine` interface dengan `recognize(page, language) -> OcrResult`
  (text + kotak kata), `progress`, `cancel`.
- Hasil OCR **wajib** ditulis sebagai lapisan teks tak terlihat, dan UI **wajib**
  menyatakan bahwa itu bukan teks yang bisa diedit.

## 8. Implikasi terhadap concurrency/background jobs

- Pola: `QThreadPool` + `QRunnable` + `JobSignals(QObject)` + `CancelToken`.
- **Peringatan GIL:** pekerjaan CPU-bound Python tidak paralel. Aturan:
  - I/O & operasi MuPDF → worker thread (`QThreadPool`).
  - Loops Python berat (mis.parsing batch) → `QProcess` ke helper terpisah.
- Semua operasi tulis ke disk: tulis ke file sementara, finalisasi setelah sukses,
  hapus file sementara bila gagal.

## 9. Implikasi terhadap packaging

- PyInstaller **belum diuji** → `B-03`. Build one-dir lebih dulu (lebih cepat
  dan lebih mudah debug), one-file menyusul.
- MuPDF payload 50,62 MB → gunakan `--exclude-module` untuk trimming PySide6
  (WebEngine, Charts, DataVisualization, dll. tidak dipakai).
- Target ukuran: **NOT_MEASURED** — tidak boleh diklaim sebelum diukur.
- Code signing **belum tersedia** → catatan jujur di `PACKAGING.md`.

## 10. Implikasi terhadap lisensi

- **MuPDF = AGPL-3.0** → UnionPDF harus AGPL-3.0 agar tetap gratis tanpa
  kewajiban lisensi berbayar.
- PySide6 = LGPL-3.0 → dinamis, exe satu bundling tetap harus memenuhi syarat
  LGPL (menyertakan lisensi + sumber pustaka yang relevan).
- OCR Windows = bagian dari OS, tanpa masalah redistribusi.
- Tesseract = Apache-2.0 (bebas, wajib sebut).
- **Belum ada klaim final** → `B-01` butuh persetujuan pengguna.

## 11. Kandidat stack awal

Awalnya (sebelum REA) kandidat implisit: *desktop Windows*. Tidak ada bahasa,
shell, atau engine yang terkunci. Itu disengaja.

## 12. Bagian kandidat yang **sesuai**

- Target **hanya Windows** → tidak perlu runtime lintas platform → Python +
  PySide6 cukup.
- Kebutuhan **satu engine untuk render + edit** → MuPDF memenuhi; composite
  PDFium+PdfSharp tidak.
- Kebutuhan **OCR offline tanpa unduhan model** → Windows OCR memenuhi.
- Kebutuhan **background job + cancel** → Qt thread pool memenuhi (S9).
- Kebutuhan **testability** → logika domain murni Python di balik interface.

## 13. Bagian kandidat yang **tidak sesuai**

| Kandidat | Tidak sesuai karena |
|---|---|
| .NET + WPF + PDFium + PdfSharp | Tidak ada API authoring anotasi/form/redaksi yang permissive (M3–M4 runtuh) |
| .NET + iText 7 | AGPL/komersial → likuidasi keunggulan lisensi; tidak ada MVP bebas |
| TypeScript + Electron | Dua engine (pdf.js + pdf-lib), M3–M4 tidak Practical, Electron besar |
| MuPDF untuk OCR | Butuh Tesseract → bukan zero-dependency |
| Windows OCR untuk enumerasi bahasa | Binding 3.2.1 tidak mengekspos API tersebut → daftar bahasa harus dari sumber lain |

## 14. Alternatif

- **pypdfium2 + pikepdf** (BSD-3 + MPL-2.0): avoids AGPL tetapi M3–M4 harus
  ditulis manual dan OCR jadi wajib Tesseract. Estimasi biaya +1–2 milestone.
  Dicatat sebagai rute cadangan di `STACK_EVALUATION.md` §7.
- **Java + PDFBox** (Apache-2.0): permissive, tapi menambah runtime JVM dan
  tetap lemah di authoring/redaksi.
- **Tauri + Rust**: shell bagus, tapi menambah runtime kedua + lapisan FFI.

## 15. Technical spike yang dilakukan

S1–S12 (`TECH_SPIKES.md`). Yang **tidak** dilakukan dan masih perlu:
spike M8 (edit teks), spike packaging one-dir, spike signature, spike Office→PDF.

## 16. Rekomendasi

**KEEP — A: Python 3.13 + PySide6 6.11 + MuPDF 1.27 (PyMuPDF) + Windows OCR.**

Dasar bukti: 9 dari 12 spike PASS pada kemampuan yang demanded M1–M4 + M7;
skor 463/500 (92,6 %) pada `STACK_EVALUATION.md`.

## 17. Alasan dan bukti (ringkas)

1. M3–M4 adalah pembeda utama dan **hanya MuPDF** yang menyediakannya dengan
   lisensi gratis → 60 poin K1+K4 melawan A.
2. Redaksi terbukti benar-benar menghapus (S5) — klaim keamanan sudah
   measurable.
3. Render 33,87 ms/halaman dan pembatalan job terbukti (S1, S9) → standar
   "modern" terpenuhi.
4. OCR Windows berhasil tanpa model eksternal (S10) → M5 tidak terblokir biaya.
5. Kekurangan A yang **tidak** bisa diabaikan: AGPL (bisa dikelola), ukuran
   distribusi (bisa diukur & di-trim), dan M8 (sudah di-DEFER).

**Yang TIDAK boleh diklaim:** bahwa A "setara Nitro". Yang terbukti hanya
cakupan M1–M4 + M7 pada fixture sintetik.

---

## 18. Konfirmasi ulang setelah analisis mendalam (v2)

**Tanggal:** 2026-10-20 · **Sesi:** `2026-10-20T1700+0700`
**Pemicu:** izin inspeksi biner read-only diberikan → analisis referensi
diperdalam (14.452 string UI, 783 kontrol ribbon, 10.284 identifier fitur,
analisis native Ghidra).

Master prompt mewajibkan tinjauan ulang bila ada temuan baru. Berikut
evaluasi ulang terhadap setiap yang dianalisis di §6–§14.

### 18.1-shell desktop — **TIDAK BERUBAH**

Temuan v2 justru **menguatkan** Qt:
- v14 memakai CEF: `libcef.dll` 212 MB + `mozjs-102.dll` 27 MB + `d3dcompiler_47.dll`
  + `chrome_elf.dll` → **≥240 MB** hanya untuk shell.
- 90 toolbar kontekstual + 14 tab → butuh sistem kontrol yang matang. Qt Widgets
  memberi `QToolBar`, `QStackedWidget`, `QGraphicsView` — cukup.
- Manifest `asInvoker` → aplikasi berjalan tanpa UAC. UnionPDF harus sama
  (Qt tidak butuh UAC).

**Kesimpulan:** Qt 6.11 tetap. Tidak ada alasan untuk menambah runtime kedua.

### 18.2 UI framework — **TIDAK BERUBAH**

Temuan baru justru *memperkuat* keputusan **tidak menyalin** struktur v14.
14 tab v14 terisi 373 kontrol; sebagian besar (Help/Smart Tips, IManage,
NitroCloud, Backstage) **vendor-specific** atau bernilai rendah bagi tool
lokal. UnionPDF merancang 5–6 tab sendiri (Home, Edit, Review, Protect,
Tools, Help) — lebih sedikit, lebih fokus, tanpa mengorbankan cakupan fitur.

### 18.3 Application core — **DIPERKUAT**

v14 memakai pola *command-handler per fitur*
(`AVCmdHandler*_RegisterCommandsProc` / `_WorkProc`) + plugin (`*_plugin::init`).
Ini **setiap** fitur punya register (UI) + work (logika). Pola yang sama sudah
dipakai UnionPDF di `application/` (use case) + `engine/` (adapter).

**Kesimpulan:** arsitektur use-case UnionPDF selaras. Tidak berubah.

### 18.4 Rendering — **TIDAK BERUBAH**

Tidak ada temuan baru. Spike S1 tetap acuan: 33,87 ms/halaman @2×.

### 18.5 PDF modification — **TIDAK BERUBAH, tapi cakupan M7 bertambah**

Temuan baru (T-2): v14 punya **penghapusan 12 channel data tersembunyi**.
Ini menambah requirement M7, bukan mengubah stack.

MuPDF punya `apply_redactions(images=…, graphics=…, text=…)` — parameter
channel yang **cocok** dengan kebutuhan ini. Perlu verifikasi mana channel
yang benar-benar ter-cover (L-07 masih terbuka; tidak boleh diklaim).

### 18.6 OCR — **TIDAK BERUBAH**

Temuan baru: v14 punya 2 mode (Searchable / Searchable+Editable) dan
**melewati** halaman yang sudah punya text. Ini menambah requirement M5:
- deteksi halaman tanpa text layer (otomatis)
- opsi paksa untuk halaman ber-text
- label mode yang jujur

Jalur OCR tetap Windows OCR (spike S10, 145,3 ms/hlm) + Tesseract opsional.
Temuan v2 tidakprovides alasan untuk mengganti.

### 18.7 Concurrency — **TIDAK BERUBAH**

Tidak ada temuan baru. Batas GIL Python tetap berlaku (spike S9).

### 18.8 Packaging — **TIDAK BERUBAH**

Tidak ada temuan baru. Ukuran tetap `NOT_MEASURED` (B-03). Data baru: shell
v14 ≥240 MB → toleransi ukuran UnionPDF (>200 MB) **wajar** bila engine PDF
satu. Ini strengthens argumen bahwa ukuran UnionPDF yang wajar perlu
disepakati pengguna (B-03).

### 18.9 Lisensi — **DIPERKUAT**

Temuan v2: `np_pdfa.dll` memuat `solid_framework` (Solid Framework) yang
mengimplementasikan **PDF/A + validasi tanda tangan** — komponen **tidak
permissive** (Solid Framework berlisensi komersial untuk sebagian fungsi).
v14 *membayar* lisensi itu.

UnionPDF tidak perlu: MuPDF (AGPL) menutup M1–M9, dan M10/M12 (PDF/A,
validasi tanda tangan) sudah **DEFER** — jadi kebutuhan berlisensi komersial
tidak muncul di baseline.

Konsekuensi: **AGPL-3.0 untuk UnionPDF tetap benar dan tidak worsened** oleh
temuan v2.

### 18.10 Storage — **TIDAK BERUBAH**

Temuan baru: v14 memakai registry Windows (`SOFTWARE\Nitro\PDF Pro\14\Settings`)
dan **Digital ID PKCS#12 terikat profil Windows** untuk kunci privat.

UnionPDF: **menolak** menulis registry (mengorhati §6). Kunci privat (M10)
akan memakai Windows Credential Manager atau PKCS#12 dengan password terpisah
di lokasi yang dikendalikan pengguna. Tetap tanpa database.

### 18.11 Testing — **DIPERKUAT**

Temuan v2 memberi **corpus fixture** yang sah: 14.452 string UI berisi label
dialog, opsi, dan **pesan error**. Ini bahan uji yang sangat baik untuk
menulis pesan UnionPDF yang setara — tanpa menyalin teks proprietary.

**Rencana:** derived test cases dari `V14_UI_EVIDENCE.md` menjadi checklist
pesan error di M7 (password salah, dokumen terkunci, form field bentrok,
sertifikat kedaluwarsa, lampiran berbahaya).

### 18.12 Rekomendasi akhir — **KEEP, tanpa perubahan**

| Aspek | Status |
|---|---|
| Stack | **KEEP** — Python 3.13 + PySide6 6.11 + MuPDF 1.27 + Windows OCR |
| Skor | 463/500 (92,6 %) — **tidak berubah** |
| Pemicu migrasi | **Tidak ada** |
| Perubahan | Hanya **penambahan cakupan** (M5, M7) + **konfirmasi arsitektur** |

**Alasan ringkas:** analisis v2 tidak memunculkan fitur yang memerlukan
penggantian engine, runtime, atau shell. Justru sebaliknya: ia mengonfirmasi
bahwa (a) shell CEF v14 terlalu berat, (b) pola command-handler cocok dengan
UnionPDF, (c) MuPDF tetap mencakup inti, (d) lisensi AGPL tetap memadai
karena v14 bergantung komponen berlisensi komersial yang tidak diperlukan
UnionPDF.

**Yang berubah dariADR-001:** tidak ada perubahan stack. Yang berubah adalah
**cakupan** M5 dan M7, dan-confidence bahwa keputusan awal benar (bukan
sekadar "sudah mulai menulis kode").

- Referensi: **Nitro PDF Pro 14.41.0.15** (1014 berkas, 854,6 MB).
- Analisis: inventaris modul engine (29 domain `np_*.dll`) + dokumentasi publik
  v14. **Tanpa** inspeksi biner, tanpa observasi UI
  (`REA_LIMITATIONS.md` L-01, L-02).
- Bukti teknis: 12 spike (`TECH_SPIKES.md`), 9 di antaranya PASS penuh.
