# POST_ALL_REFERENCES_TECH_REVIEW.md — Review Teknologi Pasca-Tiga-Referensi

| Field | Nilai |
|---|---|
| Status | **DRAFT review — tidak memuat keputusan** |
| Sesi | `2026-10-21T1057+0700` |
| Masukan | `docs/ANALYSIS_NITRO14.md`, `docs/ANALYSIS_STIRLING_PDF.md`, `docs/ANALYSIS_PDFGEAR.md`, spike lama S1–S12 (`docs/TECH_SPIKES.md`), sumber primer upstream (§5) |
| Menggantikan | Tidak menggantikan apa pun secara otomatis. `docs/POST_REA_TECH_REVIEW.md` tetap ada sebagai histori (dasar ADR-001) |
| Stack final | **BELUM DISETUJUI** |

## Label bukti

| Label | Arti |
|---|---|
| `UPSTREAM-DOC` | Tertulis di header/dokumentasi resmi proyek, dibaca pada sesi ini |
| `WRAPPER-DOC` | Tertulis di dokumentasi wrapper, dibaca pada sesi ini |
| `MEASURED-OLD` | Diukur pada mesin ini oleh spike lama (2026-10-20), stack Python lama |
| `STATIC-REF` | Disimpulkan dari analisis statis aplikasi referensi; **bukan** perilaku runtime |
| `NOT-VERIFIED` | Diketahui umum tetapi tidak diverifikasi dari sumber primer pada sesi ini |
| `UNPROVEN` | Belum diuji pada mesin ini |
| `UNKNOWN` | Belum diketahui |

---

## 1. Apa yang ditunjukkan tiga referensi (`STATIC-REF`)

| Aspek | Nitro PDF Pro 14 | Stirling-PDF 3.2.0 | PDFgear 3.0.0 |
|---|---|---|---|
| Shell | Native C++/MFC | Tauri v2 (Rust + WebView2) → server lokal Spring Boot | .NET Framework 4.6.2 / WPF + WebView2 |
| Engine yang terlihat | Modul proprietary `np_*` + komponen komersial | Apache PDFBox 3.0.8 + PDFium (jpdfium) | Pdfium.Net SDK, Patagames, SautinSoft PDF Focus, Syncfusion (komersial) |
| Tool berat | dibundel | Ghostscript, QPDF, Tesseract, LibreOffice **eksternal, tidak dibundel** | Tesseract + NsOCR **dibundel** |
| Ukuran terpasang (fakta referensi) | 854,6 MB | 256,4 MB | 369,2 MB |

Pelajaran yang boleh ditarik (dengan batas):

1. Tidak satu pun referensi terlihat mengandalkan PDFium **saja**. Stirling — yang
   shell-nya paling dekat dengan kandidat Tauri — memasangkan PDFium dengan PDFBox.
2. Analisis statis **tidak** membuktikan engine mana menjalankan operasi apa
   (Stirling S-xx dan PDFgear G-03 masih terbuka). Pemetaan "engine → operasi" untuk
   UnionPDF harus dibuktikan oleh spike sendiri.
3. Ukuran referensi adalah fakta tentang **referensi**, bukan estimasi UnionPDF.

---

## 2. Fakta kapabilitas yang diverifikasi

### 2.1 PDFium — API upstream (`UPSTREAM-DOC`, header `public/*.h`, cabang `main`)

Hampir semua API di bawah berlabel **"Experimental API"** di header — perubahan
tanda tangan antar-rilis mungkin terjadi.

