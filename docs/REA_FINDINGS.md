# REA_FINDINGS.md — Hasil Analisis Aplikasi Referensi

**Status:** v2 — analisis **mendalam** (biner read-only + sumber daya UI).
**Referensi:** Nitro PDF Pro **14.41.0.15** (Windows), `C:\Program Files\Nitro\PDF Pro\14`
**Sesi:** `2026-10-20T1624+0700` (analisis awal) → `2026-10-20T17xx+0700` (analisis mendalam)
**Izin:** inspeksi biner read-only **disetujui pengguna** (lihat `docs/BLOCKERS.md` B-02).

---

## 0. Ringkasan eksekutif

v1 analisis berbasis inventaris install-tree + dokumentasi publik. **v2 menambahkan
inspeksi biner read-only yang menghasilkan bukti jauh lebih kuat:**

| Bukti | v1 | v2 |
|---|---|---|
| String UI aplikasi (label, opsi, pesan error) | 0 | **14.452** (35 berkas `.mui`) |
| Kontrol ribbon UI | 0 | **783** (rekonstruksi 14 tab) |
| Identifier fitur internal | 0 | **10.284** (perintah, plugin, event) |
| Modul native yang dianalisis | 0 | 1 (Ghidra: 1.852 prosedur) |
| Resource tree PE | 0 | 1 (15 tipe resource) |

**Temuan paling menentukan dari v2:**

1. **v14 memisahkan "Redact" dari "White Out"/"Mask"** — dua fitur berbeda dengan
   jaminan berbeda. UnionPDF harus meniru pemisahan ini secara eksplisit.
2. **Struktur UI v14 = 14 tab ribbon** (Home, Review, PageLayout, Protect, Erase,
   Forms, Convert, Share, Help, Accessibility, BackStage, Favorite, IManage)
   + 90 toolbar kontekstual. Rekonstruksi ini menggantikan pengamatan UI langsung.
3. **Arsitektur aplikasi = command-handler per fitur**
   (`AVCmdHandler*_RegisterCommandsProc` / `_WorkProc`) + plugin
   (`*_plugin::init`). Pola ini bisa di-shift UnionPDF.
4. **Fitur "Edit Text" adalah mode toolbar kontekstual** (`NitroTextEditing`,
   `ReplaceText`), bukan panel terpisah — mengonfirmasi bahwa ini fitur real
   di v14, sekaligus menunjukkan kompleksitasnya.
