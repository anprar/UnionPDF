# EVIDENCE_INDEX.md — Indeks Bukti

**Status:** aktif · **Sesi:** `2026-10-20T1624+0700`
Semua klaim di dokumen lain harus dapat ditelusuri ke id di bawah ini.

---

## Legenda

| Prefix | Jenis | Arti |
|---|---|---|
| `E-0xx` | Bukti eksternal (dokumentasi publik) | Fakta tentang aplikasi referensi |
| `E-1xx` | Bukti workspace (inventaris) | Fakta tentang instalasi referensi |
| `E-2xx` | Bukti pengukuran (spike) | Fakta tentang engine UnionPDF |
| `E-3xx` | Bukti keputusan | Artefak keputusan proyek |

---

## Bukti eksternal — aplikasi referensi

| ID | Sumber | Isi | Digunakan di | Tingkat |
|---|---|---|---|---|
| E-001 | `gonitro.com/user-guide` (indeks) | Taksonomi fitur: anotasi, konversi, edit teks/gambar, OCR, form, tanda tangan, navigasi, undo/redo, panel | `REA_FINDINGS.md` §3–4 | DOCUMENTED |
| E-002 | `gonitro.com/user-guide/pro/article/optical-character-recognition` | Dialog OCR: "Make Searchable" vs "Make Searchable and Editable"; preferensi: deskew, orientasi, threshold, smoothing, bahasa, kualitas, downsample, kompresi, retain background; rentang halaman; prompt otomatis saat membuka scan | `REA_FINDINGS.md` §4.1 | DOCUMENTED |
| E-003 | `gonitro.com/user-guide/pro/article/optimize-a-pdf-file` | Preset Reduced Size / Reduced Size and Print Ready / Custom; opsi resample, hapus konten interaktif, bookmark, attachment, thumbnail, named destination, objek tak terpakai, link invalid; "Show Details" | `REA_FINDINGS.md` §4.2 | DOCUMENTED |
| E-004 | `gonitro.com/user-guide/pro/article/add-or-edit-text-in-a-pdf` | Model dua lapisan (annotation layer default, content layer via Ctrl+click); reflow tingkat paragraf; flatten teks & flatten semua anotasi | `REA_FINDINGS.md` §4.3 | DOCUMENTED |
| E-005 | `gonitro.com/user-guide/pro/article/ocr-an-existing-pdf` | Alur OCR: tombol OCR di Review tab, opsi rentang halaman, dialog Advanced | `REA_FINDINGS.md` §4.1 | DOCUMENTED |
| E-006 | `gonitro.com/release-hub` + `gonitro.com/documentation/release-notes` | Fitur v26 (Smart Tools/AI, redesign, color picker, responsivitas) **tidak ada** di v14; timeline rilis v14 | `REA_FINDINGS.md` §4.5 | DOCUMENTED |
| E-007 | `gonitro.com/nitro-pro` (halaman produk) | Klaim fitur tingkat produk: edit text & images dengan full-page paragraph reflow, PDF→Word/Excel/PPT, PDF/A, tag & embed fonts, enkripsi AES-256, batch | `REA_FINDINGS.md` §6 | DOCUMENTED |
| E-008 | `help.gonitro.com` (referensi pengamatan dokumen) | Navigasi pane, Comments pane, Pages pane multi-select | `REA_FINDINGS.md` §4.4 | DOCUMENTED |

## Bukti workspace — inventaris instalasi referensi

