# FEATURE_MATRIX.md — Matriks Fitur

**Status:** DRAFT v1 · **Tanggal:** 2026-10-20
Referensi: Nitro PDF Pro **14.41.0.15**.

> **Catatan 2026-10-21 (sesi `2026-10-21T1057+0700`).** Bagian 1–12 di bawah adalah
> matriks v1 (satu referensi, stack lama) dan dipertahankan sebagai histori.
> Keputusan KEEP/IMPROVE/REPLACE/DEFER/REJECT di dalamnya **belum diratifikasi**
> pengguna (lihat `BLOCKERS.md` B-07.2). Capability matrix pasca-tiga-referensi ada di
> **§13**. Stack final **BELUM DISETUJUI**.
>
> **Errata v1** (teks asli tidak diubah):
> - "14 tab ribbon" (§1b) → analisis baru mencatat **13 tab bernama**
>   (`docs/ANALYSIS_NITRO14.md`).
> - "90 toolbar kontekstual" (§1b) → analisis baru mencatat **228 grup toolbar
>   kontekstual** (`docs/ANALYSIS_NITRO14.md`).
> - Kolom "Kepastian = VERIFIED" pada baris operasi/anotasi/form/redaksi merujuk ke
>   **spike stack lama (PyMuPDF)**, bukan ke kandidat stack baru.

## Legenda

**Tingkat kepastian referensi:** `VERIFIED` (terbukti di mesin) ·
`DOCUMENTED` (ada di dokumentasi publik v14) · `HYPOTHESIS` · `UNKNOWN`

**Keputusan UnionPDF:** `KEEP` · `IMPROVE` · `REPLACE` · `DEFER` · `REJECT`

**Milestone:** M0–M12 sesuai `docs/ROADMAP.md`.

---

## 1b. Temuan v14 terverifikasi (analisis biner read-only, 2026-10-20)

Baris-baris di bawah **terverifikasi langsung** dari build 14.41.0.15 yang
terpasang (14.452 string UI, 783 kontrol ribbon), bukan dari dokumentasi.
Bukti: `E-401`, `E-406`, `E-407`, `E-408`.

### Perbedaan yang harus ditiru UnionPDF

