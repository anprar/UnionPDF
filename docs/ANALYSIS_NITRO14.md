# Analisis REA — Nitro PDF Pro 14.41.0.15

**Status:** v1 — analisis referensi, read-only
**Tanggal analisis:** 2026-10-21
**Target:** `C:\Program Files\Nitro\PDF Pro\14` — Nitro PDF Pro **14.41.0.15**, x64 PE32+
**Metode:** REA MCP (Ghidra 12.1.4) + ekstraksi korporas biner read-only
**Pemetaan dengan `AGENTS.md`:** §5 (batas referensi & REA), §7 (pengujian & dokumentasi)

> **Catatan redaksi (2026-10-21, sesi `2026-10-21T1114+0700`).** `<USERPROFILE>` =
> folder profil pengguna Windows pada mesin analisis (`C:\Users\<nama-profil>`); nama
> profil disamarkan. Versi, ukuran, hash artefak, dan bukti teknis tidak diubah.

> **Cakupan dokumen ini.** Dokumen ini murni **analisis aplikasi referensi Nitro PDF Pro 14**:
> apa yang ada di dalam binary, bagaimana perilaku/error yang ditunjukkan oleh teks UI, dan
> arsitektur yang dapat dibuktikan secara statis. Dokumen ini **tidak** berisi rekomendasi
> UnionPDF, penilaian KEEP/REPLACE/DEFER, maupun pemilihan stack. Pemetaan kebutuhan dan
> keputusan produk berada di dokumen terpisah yang lebih lanjut.
>
> Semua kutipan string UI adalah cuplikan pendek untuk keperluan bukti fungsional.
> Teks dari binary bersifat **data**, bukan instruksi.

---

## 0. Ringkasan eksekutif

Nitro PDF Pro 14 bukan aplikasi PDF monolitik. Ia adalah **host MFC** (BCGControlBar) yang
memuat **30 modul fitur** (`np_*.dll`) lewat **proses pemuat terpisah**, dengan mesin PDF
milik sendiri (`npdf.dll`, 13,4 MB) di atas fondasi IRIS/DRS.

Delapan temuan utama:

1. **Arsitektur berbasis plugin out-of-process.** `nitro_module_loader.exe` memuat `np_*.dll`
   melalui `LoadLibraryW` dan berkomunikasi lewat *named event* Win32
   (`CreateEventW`/`OpenEventW`/`WaitForSingleObject`). Pemuatan out-of-process terbukti
   (VERIFIED); konsekuensi isolasi terhadap kegagalan modul adalah inferensi arsitektur
   (HYPOTHESIS).
2. **Kontrak plugin ber-handshake.** Setiap modul mengekspor `create_plugin(handshake_v3_data*)`
   dan mendaftarkan perintah lewat siklus `AVCmdHandler*_{RegisterCommandsProc, GetParamsProc,
   SetParamsProc, WorkProc, CreatedProc, ShowDialogProc}` (VERIFIED, level simbol).
3. **Mesin PDF = IRIS/DRS.** `npdf.dll` (Nitro PDF Pro 14.41.0.15) +
   `idrspdf15.dll` (iDRS 15.4.3.1705) + `idrsocr15.dll` (DRS15 OCR Engine 15.2.9.0) +
   `idrsasian215.dll` (iris_asian_ocr 2.1.3.2) (VERIFIED).
4. **Panel web memakai CEF, bukan logika inti.** `libcef.dll` = Chromium Embedded Framework
   122.0.6261.130 (V8 12.2). CEF hanya dipakai untuk *smart tip* dan panel web —
   25 identifier `ProCEFContent*` seluruhnya milik `np_smart_tips.dll` (VERIFIED).
5. **Konversi PDF/A punya dua tahap: preflight + laporan validasi.** Simbol
   `nitro::pdfa::pdfa_converter::preflight_to_convert_to_pdfa` dan
   `::GetValidationReport` (VERIFIED, level simbol).
6. **Redaksi dan *whiteout* adalah dua fitur berbeda.** *Whiteout* menghapus tampilan;
   *redaction* "permanently delete all content beneath the active redaction marks", dengan
   peringatan jujur bahwa apply "may not have completely removed the selected content"
   (VERIFIED).
7. **Enkripsi mendukung 4 algoritma.** 40-bit ARC4, 128-bit ARC4, 128-bit AES, 256-bit AES
   (VERIFIED). Sertifikat digital + "trusted contacts" untuk enkripsi per-penerima (VERIFIED).
8. **Ada stack produk pihak ketiga yang sangat besar:** Ghostscript 10.06, ASP.NET Core Kestrel
   + PDFKit.NET 5.0.198.0 untuk XFA (109,6 MB), SOLIDWORKS PDF tools + Tesseract (72 MB),
   CEF (46 MB), BugSplat, MIP SDK, iManage (VERIFIED).

### 0.1 Angka kunci

| Metrik | Nilai | Sumber |
|---|---:|---|
| Berkas `.mui` (locale `en-US`) | 36 | `docs/research/mui_strings_en-US.json` |
| String UI (kemunculan / unik ternormalisasi) | 14.452 / 4.177 | idem |
| Identifier kontrol ribbon | 783 | `docs/research/ribbon_controls_v14.json` |
| Modul berbeda yang memiliki kontrol ribbon | 29 (28 `np_*` + `NitroPDF.exe`) | idem |
| Tab ribbon bernama | 13 | idem |
| Grup toolbar kontekstual | 228 (12 placeholder `Dummy*`) | idem |
| Identifier fitur (`Pro*`/`On*`/`AVCmd*`/`plugin::call`) | 10.284 | `docs/research/native_feature_ids_v14.json` |
| Model bahasa OCR | 20 (+ `autolang`, `nop`) | `docs/research/ocr_languages_and_shortcuts_v14.json` |
| Berkas instalasi / ukuran | 1.014 / 854,6 MB | inventaris folder referensi |
| Prosedur `np_pdfa.dll` (Ghidra) | 1.852 | REA `binary_overview` |
| Prosedur `nitro_module_loader.exe` (Ghidra) | 263 | REA `binary_overview` |
| Resource `np_ocr.dll` (PE) | 62 entri, 10 icon group | REA `inspect_pe_resources` |

### 0.2 Koreksi terhadap angka lama

| Angka lama | Angka terverifikasi | Catatan |
|---|---|---|
| 35 berkas `.mui` | **36** | ada satu `.mui` tambahan yang terlewat |
| 14 tab ribbon | **13 tab bernama** | angka lama memasukkan bucket `(kontekstual)` sebagai tab |
| 90 toolbar kontekstual | **228 grup** (80 bernama fitur spesifik) | definisi lama tidak reproducible |
| 20 bahasa OCR | **20 model + `autolang` + `nop`** | cocok, definisi diperjelas |

Semua angka pada dokumen ini dapat diperiksa ulang dengan
`scripts/verify_analysis_corpus.py` (exit 0 = cocok).

---

## 1. Metodologi, lingkungan, dan batasan

### 1.1 Lingkungan

| Item | Nilai |
|---|---|
| OS | Windows 11 (x64) |
| Shell eksekusi | PowerShell |
| Python analisis | `.venv` → 3.13.9 |
| Provider REA | Ghidra 12.1.4 (via `tools.rea`) |
| Folder referensi | `C:\Program Files\Nitro\PDF Pro\14` (read-only) |
| Snapshot REA | `<USERPROFILE>\AppData\Local\Temp\opencode\rea_nitro_snapshot.json` (118.135 byte, 6 evidence record) |

### 1.2 Urutan metode (mengikuti `AGENTS.md` §5)

Metode yang **dijalankan**, berurutan:

1. **Dokumentasi lokal & inventaris** — inventaris 1.014 berkas, versi produk tiap binary,
   struktur direktori.
2. **Ekstraksi korporas (metode 4, terarah)** — lima skrip read-only di `scripts/`:
   `extract_mui_strings.py`, `extract_native_strings.py`, `extract_shortcuts_and_ocr_lang.py`,
   lalu turunan `build_ribbon_map.py` dan `analyze_ui_evidence.py`.
3. **Inspeksi teknis terarah via REA (metode 4)** — `open_binary` + `binary_overview` +
   `list_procedures` + `search_strings` + `procedure_pseudo_code` + `inspect_pe_resources`,
   lalu `close_binary` dengan snapshot.
4. **Verifikasi ulang (metode 3, parsial)** — setiap angka kunci di dokumen ini dicocokkan
   ulang dengan skrip `scripts/verify_analysis_corpus.py`.

Metode yang **tidak** dijalankan (lihat §5.1): pengamatan UI langsung pada instalasi
referensi dan uji input-output dengan dokumen sintetis.

### 1.3 Yang tidak dilakukan (batas akses & keamanan)

- Tidak menjalankan, memodifikasi, atau meng-*patch* executable/DLL/registry/service Nitro.
- Tidak membuka fitur terkunci, tidak memalsukan aktivasi/trial, tidak mengambil product key,
  token, atau credential.
- Tidak menyalin kode proprietary, DLL, engine, logo, atau aset Nitro ke UnionPDF.
- Tidak mengunggah binary atau dokumen ke layanan eksternal.
- Tidak menguji eksekusi JavaScript/attachment dari dokumen (hanya menganalisis stringnya).
- Tidak mengukur performa runtime (tidak ada eksekusi aplikasi).

### 1.4 Reproduksi

```powershell
.venv\Scripts\python.exe scripts\extract_mui_strings.py
.venv\Scripts\python.exe scripts\extract_native_strings.py
.venv\Scripts\python.exe scripts\extract_shortcuts_and_ocr_lang.py
.venv\Scripts\python.exe scripts\build_ribbon_map.py
.venv\Scripts\python.exe scripts\analyze_ui_evidence.py
.venv\Scripts\python.exe scripts\verify_analysis_corpus.py   # cek angka dokumen ini
```

Korporas mentah disimpan di `docs/research/*.json` dan **tidak** di-commit (berisi konten
proprietary pihak ketiga dalam skala besar). Yang dipublikasikan hanya dokumen turunan ini
beserta kutipan fungsional seperlunya.

---

## 2. Inventaris arsitektur

### 2.1 Komposisi instalasi

| Direktori | Isi | Ukuran | Peran |
|---|---|---:|---|
| (root) | `NitroPDF.exe`, 30 `np_*.dll`, `npdf.dll`, 132 DLL total | ± 480 MB | host + modul fitur + mesin |
| `en-US`, `de`, `es`, `fr`, `it`, `nl` + varian regional | 36 `.mui` per locale utama | ± 20 MB | string UI terlokalisasi |
| `cef/` | `libcef.dll` (202 MB), `mozjs-102.dll`, `.pak` locale | 46,4 MB | runtime web (smart tip / panel web) |
| `xfa/` | ASP.NET Core Kestrel, `coreclr.dll`, `TallComponents.PDF.Kit.dll` 5.0.198.0, BouncyCastle | 109,6 MB | desainer XFA berbasis web |
| `solid_framework/` | `PdfFlt.flt`, `SolidLanguage.dll`, `tesseract.dll`, `ocr_solid.dll` | 72,0 MB | toolkit PDF SOLIDWORKS + OCR sekunder |
| `IRIS_OCR/resources/` | 22 kunci bahasa (20 model + `autolang` + `nop`) + 3 berkas pendukung | 23,0 MB | paket bahasa OCR |
| `Certs/` | 10 berkas `.pem` (termasuk EU Trusted List 8,3 MB) | 8,2 MB | trust store tanda tangan digital |
| `imanage/` | `iwObjects.dll` 10.9.4.39, `Newtonsoft.Json.dll` | 4,8 MB | integrasi DMS iManage |
| `x64/`, `x86/` | `PS5UI.dll`, `PScript5.dll`, `NxPdfCreator.ppd`, `Eztwain4.dll` | 9,7 MB | driver PostScript, akuisisi TWAIN |

Total: **1.014 berkas / 854,6 MB**. Angka ini penting sebagai referensi distribusi: sebagian
besar volume berasal dari runtime dan toolkit pihak ketiga, bukan dari logika fitur PDF.

### 2.2 Profil binary inti

