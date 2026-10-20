# REA_LIMITATIONS.md — Batas Analisis Aplikasi Referensi

**Status:** aktif
**Sesi:** `2026-10-20T1624+0700`
**Referensi:** Nitro PDF Pro 14.41.0.15

Dokumen ini mencatat **apa yang tidak boleh disimpulkan** dari analisis yang sudah
dilakukan. Ini adalah counterpart wajib dari `REA_FINDINGS.md`.

---

## L-01 — Inspeksi biner: DILAKUKAN (read-only, dengan izin)

**Status:** **SELESAI** — izin eksplisit diberikan pengguna pada 2026-10-20.
**Dasar:** master prompt §5 mengizinkan *"Inspeksi teknis terarah hanya jika
diperlukan dan diizinkan"*, dan pengguna telah mengizinkan inspeksi read-only
yang mendalam.

**Yang dilakukan:** `REA open_binary`/`binary_overview` (Ghidra) pada modul
native, `REA inspect_pe_resources` pada `NitroPDF.exe`, `REA search_strings`,
serta parser PE read-only milik sendiri untuk mengekstraksi 14.452 string UI
dari 35 berkas `.mui` dan 10.284 identifier fitur dari 30 modul.

**Yang tetap DILARANG (tidak berubah):** patch executable, bypass aktivasi/
trial/paywall/lisensi, pengambilan product key/token/credential/data pengguna,
perubahan registry/service/konfigurasi Nitro, penyalinan kode proprietary/DLL/
engine/logo/aset, unggah binary ke layanan eksternal, dan menjadikan Nitro
dependency runtime.

**Batas yang tersisa:**
- Ghidra gagal mengimpor `NitroPDF.exe` (16 MB, CEF) dalam batas startup
  330 detik → analisis native pada executable utama **belum tuntas** (`U-08`).
  Modul kecil (`np_pdfa.dll`) berhasil dianalisis penuh: 1.852 prosedur.
- Tidak ada **pseudocode** yang dihasilkan; tidak ada klaim "source asli".
  Bukti MuPDF/UI berasal dari **string dan struktur resource** — data teramati,
  bukan rekonstruksi logika.
- Perilaku runtime Nitro tetap **tidak** diamati (aplikasi tidak dieksekusi).

---

## L-02 — Observasi UI: DIGANTI dengan bukti yang setara atau lebih kuat

**Status:** **TERGANTUNG** — tidak ada pengamatan visual langsung, tetapi
struktur UI v14 **terekstraksi** dari binary.

**Yang diketahui sekarang:** 14 tab ribbon, 783 kontrol, 90 toolbar
kontekstual, 14.452 string UI (label, opsi dialog, pesan error) dari build
v14.41.0.15 yang terpasang. Lihat `docs/research/V14_RIBBON_STRUCTURE.md` dan
`docs/research/V14_UI_EVIDENCE.md`.

**Apa yang TETAP tidak diketahui:**
- Tata letak visual, posisi, ikon, dan perilaku interaktif.
- Urutan langkah pengguna dalam dialog.
- Pintasan keyboard.
- Perilaku dinamis (drag & drop, undo, state antar-dialog).

**Cara menutup:** pengujian manual oleh pengguna (rekaman layar / daftar
pintasan) — lihat `U-07`.

---

## L-03 — Pengujian I/O pada aplikasi referensi tidak dilakukan

**Status:** tidak dijalankan.
**Alasan:** Nitro tidak boleh dieksekusi oleh UnionPDF, dan menjalankan
aplikasi komersial pihak ketiga di luar lingkup "pengamatan UI yang dapat diakses
secara sah" yang diizinkan master prompt.

**Konsekuensi:** tidak ada angka performa, tidak ada pengukuran ketepatan
output, tidak ada daftar error yang terverifikasi dari Nitro.