| ID | Sumber | Isi | Digunakan di | Tingkat |
|---|---|---|---|---|
| E-101 | `Get-ChildItem "C:\Program Files\Nitro\PDF Pro\14"` | 1.014 berkas, 854,6 MB; 29 modul `np_*.dll`; 212 MB `libcef.dll`; `IRIS_OCR`, `solid_framework`, `xfa` (389 berkas), `Certs`, `imanage` | `REA_FINDINGS.md` §2–3 | VERIFIED |
| E-102 | `VersionInfo` pada `NitroPDF.exe`, `npdf.dll` | Versi **14.41.0.15**, publisher *Nitro Software, Inc.* | `REA_FINDINGS.md` §2 | VERIFIED |
| E-103 | `VersionInfo` pada `idrspdf15.dll` | Versi 15,4,3,1705 — *IMAGE RECOGNITION INTEGRATED SYSTEMS SA* (mesin OCR IRIS) | `REA_FINDINGS.md` §2 | VERIFIED |
| E-104 | Inventaris `x64\`, `x86\`, `en-US\`, `solid_framework\`, `imanage\` | NxPdfCreator/PS5UI (printer virtual), UI MUI per-modul, Solid Framework (PDF/A + validasi tanda tangan), integrasi iManage + WebView2 | `REA_FINDINGS.md` §2 | VERIFIED |

## Bukti pengukuran — spike UnionPDF

Semua di `spikes/out/*.json`, dapat direproduksi dengan
`.\scripts\run_spikes.ps1`.

| ID | Spike | Hasil kunci | FAIL/PASS |
|---|---|---|---|
| E-201 | S1 render + text layer | median 33,87 ms/hlm @2×; 13 word; search 12 hit | PASS |
| E-202 | S2 operasi halaman | merge 14/14, split 4/4, rotate+delete 11 hlm rot 90°, reopen konsisten | PASS |
| E-203 | S2 dokumen besar | 500 hlm: buka 11,69 ms, render 32,51 ms, simpan 12,34 ms | PASS |
| E-204 | S3 anotasi | 4 jenis anotasi dibuat, 3 anot reopen (FreeText/Highlight/Text) | PASS |
| E-205 | S4 form | text field & checkbox buat→isi→simpan→reopen, nilai bertahan | PASS |
| E-206 | S5 redaksi | `secret_still_extractable: false`, teks publik utuh | PASS |
| E-207 | S6 gambar/stempel/watermark/footer | 1 image, watermark & footer terbaca | PASS |
| E-208 | S7 ekspor PNG | median 21,3 ms/hlm | PASS |
| E-209 | S8 font & enkripsi | builtin ✓, TTF embed ✓, AES-256 ✓, re-auth ✓ | PASS |
| E-210 | S9 background job | cancel @300 ms → berhenti di langkah 15/200; 661 tick/detik | PASS |
| E-211 | S10 OCR Windows | 145,3 ms/hlm; 3 dari 4 baris persis; "1.250.000" → "1.250.OOO" | PASS (dengan catatan) |
| E-212 | S10 OCR Tesseract | tidak terpasang (`on_path: false`, `TESSDATA_PREFIX` null) | NOT AVAILABLE |
| E-213 | S10 MuPDF `get_textpage_ocr` | gagal: perlu Tesseract | FAIL (expected) |
| E-214 | S11 Qt | Qt 6.11.0, offscreen OK, DPR 1,0, widget & processEvents jalan | PASS |
| E-215 | S12 packaging | MuPDF payload 50,62 MB; PyInstaller belum terpasang | NOT MEASURED |
| E-216 | S10 binding WinRT | winrt 3.2.1: `get_available_recognizer_languages` tidak diekspos; `get_file_from_path_async` + `open_read_async` + `FileAccessMode` | VERIFIED |

## Bukti analisis mendalam (v2) — inspeksi biner read-only

Izin eksplisit pengguna, 2026-10-20. Skrip: `scripts/extract_mui_strings.py`,
`scripts/extract_native_strings.py`, `scripts/build_ribbon_map.py`,
`scripts/analyze_ui_evidence.py`. Data mentah: `docs/research/*.json`.

| ID | Sumber | Isi | Digunakan di | Tingkat |
|---|---|---|---|---|
| E-400 | REA `open_binary` + `binary_overview` (`NitroPDF.exe`) | PE32+, x86_64, 16.173.288 byte, SHA-256 `736c4b88…46b9` | `REA_FINDINGS.md` §2 | VERIFIED |
| E-401 | Ekstraksi string 30 modul (ASCII/UTF-16) | **783 kontrol `AVRibbon:*`**, 10.284 identifier fitur | `REA_FINDINGS.md` §3, §5 | VERIFIED |
| E-402 | REA `open_binary` (`np_pdfa.dll`) | SHA-256 `66949294…c051b`, 656 KB | `REA_FINDINGS.md` §2 | VERIFIED |
| E-403 | REA `binary_overview` (`np_pdfa.dll`) | 8 segment; `.text` 453.632 B; **1.852 prosedur**; 1.165 string | `REA_FINDINGS.md` §1 | VERIFIED |
| E-404 | REA `inspect_pe_resources` (`NitroPDF.exe`) | PE32+; resource dir di offset 12.265.984; 15 tipe; RT_ICON 34 entri | `REA_FINDINGS.md` §2 | VERIFIED |
| E-405 | `NitroPDF.exe.man` (manifest, read-only) | `requestedExecutionLevel="asInvoker" uiAccess="false"` | `REA_FINDINGS.md` §2 | VERIFIED |
| E-406 | Parser PE sendiri → RT_STRING, 35 berkas `.mui` | **14.452 string UI** (label, opsi, pesan error) | `REA_FINDINGS.md` §4 | VERIFIED |
| E-407 | `docs/research/V14_RIBBON_STRUCTURE.md` | 14 tab ribbon + 90 toolbar kontekstual, pemilik per modul | `REA_FINDINGS.md` §3 | VERIFIED |
| E-408 | `docs/research/V14_UI_EVIDENCE.md` | Laporan label & pesan error per modul (3.421 baris) | `REA_FINDINGS.md` §4 | VERIFIED |
| E-409 | String `AVCmdHandler*_RegisterCommandsProc` / `_WorkProc`, `*_plugin::init` | Pola command-handler per fitur | `REA_FINDINGS.md` §5 | VERIFIED |
| E-410 | String `SOFTWARE\Nitro\PDF Pro\14\Settings` | Lokasi registry per versi | `REA_FINDINGS.md` §5 | VERIFIED |
| E-411 | String `ProHomePDFCombine`, `ProWordAddinPDFCreated`, dst. | **Bukti event analitik/telemetri ada** | `REA_FINDINGS.md` §5 | VERIFIED |
| E-412 | String `DocumentPdfUAComplianceSet`, `SetPdfUALanguage` | Dukungan PDF/UA | `REA_FINDINGS.md` §4.11 | VERIFIED |
| E-413 | String `pdfa_converter::preflight_result` | Preflight pada konversi PDF/A | `REA_FINDINGS.md` §4.11 | VERIFIED |

## Bukti keputusan

| ID | Artefak | Isi |
|---|---|---|
| E-301 | `docs/decisions/ADR-001-stack-baseline.md` | Keputusan stack + konsekuensi + rute cadangan |
| E-302 | `docs/STACK_EVALUATION.md` | Perbandingan 4 kandidat, bobot, skor |
| E-303 | `docs/TECH_SPIKES.md` | Ringkasan S1–S12 |
| E-304 | `spikes/out/*.json` | Data mentah pengukuran |
| E-305 | `docs/sessions/2026-10-20T1624+0700.md` | Log aktivitas sesi |

## Bukti yang TIDAK ada (dan tidak boleh diklaim)

| Klaim | Status |
|---|---|
| Performa Nitro | **TIDAK DIUKUR** — nol benchmark Nitro dijalankan |
| Perilaku **runtime** Nitro | **TIDAK DIAMATI** — aplikasi tidak dieksekusi |
| Source asli / pseudocode Nitro | **TIDAK ADA** — tidak ada decompilasi; hanya string & resource |
| Analisis native `NitroPDF.exe` (executable utama) | **GAGAL** — Ghidra timeout saat import (16 MB, CEF) → `U-08` |
| Kecepatan OCR Nitro | **TIDAK DIUKUR** |
| Fitur terkunci lisensi Nitro | **TIDAK DIVERIFIKASI** — dilarang mencoba membukanya |
| Kualitas PDF/A Nitro | **TIDAK DIUKUR** |
| Edit teks existing MuPDF dengan reflow | **TIDAK DIUJI** — U-01 |
| Daftar bahasa OCR yang dipakai v14 | **TIDAK DIKETAHUI** — tidak ada di `.mui` → `U-10` |
| Tata letak visual & pintasan keyboard v14 | **TIDAK DIKETAHUI** — `U-07` |