| Binary | Ukuran | Versi (ProductName) | Fungsi |
|---|---:|---|---|
| `NitroPDF.exe` | 15.794,2 KB | Nitro PDF Pro 14.41.0.15 | host MFC/BCGControlBar; 109 kontrol ribbon |
| `npdf.dll` | 13.706,2 KB | Nitro PDF Pro 14.41.0.15 | **mesin PDF inti** (diekspor sebagai `NPDF.DLL`) |
| `pdf_resources.dll` | 16.203,2 KB | Nitro PDF Pro 14.41.0.15 | resource (font, template) |
| `idrspdf15.dll` | 12.921,7 KB | iDRS 15.4.3.1705 | mesin IRIS PDF |
| `idrsocr15.dll` | 17.267,2 KB | DRS15 / OCR Engine 15.2.9.0 | mesin OCR IRIS |
| `idrsasian215.dll` | 6.959,2 KB | iris_asian_ocr 2.1.3.2 | OCR/layout Asia |
| `libcef.dll` | 207.332,2 KB | CEF 122.1.13+chromium-122.0.6261.130 | runtime web |
| `gsdll64.dll` | 24.920,7 KB | GPL Ghostscript 10.06.0 | processing PostScript |
| `BCGCBPRO2430u120.dll` | 9.654,7 KB | BCGControlBar Professional 24.3.0.9 | UI ribbon/control |
| `mip_core.dll`, `mip_file_sdk.dll` | 4.314,7 + 9.429,7 KB | MIP SDK 1.13.161 | label sensitivitas (Microsoft Information Protection) |
| `np_forms.dll` | 7.827,2 KB | — | formulir (modul fitur terbesar) |
| `np_annotations.dll` | 6.164,2 KB | — | anotasi + **alat edit teks** |
| `np_set_security.dll` | 5.814,2 KB | — | enkripsi & sertifikat |
| `np_cloud_storage.dll` | 4.528,2 KB | — | SharePoint/OneDrive |
| `np_nitro_sign.dll` | 4.092,7 KB | — | tanda tangan berbasis cloud |
| `np_digital_signature.dll` | 3.855,7 KB | — | tanda tangan digital/PKCS |
| `np_convert_pdf.dll` | 3.292,2 KB | — | ekspor ke Word/Excel/PPT/teks/gambar |
| `np_ocr.dll` | 3.280,2 KB | — | orkestrasi OCR |
| `nitro_module_loader.exe` | 49,7 KB | — | pemuat modul fitur (proses terpisah) |
| `html_to_pdf.exe` | 618,7 KB | Nitro PDF Pro 14.41.0.15 | konversi HTML→PDF |
| `metrics_tool.exe` | 3.653,2 KB | Nitro PDF Pro 14.41.0.15 | pengumpulan metrik penggunaan |
| `nitro_temp_file_cleaner.exe` | 385,7 KB | — | pembersihan file sementara |

**Checksum anchor** (SHA-256, 16 karakter pertama) untuk memastikan versi yang dianalisis:

| Binary | SHA-256 (prefix) |
|---|---|
| `NitroPDF.exe` | `736c4b88c2de47bd` |
| `npdf.dll` | `584be631bd9bf4f9` |
| `np_pdfa.dll` | `66949294d455879c` |
| `np_ocr.dll` | `eb3d78b637cf742c` |
| `np_redaction.dll` | `53fce5d3c5a9f123` |
| `np_set_security.dll` | `f22920e1de4bb2ec` |
| `np_digital_signature.dll` | `5debe09cfd6f8997` |
| `np_forms.dll` | `96bc23f10fed810c` |
| `np_convert_pdf.dll` | `d17181053c2cc4da` |
| `libcef.dll` | `d16ad88419cfa0b9` |
| `gsdll64.dll` | `06e60099f26eedc3` |
| `idrsocr15.dll` | `0e7808d17eb0650e` |
| `nitro_module_loader.exe` | `ce8f590831e97177` |

### 2.3 Model proses

Terbukti dari `nitro_module_loader.exe` (Ghidra: 263 prosedur, 168 string):

| Bukti | Makna |
|---|---|
| string `np_*.dll` | modul yang dimuat berupa glob `np_*.dll` |
| `LoadLibraryW`, `SetDllDirectoryW` | pemuatan DLL saat runtime |
| `FindFirstFileW`/`FindNextFileW` | enumerasi berkas modul di direktori instalasi |
| `CreateEventW`, `OpenEventW`, `WaitForSingleObject`, `SetEvent` | IPC antarproses berbasis *named event* |
| `TerminateProcess`, `GetSystemInfo` | supervisi proses anak |

**Kesimpulan (VERIFIED untuk pemuatan out-of-process; implikasi berikut bersifat inferensi):**
setiap modul fitur dimuat sebagai **proses terpisah** di bawah host. Dampak yang relevan:
(a) kegagalan modul kemungkinan tidak menjatuhkan host; (b) biaya memori terbagi antarproses;
(c) UI harus menangani state "modul belum siap / gagal start".

### 2.4 Kontrak plugin & siklus hidup perintah

Bukti level simbol dari `np_pdfa.dll` (Ghidra, `image_base 0x180000000`):

```
NPDF.DLL::nitro::pdfa::pdfa_converter::preflight_to_convert_to_pdfa
NPDF.DLL::nitro::pdfa::pdfa_converter::GetValidationReport
NPDF.DLL::nitro::pdfa::pdfa_converter::convert_to_pdfa
nitro::pdfa::create_plugin @ 0x180031bb0
```

Pseudocode dekompilasi `create_plugin` (Ghidra, **bukan** source asli):

```c
/* class std::shared_ptr<class nitro::plugin_framework::plugin> __cdecl
   nitro::pdfa::create_plugin(struct handshake_v3_data * __ptr64) */
handshake_v3_data * __cdecl nitro::pdfa::create_plugin(handshake_v3_data *param_1)
{
    FUN_1800398d0((undefined8 *)param_1, in_RDX);
    return param_1;
}
```

Pola perintah didokumentasikan oleh identifier `AVCmdHandler*`:

| Suffiks | Arti |
|---|---|
| `RegisterCommandsProc` | mendaftarkan perintah ke framework |
| `GetParamsProc` / `SetParamsProc` | membaca/menulis parameter perintah |
| `WorkProc` | menjalankan pekerjaan (dapat berjalan lama) |
| `CreatedProc` | inisialisasi objek perintah |
| `ShowDialogProc` | menampilkan dialog (terpakai `AVCmdHandlerPasswordSecurity_ShowDialogProc`) |
| `GetPropsProc` | deskripsi properti untuk UI |

Terdapat 38 identifier `AVCmdHandler*` unik, termasuk `AVCmdHandlerOCRText_*`,
`AVCmdHandlerPageEdit_*`, `AVCmdHandlerPrint_*`, `AVCmdHandlerExecuteJavaScript_*`,
`AVCmdHandlerDeleteMetaData_*`, `AVCmdHandlerPasswordSecurity_*`.

**Pola plugin `plugin::call` (50 identifier unik)** menunjukkan batas internal yang jelas,
contoh: `redaction_plugin::init`, `ocr_plugin::init`, `pdfa_plugin::init`,
`accessibility_plugin::init`, `compare_pdf_plugin::init`, `object_detector::detect_objects`,
`xfa_document::save_to_path`, `embedded_pdf_document::open_document_for_embedding`,
`signature_tree::signature_tree`, `sharepoint_picker::*`, `nitro::get_temp_file`.

### 2.5 Stack pihak ketiga

| Komponen | Versi / bukti | Lisensi yang terindikasi | Peran |
|---|---|---|---|
| BCGControlBar Professional | 24.3.0.9 | komersial (fgCommandBars) | kerangka UI ribbon |
| Chromium Embedded Framework | 122.0.6261.130 (V8 12.2) | BSD-3 + Chrome | panel web / smart tip |
| Ghostscript | 10.06.0 | **GPL** | PostScript & raster |
| IRIS/DRS (iDRS, DRS15) | 15.4.3.1705 / 15.2.9.0 | komersial | mesin PDF + OCR |
| SolidOCR / iris_asian_ocr | 2.1.3.2 | komersial | OCR Asia |
| ASP.NET Core Kestrel + .NET (CoreCLR) | `coreclr.dll` 5.005,7 KB | MIT | XFA web app |
| PDFKit.NET (TallComponents) | 5.0.198.0 | komersial | PDF di sisi .NET |
| BouncyCastle.Crypto | 3.240,7 KB | MIT | kriptografi |
| Tesseract OCR + SOLIDWORKS PDF tools | `tesseract.dll` 6.189,2 KB | Apache-2.0 + komersial | OCR sekunder & filter PDF |
| MIP SDK | 1.13.161 | komersial (Microsoft) | label sensitivitas |
| iManage iwObjects | 10.9.4.39 | komersial | integrasi DMS |
| Newtonsoft.Json | — | MIT | JSON |
| BugSplat (`BsSndRpt64.exe`, `BugSplatHD64.dll`) | `ProBS*` ×4 | komersial | pelaporan crash |
| `metrics_tool.exe` | 3.653,2 KB | — | pengumpulan metrik penggunaan |

### 2.6 Data dan aset lokal

- **OCR**: `IRIS_OCR/resources` berisi 25 berkas = 22 kunci bahasa + 3 berkas pendukung
  (`fontmetrics.bin`, `latin_1_engine.bin`, `net_latin_1.bin`).
  Kunci: `autolang`, `latin`, `cyrillic`, `greek`, `hebrew`, `handpr`, `ocra1`, `ocrb1`,
  `brt`, `brz`, `dan`, `dut`, `eng`, `fin`, `frn`, `grm`, `itl`, `nop`, `nrw`, `prt`, `spn`,
  `swd` → **20 model** nyata (tanpa `autolang` dan `nop`).
  Total bobot model: 25,8 MB (terbesar `latin.ocr` 2.306,3 KB; `fin.ilex` 2.288,6 KB).
- **Sertifikat**: `Certs/` = 10 `.pem`, termasuk EU Trusted List (`eutl.pem`, 8.371,7 KB),
  CA timestamping DigiCert, dan root CA Notarius.
- **Font OCR**: `net_latin_1.bin` 747,9 KB + `fontmetrics.bin` 13,1 KB.

### 2.7 Catatan distribusi

- Instalasi penuh **854,6 MB** didominasi library pihak ketiga (CEF 202 MB, XFA/.NET 110 MB,
  SOLIDWORKS 72 MB, Ghostscript 25 MB, IRIS 40 MB), bukan logika fitur.
- Modul fitur dipisah per domain → muatan tiap area dapat dimuat terpisah sesuai kebutuhan.
- `metrics_tool.exe` + `BugSplat` menunjukkan adanya telemetri dan pelaporan crash pada
  referensi.

---

## 3. Katalog fitur (penuh)

Katalog ini memuat seluruh domain fitur yang teridentifikasi dari bukti. Kolom **Bukti**
menyebut sumber: Ribbon = identifier `AVRibbon:*`, MUI = string `.mui`, Simbol = level
simbol Ghidra, Aset = berkas di folder referensi.

Tingkat kepastian:
`VERIFIED` (terbukti langsung dari binary) · `DOCUMENTED_NOT_TESTED` (teks UI ada, alur
belum dijalankan) · `HYPOTHESIS` (disimpulkan) · `UNKNOWN` (belum terjawab).

### 3.1 Viewer & navigasi

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Zoom in/out tanpa mematikan alat aktif | MUI "Zoom in on the page without disabling the tool you are currently using." | app | VERIFIED |
| Fit page / fit width | Ribbon `FitPage`, `FitWidth` | app | VERIFIED |
| Rotasi tampilan sementara | Ribbon `TemporarilyRotateView` | `page_edit` | VERIFIED |
| Full screen + toolbar full-screen terpisah | MUI "Disable full screen toolbar when in full screen mode" | app | VERIFIED |
| Zoom slider / zoom tools | Ribbon `ZoomSlider`, `ZoomTool` | app | VERIFIED |
| Pencarian teks dengan progres per halaman | MUI "Searching page %d of %d...", "Nitro PDF Pro has finished searching the document." | app | VERIFIED |
| Pencarian lanjutan | Ribbon `Advanced Search` | app | VERIFIED |
| Bookmark pane + pencarian bookmark | MUI "Searching bookmarks..." | `bookmarks` | VERIFIED |
| Panel lampiran (portfolio) | MUI "attachments panel located to the lower left on the vertical toolbar" | `attachments` | VERIFIED |
| Panel struktur tag | Ribbon `Artifacts`, `Tagging` | `accessibility` | VERIFIED |
| Atur aplikasi sebagai penampil PDF default | MUI "Set Nitro PDF Pro as default viewer" | app | VERIFIED |
| Mode baca / fokus | Ribbon `SelectTextAndGraphic`, `Snapshot` | app | VERIFIED |