| Temuan v14 terverifikasi | Bukti | Keputusan UnionPDF |
|---|---|---|
| **"Redact" dan "White Out" adalah dua fitur terpisah** | `AVRibbon:Panel:Erase:Redact` vs `AVRibbon:Panel:Erase:Mask`; `Element:Erase:Whiteout` | **KEEP + IMPROVE** — UnionPDF memakai label lebih tegas: "Redaksi (isi dihapus, dapat diverifikasi)" vs "Penutupan visual (isi masih di dalam berkas)" |
| v14 sendiri messaging jujur: *"The document may contain hidden data and metadata. For a better level of protection, please use redaction instead."* | E-406 | UnionPDF meniru spirit ini, dengan bukti ekstraksi ulang (spike S5) |
| **Penghapusan 12 channel data tersembunyi** (Metadata, Comments/Markups, Links/Actions/Javascripts, Form Fields, Bookmarks, File Attachments, Embedded Thumbnail Images, Embedded Search Indexes, Deleted content, Hidden Layers, Hidden/invisible text, Document Structure) | E-406 | **KEEP, diperluas** → fitur "Pembersihan dokumen" tersendiri di M7, **bukan** sekadar "Remove Metadata" |
| **OCR melewati halaman yang sudah punya text** | *"OCR did not process pages \<PAGEVALUES\> because they already contain editable or searchable text."* | **KEEP** — deteksi otomatis + opsi paksa |
| **Dua password**: Open + Permissions, tidak boleh sama | E-406 | **KEEP** (M7) — model standar PDF |
| **Digital ID (PKCS#12)** untuk enkripsi & verifikasi tanda tangan, terikat profil Windows | E-406 | **DEFER** (M10) — UnionPDF butuh manajemen kunci privat yang aman |
| **Tiga metode split**: by page groups, by bookmarks, by page range | *"To start, choose one of the three splitting methods…"* | **KEEP** (M2) — murah & bernilai tinggi |
| **Dua mode konversi ke Word**: "Highly editable (with layout)" vs "Precisely laid out" | E-406 | **DEFER** (M9) — kualitas harus dijamin, bukan dijanjikan |
| **PDF/UA tagging** | `DocumentPdfUAComplianceSet`, `SetPdfUALanguage`, `CreateTags` | DEFER (M12) |
| **PDF/A + preflight** | `AVRibbon:Panel:Convert:Formats:PDFA:Btn`, `pdfa_converter::preflight_result` | DEFER (M12) |
| **Edit Text = mode toolbar kontekstual** | `NitroTextEditing`, `ReplaceText` | **DEFER** (M8) — fitur nyata di v14, tapi kompleks; jangan tampilkan tombol palsu |
| **Toolbar kontekstual per objek** (90 toolbar) | E-401 | **IMPROVE** (M4) — panel properti muncul saat objek dipilih |
| **Bates numbering** | `BatesNumbering` | DEFER (M3/M6) |
| **Auto bookmarks & auto links** | `AutoBuildBookmarks`, `AutoKeywordLinks`, `AutoPageLinks` | DEFER (M11) |
| **Measurement tools** (Distance, Perimeter, Area, Calibration) | E-401 | DEFER (M3) |
| **Import/Export comments** + ringkasan komentar | `ImportComments`, `ExportComments`, `SummarizeCommentsAndPrint` | DEFER (M4/M11) |
| **Deteksi lampiran berbahaya** | *"This file cannot be opened by Nitro PDF Pro because it may be harmful to your computer."* | **KEEP** (M7) — peringatan risiko lampiran |
| **Deteksi modifikasi pasca-tanda tangan** | *"Certificate is valid, document has been changed after it was certified"* | KEEP (M10) |
| **Struktur 14 tab ribbon** (Home, Review, PageLayout, Protect, Erase, Forms, Convert, Share, Help, Accessibility, BackStage, Favorite, IManage) | E-407 | **IMPROVE** — UnionPDF merancang tab sendiri, bukan menyalin; tapi **Protect vs Erase** sebagai dua tab terpisah terbukti ergonomis (redaksi vs keamanan) |
| **Telemetri/event analitik** (`ProHomePDFCombine`, `ProWordAddinPDFCreated`, …) | E-411 | **REPLACE** — UnionPDF nol telemetri |
| **Menjalankan tanpa admin** (`asInvoker`) | E-405 | KEEP — UnionPDF tanpa UAC |

### Struktur UI v14 yang terukur

| Tab | Kontrol | Isi utama |
|---|---:|---|
| Home | 32 | Tab utama, dapat dikustomisasi (pin hingga 5 tool) |
| Protect | 24 | Keamanan, enkripsi, tanda tangan, redaksi |
| Forms | 23 | 7+ tipe field, tab order, calculation order, import/export, appearance |
| Review | 21 | Markup & review tools |
| PageLayout | 20 | Crop, Delete, Extract, Insert, Replace, Rotate |
| Help | 16 | Smart Tips |
| Convert | 14 | Ke semua format termasuk PDF/A |
| Erase | 12 | **Redact, White Out, Remove Metadata** |
| Share | 4 | Email as attachment, cloud sign |
| Accessibility | 1 | PDF/UA tagging |
| BackStage | 1 | Menu File (Open, SaveAs, SaveAsFlatten) |
| Favorite | 1 | Tool favorit |
| IManage | 1 | Integrasi DMS |
| *(kontekstual)* | 373 | 90 toolbar: anotasi, bentuk, crop, zoom, form, object, link, text-editing, tagging, dsb. |

---

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Buka PDF | Ada | DOCUMENTED | KEEP | M1 | Save As by default, input tak pernah ditimpa |
| Render halaman | Ada | DOCUMENTED | KEEP | M1 | Terukur 33,87 ms/hlm @2× (E-201) |
| Zoom / fit page / fit width | Ada | DOCUMENTED | KEEP | M1 | |
| Navigasi halaman | Ada | DOCUMENTED | KEEP | M1 | |
| Panel thumbnail | Ada | DOCUMENTED | KEEP | M1 | |
| Pencarian (text layer) | Ada | DOCUMENTED | KEEP | M1 | 12 hit pada fixture (E-201) |
| Seleksi & salin teks | Ada | DOCUMENTED | KEEP | M1 | |
| Info dokumen | Ada | DOCUMENTED | KEEP | M1 | |
| Panel komentar | Ada | DOCUMENTED | KEEP | M4 | |
| Multi-window | Ada | DOCUMENTED | DEFER | M11 | |
| System tray | Ada | DOCUMENTED | REJECT | — | Tidak ada kebutuhan nyata untuk tool PDF lokal |

## 2. Operasi halaman

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Gabung (merge) | Ada | VERIFIED | KEEP | M2 | 14/14 hlm (E-202) |
| Pecah (split) | Ada | VERIFIED | KEEP | M2 | 4/4 hlm |
| Ekstrak halaman | Ada | VERIFIED | KEEP | M2 | |
| Hapus halaman | Ada | VERIFIED | KEEP | M2 | 11 hlm (E-202) |
| Putar halaman | Ada | VERIFIED | KEEP | M2 | 90° (E-202) |
| Susun ulang (reorder) | Ada | DOCUMENTED | KEEP | M2 | |
| Sisip halaman | Ada | DOCUMENTED | KEEP | M3 | |
| Duplikat halaman | Ada | DOCUMENTED | KEEP | M2 | |
| Page range | Ada | DOCUMENTED | KEEP | M3 | |
| Simpan sebagai | Ada | DOCUMENTED | KEEP | M2 | Atomic write + verifikasi |
| Flatten anotasi | Ada | DOCUMENTED | KEEP | M4 | Belum diuji (S1–S12) |
| Edit teks existing + reflow paragraf | Ada (klaim produk) | DOCUMENTED | **DEFER** | M8 | Risiko tertinggi; U-01 |
| Ganti gambar | Ada | DOCUMENTED | DEFER | M8 | |

## 3. Membuat & menambah konten

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Gambar → PDF | Ada | DOCUMENTED | KEEP | M3 |
| Halaman kosong | Ada | DOCUMENTED | KEEP | M3 |
| Tambah teks | Ada | DOCUMENTED | KEEP | M3 | Overlay, **diberi label** sebagai overlay |
| Tambah gambar | Ada | VERIFIED | KEEP | M3 | 1 image setelah reopen (E-207) |
| Watermark | Ada | VERIFIED | KEEP | M3 | Terbaca (E-207) |
| Header/footer | Ada | VERIFIED | KEEP | M3 | Terbaca (E-207) |
| Nomor halaman | Ada | DOCUMENTED | KEEP | M3 |
| Buat dari HTML | Ada | DOCUMENTED | DEFER | M9 | Butuh engine HTML tambahan |
| Buat dari clipboard/screen | Ada | DOCUMENTED | DEFER | M11 | |
| PDF Portfolio | Ada | DOCUMENTED | REJECT | — | Edge case, nilai rendah |
| Cetak ke PDF (virtual printer) | Ada | VERIFIED | DEFER | M12 | Butuh driver printer — cakupan besar |

## 4. Anotasi & form

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Highlight | Ada | VERIFIED | KEEP | M4 | E-204 |
| Underline / strikeout | Ada | DOCUMENTED | KEEP | M4 | Belum diuji |
| Note / komentar | Ada | VERIFIED | KEEP | M4 | E-204 |
| Text box / callout | Ada | VERIFIED | KEEP | M4 | E-204 |
| Bentuk dasar | Ada | VERIFIED | KEEP | M4 | E-204 |
| Tinta (ink) | Ada | DOCUMENTED | DEFER | M4 | |
| Isi form (AcroForm) | Ada | VERIFIED | KEEP | M4 | E-205 |
| Buat field form | Ada | VERIFIED | KEEP | M4 | E-205 |
| Simpan form | Ada | VERIFIED | KEEP | M4 | E-205 |
| Flatten form | Ada | DOCUMENTED | DEFER | M4 | |
| Impor/ekspor data form | Ada | DOCUMENTED | DEFER | M11 | |
| Field calculation / tab order | Ada | DOCUMENTED | DEFER | M11 | |
| Barcode field | Ada | DOCUMENTED | DEFER | M11 | |
| XFA form | Ada (389 berkas!) | DOCUMENTED | **REJECT** | — | Kompleksitas sangat tinggi, nilai rendah |
| RichText annotation | Ada (v14.3) | DOCUMENTED | DEFER | M11 | |

## 5. OCR

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| OCR → searchable | Ada | DOCUMENTED | KEEP | M5 | Windows OCR terukur (E-211) |
| OCR → searchable + editable | Ada (marketing) | DOCUMENTED | **REJECT (klaim)** | — | Rekonstruksi editable = M8; menampilkan tombol ini tanpa kemampuan nyata = tombol mati |
| Prompt OCR otomatis saat membuka scan | Ada | DOCUMENTED | KEEP | M5 | UX murah, sangat berguna |
| Pilih bahasa OCR | Ada | VERIFIED | KEEP | M5 | Windows OCR: daftar dari sumber sendiri (E-216) |
| Preferensi OCR (deskew, orientasi, quality) | Ada | DOCUMENTED | KEEP | M5 | |
| OCR batch | Ada | DOCUMENTED | KEEP | M6 | |
| Language pack management | Ada | DOCUMENTED | DEFER | M6 | |

## 6. Optimasi & batch

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Preset kompresi | Ada (3 preset) | DOCUMENTED | KEEP | M6 | Reduced Size / Print Ready / Custom |
| Resample gambar | Ada | DOCUMENTED | KEEP | M6 | |
| Hapus objek tak terpakai | Ada | DOCUMENTED | KEEP | M6 | Default **noninvasif** |
| Pratinjau perubahan ("Show Details") | Ada | DOCUMENTED | KEEP | M6 | Wajib |
| Antrean batch | Ada | DOCUMENTED | KEEP | M6 | |
| Progress & cancel | Ada | DOCUMENTED | KEEP | M6 | Terbukti (E-210) |
| Retry job gagal | Ada | HYPOTHESIS | KEEP | M6 | |
| Batch resumable | Tidak jelas | HYPOTHESIS | IMPROVE | M11 | |

## 7. Keamanan

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Enkripsi password (AES-256) | Ada | DOCUMENTED | KEEP | M7 | Terukur (E-209) |
| Password opening | Ada | DOCUMENTED | KEEP | M7 | |
| Permission settings | Ada | DOCUMENTED | KEEP | M7 | |
| Redaksi | Ada | VERIFIED | KEEP | M7 | **Terbukti**: target tidak ter-ekstrak (E-206) |
| Sanitasi metadata | Ada | DOCUMENTED | KEEP | M7 | Belum diuji pada channel metadata (L-07) |
| Hapus embedded JS | Ada | DOCUMENTED | KEEP | M7 | |
| Hapus attachment | Ada | DOCUMENTED | KEEP | M7 | |

## 8. Konversi

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| PDF → gambar (JPG/PNG/TIFF) | Ada | VERIFIED | KEEP | M9 | 21,3 ms/hlm (E-208) |
| PDF → plain text | Ada | DOCUMENTED | KEEP | M9 | |
| PDF → Word | Ada | DOCUMENTED | DEFER | M9 | Kualitas tidak terjamin; U-05 |
| PDF → Excel | Ada | DOCUMENTED | DEFER | M9 | |
| PDF → PowerPoint | Ada | DOCUMENTED | DEFER | M9 | |
| Office → PDF | Ada | DOCUMENTED | DEFER | M9 | Butuh MS Office/LibreOffice; U-05 |
| PDF/A | Ada | DOCUMENTED | DEFER | M12 | Butuh validator; risiko tinggi |

## 9. Tanda tangan

| Fitur | Referensi | Kepastian | UnionPDF | Milestone | Catatan |
|---|---|---|---|---|---|
| Gambar tanda tangan | Ada | DOCUMENTED | KEEP | M10 | |
| Stempel tanda tangan | Ada | DOCUMENTED | KEEP | M10 | |
| Tanda tangan kriptografis | Ada | DOCUMENTED | DEFER | M10 | pyHanko; U-06 |
| Validasi tanda tangan | Ada | DOCUMENTED | DEFER | M10 | |
| Pengelolaan private key | Ada | DOCUMENTED | DEFER | M10 | Jangan simpan password |
| Nitro Sign / cloud sign | Ada | VERIFIED | **REJECT** | — | Vendor-specific, butuh cloud |

## 10. Integrasi & platform (umumnya REJECT)

| Fitur | Referensi | Kepastian | UnionPDF | Keputusan |
|---|---|---|---|---|
| Add-in Microsoft Office | Ada | VERIFIED | REJECT | Terlalu terikat Office |
| Integrasi DMS (iManage) | Ada | VERIFIED | REJECT | Vendor-specific |
| WebDAV | Ada | VERIFIED | DEFER | |
| Cloud storage (iCloud/OneDrive) | Ada | VERIFIED | DEFER | |
| Preview di Explorer | Ada | VERIFIED | DEFER | |
| Thumbnail di Explorer | Ada | VERIFIED | DEFER | |
| Barcode scan | Ada | VERIFIED | DEFER | |
| TWAIN scan | Ada | VERIFIED | DEFER | |
| Sensitivity label (MIP) | Ada | VERIFIED | REJECT | Terikat Microsoft 365 |
| Auto-update | Ada (WinSparkle) | VERIFIED | DEFER | Manual lebih aman untuk tool lokal |
| Crash reporting | Ada (BugSplat) | VERIFIED | **REPLACE** | UnionPDF: opt-in, tanpa telemetry default |
| Command-line | Ada (CommandLine.dll) | VERIFIED | KEEP | M11 — otomatisasi |
| OCR bahasa Asia (CJK) | Ada | DOCUMENTED | DEFER | Tesseract + model bahasa |

## 11. Fitur "pintar" (usulan UnionPDF, bukan tiruan)

| Usulan | Masalah | Manfaat | Risiko | Acceptance criteria | Prioritas |
|---|---|---|---|---|---|
| Deteksi halaman tanpa text layer | User tidak tahu dokumen perlu OCR | Prompt OCR yang tepat waktu | Salah deteksi | Deteksi >95% benar pada fixture pindai & digital | M5 |
| Document preflight | Masalah baru ditemukan saat graft | Cegah dokumen rusak | Salah positives | Laporan menjelaskan temuan | M11 |
| Command palette | Banyak aksi sulit dipesan | Akses cepat | — | Semua aksi utama reachable | M11 |
| Preset workflow | Repetisi langkah | Efisiensi | — | Preset menyimpan chain operasi | M11 |
| Batch resumable | Job panjang Putus | Keandalan | State kompleks | Resume setelah restart | M11 |
| Pratinjau operasi berisiko | Redaksi/optimasi tanpa preview | Keamanan | — | Preview wajib sebelum apply | M6/M7 |
| Ringkasan perubahan | User tidak tahu apa yang berubah | Transparansi | — | Diff per operasi | M6 |
| AI opsional | Bantu ringkas/ekstrak | Kenyamanan | Biaya, privasi | **Opt-in**, jelas data yang dikirim, inti tetap jalan tanpa AI | M12 |

**Aturan AI (dari master prompt):** tidak boleh jadi dependency wajib; harus
opt-in; jelaskan data yang dikirim; jangan simpan credential di log; jangan unggah
otomatis.

---

## 12. Ringkasan jumlah

| Kategori | KEEP | IMPROVE | DEFER | REJECT | Total |
|---|---:|---:|---:|---:|---:|
| Viewer & navigasi | 8 | 0 | 1 | 1 | 10 |
| Operasi halaman | 9 | 0 | 2 | 0 | 11 |
| Buat & tambah | 7 | 0 | 4 | 1 | 12 |
| Anotasi & form | 6 | 0 | 6 | 1 | 13 |
| OCR | 4 | 0 | 1 | 1 | 6 |
| Optimasi & batch | 7 | 1 | 0 | 0 | 8 |
| Keamanan | 7 | 0 | 0 | 0 | 7 |
| Konversi | 2 | 0 | 4 | 0 | 6 |
| Tanda tangan | 2 | 0 | 3 | 1 | 6 |
| Integrasi | 1 | 1 | 5 | 5 | 12 |
| Pintar (usulan) | — | 7 | — | — | 7 |
| **Total** | **53** | **9** | **26** | **9** | **97** |

Tidak ada fitur yang "KEEP" tanpa alasan — alasan tercatat per baris.

---

## 13. Capability matrix v2 — pasca-tiga-referensi (2026-10-21)

**Status:** DRAFT untuk keputusan. Tidak ada baris di sini yang berarti fitur selesai.
`SUPPORTED_BY_API` ≠ fitur selesai. Sumber fakta API: `docs/POST_ALL_REFERENCES_TECH_REVIEW.md` §2.

### 13.1 Legenda

| Kode | Arti |
|---|---|
| `API` | SUPPORTED_BY_API — API terdokumentasi ada; belum berarti benar/teruji |
| `CUSTOM` | REQUIRES_CUSTOM_IMPLEMENTATION — tidak ada API tingkat tinggi; perlu kode sendiri |
| `ENGINE+` | REQUIRES_ADDITIONAL_ENGINE — butuh engine/tool tambahan |
| `UNPROVEN` | Belum terbukti; perlu spike |
| `BLOCKED` | Terhalang keputusan/kondisi lain |
| N / S / G | Nitro 14 / Stirling-PDF 3.2 / PDFgear 3.0 — bukti **statis** dari dokumen analisis |
| P0 | Wajib dibuktikan sebelum baseline dipilih |
| P1 | M1–M2 · P2 = M3–M7 · P3 = M8+ (penomoran milestone menunggu keputusan, lihat `RESTART_AUDIT.md` P-3) |

### 13.2 Kebutuhan, bukti referensi, dan acceptance criteria

| Req | Kapabilitas | Kebutuhan pengguna | Referensi (statis) | Acceptance criteria UnionPDF | Prioritas |
|---|---|---|---|---|---|
| CR-01 | Buka PDF (normal, terenkripsi, rusak ringan) | Membuka dokumen apa pun dengan error jujur | N, S, G | Fixture normal/terenkripsi/rusak: dibuka atau ditolak dengan pesan spesifik; tidak crash; password tidak dicatat | P0 |
| CR-02 | Render, zoom, fit, thumbnail | Melihat dokumen dengan nyaman | N, S, G | Halaman terlihat dirender lebih dulu; render dibatalkan saat pindah halaman; hasil render cocok dengan engine pembanding (pixel diff dalam ambang yang ditetapkan sebelum uji) | P0 |
| CR-03 | Seleksi, salin, cari teks | Mencari & mengutip | N, S, G | Fixture teks Latin + Unicode: hasil cari dan teks salinan sama dengan ground truth fixture | P1 |
| CR-04 | Page ops: merge, split, extract, rotate, delete, reorder, insert | Menyusun dokumen | N, S, G (Copilot `extract-page`, `delete-page`, `insert-page`, `rotate-page`) | Jumlah/urutan/rotasi halaman benar; teks per halaman utuh; bookmark/link/form **sesuai scope yang ditetapkan** tetap valid; `qpdf --check` tanpa error | P0 |
| CR-05 | Save As atomik + penanganan kegagalan | Input tidak pernah rusak | N, S, G | Input tidak berubah (hash sama); output via temp → verifikasi → rename; disk penuh/file terkunci/izin ditolak/cancel menghasilkan error jujur dan tanpa file parsial di lokasi akhir | P0 |
| CR-06 | Tambah teks, gambar, watermark, header/footer, nomor halaman | Menandai dokumen | N, G (`WatermarkUtils`, `PageHeaderFooters`) | Konten muncul di render setelah buka ulang; teks overlay ditandai sebagai overlay | P2 |
| CR-07 | Anotasi markup: highlight, underline, strikeout, squiggly, note, freetext, square, circle, ink, stamp | Meninjau dokumen | N, G (Copilot `add-annotation`) | Dibuat → Save As → dibuka ulang oleh engine yang sama **dan** engine independen: subtipe, rect, warna, isi sama; terlihat saat render | P0 |
| CR-08 | Anotasi line, polygon, polyline, caret | Markup teknis | N | Sama dengan CR-07 | P2 |
| CR-09 | Isi & simpan form (AcroForm) | Mengisi formulir | N, G (`FlattenWindow`) | Nilai text/checkbox/radio/choice bertahan setelah buka ulang di dua engine; appearance terlihat | P0 |
| CR-10 | Membuat field form | Mendesain formulir | N (tab Forms) | Field baru dikenali sebagai field (nama, tipe, rect) oleh dua engine; dapat diisi | P0 (penilaian), P2 (fitur) |
| CR-11 | Flatten anotasi/form | Membekukan hasil | N, G | Setelah flatten: tidak ada lagi objek anotasi/field; tampilan render setara sebelum flatten | P2 |
| CR-12 | OCR → searchable | Mencari di dokumen pindaian | N (searchable vs editable), S (semantik OCRmyPDF), G (`ConvertToSearchablePdf`) | Teks tak terlihat sejajar dengan gambar; pencarian menemukan kata fixture; tidak diklaim "editable" | P2 |
| CR-13 | Enkripsi, password, permission | Melindungi dokumen | N (4 algoritma), S (model 2 password), G (`protect-pdf`, `remove-password`) | Output terenkripsi meminta password di dua engine; password user ≠ owner ditegakkan; password tidak tersimpan/tercatat | P2 |
| CR-14 | Secure redaction | Menghapus data sensitif | N (Redact ≠ Whiteout ≠ Mask), G (`PDFEraserUtil`) | Teks/gambar/vektor di area **tidak dapat diekstrak** oleh dua engine independen; tidak tersisa di content stream, XObject, anotasi, dan metadata yang dicakup; konten di luar area utuh; label UI membedakan redaksi vs penutup visual | P0 (penilaian), P2 (fitur) |
| CR-15 | Sanitasi metadata/JS/lampiran | Privasi dokumen | N (12 channel) | Channel yang dicakup kosong setelah sanitasi, diverifikasi dengan pembaca struktur | P2 |
| CR-16 | Signature visual (gambar) | Menandai persetujuan | N, G | Ditandai jelas sebagai **gambar**, bukan signature kriptografis | P2 |
| CR-17 | Signature kriptografis + validasi | Keabsahan dokumen | N, G (`DigitalSignatures`) | Ditandatangani dengan sertifikat uji; divalidasi oleh validator independen; perubahan pasca-tanda-tangan terdeteksi | P0 (penilaian jalur), P3 (fitur) |
| CR-18 | Kompresi/optimasi | Ukuran file | N, S, G (`compress`) | Laporan delta; default noninvasif; output valid `qpdf --check` | P2 |
| CR-19 | PDF → gambar/teks | Ekspor | N, S, G | Gambar & teks sesuai fixture | P2 |
| CR-20 | Office ↔ PDF | Konversi | N (add-in), S (LibreOffice eksternal), G (Syncfusion) | Tidak dijanjikan layout identik; uji pada fixture | P3 |
| CR-21 | Edit teks existing | Koreksi isi | N (Edit Text), S (dua jalur), G (`edit-text`) | Ditentukan setelah spike; dibedakan dari overlay | P3 |
| CR-22 | Automation: preset, antrean, retry, recovery | Pekerjaan berulang | S (pipeline) | Satu command registry untuk UI/shortcut/automation; job dapat dibatalkan & dilanjutkan sesuai kontrak | P1 |
| CR-23 | AI adapter opsional | Bantuan opsional | G (Copilot 27 aksi) | Fungsi inti jalan tanpa AI; AI hanya mengusulkan command + parameter; validasi & eksekusi di aplikasi; opt-in | P3 |

### 13.3 Status teknis per baseline

A = Tauri + React/TS + Rust + PDFium + QPDF · B = Tauri + React/TS + Rust + PDFium +
Java/PDFBox · C = Tauri + React/TS + Rust + MuPDF/PyMuPDF worker.
Kolom "Lama (benchmark)" = implementasi Python/PySide6/PyMuPDF yang ada, diukur
2026-10-20 (`MEASURED-OLD`).

| Req | A | B | C | Lama (benchmark) | Risiko utama | Status uji kandidat |
|---|---|---|---|---|---|---|
| CR-01 | `API` PDFium | `API` PDFium | `API` MuPDF | PASS (test) | Dokumen rusak di luar fixture | `UNPROVEN` |
| CR-02 | `API` PDFium | `API` PDFium | `API` MuPDF atau PDFium | PASS S1 | Thread-safety PDFium (serialisasi) | `UNPROVEN` |
| CR-03 | `API` PDFium | `API` PDFium | `API` MuPDF | PASS S1 | Unicode/RTL | `UNPROVEN` |
| CR-04 | `API` PDFium (import/delete/rotate/move) atau QPDF | `API` PDFium atau PDFBox | `API` MuPDF | PASS S2 | Struktur (bookmark/link/form) saat import | `UNPROVEN` |
| CR-05 | `CUSTOM` (Rust) + `API` save | `CUSTOM` + `API` | `CUSTOM` + `API` | Unit test PASS; belum dipakai UI | Konsistensi pemilik mutasi | `UNPROVEN` |
| CR-06 | `API` PDFium objects | `API` | `API` | PASS S6 | Font/Unicode | `UNPROVEN` |
| CR-07 | `API` — kesepuluh subtipe termasuk 13 subtipe yang dapat dibuat PDFium (*experimental*) | `API` PDFium atau PDFBox | `API` MuPDF | PASS S3 (sebagian subtipe) | Appearance stream pada pembaca lain | `UNPROVEN` |
| CR-08 | `CUSTOM` (tidak dapat dibuat PDFium) | `API` PDFBox (kelas Polygon/Polyline/Caret) | `API` MuPDF (`NOT-VERIFIED`) | tidak diuji | Appearance | `UNPROVEN` |
| CR-09 | `API` FORM_* | `API` PDFium atau PDFBox | `API` MuPDF | PASS S4 | Appearance setelah isi | `UNPROVEN` |
| CR-10 | `CUSTOM` tingkat rendah | `API` PDFBox (contoh resmi) | `API` MuPDF | PASS S4 | Validitas struktur field | `UNPROVEN` |
| CR-11 | `API` `FPDFPage_Flatten` | `API` PDFium | `API` MuPDF (`NOT-VERIFIED`) | tidak diuji | Mutu flatten | `UNPROVEN` |
| CR-12 | `ENGINE+` OCR + `CUSTOM` text layer | idem | idem | Windows OCR PASS S10 (bersyarat) | Akurasi, bahasa | `UNPROVEN` |
| CR-13 | `ENGINE+` QPDF (PDFium tidak menulis enkripsi) | `API` PDFBox (`NOT-VERIFIED`) | `API` MuPDF | PASS S8 | Lisensi QPDF `NOT-VERIFIED` | `UNPROVEN` |
| CR-14 | `CUSTOM` penuh | `CUSTOM` (tanpa API redaksi) | `API` `apply_redactions` (dengan catatan dok) | PASS S5 (dokumen sintetis sederhana) | Kebocoran data tersisa | `UNPROVEN` |
| CR-15 | `CUSTOM` | `CUSTOM` + `API` parsial | `API` parsial | tidak diuji | Channel terlewat | `UNPROVEN` |
| CR-16 | `API` stamp/image | `API` | `API` | tidak diuji | Salah label | `UNPROVEN` |
| CR-17 | `BLOCKED` — tidak ada library signing terverifikasi untuk stack ini | `API` PDFBox + Bouncy Castle (contoh resmi) | `UNPROVEN` | tidak diuji | Kunci privat, validasi | `UNPROVEN` |
| CR-18 | `ENGINE+` QPDF (struktural) | `API` PDFBox (kompresi saat simpan) | `API` MuPDF | tidak diuji | Lossy vs lossless | `UNPROVEN` |
| CR-19 | `API` PDFium | `API` PDFium | `API` MuPDF | PASS S7 | — | `UNPROVEN` |
| CR-20 | `ENGINE+` (mis. LibreOffice) | idem | idem | tidak diuji | Ukuran, mutu layout | `UNPROVEN` |
| CR-21 | `CUSTOM` | `CUSTOM` (PDFBox content stream) | `CUSTOM` | tidak diuji | Font subset, reflow | `UNPROVEN` |
| CR-22 | `CUSTOM` (Rust job manager) | `CUSTOM` + IPC JVM | `CUSTOM` + IPC Python | `JobRunner` ada, belum dipakai UI | Recovery worker crash | `UNPROVEN` |
| CR-23 | `CUSTOM` | `CUSTOM` | `CUSTOM` | tidak ada | Privasi | `UNPROVEN` |

### 13.4 Dependency, lisensi, dan custom work per baseline

| Item | A | B | C |
|---|---|---|---|
| Dependency tambahan di luar shell | PDFium (biner), QPDF (biner) | PDFium (biner), JRE/JVM, PDFBox, Bouncy Castle | Runtime Python + PyMuPDF (atau MuPDF C + FFI) |
| Lisensi engine | PDFium BSD-style; QPDF `NOT-VERIFIED`; `pdfium-render` MIT OR Apache-2.0 | PDFium BSD-style; PDFBox Apache-2.0; Bouncy Castle `NOT-VERIFIED` | MuPDF/PyMuPDF **AGPL-3.0** atau komersial |
| Custom work terbesar | Field authoring, anotasi di luar 13 subtipe, redaksi penuh, signature (tanpa library) | Redaksi, integrasi IPC JVM | Integrasi IPC Python/FFI, packaging Python |
| Pemilik mutasi dokumen | PDFium dan QPDF (harus satu pemilik per revisi) | PDFium dan PDFBox (harus satu pemilik per revisi) | MuPDF |

### 13.5 Pembaruan setelah spike terbatas PDFium (2026-10-21)

Baris di §13.3 tidak diubah; tabel ini mencatat status uji **bagian PDFium** saja
(`experiments/restart/results/SUMMARY.md`). Baseline B dan C untuk kapabilitas yang sama
belum diuji.

| Req | Hasil uji PDFium (`chromium/7881` + `pdfium-render 0.9.4`) |
|---|---|
| CR-02 | **Terbukti pada fixture sintetis**: render semua halaman, cocok dengan pembaca independen, zoom/thumbnail, pembatalan antar-request |
| CR-03 | Pencarian PASS; ekstraksi Latin PASS kecuali 1 baris (cacat fixture); Unicode/RTL belum dapat dinilai |
| CR-04 | In-place (rotate/delete/reorder/insert/merge-append): **terbukti**, struktur utuh. Impor ke dokumen baru: outline, tujuan link, dan `/AcroForm` hilang → `CUSTOM` untuk merge/extract/split yang mempertahankan struktur |
| CR-07 | Pembuatan & round-trip internal PDFium berhasil, **tetapi** anotasi tanpa `/AP` dan sebagai objek langsung (interop gagal; PDFium tak merender markup/stamp buatannya) → efektif `CUSTOM` (AP kustom), jalur perbaikan `UNPROVEN` |
| CR-09 | Lewat setter `pdfium-render`: teks tersimpan tanpa appearance baru; checkbox menghasilkan file tidak valid bagi PyMuPDF; radio no-op; choice tanpa setter. Jalur `FORM_*` native belum diuji |

### 13.6 Pembaruan setelah pembandingan tiga engine & vertical slice aplikasi (2026-10-22)

Status **implementasi UnionPDF** (bukan status engine semata). Bukti:
`experiments/restart/results/SUMMARY.md` §9 (pembandingan), `apps/desktop/src-tauri/src/ops.rs`
(21 test backend), `apps/desktop/scripts/ui-e2e.ps1` (12 PASS + 1 NOT_RUN UI),
`docs/sessions/2026-10-22T0900+0700.md`.

| Req | Status UnionPDF | Bukti & catatan |
|---|---|---|
| CR-02 | **Terbukti di aplikasi**: render, navigasi, zoom/fit, thumbnail lazy | UI-01/UI-03; startup median 481 ms, halaman pertama 677 ms |
| CR-03 | **Terbukti sebagian**: teks Latin &amp; Arab terbaca; **urutan RTL masih visual** (belum ada reordering bidi) | UPDF-051 |
| CR-04 | **Terbukti di aplikasi**: putar, Save As (atomik, verifikasi), ekstrak, gabung; struktur dipertahankan lewat worker PDFBox (bookmark dipangkas, link/field disesuaikan, field bentrok diganti nama) dengan **peringatan + konfirmasi** bila ada yang dibuang | UPDF-048/049/050; U-03/U-06/U-08 |
| CR-07 | **Terbukti di aplikasi** (lewat PDFBox, bukan PDFium): highlight, underline, note, free text dengan appearance tersimpan, bertahan setelah save/reopen | UPDF-049; U-12 (form) & M-01…M-08 (manual) |
| CR-09 | **Terbukti di aplikasi** (lewat PDFBox): isi teks, checkbox, radio grup, combo; nilai & appearance bertahan setelah simpan | U-12 (PyMuPDF: nama=Budi Santoso, AP memuat nilai; setuju=Yes; pilihan=B; kota=Surabaya) |
| CR-10 (redaksi) | **Ditunda** atas instruksi pengguna; fixture `rs07_redact.pdf` + temuan "nilai field lama masih ada di appearance stream" dipertahankan sebagai test gagal | UPDF-052 |
| CR-11 (signature) | **Bukti minimal di spike** (PDFBox + sertifikat uji self-signed; rantai kepercayaan tidak dinilai); belum ada di aplikasi | `experiments/restart/results/SUMMARY.md` §9.1 |
| Installer | **Belum ada** (`bundle.active=false`); yang ada build release lokal + staging | UPDF-057; B-RT1 untuk runtime Java |

### 13.7 Pembaruan setelah continuous scroll, chrome, runtime Java & paket (2026-10-22)

Status **aplikasi UnionPDF** (bukan engine semata). Bukti: `apps/desktop/src/viewer/layout.ts` +
`layout.test.ts` (8 uji), `apps/desktop/scripts/ui-e2e.ps1` (18 PASS + 1 NOT_RUN),
`apps/desktop/scripts/{test-bundled-jre,test-no-external-java,test-package}.ps1` (PASS),
`docs/sessions/2026-10-22T1400+0700.md`.

| Req | Status UnionPDF | Bukti & catatan |
|---|---|---|
| CR-02 | **Terbukti**: continuous vertical scroll (default) + mode satu halaman; virtualisasi; zoom menjaga posisi baca; thumbnail & nomor halaman sinkron | UI-14…UI-19; 8 uji layout |
| CR-03 | **Terbukti sebagian**: navigasi & selection belum ada (selection layer per halaman masih TODO); urutan RTL masih visual | UPDF-051 |
| CR-04 | **Terbukti**: putar, Save As, ekstrak, gabung; struktur dipertahankan (bookmark dipangkas, field bentrok diganti nama) + konfirmasi pra-eksekusi | U-03, U-06, U-08 |
| CR-07 | **Terbukti**: sorot, garis bawah, catatan, teks bebas (PDFBox worker), appearance tersimpan | U-12, M-12 (manual) |
| CR-09 | **Terbukti**: isi teks, checkbox, radio, combo; nilai & appearance bertahan | U-12 (PyMuPDF independen) |
| CR-10 (redaksi) | **Ditunda** atas instruksi pengguna; fixture + temuan "nilai field lama masih ada" tetap | UPDF-052 |
| CR-12 (runtime/paket) | **Terbukti**: runtime Java bundel (jlink, 53,1 MB), paket portabel 74,6 MB (ZIP 48,0 MB), installer NSIS 43,2 MB; app jalan tanpa Java eksternal, path ber-spasi/Unicode, folder tidak writable | ADR-003; clean-install NOT_RUN |
| UI/UX | **Terbukti sebagian**: title bar, tab kategori, command bar kontekstual, sidebar, status bar, ikon sendiri, design tokens; tooltip/DPI/multi-monitor belum diuji | M-01…M-24 |

### 13.8 Pembaruan setelah lapisan teks, anotasi teruji & strategi WebView2 (2026-10-22)

| Req | Status UnionPDF | Bukti |
|---|---|---|
| CR-02 | **Terbukti**: continuous scroll (default), virtualisasi, anchor zoom, mode satu halaman, ukuran campuran & halaman berotasi dihormati | UI-14…UI-22; 8 uji layout |
| CR-03 | **Terbukti sebagian**: lapisan teks per halaman (teks dapat dipilih/disalin); find belum ada; RTL masih urutan visual | UI-26; UPDF-051 |
| CR-04 | **Terbukti**: putar/save/ekstrak/gabung + integritas struktur (bookmark dipangkas, field bentrok diganti nama) + konfirmasi pra-eksekusi | U-03, U-06, U-08 |
| CR-07 | **Terbukti**: sorot, garis bawah, catatan, teks bebas; koordinat gesture dipetakan lewat fungsi murni (zoom/DPI/rotasi) dan dibatasi per halaman | `annotation.test.ts` (6), uji backend "anotasi di halaman kedua" |
| CR-09 | **Terbukti**: isi form + save/reopen | U-12 |
| CR-12 | **Terbukti**: runtime Java bundel (53,1 MB), paket 74,6 MB (ZIP 48,0 MB), installer 43,2 MB; strategi WebView2 evergreen eksplisit | ADR-003, `docs/WEBVIEW2-STRATEGY.md` |
