# PACKAGING.md — Rencana Build & Distribusi

**Status:** DRAFT — **belum ada build**. Semua angka ukuran = `NOT_MEASURED`.

---

## 1. Status saat ini

| Item | Status |
|---|---|
| PyInstaller terpasang | ❌ belum |
| Build one-dir | ❌ belum |
| Build one-file | ❌ belum |
| Ukuran EXE | **NOT_MEASURED** |
| Code signing | ❌ belum tersedia |
| Installer (MSI/MSIX/Inno) | ❌ belum |
| Notices & license bundling | ❌ belum |

**Tidak ada klaim "installer berhasil" sebelum benar-benar dibuat dan diuji.**

## 2. Candidate distributions

| Opsi | Command | Ukuran (est.) | Kelebihan | Kekurangan |
|---|---|---|---|---|
| **One-dir** (default) | `pyinstaller --onedir` | **NOT_MEASURED** | Startup cepat, mudah debug, build cepat | Banyak berkas |
| **One-file** | `pyinstaller --onefile` | **NOT_MEASURED** | Satu berkas, mudah dibagikan | Startup lambat (unpack ke temp), build lama |
| **Portable zip** | zip dari one-dir | **NOT_MEASURED** | Mudah dibagikan | Banyak berkas |
| **Inno Setup** | installer `.exe` | **NOT_MEASURED** | UX instalasi bagus | Butuh Inno Setup terpasang |
| **MSIX** | paket MSIX | **NOT_MEASURED** | Integrasi Windows, signing | Persyaratan ketat; tanpa store pun harus trust cert |

**Rekomendasi awal: one-dir + zip portable.** One-file baru jika pengguna
komplain. Alasannya: MuPDF + Qt = payload besar; one-file menambah waktu start.

## 3. Rencana build (UPDF-014)

1. Pasang PyInstaller di venv development (versi di-pin).
2. Buat `unionpdf.spec` dengan:
   - `excludes`: WebEngine, Charts, 3D, DataVisualization, Multimedia, Designer,
     Test, Help, TextToSpeech, Sensors, Position, SpatialAudio, RemoteObjects,
     Sql, Network (bila tidak dipakai), PySide6.QtQml, dst.
   - `datas`: ikon & aset UnionPDF.
   - `hiddenimports`: modul yang dipakai dynamic import.
3. Build one-dir → **ukur** ukuran.
4. Evaluasi: masih besar? → tambah excludes; masih besar? → pertimbangkan
   `pikepdf`+`pypdfium2`? (tidak — itu mengubah stack; lihat ADR-001).
5. Smoke test pada mesin bersih (tanpa Python terpasang).
6. Dokumentasikan hasilnya di sini.

## 4. Estimasi ukuran (bukan hasil)

| Komponen | Ukuran terukur | Sumber |
|---|---|---|
| `pymupdf` di disk | 50,62 MB | spike S12 |
| `pyside6_addons` wheel | 168,7 MB (uncompressed) | pip log |
| `pyside6_essentials` wheel | 75,8 MB (uncompressed) | pip log |

Gabungan di atas **tidak** boleh dijumlahkan menjadi "ukuran EXE" — sebagian
besar library Qt tidak dipakai dan akan di-exclude. Angka final hanya boleh
dinyatakan setelah build.

## 5. Kewajiban lisensi saat distribusi

Lihat `LICENSE_REVIEW.md` §5. Ringkasan:

- [ ] `LICENSE` (AGPL-3.0) di root paket.
- [ ] `NOTICE` + lisensi tiap dependency.
- [ ] Sumber PyMuPDF/MuPDF disediakan (URL + versi, atau lampiran).
- [ ] Lisensi LGPL-3.0 Qt disertakan; sumber Qt dapat diakses.
- [ ] Exe **harus** dapat berjalan dengan versi Qt lain (dynamic linking).
- [ ] Dialog "Tentang" menyebut lisensi UnionPDF + tautan sumber.

## 6. Code signing

**Belum tersedia.** Tanpa signing, Windows SmartScreen akan menampilkan
peringatan untuk executable yang tidak dikenal. **Jangan menjanjikan exe
"tanpa peringatan Windows"** sebelum certificate ada.

## 7. Auto-update

**Ditunda** (M12). Alasan: tool PDF lokal tidak butuh update otomatis yang
berisiko; distribusi manual lebih sederhana. Jika ini akhirnya
dibutuhkan: WinSparkle (sedang dipakai Nitro) atau `pyupdater`.

## 8. Checklist rilis (M12)

- [ ] Build one-dir & one-file
- [ ] Uji pada mesin bersih (tanpa Python, tanpa dependensi dev)
- [ ] Uji: buka, render, simpan, redaksi, OCR
- [ ] Uji: DPI 100/125/150 %
- [ ] Uji: file terkunci, disk penuh, path Unicode
- [ ] Notices & license bundle
- [ ] Tautan sumber offer dalam installer
- [ ] Nomor versi & CHANGELOG
- [ ] Known limitations terdokumentasi
- [ ] (Opsional) code signing
- [ ] SHA-256 dari artefak build dicatat