| Kapabilitas | API upstream | Batasan tertulis | Status untuk UnionPDF |
|---|---|---|---|
| Membuat anotasi | `FPDFPage_CreateAnnot`, `FPDFAnnot_IsSupportedSubtype` | Subtipe yang didukung untuk dibuat: circle, fileattachment, freetext, highlight, ink, link, popup, square, squiggly, stamp, strikeout, text, underline | `SUPPORTED_BY_API` untuk 13 subtipe itu; perilaku appearance & round-trip `UNPROVEN` |
| Subtipe tidak dapat dibuat | — | line, polygon, polyline, caret, widget, redact, dll. tidak ada di daftar | `REQUIRES_CUSTOM` atau engine lain |
| Edit isi anotasi | `FPDFAnnot_AppendObject`, `UpdateObject`, `RemoveObject` | Hanya **ink dan stamp** | Terbatas |
| Atribut anotasi | `SetRect`, `SetColor`, `SetAP`, `AppendAttachmentPoints`, `AddInkStroke`, `SetBorder`, `SetStringValue`, `SetFlags`, `SetURI`, `AddFileAttachment` | `SetColor` gagal bila appearance stream sudah ada | Apakah PDFium membangkitkan appearance stream untuk anotasi baru: `UNPROVEN` |
| Hapus anotasi | `FPDFPage_RemoveAnnot` | — | `SUPPORTED_BY_API` |
| Isi form | `FORM_OnChar`, `FORM_ReplaceSelection`, `FORM_SelectAllText`, `FORM_SetIndexSelected` (+ lingkungan form-fill) | Pengisian lewat simulasi interaksi | `SUPPORTED_BY_API`; round-trip `UNPROVEN` |
| Baca/flag field | `FPDFAnnot_GetFormField{Name,Type,Value,Flags,...}`, `FPDFAnnot_SetFormFieldFlags` | — | `SUPPORTED_BY_API` |
| **Membuat field form baru** | Tidak ditemukan; widget tidak termasuk subtipe yang bisa dibuat | — | `REQUIRES_CUSTOM` (penulisan kamus tingkat rendah) atau engine lain |
| Flatten | `FPDFPage_Flatten(page, FLAT_NORMALDISPLAY/FLAT_PRINT)` | — | `SUPPORTED_BY_API`; mutu `UNPROVEN` |
| Operasi halaman | `FPDF_ImportPages`, `FPDF_ImportPagesByIndex`, `FPDF_ImportNPagesToOne`, `FPDFPage_New`, `FPDFPage_Delete`, `FPDFPage_SetRotation`; `FPDF_MovePages` (tercantum di binding `pdfium-render`) | Pemeliharaan struktur (bookmark, link antar-halaman, form) saat import: `UNKNOWN` | `SUPPORTED_BY_API`; pemeliharaan struktur `UNPROVEN` |
| Tambah konten | `FPDFPageObj_NewTextObj`, `FPDFPageObj_NewImageObj`, `FPDFText_SetText`, `FPDFPage_InsertObject`, `FPDFPage_GenerateContent` | — | `SUPPORTED_BY_API` (watermark/teks/gambar overlay) |
| Hapus objek halaman | `FPDFPage_RemoveObject` | Granularitas objek; memotong sebagian glyph dalam satu objek teks perlu kode sendiri | Bahan untuk redaksi kustom |
| Simpan | `FPDF_SaveAsCopy`, `FPDF_SaveWithVersion`; flag `FPDF_INCREMENTAL`, `FPDF_NO_INCREMENTAL`, `FPDF_REMOVE_SECURITY` | **Tidak ada** flag/API untuk **menulis** enkripsi | Save `SUPPORTED_BY_API`; enkripsi butuh engine lain |
| Signature | `FPDF_GetSignatureCount`, `FPDFSignatureObj_Get{Contents,ByteRange,SubFilter,Reason,Time,DocMDPPermission}` | **Hanya introspeksi** | Signing butuh library lain; validasi kriptografis butuh library lain |
| Redaksi | Konstanta `FPDF_ANNOT_REDACT` ada, tetapi tidak dapat dibuat dan tidak ada API "apply redaction" | — | `REQUIRES_CUSTOM`, `UNPROVEN`, risiko tinggi |
| Thread safety | — | `pdfium-render`: PDFium tidak dijamin thread-safe; disarankan pemrosesan paralel per-proses | Desain job harus memperhitungkan |

### 2.2 `pdfium-render` (Rust) — apa yang diekspos wrapper (`WRAPPER-DOC`)

| Item | Nilai |
|---|---|
| Versi terbaru (README/Cargo.toml) | 0.9.4 |
| Lisensi | `MIT OR Apache-2.0` (Cargo.toml) |
| Build PDFium yang ditargetkan | fitur `pdfium_latest` = `pdfium_7881`; tidak membundel PDFium |
| Pembuatan anotasi | ditambahkan pada 0.8.20 ("annotation creation functions to `PdfPageAnnotations`") |
| Isi field teks | `PdfFormFieldText::set_value()` sejak 0.8.21 |
| Flatten | `PdfPage::flatten()` (0.8.19) |
| Lainnya | concatenation, watermark (contoh), introspeksi signature, attachment, pembuatan objek teks/path/bitmap |
| Akses API mentah | trait binding publik sejak 0.9.2 → fungsi upstream yang belum dibungkus dapat dipanggil secara `unsafe` |
| Thread safety | fitur `thread_safe` (default) menserialisasi semua panggilan lewat mutex |
| Status di mesin ini | **Belum diuji** |

