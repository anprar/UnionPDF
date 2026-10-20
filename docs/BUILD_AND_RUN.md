# BUILD_AND_RUN.md

**Status:** aktif · **Tanggal:** 2026-10-20

---

## 1. Prasyarat

| Item | Versi | Status di mesin ini |
|---|---|---|
| Windows | 10 1809+ / 11 (x64) | ✅ build 26300 |
| Python | 3.13 | ✅ 3.13.9 |
| PowerShell | 5.1+ | ✅ 5.1 |
| Git | opsional | ✅ 2.54 |
| .NET / Rust / Node | **tidak diperlukan** | — |

> UnionPDF memakai **satu runtime** (Python). Node/.NET/Rust tidak dipakai.

## 2. Setup

```powershell
cd D:\dokumentasi\Project\UnionPDF
.\scripts\setup.ps1
```

Yang dilakukan:
1. Membuat `.venv` (lokal, **bukan** instalasi global).
2. `pip install -r requirements.txt` dan `requirements-dev.txt` (versi di-pin).
3. Verifikasi import `pymupdf` & `PySide6`.

Waktu cold start ≈ 1–3 menit (tergantung cache pip; `PySide6_Addons` ≈ 169 MB).

## 3. Jalankan aplikasi

```powershell
.\scripts\run.ps1
.\scripts\run.ps1 -File "D:\dokumen\kontrak.pdf"
```

Manual (tanpa script):

```powershell
$env:PYTHONPATH = "$PWD\src"
.\.venv\Scripts\python.exe -m unionpdf.app
```

## 4. Jalankan test

```powershell
.\scripts\test.ps1
.\scripts\test.ps1 -Verbose
```

Manual:

```powershell
$env:PYTHONPATH = "$PWD\src"
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest tests -q
```

Status saat ini: **55 passed** (`docs/TEST_RESULTS.md`).

## 5. Jalankan smoke test aplikasi

```powershell
.\.venv\Scripts\python.exe scripts\smoke_app.py
```

Menjalankan UI sungguhan secara offscreen, memuat PDF sintetis, lalu memeriksa
9 hal (jendela, dokumen, thumbnail, kanvas, zoom, navigasi, pencarian).

## 6. Jalankan technical spike

```powershell
.\scripts\run_spikes.ps1
.\scripts\run_spikes.ps1 -Only 04
```

Output: `spikes/out/*.json`.

## 7. Linter workspace

```powershell
.\.venv\Scripts\python.exe scripts\lint.py
```

Memeriksa mojibake, tautan markdown mati, dan placeholder tertinggal.
**Jalankan setiap kali selesai menulis dokumen.**

## 8. Packaging

Belum tersedia. Lihat `docs/PACKAGING.md`.

## 9. Struktur perintah

| Skrip | Fungsi |
|---|---|
| `scripts/setup.ps1` | buat venv + pasang dependensi |
| `scripts/run.ps1` | jalankan aplikasi |
| `scripts/test.ps1` | jalankan pytest |
| `scripts/run_spikes.ps1` | jalankan spike |
| `scripts/smoke_app.py` | verifikasi aplikasi jalan |
| `scripts/lint.py` | linter workspace |
| `scripts/repair_docs.py` | perbaiki karakter rusak di dokumen |

## 10. Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: unionpdf` | `PYTHONPATH` belum diset | Gunakan `scripts/run.ps1` / `scripts/test.ps1`, atau set `PYTHONPATH=$PWD\src` |
| `No module named PySide6` | venv belum disiapkan | `.\scripts\setup.ps1` |
| Jendela tidak muncul / crash | Dependensi DirectX/OpenGL | `.\scripts\run.ps1` memakai Qt default; bila bermasalah, set `QT_OPENGL=software` |
| `ImportError: cannot import name 'QT_VERSION_STR'` | Salah API Qt | Gunakan `qVersion()` (lihat `docs/REA_LIMITATIONS.md` L-08) |
| `No tessdata specified` | Tesseract tidak terpasang | Tesseract opsional; pakai Windows OCR (sudah termasuk) |
| Teks Asia tidak terbaca | Font fallback | Dokumen perlu font tertanam; di luar cakupan M1 |
| Gagal menulis ke disk | Path terkunci / tanpa izin | Aplikasi menampilkan pesan; perbaiki izin |
| `winsdk` install sangat lama | Build dari source | Gunakan paket `winrt-*` (wheel murni) — sudah di `requirements.txt` |
