# TEST_PLAN.md

**Status:** aktif · **Target:** M0–M2 dulu, diperluas per milestone.

---

## 1. Prinsip

- **Build sukses bukan bukti fitur benar.**
- **`NOT_RUN` tidak boleh diubah jadi `PASS`.**
- Test yang gagal **tidak** dihapus; test yang tidak berguna diperbaiki dengan
  alasan tertulis.
- Semua fixture **sintetis** atau **legal didistribusikan**. Sumber & lisensi
  dicatat di `tests/fixtures/SOURCES.md` (akan dibuat saat fixture eksternal
  ditambahkan).
- UI: pengujian manual tetap **NOT_RUN** sampai dilakukan.

## 2. Environment uji

| Item | Nilai |
|---|---|
| OS | Windows 11 build 26300, x64, 12 core |
| Python | 3.13.9 (venv `.venv`) |
| pymupdf | 1.27.2.2 (MuPDF 1.27.2.2) |
| PySide6 | 6.11.0 (Qt 6.11.0) |
| pytest | 8.3.4 |
| Platform UI test | `QT_QPA_PLATFORM=offscreen` |
| Tanggal | 2026-10-20 |

## 3. Fixture

| Fixture | Sifat | Dibuat oleh | Lisensi |
|---|---|---|---|
| `simple.pdf` | 5 halaman, text layer, 3 ukuran halaman campuran | `tests/conftest.py` | Sintetis |
| `single.pdf` | 1 halaman | `tests/conftest.py` | Sintetis |
| `secret.pdf` | 2 halaman, berisi 1 string rahasia | `tests/conftest.py` | Sintetis |
| `large.pdf` | 120 halaman | `tests/conftest.py` | Sintetis |
| `encrypted.pdf` | AES-256, password `user123` | `tests/conftest.py` | Sintetis |
| `corrupt.pdf` | Header PDF palsu, body rusak | `tests/conftest.py` | Sintetis |
| `scan_source.pdf` | Gambar pindai sintetis tanpa text layer | `spikes/spike_04_ocr.py` | Sintetis |

> Fixture spike dipakai bersama; tidak ada dokumen pengguna di repo ini.

## 4. Cakupan pengujian

### 4.1 Domain (unit) — `tests/test_domain.py`
- `PageRange`: inklusif, ter-clip, di luar dokumen, rentang kosong, validasi.
- `PageOperation`: rotasi harus kelipatan 90 non-nol; indeks negatif.
- `Document`: `page_count`, akses halaman di luar jangkauan.
- Hierarki exception.

**Status: TERLAMPILUI (DONE).**

### 4.2 Engine (integrasi) — `tests/test_engine.py`
| Uji | Expected |
|---|---|
| Buka PDF valid | 5 halaman |
| Buka berkas hilang | `DocumentError` |
| Buka PDF korup | `DocumentError` |
| Buka PDF terenkripsi | `PermissionDeniedError` |
| Info dokumen | page_count, text layer, versi engine |
| Render | PNG valid; rasio px ≈ pt pada zoom 1; skala linear |
| Render indeks salah | `IndexError` |
| Ekstraksi teks | berisi "Halaman 1" |
| Pencarian | 5 hit; query kosong → 0 |
| Rotate | **jumlah halaman tetap**; rotasi 90 pada halaman terpilih; **sumber tidak dimutasi** |
| Delete | jumlah halaman berkurang; halaman benar hilang |
| Extract | hanya halaman terpilih |
| Duplicate | jumlah halaman +1 per duplikat |
| Reorder | urutan berubah, jumlah sama |
| Merge | jumlah = jumlah dokumen |
| Write | berkas ada, verifikasi PASS |
| Write dengan verifikasi meleset | `verification.passed == False` + notes |
| Write ke direktori bertingkat | direktori dibuat |

**Status: TERLAMPILUI (DONE).**

### 4.3 Infrastruktur — `tests/test_infrastructure.py`
- Atomic write: file tertulis, tidak ada file sementara tertinggal, writer
  gagal → target tidak ada & tidak ada sisa, verifier gagal → finalisasi
  diblokir, output kosong ditolak, direktori induk dibuat.
- `FileStore.unique_path` tidak menimpa.
- Settings: round-trip, JSON korup → default, kunci asing diabaikan.

**Status: TERLAMPILUI (DONE).**

### 4.4 UI smoke — `tests/test_ui_smoke.py` + `scripts/smoke_app.py`
- Jendela dibangun, aksi non-dokumen disabled.
- Muat dokumen → thumbnail terisi, kanvas punya item, judul benar.
- Zoom berubah, fit width berada dalam rentang.
- Navigasi halaman, pencarian mengembalikan hit.
- Tutup dokumen → state bersih.

**Status: TERLAMPILUI (DONE).**

### 4.5 Manual — **NOT_RUN**
Belum dilakukan. Daftar yang harus diuji:
- [ ] Tampilan pada 100 %, 125 %, 150 % DPI
- [ ] Navigasi keyboard penuh (Tab order, shortcut)
- [ ] Pembukaan file terkunci (sedang dibuka di aplikasi lain)
- [ ] Penyimpanan ke direktori tanpa izin tulis
- [ ] Penyimpanan saat disk hampir penuh
- [ ] Path & nama berkas dengan Unicode, spasi, dan karakter khusus
- [ ] Drag & drop berkas ke jendela
- [ ] Opening dokumen besar (1.000+ halaman) — rasa responsif
- [ ] Tampilan night mode / kontras
- [ ] Librarian perilaku ketika dokumen ditutup saat window ditutup

### 4.6 Planned (M2+)
- Redaksi: verifikasi ekstraksi **dan** channel metadata/thumbnail (L-07).
- Form: round-trip seluruh tipe widget (text, checkbox, radio, combo, list, button).
- Anotasi: underline/strikeout/punch + redaction.
- Optimasi: hasil kompresi vs ukuran asli, preservasi elemen.
- OCR: batch + cancel + multi-bahasa.
- Regresi: fixture golden (page count + teks) per versi aplikasi.

## 5. Format hasil uji

Dicatat di `docs/TEST_RESULTS.md` dengan: Test ID, Task ID, Environment,
Input, Langkah, Expected, Actual, PASS/FAIL/NOT_RUN, bukti, keterbatasan.

## 6. Kriteria exit

- `pytest` harus **hijau penuh** sebelum checkpoint.
- Test yang di-skip harus punya alasan tertulis.
- Failure yang diketahui dan diterima → dicatat di `KNOWN_ISSUES.md` dengan ID.
