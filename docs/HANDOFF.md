# HANDOFF.md — Posisi Kerja

> Untuk sesi berikutnya. Baca bersama `PROJECT_STATE.md` dan `TASKS.md`.

**Sesi terakhir:** `2026-10-22T1400+0700` — 2026-10-22 (WIB, UTC+7)
**Fase:** M1 — viewer & authoring dasar berjalan; **scope reading tools, compact toolbar, bookmark, split, konversi masih berlanjut** (A–F baru diimplementasikan, belum "selesai")
**Sesi sebelumnya:** `2026-10-22T1400+0700` — `2026-10-22T0900+0700` — `2026-10-21T1215+0700`

> Cleanup aplikasi lama **BELUM DISETUJUI**. **Tidak ada commit/push** (G-2). Tidak ada
> perubahan lisensi, instalasi global, atau komponen berbayar. Sesi baru **tidak** berarti izin baru.

---

## 000. Posisi saat ini — sesi `2026-10-22T1400+0700` (checkpoint 15:10 WIB)

**Selesai:** continuous vertical scroll tervirtualisasi (default) + mode satu halaman · chrome
profesional (title bar, tab kategori, command bar kontekstual, sidebar, status bar, ikon sendiri)
· runtime Java bundel via jlink (53,1 MB, tanpa Java eksternal) · paket portabel + installer NSIS
· **lapisan teks per halaman** (teks dapat dipilih) · **pemetaan koordinat anotasi teruji** ·
E2E UI **24 PASS + 1 NOT_RUN** (26 kasus) · pengukuran startup/scroll/authoring/cancel/memori/cache.

**Status implementasi (ringkas):** engine dipilih = PDFium + PDFBox (ADR-002); engine terintegrasi =
keduanya; backend teruji 26/26 + 20 uji unit; UI teruji 39 PASS + 1 NOT_RUN (40 kasus); belum diverifikasi =
drag mouse, prompt timpa Windows, DPI 125–200 %, multi-monitor, clean-install, redaksi.
Detail: `docs/PROJECT_STATE.md` §"Status implementasi" · `docs/sessions/2026-10-22T1400+0700.md`.

**Penting:** PDFBox **sudah** backend authoring aktif (worker Java, IPC JSON-lines, dipakai untuk
extract/merge/form/anotasi) — bukan lagi rencana.

### Menjalankan (dari `apps/desktop`)

```powershell
npm install                                                                  # sekali
powershell -ExecutionPolicy Bypass -File scripts\prepare-pdfium.ps1         # sekali
powershell -ExecutionPolicy Bypass -File scripts\prepare-pdfbox.ps1         # sekali (butuh JDK 8+)
powershell -ExecutionPolicy Bypass -File scripts\prepare-java-runtime.ps1   # sekali (jlink, unduh JDK 17)
$env:CARGO_HOME = "$PWD\.cargo-home"
npm run tauri dev                                                            # mode dev
npm test                                                                      # typecheck + 8 uji layout
cargo test --manifest-path src-tauri\Cargo.toml                            # 21 test backend
npx tauri build --no-bundle --features e2e-hooks                            # build untuk E2E UI
powershell -ExecutionPolicy Bypass -File scripts\ui-e2e.ps1                 # E2E UI (18 PASS, 1 NOT_RUN)
powershell -ExecutionPolicy Bypass -File scripts\measure-interaction.ps1    # pengukuran interaksi
```

Release + paket:
```powershell
npx tauri build --no-bundle            # release tanpa hook uji
powershell -ExecutionPolicy Bypass -File scripts\stage-release.ps1
powershell -ExecutionPolicy Bypass -File scripts\package-standalone.ps1   # dist-package + ZIP
npx tauri build                        # installer NSIS (tidak dijalankan otomatis)
```
Uji paket: `scripts\test-package.ps1`, `scripts\test-no-external-java.ps1`,
`scripts\test-bundled-jre.ps1`.

### Strategi WebView2

Runtime **evergreen** (dipakai bersama, ±130–180 MB, komponen OS, tidak dibundel). Installer memakai
`downloadBootstrapper` → internet hanya bila OS belum punya WebView2. Opsi fully offline:
`offlineInstaller` (+±127 MB). Rincian: `apps/desktop/docs/WEBVIEW2-STRATEGY.md`.

### Isu teknis yang perlu diingat

- Jangan panggil `stroke_color()` pdfium-render (access violation pada anotasi ber-`/AP`);
  regression: canary `stroke_color_crash_canary` di `ops.rs`.
