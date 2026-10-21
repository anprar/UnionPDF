# Analisis REA — PDFgear 3.0.0 (Windows x86_64)

**Status:** v1 — analisis referensi, read-only
**Tanggal analisis:** 2026-10-21
**Target:** `C:\Program Files\PDFgear` (instalasi aktif, 349 berkas / 369,2 MB)
**Installer:** `<USERPROFILE>\Downloads\pdfgear_setup_v3.0.0.exe` (138.834.216 byte)
**Metode:** REA MCP — `inspect_managed_artifact` (metadata .NET) + `inspect_pe_resources` +
Ghidra 12.1.4 pada modul native kecil + parsing resource tertanam
**Dokumen sekeluarga:** `docs/ANALYSIS_NITRO14.md` · `docs/ANALYSIS_STIRLING_PDF.md`

> **Catatan redaksi (2026-10-21, sesi `2026-10-21T1114+0700`).** `<USERPROFILE>` =
> folder profil pengguna Windows pada mesin analisis (`C:\Users\<nama-profil>`); nama
> profil disamarkan. Versi, ukuran, hash artefak, dan bukti teknis tidak diubah.

> **Cakupan.** Analisis statis atas artefak yang terpasang di mesin ini. Aplikasi **tidak
> pernah dijalankan**; tidak ada berkas uji yang diproses; tidak ada panggilan jaringan.
> Semua pernyataan tentang perilaku bersifat inferensi dari metadata, resource, dan teks
> yang tertanam.

> **Hubungan dengan laporan sebelumnya.** Berkas
> `<USERPROFILE>\Downloads\laporan-rea-pdfgear-v3.0.0.md` (analisis di lingkungan Linux)
> berhenti pada level *installer*: payload Inno Setup 6.7 tidak bisa diekstrak, sehingga
> komponen aplikasi belum bisa diklaim. **Folder instalasi yang Anda kirimkan menghapus
> hambatan itu** — dokumen ini menganalisis isi aplikasi yang sebenarnya. SHA-256
> installer yang dianalisis di sana **identik** dengan yang ada di `Downloads`
> (`633a1a1f…`), jadi keduanya satu artefak yang sama.

---

## 0. Ringkasan eksekutif

PDFgear 3.0.0 adalah aplikasi **.NET Framework 4.6.2 / WPF** yang rakas secara industriel:
bukan satu engine, melainkan **4 pustaka PDF komersial**, **2 engine OCR**, **1 pustaka
Office**, plus lapisan web (WebView2), helper proses terpisah, dan AI assistant dengan
katalog aksi 27 perintah.

Sembilan temuan utama:

1. **Inti aplikasi = CIL/.NET Framework 4.6.2 (WPF), x86_64.** Bukti REA
   `inspect_managed_artifact`: `runtime_family: dotnet-framework`, `implementation: cil`,
   `TargetFrameworkAttribute = .NETFramework,Version=v4.6.2`, MVID
   `c8de2d6d-a2d3-44c1-9b4c-d3270cf625d2`, 49 referensi assembly, 7.828 atribut
   (VERIFIED, level metadata).
2. **Empat pustaka PDF dipakai bersamaan.** `pdfium.dll` (Pdfium.Net SDK 4.34.40.2704,
   12,7 MB), `Patagames.Pdf.dll` (Pdf .NET SDK 9.68.38.462), `SautinSoft.PdfFocus.dll`
   (PDF Focus .Net 7.8.1.29, 6,5 MB), `Syncfusion.Pdf.Base.dll` (19.3460.0.57, 7,0 MB).
   Empat lisensi komersial berbeda dalam satu binary (VERIFIED).
3. **Dua engine OCR, keduanya ter-bundel.** Tesseract 4.1.1 (wrapper `Tesseract.dll` di root +
   native `x64/tesseract41.dll` + `leptonica-1.80.0.dll`, `tessdata` 63 berkas / 38,7 MB) dan
   **NsOCR** (Nettopsoft: `NSOCR.dll`, `NsImgLdr.dll`, `asian.dll`, `NsSpell.dll`,
   `NsBars.dll`) — 54 berkas / **227,5 MB**. Berbeda dari Stirling yang memakai Tesseract
   *eksternal* (VERIFIED).
4. **Ada AI assistant dengan katalog aksi 27 perintah.** Resource tertanam
   `pdfeditor.Utils.Copilot.actions.json` (971.922 byte) berisi 27 aksi: `summary`,
   `print`, `select-page`, `page-display`, `page-zoom`, `rotate-page`, `auto-scroll`,
   `slide-show`, `set-background`, `add-annotation`, `show-annotation`, `edit-text`,
   `extract-page`, `delete-page`, `insert-page`, `crop-page`, `convert-from-pdf`,
   `convert-to-pdf`, `compress`, `protect-pdf`, `remove-password`, `contact-us`,
   `settings`, `check-update`, `about`, `close-pdf`, `find-in-pdf` (VERIFIED).
5. **Setiap aksi destruktif meminta konfirmasi dalam 11 bahasa** (en, de, es, fr, it, ja,
   ko, nl, pt, ru, zh-CN) dengan templat `{$mode}` untuk parameter — pola konfirmasi
   multibahasa yang bisa langsung diadopsi (VERIFIED).
6. **Model UI berbeda dari dua target sebelumnya:** WPF + HandyControl + WebView2 —
   bukan ribbon MFC (Nitro) dan bukan web app (Stirling).
7. **Telemetri ganda:** Google Analytics 4 (`GA4Manager`, `GA4Manager2`), Google Ads
   (`GAManager`), `AdManager`, dan **Sentry** untuk pelaporan error (VERIFIED dari nama
   tipe).
8. **Fitur dibatasi berlisensi di level UI:** ada `PaidUserVisibilityConverter` —
   visibilitas kontrol ditentukan status berbayar (VERIFIED).
