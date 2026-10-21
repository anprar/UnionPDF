# Analisis REA — Stirling-PDF 3.2.0 (Windows x86_64)

**Status:** v1 — analisis referensi, read-only
**Tanggal analisis:** 2026-10-21
**Target:** `<USERPROFILE>\Downloads\Stirling-PDF-windows-x86_64.msi` (installer, 256,4 MB)
**Artefak teranalisis:** Tauri shell `Stirling-PDF.exe` + fat JAR `stirling-pdf-3.2.0.jar` + JRE 25.0.4.1
**Metode:** REA MCP (Ghidra 12.1.4) + inventaris arsip + parsing constant pool class Java
**Dokumen kembar:** `docs/ANALYSIS_NITRO14.md` (analisis target pertama)

> **Catatan redaksi (2026-10-21, sesi `2026-10-21T1114+0700`).** `<USERPROFILE>` =
> folder profil pengguna Windows pada mesin analisis (`C:\Users\<nama-profil>`); nama
> profil disamarkan. Nilai `posthog.api.key` disamarkan menjadi `phc_<DISAMARKAN>`;
> sidik SHA-256 nilai asli (47 karakter, prefiks `phc_`):
> `a3034c652dbb6c306fe9c4460091252c42e0dbc1236c939264bc5d041726bb47`. Menurut
> dokumentasi resmi PostHog (Privacy compliance FAQ), token berawalan `phc_` adalah
> **project token** yang boleh publik dan tidak memberi akses ke data privat; ia bukan
> personal API key (`phx_`). Token tidak pernah diuji, dipakai, atau dikirimi event.
> Versi, ukuran, hash artefak, dan bukti teknis lain tidak diubah.

> **Cakupan.** Analisis statis terhadap artefak yang terpasang di komputer ini: apa yang ada di
> dalam binary, permukaan API/UI, stack, konfigurasi, dan perilaku yang dapat disimpulkan
> dari teks yang tertanam. Aplikasi **tidak pernah dijalankan** — tidak ada klaim tentang
> hasil nyata sebuah operasi pada file PDF.
>
> Stirling-PDF adalah proyek **open-source** (model *open-core*: inti MIT, sebagian fitur
> dalam paket `stirling.software.proprietary.*`). Karena itu, kutipan di dokumen ini
> Unlike dokumen Nitro bukan masalah hak ciplah yang sama.

---

## 0. Ringkasan eksekutif

Stirling-PDF 3.2.0 untuk Windows **bukan aplikasi PDF native**. Ia adalah tiga lapis yang
dirangkai:

```
┌─ Stirling-PDF.exe (52,3 MB)  ─ Tauri v2: Rust + WebView2, aset React di dalam .rdata
│     └─ menjalankan backend Java lokal di http://127.0.0.1:8080
├─ runtime/jre (JRE 25.0.4.1)  ─ runtime Java ter-bundel
└─ libs/stirling-pdf-3.2.0.jar (193,8 MB)  ─ Spring Boot 4.1.1 + Jetty 12 + PDFBox 3
      └─ 177 controller REST · 248 dependency · 476 class aplikasi
```

Enam temuan utama:

1. **Shell desktop = Tauri (Rust), bukan Electron.** Bukti: string `__TAURI_INTERNALS__`,
   `plugin:webview|internal_toggle_devtools`, `window.__TAURI_INTERNALS__.invoke('plugin:window|…')`,
   `.rdata` 38 MB berisi aset web, dan crate `serialize-to-javascript 0.1.2` (VERIFIED).
2. **Backend = server HTTP lokal.** String launcher: `"Starting backend with bundled JRE..."`,
   `"Backend started on port: "`, `"CRITICAL: Port 8080 is already in use by another process!"`,
   `"Navigate to: http://127.0.0.1:<port>"`, `"Running in Self-Hosted mode - starting local
   backend (for hybrid execution support)"` (VERIFIED).
3. **PDF diurus Apache PDFBox 3.0.8 + PDFium (jpdfium 1.1.6).** PDFium membawa native
   `natives-windows-x64`; PDFBox membawa modul `preflight` (validasi PDF/A) + `xmpbox`
   (VERIFIED, dari inventaris dependency).
4. **Fitur berat memakai tool eksternal, TIDAK dibundel.** `CompressController` mencatat
   "Pre/Post-Ghostscript file size" dan "Pre/Post-QPDF file size"; OCR memanggil
   **Tesseract** dengan flag kompatibel OCRmyPDF (`skip-text`/`force-ocr`/`Normal`,
   `hocr`/`sandwich`); konversi Office lewat `stirling-office-convert` + LibreOffice.
   Installer Windows **tidak** memuat gs/qpdf/tesseract/LibreOffice (VERIFIED).
5. **Model *open-core* + freemium, dengan telemetri aktif ke PostHog.** `ConfigController`
   mengekspos `getLicenseType`, `getPremium`, `premiumEnabled`; `application.properties`
   memuat `posthog.api.key=phc_<DISAMARKAN>` (project token PostHog; lihat catatan redaksi) dan
   `posthog.host=https://eu.i.posthog.com`; ada sakelar `system.enableAnalytics`
   (VERIFIED).
6. **Permukaan fitur sangat luas dan berbasis API REST.** 177 controller, 47 jalur API
   literal, dan frontend React yang *code-split* per fitur (nama chunk = nama fitur, mis.
   `AddWatermark`, `CertSign`, `OCR`, `Merge`, `PdfTextEditor`, `BookletImposition`).

### 0.1 Angka kunci

| Metrik | Nilai | Sumber |
|---|---:|---|
| Berkas dalam payload MSI | 5 (+ runtime JRE) | inventaris ekstraksi |
| Ukuran installer | 256,4 MB | `Get-FileHash`/ukuran |
| Ukuran shell Tauri | 52,3 MB (PE32+, x86_64) | REA `inspect_pe_resources` + parser PE |
| Ukuran fat JAR | 193,8 MB | REA `open_binary` |
| Entri ZIP dalam JAR | 1.136 | REA `inspect_artifact` (1.111 node, 1.137 occurrence, 0 kontradiksi integritas) |
| Dependency JAR (`BOOT-INF/lib`) | 248 | inventaris ZIP |
| Class aplikasi (`BOOT-INF/classes`) | 476 | parsing constant pool |
| Komposisi class | 177 controller · 153 model · 88 service · 36 config | idem |
| Jalur API literal unik | 47 | idem |
| Modul `common` (klien OpenAPI + cluster) | 470 entri | idem |
| Prosedur `stirling_thumbnail_handler.dll` | 653 (6 segment) | REA `binary_overview` (Ghidra) |
| String `Stirling-PDF.exe` | 344.413 | ekstraksi ASCII+UTF-16 |
| Resource PE `Stirling-PDF.exe` | 10 entri, 1 icon group | REA `inspect_pe_resources` |