- Operasi panjang **tidak boleh** memegang `docs` mutex (UI beku + pohon a11y WebView2 melambat);
  `save_as` sudah memakai snapshot — pola yang sama dipakai untuk operasi baru.
- CSP harus memuat `connect-src ipc: http://ipc.localhost` agar respons biner IPC berfungsi.
- Dialog Windows "Confirm Save As" (TaskDialog) hanya merespons keyboard sungguhan → E2E tidak
  mengetiknya; skenario itu NOT_RUN (manual M-11).
- Worker PDFBox butuh Java: saat ini memakai OpenJDK 17 milik instalasi lain (`JAVA_HOME`).
  Untuk distribusi: `docs/BLOCKERS.md` B-RT1 (Menunggu Persetujuan).

### Peta permintaan → bukti (Prioritas A–F)

Lihat `docs/sessions/2026-10-22T1900+0700.md` §"Peta permintaan" (36 baris: permintaan →
implementasi → bukti test → batasan). Ringkas: A (toolbar collapse, sidebar kiri/kanan, compact,
tinggi header) ✓ · B (pencarian seluruh dokumen + highlight + case-sensitive) ✓ · C (auto-scroll
waktu-based) ✓ · D (bookmark hierarki + penanda baca pribadi; salin/paste & first/last NOT_RUN) ·
E (merge daftar berkas + split 3 mode; penulisan berkas via dialog common NOT_RUN) ·
F (PDF→PNG/TXT terbukti; JPEG & gambar→PDF NOT_RUN).

### Deliverable & ruang

Paket mandiri: `apps/desktop/dist-package/UnionPDF-0.1.0/` (klik dua kali) · installer:
`apps/desktop/dist-package/UnionPDF_0.1.0_x64-setup.exe` · workspace 12,70 GB → 0,94 GB
(artefak build dapat direproduksi; lihat `docs/sessions/2026-10-22T1400+0700.md`).

Untuk membangun ulang dari sumber: `npm install` → `scripts\prepare-pdfium.ps1` →
`scripts\prepare-pdfbox.ps1` → `scripts\prepare-java-runtime.ps1` → `npx tauri build --no-bundle`
→ `scripts\stage-release.ps1` → `scripts\package-standalone.ps1`.

### Langkah berikutnya (konkret)

1. **Uji manual pengguna**: `apps/desktop/MANUAL_TEST.md` M-01…M-24 (scroll manual, anotas
   dengan mouse, prompt timpa, DPI 125–200 %, clean-install installer).
2. UPDF-051 reordering bidi untuk teks RTL (PDFium mengembalikan urutan visual).
3. UPDF-053: jenis anotasi lain (kotak/poligon/garis) + preflight untuk reorder halaman.
4. Continous scroll: tambahkan **text/selection layer** per halaman (belum ada) dan caret
   navigasi keyboard; pertahankan anchor saat jendela di-resize.
5. Redaksi: tetap ditunda; jangan mengklaim *secure redaction* sebelum fixture `rs07` lolos.

---

## 000. Posisi saat ini — sesi `2026-10-21T1215+0700` (checkpoint 12:30 WIB)

**Selesai:** G-7 lint · fixture v2 · pembandingan PDFium/MuPDF/PDFBox (`experiments/restart/results/SUMMARY.md` §9)
· provenance PDFBox/BC (`deps/PROVENANCE.md` §7) · ADR-002 · vertical slice `apps/desktop/`.

**Aplikasi `apps/desktop/`** (Tauri 2.12.4 + React 19.3.1 + Vite 8.3.4 + TS 7.0.2, Rust, PDFium 7881):
- Rust `src-tauri/src/`: `lib.rs` (command + event `job-progress` + `startup_file`), `engine.rs`
  (trait `PdfEngine`/`PdfDoc` + PDFium), `ops.rs` (workspace, `verify_output`, test integrasi),
  `atomic.rs` (Save As atomik), `pages.rs` (parser "1-3, 5, 8-"), `jobs.rs` (cancel), `error.rs`.
