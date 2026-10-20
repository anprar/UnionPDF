# V14 UI Evidence — Ringkasan Terpilih

**Status:** DRAFT v1 · **Tanggal:** 2026-10-20
**Sumber:** string UI asli dari 35 berkas `.mui` (en-US) build Nitro PDF Pro
**14.41.0.15** yang terpasang, diekstraksi read-only.

> **Catatan hak cipta & distribusi.**
> Korpus mentah (14.452 string UI, 783 kontrol ribbon, 10.284 identifier fitur)
> **disimpan secara lokal saja** dan **tidak** ikut dalam repositori publik —
> mengindersainya adalah=redistribusi konten proprietary dalam skala besar.
> Yang dipublikasikan dokumen ini: **kutipan terpilih** untuk keperluan analisis
> interoperabilitas, ditambah ringkasan turunan. Lihat `.gitignore`.

---

## 1. Bentuk & tab

| Item | Nilai |
|---|---|
| Tab ribbon | 14 (Home, Review, PageLayout, Protect, Erase, Forms, Convert, Share, Help, Accessibility, BackStage, Favorite, IManage) |
| Toolbar kontekstual | 90 |
| Total kontrol | 783 |
| Framework UI | **MFC + BCGSoft BCGControlBar 24.30** (`BCGCBPRO2430u120.dll`) |
| Webview | CEF/Chromium (`libcef.dll` 212 MB) hanya untuk panel web (cloud/help) |
| Logika aplikasi | Native C++ — **bukan** JavaScript (snapshot V8 hanya berisi builtins) |

---

## 2. Kutipan_ui yang paling relevan untuk UnionPDF

### 2.1 Redaksi vs White Out (pemisahan fitur yang wajib ditiru)

Kontrol ribbon: `AVRibbon:Panel:Erase:Redact` dan `AVRibbon:Panel:Erase:Mask`,
dengan elemen `AVRibbon:Element:Erase:Whiteout`.

Kutipan (membedakan jaminan keamanan):

> *"NOTE: The document may contain hidden data and metadata. For a better level of
> protection, please use redaction instead."*

> *"This PDF contains special interactive form functionality that does not allow
> redaction. To convert to a PDF that removes this form functionality and allows
> redaction or other functions, select File Menu > Save As and Flatten."*

> *"This PDF contains special interactive form functionality that does not allow
> White Out. To convert to a PDF that removes this form functionality and allows
> White Out or other functions, select File Menu > Save As and Flatten."*

**Keputusan UnionPDF:** label lebih tegas —
*Redaksi (isi dihapus, dapat diverifikasi)* vs
*Penutupan visual (isi masih ada di dalam berkas)*.

### 2.2 Penghapusan data tersembunyi (12 channel)

Kutipan tunggal yang memuat seluruh daftarnya:

> *"Remove hidden information, such as*
> *· Metadata · Comments and Markups · Links, Actions, Javascripts · Form Fields ·
> Bookmarks · File Attachments · Embedded Thumbnail Images · Embedded Search
> Indexes · Deleted content · Hidden Layers · Hidden or invisible text ·
> Document Structure (Tagging)"*

**Relevansi:** "Remove Metadata" di v14 hanyalah **satu** dari 12 channel.
UnionPDF harus punya fitur "Pembersihan dokumen" tersendiri di M7.

### 2.3 OCR

> *"OCR did not process pages <PAGEVALUES> because they already contain editable
> or searchable text."*

> *"Make scanned documents searchable and editable"*

Kontrol: `AVRibbon:Edit:OCR:Btn`, `AVRibbon:Review:AutoDeskewDoc:Btn`.
Mode: *Create OCR Searchable* · *Create OCR Searchable and Editable*.

**Relevansi:** UnionPDF butuh deteksi halaman tanpa text layer + opsi paksa.

### 2.4 Dua password (open + permissions)

> *"Open passwords require users to enter a password for access, where a
> permissions password restricts what features are available to the user."*

> *"The Document Open and Permissions passwords cannot be the same. Please set a
> different password for Open or Permissions security."*

Tingkat izin granular, mis. *"All document content except metadata"*.

**Relevansi:** model dua password = standar PDF; UnionPDF adopsi di M7.

### 2.5 Operasi halaman

> *"To start, choose one of the three splitting methods to use: split by groups of
> pages, bookmarks, or a specific page range."*

> *"A page range provided is invalid. Please ensure page range exists in document
> and try again."*

> *"Single page documents cannot be split."*

### 2.6 Form

> *"One or more required fields are incomplete. Please fill in all required fields
> before submitting the form."*

> *"This name is already used by an existing field of a different type. Please
> choose new name for this field."*

Tipe field: TextField, CheckBox, RadioButton, ComboBox, ListBox, PushButton,
BarcodeField, DigitalSignature. Plus SetTabOrder (manual/otomatis),
SetCalculationOrder, ResetForm, Import/Export Form Data, Appearance.

### 2.7 Tanda tangan digital

> *"Certificate is valid, document has been changed after it was certified"*

> *"Warning: Unable to sign with remote timestamp server. Signed using local
> timestamp."*

> *"This file cannot be opened by Nitro PDF Pro because it may be harmful to your
> computer."*

Sumber trust: Windows Certificate Store, European Union Trusted Lists (EUTL),
Nitro Approved Trust List.

### 2.8 Konversi

Dua mode eksplisit ke Word:

> *"Highly editable (with layout)"* — *"images are anchored to the nearest
> paragraph"*

> *"Precisely laid out"* — *"each image is anchored to and placed at the same
> position on the page"*

