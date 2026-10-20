# UPGRADE_POLICY.md — Kebijakan Upgrade Dependency

**Status:** aktif

---

## 1. Prinsip

1. **Versi di-pin eksak.** Tidak ada `latest`, `>=`, atau rentang di
   `requirements*.txt`.
2. **Upgrade = task terpisah.** Bukan bagian dari task fitur.
3. **Regresi wajib.** Setiap upgrade menjalankan test suite penuh; kegagalan =
   rollback.
4. **Satu upgrade besar per task.** Jangan mencampur upgrade dengan fitur.
5. **Catat perubahan.** Setiap upgrade menambah entri di `CHANGELOG.md` dan
   `DEPENDENCIES.md`.
6. **Hindari alpha/beta/nightly** untuk fondasi. `winsdk 1.0.0b10` hanya dipakai
   sebagai fallback spike, **bukan** fondasi.
7. **Lockfile disimpan.** `pip freeze > requirements.lock.txt` setelah setup
   yang stabil (tugas terpisah).

## 2. Kapan upgrade

| Pemicu | Tindakan |
|---|---|
| Rilis keamanan | Upgrade segera, task terpisah, regresi penuh |
| Kompatibilitas Python baru | Upgrade setelah M1 stabil |
| Bug engine yang undisputed | Spike dulu → upgrade → regresi |
| "Versi lebih baru tersedia" | **Bukan** alasan |

## 3.Prosedur upgrade

1. Buat task `UPDF-xxx` dengan status `IN_PROGRESS`.
2. `git status` bersih (jika repo sudah ada).
3. Upgrade satu paket.
4. Jalankan `.\scripts\test.ps1` — harus hijau.
5. Jalankan `.\scripts\run_spikes.ps1` — bandingkan angka dengan
   `docs/TECH_SPIKES.md`. Perubahan performa >20% harus dijelaskan.
6. Jalankan `.\scripts\smoke_app.py`.
7. Update `requirements*.txt`, `DEPENDENCIES.md`, `CHANGELOG.md`.
8. Jika gagal → kembalikan versi, catat alasannya di `KNOWN_ISSUES.md`.
9. Checkpoint.

## 4. Dependency yang paling berisiko untuk upgrade

| Paket | Risiko | Mitigasi |
|---|---|---|
| `pymupdf` | API berubah (bukti: `insert_widget` → `add_widget` di 1.27) | Baca changelog; jalankan spike; pin |
| `PySide6` | Perubahan Qt6 minor, sizing policy, QSS | Uji DPI manual; smoke test |
| `winrt-*` | Binding WinRT kecil & jarang; static method bisa hilang (B-05) | Uji spike S10 tiap upgrade |

## 5. Kompatibilitas ke depan yang sudah teramati

| Perubahan | Dampak | Mitigasi |
|---|---|---|
| PyMuPDF 1.27: `Page.insert_widget` → `Page.add_widget` | Kode lama gagal | Sudah terdeteksi di spike; `REA_LIMITATIONS.md` L-08 |
| PyMuPDF 1.27: `Widget.field_fontsize` → `text_fontsize` | Sama | idem |
| PySide6 6.11: `QT_VERSION_STR` tidak ada | Minor | Gunakan `qVersion()` |
| winrt 3.2.1: `get_available_recognizer_languages` tidak diekspos | Fitur | B-05 |
