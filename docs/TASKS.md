# TASKS.md — Backlog

Status: `TODO` · `IN_PROGRESS` · `BLOCKED` · `REVIEW` · `DONE` · `DEFERRED`

**Aturan:** `DONE` hanya bila acceptance criteria terpenuhi **dan** test
ter Relevan sudah dijalankan. Kode yang ada saja **bukan** bukti selesai.

---

## M0 — FOUNDATION

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-001 | Verifikasi workspace, OS, toolchain, REA | Tinggi | **DONE** | `docs/sessions/2026-10-20T1624+0700.md` |
| UPDF-002 | Inventaris read-only folder referensi | Tinggi | **DONE** | `docs/REA_FINDINGS.md` §2 (E-101…E-104) |
| UPDF-003 | Analisis dokumentasi publik v14 | Tinggi | **DONE** | `docs/REA_FINDINGS.md` §4 (E-001…E-008) |
| UPDF-004 | Dokumen batas analisis (REA_LIMITATIONS) | Tinggi | **DONE** | `docs/REA_LIMITATIONS.md` |
| UPDF-005 | Matriks fitur (97 fitur) | Tinggi | **DONE** | `docs/FEATURE_MATRIX.md` |
| UPDF-006 | Review teknologi pasca-REA (gate) | Tinggi | **DONE** | `docs/POST_REA_TECH_REVIEW.md` |
| UPDF-007 | Evaluation stack berbobot (4 kandidat) | Tinggi | **DONE** | `docs/STACK_EVALUATION.md` (A=463, B=384, C=322, B'=320) |
| UPDF-008 | Technical spike S1–S12 | Tinggi | **DONE** | `docs/TECH_SPIKES.md`, `spikes/out/*.json` |
| UPDF-009 | ADR keputusan stack | Tinggi | **DONE** | `docs/decisions/ADR-001-stack-baseline.md` |
| UPDF-010 | Struktur dokumentasi kontinuitas | Tinggi | **DONE** | `docs/` (33 dokumen) |
| UPDF-011 | Skeleton + vertical slice M1 (viewer) | Tinggi | **DONE** | 55 pytest PASS, smoke 9/9 PASS |
| UPDF-012 | Save As → atomic write + verifikasi | Tinggi | TODO | — |
| UPDF-013 | Operasi halaman di UI + job background | Tinggi | TODO | — |
| UPDF-014 | Build one-dir + **ukur** ukuran distribusi | Sedang | TODO | — |
| UPDF-015 | Spike edit teks existing (reflow) | Sedang | TODO | — |
| UPDF-016 | Panel anotasi & isi form minimal | Sedang | TODO | — |
| UPDF-017 | Inisialisasi git (perlu izin) | Sedang | TODO | — |
| UPDF-018 | Checklist manual DPI / keyboard / file terkunci | Sedang | TODO | — |
| UPDF-019 | Analisis biner read-only mendalam aplikasi referensi | Tinggi | **DONE** | `docs/REA_FINDINGS.md` v2; 14.452 string UI, 783 kontrol ribbon, 10.284 identifier fitur |
| UPDF-020 | Tinjauan ulang stack setelah analisis v2 | Tinggi | **DONE** | `docs/POST_REA_TECH_REVIEW.md` §18 — **KEEP**, skor tetap 463/500 |
| UPDF-021 | Lisensi proyek AGPL-3.0 + LICENSE + NOTICE | Tinggi | **DONE** | `LICENSE` (661 baris), `NOTICE` |
| UPDF-022 | Turunkan korpus pesan error v14 jadi checklist uji UnionPDF | Sedang | TODO | Sumber: `docs/research/V14_UI_EVIDENCE_SUMMARY.md` |
| UPDF-023 | Pembersihan dokumen 12-channel (M7 perluasan) | Sedang | TODO | Temuan v2 (T-2); MuPDF punya flag channel — verifikasi |
| UPDF-024 | Deteksi halaman tanpa text layer + opsi paksa OCR | Sedang | TODO | Temuan v2 (OCR skip halaman ber-text) |
| UPDF-025 | Ringkasan kurasi bukti v14 untuk repo publik | Tinggi | **DONE** | `docs/research/V14_UI_EVIDENCE_SUMMARY.md`; korpus mentah di-gitignore |
| UPDF-026 | Repository publik `anprar/UnionPDF` | Tinggi | **DONE** | Commit `336538a`, public, branch `main`, 89 blob |
| UPDF-027 | Source offer AGPL (dialog Tentang + metadata + test) | Tinggi | **DONE** | `src/unionpdf/about.py`, `tests/test_license_compliance.py` (14 test) |
| UPDF-028 | Metadata repo: description, homepage, topics | Sedang | **DONE** | 9 topik: pdf, pdf-editor, windows, python, pyside6, agpl-3-0, desktop-app, ocr, reverse-engineering |
| UPDF-029 | **Analisis REA fresh (Nitro 14) - dokumen analisis mandiri** | Tinggi | **DONE** | `docs/ANALYSIS_NITRO14.md`; angka diverifikasi `scripts/verify_analysis_corpus.py` (8/8 OK) |
| UPDF-030 | **Analisis REA target kedua (Stirling-PDF 3.2.0)** | Tinggi | **DONE** | `docs/ANALYSIS_STIRLING_PDF.md`; angka diverifikasi `scripts/verify_stirling_artifact.py` (10/10 OK) |
| UPDF-031 | **Analisis REA target ketiga (PDFgear 3.0.0)** | Tinggi | **DONE** | `docs/ANALYSIS_PDFGEAR.md`; angka diverifikasi `scripts/verify_pdfgear_artifact.py` (12/12 OK) |
| UPDF-034 | Controlled restart: audit read-only + proposal GATE A revisi 1 | Tinggi | **DONE** | `docs/RESTART_AUDIT.md`, `CLEANUP_PLAN.md`, `POST_ALL_REFERENCES_TECH_REVIEW.md`; laporan diterima pengguna sebagai dasar (2026-10-21) — **bukan** persetujuan stack |
| UPDF-035 | Redaksi project token PostHog + path profil pengguna di dokumen analisis (A-3) | Tinggi | **DONE** | Persetujuan A-3 (2026-10-21); verifikasi grep nol kemunculan — `docs/sessions/2026-10-21T1114+0700.md` |
| UPDF-036 | Perbaikan `TASKS.md` + indeks `SESSION_LOG.md` (A-4) | Sedang | **DONE** | Persetujuan A-4; mapping ID di bagian "Mapping ID" |
| UPDF-037 | Penomoran milestone mengikuti protokol restart (A-8) | Sedang | **DONE** | Persetujuan A-8; tabel mapping di bagian "Mapping milestone" dan `docs/ROADMAP.md` |
| UPDF-038 | Pembaruan terbatas `AGENTS.md` (A-9) | Sedang | **DONE** | Persetujuan A-9; §5 + §5b |
| UPDF-039 | Commit lokal pengamanan tanpa push (A-5) | Tinggi | IN_PROGRESS | Daftar path & isi: `docs/sessions/2026-10-21T1114+0700.md` |
| UPDF-040 | Spike RS-00 — review dependency & provenance PDFium | Tinggi | TODO | Persetujuan A-6; `experiments/restart/` (A-7) |
| UPDF-041 | Spike RS-01 — render, zoom, thumbnail, teks, cancel (PDFium) | Tinggi | TODO | Persetujuan A-6 |
| UPDF-042 | Spike bagian PDFium dari RS-02 / RS-03 / RS-05 | Tinggi | TODO | Persetujuan A-6 |
| UPDF-043 | Konfirmasi urutan kriteria evaluasi stack (A-1) | Tinggi | REVIEW | `docs/STACK_EVALUATION.md` §10.2b — menunggu konfirmasi pengguna |
| UPDF-044 | Pembandingan PDFBox dan MuPDF pada fixture yang sama | Tinggi | TODO | Menunggu persetujuan gate berikutnya |

## Mapping milestone (A-8, 2026-10-21)

Milestone mengikuti protokol restart. Task ID **tidak** diubah; hanya penempatan
milestone yang dipetakan. Detail: `docs/ROADMAP.md`.

| Lama | Baru |
|---|---|
| M0 Foundation | M0 Foundation |
| M1 Viewer | M1 Viewer |
| M2 Page Operations | M2 Page operations |
| M3 Create & Augment | M3 Content additions |
| M4 Annotations & Forms | M4 Annotations/forms |
| M5 OCR | M5 OCR |
| M6 Optimization & Batch | M6 Automation (batch/antrean); kompresi sementara di M6 — protokol tidak menyebut kompresi |
| M7 Security | M7 Security |
| M8 Advanced Editing | M8 Advanced editing/conversion |
| M9 Conversion | M8 Advanced editing/conversion |
| M10 Signatures | M9 Signature/compliance |
| M11 Modern Workflows | M6 Automation (command palette, preset, batch resumable, CLI) |
| M12 Release Hardening | M10 Release (PDF/A & aksesibilitas → M9 compliance) |

## Mapping ID (A-4, 2026-10-21)

| ID lama | ID baru | Alasan |
|---|---|---|
| UPDF-029 (baris kedua, tergabung dengan UPDF-028) | — (dihapus) | Duplikasi tidak disengaja; baris UPDF-029 tunggal dipertahankan |
| UPDF-901 "Audit lisensi dependency" (Latar Belakang) | **UPDF-032** | Bentrok dengan UPDF-901 "PDF → gambar & teks" |
| UPDF-902 "Jejak audit dependency" (Latar Belakang) | **UPDF-033** | Bentrok dengan UPDF-902 "Office ↔ PDF" |

## M1 — VIEWER

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-101 | Buka PDF + error handling (korup/terenkripsi) | Tinggi | **DONE** | `tests/test_engine.py` |
| UPDF-102 | Render + zoom + fit width/fit page | Tinggi | **DONE** | `tests/test_ui_smoke.py` |
| UPDF-103 | Navigasi halaman | Tinggi | **DONE** | `tests/test_ui_smoke.py` |
| UPDF-104 | Thumbnail pane | Tinggi | **DONE** | `tests/test_ui_smoke.py` |
| UPDF-105 | Pencarian + lompat ke hasil | Tinggi | **DONE** | smoke test |
| UPDF-106 | Panel informasi dokumen | Sedang | TODO | — |
| UPDF-107 | Seleksi & salin teks | Sedang | TODO | — |
| UPDF-108 | Riwayat halaman (back/forward) | Rendah | TODO | — |
| UPDF-109 | Render asynchron (worker) untuk dokumen besar | Sedang | TODO | — |

## M2 — PAGE OPERATIONS

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-201 | Merge dokumen | Tinggi | **DONE (engine)** | `tests/test_engine.py` |
| UPDF-202 | Split / extract | Tinggi | **DONE (engine)** | idem |
| UPDF-203 | Delete / rotate / duplicate / reorder | Tinggi | **DONE (engine)** | idem |
| UPDF-204 | UI operasi halaman + undo/redo | Tinggi | TODO | — |
| UPDF-205 | Simpan sebagai + verifikasi | Tinggi | TODO | — |

## M3 — CREATE & AUGMENT

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-301 | Tambah teks overlay | Tinggi | TODO | — |
| UPDF-302 | Tambah gambar | Tinggi | TODO | — |
| UPDF-303 | Watermark | Sedang | TODO | — |
| UPDF-304 | Header/footer + nomor halaman | Sedang | TODO | — |
| UPDF-305 | Halaman kosong & page range | Sedang | TODO | — |
| UPDF-306 | Gambar → PDF | Sedang | TODO | — |

## M4 — ANNOTATIONS & FORMS

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-401 | Highlight / underline / strikeout | Tinggi | TODO | API terverifikasi spike S3 |
| UPDF-402 | Note / komentar | Tinggi | TODO | idem |
| UPDF-403 | Bentuk dasar | Sedang | TODO | idem |
| UPDF-404 | Isi form + simpan | Tinggi | TODO | API terverifikasi spike S4 |
| UPDF-405 | Flatten anotasi/form | Sedang | TODO | — |

## M5 — OCR

| ID | Judul | Prioritas | Status | Bukti |
|---|---|---|---|---|
| UPDF-501 | Adapter OCR (Windows OCR) | Tinggi | TODO | spike S10 PASS |
| UPDF-502 | Dialog OCR: rentang halaman + bahasa | Tinggi | TODO | — |
| UPDF-503 | Prompt OCR otomatis untuk dokumen scan | Sedang | TODO | — |
| UPDF-504 | Lapisan teks tak terlihat + label jujur | Tinggi | TODO | — |
| UPDF-505 | Tesseract sebagai opsi lanjut | Sedang | TODO | — |
| UPDF-506 | Daftar bahasa OCR (bypass B-05) | Sedang | TODO | — |

## M6–M12 (penomoran lama; lihat kolom "Milestone (baru, A-8)")

| ID | Judul | Milestone (lama) | Milestone (baru, A-8) | Status |
|---|---|---|---|---|
| UPDF-601 | Kompresi & resample + pratinjau delta | M6 | M6 (sementara) | TODO |
| UPDF-602 | Antrean batch + retry | M6 | M6 | TODO |
| UPDF-701 | Enkripsi & permission | M7 | M7 | TODO |
| UPDF-702 | Redaksi aman (termasuk metadata/thumbnail) | M7 | M7 | TODO |
| UPDF-703 | Sanitasi metadata | M7 | M7 | TODO |
| UPDF-801 | Edit teks existing + reflow | M8 | M8 | BLOCKED (B-04) |
| UPDF-802 | Ganti gambar | M8 | M8 | TODO |
| UPDF-901 | PDF → gambar & teks | M9 | M8 | TODO |
| UPDF-902 | Office ↔ PDF | M9 | M8 | DEFERRED (U-05) |
| UPDF-1001 | Tanda tangan gambar | M10 | M9 | TODO |
| UPDF-1002 | Tanda tangan kriptografis | M10 | M9 | DEFERRED (U-06) |
| UPDF-1101 | Command palette & preset | M11 | M6 | TODO |
| UPDF-1102 | Batch resumable | M11 | M6 | TODO |
| UPDF-1201 | Packaging & rilis | M12 | M10 | TODO |
| UPDF-1202 | AI opsional (opt-in) | M12 | M10 (opsional; penempatan menunggu keputusan) | TODO |

---

## Latar Belakang (di luar milestone)

| ID | Judul | Status |
|---|---|---|
| UPDF-032 | Audit lisensi dependency (ID lama: UPDF-901) | **DONE** (`docs/LICENSE_REVIEW.md`) |
| UPDF-033 | Jejak audit dependency (ID lama: UPDF-902) | **DONE** (`docs/DEPENDENCIES.md`) |
| UPDF-903 | Linter workspace (mojibake, link mati) | **DONE** (`scripts/lint.py`) |
| UPDF-904 | Policy upgrade dependency | **DONE** (`docs/UPGRADE_POLICY.md`) |
