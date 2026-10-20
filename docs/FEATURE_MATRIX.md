# FEATURE_MATRIX.md — Matriks Fitur

**Status:** DRAFT v1 · **Tanggal:** 2026-10-20
Referensi: Nitro PDF Pro **14.41.0.15**.

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

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
|---|---|---|---|---|
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

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
|---|---|---|---|---|
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

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
|---|---|---|---|---|
| OCR → searchable | Ada | DOCUMENTED | KEEP | M5 | Windows OCR terukur (E-211) |
| OCR → searchable + editable | Ada (marketing) | DOCUMENTED | **REJECT (klaim)** | — | Rekonstruksi editable = M8; menampilkan tombol ini tanpa kemampuan nyata = tombol mati |
| Prompt OCR otomatis saat membuka scan | Ada | DOCUMENTED | KEEP | M5 | UX murah, sangat berguna |
| Pilih bahasa OCR | Ada | VERIFIED | KEEP | M5 | Windows OCR: daftar dari sumber sendiri (E-216) |
| Preferensi OCR (deskew, orientasi, quality) | Ada | DOCUMENTED | KEEP | M5 | |
| OCR batch | Ada | DOCUMENTED | KEEP | M6 | |
|/language pack management | Ada | DOCUMENTED | DEFER | M6 | |

## 6. Optimasi & batch

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
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

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
|---|---|---|---|---|---|
| Enkripsi password (AES-256) | Ada | DOCUMENTED | KEEP | M7 | Terukur (E-209) |
| Password opening | Ada | DOCUMENTED | KEEP | M7 | |
| Permission settings | Ada | DOCUMENTED | KEEP | M7 | |
| Redaksi | Ada | VERIFIED | KEEP | M7 | **Terbukti**: target tidak ter-ekstrak (E-206) |
| Sanitasi metadata | Ada | DOCUMENTED | KEEP | M7 | Belum diuji pada channel metadata (L-07) |
| Hapus embedded JS | Ada | DOCUMENTED | KEEP | M7 | |
| Hapus attachment | Ada | DOCUMENTED | KEEP | M7 | |

## 8. Konversi

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
|---|---|---|---|---|---|
| PDF → gambar (JPG/PNG/TIFF) | Ada | VERIFIED | KEEP | M9 | 21,3 ms/hlm (E-208) |
| PDF → plain text | Ada | DOCUMENTED | KEEP | M9 | |
| PDF → Word | Ada | DOCUMENTED | DEFER | M9 | Kualitas tidak terjamin; U-05 |
| PDF → Excel | Ada | DOCUMENTED | DEFER | M9 | |
| PDF → PowerPoint | Ada | DOCUMENTED | DEFER | M9 | |
| Office → PDF | Ada | DOCUMENTED | DEFER | M9 | Butuh MS Office/LibreOffice; U-05 |
| PDF/A | Ada | DOCUMENTED | DEFER | M12 | Butuh validator; risiko tinggi |

## 9. Tanda tangan

| Fitur | Referensi | Kepastian | UnionPDF | Milestone |
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