### 3.2 Operasi halaman

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Sisip halaman (blank/file/scanner/clipboard) | Ribbon `InsertBlankPage`, `InsertFromFile`, `InsertFromScanner`, `InsertFromClipboard` | `page_edit` | VERIFIED |
| Hapus halaman | Ribbon `Delete` | `page_edit` | VERIFIED |
| Putar halaman | Ribbon `Rotate`, `TemporarilyRotateView` | `page_edit` | VERIFIED |
| Potong halaman | Ribbon `Crop`, `CropToolsCRC`, `Apply_crop` | `page_edit` | VERIFIED |
| Ganti halaman dengan halaman dari PDF lain | Ribbon `Replace` | `page_edit` | VERIFIED |
| Pisah & ekstrak halaman | Ribbon `Split`, `Extract` | `page_edit` | VERIFIED |
| Atur ukuran halaman (potrait/landscape) | Ribbon `Portrait`, `Landscape` | `page_edit` | VERIFIED |
| Ganti ukuran (tinggi/lebar) | Ribbon `HeightEdit`, `WidthEdit` | `page_edit` | VERIFIED |
| Validasi rentang halaman | MUI "Valid page range is required", "The number you have entered is out of range. Document has %d pages." | `page_edit` | VERIFIED |
| Larangan menghapus seluruh halaman | MUI "It is not possible to delete all the document's pages. One page must remain in the document." | `commands` | VERIFIED |
| Halaman dokumen dengan ukuran campuran | MUI "Cropped page size: `<SIZE> <UNIT>`" | `page_edit` | VERIFIED |
| Pengukuran pada halaman | Ribbon `Measure`, `Measure_with_original` | `annotations`, `page_edit` | VERIFIED |

### 3.3 Edit objek, teks & gambar

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Edit teks yang sudah ada | Ribbon kontekstual `TextEditing`, `TypeText`, `Typewriter`, `TypeTextAlignmentTool` | `annotations` | VERIFIED |
| Format teks: nama/ukuran/warna/huruf/spasi | Ribbon `Fontname`, `FontSize`, `FontColor`, `FontCase`, `FontSpacing`, `FontRestriction`, `Justify` | `annotations` | VERIFIED |
| Sisip kotak teks dengan panah acuan | MUI "Click and drag to add a text box annotation with a reference arrow." | `annotations` | VERIFIED |
| Ganti gambar mempertahankan ukuran | MUI "Replace the selected image while preserving its original size." | `objects` | VERIFIED |
| Ekstrak gambar ke berkas | MUI "Extract the selected image and save it to a separate file." | `objects` | VERIFIED |
| Ubah resolusi & ruang warna gambar | MUI "Current image resolution is %d x %d dots (pixels) per inch." | `objects` | VERIFIED |
| Kecerahan/kontras gambar | Ribbon `Adjust` | `objects` | VERIFIED |
| Crop, flip, rotate, size gambar | MUI 8 label pengoperasian gambar | `objects` | VERIFIED |
| Perataan objek (8 arah + distribute) | Ribbon `Align*`, `Distribute*`, `Center*`, `Spacing` | `objects`, `annotations`, `forms`, `links` | VERIFIED |
| Z-order gambar | MUI "Bring the selected image in front of all other objects." / "Send ... behind all other objects." | `objects` | VERIFIED |
| Batasan font tidak tertanam | MUI "This font is not embedded in the file or installed on your computer. Editing with it is not possible." | `javascript` | VERIFIED |

### 3.4 Anotasi & markup

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Highlight + komentar | MUI "Highlight text and type a comment in its pop-up note." | `annotations` | VERIFIED |
| Coret / garis bawah | MUI "Strikethrough text..." / "Underline text..." | `annotations` | VERIFIED |
| Catatan (note) pada halaman | Ribbon `AddNote` | `annotations` | VERIFIED |
| Bentuk: garis, panah, kotak, oval, polyline | 7 label tool gambar | `annotations` | VERIFIED |
| Gambar bebas (ink) + penghapus | MUI "Erase pencil drawings by clicking and dragging..." | `annotations` | VERIFIED |
| Atribut anotasi: warna, opasitas, ketebalan, gaya | Ribbon `FillColor`, `Opacity`, `Thickness`, `Style` | `annotations` | VERIFIED |
| Sembunyikan semua markup | Ribbon `HideComments` | `annotations` | VERIFIED |
| Balas & selesaikan komentar | MUI "View and edit the information associated with comments made from this account." | `annotations` | VERIFIED |
| Impor/ekspor komentar | MUI "Import and export comments to and from this document." | `annotations` | VERIFIED |
| Ringkasan komentar (fitur AI/ringkasan) | Ribbon `SummarizeComments`; MUI "Printing & summarizing" | `annotations` | VERIFIED |
| Font anotasi hilang → ganti font | MUI "The font '%s' is missing. Please select a replacement font in Preferences->Commenting->Printing & summarizing->Font" | `annotations` | VERIFIED |

### 3.5 Formulir

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Isi & simpan form (AcroForm) | Ribbon `Forms`, `FormFields` | `forms` | VERIFIED |
| Buat field: teks, checkbox, radio, dropdown, listbox | Ribbon `TextField`, `CheckBox`, `RadioButton`, `ComboBox`, `ListBox` | `forms` | VERIFIED |
| Field barcode | Ribbon `BarcodeField`; MUI "Error: Create Barcode." | `forms` | VERIFIED |
| Field signature | Ribbon `DigitalSignature` | `forms` | VERIFIED |
| Tombol aksi (submit/reset/hitung) | Ribbon `PushButton` | `forms` | VERIFIED |
| Validasi field + opsi "Ignore" | MUI "The value you entered is invalid. To ignore validation click Ignore." | `forms` | VERIFIED |
| Field wajib | MUI "One or more required fields are incomplete..." | `forms` | VERIFIED |
| Tampilan/ sembunyikan field | MUI "Show field: %s" / "Hide field: %s" | `forms` | VERIFIED |
| Tab order manual/otomatis | MUI "Do you want to set tab order manually? Click No if you want to set tab order automatically." | `forms` | VERIFIED |
| Urutan kalkulasi | Ribbon `SetCalculationOrder` | `forms` | VERIFIED |
| Appearance stream (nama, simpan, gunakan ulang) | Ribbon `SaveNewAppearance`, `RenameAppearance`, `SetAsDefault` | `forms` | VERIFIED |
| Flatten form & simpan | Ribbon `SaveAsFlatten`; MUI "Flatten and Save As so that form fields and annotations are no longer interactive." | app | VERIFIED |
| Kirim form (email/URL) | MUI "The form cannot be sent. Please check for spaces or syntax errors in the recipient email address." | `forms` | VERIFIED |
| AutoForm (dari data) | Ribbon `AutoForm`, `CreateForms` | `forms`, `convert_pdf` | VERIFIED |
| Field duplikat | MUI "This name is already used by an existing field of a different type." | `forms` | VERIFIED |

### 3.6 Review, perbandingan & metadata

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Bandingkan dua dokumen (pixel) | MUI "Compare two PDF documents pixel by pixel and highlight the detected differences." | `compare_pdf` | VERIFIED |
| Laporan perbedaan | Ribbon `ContentComparePDF` | `compare_pdf` | VERIFIED |
| Dokumen portfolio tak dapat dibandingkan | MUI "The '%s' is a PDF Portfolio document. These types of documents cannot be compared." | `compare_pdf` | VERIFIED |
| Hapus metadata | Ribbon `RemoveMetadata`; `AVCmdHandlerDeleteMetaData_*` | `redaction` | VERIFIED |
| Lihat & ubah properti dokumen | Ribbon `Properties`; `AVCmdHandlerMetaData_*` | `commands` | VERIFIED |
| Screenshot / snapshot halaman | Ribbon `Snapshot` | app | VERIFIED |

### 3.7 Keamanan, enkripsi & redaksi

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Enkripsi 40-bit ARC4 | MUI "40-bit ARC4 (Adobe Reader 3 and above)" | `set_security` | VERIFIED |
| Enkripsi 128-bit ARC4 | MUI "128-bit ARC4 (Adobe Reader 6 and above)" | `set_security` | VERIFIED |
| Enkripsi 128-bit AES | MUI "128-bit AES (Adobe Reader 7 and above)" | `set_security` | VERIFIED |
| Enkripsi 256-bit AES | MUI "256-bit AES (Adobe Reader X and above)" | `set_security` | VERIFIED |
| Open password vs permissions password | MUI "Open passwords require users to enter a password for access, where a permissions password restricts what features are available to the user." | `set_security` | VERIFIED |
| Profil keamanan tersimpan | Ribbon `ManageProfiles`; MUI "View, add, edit, and delete saved security profiles." | `set_security` | VERIFIED |
| Enkripsi dengan sertifikat digital | MUI "User's digital ID certificates are used to encrypt documents so that only users selected by you can access the document." | `set_security` | VERIFIED |
| Kontak tepercaya + izin per penerima | MUI "A PDF file can have different security permissions for each contact it's secured for." | `set_security` | VERIFIED |
| Blokir enkripsi bila dokumen bertanda tangan | MUI "This document contains digital signatures and cannot be secured." | `set_security` | VERIFIED |
| Hapus keamanan | Ribbon `RemoveSecurity`; MUI "Are you sure you want to disable the document's security?" | `set_security` | VERIFIED |
| Redaksi aman (hapus isi) | MUI "Permanently delete all content beneath the active redaction marks." | `redaction` | VERIFIED |
| Redaksi otomatis berbasis kata kunci | Ribbon `SearchAndRedact` | `redaction` | VERIFIED |
| Tandai halaman penuh untuk redaksi | Ribbon `MarkPages` | `redaction` | VERIFIED |
| Ulangi tanda redaksi antar halaman | Ribbon `RepeatMarkAcrossPages` | `redaction` | VERIFIED |
| Whiteout (hanya visual) | Ribbon `Whiteout` | `redaction` | VERIFIED |
| Masking (black box visual) | Ribbon `Mask` | `redaction` | VERIFIED |
| Peringatan jujur tentang hasil redaksi | MUI "Warning: Applying redaction may not have completely removed the selected content." | `redaction` | VERIFIED |
| Dokumen dengan overlay redaksi tertunda | MUI "This document contains pending redaction overlays. Redactions must be applied..." | `redaction` | VERIFIED |
| Izin: hanya isi form / isi+tanda tangan / +komentar | 3 label izin | `set_security`, `nitro_sign` | VERIFIED |

### 3.8 Tanda tangan

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Tanda tangan digital (Digital ID) | Ribbon `DigSig`; MUI "Apply a digital signature to this document using a digital ID." | `digital_signature` | VERIFIED |
| Sertifikasi dokumen (attestation) | Ribbon `CertifyDocument`; MUI "Certify this document with a digital signature to attest to its contents..." | `digital_signature` | VERIFIED |
| Validasi tanda tangan | MUI "Validating signatures..."; status "Signature is Invalid / Unknown / Unverified" | `digital_signature` | VERIFIED |
| Status signature & dokumen berubah setelah signed | MUI "Signature is valid, document has been changed after it was signed" | `nitro_sign` | VERIFIED |
| Timestamp tanda tangan | MUI "Signature is timestamped" / "Signature is timestamped but the timestamp could not be verified" | `digital_signature` | VERIFIED |
| Private key hilang / sertifikat kedaluwarsa | 2 pesan khusus | `digital_signature` | VERIFIED |
| Dokumen terkunci → tak bisa ditimpa | MUI "The document is locked by another application or user and cannot be overwritten." | `digital_signature` | VERIFIED |
| QuickSign (tanda tangan gambar) | Ribbon `CreateNewSignature`; MUI "Create an image of your signature and have QuickSign apply it" | `signature_stamp` | VERIFIED |
| Profil QuickSign berpassword | MUI "An incorrect password was provided for this QuickSign profile." | `signature_stamp` | VERIFIED |
| Batas ukuran berkas untuk QuickSign | MUI "The document selected exceeds the maximum file size limit of {} MB." | `signature_stamp` | VERIFIED |
| Nitro Sign (tanda tangan cloud) | Ribbon `NitroSign`, `RequestSignature`; MUI "The following people have digitally counter - signed this document." | `nitro_sign` | VERIFIED |
| Galerie tanda tangan | Ribbon `ManageSignatures` | `signature_stamp` | VERIFIED |
| Batasan AIP/MIP pada tanda tangan | MUI "Digital Signatures or Certificates cannot be added to documents that are classified by Microsoft Azure Information Protection." | `digital_signature` | VERIFIED |

