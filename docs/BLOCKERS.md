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

---

# B-07 — Keputusan yang menunggu persetujuan pengguna

> **Status: Menunggu Persetujuan.**
> Midland atas permintaan pengguna (2026-10-20): keputusan produk & teknologi
> **wajib** dikonfirmasi, tidak cukup hanya didokumentasikan.
> Aturan ini kini codified di `AGENTS.md` §5a.
> Daftar di bawah adalah keputusan yang **sudah saya terapkan** dan
> **perlu ratifikasi** — atau instruksi untuk mengubahnya.

## B-07.1 — Stack baseline (ADR-001)

**Telah diterapkan:** Python 3.13 · PySide6 6.11 · MuPDF 1.27 (PyMuPDF) ·
Windows OCR. Skor 463/500 dibanding 3 kandidat lain.

**Trade-off:** kandidat .NET & Electron gagal karena **tidak punya API authoring
anotasi/form/redaksi** yang permissive → M3–M4 runtuh. Sebaliknya, MuPDF
memaksa lisensi proyek AGPL-3.0 (Anda sudah menyetujui).

**Perlu konfirmasi:** setujui / ubah / minta spike tambahan sebelum dikunci.
**Cara membatalkan:** ADR-002 (bukan edit diam-diam atas ADR-001).

## B-07.2 — Cakupan fitur: 7 REJECT + 30 DEFER

**Telah diterapkan** di `docs/FEATURE_MATRIX.md`.

**REJECT (7):** XFA form · Nitro Sign / cloud sign · Add-in Microsoft Office ·
Integrasi DMS (iManage) · Sensitivity label (MIP) · System tray · PDF Portfolio

**DEFER (30) — yang paling berdampak bagi Anda:**

| Area | Fitur yang ditunda | Dampak ke pengguna |
|---|---|---|
| Konversi | PDF→Word, PDF→Excel, PDF→PowerPoint, Office→PDF | Tidak ada konversi Office sama sekali |
| Tanda tangan | Kriptografis, validasi, pengelolaan private key | Hanya tanda tangan gambar |
| Kepatuhan | PDF/A | Tidak bisa kirim ke arsip yang butuh PDF/A |
| Form | Flatten, import/export data form, field calculation, tab order | Form dasar saja |
| Cetak | Virtual printer (cetak ke PDF) | — |
| Akuisisi | TWAIN scan, barcode scan, barcode field | — |
| Aksesibilitas | PDF/UA tagging | — |
| Integrasi | WebDAV, cloud storage, preview & thumbnail di Explorer | — |
| Distribusi | Auto-update | Update manual |

**Perlu konfirmasi:** apakah ada yang **harus ada** (bukan "nice to have")?

## B-07.3 — Strategi M8 (edit teks existing)

**Telah diterapkan:** DEFER M8; meantime sediakan **overlay teks + redaksi-reinsert**
dengan label jujur (bukan diklaim sebagai "edit teks asli").

**Dasar:** analisis biner v14 menunjukkan "Edit Text" diimplementasikan di
`np_annotations.dll` → pendekatan v14 adalah manipulasi **lapisan anotasi**,
bukan content-stream surgery. Jadi risiko M8 jauh lebih rendah dari dugaan awal.

**Perlu konfirmasi:** maukah M8 dinaikkan prioritasnya sekarang (M7/M8 jadi M5)?

## B-07.4 — Publikasi repository

**Telah diterapkan:** <https://github.com/anprar/UnionPDF> publik, branch `main`,
3 commit, 93 blob. Nama repo & URL **sudah permanen** di dialog "Tentang".

**Perlu konfirmasi:** nama repo & branding final sudah pas? (perubahan nama
repo = tautan lama mati)

## B-07.5 — Publikasi bukti analisis vs hak cipta

**Telah diterapkan:** korpus mentah hasil ekstraksi biner (14.452 string UI,
783 kontrol, 10.284 identifier — ±1,4 MB) **TIDAK** dipublikasikan; hanya
`docs/research/V14_UI_EVIDENCE_SUMMARY.md` (kutipan terkurasi) yang masuk repo.
Alasan: mengindeks string UI proprietary berskala besar = redistribusi.

**Perlu konfirmasi:** setujui batas ini, atau minta lain (mis. mengunggah
korpus penuh ke repo / gist pribadi / tetap lokal).

## B-07.6 — Model lisensi proyek

**Telah disetujui Anda:** AGPL-3.0. Berkas `LICENSE` + `NOTICE` dibuat,
source offer dipasang di dialog "Tentang", 14 test menjaga.
→ **TIDAK perlu konfirmasi ulang.** Disimpan di sini hanya untuk kelengkapan.


---

## B-RT1 - Runtime Java untuk distribusi worker PDFBox

**Prioritas:** Sedang · **Owner:** pengguna · **Blokir:** installer/distribusi fitur authoring
(tidak memblokir development, viewer, atau operasi halaman) · **Status: Menunggu Persetujuan**

**Masalah.** Worker PDFBox butuh Java. Saat ini aplikasi mencari `UNIONPDF_JAVA` → `worker/jre/`
bawaan → `JAVA_HOME` → `PATH`. Di mesin development, `JAVA_HOME` menunjuk OpenJDK 17.0.2 milik
aplikasi lain (`C:\orlansoft_erp\openjdk`) dan **itulah yang dipakai**; komputer pengguna tidak
boleh diasumsikan punya Java. Tanpa Java, fitur authoring (anotasi, form, extract/merge yang
mempertahankan struktur) tidak tersedia dan UI menyembunyikan tombolnya; extract/merge jatuh ke
PDFium dengan peringatan + konfirmasi.

| Opsi | Konsekuensi |
|---|---|
| A. JRE minimal (jlink, JDK 17/21 LTS, mis. Temurin/Zulu, GPLv2+CE) dibawa di `worker/jre/` | Mandiri; tambahan ukuran **NOT_MEASURED** (perlu spike jlink); kewajiban lisensi GPLv2+CE (teks lisensi + sumber tersedia dari vendor) |
| B. Wajibkan pengguna memasang Java | Ukuran kecil; UX buruk, versi tak terkontrol |
| C. Kompilasi worker ke native (GraalVM native-image) | Tanpa JRE; risiko kompatibilitas PDFBox/AWT tinggi; **NOT_MEASURED** |

**Rekomendasi:** A, setelah spike jlink mengukur ukuran dan startup.
**Yang dibutuhkan:** persetujuan arah (A/B/C) dan anggaran ukuran; izin spike jlink (unduh JDK lokal-proyek).

**Status: ~~Menunggu Persetujuan~~ SELESAI - 2026-10-22.** Pengguna memilih opsi A (bundling
runtime Java khusus UnionPDF). Ter PARTY: runtime image Temurin JDK 17.0.20.1 dipangkas dengan
`jlink` -> 53,1 MB, disertakan dalam paket; `docs/decisions/ADR-003-java-runtime-and-packaging.md`.
Fallback ke Java eksternal hanya di build debug atau `UNIONPDF_ALLOW_EXTERNAL_JAVA=1`.