### 0.2 Posisi terhadap target pertama (Nitro PDF Pro 14)

Perbandingan arsitektur — **fakta terukur dari dua artefak**, bukan penilaian.

| Aspek | Nitro PDF Pro 14.41.0.15 | Stirling-PDF 3.2.0 (Windows) |
|---|---|---|
| Bentuk aplikasi | Desktop native: MFC + BCGControlBar 24.3 | Desktop *hybrid*: Tauri/Rust shell → server HTTP lokal |
| Logika inti | Native C++ (`npdf.dll` 13,4 MB + IRIS/DRS) | Java (Spring Boot 4.1.1, PDFBox 3.0.8, PDFium) |
| Runtime | native bawaan, tanpa runtime eksternal | JRE 25.0.4.1 ter-bundel (51,9 MB / 215 berkas) |
| Render | Mesin PDF internal | PDFium native (jpdfium) + raster via PDFBox |
| UI | Ribbon 13 tab, 228 grup toolbar kontekstual | Web UI React (WebView2), **84 chunk** aset (74 JS + 10 CSS), tanpa ribbon |
| Antarmuka antar bagian | Modul `np_*.dll` out-of-process, named event | REST API `/api/v1/**`; dependensi Jetty WebSocket tersedia; cluster via Valkey |
| OCR | IRIS/DRS OCR internal, 20 model bahasa | **Tesseract eksternal** (OCRmyPDF-compatible) |
| Kompresi | Modul internal `np_optimizer` | **Ghostscript + QPDF eksternal** |
| Konversi Office | Bergantung add-in Microsoft Office | Bergantung LibreOffice + `stirling-office-convert` |
| Model lisensi | Proprietas, trial/premium | Open-core MIT + paket proprietary + lisensi tier |
| Telemetri | `metrics_tool.exe` + BugSplat | PostHog (project token tertanam, host EU), `system.enableAnalytics` |
| Basis data | Tidak (berkas) | H2 embedded + JPA (cluster opsional via Valkey) |
| Ukuran install | 854,6 MB | 256,4 MB MSI (JAR 193,8 + JRE + shell) |

---

## 1. Metodologi, lingkungan, dan batasan

### 1.1 Environment

| Item | Nilai |
|---|---|
| OS | Windows 11 (x64) |
| Shell | PowerShell |
| Python analisis | `.venv` → 3.13.9 |
| Provider REA | Ghidra 12.1.4 (`tools.rea`) |
| Target utama | `<USERPROFILE>\Downloads\Stirling-PDF-windows-x86_64.msi` (256,4 MB) |
| Area kerja ekstraksi | `<USERPROFILE>\AppData\Local\Temp\opencode\stirling` (di luar repo) |
| Snapshot REA | `…\opencode\rea_stirling_snapshot.json` (286.669 byte, 6 evidence record) |

### 1.2 Urutan metode

1. **Verifikasi target** — path yang diberikan (`…\Stirling-PDF-windows-x86_64`, tanpa
   ekstensi) tidak ada; artefak sebenarnya adalah **`.msi` di `Downloads`**.
2. **Percobaan REA langsung** — `open_binary` pada MSI **ditolak**:
   `unsupported_target` / `file_format_rejected`. MSI bukan format yang didukung REA.
3. **Ekstraksi payload** — `msiexec /a … /qn TARGETDIR=<temp>` (administrative install;
   **sumber hanya dibaca**, tidak ada instalasi ke sistem, tidak ada perubahan registry
   aplikasi). Hasil: 220 file, 299,2 MB.
4. **REA pada artefak yang didukung**:
   - `open_binary` + `inspect_artifact` pada fat JAR (arsip ZIP) → inventaris lengkap.
   - `open_binary` + `binary_overview` + `list_procedures` + `list_strings` pada
     `stirling_thumbnail_handler.dll` (163,5 KB, di bawah batas Ghidra).
   - `inspect_pe_resources` pada `Stirling-PDF.exe` dan thumbnail DLL (operasi portable,
     tanpa engine).
5. **Percobaan Ghidra pada shell 52,3 MB → gagal**:
   `provider_timeout`, batas startup 330.000 ms. Diakui sebagai keterbatasan analisis
   (§5), bukan disembunyikan.
6. **Percobaan decompiler Java (JEB) → tidak tersedia**:
   `capability_unavailable` — tidak ada JEB client yang melayani MCP
   (`http://127.0.0.1:8425/mcp` tidak hidup). Tidak di-*install* karena di luar
   otorisasi.
7. **Alternatif parsing tanpa decompiler** — parser constant pool class file sendiri
   (baca `CONSTANT_Utf8`) untuk 476 class + 470 entri modul `common`. Menghasilkan
   nama class, nama method, dan literal string (jalur API, pesan, label). Ini **bukan**
   decompilasi: tidak ada body method yang dipulihkan.

### 1.3 Yang tidak dilakukan

- Tidak menjalankan Stirling-PDF, backend Spring Boot-nya, maupun tool eksternalnya.
- Tidak mengirim berkas uji ke server, tidak memanggil API, tidak menjalankan OCR/kompresi.
- Tidak mengubah, mempatch, atau mengekstrak ulang file asli di `Downloads`.
- Tidak membayar/mengaktifkan lisensi, tidak memakai akun, tidak mengirim telemetri.
- Tidak menganalisis endpoint server secara aktif (tidak ada lalu lintas jaringan).

### 1.4 Reproduksi

```powershell
# 1) ekstrak payload (sumber read-only)
msiexec /a "<USERPROFILE>\Downloads\Stirling-PDF-windows-x86_64.msi" /qn `
  TARGETDIR="<USERPROFILE>\AppData\Local\Temp\opencode\stirling"

# 2) inventaris JAR (bisa pakai REA atau parser ZIP)
# 3) parsing constant pool class file -> nama class, method, literal
# 4) checksum anchor
Get-FileHash "…\stirling-pdf-3.2.0.jar" -Algorithm SHA256

# 5) verifikasi angka dokumen ini (keluar 0 bila cocok)
.venv\Scripts\python.exe scripts\verify_stirling_artifact.py `
  "…\libs\stirling-pdf-3.2.0.jar" "…\Stirling-PDF.exe"
```

---

## 2. Artefak & komposisi

### 2.1 Isi payload MSI

