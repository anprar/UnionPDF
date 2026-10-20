# research/REFERENCE_TAXONOMY.md — Taksonomi Modul → Fitur UnionPDF

**Status:** DRAFT v1 · **Tanggal:** 2026-10-20
**Sumber:** inventaris read-only folder instalasi Nitro PDF Pro 14.41.0.15
(`E-101`) + dokumentasi publik v14 (`E-001`…`E-008`).
**Tidak** berasal dari inspeksi biner (`REA_LIMITATIONS.md` L-01).

---

## Cara membaca

Kolom "modul aplikasi referensi" adalah **nama berkas** di folder instalasi —
ini fakta yang dapat diverifikasi siapa pun dengan melihat folder tersebut.
Kolom "kebutuhan UnionPDF" adalah **interpretasi** atas apa yang Gerbang
modul itu perlakukan.

---

## Modul engine → area fitur → keputusan UnionPDF

| Modul | Area fitur | Kebutuhan UnionPDF | Milestone | Keputusan |
|---|---|---|---|---|
| `np_page_edit` | Operasi halaman | Menyusun ulang dokumen | M2 | KEEP |
| `np_create_pdf` | Pembuatan PDF | Membuat dari nol / dari scan | M3 | KEEP (sebagian) |
| `np_annotations` | Anotasi | Menandai dokumen | M4 | KEEP |
| `np_forms` | Form & XFA | Mengisi & membuat formulir | M4 | KEEP (AcroForm), REJECT (XFA) |
| `np_actions` | Action & trigger | Form interaktif | M4 | DEFER |
| `np_objects` | Model objek | Fondasi edit granular | — | DEFER (M8) |
| `np_bookmarks` | Outline | Navigasi dokumen panjang | M11 | DEFER |
| `np_layers` | OCG layers | Dokumen multilayer | M11 | DEFER |
| `np_links` | Link | Rujukan & navigasi | M11 | DEFER |
| `np_attachments` | Lampiran | Lampiran dokumen | M7 | DEFER |
| `np_javascript` | JavaScript PDF | Legacy | — | REJECT (keamanan) |
| `np_ocr` | OCR | Dokumen pindai jadi bisa dicari | M5 | KEEP |
| `np_redaction` | Redaksi | Menghapus data sensitif | M7 | KEEP (diverifikasi) |
| `np_optimizer` | Optimasi | Ukuran file kecil | M6 | KEEP |
| `np_set_security` | Enkripsi & permission | Kontrol akses | M7 | KEEP |
| `np_digital_signature` | Tanda tangan kriptografis | Bukti autentikasi | M10 | DEFER (U-06) |
| `np_signature_stamp` | Stempel tanda tangan | Tanda tangan cepat | M10 | KEEP |
| `np_stamper` | Stempel | Penandaan status | M3 | KEEP |
| `np_watermarks` | Watermark | Branding/keselamatan | M3 | KEEP |
| `np_compare_pdf` | Perbandingan dokumen | Review revisi | M11 | DEFER |
| `np_convert_pdf` | Konversi | Office↔PDF, PDF→gambar | M9 | KEEP (gambar/teks), DEFER (Office) |
| `np_scan2pdf` | TWAIN scan | Akuisisi kertas | M9 | DEFER |
| `np_accessibility` | PDF bertag | Aksesibilitas | M12 | DEFER |
| `np_pdfa` | PDF/A | Kepatuhan arsip | M12 | DEFER |
| `np_cloud_storage` | iCloud/OneDrive | Penyimpanan awan | — | DEFER |
| `np_web_dav` | WebDAV | Repositori jarak jauh | — | DEFER |
| `np_smart_tips` | Tips kontekstual | Onboarding | M11 | DEFER |
| `np_nitro_sign` | Tanda tangan cloud | Alur tanda tangan | — | REJECT (vendor-specific) |
| `np_commands` | Lapisan command | Undo/redo, otomasi | M2/M11 | KEEP |

## Komponen pendukung → area → keputusan

| Komponen | Area | Keputusan |
|---|---|---|
| `libcef.dll` (212 MB) + `mozjs-102.dll` | UI berbasis browser | **REPLACE** → shell Qt (lebih ringan) |
| `NitroPDFPreviewHandler.dll` | Preview di Explorer | DEFER |
| `NitroPDFThumbnailProvider.dll` | Thumbnail di Explorer | DEFER |
| `Nitro.Pro.ShellExtension.dll` | Integrasi Explorer | DEFER |
| `Nitro.OfficeAddin.*.14.dll` | Add-in MS Office | REJECT |
| `imanage\` (17 berkas) | Integrasi DMS iManage | REJECT |
| `NxPdfCreator.exe` + `PS5UI.dll` | Printer virtual PDF | DEFER (M12) |
| `html_to_pdf.exe` | HTML → PDF | DEFER (M9) |
| `Eztwain4.dll` | TWAIN scanner | DEFER (M9) |
| `TBarCode11_x64.dll`, `idrsbarcode*15.dll` | Barcode | DEFER (M11) |
| `gsdll64.dll` (25 MB) | Ghostscript/PostScript | **REJECT** → tidak perlu; MuPDF menangani PS |
| `lcms2-2.dll` | Manajemen warna ICC | Tidak dipakai langsung (MuPDF punya sendiri) |
| `solid_framework\` (35 berkas) | PDF/A + validasi tanda tangan | Referensi saja (DEFER) |
| `IRIS_OCR\` + `idrsocr15.dll` | Engine OCR | Referensi saja → UnionPDF pakai Windows OCR |
| `mip_core.dll`, `mip_*_sdk.dll` | Microsoft Information Protection | REJECT |
| `Microsoft.Identity.Client.dll`, `msalruntime.dll` | Login/SSO enterprise | REJECT (tool lokal) |
| `WinSparkle.dll` | Auto-update | DEFER (manual lebih aman) |
| `BugSplat*.dll` / `BugSplatHD64.exe` | Crash reporting | **REPLACE** → tanpa telemetry |
| `mip_ClientTelemetry.dll` | Telemetri | **REPLACE** → tanpa telemetry |
| `CommandLine.dll` | CLI | KEEP (M11) |
| `Certs\EUTL`, `Certs\Nitro` | Penyimpanan sertifikat | DEFER (M10) |
| `xfa\` (389 berkas) | XFA form | REJECT |
| `NitroPlatform14.dll` | Platform check | Tidak relevan |

## Pola yang berulang

1. **Satu engine, banyak modul.** Aplikasi referensi memecah engine PDF jadi
   29 modul per kapabilitas. UnionPDF meniru **pola arsitektural** ini
   (satu adapter per kapabilitas) dengan **satu** engine (MuPDF).
2. **Integrasi vendor adalah-separat dari editing.** Modul DMS/cloud/MS
   Office berada di luar inti editing. UnionPDF juga memisahkannya — dan
   memilih tidakCompetition punya sebagian besar.
3. **Fitur berisiko comes with a proprietary engine.** Edit teks reflow,
   PDF/A, validasi signature, XFA — semuanya butuh engine khusus. UnionPDF
   akan mengimplementasikan bertahap dengan label jujur.
4. **UI berat adalah pilihan, bukan keharusan.** 212 MB CEF untuk toolbar
   + viewer; UnionPDF memilih shell native.
5. **Telemetri aktif secara default.** UnionPDF: nol.