### 3.9 OCR

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| OCR → PDF searchable | Ribbon `OCR`; MUI "Make scanned documents searchable and editable" | `ocr` | VERIFIED |
| OCR searchable **dan** editable | MUI "Create OCR Searchable and Editable" | `ocr` | VERIFIED |
| Bahasa OCR (20 model + autodeteksi) | `IRIS_OCR/resources` | `ocr` | VERIFIED |
| Mode mesin: OCR-A1 / OCR-B1 (numerik, alfanumerik, Eurobanking) | 6 label mode | `ocr` | VERIFIED |
| Auto-deskew dokumen | Ribbon `AutoDeskewDoc` | `ocr` | VERIFIED |
| Lewati halaman yang sudah punya teks | MUI "OCR did not process pages `<PAGEVALUES>` because they already contain editable or searchable text." | `ocr` | VERIFIED |
| Lewati halaman resolusi invalid | MUI "...because they have invalid resolution." | `ocr` | VERIFIED |
| Kegagalan sebagian halaman | MUI "OCR was not able to be run on one or more of the pages..." | `ocr` | VERIFIED |
| Error alokasi memori | MUI "OCR has encountered a memory allocation error and cannot proceed." | `ocr` | VERIFIED |
| Atribusi vendor engine | MUI "OCR technology by Image Recognition Integrated Systems S.A." | `ocr` | VERIFIED |
| Loading modul iDRS | MUI "An error was encountered when loading the iDRS module." | `ocr` | VERIFIED |

### 3.10 Konversi & pembuatan dokumen

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| PDF → Word | Ribbon `ToWord` | `convert_pdf` | VERIFIED |
| PDF → Excel | Ribbon `ToExcel` | `convert_pdf` | VERIFIED |
| PDF → PowerPoint | Ribbon `ToPPTX` | `convert_pdf` | VERIFIED |
| PDF → Rich Text | Ribbon `ToRichText` | `convert_pdf` | VERIFIED |
| PDF → plain text | Ribbon `ToPlainText` | `convert_pdf` | VERIFIED |
| PDF → gambar (BMP/JPEG/PNG/TIFF) | Ribbon `ToImage` | `convert_pdf` | VERIFIED |
| PDF → gambar + OCR Office (MODI) | MUI "Microsoft Office Document Imaging (MODI) is required to use this feature." | `convert_pdf` | VERIFIED |
| Ekstrak gambar | Ribbon `ExtractImages` | `convert_pdf` | VERIFIED |
| Ekstrak tabel → Excel | Ribbon `ExtractTables` | `convert_pdf` | VERIFIED |
| Ekstrak form → data | Ribbon `ExtractForms` | `convert_pdf` | VERIFIED |
| PDF/A-1b/2b/3b | Ribbon `PDF-A-1b_Btn`, `PDF-A-2b_Btn`, `PDF-A-3b_Btn` | `pdfa` | VERIFIED |
| Buat PDF dari Office/WordPerfect/HTML/teks/gambar | MUI "Use the Create PDF Files dialog to quickly convert Microsoft Office, WordPerfect, HTML, text, and images into PDF." | `create_pdf` | VERIFIED |
| Gabungkan berkas | Ribbon `Combine` | `create_pdf` | VERIFIED |
| Add-in Office & Outlook | MUI "Your Nitro PDF Pro Office add-in is disabled or installed incorrectly." | `create_pdf` | VERIFIED |
| HTML → PDF | `html_to_pdf.exe` | app | VERIFIED |
| Add-in Excel | `ProExcelAddinPDFCreated` | app | VERIFIED |
| Pemrosesan PostScript | `gsdll64.dll` (Ghostscript 10.06), `x64/PS5UI.dll` | app | VERIFIED |
| Driver printer PDF | `x64/NxPdfCreator.ppd`, `NxPdfCreator.exe` | app | VERIFIED |
| Konversi gagal: file terkunci / sandi salah / izin | 4 pesan spesifik | `convert_pdf` | VERIFIED |
| Ukuran halaman melebihi batas konversi | MUI "Conversion to image has failed because the page exceeds the maximum allowed size." | `convert_pdf` | VERIFIED |
| Dokumen tanpa tabel → gagal ke Excel | MUI "Conversion to Excel has failed since the selected PDF file does not contain any tables." | `convert_pdf` | VERIFIED |

### 3.11 Watermark, stempel & nomor

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Watermark teks/gambar + profil | MUI "Add text- and image-based watermarks to multiple pages and documents using profiles with custom opacity and layering options." | `watermarks` | VERIFIED |
| Header/footer + profil | MUI "Add text- and image-based headers and footers across multiple pages and documents using custom profiles." | `watermarks` | VERIFIED |
| Halaman: all/odd/even/first/last | 5 label | `watermarks` | VERIFIED |
| Stempel teks/gambar + profil | Ribbon `CreateNewStamp` | `stamper` | VERIFIED |
| Nomor Bates | Ribbon `BatesNumbering`, `RemoveBatesNumbering`; MUI "Adding Bates numbers.." | `stamper` | VERIFIED |
| Nomor urut | MUI "Insert a sequential number or code onto each page of this document." | `stamper` | VERIFIED |
| Konflik profil (hanya dokumen genap / min. halaman) | 2 pesan | `watermarks` | VERIFIED |

### 3.12 Scan, lampiran, bookmark, link, layer

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Scan ke PDF (TWAIN) | Ribbon `SingleScan`, `CreateScanProfile`; `x86/Eztwain4.dll` | `scan2pdf` | VERIFIED |
| Profil scan (ganti nama, preset tak dapat dihapus) | MUI "Preset scan profile can't be deleted. It will be reset to default state." | `scan2pdf` | VERIFIED |
| Kegagalan akuisisi scanner | MUI "The image could not be acquired from the selected scanner." | `scan2pdf` | VERIFIED |
| Lampirkan berkas / ekstrak lampiran | MUI "Add a file as an attachment to this document." | `attachments` | VERIFIED |
| Portfolio PDF | MUI "Portfolio PDF creation has failed." | `attachments` | VERIFIED |
| Blokir lampiran executable | MUI "The file %s is being blocked from launching as it is an executable file format." | `actions` | VERIFIED |
| Peringatan file berbahaya | MUI "This file cannot be opened by Nitro PDF Pro because it may be harmful to your computer." | `actions` | VERIFIED |
| Bookmark manual & otomatis (dari header/style) | MUI "Automatically build a set of bookmarks based on headers and styles used in this document." | `bookmarks` | VERIFIED |
| Link halaman, weblink, link kata kunci, auto page link | 4 label tool | `links` | VERIFIED |
| Lapisan OCG | MUI "View and hide the Optional Content Group layers"; "This layer is locked." | `layers` | VERIFIED |

### 3.13 Aksesibilitas

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Auto-tag dokumen | MUI "Automatically apply tags to the document." | `accessibility` | VERIFIED |
| Struktur tag manual (root/parent/child/sibling) | 4 label tool | `accessibility` | VERIFIED |
| Kegagalan embedding font saat auto-tag | MUI "Failed to embed all fonts. Please review Fonts tab in Document Properties for more details." | `accessibility` | VERIFIED |
| Ganti tipe tag menghapus atribut | MUI "Changing the tag type will remove some type specific attributes." | `accessibility` | VERIFIED |
| ID sel tabel | MUI "The ID is not associated with any table cell in this document." | `accessibility` | VERIFIED |

### 3.14 Batch, cloud, DMS & preferensi

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Batch processing (perintah ke banyak berkas) | MUI "Specify and execute a set commands to one or more PDF files." | `commands` | VERIFIED |
| Laporan/log batch | MUI "ERRORS FOUND: Process was completed with errors. See log for more." | `commands` | VERIFIED |
| SharePoint / OneDrive | Ribbon `MSSecurity`, `RMSSecurity`; `sharepoint_*` | `cloud_storage` | VERIFIED |
| WebDAV | Ribbon kontekstual; pesan DAV | `web_dav` | VERIFIED |
| iManage (DMS) | `imanage/iwObjects.dll` 10.9.4.39 | — | VERIFIED |
| Label sensitivitas (AIP/MIP) | `mip_core.dll` + pesan AIP di `digital_signature` | — | VERIFIED |
| Preferensi (antarmuka, bahasa, font komentar, JavaScript) | MUI "JavaScript was detected but not executed because of Preference." | app | VERIFIED |
| Ubah bahasa aplikasi | MUI "Please restart Nitro PDF Pro to apply the application language change." | app | VERIFIED |
| Blokir URL | MUI "URL was blocked (see preferences for more details): '%s'" | app | VERIFIED |
| Smart tip / FTUX (panel CEF) | 25 identifier `ProCEFContent*` | `smart_tips` | VERIFIED |
| Activation / trial / volume licensing | Ribbon `Activation`, `Licensing`, `VolumeLicensing` | app | VERIFIED |
| Support Tools | Ribbon `SupportTools`; `NitroPDFSupportTools.exe` | app | VERIFIED |

### 3.15 JavaScript & aksi dokumen

| Fitur | Bukti | Modul | Kepastian |
|---|---|---|---|
| Tambah & edit aksi JavaScript | MUI "Add reusable JavaScript actions to this document." | `javascript` | VERIFIED |
| Eksekusi JavaScript pada event dokumen | MUI "Execute JavaScript on document events." | `javascript` | VERIFIED |
| Uji & eksekusi JS di jendela terpisah | MUI "Test and execute JavaScript code in a separate window." | `javascript` | VERIFIED |
| Aksi bernama | MUI "Named actions" | `actions` | VERIFIED |
| Modul JavaScript "deprecated" terpisah | `np_java_script_deprecated.dll` (6 kontrol ribbon) | — | VERIFIED |
| Hapus semua JS pada aksi terpilih | MUI "This will clear all JavaScript from the selected document actions. Continue?" | `javascript` | VERIFIED |

> Catatan: `np_java_script_deprecated.dll` adalah modul terpisah dengan 339 string identik
> dengan `np_javascript.dll` (347 string), sehingga **msubset**; pemisahan ini konsisten
> dengan internesionalisasi versi fitur, bukan implementasi terpisah (HYPOTHESIS).

---

## 4. Deep-dive 25 fitur

### 4.0 Kriteria seleksi

25 fitur dipilih dengan tiga kriteria yang dinyatakan terbuka:

1. **Lebar permukaan** — fitur muncul di banyak tab/grup ribbon atau punya banyak kontrol
   kontekstual.
2. **Risiko teknis** — fitur menyentuh integritas dokumen, keamanan, atau format yang
   sulit direimplementasi (enkripsi, redaksi, tanda tangan, OCR, konversi).
3. **Cakupan domain** — representatif untuk seluruh kelompok fitur di §3, agar tidak ada
   domain yang terlewat.

Hasil seleksi: 1 PDF/A, 2 OCR, 3 Redaksi, 4 Enkripsi password, 5 Enkripsi sertifikat,
6 Tanda tangan digital, 7 QuickSign, 8 Nitro Sign, 9 Formulir, 10 JavaScript/aksi,
11 Operasi halaman, 12 Edit teks/gambar, 13 Anotasi, 14 Compare, 15 Konversi keluar,
16 Buat PDF, 17 Scan, 18 Watermark/header-footer, 19 Bates/stempel, 20 Aksesibilitas,
21 Lampiran, 22 Bookmark, 23 Auto-link, 24 Optimizer, 25 Cloud/WebDAV.

