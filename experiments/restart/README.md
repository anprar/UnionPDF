# experiments/restart — Spike terbatas controlled restart

| Field | Nilai |
|---|---|
| Persetujuan | A-6 (RS-00, RS-01, bagian PDFium RS-02/03/05) dan A-7 (lokasi ini), 2026-10-21 |
| Status stack | **BELUM DISETUJUI** — spike ini **tidak** mengesahkan PDFium sebagai engine lengkap |
| Sesi | `2026-10-21T1114+0700` |

Eksperimen ini terpisah dari `src/`, `tests/`, dan `spikes/` lama. Tidak ada kode di sini
yang boleh diimpor ke aplikasi produksi.

## Struktur

| Path | Isi | Dilacak Git |
|---|---|---|
| `pdfium-spike/src/` | Source Rust spike | ya |
| `pdfium-spike/Cargo.toml`, `Cargo.lock` | Manifest & lockfile dependency | ya |
| `deps/PROVENANCE.md` | Hasil RS-00: versi, penerbit, provenance, lisensi | ya |
| `deps/download/`, `deps/pdfium/` | Arsip & biner PDFium | tidak |
| `fixtures/generate_fixtures.py`, `fixtures/FIXTURES.md` | Generator fixture sintetis + manifest (hash) | ya |
| `fixtures/generated/` | PDF fixture hasil generator | tidak (dibuat ulang) |
| `verify/verify_independent.py` | Pembaca independen (PyMuPDF di `.venv`) | ya |
| `raw/` | Output mentah spike (JSON, PDF, PNG) | tidak — **bukti mentah, bukan cache bebas hapus** |
| `results/` | Ringkasan hasil & bukti per spike | ya |
| `.cargo-home/` | Cache Cargo lokal-proyek (`CARGO_HOME`) | tidak |

## Aturan

- Instalasi hanya lokal-proyek: `CARGO_HOME` diarahkan ke `.cargo-home/`; toolchain Rust
  yang ada dipakai apa adanya (tidak di-upgrade); tidak ada instalasi global/admin.
- Fixture sintetis saja; tidak memakai PDF pribadi atau dokumen referensi.
- Engine yang diuji (PDFium) tidak dipakai untuk membuat fixture-nya; fixture dibuat
  dengan PyMuPDF 1.27.2.2 yang sudah ada di `.venv`, dan PyMuPDF juga dipakai sebagai
  pembaca independen.
- Semua angka dicatat apa adanya; tidak ada target performa yang dikarang.

## Kriteria yang ditetapkan sebelum verifikasi independen

Ditulis sebelum `verify/verify_independent.py` dijalankan (sesi `2026-10-21T1114+0700`):

| Kriteria | Ambang / aturan |
|---|---|
| Render PDFium vs PyMuPDF (RS-01) | Grayscale mean absolute difference (MAD) per halaman ≤ **10,0** (skala 0–255) pada skala 2,0 → cocok. Persentase piksel dengan selisih > 64 dicatat sebagai info |
| Anotasi terlihat (RS-02) | Pada area anotasi, ≥ **1 %** piksel berbeda (> 16) antara render dengan vs tanpa anotasi, di PDFium **dan** di PyMuPDF |
| Teks (RS-01) | Fixture Latin: semua baris harus cocok. Fixture Unicode/Arab: dicatat; ketidakcocokan diklasifikasikan engine vs fixture dengan membandingkan ekstraksi PyMuPDF |
| Struktur (RS-05) | **Wajib untuk semua operasi:** jumlah, urutan (via teks), rotasi halaman benar; output dibuka PyMuPDF tanpa repair/warning. **Dalam scope untuk operasi in-place** (rotate, delete, reorder, insert, merge-append): bookmark, link internal, anotasi, field form pada halaman yang tersisa tetap valid. **Hanya diamati** untuk operasi impor ke dokumen baru (merge-new, extract, split) |
| Input | SHA-256 semua fixture sama sebelum & sesudah spike |

## Reproduksi (ringkas)

```powershell
cd D:\dokumentasi\Project\UnionPDF\experiments\restart
..\..\.venv\Scripts\python.exe fixtures\generate_fixtures.py
$env:CARGO_HOME = "$PWD\.cargo-home"
cargo run --release --manifest-path pdfium-spike\Cargo.toml -- all
..\..\.venv\Scripts\python.exe verify\verify_independent.py
```

Detail command, versi, dan hasil: `results/`.
