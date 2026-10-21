# PROJECT_STATE.md — Status Saat Ini

> Status **saat ini**, bukan riwayat lengkap. Riwayat ada di `SESSION_LOG.md`.

| Field | Nilai |
|---|---|
| Tanggal | 2026-10-21 |
| Waktu | 11:05 WIB (UTC+7) |
| Zona waktu | Asia/Bangkok / SE Asia Standard Time |
| Session ID | `2026-10-21T1114+0700` (controlled restart — penerapan keputusan A-1…A-9, commit lokal, spike terbatas) |
| Fase aktif | **Fase A (analisis referensi) — 3 target selesai**: `docs/ANALYSIS_NITRO14.md` (Nitro 14.41.0.15), `docs/ANALYSIS_STIRLING_PDF.md` (Stirling-PDF 3.2.0), `docs/ANALYSIS_PDFGEAR.md` (PDFgear 3.0.0); sekarang **GATE A (revisi 1) — menunggu keputusan pengguna** (`docs/RESTART_AUDIT.md`) |
| Milestone aktif | **M0 — Foundation** |
| Task aktif | Audit & proposal GATE A revisi 1 **ditulis** → menunggu keputusan (daftar approval di `docs/HANDOFF.md` §0). `UPDF-029`/`030`/`031` DONE (analisis) |
| Git repo | **`github.com/anprar/UnionPDF`** (public, branch `main`) — HEAD `d01cd16` (commit awal `336538a`) |
| Working tree | Tidak bersih — file baru **belum di-commit**: 13 file pra-restart (3 dokumen analisis, 3 skrip verifikasi, 3 session log, 4 file checkpoint) + dokumen sesi `2026-10-21T1057+0700`. **Commit/push belum disetujui** |
| Stack | **Stack final BELUM DISETUJUI.** Implementasi existing: Python 3.13 · PySide6 6.11 · PyMuPDF 1.27 · Windows OCR (ADR-001; status ratifikasi **DISPUTED**, kini berperan sebagai benchmark). Kandidat restart A/B/C: `docs/STACK_EVALUATION.md` §10 |
| Lisensi proyek | `LICENSE` = **AGPL-3.0** (B-01 tercatat selesai 2026-10-20); untuk restart **belum diratifikasi ulang** — tidak diubah |
| Review pasca-REA | v1 (histori, dasar ADR-001): `docs/POST_REA_TECH_REVIEW.md`. Pasca-tiga-referensi: `docs/POST_ALL_REFERENCES_TECH_REVIEW.md` (**DRAFT**, tanpa keputusan) |
| Inspeksi biner referensi | **DIIZINKAN & DILAKUKAN** (B-02 selesai) |
| Status REA | **Tiga target dianalisis** (Nitro 14 native C++/MFC · Stirling-PDF Tauri+Spring Boot/PDFBox · PDFgear .NET 4.6.2 WPF + 4 pustaka PDF + 2 engine OCR + Copilot 27 aksi) — 35 operasi REA total. **Metode #2 (observasi UI runtime) & #3 (uji I/O) NOT_RUN pada ketiganya**; unknown terbuka: 4 lama (U-01/U-04/U-05/U-06) + 8 (S-01…S-08) + 8 (G-01…G-08) |

---

## Status persetujuan (controlled restart)

**Tetap berlaku:** stack final **BELUM DISETUJUI** · cleanup aplikasi lama **BELUM
DISETUJUI** · `LICENSE`/`NOTICE` tidak diubah, lisensi belum diratifikasi ulang ·
**tidak ada izin push/publikasi** · tidak ada scaffold penuh/aplikasi produksi.

Keputusan pengguna 2026-10-21 (sesi `2026-10-21T1114+0700`):