- Frontend `src/`: `App.tsx`, `api.ts`, `types.ts`, `styles.css`, `components/{PageCanvas,Thumbnails,Logo}.tsx`.
- Skrip: `scripts/prepare-pdfium.ps1` (salin/unduh DLL + cek SHA-256), `scripts/smoke-window.ps1`.
- Bisa dipakai: buka (dialog / argumen CLI), render, navigasi, zoom ±/Lebar/Halaman, thumbnail lazy,
  pesan error spesifik, putar halaman (in-memory → Simpan Sebagai), Simpan Sebagai, Ekstrak, Gabung —
  semua output dibuka ulang & diverifikasi sebelum menggantikan berkas tujuan; input tidak pernah ditimpa.
- Bukti: `cargo test` 12/12, typecheck, smoke visual 4/4 (`docs/sessions/2026-10-21T1215+0700.md`).
- **NOT_RUN:** klik UI interaktif untuk dialog/operasi; High-DPI; build release/installer.

**Menjalankan (dari `apps/desktop`):**
```powershell
npm install                                                   # sekali
powershell -ExecutionPolicy Bypass -File scripts\prepare-pdfium.ps1   # sekali
$env:CARGO_HOME = "$PWD\.cargo-home"
npm run tauri dev                                             # mode dev (Vite 127.0.0.1:1420)
cargo test --manifest-path src-tauri\Cargo.toml               # test backend
```

**Langkah berikutnya:** UPDF-049 worker PDFBox · UPDF-050 pemangkasan outline · UPDF-051 bidi RTL ·
UPDF-052 provider redaksi (BLOCKED: keputusan lisensi) · uji UI manual oleh pengguna.

**Peringatan teknis:** jangan panggil `stroke_color()` pdfium-render (access violation pada anotasi
ber-`/AP`); CSP wajib memuat `connect-src ipc: http://ipc.localhost` agar respons biner IPC berfungsi.

---

## 00. Posisi saat ini — sesi `2026-10-21T1114+0700` (checkpoint 11:42 WIB)

> **Stack final BELUM DISETUJUI. Cleanup aplikasi lama BELUM DISETUJUI.** Tidak ada push.
> `src/`, `tests/`, `spikes/` lama tetap utuh. Sesi baru tidak berarti izin baru.

**Langkah terakhir yang berhasil**
1. Keputusan A-1…A-9 diterapkan (redaksi, TASKS/indeks, milestone, `AGENTS.md` §5/§5b,
   kriteria v2 status REVIEW).
2. Commit lokal `2a1718a` (24 file, stage per file, tanpa push; `main` ahead 1).
3. Spike terbatas di `experiments/restart/`: RS-00 PASS; RS-01 sebagian besar PASS; bagian
   PDFium RS-02/RS-03 FAIL pada kriteria interoperabilitas; RS-05 PASS.
   Ringkasan: `experiments/restart/results/SUMMARY.md`.

**Langkah gagal / temuan penting**
- PDFium menulis anotasi baru sebagai objek langsung tanpa `/AP`; PDFium tidak merender
  markup/stamp buatannya sendiri.
- Setter form `pdfium-render 0.9.4` cacat (checkbox `/AS` string → halaman tak dapat dimuat
  PyMuPDF; radio no-op; tanpa setter choice; AP teks basi).
- Impor halaman ke dokumen baru membuang outline, tujuan link, `/AcroForm`.
- Tiga cacat fixture (Œ, Arab tanpa shaping, radio bukan grup) — `fixtures/FIXTURES.md`.

**File berubah setelah commit `2a1718a` (belum di-commit):** `experiments/restart/` (16 file
kandidat terlacak), `docs/TECH_SPIKES.md` §R.4, `docs/FEATURE_MATRIX.md` §13.5,
`docs/POST_ALL_REFERENCES_TECH_REVIEW.md` §2.8, `docs/STACK_EVALUATION.md` §10.7,
`docs/TASKS.md`, `docs/PROJECT_STATE.md`, `docs/CLEANUP_PLAN.md`, file ini, session log
`2026-10-21T1114+0700`.

### 00.1 Gate berikutnya — approval yang ditunggu