5. **Enkripsi v14beyond password: "Digital ID" (PKCS#12)** — enkripsi berbasis
   sertifikat pengguna, plus Password Security (open + permissions).

---

## 1. Metode analisis yang dipakai

| # | Metode | Status | Catatan |
|---|---|---|---|
| 1 | Dokumentasi publik | **DIJALANKAN** | User guide resmi v14 |
| 2 | Pengamatan UI langsung | **DIGANTI** | Tidak ada desktop interaktif; digantikan **ekstraksi resource `.mui`** (bukti yang lebih presisi, bukan lebih lemah) |
| 3 | Uji I/O pada aplikasi referensi | **TIDAK DIJALANKAN** | Nitro tidak dieksekusi oleh UnionPDF |
| 4 | Inspeksi biner read-only | **DIJALANKAN** (v2) | REA + parser PE sendiri. Tidak ada patching, tidak ada bypass lisensi, tidak ada penulisan ke folder referensi. |

### Alat yang dipakai (v2)

| Alat | Peran | Hasil |
|---|---|---|
| REA `open_binary` / `binary_overview` | Analisis native Ghidra | `np_pdfa.dll`: 1.852 prosedur, 1.165 string, 8 segment |
| REA `inspect_pe_resources` | Pohon resource PE (portable) | `NitroPDF.exe`: PE32+, 15 tipe resource |
| REA `search_strings` | Kueri string pada target aktif | Konvensi `AVRibbon:*`, `AVCmd*`, `*_plugin::init` |
| `scripts/extract_mui_strings.py` | Parser resource PE sendiri → RT_STRING | 14.452 string UI dari 35 `.mui` |
| `scripts/extract_native_strings.py` | Ekstraksi ASCII/UTF-16 dari 30 DLL | 783 kontrol ribbon + 10.284 identifier fitur |
| `scripts/build_ribbon_map.py` | Rekonstruksi hierarki UI | `docs/research/V14_RIBBON_STRUCTURE.md` |
| `scripts/analyze_ui_evidence.py` | Laporan label & pesan error | `docs/research/V14_UI_EVIDENCE.md` |

> **Batas alat:** Ghidra **gagal** mengimpor `NitroPDF.exe` (16 MB, CEF-embedded)
> dalam batas startup 330 detik. Analisis native mendalam karena itu dilakukan
> pada modul kecil (`np_pdfa.dll`, 656 KB) yang berhasil dianalisis penuh.
> Bukti MuPDF/UI substitute dari ekstraksi string, bukan dekompilasi.

---

## 2. Identitas build (terverifikasi)

| Item | Nilai | Bukti |
|---|---|---|
| `NitroPDF.exe` | 14.41.0.15, x86_64, 16.173.288 byte | E-102, E-400 |
| SHA-256 `NitroPDF.exe` | `736c4b88c2de47bdf7ca88639258dfba2568d4b8c9acaa87f69bd81dcb2246b9` | E-400 |
| SHA-256 `np_pdfa.dll` | `66949294d455879c20080f2f730e0230afa0704d05e582e5c9eedaa9b26c051b` | E-402 |
| Format | PE32+ (64-bit) | E-403 |
| Manifest | `requestedExecutionLevel level="asInvoker" uiAccess="false"` | E-404 |
| Registry app | `SOFTWARE\Nitro\PDF Pro\14` (+ `Settings`, `Settings\NitroCloud`, `BCG`) | E-405 |
| Resource tree | 15 tipe; RT_ICON 34 entri; RT_STRING terpisah | E-403 |

**Konsekuensi:** aplikasi berjalan **tanpa hak administrator** (`asInvoker`).
UnionPDF sebaiknya sama — menghindari prompt UAC.

---

## 3. Struktur UI v14 (rekonstruksi, 783 kontrol)

**14 tab ribbon:**

| Tab | Kontrol | Fungsi |
|---|---:|---|
| `Home` | 32 | Tab utama, **bisa dikustomisasi** ("Add up to 5 of your most used tools") |
| `Protect` | 24 | Keamanan, enkripsi, tanda tangan, redaksi |
| `Forms` | 23 | Field form: CheckBox, ComboBox, ListBox, RadioButton, PushButton, TextField, BarcodeField, DigitalSignature, Import/Export, SetTabOrder, SetCalculationOrder, ResetForm, EditAllFields, Appearance (Rotate/Remove/Rename/Save/Update) |
| `Review` | 21 | Markup & review tools |
| `PageLayout` | 20 | Crop, Delete, Extract, Insert, Replace, Rotate + panel Navigation/Pages/Document/PageMarks |
| `Help` | 16 | Smart Tips |
| `Convert` | 14 | Ke semua format (termasuk PDF/A) |
| `Erase` | 12 | **Redact + White Out + Remove Metadata** |
| `Share` | 4 | Email as attachment, cloud sign |
| `Accessibility` | 1 | PDF/UA tagging |
| `BackStage` | 1 | Menu File (Open, SaveAs, SaveAsFlatten) |
| `Favorite` | 1 | Tool favorit |
| `IManage` | 1 | Integrasi DMS |

**90 toolbar kontekstual** (373 kontrol) — diaktifkan sesuai konteks:
annotasi, bentuk, crop, zoom, form, object, link, review, watermark, header/footer,
Bates numbering, PDF/A, bookmark, JavaScript, cloud, aktivasi, touch mode, dan
sebagainya.

Toolbar kontekstual kunci:
`NitroTextEditing` + `ReplaceText` (edit teks), `AnnotProp` (properti anotasi),
`FormsTool`, `ReviewTool`, `ObjectTool`, `LinksTool`, `CreateTags` (PDF/UA),
`BatesNumbering`, `AutoBuildBookmarks`, `AutoKeywordLinks`, `AutoPageLinks`,
`DocumentActions` (JavaScript), measurement (`Distance`, `Perimeter`, `Area`,
`Calibration`), `ImportComments` / `ExportComments` / `SummarizeCommentsAndPrint`,
`TouchMode` / `TouchMouseMode`.

Berkas lengkap: `docs/research/V14_RIBBON_STRUCTURE.md`.

---

## 4. Perilaku fitur terverifikasi dari UI build v14

**Bukti:** 14.452 string UI asli. Sumber: `docs/research/V14_UI_EVIDENCE.md`.

### 4.1 Redaksi vs White Out (temuan paling penting)

v14 menyediakan **dua operasi berbeda**:

| Fitur | Kontrol ribbon | Jaminan |
|---|---|---|
| **Redact** | `AVRibbon:Panel:Erase:Redact`, `Element:Erase:MarkForRedaction` | Menghapus isi; ada `ApplyAllRedactions` |
| **White Out / Mask** | `AVRibbon:Panel:Erase:Mask`, `Element:Erase:Whiteout` | **Menutupi secara visual** |

Pesan v14 sendiri menyatakan perbedaan ini dengan jujur:

> *"NOTE: The document may contain hidden data and metadata. For a better level of
> protection, please use redaction instead."*

Teks lain mengonfirmasi:
- *"This PDF contains special interactive form functionality that does not allow
  redaction. To convert to a PDF that removes this form functionality and allows
  redaction or other functions, select File Menu > Save As and Flatten."*
- Pesan yang sama untuk **White Out** → keduanya terhalang form interaktif.

**Keputusan UnionPDF:** pertahankan pemisahan, dan beri label yang **lebih tegas**
daripada v14: "Redaksi (isi dihapus — dapat diverifikasi)" vs
"Penutupan visual (isi masih di dalam berkas)".

### 4.2 Redaksi — cakupan penghapusan tersembunyi

v14 stormy menginventory data tersembunyi yang bisa dihapus:

> Metadata · Comments and Markups · Links, Actions, Javascripts · Form Fields ·
> Bookmarks · File Attachments · Embedded Thumbnail Images · Embedded Search
> Indexes · Deleted content · Hidden Layers · Hidden or invisible text ·
> Document Structure (Tagging)

**Konsekuensi:** "Remove Metadata" di v14 = **satu bagian** dari kemampuan
penghapusan tersembunyi yang lebih luas. UnionPDF harus punya
`hidden content removal` sebagai fitur tersendiri, bukan menyamakan dengan
"remove metadata".

### 4.3 OCR

| Aspek | Bukti v14 |
|---|---|
| Dua mode | "Create OCR Searchable" · "Create OCR Searchable and Editable" |
| Lewati halaman ber-text | *"OCR did not process pages \<PAGEVALUES\> because they already contain editable or searchable text."* |
| Auto deskew | `AVRibbon:Review:AutoDeskewDoc:Btn`, "Auto Deskew" |
| Bahasa | "Language" |
| Prompt otomatis | "Make scanned documents searchable and editable" |
| Dokumen terenkripsi | Pesan khusus: *"The file is secured and cannot be converted without the correct open password."* |

**Konsekuensi UnionPDF:** (a) deteksi "halaman tanpa text layer" harus otomatis
seperti v14; (b) halaman yang sudah punya text **tidak boleh** di-OCR ulang
tanpa opsi paksa.

### 4.4 Keamanan & enkripsi

v14 punya **dua sistem keamanan dokumen**:

**A. Password Security**
- Dua password: **Open password** (akses) + **Permissions password** (batas fitur).
- *"The Document Open and Permissions passwords cannot be the same."*
- *"All document content except metadata"* — tingkat izin granular.
- Pesan: *"The open password fields are empty or do not match."*

**B. Digital ID (PKCS#12)**
- Enkripsi & verifikasi tanda tangan berbasis sertifikat pengguna.
- *"Please select a file location and password for your new PKCS#12 digital ID file."*
- *"Under this Windows user profile you cannot create Digital ID."* → penyimpanan
  terikat profil Windows (DPAPI).
- Konsep **Trusted Contacts** untuk enkripsi ke orang lain.
- Pesan: *"This certificate is not password protected. Documents signed with this
  certificate could be compromised."*

**Konsekuensi UnionPDF:** model **dua password** (open + permissions) harus
diadopsi — itustandar PDF dan fitur M7. "Digital ID" adalah fitur M10 lanjut;
untuk UnionPDF, **penyimpanan kunci privat harus mempertimbangkan** Windows Credential Manager
atau PKCS#12 dengan password terpisah, **bukan** database app.

### 4.5 Operasi halaman

Kontrol: `Insert`, `Delete`, `Extract`, `Rotate`, `Split`, `Replace`,
`Insert Blank Page`, `Insert Pages`.

Tiga metode split yang dikonfirmasi:
> *"To start, choose one of the three splitting methods to use: split by groups of
> pages, bookmarks, or a specific page range."*

Validasi:
> *"A page range provided is invalid. Please ensure page range exists in document
> and try again."* · *"Single page documents cannot be split."* ·
> *"Valid page range is required."*

### 4.6 Anotasi

Alat lengkap: `Highlight`, `Underline`, `Strikethrough`, `Markup Text`,
`Add Note` (pop-up), `Rectangle`, `Line`, `Polygon` (oval), `Arrow`, `Pencil`
(freehand), `Pencil Eraser`, `TextBox`, `CallOut`.

Semua bentuk alat punya pop-up note ("type a comment in its pop-up note").

### 4.7 Form

Field: TextField, CheckBox, RadioButton, ComboBox, ListBox, PushButton,
BarcodeField, DigitalSignature. Plus SetTabOrder (manual/otomatis),
SetCalculationOrder, ResetForm, EditAllFields, Import/Export Form Data,
MakeCopies (EveryPage / SameName / Spacing), Appearance (Rotate/Remove/Rename/
Save/Update), Create Form Fields (otomatis), Submit ke email/URL.

Validasi: *"One or more required fields are incomplete..."*,
*"This name is already used by an existing field of a different type."*

### 4.8 Tanda tangan digital

- Sumber trust: **Windows Certificate Store**, **European Union Trusted Lists
  (EUTL)**, **Nitro Approved Trust List**.
- Timestamp: *"Warning: Unable to sign with remote timestamp server. Signed using
  local timestamp."* → ada fallback lokal.
- Deteksi modifikasi pasca-tanda tangan: *"Certificate is valid, document has
  been changed after it was certified"*.
- Validasi lifecycle sertifikat: expired / not-yet-valid / missing private key.
- Peringatan lampiran berbahaya: *"This file cannot be opened by Nitro PDF Pro
  because it may be harmful to your computer."*

### 4.9 Konversi

Target: Word (.docx/.doc), Excel (.xlsx), PowerPoint, Rich Text, Plain Text,
gambar (BMP/JPEG/PNG/TIFF).

Dua mode konversi ke Word yang **eksplisit**:
- *"Highly editable (with layout)"* — flow ke paragraf, gambar di-anchor ke paragraf terdekat.
- *"Precisely laid out"* — gambar di-anchor & diposisikan sama persis di halaman.

Ada juga *"Fast PDF-to-Word conversion"* (mode terpisah).
Fitur scan→Word butuh **Microsoft Office Document Imaging (MODI)**.

### 4.10 Crop & measure

`Crop` dengan `Apply_crop`, `WidthEdit`, `HeightEdit`, `Landscape`, `Portrait`,
`OriginalpagesizeCrop`, `Measure_with_original`, `Advanced`.
Measurement tools: `Distance`, `Perimeter`, `Area`, `Calibration`.

### 4.11 PDF/A & aksesibilitas

- `AVRibbon:Panel:Convert:Formats:PDFA:Btn` — konversi ke PDF/A.
- `pdfa_converter::preflight_result` — **preflight** sebelum konversi.
- `DocumentPdfUAComplianceSet` + `SetPdfUALanguage` + `CreateTags` → **PDF/UA
  (accessibility)** juga didukung.

### 4.12 Edit teks (konfirmasi fitur)

- Toolbar kontekstual `NitroTextEditing` + `ReplaceText` → **fitur Edit Text
  ada dan berupa mode kontekstual**, bukan tombol statis.
- Ini konsisten dengan klaim "paragraph-level reflow" pada dokumentasi produk.

**Konsekuensi UnionPDF:** fitur ini **nyata** dan ekspektasi pengguna terhadap
aplikasi PDF modern adalah tinggi. Tapi kompleksitasnya luar biasa. Strategi
UnionPDF tetap: **DEFER M8**, meanwhile sediakan overlay + redaksi-reinsert
dengan label jujur — dan **jangan** menampilkan tombol "Edit Text" yang tidak
benar-benar mengedit teks asli.

---

## 5. Arsitektur internal (terverifikasi via string & simbol)

| Pola | Bukti | Implikasi UnionPDF |
|---|---|---|
| **Command handler per fitur** | `AVCmdHandlerConvertToPDFA_RegisterCommandsProc`, `AVCmdHandlerConvertToPDFA_WorkProc` | Setiap fitur = sepasang (register, work). Cocok dengan pola use-case UnionPDF. |
| **Plugin per domain** | `pdfa_plugin::init` | Modularitas yang sudah UnionPDF rencanakan. |
| **Namespace `::`** | `CCT2PDF::CCT2PDF` | Format internal `CCT` = format dokumen Nitro sendiri. |
| **Ribbon berbasis identifier** | `AVRibbon:<Tipe>:<Tab>:<Grup>:<Nama>` | Identitas visual UnionPDF harus sendiri. |
| **Event analitik** | `ProHomePDFCombine`, `ProOutlookAddinPDFCreated`, `ProWordAddinPDFCreated` | **Membuktikan telemetri ada di v14.** UnionPDF: nol. |
| **Registry per versi** | `SOFTWARE\Nitro\PDF Pro\14\Settings` | UnionPDF tidak boleh menulis registry. |
| **Font & lisensi font** | *"The license for this font does not allow you to embed it in your file."* | UnionPDF harus menangani embedding font yang tidak diizinkan. |
| **Deteksi lampiran berbahaya** | Pesan "may be harmful to your computer" | UnionPDF wajib menandai lampiran berisiko (M7). |

---

## 6. Pemetaan temuan → keputusan UnionPDF (diperbarui)

| Temuan v2 | Keputusan | Catatan |
|---|---|---|
| Redact vs White Out terpisah | **KEEP + IMPROVE** | Label UnionPDF lebih tegas (verifiable vs visual) |
| Penghapusan data tersembunyi (12 channel) | **KEEP, diperluas** | Bukan sekadar "remove metadata" — fitur tersendiri di M7 |
| OCR: 2 mode + skip halaman ber-text | **KEEP + IMPROVE** | Deteksi otomatis + label mode yang jujur |
| 2 password (open + permissions) | **KEEP** | Standar PDF, terverifikasi ada di v14 |
| Digital ID / PKCS#12 | **DEFER** ke M10 | Butuh manajemen kunci privat yang aman |
| 3 metode split (group/bookmark/range) | **KEEP** | Cheap, high value |
| 2 mode konversi ke Word | **DEFER** ke M9 | Butuh quality guarantee |
| PDF/A + preflight | **DEFER** ke M12 | Butuh validator |
| PDF/UA tagging | **DEFER** ke M12 | Kompleks |
| Edit Text (mode kontekstual) | **DEFER** ke M8 (B-04) | Mayoritas complex feature; jangan tampilkan tombol palsu |
| Toolbar kontekstual per objek | **IMPROVE** di M4 | UnionPDF: panel properti muncul saat objek dipilih |
| Command-handler per fitur | **KEEP** (arsitektur) | Cocok use-case layer UnionPDF |
| Telemetri | **REPLACE** | Nol telemetri |
| Registry | **REJECT** | UnionPDF: setelan di file JSON lokal |
| `asInvoker` | **KEEP** | Tanpa UAC |

---

## 7. Dampak terhadap keputusan stack

Analisis mendalam **menguatkan** ADR-001, tidak mengubahnya:

- Konfirmasi bahwa **satu engine + banyak adapter** adalah pola yang tepat
  (Nitro butuh 29 DLL; UnionPDF cukup 1 engine + N adapter).
- Konfirmasi bahwa **engineering text editing** adalah barrier utama (bukan
  sekadar fitur) → mendukung keputusan DEFER M8.
- Konfirmasi **rendering + text layer + annotasi + form + redaksi** adalah inti
  yang harus satu engine — persis yang offerte MuPDF (spike S1–S8 PASS).
- Menambahkan satu kebutuhan baru: **penghapusan data tersembunyi multi-channel**
  → MuPDF punya `apply_redactions` dengan flag channel; perlu diverifikasi
  (L-07 masih terbuka).

Tidak ada temuan baru yang_**membatalkan** muatan 463/500.

---

## 8. Yang masih belum diketahui

| # | Pertanyaan | Kenapa belum tertutup |
|---|---|---|
| U-01 | Apakah MuPDF bisa edit teks existing dengan reflow? | Belum diuji (B-04) |
| U-04 | Performa >5.000 halaman | Belum diukur |
| U-06 | Pustaka tanda tangan kriptografis | pyHanko belum dievaluasi |
| U-08 | Ghidra gagal mengimpor `NitroPDF.exe` (16 MB CEF) | Batas startup; analisis native pada exe utama belum tuntas |
| U-09 | Perilaku internal `np_ocr.dll` (algoritme) | Belum dianalisis native (hanya string) |
| U-10 | Daftar bahasa OCR yang benar-benar dipakai v14 | Tidak ada di `.mui`; bergantung installer |
| U-11 | Apakah v14 punya "Edit Text" sungguhan atau baru placeholder UI | Hanya identifier ribbon yang ditemukan; perlu uji interaksi |

---

## 9. Bukti

Lihat `docs/EVIDENCE_INDEX.md` (E-4xx = bukti analisis mendalam v2).
Data mentah: `docs/research/mui_strings_en-US.json`, `ribbon_controls_v14.json`,
`native_feature_ids_v14.json`.