| ID | Lingkup | Status |
|---|---|---|
| A-1 | Urutan kriteria evaluasi | **REVIEW** — arah prioritas pengguna diterapkan di `STACK_EVALUATION.md` §10.2b; menunggu konfirmasi final |
| A-2 | Anggaran ukuran | Acuan awal: installer core ≤ 250 MB, instalasi core ≤ 750 MB; saat ini ukuran mengikuti kebutuhan library; wajib dilaporkan terpisah |
| A-3 | Redaksi token PostHog & path profil | **Disetujui & diterapkan** |
| A-4 | Perbaikan `TASKS.md` & indeks sesi | **Disetujui & diterapkan** |
| A-5 | Commit lokal tanpa push (bersyarat) | **Disetujui** — pelaksanaan & daftar path di `docs/sessions/2026-10-21T1114+0700.md` |
| A-6 | Spike RS-00, RS-01, bagian PDFium RS-02/03/05 | **Disetujui** (instalasi lokal-proyek saja) |
| A-7 | Lokasi `experiments/restart/` | **Disetujui** |
| A-8 | Milestone protokol restart (M9 Signature, M10 Release) | **Disetujui & diterapkan** |
| A-9 | Pembaruan terbatas `AGENTS.md` | **Disetujui & diterapkan** (§5, §5b) |

Riwayat K-1…K-10 (sesi `2026-10-21T1057+0700`): `docs/RESTART_AUDIT.md` §1.

**Blocker sebelumnya:**
- ~~PUB-1~~ — project token PostHog pihak ketiga (klasifikasi dikoreksi: menurut dok
  resmi PostHog boleh publik, bukan personal API key) — **disamarkan**; tidak ada di
  commit lokal mana pun.
- ~~DOC-1~~ — defek `docs/TASKS.md` — **diperbaiki** (mapping ID di `TASKS.md`).

## Fitur yang sudah berfungsi (implementasi lama — benchmark)

| Fitur | Status | Bukti |
|---|---|---|
| Buka dokumen PDF | **DONE** | `tests/test_engine.py`, smoke test |
| Render halaman + text layer | **DONE** | spike S1 (33,87 ms/hlm @2×) |
| Panel thumbnail | **DONE** | `tests/test_ui_smoke.py` |
| Zoom / fit width / fit page | **DONE** | `tests/test_ui_smoke.py` |
| Navigasi halaman | **DONE** | `tests/test_ui_smoke.py` |
| Pencarian teks | **DONE** | spike S1, `tests/test_ui_smoke.py` |
| Save As + verifikasi output | **DONE** | `tests/test_engine.py` (verification mismatch terdeteksi) |
| Operasi halaman (merge/split/rotate/delete/duplicate/reorder/extract) | **DONE (engine)** | `tests/test_engine.py` |
| Penulisan atomik (temp → verifikasi → final) | **DONE** | `tests/test_infrastructure.py` |
| Tampilan UI dasar (toolbar, menu, status bar, tema) | **DONE** | `scripts/smoke_app.py` |

## Fitur parsial

| Fitur | Yang sudah | Yang belum |
|---|---|---|
| Anotasi | API engine terverifikasi (spike S3) | Tidak ada UI |
| Form | API engine terverifikasi (spike S4) | Tidak ada UI |
| Redaksi | API engine terverifikasi + aman (spike S5) | Tidak ada UI; metadata/thumbnail belum diuji (L-07) |
| OCR | Windows OCR jalan (spike S10) | Tidak ada UI; daftar bahasa tidak bisa dienumerasi (E-216) |
| Background job | `JobRunner` + `CancelToken` ada | Belum dipakai UI |

## Build terakhir

| Item | Nilai |
|---|---|
| Build aplikasi | **N/A** — belum ada packaging (B-03) |
| Import aplikasi | **PASS** — `python -m unionpdf.app` jalan (offscreen) |
| Smoke test | **PASS** — 9/9 pemeriksaan |
| Test suite | **PASS** — 69 pytest (2026-10-20 18:29; tidak dijalankan ulang sejak itu) |

## Test terakhir

| Suite | Hasil | Waktu |
|---|---|---|
| `pytest tests -q` | **69 passed** | 2026-10-20 18:29 |
| `scripts/smoke_app.py` | **9/9 PASS** | 2026-10-20 18:29 |
| `scripts/lint.py` | **0 temuan** | 2026-10-20 18:29 |
| Spike S1–S12 | 9 PASS · 1 PASS bersyarat · 2 NOT AVAILABLE | 2026-10-20 16:35 |

## Repository publik