### 2.3 Provenance biner PDFium

| Sumber | Penerbit | Fakta terverifikasi | Status |
|---|---|---|---|
| `github.com/bblanchon/pdfium-binaries` | Komunitas (Benoît Blanchon, kontributor) | *"This project isn't affiliated with Google or Foxit"*; build otomatis mingguan sejak 2017 via GitHub Actions; repo memuat folder `patches/`; lisensi MIT untuk repo build | **Bukan build resmi Google.** Biner = PDFium + patch pihak ketiga |
| Source upstream `pdfium.googlesource.com/pdfium` | PDFium Authors | Lisensi BSD-style (header) | Build sendiri = provenance terkendali; biaya toolchain `NOT_MEASURED` |
| `paulocoutinhox/pdfium-lib` | Komunitas | Disebut `pdfium-render` untuk Android/iOS/macOS/WASM | Tidak dievaluasi |
| Distribusi biner resmi Google | — | Tidak ditemukan pada sumber yang diperiksa | Jangan diasumsikan ada |

Data yang wajib dicatat sebelum biner dipakai (belum dilakukan): upstream + revisi
PDFium (nomor build Chromium), pembangun/distributor, tag rilis, URL run workflow,
daftar patch yang diterapkan, checksum yang dipublikasikan penerbit (bila ada),
atestasi artefak (bila ada — `UNKNOWN`), dan daftar lisensi komponen pihak ketiga di
dalam biner (FreeType, dsb. — `NOT-VERIFIED`). **Hash yang dihitung setelah unduh hanya
membuktikan integritas salinan, bukan asal-usul.** Jaminan tertinggi: build ulang dari
commit + patch yang sama dan bandingkan.

### 2.4 Apache PDFBox 3.0 (`UPSTREAM-DOC` kecuali disebut lain)

| Kapabilitas | Bukti | Status |
|---|---|---|
| Minimum Java | Migration Guide: *"requires at least Java 8. Testing has been done up to Java 19."* | Fakta. Java lebih baru = kebijakan proyek |
| Kelas anotasi untuk dibuat | Migration Guide: `PDAnnotationCaret`, `FreeText`, `Ink`, `Polygon`, `Polyline`, `Sound`, `Circle`, `Square`, `Highlight`, `Squiggly`, `Strikeout`, `Underline` | `SUPPORTED_BY_API`; pembangkitan appearance `UNPROVEN` |
| AcroForm | `getAcroForm()` menerapkan fix-up: default font resources, field dari widget yatim, normal appearance stream "under certain conditions" | Fakta |
| Membuat field form | Contoh resmi pembuatan AcroForm dari nol (paket `examples`, a.l. `CreateEmptySignatureForm`, dalam pohon kelas 3.0.7) | `SUPPORTED_BY_API`; `UNPROVEN` di mesin ini |
| Signature | Contoh resmi `CreateSignature` ("signing a PDF with bouncy castle"), `CreateVisibleSignature2` (tag 3.0.0) | `SUPPORTED_BY_API` via contoh; nama API inti `NOT-VERIFIED` sesi ini; `UNPROVEN` |
| Dependensi signing | Bouncy Castle 1.75 (versi di Migration Guide) | Lisensi Bouncy Castle `NOT-VERIFIED` sesi ini |
| Enkripsi | `NOT-VERIFIED` sesi ini (API protection policy dikenal umum) | Perlu verifikasi dokumen |
| Penyimpanan | Kompresi default; *"The input file must not be used as output"* | Selaras dengan kebijakan Save As |
| Redaksi | Tidak ditemukan API redaksi tingkat tinggi pada sumber yang diperiksa | `REQUIRES_CUSTOM` |
| Render | `NOT-VERIFIED` sesi ini | Tidak dibutuhkan bila render oleh PDFium |
| Integrasi dengan Tauri | Proses JVM terpisah (sidecar) + IPC stdin/stdout atau pipe; tanpa HTTP server | Ukuran JRE/jlink `NOT_MEASURED` |

### 2.5 QPDF (`UPSTREAM-DOC`: "What is qpdf?")