9. **Lima helper proses terpisah:** `PDFLauncher.exe`, `PDFMonitor.exe`, `RegExt.exe`,
   `pdfconverter.exe`, `OpenWithPicker.exe`, plus `conv_helper.dll` (VERIFIED).

### 0.1 Angka kunci

| Metrik | Nilai | Sumber |
|---|---:|---|
| Berkas terpasang | 349 (369,2 MB) | inventaris `C:\Program Files\PDFgear` |
| `PDFgear.exe` | 8.681.096 byte | REA `inspect_managed_artifact` |
| Target framework | `.NETFramework,Version=v4.6.2` | idem |
| Referensi assembly | 49 | idem |
| Atribut metadata | 7.828 | idem |
| Resource tertanam | 4 | idem |
| Resource `Copilot.actions.json` | 971.922 byte → **27 aksi** | idem + parsing |
| String unik `PDFgear.exe` | 82.972 | ekstraksi ASCII + UTF-16 |
| Tipe .NET terpetakan (`pdfeditor.*`) | 64 kontrol · 24 util · 23 model · 16 view · 11 viewmodel | parsing string metadata |
| Pustaka PDF | 4 | inventaris versi |
| Model OCR | 2 engine (Tesseract 4.1.1 + NsOCR) | inventaris versi |
| `tessdata` | 63 berkas / 38,7 MB (16 model) | inventaris |
| `NsOCR/` | 54 berkas / 227,5 MB | inventaris |
| Paket open-source tercatat | 15 | `OpensourceLicense/LICENSE.txt` |
| Prosedur `jnsocr.dll` (Ghidra) | 537 | REA `binary_overview` |
| Prosedur `Twaindsm.dll` (Ghidra) | 510 | idem |
| Resource PE `PDFgear.exe` | 16 entri, 2 icon group | REA `inspect_pe_resources` |
| Bahasa UI | 10 locale satellite + English (bawaan assembly utama) | inventaris direktori |

### 0.2 Posisi terhadap tiga target lain

| Aspek | Nitro 14 | Stirling-PDF 3.2 | **PDFgear 3.0** |
|---|---|---|---|
| Bentuk | Native C++/MFC | Tauri + server Spring Boot | **.NET Framework WPF** |
| UI | Ribbon 13 tab | Web React (84 chunk) | **WPF + HandyControl + WebView2** |
| Engine PDF | IRIS/DRS (1) | PDFBox 3 + PDFium (2) | **Pdfium + Patagames + PDF Focus + Syncfusion (4)** |
| OCR | IRIS internal, 20 model | Tesseract **eksternal** | **Tesseract + NsOCR, keduanya ter-bundel** |
| Konversi Office | add-in MS Office | LibreOffice + `stirling-office-convert` | **Syncfusion (DocIO/XlsIO/Presentation)** |
| AI | tidak ada | tidak ada (temu) | **Copilot, 27 aksi, konfirmasi 11 bahasa** |
| Telemetri | `metrics_tool` + BugSplat | PostHog + WAU tracking | **GA4 + Google Ads + Sentry** |
| Lisensi | komersial proprietary | open-core MIT + paket proprietary | **komersial proprietary, 4 pustaka berlisensi** |
| Basis data | — | H2 + JPA | **SQLite** (Microsoft.Data.Sqlite) |

---

## 1. Metodologi, environment, dan batasan

### 1.1 Environment

| Item | Nilai |
|---|---|
| OS | Windows 11 (x64) |
| Python analisis | `.venv` → 3.13.9 |
| Provider REA | `rea-workflow` (Ghidra 12.1.4) + inspeksi metadata terkelola |
| Target | `C:\Program Files\PDFgear` (instalasi aktif) |
| Installer | `<USERPROFILE>\Downloads\pdfgear_setup_v3.0.0.exe` |
| Snapshot REA | `…\opencode\rea_pdfgear_snapshot.json` (30.211 byte, 2 evidence record) |

### 1.2 Urutan metode

1. **Verifikasi target** — folder instalasi ada (349 berkas) dan installer ada di
   `Downloads`; SHA-256 installer dicocokkan dengan laporan sebelumnya → identik.
2. **REA `inspect_managed_artifact`** pada `PDFgear.exe` → klasifikasi terkelola, identitas
   assembly, 49 referensi, 4 resource tertanam (coverage `complete-within-view`,
   7.881/7.881 item). Diulang pada `CommonLib.dll` (2.030 item), `PDFKit.dll` (2.515),
   `conv_helper.dll` (0 — bukan assembly terkelola).