**Pengganti:** seluruh pengujian I/O diarahkan ke **fixture sintetis** yang
dibuat sendiri di `spikes/fixtures/` dan `tests/fixtures/`. Lihat `E-010`.

---

## L-04 — Fitur yang mungkin terkunci tidak diverifikasi

**Status:** `DOCUMENTED_NOT_TESTED`.
Master prompt melarang mencoba membuka fitur terkunci. Karena itu status
lisensi/trial tiap fitur pada 14.41.0.15 **tidak diketahui** dan tidak boleh
diasumsikan.

Konsekuensi: matriks fitur membedakan `VERIFIED` (terbukti di mesin) dari
`DOCUMENTED` (ada di dokumentasi publik v14) dan `HYPOTHESIS`.

---

## L-05 — Dokumentasi publik yang dipakai bukan khusus build 14.41.0.15

**Status:** ketegangan versi yang acknowledged.
Dokumentasi `gonitro.com/user-guide` adalah dokumentasi *living* — beberapa
artikel diperbarui pada 2026 dan mencerminkan v26. Diposisi v14.41.0.15 berada
di tengah: setelah v14.42 (upgrade PDF/A) dan sebelum v14.43.

**Yang dilakukan:** setiap klaim yang bersumber dari dokumentasi publik diberi
tingkat kepastian. Klaim yang jelas merupakan fitur v26 (tab Smart Tools, AI,
redesign toolbar) **tidak** dipakai sebagai fakta tentang v14.

**Cara menutup:** arsip release notes v14.41–v14.43 + pengujian langsung pada
build yang diinstal.

---

## L-06 — Angka performa di dokumen ini hanya dari UnionPDF, bukan Nitro

Semua angka di `TECH_SPIKES.md` dan `STACK_EVALUATION.md` adalah pengukuran
**UnionPDF dengan MuPDF** pada mesin ini (12 core, Windows 11 build 26300).
Tidak ada satu pun benchmark Nitro. Perbandingan performa Nitro-vs-UnionPDF
**tidak diklaim**.

---

## L-07 — Perilaku `apply_redactions` pada dokumen kompleks belum diuji

Spike `spike_02_annotate.py` membuktikan pada dokumen sintetik sederhana bahwa
setelah `apply_redactions`, teks target **tidak** dapat diekstrak ulang. Itu
cukup untuk M7, tetapi **belum** membuktikanIGH sanitization menyeluruh
(embedded JavaScript, thumbnail lama, object stream, XMP metadata, layer).

**Syarat M7 (wajib):** uji pada dokumen dengan XMP metadata, thumbnail, dan
embedded object; verifikasi tidak ada kebocoran di setiap channel tersebut.

---

## L-08 — Batas versi API MuPDF yang dipakai

Spike menemukan perubahan API yang sudah terjadi pada PyMuPDF 1.27:

| API lama | API yang berlaku |
|---|---|
| `Page.insert_widget(widget)` | `Page.add_widget(widget)` |
| `Widget.field_fontsize` | `Widget.text_fontsize` (atau absen) |

**Konsekuensi:** kode produksi **wajib** ditulis dan diuji terhadap versi
tertinct yang dikunci, bukan berdasarkan contoh dokumentasi lama. Lihat
`docs/DEPENDENCIES.md` dan `docs/UPGRADE_POLICY.md`.

---

## Ringkasan tingkat kepastian

| Aspek | Tingkat |
|---|---|
| Versi & inventaris modul Nitro | `VERIFIED` (metadata berkas + inventaris) |
| Daftar kapabilitas engine | `VERIFIED` (nama modul) |
| Opsi dialog OCR, Optimize, Edit Text | `DOCUMENTED` (dokumentasi publik v14) |
| Perilaku internal / alur UI Nitro | `UNKNOWN` |
| Performa Nitro | `UNKNOWN` (tidak diukur) |
| Fitur terkunci lisensi | `UNKNOWN` |
| Kemampuan engine UnionPDF (MuPDF) | `VERIFIED` via spike |