| Kelas kapabilitas | QPDF | Catatan |
|---|---|---|
| Transformasi struktur (object stream, linearization, xref) | **Ya** | "structural, content-preserving transformations" |
| Operasi halaman (merge, split, manipulasi daftar halaman) | **Ya** | |
| Enkripsi / password | **Ya** | disebut di dokumentasi |
| Optimasi | Sebagian (struktural) | Optimasi gambar `NOT-VERIFIED` |
| Rendering | **Tidak** | "not … a PDF viewer" |
| Ekstraksi teks | **Tidak** | "knows nothing about the semantics of PDF content streams" |
| Content editing / pembuatan konten | **Tidak** (tingkat tinggi) | "not a PDF content creation library" |
| Secure redaction | **Tidak** | Tidak boleh ditempatkan sebagai engine redaksi |
| Konversi format | **Tidak** | |
| Lisensi | `NOT-VERIFIED` sesi ini | Wajib diverifikasi sebelum dipakai |

Peran QPDF yang masuk akal: pemeriksa struktur independen (`qpdf --check`) dalam
pengujian, dan **opsional** untuk enkripsi/linearization bila engine utama tidak
mampu. Itu pun harus dibuktikan perlu.

### 2.6 MuPDF / PyMuPDF

| Item | Bukti | Status |
|---|---|---|
| Lisensi | Artifex: dual license **AGPL-3.0 atau komersial**; "ideally" menyertakan informasi AGPL dan mempertahankan *producer line* di metadata PDF; modifikasi wajib dibuka; aplikasi yang memakai harus membuka source ke pengguna yang berinteraksi | `UPSTREAM-DOC` |
| Anotasi, form create/fill, redaksi (dokumen sintetis), gambar/watermark, AES-256 | Spike S3, S4, S5, S6, S8 dengan PyMuPDF 1.27.2.2 | `MEASURED-OLD` |
| Redaksi | `apply_redactions` dengan opsi images/graphics/text; teks dihapus per karakter; catatan: gambar pengganti PNG tidak terkompresi, gambar asli tetap ada bila direferensikan halaman lain, perlu garbage collection saat simpan | `UPSTREAM-DOC` |
| Signing | Hanya `Document.get_sigflags()` terlihat pada dokumentasi yang diperiksa | `UNPROVEN` / `NOT-VERIFIED` |
| Integrasi Tauri — opsi 1 | Worker Python + PyMuPDF sebagai sidecar (memakai ulang pengetahuan implementasi lama) | Packaging Python `NOT_MEASURED` (B-03 lama) |
| Integrasi Tauri — opsi 2 | MuPDF C lewat FFI Rust | Crate tidak dievaluasi → `UNKNOWN` |

### 2.7 Kandidat library signature yang dipelihara

| Kandidat | Bahasa | Bukti pemeliharaan | Status |
|---|---|---|---|
| PDFBox + Bouncy Castle | Java | Proyek Apache; rilis 3.0.x (javadoc 3.0.7 ada) | Kandidat terkuat yang terverifikasi sesi ini; `UNPROVEN` |
| pyHanko | Python | `NOT-VERIFIED` sesi ini | Hanya relevan bila worker Python dipakai |
| MuPDF (C) | C | `NOT-VERIFIED` | — |
| Library Rust native | Rust | Tidak ada yang diverifikasi | `UNKNOWN` |

### 2.8 Temuan uji spike terbatas PDFium (2026-10-21, `MEASURED` pada mesin ini)

Melengkapi §2.1–2.3 dengan perilaku yang **teramati** (bukan dokumentasi):

| Temuan | Bukti |
|---|---|
| Anotasi yang dibuat lewat `FPDFPage_CreateAnnot` (wrapper maupun FFI mentah) disimpan sebagai **kamus langsung** di array `/Annots` dan **tanpa `/AP`** | Objek mentah output; API anotasi PyMuPDF memuat 0/10 |
| PDFium merender anotasi text, freetext, square, circle, ink tanpa `/AP`, tetapi **tidak** merender highlight/underline/strikeout/squiggly/stamp yang ia buat | Selisih piksel render dengan/tanpa anotasi |
| Setter form `pdfium-render 0.9.4`: checkbox menulis `/AS` sebagai string; radio tidak berefek; getter radio salah; tidak ada setter choice; AP field teks tidak diperbarui | Objek mentah + source crate |
| `FPDF_ImportPages` (lewat `append`/`copy_page_range_from_document`) ke dokumen baru tidak membawa outline, tujuan link, maupun `/AcroForm` | Objek mentah output |
| Trait akses binding mentah `pdfium-render 0.9.4` masih `pub(crate)` (berbeda dari catatan README 0.9.2) | Source crate |
| Biner `pdfium-binaries` memiliki atestasi SLSA provenance v1 yang dapat diverifikasi; DLL tidak bertanda tangan Authenticode; resource `CompanyName "Google Inc."` berasal dari template distributor | `gh attestation verify`, `patches/win/resources.rc` |