| ID | Keputusan | Pilihan |
|---|---|---|
| G-1 | Konfirmasi final urutan kriteria K2-1…K2-8 (`STACK_EVALUATION.md` §10.2b) | setuju / ubah |
| G-2 | Commit lokal tanpa push: `experiments/restart/` (16 file terlacak; biner, PDF, PNG, cache tetap di-gitignore) + pembaruan dokumen sesi ini | ya / tidak |
| G-3 | Perbaikan fixture (UPDF-045) + pembandingan **MuPDF** memakai PyMuPDF 1.27.2.2 yang sudah ada (tanpa instalasi baru): RS-02, RS-03 (+choice, radio grup), RS-04, RS-05 (+impor dengan struktur), RS-07, penelusuran kemampuan signing (RS-08) | ya / tidak / sebagian |
| G-4 | Pembandingan **PDFBox**: review RS-00-B lalu unduh PDFBox 3.0.x (`pdfbox`, `fontbox`, `pdfbox-io`, `commons-logging`; Bouncy Castle untuk RS-08) dari Maven Central/Apache dengan verifikasi checksum & tanda tangan penerbit; kompilasi dengan Zulu 8 JDK yang sudah ada; spike RS-02/03/04/05/07/08 | ya / tidak |
| G-5 | Opsional — pendalaman PDFium: jalur `FORM_*` native dan AP kustom (`FPDFAnnot_SetAP`) untuk menilai apakah gap baseline A dapat ditutup | ya / tidak |
| G-6 | Backup independen (opsi 1b `CLEANUP_PLAN.md`) | pilih lokasi / tunda |
| G-7 | `scripts/lint.py` kini memindai folder gitignored eksperimen (`.cargo-home/`, `deps/pdfium/`) → 10 temuan dari file pihak ketiga (file proyek: 0). Usulan: lint melewati path yang di-gitignore | ya / tidak |

### 00.2 Perintah berikutnya (aman, read-only)

```powershell
cd D:\dokumentasi\Project\UnionPDF
git status --short --untracked-files=all      # 1 commit ahead; experiments/ + docs termodifikasi
.\.venv\Scripts\python.exe scripts\lint.py    # read-only
```

Reproduksi spike: `experiments/restart/README.md` (butuh biner di `deps/pdfium/`, tidak
dilacak Git; provenance di `deps/PROVENANCE.md`).

### 00.3 Risiko

- Bukti mentah `experiments/restart/raw/` dan biner PDFium hanya ada lokal (gitignored).
- `rs01_unicode_arabic.pdf` menanamkan font sistem Arial — jangan pernah di-commit.
- Snapshot REA masih di folder temp sistem (belum ada backup independen).

### 00.4 Lima langkah kelanjutan

1. Tunggu jawaban G-1…G-6; diam ≠ persetujuan.
2. Bila G-2: commit per file daftar sesi ini (tanpa push).
3. Bila G-3: perbaiki fixture → jalankan verifier yang sama pada MuPDF.
4. Bila G-4: RS-00-B (provenance PDFBox) → spike PDFBox pada fixture yang sama.
5. Susun perbandingan A/B/C berbasis hasil → ajukan keputusan baseline (ADR baru).

### 00.5 Jangan diulang

- RS-00 untuk PDFium `chromium/7881` + `pdfium-render 0.9.4` (ulangi hanya bila versi berubah).
- Spike PDFium RS-01 & bagian PDFium RS-02/03/05 pada fixture saat ini (ulangi setelah fixture
  diperbaiki, khusus teks & radio).
- Verifikasi histori token/path (tidak ada di commit lokal sebelum `2a1718a`).

---

## 00-histori. Ringkasan awal sesi `2026-10-21T1114+0700`

Keputusan pengguna A-1…A-9 tercatat di `docs/PROJECT_STATE.md` § "Status persetujuan".
Diterapkan: redaksi dokumen analisis (A-3), perbaikan `TASKS.md` + indeks sesi (A-4),
mapping milestone (A-8), pembaruan terbatas `AGENTS.md` (A-9), kriteria v2 di
`STACK_EVALUATION.md` §10.2b (A-1, status REVIEW). Commit lokal (A-5) dan spike terbatas
(A-6/A-7): lihat `docs/sessions/2026-10-21T1114+0700.md`.

§0 di bawah adalah posisi GATE A revisi 1 (histori sesi `2026-10-21T1057+0700`);
PUB-1 dan DOC-1 yang disebut di sana sudah ditangani.

## 0. Posisi GATE A revisi 1 — controlled restart (2026-10-21, histori)

**Langkah terakhir yang berhasil:** audit read-only + proposal GATE A revisi 1 ditulis
dalam batas izin terbatas pengguna:
`docs/RESTART_AUDIT.md`, `docs/CLEANUP_PLAN.md`, `docs/POST_ALL_REFERENCES_TECH_REVIEW.md`
(baru); `docs/STACK_EVALUATION.md` §10, `docs/FEATURE_MATRIX.md` §13,
`docs/TECH_SPIKES.md` §R (ditambahkan; isi lama dipertahankan);
`docs/PROJECT_STATE.md`, file ini; `docs/sessions/2026-10-21T1057+0700.md`.