3. **REA `inspect_pe_resources`** pada `PDFgear.exe` → 16 resource, 2 icon group.
4. **REA pada installer → ditolak**: `resource_constraint` ("Selected artifact exceeds
   67108864 bytes") — batasan input 64 MiB REA. Dicatat, bukan dipaksa.
5. **REA Ghidra pada modul native kecil**: `NsOCR\Bin_64\jnsocr.dll` (537 prosedur) dan
   `Twaindsm.dll` (510 prosedur). Modul besar (`pdfium.dll` 12,7 MB, `tesseract41.dll`
   3,0 MB) tidak dikirim ke Ghidra — batas ~700 KB pada sesi ini.
6. **Ekstraksi resource tertanam** — `pdfeditor.Utils.Copilot.actions.json` (969.092
   karakter JSON valid) ditulis ke temp dan diparse; 27 aksi dengan prompt konfirmasi
   multibahasa.
7. **Inventaris tipe .NET** dari string metadata (nama namespace + kelas) untuk
   `PDFgear.exe`, `CommonLib.dll`, `PDFKit.dll`, `conv_helper.dll`.
8. **Inventaris versi** tiap DLL + `FileVersionInfo` untuk memetakan stack.

### 1.3 Yang tidak dilakukan

- Tidak menjalankan PDFgear, tidak membuka dokumen uji, tidak menjalankan OCR/konversi.
- Tidak mengirim dokumen ke layanan AI apa pun; katalog aksi hanya **dibaca** dari resource.
- Tidak memodifikasi file di `C:\Program Files\PDFgear` maupun installer.
- Tidak mengaktifkan/membayar lisensi, tidak masuk akun, tidak menguji IAP.
- Tidak menyalin resource/kode proprietary ke UnionPDF.

### 1.4 Reproduksi

```powershell
# 1) identitas & metadata terkelola (REA)
#    inspect_managed_artifact  C:\Program Files\PDFgear\PDFgear.exe
# 2) inventaris versi
Get-ChildItem "C:\Program Files\PDFgear" -File | ForEach-Object {
  $_.VersionInfo | Select-Object ProductName, FileVersion, CompanyName }
# 3) katalog aksi Copilot (resource tertanam di dalam PDFgear.exe)
#    -> {"actions": [ ... 27 aksi ... ]}
# 4) checksum anchor
Get-FileHash "C:\Program Files\PDFgear\PDFgear.exe" -Algorithm SHA256
```

---

## 2. Artefak & komposisi

### 2.1 Identitas & tanda tangan

| Item | Nilai |
|---|---|
| Produk | PDFgear **3.0.0** (assembly version 3.0.0.0) |
| Perusahaan | **PDF GEAR TECH PTE. LTD.**, Singapura (SGN 202026788N) |
| Penanda tangan | `SSL.com EV Code Signing Intermediate CA ECC R2` — status **Valid**, berlaku s/d **04/03/2027 17:25:27** |
| SHA-256 `PDFgear.exe` | `6b74060a120115405ca685761ec955f54315dfd6883097dd79d219966aacd891` |
| SHA-256 installer | `633a1a1ff3aef27541e8bd8a472066b8ffc10442ee83729388958604496db69a` |
| Ukuran installer | 138.834.216 byte (132,4 MB) |
| Nama internal proyek | `pdfeditor` (namespace `pdfeditor.*`) — cocok dengan pencatatan pentest v2.x |

### 2.2 Komposisi instalasi

| Area | Isi |
|---|---|
| Root (≈ 90 berkas) | `PDFgear.exe`, `CommonLib.dll`, `PDFKit.dll`, `conv_helper.dll`, 4 pustaka PDF, 12 DLL Syncfusion, `Tesseract.dll`, `BouncyCastle`, `NLog`, `Sentry`, `Newtonsoft.Json`, `HandyControl`, WebView2, `e_sqlite3.dll`, helper `.exe` |
| `x64/` | `tesseract41.dll` (3.013,0 KB), `leptonica-1.80.0.dll` (3.968,0 KB) |
| `tessdata/` | 63 berkas / 38,7 MB; **16 `*.traineddata`** (12 bahasa dasar: chi_sim, chi_tra, deu, eng, fra, ita, jpn, kor, nld, por, rus, spa + varian `_vert`) + `pdf.ttf` (0 byte, placeholder) |
| `NsOCR/` | 54 berkas / **227,5 MB**: `NSOCR.dll` (3.559,4 KB), `NsImgLdr.dll` (5.952,9 KB), `asian\asian.dll` (3.027,0 KB), `NsSpell.dll` (416,4 KB), `NsBars.dll` (209,9 KB), `Twaindsm.dll` (162,7 KB), `jnsocr.dll` (133,5 KB), `Bin_common\*.lng` (BG, CA, CS, …), `ALL_base.dat` (3.718,6 KB) |
| 10 direktori locale | `de, es, fr, it, ja, ko, nl, pt, ru, zh-CN` (Inggris = bahasa bawaan assembly utama, tanpa direktori terpisah) → tiap locale 4 satellite assembly: `CommonLib.resources.dll`, `pdfconverter.resources.dll`, `PDFgear.resources.dll`, `PDFMonitor.resources.dll` |
| `OpensourceLicense/` | `LICENSE.txt` (65,3 KB) — 15 paket |
| `runtimes/win-x64/native/` | `WebView2Loader.dll` |

### 2.3 Resource tertanam `PDFgear.exe` (REA)

| Resource | Ukuran | Isi |
|---|---:|---|
| `PDFgear.g.resources` | 3.995.897 byte | Resource WPF (BAML, gambar, style) |
| `pdfeditor.Properties.Resources.resources` | 121.025 byte | Gambar & string UI |
| **`pdfeditor.Utils.Copilot.actions.json`** | **971.922 byte** | **Katalog 27 aksi AI** |
| `pdfeditor.Utils.DigitalSignatures.ISO-3166-ID-SHORT.json` | 28.670 byte | Kode negara untuk tanda tangan digital |

---

## 3. Arsitektur runtime

### 3.1 Peta lapisan

```
┌─ PDFgear.exe (8,68 MB)  ─ .NET Framework 4.6.2 / WPF / CIL x86_64
│    │  · HandyControl 3.5.1 · CommunityToolkit.Mvvm 8.4 · Syncfusion.Shared.WPF
│    │  · WebView2 1.0.3065.39 (panel web)
│    ├─ PDFKit.dll 1,07 MB   ─ wrapper internal: Konten, Operasi, Util (Encrypt, Stamp, Watermark, DigitalSignatures, PageHeaderFooters, XObjects)
│    ├─ CommonLib.dll 996 KB — bersama: Akun, IAP, GA4/GAM, AdManager, History, Update, OcrUtils, HotKeys
│    ├─ pdfconverter.exe + conv_helper.dll ─ konversi terpisah (proses sendiri)
│    ├─ 4 pustaka PDF: pdfium · Patagames.Pdf · SautinSoft.PdfFocus · Syncfusion.Pdf
│    ├─ OCR: Tesseract 4.1.1 (x64/) + NsOCR (jnsocr/NSOCR/NsImgLdr/asian) + NsSpell + NsBars
│    ├─ Office: Syncfusion DocIO / XlsIO / Presentation / OfficeChart + *ToPdfConverter
│    └─ Scan: NAPS2.Wia 2.0 (WIA) + Twaindsm.dll (TWAIN)
└─ Helper proses: PDFLauncher.exe · PDFMonitor.exe · RegExt.exe · OpenWithPicker.exe
```

### 3.2 Bukti arsitektur dari metadata terkelola

**Identitas & framework** (REA `inspect_managed_artifact`):

| Field | Nilai |
|---|---|
| `classification.status` | `managed` |
| `runtime_family` | `dotnet-framework` |
| `implementation` | `cil` |
| `managed_architecture` | `x86_64` |
| `target_frameworks` | `.NETFramework,Version=v4.6.2` |
| `assembly` | `PDFgear` 3.0.0.0, **tanpa strong name** (`public_key.kind = none`) |
| `module.mvid` | `c8de2d6d-a2d3-44c1-9b4c-d3270cf625d2` |
| Bukti klasifikasi | `cli-header-observed` (offset 512), `target-framework-observed` (offset 1.982.488), `managed-architecture-derived` (offset 528) |

**49 referensi assembly** — highlights:

| Area | Referensi |
|---|---|
| WPF | PresentationFramework, PresentationCore, WindowsBase, System.Xaml, System.Printing, ReachFramework |
| PDF | **Patagames.Pdf 9.68.38.462**, **PDFKit 0.0.73.0** (internal), **Syncfusion.Pdf.Base 19.3460.0.57** |
| UI | **HandyControl 3.5.1.0**, CommunityToolkit.Mvvm 8.4.0.0, GongSolutions.WPF.DragDrop 4.0.0.0, VirtualizingWrapPanel 1.5.4.0, Microsoft.Xaml.Behaviors |
| OCR/Scan | **NAPS2.Wia 2.0.0.0** (WIA), System.Drawing, ImageProcessor 2.9.0.207 |
| Suara | **System.Speech**, **NAudio.Core 2.2.1.0**, NAudio.WinMM, **SoundTouch.Net** (pitch/tempo) |
| Data | **Microsoft.Data.Sqlite 6.0.31.0**, System.Data |
| Infrastruktur | **NLog 5.0.0.0**, **Sentry 6.6.0.0**, Newtonsoft.Json 13.0.0.0, LruCacheNet, Nito.AsyncEx, Microsoft.Extensions.DependencyInjection 9.0.0.2 |
| Shell | Microsoft.WindowsAPICodePack.Shell (dialog Open With), System.Windows.Forms |

**Konfigurasi runtime** (`PDFgear.exe.config`):

- `supportedRuntime` = `.NETFramework,Version=v4.6.2`
- `Switch.System.Windows.DoNotScaleForDpiChanges=false` → **DPI-aware aktif**
- `Switch.System.IO.UseLegacyPathHandling=false` → semantik path modern
- `Switch.System.IO.BlockLongPaths=false` → long path diizinkan
- 10+ `bindingRedirect` (Microsoft.Bcl.AsyncInterfaces→9.0.0.2, NAudio.Core→2.2.1.0,
  System.Buffers→4.0.4.0, …) → **aplikasi .NET Framework lama yang di-porting ke runtime modern**
  lewat paket NuGet-era.

**Logging** (`NLog.config`): target file `%LocalAppData%\PDFGEAR\Logs\Debug.log`, arsip harian
maks 30 berkas, level minimum `Info`, `throwExceptions=false`.

### 3.3 Helper proses terpisah

| Helper | Ukuran | Fungsi (dari nama & lokasi) |
|---|---:|---|
| `PDFLauncher.exe` | 518,1 KB | Peluncur dokumen dari shell |
| `PDFMonitor.exe` | 442,1 KB | Pemantau (1 tab) |
| `RegExt.exe` | 393,6 KB | Registrasi ekstensi shell |
| `pdfconverter.exe` | 1.148,1 KB | Konversi batch (punya `resources.dll` per locale) |
| `OpenWithPicker.exe` | 859,0 KB | Dialog "Open with" |
| `conv_helper.dll` | 1.110,5 KB | Pustaka helper konversi (bukan assembly terkelola: 0 item) |

> Pola **helper per fungsi + `resources.dll` per locale** memberi indikasi arsitektur
> "satu proses per capability" — mirip ide out-of-process pada Nitro, namun diimplementasikan
> lewat `.exe` terpisah, bukan modul yang di-*load* (VERIFIED untuk وجود file; PROCESS
> modelnya inferensi).

---

## 4. Permukaan fitur

### 4.1 Katalog aksi Copilot (27 aksi) — VERIFIED dari resource JSON

Setiap aksi punya `name`, `desc` (prompt), `embedding`, `params`, `examples`, `static`,
`confirm`, `disabled`.

| # | Aksi | Deskripsi (terjemahan prompt) | `static` | Konfirmasi |
|---:|---|---|---|---|
| 1 | `summary` | ringkas berkas ini | false | — |
| 2 | `print` | cetak dokumen/berkas | false | 11 bahasa |
| 3 | `select-page` | pindah/seleksi halaman tertentu | false | 11 bahasa |
| 4 | `page-display` | ubah mode tampilan halaman | false | 11 bahasa |
| 5 | `page-zoom` | zoom in/out tampilan | false | 11 bahasa |
| 6 | `rotate-page` | putar halaman kiri/kanan | false | 11 bahasa |
| 7 | `auto-scroll` | aktif/nonaktif auto-scroll | false | 11 bahasa |
| 8 | `slide-show` | mode presentasi (slide show) | false | 11 bahasa |
| 9 | `set-background` | ubah warna latar tampilan | false | 11 bahasa |
| 10 | `add-annotation` | tambah objek (highlight, underline, strike, area, line, rectangle, oval, ink, textbox, note) | false | 11 bahasa |
| 11 | `show-annotation` | tampil/sembunyikan anotasi | false | 11 bahasa |
| 12 | `edit-text` | **edit teks halaman PDF** | false | 11 bahasa |
| 13 | `extract-page` | ekstrak halaman ke PDF baru | false | 11 bahasa |
| 14 | `delete-page` | hapus halaman | false | 11 bahasa |
| 15 | `insert-page` | sisip halaman (blank, PDF lain, Word, gambar) | false | 11 bahasa |
| 16 | `crop-page` | potong halaman / ubah lebar-tinggi | false | 11 bahasa |
| 17 | `convert-from-pdf` | PDF → word/excel/ppt/png/jpeg/txt/html/rtf/xml | false | 11 bahasa (templat `{$mode}`) |
| 18 | `convert-to-pdf` | word/excel/gambar/ppt/rtf/txt → PDF | false | 11 bahasa (`{$mode}`) |
| 19 | `compress` | kompres PDF | false | 11 bahasa |
| 20 | `protect-pdf` | tambahkan password | false | 11 bahasa |
| 21 | `remove-password` | hapus password | false | 11 bahasa |
| 22 | `contact-us` | kirim umpan balik & dukungan | false | 11 bahasa |
| 23 | `settings` | buka pengaturan | false | 11 bahasa |
| 24 | `check-update` | cek & unduh pembaruan | false | 11 bahasa |
| 25 | `about` | buka halaman Tentang | false | 11 bahasa |
| 26 | `close-pdf` | tutup tampilan PDF | false | 11 bahasa |
| 27 | `find-in-pdf` | cari di dalam PDF | **true** | 11 bahasa |

> **Pola yang layak dicatat:** `static: true` pada `find-in-pdf` membedakan aksi yang bisa
> dijalankan tanpa dokumen terbuka. Prompt konfirmasi memakai placeholder `{$mode}` untuk
> memparameterisasi nama format. Seluruh 27 aksi tersedia dalam 11 bahasa.

### 4.2 Inventaris tipe .NET (permukaan produk)

Dari string metadata (nama namespace + kelas), dipetakan:

**`pdfeditor.Controls` — 64 tipe**, antara lain: `AllToolsControl`, `AnnotationCanvas`,
`Bookmarks`, `CommetTreeView`, `Copilot`, `DigitalSignatures`, `EnterPasswordDialog`,
`FlattenWindow`, `ImageControl`, `LinkEditWindows`, `Menus`, `NavigationView`,
`OcrComponents`, `PageEditor`, `PageOperation`, `PdfFileThumbnailImage`, `PdfPagePreview*`
(4 varian), `PdfViewerContextMenu`, `AppFrameWindow`.

**`pdfeditor.Models` — 23 tipe**: `Annotations`, `Attachments`, `Bookmarks`, `Commets`,
`Copilot`, `DynamicStamps`, `DocumentWrapper`, `Operations`, `Print`, `Protection`,
`RecoverStatusImage`, `RecoverStatusToStr`, `Scan`, `Stamp`, `Thumbnails`, `Translate`,
`Viewer`.

**`pdfeditor.Utils` — 24 tipe**: `AttachmentFileUtils`, `DocumentOcr`, `DrawUtils`, `Email`,
`PDFEraserUtil`, `PdfObjectExtensions`, `PdfTextMarkupAnnotationUtils`, `Print`, `Printer`,
`Scan`, `ScanService`, `ShareUtils`, `StampApplyHepler`, `TempFileUtils`, `TextInfo`,
`Validations`.

**`pdfeditor.ViewModels` — 11 tipe**: `AppFrameViewModel`, `DocumentViewModel`,
`GlobalViewModel`, `MenuViewModel`, `PageEditorViewModel`, `RecoverViewModel`,
`StampManageViewModel`, `TranslateViewModel`, `ViewToolbarViewModel`,
`AnnotationToolbarViewModel`, `InsertFromScannerViewModel`.

**`pdfeditor.Views` — 16 dialog/jendela**: `AppFrameWindow`, `AppSettingsWindow`,
`AttachmentDescriptionWindow`, `Discardconfirm`, `DocumentMainView`,
`DocumentPropertiesWindow`, `ESignLinkWindow`, `GearForMobilephone`, `PurchasedWindow`,
`RateWindow`, `RecoverWindow`, `SettingWindow`, `SubscribeWindow`, `Survey`, `WelcomeView`.

**`CommonLib.Common` — 19 tipe**: `AdManager`, `AppIdHelper`, `AppManager`, `BBCode`,
`ExplorerUtils`, **`GA4Manager`**, **`GA4Manager2`**, **`GAManager`**, `HistoryManager`,
`HotKeys`, `HttpHelper`, `ImageAnalyze`, `OcrHelpers`, **`OcrUtils`**, `ProcessMessageHelper`,
`RenderUtils`, `RestorePurchaseUtils`, `UpdateHelper`.

**`PDFKit.Utils` — 13 tipe**: `DigitalSignatures`, `DrawingHelpers`, **`Encrypt`**,
`FreeTextUtils`, `PageContents`, `PageHeaderFooters`, `PageRangeExtensions`,
`PdfFileInformationHelper`, `PdfPageRange`, `PdfRichTextStrings`, `StampUtils`,
`WatermarkUtils`, `XObjects`.

**`CommonLib.IAP` — 7 tipe**: `ActivationWindow`, `IAPHelper`, `InternalActivateHelper`,
`CountdownButton`, `BooleanToOpacityConverter` ×2, `TextEmptyVisibilityConverter`.

### 4.3 OCR (dua engine, satu lokal)

| Aspek | Tesseract | NsOCR |
|---|---|---|
| Biner | `x64/tesseract41.dll` (3.013,0 KB) | `NSOCR.dll` (3.559,4 KB) |
| Pendamping | `leptonica-1.80.0.dll` (3.968,0 KB) | `NsImgLdr.dll` (5.952,9 KB), `asian\asian.dll` (3.027,0 KB) |
| Data | `tessdata/` 63 berkas, 16 `traineddata` | `Bin_common\*.lng` (BG, CA, CS, …), `ALL_base.dat` |
| Kapabilitas ekstra | — | `NsSpell.dll` (ejaan), `NsBars.dll` (barcode) |
| REA | tidak dikirim ke Ghidra (>700 KB) | `jnsocr.dll` → **537 prosedur**, 505 string, 8 segment |

Kode aplikasi: `CommonLib.Common.OcrUtils` dengan metode
`GetAllOcrLanguages`, `ParseHocrCore`, `AddHocrContent`, `SetOCRDocumentLanguages`,
`DetectLanguageCore`, `GetStringAsync`, `GetStringAndCultureAsync` → **parser hOCR**
(hasil OCR dengan koordinat), bukan teks polos saja.

UI terkait: `ConvertToSearchablePdf` (dialog), `OcrSelectLanguageDialog`,
`NeedRecognitionBanner` (banner "dibutuhkan pengenalan"), `ScreenshotOcrToolbar`,
`ImageControl+<ocrBtn_Click>`, serta preferensi "%Prompt OCR when opening scanned PDFs."

### 4.4 Konversi & Office

- Syncfusion: `DocIO`, `XlsIO`, `Presentation`, `OfficeChart`, plus
  `DocToPdfConverter`, `ExcelToPdfConverter`, `PresentationToPdfConverter` — konversi
  Office **berhenti di .NET**, tanpa ketergantungan MS Office (berbeda dari Nitro yang
  bergantung add-in Office, dan Stirling yang bergantung LibreOffice).
- `PDFgear.Utils.ConvertUtils`, `conv_helper.dll`, `pdfconverter.exe` → jalur konversi
  terpisah.
- `PDFKit.Contents.Operations` + `pdfeditor.Models.Operations` → lapisan operasi PDF.

### 4.5 Tanda tangan, keamanan, redaksi

| Area | Bukti |
|---|---|
| Tanda tangan digital | `pdfeditor.Utils.DigitalSignatures`, `PDFKit.Utils.DigitalSignatures`, `ESignLinkWindow`, resource `ISO-3166-ID-SHORT.json` (kode negara) |
| Enkripsi | `PDFKit.Utils.Encrypt`, `pdfeditor.Models.Protection`, `EnterPasswordDialog` |
| Redaksi | `pdfeditor.Utils.PDFEraserUtil`, `PdfTextMarkupAnnotationUtils`, `Models.Annotations` |
| Watermark & stempel | `PDFKit.Utils.WatermarkUtils`, `StampUtils`, `Models.DynamicStamps`, `StampManageViewModel` |
| Header/footer | `PDFKit.Utils.PageHeaderFooters`, `pdfeditor.Controls.PageHeaderFooters` |
| Lampiran | `Models.Attachments`, `AttachmentFileUtils`, `AttachmentDescriptionWindow` |
| Scan | `Models.Scan`, `Utils.ScanService`, `InsertFromScannerViewModel`, `NAPS2.Wia` + TWAIN |
| Cetak | `Models.Print`, `Utils.Print`, `Utils.Printer`, `PDFKit.ToolBars.PrintProgress` |
| Berbagi | `Utils.ShareUtils`, `Utils.Email` |
| Pemulihan | `Models.RecoverStatus*`, `RecoverViewModel`, `RecoverBtnEnable` (tombol "pulihkan") |
| Form | `pdfeditor.Controls.EnterPasswordDialog`, `FlattenWindow` |

---

## 5. AI, telemetri, lisensi, dan privasi

### 5.1 Copilot:model dan batasan

- Katalog 27 aksi dengan `embedding` (embedding vektor per aksi) + `examples` (contoh prompt)
  + `params` (skema parameter) → ini **tool-calling/agentic** (bukan sekadar paraphrase).
- `static` menandai aksi yang tidak butuh dokumen terbuka.
- `confirm` memuat prompt konfirmasi **lokal** per bahasa (tidak perlu panggilan jaringan
  untuk menampilkan konfirmasi).
- Implementasi UI: `pdfeditor.Controls.Copilot`, `pdfeditor.Models.Copilot`,
  `pdfeditor.Utils.Copilot`, `AllToolsControlViewModel.*Command`.
- Tidak ada string yang menunjukkan model LLM atau endpoint API secara langsung dalam
  sapuan string — **OPEN**: model apa yang dipakai, apakah on-device atau cloud, dan
  apakah dokumen dikirim ke server, **tidak dapat dipastikan** dari artefak statis.

### 5.2 Telemetri & pelaporan

| Komponen | Bukti | Catatan |
|---|---|---|
| Google Analytics 4 | `CommonLib.Common.GA4Manager`, `GA4Manager2` | dua kelas GA4 — kemungkinan jalur event berbeda |
| Google Ads | `CommonLib.Common.GAManager` | pelacakan iklan/ads |
| Ads internal | `CommonLib.Common.AdManager` | iklan dalam aplikasi |
| Error reporting | assembly `Sentry 6.6.0.0` (referensi + `Sentry.dll` 770,5 KB) | crash/exception reporting |
| Log lokal | `NLog.config` → `%LocalAppData%\PDFGEAR\Logs\Debug.log` | retensi 30 arsip harian, level `Info` |
| Riwayat | `HistoryManager` | riwayat lokal aplikasi |
| Pembaruan | `UpdateHelper`, `CommonLib.Controls.UpdateWindow`, `NewVersionWindow` | |
| Login/akun | `CommonLib.Account.UserRequestClient`, `UserStore`, `CommonLib.Views.UserLoginWin` | ada alur akun |
| Pembelian | `CommonLib.IAP.*`, `RestorePurchaseUtils`, `PurchasedWindow`, `SubscribeWindow` | in-app purchase + restore |
| Pembatasan berbayar | **`CommonLib.Controls.PaidUserVisibilityConverter`** | visibilitas kontrol = status lisensi |

> Untuk UnionPDF: telemetri aktif (GA4 + GA + Sentry) **berlawanan** dengan default
> UnionPDF (telemetri nonaktif, AGPL, gratis penuh). Dicatat sebagai **fakta artefak**.

### 5.3 Lisensi pihak ketiga

**Open-source (15 paket tercatat di `OpensourceLicense/LICENSE.txt`)**:

| Paket | Lisensi |
|---|---|
| gong-wpf-dragdrop | BSD-3-Clause |
| HandyControl | MIT |
| ImageProcessor | MIT |
| LruCacheNet | MIT |
| NAPS2.Wia | MIT |
| NAudio.WinMM | MIT |
| Newtonsoft.Json | MIT |
| Nito.AsyncEx | MIT |
| SoundTouch.Net | MIT |
| VirtualizingWrapPanel | MIT |
| BouncyCastle.Cryptograph | MIT |
| DirectN | MIT |
| DotNetZip | MIT |
| NLog | MIT |
| Tesseract | Apache-2.0 |

**Komersial (tanpa kewajiban redistribusi terbuka)**:

| Pustaka | Versi | Peran |
|---|---|---|
| **Pdfium.Net SDK** (Chromium) | 4.34.40.2704 | render/mesin PDF |
| **Patagames Pdf .NET SDK** | 9.68.38.462 | baca/tulis PDF |
| **SautinSoft PDF Focus .Net** | 7.8.1.29 | PDF + OCR + konversi |
| **Syncfusion Essential** (PDF, DocIO, XlsIO, Presentation, OfficeChart, *ToPdfConverter) | 19.3460.0.57 | PDF & Office |
| **NsOCR** (Nettopsoft) | — | OCR, ejaan, barcode |
| BouncyCastle (versi .NET di CommonLib) | 2.5.0.6119 | kriptografi |
| HandyControl (versi Syncfusion Shared WPF) | — | komponen UI |
| Tesseract native (leptonica) | 4.1.1 / 1.80.0 | OCR (Apache-2.0 + BSD) |

> Empat pustaka PDF komersial dalam satu produk berarti **empat daftar kewajiban
> redistribusi** — pola yang perlu dipertimbangkan bila UnionPDF memilih satu engine.

---

## 6. Batasan analisis & pertanyaan terbuka

### 6.1 Metode yang tidak dijalankan / gagal

| Metode | Status | Dampak |
|---|---|---|
| Observasi runtime | **NOT_RUN** | tidak ada bukti urutan langkah, tampilan, atau perilaku |
| Uji I/O (dokumen nyata) | **NOT_RUN** | mutu output edit-teks/OCR/konversi **tidak** terukur |
| REA pada installer 132 MB | **DITOLAK** | `resource_constraint` (>64 MiB) |
| Ghidra pada `pdfium.dll` (12,7 MB) & `tesseract41.dll` (3,0 MB) | **DILEWATI** | batas ~700 KB per sesi; hanya inventaris versi |
| Decompilasi IL C# | **TIDAK DILAKUKAN** | metadata & string nama tipe dipakai; **body method tidak pernah dibaca** |
| Jaringan / panggilan API | **NOT_RUN** | tidak ada permintaan ke server AI/telemetri |

### 6.2 Unknown

| ID | Pertanyaan | Status |
|---|---|---|
| G-01 | Model LLM apa yang dipakai Copilot; on-device atau cloud? | **TERBUKA** — tidak ada string model/endpoint; hanya `embedding`/`examples`/`params` |
| G-02 | Apakah isi dokumen dikirim ke server saat Copilot dipakai? | **TERBUKA** — tidak ada bukti arah data; `CommonLib.Common.HttpHelper` ada |
| G-03 | Pembagian peran 4 pustaka PDF (mana yang dipakai untuk apa)? | **TERBUKA** — `PDFKit.Contents.Operations` pembungkus, tetapi pemetaan per operasi tidak teramati |
| G-04 | Apakah redaksi PDFgear benar-benar menghapus konten atau hanya menutupi? | **TERBUKA** — ada `PDFEraserUtil`; perilaku runtime tidak diuji |
| G-05 | Bagaimana `RecoverViewModel`/`RecoverStatusImage` memulihkan dokumen? | **TERBUKA** — indikasi ada fitur pemulihan, tidak teramati |
| G-06 | Apa peran `DirectN` (Direct3D/managed) dan `BBCode`? | **TERBUKA** |
| G-07 | Berapa languages OCR yang benar-benar tersedia (16 traineddata + .lng)? | **TERBUKA** — daftar nama file terpetakan, tetapi cakupan per versi Tesseract tidak diverifikasi |
| G-08 | Apakah `PDFgear.exe` masih memakai .NET Framework runtime bawaan Windows (bawaan OS) atau payload runtime sendiri? | **TERBUKA** — tidak ada folder runtime; `supportedRuntime v4.0`; Windows 11 masih menyertakan .NET Framework 4.8 |

### 6.3 Cakupan bukti

- **Kuat**: identitas & metadata assembly, 49 referensi, 4 resource tertanam, 27 aksi
  Copilot lengkap dengan prompt 11 bahasa, inventaris 4 pustaka PDF / 2 OCR / 15 paket
  OSS, inventaris tipe UI, tanda tangan digital, konfigurasi runtime.
- **Sedang**: nama tipe & method dari string metadata (kuat untuk *apa*, lemah untuk
  *bagaimana*).
- **Lemah/tidak ada**: perilaku runtime, mutu keluaran, performa, kompatibilitas file.

---

## 7. Lampiran

### 7.1 Indeks bukti REA (G-001 …)

| ID | Operasi | Target | Hasil kunci | Evidence ID |
|---|---|---|---|---|
| G-001 | `open_binary` | `PDFgear.exe` | PE, managed, CIL, x86_64, 8.681.096 byte, SHA-256 `6b74060a…` | — |
| G-002 | `inspect_managed_artifact` (summary) | `PDFgear.exe` | 7.881 item, coverage `complete-within-view` | `ev_290903ca2927104ec8dff161f67dcf33273bc9af6ea809fc267596f09933f9be` |
| G-003 | `inspect_managed_artifact` (lengkap) | `PDFgear.exe` | klasifikasi, target framework, 49 referensi, 4 resource, MVID, 7.828 atribut | `ev_a7cf577c399655fa786c76400e0088b3fd4e5a0d9ec8f792bc95bce10d715212` |
| G-004 | `inspect_managed_artifact` | `CommonLib.dll` | 2.030 item, SHA-256 `8adfb5d4…` | `ev_67c7c3ee02cb1585bd24a14beb2b7e025754db794c24618a85227ea9bdb6136a` |
| G-005 | `inspect_managed_artifact` | `PDFKit.dll` | 2.515 item, SHA-256 `113805a5…` | `ev_2ec8e9cd2a67203cc265bd23d6ad10e8e613f76b98362db256553c7d81d4a543` |
| G-006 | `inspect_managed_artifact` | `conv_helper.dll` | 0 item → **bukan** assembly terkelola (SHA-256 `2b7866b8…`) | `ev_d564fa0507179bc4d88e7fe4ea11a783b7a26e928758b5fffe7c5dc182a33dcd` |
| G-007 | `inspect_pe_resources` | `PDFgear.exe` | PE32+, machine 34404, 16 resource, 2 icon group | `ev_7f2a2a71b6195805f8db1ccc44b43cb76b34b185b785b002accdd9f8ab4a2863` |
| G-008 | `inspect_pe_resources` | installer 132 MB | **DITOLAK** `resource_constraint` (>67.108.864 byte) | — |
| G-009 | `open_binary` + `binary_overview` | `NsOCR\Bin_64\jnsocr.dll` | 537 prosedur, 505 string, 8 segment, SHA-256 `82b9339e…` | `ev_09b40e950440dcdde7ec2e5588a704bcefce90f3c2e080d698f2cdb901beee57` |
| G-010 | `open_binary` + `binary_overview` | `NsOCR\Bin_64\Twaindsm.dll` | 510 prosedur, 980 string, 8 segment, SHA-256 `3f76ff77…` | `ev_8fe48cea6604e87f20852c0f0799e1bb68bb282e7f83149f8e5686d332e7f7fa` |
| G-011 | `close_binary` (snapshot) | target aktif | snapshot 30.211 byte, 2 evidence record | — |

Bukti non-REA (alat lokal, read-only): `FileVersionInfo` per DLL, `Get-AuthenticodeSignature`,
ekstraksi string ASCII/UTF-16 (82.972 string unik pada `PDFgear.exe`), parsing resource JSON
tertanam (`Copilot.actions.json` → 27 aksi), inventaris tipe dari string metadata,
inventaris versi/tanggal berkas.

### 7.2 Ringkasan temuan

1. Inti .NET Framework 4.6.2 / WPF / CIL x86_64, MVID & 49 referensi terpetakan.
2. Empat pustaka PDF komersial dalam satu produk (Pdfium, Patagames, PDF Focus, Syncfusion).
3. Dua engine OCR ter-bundel (Tesseract 4.1.1 + NsOCR) plus ejaan & barcode.
4. AI Copilot: 27 aksi tool-calling dengan prompt konfirmasi 11 bahasa.
5. Konversi Office via Syncfusion — tidak bergantung MS Office.
6. UI: WPF + HandyControl + WebView2; 64 kontrol, 24 util, 23 model, 16 dialog, 11 viewmodel.
7. Telemetri: GA4 ×2, Google Ads, AdManager, Sentry, log NLog lokal.
8. Model berbayar: IAP + `PaidUserVisibilityConverter` + `RestorePurchaseUtils`.
9. Enkripsi (`PDFKit.Utils.Encrypt`), tanda tangan digital (ISO-3166), redaksi
   (`PDFEraserUtil`), watermark/stempel/header-footer, lampiran, scan WIA+TWAIN,
   cetak, email/berbagi, pemulihan dokumen.
10. 15 paket OSS tercatat; sisanya library komersial.
11. Installer 132 MB (Inno Setup) ditolak REA karena batas 64 MiB; analisis dilakukan pada
    instalasi aktif sehingga hambatan payload teratasi.

### 7.3 Catatan akhir

Semua angka berasal dari artefak read-only di mesin ini. PDFgear tidak dijalankan; tidak ada
berkas uji diproses; tidak ada panggilan jaringan; tidak ada lisensi diaktifkan. Batasan
terverifikasi: REA menolak installer >64 MiB, Ghidra tidak dipakai untuk modul >~700 KB,
dan **body method C# tidak pernah didekompilasi** — analisis ini berhenti pada metadata,
nama tipe, dan teks yang tertanam.
