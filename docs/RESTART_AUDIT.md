# RESTART_AUDIT.md — Audit Controlled Restart (GATE A, revisi 1)

| Field | Nilai |
|---|---|
| Status | **DRAFT audit — bukan keputusan** |
| Sesi | `2026-10-21T1057+0700` |
| Gate | **GATE A (revisi 1)** — menunggu keputusan pengguna |
| Stack final | **BELUM DISETUJUI** |
| Cleanup | **BELUM DISETUJUI** |
| Commit / push / publikasi | **BELUM DISETUJUI** |
| Lisensi | AGPL-3.0 tetap seperti apa adanya; **belum diratifikasi ulang**; tidak diubah |

Dokumen ini mencatat hasil audit read-only workspace, koreksi atas proposal
GATE A sebelumnya, dan status persetujuan. Ia **tidak** menyatakan keputusan apa pun
telah disetujui.

---

## 1. Izin yang berlaku pada sesi ini

Izin terbatas dari pengguna (2026-10-21): menulis **hanya** dokumen berikut,
tanpa menyentuh kode aplikasi, dependency, `LICENSE`, `NOTICE`, `AGENTS.md`, atau
metadata Git:

- `docs/RESTART_AUDIT.md` (file ini), `docs/CLEANUP_PLAN.md`,
  `docs/POST_ALL_REFERENCES_TECH_REVIEW.md`, `docs/STACK_EVALUATION.md`,
  `docs/FEATURE_MATRIX.md`, `docs/TECH_SPIKES.md`
- session log baru (`docs/sessions/2026-10-21T1057+0700.md`)
- checkpoint `docs/PROJECT_STATE.md` dan `docs/HANDOFF.md` **tanpa** menyatakan
  keputusan sudah disetujui

**Di luar izin (tidak disentuh):** `docs/TASKS.md`, `docs/SESSION_LOG.md`,
`docs/ANALYSIS_*.md`, `README.md`, `ROADMAP.md`, `BLOCKERS.md`, `DECISIONS.md`,
ADR, seluruh `src/`, `tests/`, `spikes/`, `scripts/`.

### Status konfirmasi (sebagaimana dinyatakan pengguna)

| ID | Lingkup | Status |
|---|---|---|
| K-1 | Commit 13 file | **BELUM DISETUJUI** |
| K-2 | Arsip aplikasi lama | **BELUM DISETUJUI** |
| K-3 | Regenerasi cache | **BELUM DISETUJUI** |
| K-4 | Keputusan stack | **BELUM DISETUJUI** |
| K-5 | Spike | Hanya **perencanaan**; belum eksekusi, belum scaffold |
| K-6 | Instalasi dependency | **BELUM DISETUJUI** |
| K-7 | Lisensi | **Belum diratifikasi ulang**; jangan ubah lisensi |
| K-8 | Dokumen legacy | Hanya koreksi dokumentasi dalam batas izin |
| K-9 | Push / publikasi | **TIDAK ADA IZIN** |
| K-10 | Typo / ID / status pada dokumen yang diizinkan | **Diizinkan**, tanpa mengubah makna keputusan |

---

## 2. Metode audit

- Pemeriksaan read-only: `git log/status/diff --stat/--numstat/ls-files/check-ignore`,
  `Get-ChildItem`, `Get-Command`, pembacaan file dengan alat baca.
- **Tidak ada** skrip aplikasi/audit lama yang dijalankan. Pengecualian setelah
  pemeriksaan isi: `scripts/lint.py` (dibaca penuh: hanya membaca file dan mencetak
  temuan, tidak menulis) — dijalankan di akhir sesi untuk validasi dokumen.
- Verifikasi teknis dari sumber primer (diakses 2026-10-21): header publik PDFium
  (`fpdf_annot.h`, `fpdf_save.h`, `fpdf_signature.h`, `fpdf_ppo.h`, `fpdf_edit.h`,
  `fpdf_flatten.h`, `fpdf_formfill.h`), README & `Cargo.toml` `pdfium-render`,
  README `bblanchon/pdfium-binaries`, PDFBox 3.0 Migration Guide, dokumentasi QPDF
  "What is qpdf?", halaman lisensi Artifex, dokumentasi PyMuPDF. Rincian di
  `docs/POST_ALL_REFERENCES_TECH_REVIEW.md` §2.