**Koreksi teknis yang sudah dicatat:** PDFBox 3.0 minimum Java 8; PDFium punya
`FPDFPage_CreateAnnot` (13 subtipe) tetapi tidak membuat field form, tidak menulis
enkripsi, signature hanya introspeksi, tidak ada API redaksi; QPDF bukan engine ekstraksi
teks/redaksi; `pdfium-binaries` bukan build resmi Google. Rincian:
`docs/RESTART_AUDIT.md` §8.

**Langkah gagal / temuan yang menghentikan:** tidak ada kegagalan alat. Temuan blocker:
**PUB-1** — project token PostHog pihak ketiga utuh di `docs/ANALYSIS_STIRLING_PDF.md`
baris 53 & 335 (saat itu di luar izin). *Pembaruan 2026-10-21 sesi 1114: disamarkan;
klasifikasi dikoreksi menjadi project token publik, bukan personal API key.*

**Tidak disentuh:** `src/`, `tests/`, `spikes/`, `scripts/`, dependency, `LICENSE`,
`NOTICE`, `AGENTS.md`, `README.md`, `TASKS.md`, `SESSION_LOG.md`, `ANALYSIS_*.md`,
metadata Git.

### 0.1 Daftar approval yang ditunggu

| ID | Keputusan | Pilihan |
|---|---|---|
| A-1 | Urutan prioritas kriteria E-1…E-9 (`STACK_EVALUATION.md` §10.2) | setuju / ubah |
| A-2 | Toleransi ukuran distribusi (installer dan terpasang) | angka dari pengguna |
| A-3 | Izin menyamarkan kunci PostHog di `ANALYSIS_STIRLING_PDF.md` + perlakuan path `<USERPROFILE>\…` di tiga dokumen analisis | ya / tidak; samarkan path ya / tidak |
| A-4 | Izin memperbaiki defek `TASKS.md` (DOC-1) tanpa mengubah makna | ya / tidak |
| A-5 | Pengamanan 13 file (`CLEANUP_PLAN.md` Fase 1) | 1a commit lokal tanpa push / 1b backup independen (+lokasi) / keduanya / tunda |
| A-6 | Eksekusi spike fase 1 (RS-00, RS-01, RS-02/03/05 bagian PDFium) termasuk instalasi crate `pdfium-render` dan biner PDFium dari sumber yang disetujui di RS-00 | ya / tidak |
| A-7 | Lokasi eksperimen `experiments/restart/` + output di-gitignore | ya / lokasi lain |
| A-8 | Penomoran milestone: protokol restart (M9 Signature, M10 Release) atau `ROADMAP.md` lama | protokol / lama |
| A-9 | Ubah referensi `AGENTS.md` §5 ke `POST_ALL_REFERENCES_TECH_REVIEW.md` | ya / tidak |

**Belum diajukan sekarang (menunggu hasil spike):** keputusan stack (K-4), cleanup
Fase 2–3, ratifikasi ulang lisensi (K-7).

### 0.2 Perintah berikutnya (read-only, aman)

```powershell
cd D:\dokumentasi\Project\UnionPDF
git status --short                              # harus: 13 file pra-restart + dokumen sesi 1057
.\.venv\Scripts\python.exe scripts\lint.py      # skrip read-only; dicek isinya 2026-10-21
```

Hasil yang diharapkan: tidak ada perubahan di `src/`, `tests/`, `spikes/`; lint 0 temuan.

### 0.3 Risiko

- Snapshot REA berada di folder temp sistem — bisa hilang sebelum backup disetujui.
- Commit sebelum PUB-1 ditangani akan mengabadikan token pihak ketiga di histori
  (*sudah ditangani sesi 1114*).
- Membaca §1–§10 di bawah tanpa §0 dapat menyesatkan: bagian itu histori pra-restart
  (mis. "jangan buka ulang perbandingan stack" sudah tidak berlaku).

### 0.4 Lima langkah kelanjutan

1. Tunggu jawaban A-1 … A-9; jangan menafsirkan diam sebagai persetujuan.
2. Bila A-3/A-4 disetujui: perbaiki PUB-1 dan DOC-1, jalankan `lint.py`.
3. Bila A-5 disetujui: jalankan Fase 1 persis seperti `CLEANUP_PLAN.md` (per-file, tanpa push).
4. Bila A-6/A-7 disetujui: spike fase 1 sesuai `TECH_SPIKES.md` §R; catat hasil dan bukti.
5. Ajukan keputusan baseline berdasarkan hasil spike → ADR baru.

