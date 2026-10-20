# LICENSE_REVIEW.md — Audit Lisensi

**Status:** **KEPUTUSAN DIAMBIL — 2026-10-20** · Lisensi proyek: **AGPL-3.0**
**Penting:** dokumen ini **menjadi blocker distribusi** sampai lisensi proyek
disetujui pengguna (B-01).

> ✅ **B-01 SELESAI.** Pengguna menetapkan UnionPDF sebagai **open source** dan
> bagian dari portofolio pribadi. Lisensi **AGPL-3.0** dipilih — diwajibkan oleh
> MuPDF, konsisten dengan "gratis tanpa paywall", dan asetnya dapat dipublikasikan
> tanpa kewajiban berbayar.
> Berkas `LICENSE` (teks lengkap AGPL-3.0, 661 baris) dan `NOTICE` sudah ada di
> root workspace.

---

## 1. Empat hal yang harus dibedakan

| Istilah | Arti |
|---|---|
| **Gratis digunakan** | Pengguna akhir boleh memakai tanpa biaya |
| **Open source** | Sumber tersedia, boleh diubah dan dibagikan |
| **Boleh didistribusikan** | Tidak melanggar syarat lisensi saat binaries diberikan |
| **Cocok untuk model lisensi UnionPDF** | Konsisten dengan tujuan "gratis, tanpa paywall" |

---

## 2. Lisensi dependency

| Komponen | Lisensi | Boleh dipakai gratis? | Boleh didistribusikan? | Beban tambahan |
|---|---|---|---|---|
| **MuPDF / PyMuPDF** | **AGPL-3.0** (atau lisensi komersial Artifex) | Ya | Ya, **hanya jika** UnionPDF juga AGPL-3.0 | Wajib offer source; wajib beri lisensi; wajib bukaicingk bylaws of the covered work |
| PySide6 / Qt 6 | LGPL-3.0 | Ya | Ya (dynamic linking) | Wajib sertakan lisensi LGPL; sediakan sumber pustaka Qt atau alamat lengkap; izinkan user mengganti versi Qt |
| shiboken6 | LGPL-3.0 | Ya | Ya | Sama seperti PySide6 |
| Pillow | MIT-CMU | Ya | Ya | Wajib sertakan teks lisensi |
| pytest & deps | MIT / PSF | Ya | Ya | Wajib sertakan teks lisensi |
| winrt-* / winrt-runtime | MIT | Ya | Ya | Wajib sertakan teks lisensi |
| Tesseract (opsional) | Apache-2.0 | Ya | Ya | Wajib sertakan NOTICE + lisensi; **tidak boleh** memakai trademark Tesseract |
| PyInstaller (dev) | GPL-2.0-or-later **+ bootloader exception** | Ya | Ya | Exceptioncts-long mengatur tool output tidak menjadi GPL |

## 3. Dampak AGPL-3.0 pada UnionPDF

**FAKTA:** AGPL-3.0 §13 mengharuskan offer source bagi pengguna yang
berinteraksi dengan program melalui jaringan, dan §4–6 mengharuskan
penyebaran versi lengkap dari karya yang tercakup beserta source-nya.

Implikasi praktis:

1. **UnionPDF harus berlisensi AGPL-3.0** agar dapat memakai MuPDF tanpa biaya.
2. Saat distributesbinary, **wajib_identitas_offer source** (URL repo, arsip
   source, atau media).
3. UnionPDF tidak boleh distraibusikan sebagai Closed Source (closed source)
   tanpa lisensi komersial dari Artifex.
4. Modifikasi MuPDF sendiri harus di-publish juga (bila diubah).

**Ini TIDAK melanggar tujuan produk.** Justru ini cara legal صدر dari produk
gratis tanpa paywall: source terbuka, binary gratis, tanpa langganan.

## 4. Keputusan lisensi proyek — **AGPL-3.0 (DIPUTUSKAN)**

**Rekomendasi: AGPL-3.0** — diwajibkan oleh MuPDF, konsisten dengan "gratis
tanpa paywall", dan tidak menambah kewajiban redistribusi. **DITERIMA.**

Berkas terkait di root workspace:
- `LICENSE` — teks lengkap GNU AGPL v3 (diunduh dari gnu.org, 661 baris).
- `NOTICE` — daftar komponen pihak ketiga, kewajiban distribusi, dan catatan
  bahwa UnionPDF tidak memuat aset proprietary pihak lain.

Alternatif yang **tidak** dipilih:

| Alternatif | Konsekuensi |
|---|---|
| MIT / Apache-2.0 | **Tidak mungkin** selama MuPDF dipakai. Memerlukan lisensi komersial Artifex (biaya). |
| Source-available (bukan OSI) | Tidak kompatibel dengan AGPL-3.0 untuk karya yang tercakup. |
| GPL-3.0 (bukan AGPL) | Tidak kompatibel dengan AGPL-3.0 §13. |

## 5. Kewajiban redistribusi (checklist engineering)

- [ ] Sertakan `LICENSE` (AGPL-3.0) di root paket distribusi.
- [ ] Sertakan `NOTICE` + lisensi tiap komponen.
- [ ] Sertakan sumber PyMuPDF/MuPDF: cara paling sederhana → sertakan URL
      git resmi + nomor versi, atau lampirkan tarball sumber.
- [ ] Sertakan lisensi LGPL-3.0 Qt dan **tawarkan** sumber Qt (dynamic linking).
- [ ] Pastikan exe dapat berjalan dengan Qt versi lain yang pengguna Miliki
      (dynamic linking, bukan static).
- [ ] Tampilkan dialog "Tentang" yang menyebut: nama, versi, lisensi
      UnionPDF, dan tautan sumber.
- [ ] Dokumentasikan setiap dependensi dalam `DEPENDENCIES.md` (sudah ada).

## 6. Hal yang belum sicher

| # | Item | Status |
|---|---|---|
| 1 | Keputusan lisensi proyek final | ✅ **SELESAI — AGPL-3.0** |
| 2 | Cara satisfy LGPL di build PyInstaller | **NOT_RUN** — harus diuji di M12 |
| 3 | Dampak "source offer" pada UX installer | **UNKNOWN** |
| 4 | Apakah ada komponen yang memaksa GPL-3.0 (mis. Ghostscript)? | Tidak dipakai — Ghostscript **tidak** masuk UnionPDF |
| 5 | URL publik repository untuk source offer | **Menunggu** — bergantung pada pengguna memilih host & nama repo |
| 6 | Code signing certificate | **Belum tersedia** |

## 7. Yang DITOLAK secara sengaja

| Aset | Alasan |
|---|---|
| Engine/DLL Nitro (`npdf.dll`, `idrspdf15.dll`, `libcef.dll`, dll.) | Proprietary; tidak boleh dipakai atau disalin |
| Ikon/logo Nitro | Aset merek |
| Font berlisensi khusus | Bukan perlu; pakai font sistem atau berlisensi bebas |
| Ghostscript (GPL) | Tidak diperlukan; menambah kewajiban GPL + ukuran |

## 8. Aset UnionPDF sendiri

- Ikon & logo: **dibuat sendiri** (SVG buatan), bukan turunan aset Nitro.
- Nama "UnionPDF" & identitas visual: independen.
- Dokumentasi berbahasa Indonesia; identifier kode berbahasa Inggris.