---

## 3. Kondisi repository

| Item | Nilai terverifikasi |
|---|---|
| Remote | `origin https://github.com/anprar/UnionPDF.git` (repo publik) |
| Branch | `main` |
| HEAD | `d01cd16` (4 commit: `336538a` → `61c0547` → `4da08b1` → `d01cd16`) |
| File tracked | 93 |
| Stash | kosong |
| Working tree | 4 file termodifikasi + 9 file untracked (§4) |

---

## 4. Tiga belas file yang belum di-commit

Belum ada yang di-stage. **Jangan** gunakan `git add -A`, `git add .`, atau wildcard.

| # | Path | Status Git | Diff | Ringkasan isi / perubahan |
|---:|---|---|---|---|
| 1 | `docs/HANDOFF.md` | M | +76 / −16 | Header sesi → `2026-10-21T1000+0700`; ringkasan 3 analisis di §1. **Defek:** heading `## 1. Posisi saat ini` muncul dua kali |
| 2 | `docs/PROJECT_STATE.md` | M | +7 / −7 | Tanggal, session ID, fase, task aktif, working tree, status REA |
| 3 | `docs/SESSION_LOG.md` | M | +3 / −0 | 3 entri indeks sesi (0851, 0932, 1000) |
| 4 | `docs/TASKS.md` | M | +5 / −3 | UPDF-029/030/031 DONE. **Defek:** baris UPDF-028 dan UPDF-029 tergabung; UPDF-029 ganda; heading `## M1` berubah menjadi `# M1` |
| 5 | `docs/ANALYSIS_NITRO14.md` | ?? | baru, 82 KB | Analisis REA Nitro PDF Pro 14.41.0.15 |
| 6 | `docs/ANALYSIS_STIRLING_PDF.md` | ?? | baru, 41 KB | Analisis REA Stirling-PDF 3.2.0. Semula memuat project token PostHog pihak ketiga utuh (baris 53, 335) — **disamarkan** pada sesi `2026-10-21T1114+0700` |
| 7 | `docs/ANALYSIS_PDFGEAR.md` | ?? | baru, 33 KB | Analisis REA PDFgear 3.0.0 |
| 8 | `docs/sessions/2026-10-21T0851+0700.md` | ?? | baru | Log sesi analisis Nitro |
| 9 | `docs/sessions/2026-10-21T0932+0700.md` | ?? | baru | Log sesi analisis Stirling |
| 10 | `docs/sessions/2026-10-21T1000+0700.md` | ?? | baru | Log sesi analisis PDFgear |
| 11 | `scripts/verify_analysis_corpus.py` | ?? | baru, 3 KB | Verifikasi angka dokumen Nitro terhadap korpus lokal |
| 12 | `scripts/verify_stirling_artifact.py` | ?? | baru, 4 KB | Verifikasi angka Stirling dari JAR/EXE (path argumen) |
| 13 | `scripts/verify_pdfgear_artifact.py` | ?? | baru, 5 KB | Verifikasi angka PDFgear dari instalasi (path argumen) |

### 4.1 Temuan risiko publikasi (koreksi atas klaim sebelumnya)

Klaim pada proposal GATE A sebelumnya bahwa dokumen analisis "aman dipublikasikan
karena analisis sendiri" **ditarik**. Pemeriksaan terarah menemukan:

| Temuan | File | Status |
|---|---|---|
| Project token PostHog pihak ketiga (literal penuh). Klasifikasi dikoreksi 2026-10-21: menurut dokumentasi resmi PostHog, token `phc_` adalah project token yang boleh publik dan tidak memberi akses data privat — **bukan** personal API key (`phx_`) dan tidak dibuktikan sebagai credential akses privat | `ANALYSIS_STIRLING_PDF.md` baris 53 dan 335 | **Disamarkan** (keputusan A-3, sesi `2026-10-21T1114+0700`); sidik SHA-256 nilai asli dicatat di dokumen. Tidak ada di commit lokal mana pun (`git log --all -S` kosong) |
| Path lokal pengguna (`<USERPROFILE>\…`) | Nitro 1×, Stirling 5×, PDFgear 3× | **Disamarkan** menjadi `<USERPROFILE>` (A-3). Tidak ada di commit lokal mana pun |
| Kutipan teks UI/string dari biner proprietary | ketiga dokumen | Perlu tinjauan hak cipta per kutipan sebelum publikasi; kebijakan korpus mentah (gitignore) tidak otomatis mencakup kutipan dalam dokumen |
| Nama, hash, versi komponen pihak ketiga | ketiga dokumen + skrip verifikasi | Fakta teknis; tetap perlu tinjauan |

Kesimpulan: **status publikasi dokumen analisis = BELUM DITINJAU**, bukan aman.

---

## 5. Inventaris dan klasifikasi

| Path | Isi terverifikasi | Kelas | Perlakuan pada fase ini |
|---|---|---|---|
| `docs/ANALYSIS_*.md` (3) | analisis REA | A — evidence | Pertahankan; tidak diubah |
| `scripts/verify_*.py` (3) | verifikasi angka | A | Pertahankan |
| `scripts/` lainnya (12) | 5 skrip ekstraksi REA, `lint.py`, `repair_docs.py`, `smoke_app.py`, 4 `.ps1` | A / C | Pertahankan; **jangan dijalankan** tanpa memeriksa isi |
| `docs/research/` | 9 file, 1.498 KB; 5 file gitignored (`.gitignore` baris 34–38), 4 tracked | A — korpus | Tetap lokal; jangan unggah |
| Snapshot REA (temp, di luar workspace) | `rea_nitro_snapshot.json` 115 KB, `rea_stirling_snapshot.json` 280 KB, `rea_pdfgear_snapshot.json` 30 KB | A — evidence | Jangan unggah; rentan hilang karena berada di temp (lihat §8) |
| `src/unionpdf/` | 20 modul Python (156 KB) — implementasi lama | C | **Dipertahankan** sebagai benchmark sampai kandidat diuji |
| `tests/` | 6 modul test (130 KB); 69 passed tercatat 2026-10-20 (tidak dijalankan ulang sesi ini) | C | **Dipertahankan** |
| `spikes/` | 5 skrip + `out/` (gitignored) + `fixtures/` (gitignored) | C / D | **Dipertahankan** |
| `requirements*.txt`, `pytest.ini` | konfigurasi stack lama | C | Dipertahankan |
| `.venv/` | 6.362 file, ≈771 MB, gitignored | D | Dipertahankan |
| `.pytest_cache/`, `__pycache__/` | cache | D | Dipertahankan pada fase ini |
| `LICENSE`, `NOTICE` | AGPL-3.0 | A | Tidak diubah |
| `.git/`, `.gitignore`, `.gitattributes`, `AGENTS.md`, `README.md` | metadata/instruksi | G / A | Tidak diubah |
| File pribadi / tak dikenal | tidak ditemukan | E | — |
| Credential / secret milik proyek | tidak ditemukan di workspace; ditemukan **project token** pihak ketiga dalam dokumen analisis (§4.1; bukan credential akses privat menurut dokumentasi resmi) — sudah disamarkan | F | Jangan salin/sebarkan |
| Symlink / junction | tidak terdeteksi pada jalur yang diperiksa; belum dipindai menyeluruh | H | Periksa ulang sebelum cleanup |

---

## 6. Toolchain (fakta, bukan rencana instalasi)