### 0.5 Jangan diulang

- Audit read-only workspace 2026-10-21 (`RESTART_AUDIT.md`).
- Verifikasi sumber primer PDFium/PDFBox/QPDF/MuPDF/pdfium-binaries
  (`POST_ALL_REFERENCES_TECH_REVIEW.md` §5) — ulangi hanya bila versi target berubah.
- Analisis REA tiga referensi.

---

## 1. Posisi sesi analisis (2026-10-21 pagi — histori)

**Titik berat proyek berubah.** Pengguna menyatakan dokumen lama di workspace
dianggap belum sah karena analisis belum mendahului keputusan, dan meminta
analisis referensi lebih dulu. Sesi ini memenuhi permintaan itu.

- **Dokumen analisis baru (otoritatif untuk fase ini):**
  `docs/ANALYSIS_NITRO14.md` — analisis mandiri Nitro PDF Pro 14.41.0.15:
  inventaris arsitektur, katalog fitur penuh 15 domain, deep-dive 25 fitur,
  12 operasi REA MCP, status unknown, dan indeks bukti.
- **Bukti dapat diverifikasi ulang:** `scripts/verify_analysis_corpus.py`
  mencocokkan 8 angka kunci dokumen dengan korporas — saat ini **8/8 OK (exit 0)**.
- **Korporas di-refresh** (re-run 5 skrip read-only). 3 dari 4 file korporas
  **identik byte-per-byte** dengan run sebelumnya, jadi instalasi referensi tidak
  berubah; angka lama tetap berlaku kecuali koreksi di §0.2 dokumen baru.
- **Koreksi angka lama:** 36 `.mui` (bukan 35) - **13 tab bernama** (bukan 14) -
  228 grup toolbar kontekstual (bukan 90) - 20 model bahasa OCR (cocok).
- **Temuan baru utama:** arsitektur **out-of-process** (`nitro_module_loader.exe`),
  kontrak plugin `handshake_v3_data`, PDF/A **preflight + laporan validasi**,
  XFA sebagai **aplikasi web lokal terpisah** (109,6 MB), Ghostscript **GPL**,
  4 algoritma enkripsi, mode OCR *searchable* vs *searchable-and-editable*.
