# SECURITY.md — Keamanan & Privasi Dokumen

**Status:** aktif

---

## 1. Prinsip

1. **Pemrosesan lokal secara default.** Tidak ada dokumen yang keluar dari
   mesin kecuali pengguna secara eksplisit mengaktifkan fitur yang networked.
2. **Tidak ada telemetry.** UnionPDF tidak mengirim crash report, usage data,
   atau content hash. (Kebalikan dari aplikasi referensi yang memakai BugSplat.)
3. **Tidak ada AI untuk fungsi inti.** Fitur PDF inti tidak bergantung pada
   layanan berbayar.
4. **Integritas dokumen diutamakan.** Output parsial tidak pernah
   ditampilkan sebagai sukses.
5. **Tidak ada bypass proteksi.** Dokumen terenkripsi/berlisensi dibuka tanpa
   password yang benar.

## 2. Aturan implementasi

| Area | Aturan |
|---|---|
| **Penulisan** | Tulis ke file sementara → tutup & flush → verifikasi → `os.replace` (atomik). Hapus file sementara pada setiap jalur gagal. |
| **Input** | Input **tidak pernah** ditimpa tanpa konfirmasi eksplisit. Default: "Simpan Sebagai". |
| **File terkunci** | Tangkap `PermissionError` → pesan jelas, bukan crash. |
| **Disk penuh** | Tangkap `ENOSPC`/`EDQUOT` → pesan jelas, bersihkan file sementara. |
| **Unicode/path spasi** | Selalu `pathlib.Path`; tidak ada interpolasi string ke shell. |
| **Subprocess** | Selalu list argumen, bukan string shell. Timeout + cancel + exit code + cleanup. |
| **Password** | Tidak pernah disimpan, tidak pernah di-log, tidak pernah ditulis ke pengaturan. |
| **Logging** | Tidak mencatat isi dokumen, teks, atau path berisi data sensitif beyond nama berkas. |
| **Embedded script** | JavaScript dokumen **tidak** dieksekusi. Otomasi PDF dinonaktifkan secara default. |
| **Attachment** | Tidak dieksekusi atau diekstrak otomatis. |
| **Redaksi** | Divergence: isi target harus **tidak dapat diekstrak ulang** setelah redaksi. Kotak hitam visual **bukan** bukti. |
| **Metadata** | Sanitasi metadata opsional; hapus XMP/author/producer bila diminta. |
| **Telemetri** | Tidak ada. Tidak pernah aktif secara default. |

## 3. Model ancaman (ringkas)

| Ancaman | Mitigasi |
|---|---|
| DokumenTJ kehabisan ruang saat ditulis | Temp file + atomic replace + pembersihan pada gagal |
| Output rusak dianggap sukses | `VerificationResult` wajib; UI menampilkan peringatan bila verifikasi gagal |
| Dokumen bermuatan skrip berbahaya | JavaScript tidak dieksekusi; attachment tidak dibuka otomatis |
| Penghapusan data sensitif yang tidak tuntas | Redaksi diverifikasi lewat ekstraksi ulang; channel metadata punya test terpisah (L-07) |
| Path traversal lewat nama berkas | `pathlib` + normalisasi; tidak ada concatenasi string |
| Password bocor | Tidak disimpan, tidak di-log, hanya ada di memori selama operasi |
| Dependencies---|---|

## 4. Pelaporan kerentanan

Belum ada kebijakan publik (UnionPDF belum dipublikasikan). Saat dipublikasikan,
akan ditambahkan di `README.md` dan `SECURITY.md`.

## 5. Status Dependency Security

| Aspek | Status |
|---|---|
| Pemindaian kerentanan dependency | **NOT_RUN** — belum ada tool yang dikonfigurasi |
| SBOM | **NOT_RUN** |
| Code signing | **Belum tersedia** — lihat `docs/PACKAGING.md` |
| Hash verifikasi build | **NOT_RUN** |
