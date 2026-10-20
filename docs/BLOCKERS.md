# BLOCKERS.md — Hal yang Butuh Keputusan

**Status:** aktif
Setiap blocker harus menyebut: apa masalahnya, apa opsinya, apa konsekuensinya,
dan apa yang dibutuhkan dari pengguna.

---

## B-01 — Lisensi proyek UnionPDF belum diputuskan

**Prioritas:** Tinggi · **Owner:** pengguna · **Blokir:** distribusi binary

**Masalah.** MuPDF/PyMuPDF berada di bawah **AGPL-3.0** (atau lisensi komersial
Artifex berbayar). AGPL-3.0 mensyaratkan karya yang tercakup juga memakai
AGPL-3.0. Artifex menjual lisensi komersial dengan biaya.

**Opsi.**

| Opsi | Konsekuensi |
|---|---|
| **A. AGPL-3.0 (rekomendasi)** | Gratis, boleh didistribusikan binary, **wajib** offer source. Konsisten dengan "gratis tanpa paywall". |
| B. Lisensi komersial Artifex | UnionPDF boleh closed-source, tapi ada biaya lisensi per tahun → bertentangan dengan model gratis. |
| C. Ganti engine ke jalur permissive (pypdfium2 + pikepdf) | Bebas AGPL, tetapi M3–M4 harus ditulis manual, redaksi tertunda, OCR jadi wajib Tesseract. Estimasi +1–2 milestone. |
| D. Tunda keputusan | UnionPDF tetap dapat dikembangkan, tetapi **tidak boleh** didistribusikan sebagai binary. |

**Rekomendasi:** A.

**Yang dibutuhkan:** konfirmasi eksplisit — opsi mana yang disetujui.

**Status:** ~~terbuka~~ **SELESAI — 2026-10-20.** Lisensi proyek ditetapkan
**AGPL-3.0**. UnionPDF akan dipublikasikan sebagai open source dan menjadi
bagian dari portofolio pengguna.

Berkas `LICENSE` (teks AGPL-3.0 lengkap) dan `NOTICE` sudah dibuat di root
workspace. Kewajiban redistribusi tercatat di `docs/LICENSE_REVIEW.md` §5.

---

## B-02 — Izin inspeksi biner aplikasi referensi

**Prioritas:** Sedang · **Owner:** pengguna · **Blokir:** ~~kedalaman analisis~~

**Status:** ~~terbuka~~ **SELESAI — 2026-10-20.** Pengguna **secara eksplisit
mengizinkan** inspeksi biner read-only yang mendalam, dengan tujuan
membangun aplikasi sendiri (bukan menyalin).

**Yang dilakukan (sesuai izin):**
- `REA open_binary` + `binary_overview` pada modul native (Ghidra).
- `REA inspect_pe_resources` pada `NitroPDF.exe` (portable, tanpa disassembler).
- `REA search_strings` pada target aktif.
- Parser PE sendiri (read-only) untuk mengekstraksi resource `RT_STRING` dari
  35 berkas `.mui` → 14.452 string UI.
- Ekstraksi string ASCII/UTF-16 dari 30 modul → 783 kontrol ribbon +
  10.284 identifier fitur.

**Yang TIDAK dilakukan (tetap di luar cakupan, sesuai master prompt §5):**
- Tidak mem-patch executable.
- Tidak mem-bypass aktivasi, trial, paywall, atau lisensi.
- Tidak mengambil product key, token, credential, atau data pengguna.
- Tidak mengubah registry, service, atau konfigurasi Nitro.
- Tidak menyalin kode proprietary, DLL, engine, logo, ikon, atau aset Nitro.
- Tidak mengunggah binary Nitro ke layanan eksternal.
- Tidak menjadikan Nitro dependency runtime UnionPDF.

**Bukti:** `docs/REA_FINDINGS.md` v2, `docs/research/V14_RIBBON_STRUCTURE.md`,
`docs/research/V14_UI_EVIDENCE.md`.

**Catatan batasan alat:** Ghidra **gagal** mengimpor `NitroPDF.exe` (16 MB,
CEF-embedded) dalam batas startup 330 detik. Analisis native penuh dilakukan
pada modul kecil (`np_pdfa.dll`, 656 KB) yang berhasil. Bukti MuPDF/UI
diperoleh dari ekstraksi string, bukan dekompilasi. → `U-08`.

---

## B-03 — Ukuran distribusi belum terukur

**Prioritas:** Sedang · **Owner:** tim · **Blokir:** M12 (tidak memblokir M0–M6)

**Masalah.** MuPDF payload native 50,62 MB; `pyside6_addons` 168,7 MB
(uncompressed). PyInstaller belum dipasang, jadi **belum ada** angka ukuran
EXE. Nomor perkiraan tidak boleh diklaim.

**Rencana.** Pasang PyInstaller di venv dev → build one-dir → **ukur** →
evaluasi trimming (`--exclude-module` untuk WebEngine, Charts, Sql, 3D,
DataVisualization, Multimedia, Designer, Test, Help, TextToSpeech, dll.).

**Yang dibutuhkan:** toleransi ukuran dari pengguna (mis. "di bawah 150 MB"
atau "prioritaskan ringan"). Kriteria trimming memengaruhi B-01.

**Status:** terbuka.

---

## B-04 — Edit teks existing dengan reflow belum dibuktikan

**Prioritas:** Sedang · **Owner:** tim · **Blokir:** M8

**Masalah.** Nitro mengklaim *paragraph-level reflow*. UnionPDF harus jujur:
edit teks in-place + reflow membutuhkan content-stream surgery, pengukuran
ulang font, dan penanganan font tertanam — belum diuji di engine mana pun.

**Opsi.**

| Opsi | Konsekuensi |
|---|---|
| A. Defer penuh ke M8, sediakan overlay + redaksi-reinsert (berlabel jujur) | Aman, cepat, tapi tidak setara Nitro. |
| B. Bangun content-stream surgery sekarang | Risiko tinggi, effort besar, manfaat belum terukur. |
| C. Gunakan pustaka pihak ketiga (iText — AGPL/komersial) | MelanggarChoosing B-01 & biaya. |

**Rekomendasi:** A sampai spike (UPDF-015) memberi bukti.

**Status:** terbuka, tidak memblokir M0–M7.

---

## B-05 — Daftar bahasa OCR tidak bisa dienumerasi

**Prioritas:** Rendah · **Owner:** tim · **Blokir:** M5

**Masalah.** Binding `winrt-Windows.Media.Ocr` 3.2.1 **tidak mengekspos**
`OcrEngine.get_available_recognizer_languages()` (Bukti E-216). Yang tersedia
hanya `try_create_from_user_profile_languages()` dan
`try_create_from_language(Language(...))`.

**Opsi.**

| Opsi | Konsekuensi |
|---|---|
| A. Hardcode daftar + biarkan pengguna mengetik kode bahasa | Cepat; daftar bisa basi bila Windows menambah bahasa. |
| B. Pakai `winsdk` 1.0.0b10 yang mengekspos API tersebut | APIs tersedia, tapi paket **beta** → melanggar prinsip "hindari beta". |
| C. Baca daftar bahasa dari paket language pack Windows | Lebih akurat; perlu riset tambahan. |
| D. Tampilkan input teks bebas untuk kode bahasa | Praktis, tidak perlu daftar. |

**Rekomendasi:** A + D digabung — daftar statis sebagai bantuan, input bebas
sebagai jalur utama.

**Status:** terbuka.