- **Target kedua selesai** — `docs/ANALYSIS_STIRLING_PDF.md`: Stirling-PDF 3.2.0
  (Windows). Arsitektur: shell **Tauri/Rust + WebView2** → backend **Spring Boot 4.1.1 +
  Jetty 12** di `127.0.0.1:8080` (JRE 25.0.4.1 ter-bundel) → engine **Apache PDFBox 3.0.8 +
  PDFium (jpdfium)**. 177 controller · 248 dependency · 47 jalur API · 84 chunk UI React.
  Temuan kunci: fitur berat (**Ghostscript, QPDF, Tesseract, LibreOffice**) bergantung tool
  eksternal yang **tidak dibundel**; model *open-core* (inti MIT + paket proprietary) dengan
  tier lisensi di server; **telemetri PostHog** (project token tertanam) dan
  `include-stacktrace=always`.
  Bukti: `scripts/verify_stirling_artifact.py` (10/10 OK). Installed copy di
  `C:\Program Files\Stirling PDF\` **byte-identik** dengan MSI yang dianalisis.
- **Target ketiga selesai** — `docs/ANALYSIS_PDFGEAR.md`: PDFgear 3.0.0 =
  **.NET Framework 4.6.2 / WPF** dengan **4 pustaka PDF komersial** (Pdfium.Net, Patagames,
  SautinSoft PDF Focus, Syncfusion), **2 engine OCR ter-bundel** (Tesseract 4.1.1 + NsOCR,
  227,5 MB), **Copilot 27 aksi** dengan konfirmasi 11 bahasa, telemetri GA4 + Google Ads +
  Sentry, dan `PaidUserVisibilityConverter` (fitur berbayar). Verifikasi
  `scripts/verify_pdfgear_artifact.py` (12/12 OK). Installer 132 MB ditolak REA
  (batas 64 MiB) → analisis memakai instalasi aktif.

Stack **tidak diubah** (ADR-001: Python 3.13 + PySide6 6.11 + MuPDF 1.27 +
Windows OCR), tetapi **belum diratifikasi ulang** setelah analisis baru ini.

## 1b. Posisi sebelumnya (2026-10-20 — histori)

Tiga milestone terpenuhi sekaligus:
- **REA ditutup.** Enam unknown ditutup (U-08/U-10/U-11/U-12 *closed*,
  U-07/U-09 *partial* dengan alasan).
- **Repository publik aktif:** <https://github.com/anprar/UnionPDF>
  (public, `main`, commit `336538a`, 89 blob, 0,4 MB).
- **Source offer AGPL** terpasang di aplikasi (`src/unionpdf/about.py` → dialog
  "Tentang") dan dijaga 14 test otomatis.

Stack **tidak berubah** — tinjauan ulang pasca-v2/v3 mengonfirmasi skor
463/500. Temuan terbaru justru **menurunkan risiko M8**: "Edit Text" di v14
diimplementasikan di `np_annotations.dll` (manipulasi lapisan anotasi), bukan
content-stream surgery.

## 2. Langkah terakhir yang BERHASIL

`git push -u origin main` → branch `main` ter-track; `gh repo edit` menambah
description, homepage, dan 9 topik. Verifikasi: 89 blob di remote, `LICENSE` /
`NOTICE` / `README` / `src` ada, korpus mentah **tidak** ikut.

## 3. Langkah terakhir yang GAGAL

| Kegagalan | Akar masalah | Perbaikan |
|---|---|---|
| REA `binary_overview` pada `np_ocr.dll` (3,3 MB) | Ghidra timeout startup 330 s | Batas Ghidra ≈ 700 KB; pivot ke jalur string + PE resources (bukti setara) |
| `git commit -F - <<'EOF'` | PowerShell tidak mendukung heredoc | Tulis pesan ke file, lalu `git commit -F <file>` |
| Ekstraksi shortcut menghasilkan noise ("control bar", "controller") | Regex terlalu longgar; "Ctrl" muncul di dalam nama kelas C++ (`CBCGP**Ctrl**`) | Diketahui sebagai keterbatasan BCG (binary resource) → U-07 partial |

## 4. Berkas yang sedang dimodifikasi

Tidak ada file sumber yang sedang diedit. File **baru** (belum di-commit):

| File | Status |
|---|---|
| `docs/ANALYSIS_NITRO14.md` | baru, belum di-commit (menunggu izin) |
| `scripts/verify_analysis_corpus.py` | baru, belum di-commit |
| `docs/sessions/2026-10-21T0851+0700.md` | log sesi |
| `docs/TASKS.md`, `docs/PROJECT_STATE.md`, `docs/HANDOFF.md`, `docs/SESSION_LOG.md` | checkpoint |

## 5. Perubahan belum terverifikasi

Lihat `PROJECT_STATE.md` § "Perubahan belum terverifikasi":
jalur atomic write belum dipakai UI, `JobRunner` belum dipakai UI, QSS belum
diuji visual, `RenderCache` belum diukur memory-nya.

## 6. Perintah berikutnya

```powershell
cd D:\dokumentasi\Project\UnionPDF
.\.venv\Scripts\python.exe scripts\verify_analysis_corpus.py   # cek angka analisis
.\.venv\Scripts\python.exe scripts\lint.py                      # 0 temuan
.\.venv\Scripts\python.exe -m pytest tests -q                     # baseline tidak boleh turun
```

Setelah itu: **baca `docs/ANALYSIS_NITRO14.md`**, lalu jawab 5 blok ratifikasi
(stack, scope REPLACE/DEFER/REJECT, prioritas M8, publikasi bukti mentah,
toleransi ukuran EXE). Task implementasi (`UPDF-012`) menunggu keputusan
tersebut agar tidak membangun di atas asumsi lama.
## 7. Hasil yang diharapkan

- `pytest` → 69 passed (tercatat 2026-10-20 18:29; tidak dijalankan ulang sejak itu).
- Semua task baru harus menambah test; **jangan** menurunkan jumlah test.

## 8. Keputusan terbuka

| ID | Keputusan | Impact |
|---|---|---|
| B-03 | Toleransi ukuran distribusi? | Menentukan strategi build & trimming PySide6 |
| B-04 | Kapan membangun edit teks existing? | Sekarang **rendah risiko** (T-12) — tinggal proof-of-concept |
| B-05 | Sumber daftar bahasa OCR untuk Windows OCR? | Memengaruhi UX M5 |
| — | Nama/host repository | ✅ **SELESAI** — `github.com/anprar/UnionPDF` |
| — | Code signing certificate | Untuk rilis M12 (opsional) |
| — | Nama domain / halaman dokumentasi publik | Untuk M12 |

## 9. Kerja yang SUDAH selesai — jangan diulang

- Inventaris folder referensi (nama modul + versi) — **jangan** ulangi.
- Spikes S1–S12 — **jangan** ulangi; hasil ada di `spikes/out/*.json`.
- ~~Perbandingan stack A/B/C/B' + pembobotan — jangan buka ulang~~ —
  **tidak berlaku lagi**: pengguna membuka ulang perbandingan stack pada controlled
  restart 2026-10-21 (lihat `STACK_EVALUATION.md` §10). "Dikonfirmasi" pada §18
  `POST_REA_TECH_REVIEW.md` adalah evaluasi agent, bukan persetujuan pengguna.
- **Ekstraksi UI biner v14** (14.452 string, 783 kontrol) — **jangan** ulangi;
  hasilnya sudah di `docs/research/*.json` (lokal, tidak di-commit).
- Inventaris bahasa OCR (20 paket) — **jangan** ulangi.
- **Re-run ekstraksi korporas v14 (2026-10-21)** — **jangan** ulangi; hasilnya
  identik dengan run sebelumnya (lihat `docs/ANALYSIS_NITRO14.md` §0.2). Butuh
  hanya jika instalasi referensi berubah.
- **REA pada `np_pdfa.dll` & `nitro_module_loader.exe`** — **jangan** ulangi;
  12 operasi dan evidence ID tercatat di `docs/ANALYSIS_NITRO14.md` §6.1.
- **Analisis Stirling-PDF 3.2.0** (2026-10-21) — **jangan** ulangi; 12 operasi REA
  tercatat di `docs/ANALYSIS_STIRLING_PDF.md` §9.1. Ekstraksi payload MSI memakai
  `msiexec /a` ke temp (read-only) — ulangi hanya bila versi berubah.
- Penyiapan venv + daftar dependency — sudah ada di `requirements*.txt`.
- Struktur `src/unionpdf/` — sudah sesuai ADR-001.
- Berkas `LICENSE` + `NOTICE` + repo publik — sudah dibuat.
- Metadata `src/unionpdf/about.py` — jangan diduplikasi; itu satu-satunya
  sumber kebenaran untuk tautan source.

## 10. Lima langkah berikutnya

1. **Baca dua dokumen analisis** — `docs/ANALYSIS_NITRO14.md` (target 1) dan
   `docs/ANALYSIS_STIRLING_PDF.md` (target 2).
2. **Ratifikasi 5 blok** (§8): stack, scope REPLACE/DEFER/REJECT, prioritas M8,
   publikasi bukti mentah, toleransi ukuran EXE.
3. **Tentukan perlakuan dokumen lama** — tulis ulang mengikuti analisis baru, atau jadikan
   arsip yang digantikan dokumen baru.
4. **Commit** dokumen + 2 skrip verifikasi (menunggu izin).
5. **UPDF-012** — sambungkan `Save As` ke `atomic_write` + verifikasi →
   `src/unionpdf/ui/main_window.py`, `src/unionpdf/infrastructure/file_store.py`.

## 11. Peringatan

- `scripts/lint.py` **wajib** dijalankan setiap kali selesai menulis dokumen —
  karakter CJK/Hangul pernah masuk beberapa kali (bug berulang). Perbaikannya
  ada di `scripts/repair_docs.py`.
- **Jangan commit korpus mentah** di `docs/research/*.json` — itu konten
  proprietary pihak ketiga dalam skala besar; sudah di-gitignore dengan alasan.
  Yang dipublikasikan hanya `V14_UI_EVIDENCE_SUMMARY.md` (kutipan terkurasi).
- `docs/research/V14_UI_EVIDENCE_SUMMARY.md` memuat label yang **tidak
  semuanya** diverifikasi sebagai aktif pada build ini — perlakukan sebagai
  indikasi.
- Ghidra **tidak bisa** menganalisis modul Nitro > ~700 KB pada toolchain ini.
  Jangan coba berulang tanpa menaikkan `REA_GHIDRA_STARTUP_TIMEOUT_MS`.
- Jangan pernah push tanpa review `git status` + `git diff --cached --stat`.
- `spikes/` **terpisah** dari `src/`. Jangan import spike ke kode produksi.
