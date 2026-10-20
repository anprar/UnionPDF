# UnionPDF

![License: AGPL-3.0](https://img.shields.io/badge/Lisensi-AGPL--3.0-blue.svg)
![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB.svg)
![PySide6 6.11](https://img.shields.io/badge/UI-PySide6%206.11-41B883.svg)
![Engine: MuPDF 1.27](https://img.shields.io/badge/Engine-MuPDF%201.27-888888.svg)
![Platform: Windows x64](https://img.shields.io/badge/Platform-Windows%20x64-0078D4.svg)
![Status: M0 Foundation](https://img.shields.io/badge/Status-M0%20Foundation-orange.svg)
![Telemetry: none](https://img.shields.io/badge/telemetry-none-success.svg)

Aplikasi desktop Windows untuk pengolahan PDF: melihat, mengedit, menganotasi,
mengisi formulir, mengoptimasi, menandatangani, dan mengonversi dokumen PDF.

- **Gratis** — tanpa paywall untuk fitur yang sudah diimplementasikan
- **Tanpa watermark** pada hasil ekspor
- **Offline-first** — pemrosesan lokal, tidak ada unggah dokumen
- **Tanpa telemetri** — nol crash-report, nol usage tracking
- **Implementasi independen** — tidak memakai engine atau aset aplikasi referensi

Aplikasi referensi: **Nitro PDF Pro 14.41.0.15** (read-only, di
`C:\Program Files\Nitro\PDF Pro\14`). Dipakai sebagai sumber **kebutuhan**,
bukan sebagai dependency.

> **Status: DRAFT / fase M0 (Foundation).** Belum ada rilis publik.
> Lihat `docs/START_HERE.md` untuk peta dokumen dan `docs/PROJECT_STATE.md`
> untuk status terkini.
> Yang sudah terbukti: **69 test otomatis**, **12 technical spike terukur**,
> 40+ dokumen desain & kontinuitas.

---

## Prinsip

| Prinsip | Konsekuensi teknis |
|---|---|
| Gratis dipakai, tanpa paywall | Tidak ada fitur yang disembunyikan di balik langganan |
| Tanpa watermark ekspor | Tidak ada penandaan dokumen hasil ekspor |
| Offline-first | Tidak ada panggilan jaringan untuk fungsi PDF inti |
| Privasi dokumen | Dokumen tidak pernah keluar dari mesin tanpa persetujuan eksplisit |
| Implementasi independen | Tidak memakai engine, DLL, atau aset aplikasi referensi |
| UI jujur | Tombol yang belum berfungsi disembunyikan atau diberi label status |

## Stack

| Lapisan | Pilihan | Lisensi |
|---|---|---|
| Runtime | Python 3.13 | PSF |
| Desktop shell | PySide6 6.11 (Qt 6.11) | LGPL-3.0 |
| Engine PDF | PyMuPDF 1.27 (MuPDF 1.27) | **AGPL-3.0** |
| OCR | Windows.Media.Ocr (bawaan OS) | API OS |
| Pengujian | pytest 8.3 | MIT |

> **Catatan lisensi:** PyMuPDF/MuPDF berada di bawah **AGPL-3.0**, dan itu
> yang membuat UnionPDF dipublikasikan sebagai AGPL-3.0 — agar tetap gratis
> dan bebas dari kewajiban lisensi berbayar.
> Lihat `docs/LICENSE_REVIEW.md`.

Keputusan stack ditetapkan lewat proses berbobot (4 kandidat dinilai, 12 kriteria,
skor A=463/500) dan **dikonfirmasi ulang** setelah analisis referensi mendalam:
`docs/STACK_EVALUATION.md` dan `docs/POST_REA_TECH_REVIEW.md` §18.

## Kemampuan saat ini

Vertical slice M1 — **berjalan & teruji otomatis**:

- Buka PDF, dengan penanganan error untuk berkas korup dan dokumen terenkripsi
- Render halaman + text layer, zoom, fit width, fit page
- Panel thumbnail, navigasi halaman
- Pencarian teks + lompat ke hasil
- Simpan sebagai dengan **verifikasi output** (jumlah halaman dicek ulang)
- Operasi halaman di engine: merge · split · extract · delete · rotate ·
  duplicate · reorder

Belum tersedia: anotasi & form di UI · OCR di UI · optimasi · redaksi di UI ·
tanda tangan digital · packaging EXE. **Tidak ada tombol mati** — yang belum
ada disembunyikan, bukan diklik dan gagal diam-diam.

## Menjalankan

```powershell
.\scripts\setup.ps1     # buat .venv + pasang dependensi
.\scripts\run.ps1       # jalankan aplikasi
.\scripts\test.ps1      # jalankan test suite
```

Detail: `docs/BUILD_AND_RUN.md`.

## Struktur

```
AGENTS.md            instruksi permanen untuk agent
README.md            file ini
LICENSE / NOTICE     AGPL-3.0 + daftar komponen pihak ketiga
docs/                dokumentasi kontinuitas, desain, dan bukti
src/unionpdf/        kode produksi (domain, application, engine, infra, ui)
spikes/              eksperimen terisolated, terpisah dari kode produksi
tests/               pytest: fixtures/, integration/, regression/
scripts/             setup, run, test, build, dan alat analisis biner
```

## Dokumentasi

| Dokumen | Isi |
|---|---|
| `docs/START_HERE.md` | Peta dokumen + urutan baca |
| `docs/PROJECT_STATE.md` | Status **saat ini** (bukan riwayat) |
| `docs/HANDOFF.md` | Posisi kerja untuk sesi berikutnya |
| `docs/TASKS.md` | Backlog `UPDF-xxx` |
| `docs/PRODUCT_VISION.md` | Untuk siapa, prinsip, batas |
| `docs/REA_FINDINGS.md` | Hasil analisis aplikasi referensi |
| `docs/FEATURE_MATRIX.md` | 97 fitur: referensi → keputusan UnionPDF |
| `docs/STACK_EVALUATION.md` | Perbandingan stack berbobot |
| `docs/POST_REA_TECH_REVIEW.md` | Gate review teknologi pasca-REA |
| `docs/ARCHITECTURE.md` | Lapisan, kontrak, struktur direktori |
| `docs/LICENSE_REVIEW.md` | Audit lisensi (AGPL-3.0) |
| `docs/BLOCKERS.md` | Yang butuh keputusan pengguna |
| `docs/research/V14_UI_EVIDENCE_SUMMARY.md` | Bukti UI v14 (kutipan terkurasi) |

## Lisensi proyek

**AGPL-3.0** — ditetapkan 2026-10-20.

AGPL-3.0 dipilih karena MuPDF (engine PDF UnionPDF) berada di bawah AGPL-3.0,
dan model "gratis, open source, tanpa paywall" adalah tujuan produk UnionPDF.
Konsekuensinya: UnionPDF **wajib open-source**, dan source lengkap harus
disediakan saat distribusi.

**Source:** <https://github.com/anprar/UnionPDF>
(Tautan ini juga tampil di dialog "Tentang" aplikasi — itu adalah
*source offer* yang diwajibkan AGPL-3.0.)

- `LICENSE` — teks lengkap GNU AGPL v3
- `NOTICE` — komponen pihak ketiga, kewajiban distribusi, dan aset yang
  **tidak** dipakai
- Audit lengkap: `docs/LICENSE_REVIEW.md`

## Repository

<https://github.com/anprar/UnionPDF> · Lisensi: AGPL-3.0 · Python 3.13 ·
PySide6 6.11 · MuPDF 1.27 · Windows OCR · Windows x64.
