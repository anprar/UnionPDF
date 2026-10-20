# DEPENDENCIES.md

**Status:** DRAFT v1 · **Tanggal:** 2026-10-20
Semua versi di-pin. Tidak ada `latest` tanpa lockfile.

---

## 1. Dependency runtime (wajib)

| Paket | Versi | Fungsi | Sumber | Lisensi | Komponen native | Runtime tambahan | Wajib redistribusi |
|---|---|---|---|---|---|---|---|
| `pymupdf` | 1.27.2.2 | Engine PDF: render, text, halaman, anotasi, form, redaksi, enkripsi | PyPI / Artifex | **AGPL-3.0** atau komersial | `mupdfcpp64.dll` 24,46 MB, `_mupdf.pyd` 11,75 MB | Tidak | Ya (lisensi + sumber MuPDF) |
| `PySide6` | 6.11.0 | Desktop shell (Qt Widgets) | PyPI / Qt | LGPL-3.0 | `Qt6Core.dll` dkk | Tidak | Ya (lisensi LGPL + sumber pustaka) |
| `Pillow` | 12.3.0 | Manipulasi gambar (ekspor PNG/JPEG, thumbnail) | PyPI | MIT-CMU | Tidak | Tidak | Ya (pertains) |
| `winrt-Windows.Media.Ocr` | 3.2.1 | Binding OCR Windows | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-Windows.Graphics.Imaging` | 3.2.1 | `BitmapDecoder` untuk OCR | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-Windows.Storage` | 3.2.1 | `StorageFile` untuk OCR | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-Windows.Storage.Streams` | 3.2.1 | Tipe stream WinRT | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-Windows.Globalization` | 3.2.1 | `Language` untuk OCR | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-Windows.Foundation` | 3.2.1 | Tipe dasar WinRT | PyPI | MIT | Tidak | Tidak | Ya |
| `winrt-runtime` | 3.2.1 | Runtime WinRT | PyPI | MIT | Tidak | Tidak | Ya |
| `typing_extensions` | 4.16.0 | Kebutuhan winrt-runtime | PyPI | PSF-2.0 | Tidak | Tidak | Ya |

### Dependency opsional

| Paket | Versi | Fungsi | Lisensi | Catatan |
|---|---|---|---|---|
| `tesseract-ocr` (biner) | 5.x | Jalur OCR lanjut | Apache-2.0 | **Bukan** dependensi pip. Dibutuhkan instalasi sistem; UnionPDF mencari path via env `TESSERACT_CMD` / lokasi umum. Tidak wajib untuk M0–M4. |
| `pyHanko` | TBD | Tanda tangan kriptografis (M10) | MIT | Belum dievaluasi — spike terpisah (U-06) |
| `PyInstaller` | TBD | Packaging EXE (M12) | GPL-2.0-or-later + bootloader exception | Belum diuji (B-03) |

### Dependency yang dievaluasi dan DITOLAK

| Paket | Alasan ditolak |
|---|---|
| `winsdk` 1.0.0b10 | Berstatus **beta** (1.0.0b10). Dipakai hanya sebagai fallback saat spike. Master prompt melarang alpha/beta sebagai fondasi. |
| `rapidocr-onnxruntime` | Butuh ±150 MB model ONNX. Ditunda sampai ada kebutuhan nyata (M5+). |
| `pikepdf` / `pypdfium2` | Rute cadangan bila AGPL ditolak (`STACK_EVALUATION.md` §7). |
| `iText 7` | AGPL/komersial. |
| `Aspose.*` | Komersial; trial memberi watermark. |

## 2. Dependency development

| Paket | Versi | Fungsi | Lisensi |
|---|---|---|---|
| `pytest` | 8.3.4 | Test runner | MIT |
| `pyinstaller` | TBD | Build EXE | GPL-2.0-or-later + exception |

## 3. Transitif yang perlu diperhatikan

| Transitif | Asal | Kenapa penting |
|---|---|---|
| `shiboken6` 6.11.0 | PySide6 | Binding C++→Python; wajib ikut. |
| `PySide6_Addons` 6.11.0 | PySide6 | **168,7 MB uncompressed.** Mengandung WebEngine, Charts, 3D, DataVisualization, Multimedia, Designer, PrintSupport, Sql, Test, Xml, Concurrent, Help, Network, OpenGL, Position, Quick, RemoteObjects, Sensors, SpatialAudio, StateMachine, TextToSpeech, UiTools. **Sebagian besar tidak dipakai** → harus di-exclude saat build. |
| `PySide6_Essentials` 6.11.0 | PySide6 | 75,8 MB uncompressed. Memuat Core, Gui, Widgets, Network, PrintSupport, Sql, Test, Xml, Concurrent, OpenGL, Quick, UiTools, SpatialAudio, StateMachine, TextToSpeech, Help, RemoteObjects, WebSockets, Position, Sensors, WebChannel, WebEngineCore, WebEngineWidgets. **WebEngine dan Sql tidak dipakai** → exclude. |
| `pluggy` 1.5.0 | pytest | — |
| `iniconfig` 2.0.0 | pytest | — |
| `packaging` 26.3 | pytest | — |
| `colorama` 0.4.6 | pytest | — |

## 4. Ukuran payload native terukur

| Komponen | Ukuran | Sumber |
|---|---|---|
| `mupdfcpp64.dll` | 24,46 MB | spike S12 |
| `_mupdf.pyd` | 11,75 MB | spike S12 |
| `mupdf.py` | 2,48 MB | spike S12 |
| Total paket pymupdf di disk | **50,62 MB** | spike S12 |
| `pyside6_addons` wheel (uncompressed) | 168,7 MB | pip log |
| `pyside6_essentials` wheel (uncompressed) | 75,8 MB | pip log |

**Ukuran EXE final: `NOT_MEASURED`.** Belum ada build. Lihat `B-03`.

## 5. Aturan versi

1. Versi di-pin eksak di `requirements.txt` (dibuat di M1).
2. `requirements-dev.txt` untuk tooling.
3. Upgrade hanya lewat task terpisah + regression test + catatan di
   `CHANGELOG.md` + `UPGRADE_POLICY.md`.
4. Jangan upgrades besar di tengah milestone.
5. Simpan `pip freeze` snapshot setelah tiap upgrade.

## 6. Pemeriksaan lisensi dependency

Lihat `LICENSE_REVIEW.md` untuk audit lengkap dan kewajiban redistribusi.
