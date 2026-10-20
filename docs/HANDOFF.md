# HANDOFF.md — Posisi Kerja

> Untuk sesi berikutnya. Baca bersama `PROJECT_STATE.md` dan `TASKS.md`.

**Sesi terakhir:** `2026-10-20T1800+0700` · 2026-10-20 18:29 WIB (UTC+7)
**Fase:** M0 — Foundation · Fase A (analisis referensi) **DITUTUP**
**Sesi sebelumnya:** `2026-10-20T1700+0700` · `2026-10-20T1624+0700`

---

## 1. Posisi saat ini

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

Tidak ada. Semua perubahan tersimpan.

## 5. Perubahan belum terverifikasi

Lihat `PROJECT_STATE.md` § "Perubahan belum terverifikasi":
jalur atomic write belum dipakai UI, `JobRunner` belum dipakai UI, QSS belum
diuji visual, `RenderCache` belum diukur memory-nya.

## 6. Perintah berikutnya

```powershell
cd D:\dokumentasi\Project\UnionPDF
.\.venv\Scripts\python.exe -m pytest tests -q
```

Setelah itu, task aktif berikutnya adalah `UPDF-012` (lihat `TASKS.md`).

## 7. Hasil yang diharapkan

- `pytest` → 55 passed (baseline saat ini).
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
- Perbandingan stack A/B/C/B' + pembobotan — **jangan** buka ulang; sudah
  dikonfirmasi pada §18 `POST_REA_TECH_REVIEW.md`.
- **Ekstraksi UI biner v14** (14.452 string, 783 kontrol) — **jangan** ulangi;
  hasilnya sudah di `docs/research/*.json` (lokal, tidak di-commit).
- Inventaris bahasa OCR (20 paket) — **jangan** ulangi.
- Penyiapan venv + daftar dependency — sudah ada di `requirements*.txt`.
- Struktur `src/unionpdf/` — sudah sesuai ADR-001.
- Berkas `LICENSE` + `NOTICE` + repo publik — sudah dibuat.
- Metadata `src/unionpdf/about.py` — jangan diduplikasi; itu satu-satunya
  sumber kebenaran untuk tautan source.

## 10. Lima langkah berikutnya

1. **UPDF-012** — sambungkan `Save As` ke `atomic_write` + verifikasi →
   `src/unionpdf/ui/main_window.py`, `src/unionpdf/infrastructure/file_store.py`.
2. **UPDF-013** — operasi halaman di UI (putar, hapus, gabung) memakai
   `JobRunner` + progress + cancel → `src/unionpdf/ui/`, `application/jobs.py`.
3. **UPDF-015** — spike edit teks existing, **diarahkan T-12**: uji pendekatan
   annotate-layer (redact + reinsert) lebih dulu sebelum content-stream surgery
   → `spikes/spike_06_text_edit.py`.
4. **UPDF-014** — pasang PyInstaller di venv dev, build one-dir, **ukur**
   ukuran → `docs/PACKAGING.md`, `docs/BLOCKERS.md` B-03.
5. **UPDF-022** — checklist pesan error dari `docs/research/V14_UI_EVIDENCE_SUMMARY.md`.

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