| Berkas | Ukuran | Identitas | Peran |
|---|---:|---|---|
| `Stirling-PDF.exe` | 52,3 MB | ProductName "Stirling PDF", FileVersion **3.2.0**, PE32+ AMD64 | Shell Tauri (Rust + WebView2) |
| `libs/stirling-pdf-3.2.0.jar` | 193,8 MB | Spring Boot fat JAR, SHA-256 `e3ebb751…` | Backend: API + UI + engine PDF |
| `runtime/jre/` | 51,9 MB (215 berkas) | **JRE 25.0.4.1** | Runtime Java ter-bundel |
| `stirling_thumbnail_handler.dll` | 163,5 KB | Rust (sha256 `16f064ed…`) | Thumbnail handler shell Explorer |
| `stirling-provision.exe` | 280,0 KB | tanpa metadata versi | Helper provisioning |

Checksum anchor:

| Artefak | SHA-256 |
|---|---|
| `Stirling-PDF-windows-x86_64.msi` | `043a2b01324dea6fe126fb6e658aa52f8106abe33ef5df8ef752c4ca05f5c8b1` |
| `Stirling-PDF.exe` | `2a5a74c6afcbdacc97833518a4d0b6488579cc368f207fc53c5ab17fff6e4a4b` |
| `stirling-pdf-3.2.0.jar` | `e3ebb751b6eff3e57d34057d6c35150554e7a3df63128a37c99c79d5afc3e290` |
| `stirling_thumbnail_handler.dll` | `16f064edbf2101ec9f56009992ea8a1729ebd214cad10a32804eee8415f6a6dc` |

### 2.2 Verifikasi terhadap instalasi sistem

