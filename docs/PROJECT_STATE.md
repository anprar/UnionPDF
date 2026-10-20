# PROJECT_STATE.md — Status Saat Ini

> Status **saat ini**, bukan riwayat lengkap. Riwayat ada di `SESSION_LOG.md`.

| Field | Nilai |
|---|---|
| Tanggal | 2026-10-20 |
| Waktu | 17:21 WIB (UTC+7) |
| Zona waktu | Asia/Bangkok / SE Asia Standard Time |
| Session ID | `2026-10-20T1700+0700` (lanjutan dari `2026-10-20T1624+0700`) |
| Fase aktif | **Fase A selesai (v2 — analisis mendalam)** · Fase B terkonfirmasi · Fase C selesai |
| Milestone aktif | **M0 — Foundation** |
| Task aktif | `UPDF-012` — Save As → atomic write + verifikasi |
| Git repo | **Belum** diinisialisasi (belum ada izin commit) |
| Working tree | N/A — belum ada repo |
| Stack | **Diputuskan & dikonfirmasi v2** — Python 3.13 · PySide6 6.11 · MuPDF 1.27 · Windows OCR (ADR-001) |
| Lisensi proyek | **AGPL-3.0** (B-01 selesai) — open source |
| Review pasca-REA | **SELESAI + dikonfirmasi v2** — `docs/POST_REA_TECH_REVIEW.md` §18, skor tetap 463/500 |
| Inspeksi biner referensi | **DIIZINKAN & DILAKUKAN** (B-02 selesai) |

---

## Fitur yang sudah berfungsi

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
| Test suite | **PASS** — 55 pytest |

## Test terakhir

| Suite | Hasil | Waktu |
|---|---|---|
| `pytest tests -q` | **55 passed** | 2026-10-20 16:49 |
| `scripts/smoke_app.py` | **9/9 PASS** | 2026-10-20 16:49 |
| `scripts/lint.py` | **0 temuan** | 2026-10-20 16:49 |
| Spike S1–S12 | 9 PASS · 1 PASS bersyarat · 2 NOT AVAILABLE | 2026-10-20 16:35 |

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

1. `UPDF-012` — sambungkan `Save As` UI ke jalur atomik + verifikasi.
2. `UPDF-013` — operasi halaman di UI (rotate/delete/merge) dengan job background.
3. `UPDF-014` — pengukuran ukuran build one-dir (menutup B-03).
4. `UPDF-015` — spike edit teks existing (menutup B-04).
5. `UPDF-016` — panel anotasi & form minimal (M4).