Target lain: Excel (.xlsx), PowerPoint, Rich Text, Plain Text,
gambar (BMP/JPEG/PNG/TIFF). Scan→Word butuh Microsoft Office Document Imaging
(MODI).

### 2.9 Font berlisensi

> *"The license for this font does not allow you to embed it in your file. Please
> try using another font."*

**Relevansi:** UnionPDF harus menangani embedding font yang dilarang lisensinya.

### 2.10 Digital ID (PKCS#12)

> *"Please select a file location and password for your new PKCS#12 digital ID
> file. This password will protect others from using your digital ID in the case
> they obtain a copy somehow."*

> *"Under this Windows user profile you cannot create Digital ID."*

> *"This certificate is not password protected. Documents signed with this
> certificate could be compromised."*

---

## 3. Daftar bahasa OCR v14 (tidak ada di `.mui`; dari `IRIS_OCR\resources`)

**20 paket bahasa/skirp**, total ±23 MB:

| Kode | Bahasa | Berkas | Ukuran |
|---|---|---|---:|
| `autolang` | Deteksi otomatis | autolang.ocr | 2.158 KB |
| `brt` | Breton | brt.ilex | 527 KB |
| `brz` | Portugis Brasil | brz.ilex | 457 KB |
| `cyrillic` | Cyrillic | cyrillic.ocr | 1.858 KB |
| `dan` | Danska | dan.ilex | 1.219 KB |
| `dut` | Belanda | dut.ilex | 1.077 KB |
| `eng` | Inggris | eng.ilex | 605 KB |
| `fin` | Finlandia | fin.ilex | 2.289 KB |
| `frn` | Prancis | frn.ilex | 694 KB |
| `greek` | Yunani | greek.ocr | 1.740 KB |
| `grm` | Jerman | grm.ilex | 1.232 KB |
| `handpr` | Tulisan tangan | handpr.ocr | 1.805 KB |
| `hebrew` | Ibrani | hebrew.ocr | 1.600 KB |
| `itl` | Italia | itl.ilex | 501 KB |
| `latin` | Huruf Latin | latin.ocr | 2.306 KB |
| `nrw` | Norwegia | nrw.ilex | 1.320 KB |
| `ocra1` | OCR-A (mesin ketik) | ocra1.ocr | 55 KB |
| `ocrb1` | OCR-B (mesin ketik) | ocrb1.ocr | 76 KB |
| `prt` | Portugis | prt.ilex | 385 KB |
| `spn` | Spanyol | spn.ilex | 326 KB |
| `swd` | Swedia | swd.ilex | 542 KB |

Berkas pendukung: `fontmetrics.bin`, `latin_1_engine.bin`, `net_latin_1.bin`,
`nop.ilex`.

**Relevansi UnionPDF:** Windows OCR (spike S10) hanya mengenali bahasa yang
terpasang di Windows. Daftar di atas adalah **bar pembanding** untuk keputusan
jalur OCR M5: Tesseract (bisa 100+ bahasa, tapi biner eksternal) vs
Windows OCR (bawaan, tapi terbatas) vs model ONNX sendiri.

---

## 4. Temuan arsitektur dari string & simbol

| Pola | Bukti | Implikasi |
|---|---|---|
| Command-handler per fitur | `AVCmdHandlerConvertToPDFA_RegisterCommandsProc`, `AVCmdHandlerConvertToPDFA_WorkProc` | Cocok dengan use-case UnionPDF |
| Plugin per domain | `pdfa_plugin::init` | Modularitas yang sudah direncanakan |
| Format internal | `CCT2PDF::CCT2PDF` | Format dokumen internal Nitro |
| Ribbon berbasis ID | `AVRibbon:<Tipe>:<Tab>:<Grup>:<Nama>` | UnionPDF butuh identitas sendiri |
| Event analitik | `ProHomePDFCombine`, `ProWordAddinPDFCreated`, … | **Telemetri ada di v14** → UnionPDF: nol |
| Registry per versi | `SOFTWARE\Nitro\PDF Pro\14\Settings` | UnionPDF tidak menulis registry |
| **Edit Text ada di modul anotasi** | `AVRibbon:*NitroTextEditing*` dimiliki `np_annotations.dll` | **Penting:** pendekatan Nitro adalah manipulasi lapisan anotasi, bukan content-stream surgery murni → menurunkan risiko M8 |

---

## 5. Yang tetap tidak diketahui

| Item | Alasan |
|---|---|
| Pintasan keyboard lengkap | BCG menyimpan shortcut di resource biner ribbon, **bukan** teks. Hanya 1 literal `Ctrl+Shift+W` (milik BCGSoft) yang ditemukan. → perlu observasi runtime. |
| Tata letak visual & ikon | Tidak ada di `.mui` (hanya string) |
| Perilaku dinamis antar-dialog | Tidak diamati (aplikasi tidak dieksekusi) |
| Algoritme internal OCR | Ghidra timeout pada `np_ocr.dll` (3,3 MB); analisis native hanya berhasil pada modul ≤ ~700 KB |
| Daftar bahasa OCR *aktif* | Installer dapat memilih subset; yang terpasang di mesin ini = 20 paket |

---

## 6. Bukti

Indeks: `docs/EVIDENCE_INDEX.md` (E-4xx).
Data mentah: **lokal saja** (`docs/research/*.json`, tidak di-commit).
Skrip: `scripts/extract_mui_strings.py`, `scripts/extract_native_strings.py`,
`scripts/build_ribbon_map.py`, `scripts/analyze_ui_evidence.py`,
`scripts/extract_shortcuts_and_ocr_lang.py`.