Aplikasi yang sama terpasang di `C:\Program Files\Stirling PDF\` (terdaftar di registry:
DisplayName "Stirling PDF", DisplayVersion 3.2.0, Publisher "Stirling PDF Inc.").
Kelima artefak **byte-identik** dengan payload MSI yang dianalisis:

| Artefak | SHA-256 (prefix) | Identik dengan MSI |
|---|---|---|
| `Stirling-PDF.exe` | `2a5a74c6afcbdacc` | ✅ |
| `stirling-provision.exe` | `435fc33ba39766fa` | ✅ |
| `stirling_thumbnail_handler.dll` | `16f064edbf2101ec` | ✅ |
| `libs/stirling-pdf-3.2.0.jar` | `e3ebb751b6eff3e5` | ✅ |
| `runtime/jre/release` | `285bbf962e8fd40d` | ✅ |

Artinya: **seluruh hasil analisis dokumen ini berlaku persis untuk versi yang terpasang**
di mesin ini — tidak ada keraguan "versi berbeda".

> Catatan: folder `C:\Program Files (x86)\UPDF` juga ada di mesin ini, tetapi berisi
> **UPDF (Superace) yang tidak lengkap** — hanya runtime Qt 6 + ekstensi shell + komponen
> virtual printer, **tanpa executable aplikasi utama**. Tidak dipakai sebagai sumber
> analisis karena tidak mewakili produk yang utuh.

### 2.3 Komposisi fat JAR

Inventaris REA (`inspect_artifact`, provider `rea-workflow`):

- **1.111 node**, **1.137 occurrence**, **1.136 edge**, coverage `complete-within-view`
  (3.384 item diperiksa dari 3.384).
- **1.056 entri berkas** + **81 entri direktori**, **0 symlink**, **0 kontradiksi integritas**.
- Batasan yang dilaporkan REA: inventaris ZIP hanya memuat entri *central directory*;
  byte non-entri (mis. signing block sebelum central directory) **tidak** terhitung.

Struktur:

| Lokasi | Isi |
|---|---|
| `BOOT-INF/classes/` | 476 class aplikasi + resource (font, config) |
| `BOOT-INF/lib/` | 248 JAR dependency |
| `org/` | 116 class Spring Boot Loader |
| `META-INF/` | 5 entri (manifest, signature) |

Resource non-class di `BOOT-INF/classes` (terbesar):

| Resource | Ukuran | Arti |
|---|---:|---|
| `static/fonts/NotoSansSC-Regular.ttf` | 12,9 MB | CJK sans-serif (Tionghoa) |
| `static/fonts/NotoSansKR-Regular.ttf` | 7,1 MB | Korea |
| `static/fonts/NotoSansTC-Regular.ttf` | 4,9 MB | Tradisional |
| `static/fonts/NotoSansJP-Regular.ttf` | 2,8 MB | Jepang |
| `certdata.txt` | 1,4 MB | **Basis data sertifikat bawaan Mozilla NSS** (MPL-2.0) |
| `type3/library/fonts/**` | ± 30 MB | Pustaka font Type3 (Noto, DejaVu, STIX Two Math) |
| `application.properties` | 6,3 KB | Konfigurasi aplikasi (lihat §4.3) |
| `logback.xml` | 4,1 KB | Konfigurasi logging |
| `banner.txt` | 380 B | Banner ASCII "Powered by Spring Boot" |

> Font CJK ± 28 MB di dalam JAR menunjukkan target pengguna non-Latin-first; font Type3
> (`type3/library`) adalah kebutuhan khusus konversi teks editable.

---

## 3. Arsitektur runtime

### 3.1 Empat lapis yang terverifikasi

| Lapis | Bukti | Peran |
|---|---|---|
| **1. Shell Tauri (Rust)** | `__TAURI_INTERNALS__`, `plugin:webview|internal_toggle_devtools`, `window.__TAURI_INTERNALS__.invoke('plugin:window|…')`, crate `serialize-to-javascript 0.1.2`, `socket2 0.6.2`, `image 2.10.3`; sumber Rust `src\commands\backend.rs` | Jendela desktop, webview, supervise backend |
| **2. Backend HTTP lokal** | `"Starting backend with bundled JRE…"`, `"Backend started on port: "`, `"CRITICAL: Port 8080 is already in use by another process!"`, `"Navigate to: http://127.0.0.1:<port>"` | Spring Boot + Jetty di `127.0.0.1:8080` |
| **3. Engine PDF** | `pdfbox-3.0.8`, `preflight-3.0.8`, `xmpbox-3.0.8`, `pdf-model/parser-1.30.2`, `jpdfium-1.1.6` + `jpdfium-natives-windows-x64-1.1.6` | PDFBox (baca/tulis) + PDFium (render) + Preflight (validasi PDF/A) |
| **4. Tool eksternal** | "Pre/Post-Ghostscript file size", "Pre/Post-QPDF file size", flag Ghostscript `-dBATCH`, `processWithTesseract`, `ExternalAppDepConfig` | Kompresi, OCR, konversi Office — **tidak dibundel** di installer Windows |

### 3.2 Shell Tauri — detail dari string & import

Bukti import PE (26 DLL, 340+ fungsi) menunjukkan karakter shell desktop, bukan sekadar
pemungkus browser:

| Import | Fungsi yang terlihat |
|---|---|
| `user32.dll` (120 fn) | Jendela, menu, akselerator, input keyboard (`GetKeyState`, `GetAsyncKeyState`, `GetKeyboardLayout`, `MapVirtualKeyExW`), `ToUnicodeEx` |
| `comctl32.dll` | `TaskDialogIndirect` (dialog native), `SetWindowSubclass` |
| `dwmapi.dll` | `DwmEnableBlurBehindWindow`, `DwmSetWindowAttribute` (efek visual) |
| `gdi32.dll` | `CreateDIBSection`, `BitBlt`, `CombineRgn` (ikon & render) |
| `ole32.dll` | `RegisterDragDrop`/`RevokeDragDrop` (drag & drop file) |
| `shell32.dll` | `ShellExecuteW/Ex`, `SHGetKnownFolderPath`, `DragQueryFileW` |
| `advapi32.dll` | `CredRead/CredWrite/CredDelete` (Windows Credential Manager), registry |
| `crypt32.dll` | `CertOpenStore`, `CertVerifyCertificateChainPolicy`, `CertGetCertificateChain`, `CertVerifyTimeValidity` (verifikasi sertifikat) |
| `bcrypt.dll` | `BCryptGenRandom` (CSPRNG) |
| `ws2_32.dll` (21 fn) | `listen`, `bind`, `accept`, `connect`, `getaddrinfo` (komunikasi lokal) |
| `ntdll.dll` | `NtCreateFile`, `NtReadFile`, `NtCreateNamedPipeFile` |

Section PE: `.text` 15,8 MB · `.rdata` **38,1 MB** (aset web ter-embed) · `.pdata` 874 KB
(unwinding Rust) · `.reloc` 71,6 KB. Bukti tambahan: path build
`C:\Users\runneradmin\.cargo\registry\...` → dibangun di **GitHub Actions**.

Resource PE `Stirling-PDF.exe`: 10 entri — 7 ikon (`id:3`), 1 group icon (`id:14`),
1 version (`id:16`), 1 manifest (`id:24`).

### 3.3 Thumbnail handler (Rust)

- 653 prosedur, 285 string, 6 segment (Ghidra 12.1.4, PE32+ x86_64).
- String khas Rust: `rustc/58cf8f9c35b355199727627d07ae34a4e2846d67/library\...`,
  `fatal runtime error: Rust panics must be rethrown, aborting`,
  `thread caused non-unwinding panic. aborting.`
- Mengacu ke `ws.Data.Pdf.PdfPageRenderOptions` → memakai pustaka PDF/.NET untuk merender
  pratinjau halaman, di dalam handler COM shell Explorer.
- Import: `CreateDIBSection` (bitmap), `SHCreateMemStream` (stream COM), `RoGetActivationFactory`
  (WinRT), `CoCreateInstance`.

### 3.4 Modul `common` (paket `common-3.2.0-plain.jar`, 470 entri)

Tiga kelompok isi:

1. **Klien OpenAPI** (antarmuka): `AccountSecurityApi`, `AdminApi`, `AdminServerCertificateApi`,
   `AnalysisApi`, `ConfigApi`, `ConvertApi`, `DatabaseApi`, `DatabaseManagementApi`,
   `FilterApi`, `GeneralApi`, `InfoApi`, `InviteApi`, `MiscApi`, `PipelineApi`,
   `ProprietaryUiDataApi`, `SecurityApi`, `SettingsApi`, `TeamApi`, `UiDataApi`, `UserApi`.
   → API didokumentasikan **di dalam kode** (generik/ber anotasi), bukan hanya via Swagger.
2. **Cluster**: `ClusterBackplane`, `DistributedLock`, `FileStore`, `HostPort`,
   `ClusterNode`, plus implementasi `cluster/inprocess/*` (default) dan
   `ClusterBackplane` untuk Valkey/Redis (opsional).
3. **Infrastruktur job**: `JobController`, `JobOwnershipCache`, `JobExecutorService`,
   `TaskManager`, `CustomPDFDocumentFactory`, `TempFileManager`, `AutoJobAspect`
   (AOP untuk otomatis mencatat job), `model/api/PDFFile`.

Implikasi: arsitektur yang sama dipakai untuk **desktop tunggal** maupun **server tim**
(berubah via backplane in-process → Valkey).

---

## 4. Konfigurasi, keamanan, privasi

### 4.1 `application.properties` (6.338 byte, dari JAR)

| Area | Nilai | Catatan |
|---|---|---|
| Basis data | `jdbc:h2:file:./configs/stirling-pdf-DB-2.3.232;MODE=PostgreSQL` | H2 embedded, `ddl-auto=update`, konsol H2 **dimatikan** |
| Threading | `spring.threads.virtual.enabled=true` | virtual thread (Java 21+), catatan: pinning fix di Java 25 |
| HTTP/2 | `server.http2.enabled=true` | multiplexing + kompresi header |
| Batas unggah | `spring.servlet.multipart.max-file-size=${…:2000MB}` | default **2.000 MB** |
| Form Jetty | `server.jetty.max-http-form-post-size=10MB` | cukup untuk gambar tanda tangan |
| Async | `spring.mvc.async.request-timeout=${…:1200000}` | 20 menit |
| Sesi | `server.servlet.session.timeout:30m`, `tracking-modes=cookie` | cookie session |
| Error | `spring.web.error.include-stacktrace=always`, `include-exception=true`, `include-message=always` | **stack trace ikut dikembalikan ke klien** |
| ProblemDetails | `spring.mvc.problemdetails.enabled=false` | dipakai `GlobalExceptionHandler` sendiri (RFC 7807) |
| OpenAPI | `/v1/api-docs`, Swagger UI `/swagger-ui.html` | didokumentasikan + UI |
| Redis | `spring.autoconfigure.exclude=…DataRedis…` | dimatikan default; opsional Valkey |
| Telemetri | `posthog.api.key=phc_<DISAMARKAN>`, `posthog.host=https://eu.i.posthog.com` | **project token PostHog tertanam** (bukan personal API key; lihat catatan redaksi) |
| Model bisnis | `stirling.billing.account-link.enabled=true` | tautan akun berbayar aktif default |
| Fitur | `v2=true` | sakelar versi fitur |
| Devtools | `spring.devtools.restart.enabled=true`, `livereload.enabled=true` | **default dev aktif di artefak rilis** |

### 4.2 Model autentikasi & otorisasi

Dari konstanta kelas:

| Mekanisme | Bukti |
|---|---|
| Login opsional (`security.enableLogin`) | `ConfigController.isEnableLogin`, `WAUTrackingFilter.security.enableLogin` |
| OAuth2 / OIDC | `enableOAuth`, `getOauth2`, `OAUTH2`, `SSOAutoLogin` |
| CSRF | `X-CSRF-TOKEN` + `allowCredentials` di `WebMvcConfig` |
| Password dokumen | `honorOwnerPasswords` / `isHonorOwnerPasswords` (password owner PDF dihormati) |
| Disclaimer login | `LoginDisclaimerController` → markdown per bahasa |
| Sesi | `spring.servlet.session.tracking-modes=cookie`, timeout 30 m |
| Tim & undangan | `/api/v1/team/**`, `/api/v1/invite/**`, `JobOwnershipCache` (kepemilikan job per pengguna) |
| Admin | `/api/v1/admin/**` (termasuk sweep job semua pengguna) |

### 4.3 Model password PDF (detail)

`PdfSessionSecurityController` + `PasswordController` menunjukkan pemisahan yang **sangat
rinci** antara password pembuka dan password izin:

| Pernyataan tertanam | Makna |
|---|---|
| "The opening password is incorrect or is not set" | password pembuka != password izin |
| "The opening and permissions passwords must remain distinct after PDF encoding" | ada **verifikasi setelah** enkripsi bahwa keduanya tidak sama |
| "Restrictions require a nonempty permissions password different from the opening password" | password izin wajib terisi & berbeda |
| "Verify the permissions password to retain it while removing the opening password" | penghapusan password pembuka harus diverifikasi terpisah |
| "Open the PDF with its opening password before removing only the permissions password" | operasi dibedakan secara eksplisit |
| `credentialFingerprint` | sidik jari kredensial disimpan (untuk mengenali password lama) |

Model ini **lebih ketat** dari deskripsi yang ditemukan pada Nitro (§4.4 dokumen Nitro),
yang hanya menyebut "open password" vs "permissions password" tanpa aturan keunikan.

### 4.4 Telemetri & model bisnis

| Aspek | Bukti | Catatan |
|---|---|---|
| PostHog | `posthog-1.2.0.jar`, `postHogService` di `PdfMetricsService`, `MetricsAggregatorService`, `PipelineController` | project token **tertanam di konfigurasi** |
| Sakelar | `system.enableAnalytics`, `getEnableAnalytics`, `setEnableAnalytics`, `enablePosthog` | bisa dimatikan lewat UI |
| Event | `pdf_operation_metrics`, `aggregated_metrics`, `lastSentMetrics` | metrik per operasi PDF, dikirim teragregasi |
| WAU | `WAUTrackingFilter`, "WAU tracking is only available when security is disabled (no-login mode)" | penghitung pengguna aktif mingguan, **hanya** saat login dimatikan |
| Halaman UI | `MetricsController.getMetrics`, `metricsEnabled` | UI metrik internal |
| Lisensi | `getLicenseType`, `getLicenseTypeName`, `getPremium`, `premiumEnabled`, `licenseType`, `accountLinkAvailable` | tier lisensi dibaca server |
| Kontak | `stirling.billing.account-link.enabled=true`, `CleanUrlInterceptor.accountLinkCallback` | callback linking akun |
| Open-core | `OpenApiConfig` deskripsi "Open-Core - MIT Licensed"; `spring.devtools.restart.exclude=stirling.software.proprietary.security/**` | paket proprietary terpisah |

> Untuk UnionPDF, dua hal ini berlawanan dengan tujuan proyek: (a) telemetri ada dan
>-default-nya untuk analytics menyala, (b) `stacktrace=always` filtración detail internal
> ke klien. Keduanya tercatat di sini sebagai **fakta artefak**, bukan rekomendasi.

---

## 5. Permukaan fitur

### 5.1 Ringkasan domain (dari 177 controller)

| Domain | Controller kunci |
|---|---|
| **Operasi halaman** | `MergeController`, `RearrangePagesPDFController`, `RotationController`, `ScalePagesController`, `CropController`, `SplitPDFController`, `SplitPdfByChaptersController`, `SplitPdfBySectionsController`, `SplitPdfBySizeController`, `ToSinglePageController`, `BookletImpositionController`, `MultiPageLayoutController`, `PosterPdfController` |
| **Edit teks & JSON** | `EditTextController` (+`CompiledEdit`, `MatchSpan`), `PdfTextEditorCharcodeController` (+`ResourceFont`, `BoundedReverseMapCache`), `ConvertPdfJsonController`, `EditTableOfContentsController` |
| **Formulir** | `form.FormFillController` (+`FormPayloadParser`, `FieldEditBatch`), `misc.UnlockPDFFormsController` |
| **Tanda tangan & sertifikat** | `security.CertSignController` (+`Pkcs11Session`, `CreateSignature`), `security.HardwareSigningController`, `security.ValidateSignatureController`, `security.RemoveCertSignController`, `security.TimestampController`, `misc.AddCommentsController` |
| **Keamanan** | `security.PasswordController`, `security.PdfSessionSecurityController`, `security.RedactController` (+`RedactExecuteService`, `TextRedactionService`, `MultiPatternTextFinder`, `ManualRedactionService`, `AllTextLineExtractor`), `security.SanitizeController`, `security.WatermarkController`, `security.VerifyPDFController`, `security.GetInfoOnPDF`, `security.ValidateComplianceController` |
| **Konversi** | `converters.ConvertPDFToOffice`, `ConvertOfficeController`, `ConvertPDFToExcelController`, `ConvertPDFToEpubController`, `ConvertPDFToHtml`, `ConvertHtmlToPDF`, `ConvertWebsiteToPDF`, `ConvertMarkdownToPdf`, `ConvertSvgToPDF`, `ConvertEmlToPDF`, `ConvertEbookToPDFController`, `ConvertImgPDFController`, `ConvertPDFToPDFA`, `ConvertPdfToVideoController`, `PdfVectorExportController`, `ExtractCSVController` |
| **OCR** | `misc.OCRController`, `misc.AutoRotateController`, `utils.AutoRotateDetection` |
| **Kompresi & gambar** | `misc.CompressController` (+`CompressionStats`, `ImageFingerprint`), `misc.DecompressPdfController`, `misc.ExtractImagesController`, `misc.RemoveImagesController`, `misc.OverlayImageController`, `misc.ScannerEffectController`, `misc.ReplaceAndInvertColorController` |
| **Metadata & perbaikan** | `misc.MetadataController` (metadata standar + kustom), `misc.RepairController`, `misc.FlattenController`, `misc.PortfolioController`, `misc.AttachmentController` (+`BatchOpsData`, `RenameOp`), `misc.AutoRenameController`, `misc.AutoSplitPdfController`, `misc.StampController`, `misc.PageNumbersController`, `misc.BlankPageController`, `misc.PrintFileController`, `misc.ShowJavascript` |
| **Pipeline & batch** | `pipeline.PipelineController`, `pipeline.PipelineDirectoryProcessor` (+`PipelineProcessor`), `common.controller.JobController` |
| **Analisis** | `AnalysisController` (halaman, versi, ukuran, enkripsi, izin, tanda tangan), `api.Bookmark`, `api.filters.FilterController`, `api.AdditionalLanguageJsController` |
| **Sistem** | `api.SettingsController`, `api.misc.ConfigController`, `api.UIDataController` (+`HomeData`, `FooterData`, `LicensesData`, `OcrData`, `SignData`, `PipelineData`, `FontResource`), `web.MetricsController`, `web.RobotsController`, `web.ReactRoutingController`, `web.SignatureImageController`, `web.UploadLimitService` |
| **Mobile** | `misc.MobileScannerController` (sesi unggah pindai dari ponsel) |

### 5.2 Jalur API literal (47 unik, contoh)

```
/api/v1/general/merge-pdfs          /api/v1/general/rearrange-pages
/api/v1/general/remove-pages        /api/v1/general/rotate-pdf
/api/v1/general/split-pages         /api/v1/general/split-by-size-or-count
/api/v1/general/split-pdf-by-chapters  /api/v1/general/split-pdf-by-sections
/api/v1/general/split-for-poster-print  /api/v1/general/signatures/**
/api/v1/misc/compress-pdf           /api/v1/misc/auto-split-pdf
/api/v1/misc/repair                /api/v1/security/sanitize-pdf
/api/v1/security/cert-sign/hardware /api/v1/security/cert-sign/sessions
/api/v1/security/cert-sign/sign-requests  /api/v1/security/cert-sign/validate-certificate
/api/v1/admin/**  /api/v1/audit/**  /api/v1/auth/**  /api/v1/database/**
/api/v1/filter/filter-             /api/v1/form       /api/v1/general/files/**
/api/v1/general/job/**             /api/v1/info/**    /api/v1/invite/**
/api/v1/misc                       /api/v1/mobile-scanner  /api/v1/proprietary/**
/api/v1/security                   /api/v1/settings/**  /api/v1/storage/**
/api/v1/team/**                    /api/v1/ui-data/**  /api/v1/user/**
/api/v1/workflow/participant/**
```

Dokumentasi REST tersedia di dalam paket (`springdoc-openapi-starter` + `swagger-ui-5.32.2`),
dan **OpenAPI client interface-nya juga tertanam di modul `common`** — API ini
dirancang untuk dipakai program lain, bukan hanya UI.

### 5.3 Permukaan UI (React, code-split per fitur)

Nama chunk aset di `.rdata` shell Tauri menunjukkan pemetaan fitur 1:1 (84 chunk unik: 74 JS + 10 CSS):

`AddAttachmentsSettings` · `AddPageNumbersAppearanceSettings` · `AddPageNumbersAutomationSettings`
· `AddStampAutomationSettings` · `AddWatermark` + `AddWatermarkSingleStepSettings` ·
`AdjustContrastColorSettings` · `AdjustPageScaleSettings` · `AutoFormDetectionSettings` ·
`AutoRotateAutomationSettings` · `BillingSettingsSection` · `BookletImpositionSettings` ·
`CertSign` + `CertSignAutomationSettings` · `ChangePermissionsSettings` · `Compress` ·
`Convert` + `ConvertSettings` · `CreatePortfolio` + `CreatePortfolioSettings` ·
`CropAutomationSettings` · `ExtractImagesSettings` · `ExtractPagesSettings` ·
`FlattenSettings` · `GetPdfInfo` · `Merge` + `MergeSettings` · `MobileSignPage` ·
`OCR` + `OCRSettings` · `Onboarding` + `onboardingFlowConfig` · `OverlayPdfs` ·
`PdfTextEditor` (+`pdf.worker.min.js` → pdf.js di sisi browser) · `PortalRosterLinkFlow` ·
`portalSettingsSections` · `CreatePortfolio` · `de--4oxyX1l.js` (chunk locale).

Artefak tambahan: `pdf.worker.min.js` (pdf.js) → pemrosesan sebagian PDF terjadi **di
browser**, bukan di server.

### 5.4 Model pipeline (otomatisasi)

`PipelineController` + `PipelineDirectoryProcessor`+gambar:

- `runPipelineAgainstFiles` — menjalankan rangkaian operasi atas berkas.
- Watched folders: `getPipelineWatchedFoldersPaths`, `getPipelineFinishedFoldersPath`,
  retry bila berkas "still being written or locked".
- Contoh pipeline dari literal konstanta:
  `{"name":"Prepare-pdfs-for-email","pipeline":[{"operation":"/api/v1/misc/repair"},{"operation":"/api/v1/security/sanitize-pdf","parameters":{"removeJavaScript":true,"removeEmbeddedFiles":false}},{"operation":"/api/v1/misc/compress-pdf","parameters":{"optimizeLevel":2}}]}`
- Integrasi luar: `TelegramPipelineBot` ("Telegram pipeline bot registered as {}"),
  event `pipeline_api_event`, `pipeline_directory_event`.

---

## 6. Engine PDF, tool eksternal, dan batasan platform

### 6.1 PDFBox + PDFium

| Komponen | Peran |
|---|---|
| `pdfbox-3.0.8`, `pdfbox-io-3.0.8` | baca/tulis struktur PDF |
| `preflight-3.0.8` | validasi (induknya PDF/A Preflight) |
| `xmpbox-3.0.8`, `verapdf-xmp-core-1.30.2` | metadata XMP untuk PDF/A |
| `pdf-model-1.30.2`, `parser-1.30.2`, `metadata-extractor-2.21.0`, `metadata-fixer-1.30.2` | model & metadata |
| `jpdfium-1.1.6` + `jpdfium-natives-windows-x64-1.1.6` (+ `linux-x64`) | render raster via PDFium (bukan Java) |
| `fontbox-3.0.8`, `xmlgraphics-commons-2.11` | font & graphic |

Konversi PDF/A punya pipeline sanitasi sendiri
(`ConvertPDFToPDFA$DocumentSanitizer`): "Flatten highlight annotations",
"Sanitize font resources", "Clean metadata", "XMP metadata is required for …",
"PDF sanitized with PDFBox for better Ghostscript compatibility", plus
`upgradeToLevelA` (PDF/UA).

### 6.2 Tool eksternal — yang TIDAK dibundel

| Tool | Bukti | Dampak di Windows |
|---|---|---|
| **Ghostscript** | "Pre-Ghostscript file size: {}", "Post-Ghostscript file size: {} (reduced by {}%)", flag `-dBATCH`, "PDF sanitized with PDFBox for better Ghostscript compatibility" | kompresi/raster perlu Ghostscript terpasang |
| **QPDF** | "Pre-QPDF file size: {}", "Post-QPDF file size: {} (reduced by {}%)" | optimasi struktural perlu QPDF |
| **Tesseract** | `ExternalAppDepConfig.tesseract`, `processWithTesseract`, `getAvailableTesseractLanguages`, `tesseractAvailable/Unavailable` | OCR bergantung tool eksternal + daftar bahasa dari Tesseract |
| **OCRmyPDF (kompatibilitas)** | tipe OCR `skip-text` / `force-ocr` / `Normal`, render `hocr` / `sandwich`, "--force-ocr", "Minimum Tesseract OSD orientation confidence … Matches OCRmyPDF's --rotate-pages-threshold scale", "Include OCR text in a sidecar text file" | semantik mengikuti OCRmyPDF, bukan engine bawaan |
| **LibreOffice/Office** | `stirling-office-convert-0.2.2` (3 artefak: base, legacy, topdf), `OfficeToPdfService`, `ExternalAppDepConfig` | konversi Office bergantung tool eksternal |
| **SAXON, Batik, POI** | `Saxon-HE-12.8`, `batik-1.19` (SVG), `poi-5.5.1` (+`poi-ooxml`, `poi-scratchpad`) | dokumen lain diproses di server (bukan client) |

**Installer Windows tidak memuat satupun binary di atas** (5 berkas saja + JRE) — fitur
berat tersebut bergantung lingkungan host pengguna.

### 6.3 Model konversi teks editable (unik)

Terdapat **dua** jalur editing teks:

1. **Edit teks pada PDF** (`EditTextController`) dengan `CompiledEdit`/`MatchSpan`.
2. **Model JSON** (`ConvertPdfJsonController`): "Extracts PDF text, fonts, and metadata into
   an editable JSON structure for the text editor tool", dengan
   `PdfJsonConversionService` + `Type3FontConversionService` (`registerType3GlyphCoverage`,
   "[TYPE3] No conversion strategies registered for font {}", "Registered conversion
   candidate payload … (format=…, size=… bytes)") serta
   `PdfTextEditorCharcodeController` (pemetaan charcode ↔ font, `PendingResources`).

Ini pola "bawa dokumen ke model data, edit di model, tulis kembali" — berbeda dari
approach Nitro yang berbasis content-stream.

---

## 7. Stack pihak ketiga & lisensi

### 7.1 Dependency utama (dari 248 JAR)

| Area | Dependency |
|---|---|
| Framework | Spring Boot **4.1.1**, Spring Framework **7.0.9**, Jetty **12.1.12** (embedded), Micrometer 1.17.1 |
| PDF | PDFBox **3.0.8**, jpdfium 1.1.6, preflight 3.0.8, xmpbox 3.0.8, verapdf-xmp-core 1.30.2, tabula 1.0.5 (tabel), junrar 8.0.0 (RAR), metadata-extractor 2.21.0 |
| Dokumen lain | Apache POI **5.5.1** (+ooxml, scratchpad), **Saxon-HE 12.8** (XSLT), Batik 1.19 (SVG), flexmark 0.64.8 (Markdown), rhino 1.9.1 (JS), tabula, opencsv 5.12.0, rtf-to-html 2.0.2, outlook-message-parser 1.16.2 |
| Gambar | ImageIO core 3.15.2 (+bmp, jpeg, psd, tiff, webp), JAI-ImageIO 1.4.0 (+JPEG2000), jbig2-imageio 3.0.5, curvesapi 1.08, commons-image 3.15.2 |
| Kripto | BouncyCastle **1.85** (bcpkix/bcprov/bcutil), java-security-toolkit 1.2.3 |
| Keamanan web | owasp-java-html-sanitizer 20260924.2, bucket4j 8.19.0 (rate limit), hibernate-validator 9.1.3, jakarta.* 3.x/6.x |
| API | springdoc-openapi 3.0.3, swagger-ui 5.32.2, jackson 2.21.5 **dan** 3.1.5 |
| Integrasi | telegrambots 6.9.7.1, simple-java-mail 9.3.5, angus-mail 2.0.5, httpclient 4.5.14 |
| Observability | logback 1.6.3, log4j-api 2.25.5, slf4j 2.0.18, Micrometer + actuator |
| Analitik | **posthog 1.2.0** |
| Util | Guava 33.6.0, gson 2.14.0, commons-*, snakeyaml 2.6, javax.mail |

> Depensi versi ganda Jackson (2.21.5 + 3.1.5) dan `javax.*` + `jakarta.*` menandakan
> masa transisi migrasi yang belum tuntas.

### 7.2 Lisensi

- **Inti: MIT** (open-core). Deskripsi OpenAPI di dalam aplikasi: "Open-Core - MIT Licensed".
- Paket `stirling.software.proprietary.*` → fitur berbayar di modul terpisah.
- `common-3.2.0-plain.jar` → modul inti (lisensi mengikuti proyek).
- `certdata.txt` → **Mozilla Public License 2.0** (basis data sertifikat NSS).
- BouncyCastle MIT, tabula MIT, POI/Apache-2.0, Saxon dual (MPL/SAX-PD), Batik BSD-3,
  flexmark BSD-2, Tesseract Apache-2.0, Ghostscript GPL, QPDF Apache-2.0, PostHog SDK MIT.
- Scanner barcode: `idrsirisbarcode*` **tidak** ada di artefak ini (berbeda dari Nitro).

> Signifikansi lisensi: Ghostscript **GPL** muncul juga di Nitro (§2.5 dokumen Nitro) — dua
> target yang sama-sama menarik duty-cycle GPL bila downstream didistribusikan.

---

## 8. Batasan analisis & pertanyaan terbuka

### 8.1 Metode yang tidak dijalankan

| Metode | Status | Dampak |
|---|---|---|
| Observasi runtime (jalankan aplikasi, klik UI) | **NOT_RUN** | tidak ada bukti perilaku visual atau urutan langkah |
| Uji I/O (unggah PDF nyata → hasil) | **NOT_RUN** | mutu output konversi/OCR/kompresi **tidak** terukur |
| Decompilasi Java (JEB) | **TIDAK TERSEDIA** | `capability_unavailable`; JEB client tidak hidup dan tidak di-install. Analisis class dibatasi ke constant pool |
| Dekompilasi native shell 52,3 MB | **GAGAL (timeout)** | Ghidra 330 s habis; shell hanya dianalisis via PE + string |
| Analisis repo sumber | **NOT_RUN** | analisis murni dari artefak;banyak perilaku hanya dapat disimpulkan |
| Jaringan (panggilan API) | **NOT_RUN** | tidak ada permintaan ke server |

### 8.2 Unknown

| ID | Pertanyaan | Status |
|---|---|---|
| S-01 | Apa persisnya algoritma enkripsi PDF (RC4/AES, V/R) yang dipakai? | **TERBUKA** — hanya terlihat dari `PdfSessionSecurityController`; implementasi PDFBox tidak dianalisis |
| S-02 | Bagaimana `stirling.software.proprietary.*` menggate fitur premium? | **TERBUKA** — paket proprietary tidak ada di JAR open-core ini |
| S-03 | Apakah shell Tauri bisa berjalan tanpa JRE lokal / mode self-hosted? | **TERBUKA** — string "Running in Self-Hosted mode" menunjukkan jalur alternatif, tapi alurnya tak teramati |
| S-04 | Bagaimana pipeline folder dipicu dan apa format settings.yml? | **TERBUKA** — `settings.yml` dirujuk komentar konfigurasi, tidak ada di JAR (dibuat saat runtime) |
| S-05 | Berapa lama dan seberapa andal OCR via Tesseract pada dokumen besar? | **NOT_MEASURED** |
| S-06 | Bagaimana pdf.js di browser dipakai berdampingan dengan server? | **HYPOTHESIS** — keberadaan `pdf.worker.min.js` + `PdfTextEditor`/lazy loading metadata |
| S-07 | Apakah backend mengikat antarmuka jaringan selain loopback? | **TERBUKA** — string Tauri memakai `127.0.0.1`; binding server tidak teramati |
| S-08 | Apa perilaku pasti saat tool eksternal (gs/qpdf/tesseract) tidak ada? | **TERBUKA** — string error ada ("Tesseract did not create expected output file", "Unsupported" ), tapi jalur fallback tidak teramati |

### 8.3 Cakupan bukti

- **Kuat**: inventaris arsip & dependensi, komposisi class, jalur API, konfigurasi,
  string shell, profil PE, versi library.
- **Sedang**: nama method/literal string (constant pool) — kuat untuk *apa* yang ada,
  lemah untuk *bagaimana*.
- **Lemah/tidak ada**: perilaku runtime, mutu keluaran, performa, kualitas konversi.

---

## 9. Lampiran

### 9.1 Indeks bukti REA (S-001 …)

| ID | Operasi | Target | Hasil kunci | Evidence ID |
|---|---|---|---|---|
| S-001 | `open_binary` | `stirling-pdf-3.2.0.jar` | ZIP, SHA-256 `e3ebb751…` | — |
| S-002 | `inspect_artifact` (summary) | JAR | 1.111 node, 1.137 occurrence, 1.136 edge, 1.056 file + 81 dir, 0 kontradiksi | `ev_a40ca11348f7ed28100172ea74e2942abc3edb203a2a3239a5e43c158ac52b63` |
| S-003 | `inspect_artifact` (lengkap, induk) | JAR | coverage `complete-within-view` (3.384/3.384) | `ev_1de8f70fa49fa941aab2de878db5ad0312aa27121080cd277cb1196f483cb4e1` |
| S-004 | `inventory_artifact` (substep) | JAR | inventaris entri ZIP | `ev_ce91b519eea46712b585dc17804bdc978fb1e09a87c66f51f5981b682fbed361` |
| S-005 | `open_binary` | `Stirling-PDF.exe` | PE32+ x86_64, SHA-256 `2a5a74c6…` | — |
| S-006 | `inspect_pe_resources` | `Stirling-PDF.exe` | 10 resource (7 ikon, group icon, version, manifest), 1 icon group | `ev_ebe620c87b8ae43f9398b4243be24817ec1e30b5eb79eb3fb47a00fafb90ee92` |
| S-007 | `open_binary` | `stirling_thumbnail_handler.dll` | PE32+ x86_64, SHA-256 `16f064ed…` | — |
| S-008 | `inspect_pe_resources` | thumbnail DLL | 0 resource (DLL murni kode) | `ev_0ace9f35c2c28d5ed0854e91f81b7e18a7cee6a771b12a35ae2fce8cf86e49bc` |
| S-009 | `binary_overview` (Ghidra) | thumbnail DLL | **653 prosedur**, 285 string, 6 segment | `ev_b6747ff923c64bcbcdb4286fd0a463aded7c41d5963f5bcbb3f8bc6cffbe0f1c` |
| S-010 | `list_procedures` / `list_strings` | thumbnail DLL | simbol & string Rust (`rustc/58cf8f9c…`, `ws.Data.Pdf.PdfPageRenderOptions`) | — |
| S-011 | `close_binary` (snapshot) | kedua target | snapshot 286.669 byte, 6 evidence record | — |
| S-012 | `open_binary` (ditolak) | `.msi` | `unsupported_target` / `file_format_rejected` | — |
| S-013 | `binary_overview` (gagal) | `Stirling-PDF.exe` | `provider_timeout` 330.000 ms | — |
| S-014 | `inspect_jeb_client` | — | `capability_unavailable` (tidak ada JEB serving MCP) | — |

Bukti non-REA (alat lokal, read-only): parser PE sendiri, parser constant pool class,
ekstraksi string ASCII/UTF-16, `msiexec /a` untuk ekstraksi payload, `Get-FileHash`.

### 9.2 Skrip verifikasi

`scripts/verify_stirling_artifact.py <path-jar> [path-exe]` menghitung ulang 9 angka kunci
dari artefak (entri ZIP, dependency, komposisi class, entri modul `common`, jalur API)
+ hitungan string shell, lalu mencocokkannya dengan nilai yang tertulis di dokumen.
Status terakhir: **10/10 OK (exit 0)**.

### 9.3 Ringkasan temuan

1. Shell Tauri/Rust + backend Spring Boot di `127.0.0.1:8080` + JRE 25 ter-bundel.
2. Fat JAR: 1.136 entri, 248 dependency, 476 class aplikasi, 177 controller, 47 jalur API.
3. Engine: PDFBox 3 + PDFium (native) + Preflight (PDF/A).
4. Fitur berat (OCR, kompresi, Office) bergantung tool eksternal yang **tidak** dibundel.
5. Model *open-core*: inti MIT + paket proprietary; tier lisensi & penagihan di server.
6. Telemetri PostHog dengan project token tertanam; sakelar `system.enableAnalytics`.
7. `stacktrace=always` pada respons error.
8. Redaksi & sanitasi sebagai fitur kelas satu, dengan eksekusi terstruktur
   (`RedactExecuteService` + `TextRedactionService` + `MultiPatternTextFinder`).
9. Model password PDF dua-lapis dengan aturan keunikan yang diverifikasi pasca-enkripsi.
10. Arsitektur designed for both: desktop tunggal & cluster (backplane in-process ↔ Valkey).

### 9.4 Catatan akhir

Semua angka berasal dari artefak read-only. Aplikasi tidak dijalankan; tidak ada permintaan
jaringan; tidak ada berkas uji yang diproses. Batasan terverifikasi: JEB tidak tersedia,
Ghidra timeout pada shell 52 MB. Yang tertulis di sini adalah **apa yang ada di dalam
artefak**, dengan label kepastian di setiap bagian — bukan klaim bahwa fitur tersebut
berfungsi atau menghasilkan keluaran bermutu tertentu.
