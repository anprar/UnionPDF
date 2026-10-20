# COMMAND_LOG.md — Indeks Perintah

Perintah penting yang dijalankan pada sesi `2026-10-20T1624+0700`.
Log lengkap ada di `docs/sessions/2026-10-20T1624+0700.md`.

> Tidak ada kredensial, token, atau isi dokumen yang dicatat di sini.

---

## Verifikasi lingkungan

```powershell
[System.Environment]::OSVersion.VersionString
python --version; node --version; git --version
Test-Path "C:\Program Files\Nitro\PDF Pro\14"
Get-ChildItem "C:\Program Files\Nitro\PDF Pro\14" -Force
(Get-Item "C:\Program Files\Nitro\PDF Pro\14\NitroPDF.exe").VersionInfo
```

## Instalasi

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "pymupdf==1.27.2.2" "PySide6==6.11.0" \
    "Pillow==12.3.0" "pytest==8.3.4" --disable-pip-version-check
.\.venv\Scripts\python.exe -m pip install winsdk                       # 1.0.0b10 (beta, fallback)
.\.venv\Scripts\python.exe -m pip install "winrt-Windows.Media.Ocr" \
    "winrt-Windows.Graphics.Imaging" "winrt-Windows.Storage" \
    "winrt-Windows.Globalization" "winrt-Windows.Foundation"          # 3.2.1
.\.venv\Scripts\python.exe -m pip install "winrt-Windows.Storage.Streams"  # 3.2.1
```

Catatan: `winsdk` memerlukan build dari source (≈5 menit) — **tidak** dipakai
sebagai fondasi karena berstatus beta.

## Spike

```powershell
.\.venv\Scripts\python.exe spikes\spike_01_core.py
.\.venv\Scripts\python.exe spikes\spike_02_annotate.py
.\.venv\Scripts\python.exe spikes\spike_03_threading.py
.\.venv\Scripts\python.exe spikes\spike_04_ocr.py
.\.venv\Scripts\python.exe spikes\spike_05_packaging.py
# gabungan:
.\scripts\run_spikes.ps1
```

Hasil: `spikes/out/*.json`.

## Build & uji

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe scripts\smoke_app.py
.\.venv\Scripts\python.exe scripts\lint.py
```

## Aplikasi

```powershell
.\scripts\setup.ps1
.\scripts\run.ps1
.\scripts\run.ps1 -File "D:\contoh\ dokumen.pdf"
```

## Perintah yang gagal (dan perbaikannya)

| Perintah | Gejala | Perbaikan |
|---|---|---|
| `pip install winsdk` | Timeout >5 menit (build dari source) | Pakai paket `winrt-*` terpisah (wheel murni) |
| `Page.insert_widget(...)` | `AttributeError` | `Page.add_widget(...)` (MuPDF 1.27) |
| `Signal` di kelas `QRunnable` | `AttributeError: 'Signal' object has no attribute 'connect'` | Pisahkan `JobSignals(QObject)` |
| `from PySide6.QtCore import QT_VERSION_STR` | `ImportError` | `from PySide6.QtCore import qVersion` |
| `pytest` → `ModuleNotFoundError: unionpdf` | paket tidak di path | `pythonpath = src` di `pytest.ini` + sisipkan di `tests/conftest.py` |
| `self._viewport()` | `AttributeError` | `self.viewport()` |
| Test rotate/duplicate gagal | 2 halaman dari 5 | Semantik engine diperbaiki: ROTATE/DELETE/DUPLICATE mempertahankan semua halaman |
| `StorageFile.get_file_from_path` | `AttributeError` | `StorageFile.get_file_from_path_async(path).get()` |
| `from ...storage import FileAccess` | `ImportError` | `FileAccessMode` |
| `OcrEngine.get_available_recognizer_languages()` | tidak diekspos binding 3.2.1 | Pakai `try_create_from_user_profile_languages()`; lihat B-05 |