---

### 4.1 Konversi PDF/A — preflight dan laporan validasi

- **Modul:** `np_pdfa.dll` (641,2 KB) — *plugin tipis*; seluruh simbol implementasi berada di
  `npdf.dll` (disebut sebagai `NPDF.DLL` oleh Ghidra).
- **Bukti simbol** (Ghidra, `np_pdfa.dll`, image base `0x180000000`):
  `nitro::pdfa::pdfa_converter::preflight_to_convert_to_pdfa`,
  `nitro::pdfa::pdfa_converter::convert_to_pdfa`,
  `nitro::pdfa::pdfa_converter::GetValidationReport`,
  `nitro::pdfa::create_plugin` @ `0x180031bb0`; string
  `"Unexpected result value for pdfa_converter::preflight_result: "`.
- **Bukti UI:** ribbon `AVRibbon:Panel:Convert:Formats:PDFA:Btn`; toolbar kontekstual
  `PDF-A-1b_Btn`, `PDF-A-2b_Btn`, `PDF-A-3b_Btn` (dimiliki `np_smart_tips.dll`, yaitu tombol
  penunjuk discoverability, bukan implementasi).
- **Input → Output:** PDF (satu atau banyak) → PDF/A-1b / 2b / 3b.
- **Opsi & alur:** tiga tombol level terpisah (bukan dropdown) → pengguna memilih konformitas
  secara eksplisit. Alur dua tahap: **preflight** lebih dulu, baru **konversi**, dengan
  **laporan validasi** sebagai keluaran tersendiri.
- **Perilaku error:** nilai enum preflight yang tak terduga ditangani lewat pesan
  "Unexpected result value for pdfa_converter::preflight_result: " (memakai placeholder
  `%s`-style) — artinya preflight mengembalikan kode berstatus, bukan boolean.
- **Kebutuhan teknis yang teridentifikasi:** engine PDF harus (a) menulis struktur tag PDF/A,
  (b) menulis metadata XMP, (c) memvalidasi konstrain (font tertanam, transparansi, JavaScript),
  (d) mengembalikan laporan per-konstrain, bukan hanya lulus/gagal.
- **Kepastian:** VERIFIED untuk arsitektur & opsi; **DOCUMENTED_NOT_TESTED** untuk kualitas
  hasil konversi dan kelengkapan laporan validasi.

### 4.2 OCR — searchable dan editable

- **Modul:** `np_ocr.dll` (3.280,2 KB, 62 resource PE, 10 icon group) +
  `idrsocr15.dll` (17,3 MB, DRS15 15.2.9.0) + `idrsasian215.dll` (OCR Asia).
- **Bukti UI:** ribbon `AVRibbon:Category:OCR`; MUI "Recognize Text using OCR",
  "Make scanned documents searchable and editable", "Use this tool on a scanned document to be
  able to search, markup or edit text."
- **Input → Output:** PDF hasil scan → PDF dengan lapisan teks (dapat dicari, disorot,
  diedit).
- **Opsi:** dua target keluaran eksplisit — "Create OCR Searchable" dan "Create OCR
  Searchable **and Editable**"; 6 mode mesin (OCR-A1 Numeric/Alphanumeric/Eurobanking,
  OCR-B1 Numeric/Alphanumeric/Eurobanking); 20 model bahasa + `autolang`; auto-deskew.
- **Validasi & perilaku error (terbukti dari string):**
  - halaman yang sudah punya teks editable/searchable **dilewati** (bukan di-OCR ulang);
  - halaman dengan **resolusi invalid dilewati**;
  - kegagalan sebagian halaman dilaporkan sebagai "OCR was not able to be run on one or more of
    the pages..." dengan rujukan ke pane Output;
  - kegagalan alokasi memori ditangani eksplisit;
  - kegagalan pemuatan modul `iDRS` ditangani eksplisit.
- **Kebutuhan teknis:** dua mode keluaran berbeda (searchable ≠ editable) adalah perbedaan
  kualitas yang nyata — mode editable memerlukan rekonstruksi posisi glyph, bukan sekadar
  lapisan teks tak terlihat. Model bahasa dimuat sebagai berkas terpisah
  (total 25,8 MB untuk 20 model) → perlu strategi lazy-load.
- **Kepastian:** VERIFIED untuk opsi, mode, dan pesan error; **DOCUMENTED_NOT_TESTED** untuk
  akurasi, kecepatan, dan perilaku pada dokumen campuran.

### 4.3 Redaksi aman versus whiteout dan masking

- **Modul:** `np_redaction.dll` (1.959,2 KB; 26 kontrol ribbon).
- **Bukti UI:** "Permanently delete all content beneath the active redaction marks.",
  "Configure the appearance and labeling of redaction marks.",
  "Automatically redact all found instances of keywords or phrases.",
  "Find, mark, and permanently remove sensitive information from this document."
- **Tiga operasi berbeda (penting untuk pembedaan):**
  | Operasi | Arti | Risiko |
  |---|---|---|
  | Redact | menghapus isi di bawah tanda | benar-benar menghapus data |
  | Whiteout | menutupi tampilan | **data tetap ada** |
  | Mask | kotak hitam visual | **data tetap ada** |
- **Opsi:** tandai halaman penuh (`MarkPages`), ulangi tanda di semua halaman
  (`RepeatMarkAcrossPages`), pencarian & redaksi kata kunci (`SearchAndRedact`), properti
  (`RedactionProperties`), terapkan semua (`ApplyAllRedactions`).
- **Perilaku error & kejujuran (penting):**
  - "Warning: Applying redaction may not have completely removed the selected content.
    Please check that content has been redacted and if not, use the Edit Tool to select and
    delete the text or image." → **aplikasi mengakui batasnya**.
  - "This document contains pending redaction overlays. Redactions must be applied for
    sensitive data to be securely removed from the PDF file." → ada state "tertunda" yang
    bisa terlupakan.
  - "NOTE: The document may contain hidden data and metadata. For a better level of
    protection, please use redaction instead." → whiteout tidak dianggap sebagai redaksi.
  - "This operation will permanently remove content that is marked for redaction. Once the
    file is saved these changes cannot be undone." → konfirmasi eksplisit, irreversible.
- **Kebutuhan teknis:** pipeline yang benar-benar menghapus objek + objek gambar di bawah
  area tanda, membersihkan metadata, dan memvalidasi ulang (ekstraksi teks setelah redaksi
  harus kosong).
- **Kepastian:** VERIFIED untuk semantik & pesan; **UNKNOWN** untuk apakah implementasinya
  juga membersihkan content stream yang tidak terlihat.

### 4.4 Enkripsi berbasis password

- **Modul:** `np_set_security.dll` (5.814,2 KB; 16 kontrol ribbon; 693 string unik — terbesar
  kedua setelah app).
- **Empat algoritma, dua digabung (open vs permissions):**

  | Algoritma | Label aplikasi |
  |---|---|
  | RC4 40-bit | "40-bit ARC4 (Adobe Reader 3 and above)" |
  | RC4 128-bit | "128-bit ARC4 (Adobe Reader 6 and above)" |
  | AES 128-bit | "128-bit AES (Adobe Reader 7 and above)" |
  | AES 256-bit | "256-bit AES (Adobe Reader X and above)" |

- **Input → Output:** PDF → PDF terenkripsi dengan open password dan/atau permissions
  password; profil keamanan dapat disimpan & diterapkan ulang (`ManageProfiles`).
- **Validasi:** "The open password fields are empty or do not match.", "The permissions
  password fields are empty or do not match.", "Password fields must match.",
  "Incorrect password. Please enter your password again."
- **Perilaku error:** "Password security was not applied to this document due to an internal
  error. Please try again." (gagal ≠ terenkripsi sebagian); dokumen bertanda tangan tidak
  boleh diamankan; email sertifikat memakai MAPI32 ("Invalid MAPI32.dll.").
- **Kebutuhan teknis:** implementasi RC4 & AES standard, perbedaan semantics owner/user
  password, dan penulisan dictionary/encryption PDF yang kompatibel Acrobat.
- **Kepastian:** VERIFIED untuk algoritma & alur; **UNKNOWN** untuk detail parameter
  enkripsi (V/R, panjang kunci, derive) karena memerlukan analisis `npdf.dll` (terlalu besar
  untuk Ghidra) atau uji dokumen.

### 4.5 Enkripsi dengan sertifikat digital & kontak tepercaya

- **Modul:** `np_set_security.dll`; konteks `CertificateSecurity`, `MyDigitalID`,
  `TrustedContacts`.
- **Bukti UI:** "User's digital ID certificates are used to encrypt documents so that only
  users selected by you can access the document."; "A PDF file can have different security
  permissions for each contact it's secured for. Highlight a contact to select their
  permissions."; "Trusted Contacts are people you've received a digital certificate from..."
- **Alur:** ekspor/import Digital ID (`.pfx`/PEM), kirim sertifikat via email (MAPI),
  kelola kontak tepercaya, terapkan enkripsi per penerima dengan izin berbeda.
- **Perilaku error:** "Unknown error occurred while exporting the certificate to a file.",
  "Unknown error occurred while importing the certificate.", "Error occurred while sending
  the message to recipient."
- **Kebutuhan teknis:** PKCS#12/PEM, direktori sertifikat Windows, enkripsi hybrid
  (enkripsi kunci sesi + Recipient), izin per recipient.
- **Kepastian:** VERIFIED untuk model fitur; **UNKNOWN** untuk detail kriptografi.

### 4.6 Tanda tangan digital & sertifikasi dokumen

- **Modul:** `np_digital_signature.dll` (3.855,7 KB; 8 kontrol ribbon).
- **Dua operasi berbeda:**
  - **Sign**: "Apply a digital signature to this document using a digital ID."
  - **Certify**: "Certify this document with a digital signature to attest to its contents
    and to specify what changes are permitted." →_attestation_ + daftar perubahan yang
    diizinkan.
