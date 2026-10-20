# HANDOFF.md — Posisi Kerja

> Untuk sesi berikutnya. Baca bersama `PROJECT_STATE.md` dan `TASKS.md`.

**Sesi terakhir:** `2026-10-20T1700+0700` · 2026-10-20 17:21 WIB (UTC+7)
**Fase:** M0 — Foundation · Fase A (analisis referensi) **v2 selesai**
**Sesi sebelumnya:** `2026-10-20T1624+0700`

---

## 1. Posisi saat ini

Dua blocker besar **sudah ditutup**:
- **B-01** → lisensi proyek **AGPL-3.0**, open source. `LICENSE` + `NOTICE` dibuat.
- **B-02** → inspeksi biner read-only **diizinkan & dilakukan**.

Analisis referensi kini **jauh lebih kuat**: 14.452 string UI asli, 783 kontrol
ribbon (14 tab + 90 toolbar kontekstual), 10.284 identifier fitur, plus analisis
native Ghidra atas `np_pdfa.dll` (1.852 prosedur). Struktur UI v14 yang tadinya
"mustahil diamati" kini **terekstraksi** dari binary.

Stack **tidak berubah** — tinjauan ulang pasca-v2 (`POST_REA_TECH_REVIEW.md` §18)
mengonfirmasi skor tetap 463/500.

Fondasi + vertical slice M1 tetap berjalan: 55 pytest PASS, smoke 9/9 PASS.

## 2. Langkah terakhir yang BERHASIL

`REA search_strings` pada `np_pdfa.dll` → menemukan pola
`AVCmdHandler*_RegisterCommandsProc` / `_WorkProc` dan `*_plugin::init`, yang
membuktikan arsitektur command-handler per fitur. Lihat
`docs/REA_FINDINGS.md` §5.

## 3. Langkah terakhir yang GAGAL

| Kegagalan | Akar masalah | Perbaikan |
|---|---|---|
| REA `binary_overview` pada `NitroPDF.exe` (16 MB CEF) | Ghidra timeout import (330 s) | Pivot ke modul kecil (`np_pdfa.dll` → berhasil) + jalur target-free `inspect_pe_resources` + parser PE sendiri. Dicatat sebagai `U-08`. |
| Parser resource PE: `struct.error: unpack_from requires a buffer of at least 955774581 bytes` | Offset subdirektori resource relatif terhadap **root** resource directory, bukan direktori aktif | Perbaiki `walk_resource_dir` → ekstraksi 14.452 string berhasil |
| Edit §18 `POST_REA_TECH_REVIEW.md` menimpa header §1 | `oldString` mencakup header yang terhapus | Pulihkan §1 + pindahkan §18 ke akhir lewat skrip penyusun |

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
| B-04 | Kapan membangun edit teks existing? | Menentukan cakupan M8 |
| — | Inisialisasi git + nama repo? | Menentukan cara memenuhi kewajiban "source offer" AGPL |
| — | Host repository (GitHub/GitLab)? | Menentukan URL source offer di dialog "Tentang" |

## 9. Kerja yang SUDAH selesai — jangan diulang

- Inventaris folder referensi (nama modul + versi) — **jangan** ulangi.
- Spikes S1–S12 — **jangan** ulangi; hasil ada di `spikes/out/*.json`.
- Perbandingan stack A/B/C/B' + pembobotan — **jangan** buka ulang; sudah
  dikonfirmasi pada §18 `POST_REA_TECH_REVIEW.md`.
- **Ekstraksi UI biner v14** (14.452 string, 783 kontrol) — **jangan** ulangi;
  hasilnya sudah di `docs/research/*.json`. Skripnya ada di `scripts/`.
- Penyiapan venv + daftar dependency — sudah ada di `requirements*.txt`.
- Struktur `src/unionpdf/` — sudah sesuai ADR-001.
- Berkas `LICENSE` + `NOTICE` — sudah dibuat.

## 10. Lima langkah berikutnya

1. **UPDF-012** — sambungkan `Save As` ke `atomic_write` + verifikasi →
   `src/unionpdf/ui/main_window.py`, `src/unionpdf/infrastructure/file_store.py`.
2. **UPDF-013** — operasi halaman di UI (putar, hapus, gabung) memakai
   `JobRunner` + progress + cancel → `src/unionpdf/ui/`, `application/jobs.py`.
3. **UPDF-015** — spike edit teks existing (redact + reinsert vs content-stream
   surgery) → `spikes/spike_06_text_edit.py`. **Lebih prioritas** karena
   analisis v2 mengonfirmasi fitur ini nyata di v14 (`NitroTextEditing`).
4. **UPDF-014** — pasang PyInstaller di venv dev, build one-dir, **ukur**
   ukuran → `docs/PACKAGING.md`, `docs/BLOCKERS.md` B-03.
5. **UPDF-022** — turunkan korpus pesan error v14 jadi checklist uji UnionPDF
   (sumber: `docs/research/V14_UI_EVIDENCE.md`).

## 11. Peringatan

- `scripts/lint.py` **wajib** dijalankan setiap kali selesai menulis dokumen —
  karakter CJK/Hangul pernah masuk beberapa kali (bug berulang). Perbaikannya
  ada di `scripts/repair_docs.py`.
- `docs/research/V14_UI_EVIDENCE.md` memuat label yang **tidak semuanya**
  diverifikasi sebagai aktif pada build ini — perlakukan sebagai indikasi.
- Jangan buat commit tanpa izin pengguna. `git` belum diinisialisasi.
- `spikes/` **terpisah** dari `src/`. Jangan import spike ke kode produksi.
- Ghidra **tidak bisa** menganalisis `NitroPDF.exe` (16 MB, CEF) dalam batas
  startup default. Jangan coba berulang tanpa menaikkan
  `REA_GHIDRA_STARTUP_TIMEOUT_MS` di environment REA.