| Item | Nilai |
|---|---|
| URL | <https://github.com/anprar/UnionPDF> |
| Visibilitas | Public |
| Branch default | `main` |
| Commit awal | `336538a` — feat(unionpdf): M0 — fondasi, analisis referensi mendalam, dan vertical slice viewer |
| Isi | 89 blob, 0,4 MB (tanpa `.venv`, tanpa spike output, tanpa korpus mentah) |
| Topik | pdf, pdf-editor, windows, python, pyside6, agpl-3-0, desktop-app, ocr, reverse-engineering |
| Source offer | `src/unionpdf/about.py` → `SOURCE_URL`, tampil di dialog "Tentang"; diuji oleh `tests/test_license_compliance.py` |


## Inventory workspace

| Area | Jumlah |
|---|---|
| Dokumen `docs/` | 42 berkas `.md` (7.930 baris) |
| Kode produksi `src/unionpdf/` | 1.515 baris, 19 modul |
| Test `tests/` | 527 baris, 4 modul + `conftest.py` |
| Skrip `scripts/` | 708 baris, 11 berkas (termasuk 4 alat analisis biner) |
| Spike `spikes/` | 828 baris, 5 skrip, 25 berkas hasil |
| Total berkas workspace | 120 (di luar `.venv`) |

## Blocker aktif

| ID | Ringkas | Perlu apa | Status |
|---|---|---|---|
| ~~B-01~~ | Lisensi proyek | — | ✅ **SELESAI** — AGPL-3.0, open source; `LICENSE` + `NOTICE` dibuat |
| ~~B-02~~ | Izin inspeksi biner | — | ✅ **SELESAI** — diizinkan & dilakukan (analisis v2) |
| **B-03** | Ukuran distribusi & build EXE belum terukur | Build one-dir (PyInstaller belum dipasang) | Terbuka |
| **B-04** | Edit teks existing dengan reflow (M8) belum dibuktikan | Spike content-stream surgery | Terbuka — **makin prioritas**, fitur ini terkonfirmasi ada di v14 |
| **B-05** | `Windows.Media.Ocr` tidak bisa enumerasi bahasa lewat binding 3.2.1 | Sumber daftar bahasa alternatif | Terbuka |

Detail: `docs/BLOCKERS.md`.

## Analisis referensi v2 (inspeksi biner read-only)

| Item | Nilai |
|---|---|
| String UI dari 35 berkas `.mui` | **14.452** |
| Kontrol ribbon | **783** (14 tab + 90 toolbar kontekstual) |
| Identifier fitur | **10.284** |
| Analisis native Ghidra (`np_pdfa.dll`) | 1.852 prosedur, 1.165 string |
| Resource tree `NitroPDF.exe` | PE32+, 15 tipe resource |

Berkas: `docs/REA_FINDINGS.md` v2, `docs/research/V14_RIBBON_STRUCTURE.md`,
`docs/research/V14_UI_EVIDENCE.md`.

## Perubahan belum terverifikasi

| Perubahan | Status |
|---|---|
| Penulisan atomik `atomic_write` | Teruji unit — **belum** dipakai oleh jalur save UI (UI masih memanggil `engine.write` langsung) |
| `JobRunner` | **belum** dipakai UI |
| `RenderCache` | Dipakai, tetapi belum ada pengukuran memory |
| Theme/QSS | **NOT_RUN** — belum diuji visual pada display nyata |

## Langkah berikutnya

1. **Menunggu keputusan pengguna** atas daftar approval di `docs/HANDOFF.md` §0.
2. Setelah disetujui: tangani prasyarat publikasi (PUB-1) dan defek `TASKS.md` (DOC-1).
3. Setelah keputusan prioritas & toleransi ukuran: eksekusi spike fase 1
   (`docs/TECH_SPIKES.md` §R.3) — hanya bila disetujui, termasuk instalasinya.
4. Keputusan baseline → ADR baru (ADR-001 tidak diedit diam-diam).
5. Cleanup Fase 2–3 (`docs/CLEANUP_PLAN.md`) hanya setelah keputusan baseline.

Task implementasi lama (`UPDF-012` … `UPDF-016`) **ditahan** sampai keputusan baseline.