- **Input → Output:** PDF + Digital ID → PDF bertanda tangan; validasi menghasilkan status
  (`Valid` / `Invalid` / `Unknown` / `Unverified`) dan deskripsi status dokumen
  ("The document has not changed since it was signed...", "Signature is valid, document has
  been changed after it was signed").
- **Perilaku error (sangat informatif untuk rancangan ulang):**
  - "The selected profile is missing its private key and cannot be used to sign this document."
  - "The Digital ID of the selected profile is expired and cannot be used to certify this
    document."
  - "The imported Digital ID '%s' is expired... cannot be used to create Sign or Certify
    profiles."
  - "The document is locked by another application or user and cannot be overwritten. Please
    use Save As to create a new PDF file." → **tidak menimpa input**; memaksa Save As.
  - "Security settings on this document and/or form do not permit you to apply digital
    signature." → permission PDF diperiksa sebelum attempting.
  - "The document integrity verification could not be completed."
  - "Signature is timestamped but the timestamp could not be verified" → timestamp tidak
    dianggap sah bila validasi TSA gagal.
- **Kebutuhan teknis:** PKCS#7/CMS, digest inkremental, RS/ECDSA, TSA, trust store, dan
  penanganan font/AIR yang benar agar tampilan tanda tangan stabil.
- **Kepastian:** VERIFIED untuk model & pesan; **UNKNOWN** untuk algoritme tanda tangan
  default dan format tanda tangan.

### 4.7 QuickSign — tanda tangan berbasis gambar

- **Modul:** `np_signature_stamp.dll` (2.749,2 KB).
- **Bukti UI:** "Create an image of your signature and have QuickSign apply it to your
  document.", "Stamp a copy of a saved signature onto the page.", "Create, Edit or Delete
  existing signatures."
- **Input → Output:** file gambar (dipotong/dicrop manual) → profil QuickSign → stempel
  tanda tangan pada halaman.
- **Opsi:** wizard pembuatan terkelola (nama, gambar, ikon pratinjau, password profil),
  penerapan ke dokumen, galeri terkelola.
- **Perilaku error:** "The file provided is too small to be used to create a QuickSign
  profile."; "A QuickSign profile with this name already exists."; "An incorrect password was
  provided for this QuickSign profile."; "A problem occurred creating the QuickSign preview
  icon."; "Unable to save changes, the QuickSign profile is in use by another application.";
  "The document selected exceeds the maximum file size limit of {} MB."
- **Kebutuhan teknis:** ini **bukan** tanda tangan kriptografis; hanya gambar (stempel).
  Penyimpanan profil (dengan password) + penempatan stempel pada halaman.
- **Kepastian:** VERIFIED.

### 4.8 Nitro Sign — tanda tangan berbasis cloud

- **Modul:** `np_nitro_sign.dll` (4.092,7 KB; 13 kontrol ribbon).
- **Bukti UI:** "The following signature fields are not signed", "The following people have
  digitally counter - signed this document.", "This document was signed by the current
  user / by a trusted contact / by an unknown contact", "Certified with a valid signature".
- **Input → Output:** PDF → permintaan tanda tangan → PDF berisi tanda tangan; mendukung
  pengaman (digital) dan counter-signature.
- **Perilaku error:** "Unable to connect to the Internet. Please check your connection and
  try again."; "Unable to connect to the Internet. You have been automatically logged
  out."; "Invalid email address or password."; "The file you are working with is a secured
  document and not supported."; "The file you are working with is a XFA document and not
  supported."; "An error occured while processing the file"; "Unable to save the file."
- **Batasan model lisensi terdeteksi (diamati, tidak dimanipulasi):** "Your Nitro PDF Pro
  trial has expired. Please upgrade to enable premium features." — fitur premium diikat
  langganan.
- **Kebutuhan teknis:** sinkronisasi status server, template, invitations, status tracking.
- **Kepastian:** VERIFIED untuk alur & pesan; **UNKNOWN** untuk protokol server (tidak
  dianalisis, dan tidak boleh dianalisis lebih jauh tanpa otorisasi).

### 4.9 Formulir — isi, desain, validasi

- **Modul:** `np_forms.dll` (7.827,2 KB; 79 kontrol ribbon; 615 string unik — modul fitur
  terbesar).
- **Bukti UI:** tipe field (teks, checkbox, radio, combo, list, barcode, signature, push
  button), validasi, tab order, calculation order, appearance.
- **Validasi (bukti string):**
  - "The value you entered is invalid." + tombol **"Ignore"** untuk melewati validasi;
  - "The value cannot be left blank." + "Ignore";
  - "One or more required fields are incomplete. Please fill in all required fields before
    submitting the form.";
  - "Value must be greater than 0."; "Please ensure the 'From' value is lower than the 'To'
    value." (validasi rentang);
  - nama field duplikat ditolak;
- **Perilaku error:** "The form cannot be sent. Please check for spaces or syntax errors in
  the recipient email address."; "The form cannot be submitted. Please check for spaces or
  syntax errors in the destination URL."; "Unfortunately loading of our barcode library has
  failed! This document contains a barcode form field and may not function correctly." →
  **graceful degradation** dengan peringatan eksplisit; "The action assigned to this form
  field is not supported."
- **Fitur lanjutan:** `MakeCopies*` (salinan jamak), `VisibleOnScreen` /
  `VisibleWhenPrinted`, `InheritProperties`, `SetAsDefault`, export/import field.
- **Kebutuhan teknis:** AcroForm read/write, appearance stream generator, XFA **tidak**
  didukung (lihat §4.10), JavaScript form Action, calculation order (ekspresi),
  flatten.
- **Kepastian:** VERIFIED.

### 4.10 XFA — desainer berbasis web (di luar `np_*`)

- **Aset:** `xfa/` — 449 berkas, 109,6 MB: `nitro-xfa-server.exe` (146 KB, ProductName
  "NitroXFA"), `web.config`, ASP.NET Core Kestrel + `coreclr.dll`,
  `TallComponents.PDF.Kit.dll` 5.0.198.0, `BouncyCastle.Crypto.dll`, dan SPA
  `main.59c52164156e6d02.js` (4.069,5 KB).
- **Bukti internal:** `xfa_document::save_to_path` (identifier `plugin::call`).
- **Perilaku:** "The file you are working with is a XFA document and not supported." (dari
  `np_nitro_sign.dll`) → jalur XFA ditangani sebagai kasus khusus, bukan sebagai PDF biasa.
- **Implikasi arsitektural:** XFA bukan fitur "form PDF" pada inti MFC, melainkan
  **aplikasi web lokal terpisah** yang dilayani proses sendiri (`nitro-xfa-server.exe`).
  Batas modulnya adalah *desainer* XFA, bukan pembaca PDF umum.
- **Kepastian:** VERIFIED untuk arsitektur; **UNKNOWN** untuk cakupan fungsional XFA.

### 4.11 Operasi halaman

- **Modul:** `np_page_edit.dll` (2.955,2 KB; 56 kontrol ribbon).
- **Bukti UI:** sisip/hapus/putar/potong/ganti/pisah/ekstrak; pesan proses:
  "Moving pages...", "Replacing pages...", "Inserting new pages...", "Extracting pages...",
  "Splitting pages...", "Deleting pages..." → setiap operasi punya status proses tersendiri.
- **Validasi & error:**
  - "Valid page range is required"; "The page range (pxx_pyy)";
  - "The number you have entered is out of range. Document has %d pages.";
  - "The starting page number must be less or the same as the ending page number.";
  - "There is no page number '%d' in the source document.";
  - "Single page documents cannot be split.";
  - "The file \"%s\" is protected. It cannot be used for this command.";
  - "Out of memory.";
  - "The document could not be opened. It has been encrypted using third party software not
    supported by Nitro PDF Pro." → **saya batasan enkripsi pihak ketiga secara eksplisit**.
- **Kebutuhan teknis:** operasi halaman harus menangani: reflow content stream, kloning
  resource bersama antar-halaman, dan penyegaran thumbnail.
- **Kepastian:** VERIFIED.

### 4.12 Edit teks & gambar yang sudah ada

- **Modul:** `np_annotations.dll` (memiliki kontrol `TextEditing`, `TypeText`, `Typewriter`,
  `TypeTextAlignmentTool`, `Fontname`, `FontSize`, `FontColor`, `FontCase`, `FontSpacing`,
  `FontRestriction`, `Justify`) dan `np_objects.dll` (91 kontrol ribbon: operasi gambar).
- **Bukti UI:** "This font is not embedded in the file or installed on your computer. Editing
  with it is not possible."; "This font is embedded in the file but not installed on your
  computer. Characters may not display properly if the font was subset."; "The license for
  this font does not allow you to embed it in your file."
- **Implikasi teknis:** edit teks asli bukan sekadar "ganti string". Ia menuntut:
  parsing content stream, pemetaan glyph→unicode via `ToUnicode`/encoding font, penanganan
  font subset, serta penataan ulang posisi agar reflow tidak merusak tata letak.
- **Perbedaan penting (jaga agar tidak disamakan):**
  | Operasi | Sifat | Keterbatasan |
  |---|---|---|
  | Tambah teks (overlay) | selalu memungkinkan | teks asli tetap ada di bawah |
  | Edit teks asli | sulit | bergantung font tertanam & encoding |
  | OCR searchable | lapisan teks baru | teks hasil OCR boleh tidak identik |
  | OCR editable | rekonstruksi | mutu bergantung segmentasi |
- **Kepastian:** VERIFIED untuk keberadaan fitur & batasan font; **UNKNOWN** untuk mutu
  reflow (tidak ada uji dokumen).

### 4.13 Anotasi & komentar

- **Modul:** `np_annotations.dll` (6.164,2 KB; 146 kontrol ribbon — kontributor toolbar
  kontekstual terbesar).
- **Bukti UI:** 15+ alat (highlight, coret, garis bawah, note, text box + panah, garis,
  panah, kotak, oval, polyline, ink, hapus ink), pop-up note terhubung di setiap alat gambar,
  properties (warna, opasitas, ketebalan, gaya, leader), sembunyikan semua markup,
  impor/ekspor komentar, dan `SummarizeComments`.
- **Perilaku error:** "The number must be between 1 and 1638."; "Error in measure creation.";
  "Error occurred during calibration."; "The precision with given values cannot be achieved.";
  font anotasi hilang → permintaan penggantian font.
- **Kebutuhan teknis:** objek anotasi PDF (subtype Highlight/Text/Line/Square/Circle/
  Polygon/FreeText/Ink), **appearance stream** untuk tiap anotasi, pop-up note dengan
  reply/resolve, dan `IRT` pada text markup.
- **Kepastian:** VERIFIED.

### 4.14 Perbandingan dokumen

- **Modul:** `np_compare_pdf.dll` (2.582,7 KB; 6 kontrol ribbon).
- **Bukti UI:** "Compare two PDF documents pixel by pixel and highlight the detected
  differences."; "Identify changes and differences between two versions of a document.";
  "This page is unable to be compared with the active document."; "The selected document has
  no pages, it cannot be compared."; "The '%s' is a PDF Portfolio document. These types of
  documents cannot be compared."; "An error occured when comparing documents. Please check
  the documents being used."
- **Keterbatasan eksplisit:** dokumen portfolio tidak dapat dibandingkan; halaman
  individual bisa tidak dapat dibandingkan; dokumen berpassword harus dibuka dulu
  ("The password entered was incorrect.").
- **Kebutuhan teknis:** render kedua dokumen → perbandingan piksel (atau tekstual) →
  laporan perbedaan; ini **fitur mahal** (dua render penuh per pasangan).
- **Kepastian:** VERIFIED untuk perilaku; **UNKNOWN** untuk algoritma & ambang sensitivitas.

### 4.15 Konversi keluar (PDF → format lain)

- **Modul:** `np_convert_pdf.dll` (3.292,2 KB; 23 kontrol ribbon; 445 string unik).
- **Target:** Word, Excel, PowerPoint, Rich Text, plain text, gambar (BMP/JPEG/PNG/TIFF),
  plus ekstraksi gambar/tabel/form.
- **Bukti UI & opsi:** "Intelligently decides how to place and anchor images based on content
  layout."; "Convert in-line images only" + penjelasannya ("images that have been placed
  between words and on the same baseline"); "Excel 2003 XML Spreadsheet (.xml)" → dukungan
  beberapa format keluaran.
- **Kebutuhan & batasan (eksplisit di string):**
  - "Microsoft Office Document Imaging (MODI) is required to use this feature." → konversi
    Office **bergantung** komponen Microsoft Office (bukan mandiri);
  - "Conversion to image has failed because the page exceeds the maximum allowed size.";
  - "Conversion to Excel has failed since the selected PDF file does not contain any tables.";
  - "Extract Images has failed since the selected PDF file does not contain any images.";
  - "File conversion has failed due to an invalid password.", "due to invalid content that
    could not be read.", "The selected output file is already opened in another application
    and cannot be overwritten.", "Permission denied", "File Locked".
- **Kebutuhan teknis:** parser tabel + heuristik baris/kolom, penempatan gambar berbasis
  layout, batas ukuran halaman saat raster, dan penanganan file keluaran terkunci.
- **Kepastian:** VERIFIED untuk target, opsi, dan pesan; **UNKNOWN** untuk mutu rekonstruksi
  tabel/gambar.

### 4.16 Pembuatan PDF (Office, HTML, gambar, gabungan)

- **Modul:** `np_create_pdf.dll` (2.695,2 KB) + `html_to_pdf.exe` + add-in
  Office/Outlook/Excel (`ProExcelAddinPDFCreated`).
- **Bukti UI:** "Use the Create PDF Files dialog to quickly convert Microsoft Office,
  WordPerfect, HTML, text, and images into PDF."; "Use the Combine Files dialog to convert
  and combine a collection of different files into the one polished PDF document.";
  opsi bookmark: "Preserve bookmarks in all files" / "One bookmark to every file" /
  "No bookmarks".
- **Perilaku error:** "Your Nitro PDF Pro Office add-in is disabled or installed incorrectly.";
  "Your Nitro PDF Pro Outlook add-in is disabled or installed incorrectly."; "An error was
  encountered when merging the selected PDF file."; "There was a problem converting one or
  more of the selected source files to PDF."; "\"<FILE>\" failed while being created as PDF.
  Would you like to continue ?" → **per-file failure dengan opsi lanjutkan**;
  "The selected output PDF file is already open in another application and cannot be
  overwritten."
- **Kebutuhan teknis:** konversi Office **bergantung pada Office/WordPerfect** (add-in),
  HTML→PDF memerlukan `html_to_pdf.exe`, PDF→PDF perlu operator konversi yang tersedia.
- **Kepastian:** VERIFIED untuk cakupan & ketergantungan; **UNKNOWN** untuk kualitas tata
  letak hasil konversi.

### 4.17 Scan ke PDF

- **Modul:** `np_scan2pdf.dll` (1.839,2 KB; 11 kontrol ribbon) + `x86/Eztwain4.dll`
  (1.008,7 KB) + `x86/Nitro_Scan2PDFApp.exe`.
- **Bukti UI:** "Turn paper into digital documents that you can archive, annotate, and
  share."; "Select your scan settings and save them to a profile so that they can be reused
  at a later time."; kontrol `SingleScan`, `CreateScanProfile`, `ManageScanProfiles`.
- **Perilaku error:** "Please select a scanning device."; "The image could not be acquired
  from the selected scanner."; "The image transfer from the scanner has failed."; "The
  scanned image is invalid and cannot be opened."; "Preset scan profile can't be deleted. It
  will be reset to default state."; "The name of a Preset Profile cannot be used/changed.";
  "File does not exist. Please modify Destination parameter in this profile."
- **Kebutuhan teknis:** akuisisi TWAIN (atau WIA), profil scan, penanganan warna/
  grayscale/bitmap, dan membersihkan file temporer.
- **Kepastian:** VERIFIED untuk alur; **NOT_MEASURED** untuk kecepatan & kualitas.

### 4.18 Watermark, header/footer & nomor halaman

- **Modul:** `np_watermarks.dll` (2.583,2 KB; 16 kontrol ribbon; 474 string unik).
- **Bukti UI:** "Add text- and image-based headers and footers across multiple pages and
  documents using custom profiles."; "Add text- and image-based watermarks to multiple pages
  and documents using profiles with custom opacity and layering options."
- **Opsi:** cakupan halaman (all/odd/even/first/last), profil, opasitas, layering, penempatan
  ("Fit page", "On all pages"), preset "Total pages"/"Batch Total pages"/"Bates Total pages".
- **Perilaku error:** "This profile can only work in documents with even pages."; "This
  profile can only work in documents of '%d' pages or more."; "Please define text for
  Header/Footer or Watermark"; "Please define Watermark name."; "This feature has been
  disabled due to the required screen size needed for this." → **fitur dinonaktifkan otomatis
  bila layar kecil** (mengindikasikan perhatian pada layout di layar kecil).
- **Kebutuhan teknis:** watermark adalah overlay per-halaman → harus menghormati crop box,
  rotasi, dan bleed; header/footer butuh posisi relatif terhadap media box.
- **Kepastian:** VERIFIED.

### 4.19 Stempel & penomoran Bates

- **Modul:** `np_stamper.dll` (2.414,2 KB; 14 kontrol ribbon).
- **Bukti UI:** "Add a stamp to indicate the status of this document."; "Insert a sequential
  number or code onto each page of this document."; "To start, use the Prefix, Suffix, and
  Start at boxes to design your Bates numbering scheme."; "Files for Bates numbering";
  "Apply Bates numbers.." (status proses).
- **Opsi & error:** "Please specify the title for the stamp profile."; "Please select image
  or file for the stamp appearance."; "Bates text has not been defined. Please revise the
  Bates numbering settings."; "Page range must contain all desired pages at once."; "An error
  occurred while applying the stamp."; "Are you sure you want to delete this stamp?".
- **Kebutuhan teknis:** penomoran berurutan lintas dokumen → membutuhkan state "nomor
  terakhir" per batch; profil stempel harus bisa disimpan/dihapus.
- **Kepastian:** VERIFIED.

### 4.20 Aksesibilitas (auto-tagging)

- **Modul:** `np_accessibility.dll` (2.438,2 KB; 466 string unik; kontrol `CreateTags`,
  `Tagging`, `TagProperties`, `Artifacts`).
- **Alur:** "Analyzing document structure" → "Adding tags to document..." → tags dapat
  disunting manual (root/parent/child/sibling).
- **Perilaku error:** "Nitro PDF Pro is not able to auto-tag this document. If the problem
  persists, please contact support."; "...The password for the document was incorrect." →
  kegagalan auto-tag **tidak menggagalkan seluruh operasi**, disertai fallback tagging manual;
  "Document is already tagged. Are you sure you want to overwrite the existing tags?"; "There
  was an error while reloading the document structure."; "No tags available in this document
  to view."; "The ID is not associated with any table cell in this document."
- **Kebutuhan teknis:** inferensi struktur (heading, paragraf, tabel, list) dari layout —
  pekerjaan sejenis dengan OCR reading-order; membuat tag tree yang valid; embedding font.
- **Kepastian:** VERIFIED untuk alur & pesan; **UNKNOWN** untuk mutu inferensi struktur.

### 4.21 Lampiran & portfolio

- **Modul:** `np_attachments.dll` (2.779,2 KB; 7 kontrol ribbon).
- **Bukti UI:** "Add a file as an attachment to this document."; "View, add, and delete files
  attached to this document."; panel lampiran di sisi kiri bawah; "Only PDF attachments can
  be printed!".
- **Perilaku error:** "Portfolio PDF creation has failed."; "Extraction of portfolio file
  failed."; "Cannot open file \"%s\"."; "This document is secured and requires a correct
  password or private key to be printed."; "One or more of the files you are loading have
  been modified and must be saved before they can be processed."
- **Keamanan:** `np_actions.dll` memblokir lampiran executable ("The file %s is being blocked
  from launching as it is an executable file format.") dan memberi peringatan file berbahaya
  ("This file cannot be opened by Nitro PDF Pro because it may be harmful to your computer.
  If you trust this file, you can save it from the Attachments panel.") → **referensi
  implementasi *execution gating* untuk attachment**.
- **Kepastian:** VERIFIED.

### 4.22 Bookmark & navigasi

- **Modul:** `np_bookmarks.dll` (1.927,7 KB; 9 kontrol ribbon).
- **Bukti UI:** "Add and edit bookmarks to improve the navigation of this document.";
  "Automatically build a set of bookmarks based on headers and styles used in this document.";
  proses "Building page %d of %d..." → **auto-bookmark melaporkan progres per halaman**.
- **Opsi auto-bookmark:** "To start, click the Level 1 button, and then with your pointer
  select an example of the text in your document that you want to become a bookmark." +
  "Use the options below to control precisely what text becomes a bookmark."
- **Perilaku error:** "All bookmark levels will be replaced. Continue?"; "Bookmark cannot be
  deleted. Finish renaming your bookmark before deleting it."; "The action assigned to this
  bookmark is not supported."; "An unknown error occurred - PDDocGetBookmarkRoot - while
  reloading the bookmark tree in the Bookmarks Pane."
- **Kepastian:** VERIFIED.

### 4.23 Pembuatan link otomatis

- **Modul:** `np_links.dll` (2.012,2 KB; 38 kontrol ribbon).
- **Tiga varian:** (1) link manual antar halaman/berkas/URL; (2) "Scan this document and
  automatically add a link to each instance of a specified keyword or phrase."; (3) "Scan
  this document and add a link to any text recognized as a URL." + auto page-link dari
  penomoran TOC.
- **Perilaku & status:** "Generating links... (page %d)"; "Creating weblinks… (Page %d)";
  "%d weblinks were added to this document."; "Your keyword or phrase was not found in the
  document. No links were created." → **laporan jumlah hasil**, termasuk 0.
- **Perilaku error:** "The action assigned to this link is not supported."
- **Kebutuhan teknis:** regex URL + konteks; penyesuaian rectangle agar tidak menimpa
  teks; progres per halaman.
- **Kepastian:** VERIFIED.

### 4.24 Optimasi ukuran berkas

- **Modul:** `np_optimizer.dll` (1.725,7 KB; 1 kontrol ribbon, 337 string unik).
- **Bukti UI:** "Reduce the size of this document by compressing images and removing
  objects."; "Result of file optimization"; "Compare the original and reduced file size."
- **Granularitas penghapusan (terbukti dari pesan galat):** attachments, thumbnails, named
  destinations, form widgets, annotations, bookmarks, JavaScript — masing-masing punya
  pesan "An error occurred while removing X." → **penghapusan selektif dengan pelaporan
  per-kategori**.
- **Perilaku error:** "This document must be saved before it can be optimized. Would you
  like to save this PDF and continue?"; "The optimized file could not be created in the
  selected location."; "The document does not have the required security permissions for
  this operation."; "The DPI setting must be a value between %d and %d."; "An error occured
  while un-embedding fonts."; "An error occurred during the creation of the optimized file's
  name and path."
- **Kebutuhan teknis:** re-encode gambar (DPI/JPEG), subset/lepas font, buang objek tak
  terpakai — **harus tradeoff antara ukuran dan fidelity**, dan perlu melaporkan ukuran
  sebelum/sesudah.
- **Kepastian:** VERIFIED untuk opsi & pesan; **NOT_MEASURED** untuk rasio pengurangan.

### 4.25 Cloud storage, SharePoint & WebDAV

- **Modul:** `np_cloud_storage.dll` (4.528,2 KB) dan `np_web_dav.dll` (1.646,7 KB).
- **Model SharePoint:** simpan sebagai situs terdaftar (label + URL), kontrol versi
  ("Publish a new major version of the file. This SharePoint site does not allow minor
  versions."), auth per-kontak, pick folder (`sharepoint_picker::*`),
  `ms_graph_authenticator.exe` (40 KB) untuk autentikasi Microsoft Graph.
- **Model WebDAV:** dokumen remote bisa **read-only** bila lokasi tidak mendukung locking /
  exclusive write lock → status dokumen dipengaruhi kapabilitas server.
- **Perilaku error:** "The file you are trying to update is checked out or locked by another
  SharePoint user."; "This location is not DAV compliant, this document is read-only.";
  "This document is locked by another user, unable to save the document."; "Failed to
  connect to the site '{}'."; "You do not have access to the URL provided."
- **Pola API terdeteksi dari kode:** 400 invalid argument, 403 permission denied, 404 object
  not found, 405 not supported → **lapisan_error_layanan_terpisah** dari error internal.
- **Kebutuhan teknis:** OAuth/device-code flow, cache kredensial, penanganan check-out,
  dan degradasi aman ke read-only.
- **Kepastian:** VERIFIED untuk alur & pesan; **UNKNOWN** untuk detail protokol.

---

## 5. Batasan analisis & pertanyaan terbuka

### 5.1 Metode yang tidak dijalankan

| Metode (urutan master prompt) | Status | Alasan / dampak |
|---|---|---|
| 1. Dokumentasi publik | **dijalankan sebagian** | hanya inventaris lokal + metadata produk; dokumentasi daring tidak diambil pada sesi ini |
| 2. Pengamatan UI langsung | **NOT_RUN** | instalasi referensi tidak dijalankan; seluruh bukti UI berasal dari string `.mui` dan identifier ribbon |
| 3. Uji input-output dengan dokumen sintetis | **NOT_RUN** | tidak ada dokumen sintetis yang dibuat pada sesi ini |
| 4. Inspeksi teknis terarah | **dijalankan** | REA MCP pada `np_pdfa.dll`, `nitro_module_loader.exe`, `np_ocr.dll` (resource), + ekstraksi korporas 36 `.mui` |

**Dampak:** bukti "perilaku" pada dokumen ini adalah *bukti statis* (teks UI, identifier,
simbol). Tidak ada klaim tentang hasil aktual sebuah operasi pada file PDF nyata. Semua
klaim yang bergantung pada isi dokumen nyata ditandai **UNKNOWN** atau **NOT_MEASURED**.

### 5.2 Status pertanyaan terbuka

| ID | Pertanyaan | Status setelah analisis ini |
|---|---|---|
| U-01 | Apakah MuPDF (atau mesin lain) dapat merekonstruksi teks yang bisa diedit dari PDF hasil OCR dengan mutu memadai? | **TERBUKA** — tidak ada uji dokumen; teks UI menunjukkan mode "Searchable **and Editable**" memang ada, sehingga topik ini penting |
| U-02 | Berapa biaya lisensi mesin PDF IRIS/DRS & Ghostscript (GPL) untuk distribusi UnionPDF? | **TERBUKA** — GPL Ghostscript menimbulkan kewajiban distribusi; lisensi IRIS tidak dapat diverifikasi tanpa keterangan lisensi resmi |
| U-03 | Apa risiko lisensi XFA/PDFKit.NET/SOLIDWORKS bila tidak disalin? | **TERBUKA** — dependency pihak ketiga tidak akan diambil; tetap perlu dicatat |
| U-04 | Performa pada dokumen >5.000 halaman | **NOT_MEASURED** |
| U-05 | Mutu konversi Office→PDF | **NOT_MEASURED**; bukti menunjukkan ketergantungan pada Office/WordPerfect |
| U-06 | Pustaka tanda tangan digital yang mandiri & berlisensi jelas | **TERBUKA** — referensi memakai engine miliknya sendiri + TSA eksternal |
| U-07 | Pintasan keyboard lengkap | **TERBUKA** — ekstraksi regex hanya menghasilkan 15 kecocokan, mayoritas false positive ("control bar", "shift to"); perlu sumber otoritatif lain |
| U-08 | Modul mana yang memiliki renderer | **TERBUKA** — `npdf.dll`/`idrspdf15.dll` terlalu besar untuk Ghidra dalam sesi ini |
| U-09 | Detail parameter enkripsi (V/R, key length) | **TERBUKA** |
| U-10 | Daftar bahasa OCR | **TERBUKA** — 20 model + `autolang` + `nop` teridentifikasi dari berkas, tetapi **nama paket/bahasa per file belum diverifikasi** |
| U-11 | pipa konversi internal (Word/Excel) | **TERBUKA** — ada `MSHTMLApi.dll`, `ExcelApi.dll`, `html_to_pdf.exe`, add-in Office; mekanismenya belum jelas |
| U-12 | Batas maksimum ukuran dokumen | **TERBUKA** — satu indikasi: "The document selected exceeds the maximum file size limit of {} MB" (QuickSign) |

### 5.3 Cakupan bukti

- **Kuat** (level simbol, VERIFIED): arsitektur plugin, model proses, kontrak perintah,
  ada/tidaknya fitur, algoritma enkripsi yang ditawarkan, pemisahan redaksi/whiteout/mask,
  hierarki UI (tab/grup/toolbar), daftar bahasa OCR, ketergantungan add-in Office.
- **Sedang** (teks UI tanpa alur): perilaku dialog, nilai default, urutan langkah,
  copywriting pesan error.
- **Lemah / belum ada**: mutu keluaran, performa, kompatibilitas file, dan perilaku pada
  dokumen rusak/terkunci/berpassword. Semua **NOT_MEASURED**.

---

## 6. Lampiran

### 6.1 Indeks bukti REA (A-001 …)

| ID | Operasi | Target | Hasil kunci | Evidence ID REA |
|---|---|---|---|---|
| A-001 | `open_binary` | `np_pdfa.dll` | PE x86_64, SHA-256 `66949294…` | — |
| A-002 | `binary_overview` | `np_pdfa.dll` | 1.852 prosedur, 1.165 string, 8 segment, base `0x180000000`, Ghidra 12.1.4 | `ev_0433690df3977287f066bec285975150463f25313ff133f782bda12b5463dcc5` |
| A-003 | `list_procedures` | `np_pdfa.dll` | simbol `nitro::pdfa::pdfa_converter::*` | — |
| A-004 | `search_strings("pdfa")` | `np_pdfa.dll` | 27 hit, antara lain `AVCmdHandlerConvertToPDFA_WorkProc`, `pdfa_plugin::init`, `"Unexpected result value for pdfa_converter::preflight_result: "` | `ev_7de703563502cc1667c7add9d0b22b1c70a2c4d31e59af2b1120f2b206ab56c2` |
| A-005 | `procedure_pseudo_code` | `nitro::pdfa::pdfa_converter::preflight_to_convert_to_pdfa` | tidak mengembalikan body (simbol eksternal `NPDF.DLL`) | `ev_de42111b15401c991662270a2f712358135304c002c41eba9c97955898cf0fc2` |
| A-006 | `procedure_pseudo_code` | `nitro::pdfa::create_plugin` @ `0x180031bb0` | pseudocode 531 char: badan fungsi hanya berisi satu panggilan ke `FUN_1800398d0` | `ev_b23a838f1f4002fd8a766a5dae4fa4f0922ace77abdb4e179d7ce89e5622a933` |
| A-007 | `open_binary` + `binary_overview` | `nitro_module_loader.exe` | 263 prosedur, 168 string; SHA-256 `ce8f5908…` | — |
| A-008 | `search_strings("np_")` | `nitro_module_loader.exe` | satu-satunya hit: `np_*.dll` | — |
| A-009 | `search_strings(".dll")` | `nitro_module_loader.exe` | `np_*.dll` + MSVCP140/VCRUNTIME140/api-ms-win-crt-* | — |
| A-010 | `inspect_pe_resources` | `np_ocr.dll` | PE32+, machine 34404 (AMD64), 62 resource, 10 icon group, 11 PNG, named resource `MUI` | `ev_56634a8213a4f03bac80224cbdff9aa2a54b3f7f35ee00e548d9410f0cf78c23` |
| A-011 | `close_binary` (snapshot) | kedua target | snapshot 118.135 byte, 6 evidence record | — |
| A-012 | `list_procedures` (eksternal) | `nitro_module_loader.exe` | import Win32: `LoadLibraryW`, `SetDllDirectoryW`, `FindFirstFileW/FindNextFileW`, `CreateEventW/OpenEventW/WaitForSingleObject`, `TerminateProcess` | — |

Korporas turunan (lokal, tidak dipublikasikan): `docs/research/mui_strings_en-US.json`,
`ribbon_controls_v14.json`, `native_feature_ids_v14.json`,
`ocr_languages_and_shortcuts_v14.json`, `V14_RIBBON_STRUCTURE.md`, `V14_UI_EVIDENCE.md`.

### 6.2 Toolbar kontekstual bernama fitur (80 dari 228 grup)

```
About  AddImage  AddNote  Alignment  Artifacts  AttachFiles  AutoDeskewDoc
BatchProcessing  BatesNumbering  Bookmark  CenterBoth  Combine  ContentComparePDF
ContextAligment  ContextAppearance  CreateNewSignature  CreateNewStamp
CreateScanProfile  CreateTags  EditAllFields  Exit  ExtractImages  FitPage  FitWidth
HideComments  InheritProperties  LeaderExtension  LeaderLength  LeaderOffset
LinkAlignment  MakeCopies  MakeCopiesEveryPage  MakeCopiesSameName
MakeCopiesSpacing  ManageScanProfiles  ManageSignatures  ManageStamps  Migrate
PDF-A-1b_Btn  PDF-A-2b_Btn  PDF-A-3b_Btn  RemoveAppearance  RemoveBatesNumbering
RenameAppearance  SaveAsFlatten  SaveNewAppearance  SetAsDefault  SetCalculationOrder
SetTabOrder  SingleScan  SizeBoth  SizeHeight  SizeWidth  Spacing  StampSignature
SummarizeComments  SupportTools  TagProperties  Tagging  Tasks  TextEditing  TextField
Thickness  ToImage  ToPPTX  ToPlainText  ToRichText  ToolsFP  TrustedContacts  TypeText
TypeTextAlignmentTool  Typewriter  UpdateAppearance  UserGuide  VisibleOnScreen
VisibleWhenPrinted  VolumeLicensing  Watermark  WidthEdit  ZoomTool
```

Sisa 148 grup: 12 placeholder `Dummy*Separator*`, 1 format-string `%s`, dan 135 token
generik BCGSoft (`Btn`, `Empty`, `Sep`, `General`, `More`, `Size`, `Style`, `Panel`, …).

### 6.3 Daftar 36 berkas `.mui` (locale `en-US`)

| Berkas | String | Berkas | String |
|---|---:|---|---:|
| `NitroPDF.exe.mui` | 1.343 | `np_cloud_storage.dll.mui` | 391 |
| `np_annotations.dll.mui` | 751 | `np_commands.dll.mui` | 380 |
| `np_set_security.dll.mui` | 720 | `np_stamper.dll.mui` | 380 |
| `np_forms.dll.mui` | 673 | `np_create_pdf.dll.mui` | 369 |
| `np_page_edit.dll.mui` | 521 | `np_nitro_sign.dll.mui` | 368 |
| `np_watermarks.dll.mui` | 494 | `np_redaction.dll.mui` | 365 |
| `np_accessibility.dll.mui` | 478 | `np_scan2pdf.dll.mui` | 365 |
| `np_objects.dll.mui` | 477 | `np_attachments.dll.mui` | 355 |
| `np_ocr.dll.mui` | 472 | `np_compare_pdf.dll.mui` | 353 |
| `np_convert_pdf.dll.mui` | 454 | `np_actions.dll.mui` | 350 |
| `np_links.dll.mui` | 450 | `np_java_script_deprecated.dll.mui` | 347 |
| `np_digital_signature.dll.mui` | 429 | `np_javascript.dll.mui` | 347 |
| `np_bookmarks.dll.mui` | 397 | `np_optimizer.dll.mui` | 346 |
| `np_signature_stamp.dll.mui` | 334 | `np_smart_tips.dll.mui` | 330 |
| `np_layers.dll.mui` | 321 | `np_web_dav.dll.mui` | 317 |
| `ControlActivation.exe.mui` | 319 | `NitroPDFPreviewHandler.dll.mui` | 309 |
| `NitroPDFSupportTools.exe.mui` | 66 | `np_pdfa.dll.mui` | 33 |
| `NxPdfCreator.exe.mui` | 29 | `Nitro.Pro.ShellExtension.dll.mui` | 19 |

### 6.4 Skrip yang dipakai

| Skrip | Fungsi | Keluaran |
|---|---|---|
| `scripts/extract_mui_strings.py` | parse resource `RT_STRING` dari `.mui` | `docs/research/mui_strings_en-US.json` |
| `scripts/extract_native_strings.py` | ekstraksi string ASCII + UTF-16 dari `np_*.dll` + exe | `ribbon_controls_v14.json`, `native_feature_ids_v14.json` |
| `scripts/extract_shortcuts_and_ocr_lang.py` | inventaris bahasa OCR & pintasan | `ocr_languages_and_shortcuts_v14.json` |
| `scripts/build_ribbon_map.py` | rekonstruksi hierarki tab/grup ribbon | `V14_RIBBON_STRUCTURE.md` |
| `scripts/analyze_ui_evidence.py` | laporan label & pesan error per modul | `V14_UI_EVIDENCE.md` |
| `scripts/verify_analysis_corpus.py` | **verifikasi angka dokumen ini** | stdout + exit code |

### 6.5 Model bahasa OCR

`autolang`, `latin`, `cyrillic`, `greek`, `hebrew`, `handpr`, `ocra1`, `ocrb1`, `brt`, `brz`,
`dan`, `dut`, `eng`, `fin`, `frn`, `grm`, `itl`, `nrw`, `prt`, `spn`, `swd` → **20 model**
(`autolang` = deteksi otomatis, `nop` = no-op). Berkas pendukung: `fontmetrics.bin`,
`latin_1_engine.bin`, `net_latin_1.bin`.

---

**Catatan akhir.** Dokumen ini sepenuhnya diturunkan dari artefak read-only yang terpasang
di `C:\Program Files\Nitro\PDF Pro\14` dan dari 12 operasi REA MCP yang tercatat di §6.1.
Tidak ada fitur aplikasi referensi yang dijalankan, dibuka, atau dimanipulasi; tidak ada
lisensi yang dipalsukan; tidak ada aset proprietary yang disalin ke UnionPDF. Verifikasi
silang: `scripts/verify_analysis_corpus.py`.