| Tool | Status | Catatan |
|---|---|---|
| Node | v22.20.0 | sudah terpasang |
| Rust | cargo/rustc 1.98.0 | sudah terpasang |
| Java | Zulu 8 (`C:\Program Files\Zulu\zulu-8\bin\java.exe`) | **Memenuhi minimum PDFBox 3.0 (Java 8)** — lihat koreksi §8.1 |
| Python | 3.13 (sistem) + `.venv` | dipakai implementasi lama & skrip verifikasi |
| Tesseract | tidak tersedia | — |
| LibreOffice (`soffice`) | tidak tersedia | — |
| PDFium binary | tidak ada di workspace | — |

---

## 7. Konflik dokumen

### 7.1 Antar-file (defek internal)

| # | Konflik | Bukti |
|---|---|---|
| D-1 | **Klaim persetujuan stack tidak dapat ditelusuri ke persetujuan eksplisit pengguna.** `README.md:58-60` ("dikonfirmasi ulang"), `PROJECT_STATE.md:16` ("Diputuskan & dikonfirmasi"), `TASKS.md` UPDF-009/020 DONE "KEEP" — bertentangan dengan `HANDOFF.md:50-51` ("belum diratifikasi ulang") dan `BLOCKERS.md` B-07.1 ("Menunggu Persetujuan"). Status: **DISPUTED**; pengguna menyatakan stack final belum disetujui | baris yang disebut |
| D-2 | `TASKS.md` baris 41–42: baris tergabung, UPDF-029 ganda | `TASKS.md:41-42` |
| D-3 | ID ganda UPDF-901 dan UPDF-902 di dua tabel berbeda | `TASKS.md:112-113` vs `127-128` |
| D-4 | `PROJECT_STATE.md` menyebut commit `336538a` (HEAD sebenarnya `d01cd16`) dan test 55 vs 69 | `PROJECT_STATE.md:14,56,62` |
| D-5 | Heading `## 1. Posisi saat ini` ganda | `HANDOFF.md:11,53` |
| D-6 | `TECH_SPIKES.md:3` menyebut "S1–S5" padahal tabel memuat S1–S12 | diperbaiki sesi ini (K-10) |
| D-7 | `STACK_EVALUATION.md:115-116` mencatat sebagai **FAKTA** bahwa PDFium "read-only… tidak menulis dokumen" — **terbantah** oleh header publik PDFium (`FPDFPage_CreateAnnot`, `FPDF_SaveAsCopy`) | dicatat sebagai errata di `STACK_EVALUATION.md` §10.1; teks lama dipertahankan |
| D-8 | `STACK_EVALUATION.md:73-75` menyatakan PDFBox "tidak punya authoring anotasi/redaksi yang memadai" tanpa bukti yang dirujuk | errata §10.1 |
| D-9 | `FEATURE_MATRIX.md:45` menyebut 14 tab ribbon; analisis baru mencatat 13 tab bernama | errata di `FEATURE_MATRIX.md` |

D-2, D-3, D-4 (sebagian), dan D-5 berada di file yang hanya boleh diubah dalam batas
izin: D-4 dan D-5 diperbaiki pada checkpoint sesi ini; **D-2 dan D-3 belum
diperbaiki** karena `TASKS.md` di luar izin.

### 7.2 Protokol restart vs file lama

| # | Perbedaan | Penanganan yang diusulkan |
|---|---|---|
| P-1 | Kandidat stack restart berbeda dari ADR-001 | Lewat ADR baru setelah keputusan; ADR-001 tidak diedit diam-diam |
| P-2 | Nama review baru `POST_ALL_REFERENCES_TECH_REVIEW.md` vs referensi `AGENTS.md` §5 ke `POST_REA_TECH_REVIEW.md` | File baru dibuat sesi ini; perubahan referensi di `AGENTS.md` **butuh izin** |
| P-3 | Penomoran milestone protokol (M9 Signature, M10 Release) vs `ROADMAP.md`/`TASKS.md` (M9 Conversion, M10 Signatures, M11, M12) | Butuh keputusan; belum diubah |
| P-4 | ID spike lama S1–S12 vs rencana baru | ID baru `RS-xx` di `TECH_SPIKES.md` §R |

---