Rincian: `experiments/restart/results/SUMMARY.md` dan `experiments/restart/deps/PROVENANCE.md`.

---

## 3. Implikasi untuk tiga baseline

| Kebutuhan | A: PDFium + QPDF | B: PDFium + PDFBox | C: PDFium? + MuPDF worker |
|---|---|---|---|
| Render / teks / thumbnail | PDFium | PDFium | MuPDF atau PDFium |
| Anotasi markup | PDFium (13 subtipe) + kustom untuk sisanya | PDFium atau PDFBox | MuPDF (`MEASURED-OLD`) |
| Isi form | PDFium | PDFium atau PDFBox | MuPDF (`MEASURED-OLD`) |
| Buat field form | **kustom tingkat rendah** | PDFBox | MuPDF (`MEASURED-OLD`) |
| Page ops | PDFium atau QPDF | PDFium atau PDFBox | MuPDF |
| Enkripsi | **QPDF** (PDFium tidak menulis enkripsi) | PDFBox (`NOT-VERIFIED`) | MuPDF (`MEASURED-OLD`) |
| Secure redaction | **kustom penuh** | kustom (PDFBox tanpa API redaksi) | MuPDF `apply_redactions` |
| Signature kriptografis | **tidak ada library terverifikasi** | PDFBox + Bouncy Castle | `UNPROVEN` |
| Runtime tambahan | QPDF (native) | JVM | Python (atau FFI C) |
| Lisensi engine | BSD-style + Apache/`NOT-VERIFIED` (QPDF) | BSD-style + Apache-2.0 | **AGPL-3.0** atau komersial |

Perbandingan lengkap: `docs/STACK_EVALUATION.md` §10.

---

## 4. Pertanyaan terbuka

| ID | Pertanyaan | Cara menjawab |
|---|---|---|
| Q-01 | Apakah anotasi yang dibuat PDFium memiliki appearance stream yang dirender konsisten oleh pembaca lain setelah disimpan? | Spike RS-02 |
| Q-02 | Apakah import halaman PDFium mempertahankan bookmark, link, dan form? | Spike RS-04 |
| Q-03 | Seberapa besar runtime JVM minimal (jlink) untuk PDFBox? | Spike RS-08 (packaging) |
| Q-04 | Seberapa besar worker Python + PyMuPDF terbundel? | Spike RS-08 |
| Q-05 | Strategi redaksi kustom di atas PDFium/PDFBox: berapa kelas konten yang tertangani (teks, gambar, vektor, anotasi, metadata, XObject, form)? | Spike RS-06 |
| Q-06 | Provenance biner PDFium mana yang dapat diterima pengguna? | Keputusan pengguna |
| Q-07 | Lisensi QPDF dan Bouncy Castle | Verifikasi dokumen resmi sebelum dipakai |

---

## 5. Sumber primer (diakses 2026-10-21)

| Sumber | URL |
|---|---|
| PDFium `fpdf_annot.h` | <https://raw.githubusercontent.com/chromium/pdfium/main/public/fpdf_annot.h> |
| PDFium `fpdf_save.h` | <https://raw.githubusercontent.com/chromium/pdfium/main/public/fpdf_save.h> |
| PDFium `fpdf_signature.h` | <https://raw.githubusercontent.com/chromium/pdfium/main/public/fpdf_signature.h> |
| PDFium `fpdf_ppo.h` | <https://raw.githubusercontent.com/chromium/pdfium/main/public/fpdf_ppo.h> |
| PDFium `fpdf_edit.h`, `fpdf_flatten.h`, `fpdf_formfill.h` | `https://raw.githubusercontent.com/chromium/pdfium/main/public/` |
| `pdfium-render` README & Cargo.toml | <https://github.com/ajrcarey/pdfium-render> |
| `pdfium-binaries` README | <https://github.com/bblanchon/pdfium-binaries> |
| PDFBox 3.0 Migration Guide | <https://pdfbox.apache.org/3.0/migration.html> |
| PDFBox examples (signature) | <https://github.com/apache/pdfbox/tree/trunk/examples/src/main/java/org/apache/pdfbox/examples/signature> |
| QPDF "What is qpdf?" | <https://qpdf.readthedocs.io/en/stable/overview.html> |
| Artifex licensing | <https://artifex.com/licensing> |
| PyMuPDF Page (redactions) | <https://pymupdf.readthedocs.io/en/latest/page.html> |

Catatan: mirror GitHub `chromium/pdfium` dipakai untuk membaca header; sumber
kanonik adalah `pdfium.googlesource.com`.
