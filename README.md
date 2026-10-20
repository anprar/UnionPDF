# UnionPDF

Aplikasi desktop Windows untuk pengolahan PDF — **gratis, offline, tanpa watermark**.

> **Status: DRAFT / fase M0 (Foundation).** Belum ada rilis publik.
> Lihat `docs/START_HERE.md` untuk peta dokumen dan `docs/PROJECT_STATE.md`
> untuk status terkini.

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

## Stack (baseline — lihat ADR-001)

| Lapisan | Pilihan | Lisensi |
|---|---|---|
| Runtime | Python 3.13 | PSF |
| Desktop shell | PySide6 6.11 (Qt 6.11) | LGPL-3.0 |
| Engine PDF | PyMuPDF 1.27 (MuPDF 1.27) | **AGPL-3.0** |
| Pengujian | pytest 8.3 | MIT |

> **Catatan lisensi penting:** PyMuPDF/MuPDF berada di bawah **AGPL-3.0**.
> UnionPDF harus dipublikasikan sebagai AGPL-3.0 agar tetap gratis dan
> bebas dari kewajiban lisensi berbayar. Lihat `docs/LICENSE_REVIEW.md`.

## Kemampuan saat ini

- `NOT_RUN` — belum ada fitur yang dirilis. Fase M0 baru sebatas investigasi,
  keputusan stack, dan scaffold.

## Menjalankan

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
```

Detail: `docs/BUILD_AND_RUN.md`.

## Struktur

```
AGENTS.md            instruksi permanen agent
README.md            file ini
docs/                seluruh dokumentasi kontinuitas & desain
spikes/              eksperimen terisolated (terpisah dari kode produksi)
tests/               pytest: fixtures/, integration/, regression/
scripts/             setup, run, test, build (PowerShell)
```

> Struktur `src/` **belum** dibuat. Master prompt melarang membuat struktur
> source yang terikat framework sebelum keputusan stack. Setelah ADR-001
> disepakati, skeleton dibuat mengikuti konvensi stack terpilih.

## Dokumentasi

| Dokumen | Isi |
|---|---|
| `docs/START_HERE.md` | Peta dokumen + urutan baca |
| `docs/PROJECT_STATE.md` | Status terkini (bukan riwayat) |
| `docs/HANDOFF.md` | Posisi kerja untuk sesi berikutnya |
| `docs/TASKS.md` | Backlog UPDF-xxx |
| `docs/REA_FINDINGS.md` | Hasil analisis aplikasi referensi |
| `docs/FEATURE_MATRIX.md` | Matriks fitur referensi → UnionPDF |
| `docs/STACK_EVALUATION.md` | Perbandingan stack berbobot |
| `docs/POST_REA_TECH_REVIEW.md` | Gate review teknologi pasca-analisis |
| `docs/ARCHITECTURE.md` | Batas modul & kontrak |
| `docs/LICENSE_REVIEW.md` | Audit lisensi dependency |
| `docs/BLOCKERS.md` | Hal yang butuh keputusan pengguna |

## Lisensi proyek

**AGPL-3.0** — ditetapkan 2026-10-20.

AGPL-3.0 dipilih karena MuPDF (engine PDF UnionPDF) berada di bawah AGPL-3.0,
dan model "gratis, open source, tanpa paywall" adalah tujuan produk UnionPDF.
Konsekuensinya: UnionPDF **wajib open-source**, dan source lengkap harus
disediakan saat distribusi.

- `LICENSE` — teks lengkap GNU AGPL v3
- `NOTICE` — komponen pihak ketiga, kewajiban distribusi, dan aset yang
  **tidak** dipakai
- Audit lengkap: `docs/LICENSE_REVIEW.md`