## 8. Koreksi atas proposal GATE A sebelumnya

### 8.1 Java / PDFBox
- **Salah sebelumnya:** "Zulu 8 tidak cukup untuk PDFBox 3.x; perlu JDK 17+/21".
- **Benar:** PDFBox 3.0 Migration Guide: *"PDFBox 3.0 requires at least Java 8. Testing
  has been done up to Java 19."* Memilih Java yang lebih baru adalah **kebijakan proyek**
  (mis. siklus dukungan runtime) atau kebutuhan komponen lain — bukan minimum PDFBox.

### 8.2 PDFium dan authoring anotasi
- **Salah sebelumnya:** menggeneralisasi "PDFium tidak punya API authoring
  anotasi/form/redaksi".
- **Benar (API upstream):** `FPDFPage_CreateAnnot` ada (berlabel *Experimental*);
  `FPDFAnnot_IsSupportedSubtype` menyatakan 13 subtipe yang didukung untuk dibuat:
  circle, fileattachment, freetext, highlight, ink, link, popup, square, squiggly,
  stamp, strikeout, text, underline. Widget (field form) dan redact **tidak** termasuk.
  Form, redaksi, dan signature dievaluasi terpisah di
  `POST_ALL_REFERENCES_TECH_REVIEW.md` §2.1.

### 8.3 QPDF
- **Salah sebelumnya:** menempatkan QPDF sebagai fallback ekstraksi teks dan bagian
  jalur redaksi.
- **Benar:** dokumentasi QPDF: *"structural, content-preserving transformations"*;
  *"qpdf knows nothing about the semantics of PDF content streams"*; bukan viewer,
  bukan alat konversi, bukan library pembuatan konten. QPDF **bukan** engine ekstraksi
  teks dan **bukan** engine secure redaction.

### 8.4 PDFBox ditunda ke M8
- **Salah sebelumnya:** menunda PDFBox ke M8 hanya dengan alasan edit teks/reflow.
- **Benar:** PDFBox harus dinilai untuk authoring anotasi, form, signature, dan
  penulisan dokumen (lihat review §2.4), bukan hanya edit teks existing.

### 8.5 Sumber biner PDFium
- **Salah sebelumnya:** menyebut "build resmi Chromium/pdfium-binaries".
- **Benar:** `bblanchon/pdfium-binaries` menyatakan *"This project isn't affiliated with
  Google or Foxit"*, memiliki folder `patches/`, dan lisensi MIT untuk skrip build.
  Provenance harus dicatat terpisah (upstream, pembangun, revisi, metode verifikasi);
  hash yang dihitung setelah unduh **tidak** membuktikan keaslian sendirian.

### 8.6 Arsip lokal ≠ backup independen
- `_archive/` di dalam workspace berada pada disk dan folder yang sama; ia melindungi
  dari salah hapus, **tidak** dari kerusakan disk atau kehilangan mesin. Backup
  independen membutuhkan lokasi/perangkat lain yang dipilih pengguna. Lihat
  `CLEANUP_PLAN.md` §3.

### 8.7 Urutan cleanup
- **Salah sebelumnya:** mengusulkan pengarsipan `src/`, `tests/`, `spikes/` sebelum
  kandidat diuji.
- **Benar:** implementasi lama dipertahankan sebagai benchmark sampai baseline dipilih
  dan spike kandidat selesai. Cleanup dijadwalkan **setelah** keputusan baseline.

---

## 9. Ringkasan untuk keputusan

- Audit selesai; tidak ada file kode, dependency, lisensi, atau metadata Git yang diubah.
- Perbandingan baseline yang dikoreksi: `STACK_EVALUATION.md` §10.
- Capability matrix: `FEATURE_MATRIX.md` §13.
- Review teknologi: `POST_ALL_REFERENCES_TECH_REVIEW.md`.
- Rencana spike: `TECH_SPIKES.md` §R.
- Rencana cleanup (setelah keputusan baseline): `CLEANUP_PLAN.md`.

**Stack final dan cleanup BELUM DISETUJUI.**
