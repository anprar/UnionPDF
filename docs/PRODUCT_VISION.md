# PRODUCT_VISION.md — Visi Produk

**Status:** DRAFT v1

---

## 1. Untuk siapa

| Persona | Kebutuhan utama | Feature yang harus ada duluan |
|---|---|---|
| **Admin dokumen** | Menimbabwe, menggabung, merapikan arsip | Viewer, operasi halaman, Save As aman |
| **Staff operasional** | Mengisi formulir, menandatangani, menganotasi | Form, anotasi, tanda tangan gambar, OCR |
| **Pengajar /:notaris** | Menandai, menyorot, menambah catatan | Anotasi, cetak, ekspor gambar |
| **Developer** | Otomatisasi pemrosesan PDF | CLI, batch, API lokal |
| **Organisasi** | Kepatuhan & audit | Metadata sanitasi, redaksi aman, log operasi |

## 2. Prinsip produk

1. **Gratis tanpa paywall.** Tidak ada fitur yang disembunyikan di balik
   langganan. Biaya boleh ada (mis. distribusi bertanda tangan), tetapi
   **fitur intinya** gratis selamanya.
2. **Tanpa watermark.** Hasil ekspor bersih.
3. **Offline-first.** Fungsi inti tidak butuh internet. Jika ada fitur yang
   butuh internet (mis. AI awan), itu **opsional, opt-in, dan dijelaskan**.
4. **Privasi dokumen.** Dokumen tidak keluar dari mesin tanpa persetujuan.
5. **Kejujuran UI.** Tidak ada tombol mati. Fitur yang belum ada disembunyikan
   atau diberi label status.
6. **Kejujuran klaim.** Tidak ada klaim "seperti Nitro" atau "100% aman"
   tanpa bukti. Redaksi diverifikasi lewat ekstraksi ulang, bukan tampilan.
7. **Arsitektur yang bisa diganti.** Engine PDF di balik interface; bagian
   yang sering berubah (render, OCR, ekspor) tidak boleh meresap seluruh
   aplikasi.

## 3. Batas yang disepakati

| Tidak akan.done | Alasan |
|---|---|
| Paywall / langganan | Melawan tujuan produk |
| Watermark ekspor | Melawan tujuan produk |
| Telemetri default | Melawan privasi |
| AI sebagai syarat fungsi inti | Melawan prinsip offline & gratis |
| Kode proprietary aplikasi referensi | Melawan aturan legal & etika |
| Klaim tak terverifikasi | Melawan kejujuran |

## 4. Nilai UnionPDF dibanding aplikasi referensi

Bukan "meniru", tapi **memperbaiki hal yang kurang**:

| Area | Aplikasi referensi | UnionPDF |
|---|---|---|
| Ukuran & startup | UI berbasis CEF, 212 MB `libcef.dll` | Shell Qt ringan; MuPDF 50 MB |
| Telemetri | Crash reporting **aktif default** | Tidak ada telemetry, tidak pernah |
| Integrasi vendor | Office add-in, iManage, Nitro Sign, WebDAV | Fokus: tool PDF lokal yang\|_independen |
| Edit teks | Klaim reflow tingkat paragraf | Disediakan sebagai **overlay + redaksi-reinsert** yang berlabel jujur, sampai reflow terbukti |
| OCR | Engine proprietary | API Windows bawaan, offline, tanpa model unduhan |
| Redaksi | Ada | Diverifikasi secara **terukur** (ekstraksi ulang = kosong) |
| Optimasi | "Show Details" | Pratinjau delta + default noninvasif |
| AI | Tab Smart Tools (v26) | **Opsional, opt-in**, dengan penjelasan data yang dikirim |

## 5. Identitas visual

- Nama: **UnionPDF**.
- Palet: netral gelap + satu aksen biru (`#4c8dff`), kontras tinggi.
- Sudut membulat 6–14 px, tanpa dekorasi berlebihan.
- Tipografi: Segoe UI / Inter.
- Ikon: **dibuat sendiri** (SVG), bukan aset pihak ketiga.
- Lihat `src/unionpdf/ui/theme.py`.

## 6. Prinsip "modern" yang dipegang

Modern ≠ terbaru. Modern berarti:
- teknologi stabil dan masih didukung;
- UI responsif;
- proses panjang tidak membekukan UI, dengan progress + cancel;
- komponen mudah diuji;
- dependency dapat diperbarui secara terkendali;
- engine PDF dapat diganti lewat batas modul;
- privasi & keamanan sejak awal;
- pengalaman sederhana;
- workflow dapat diotomatisasi;
- konsumsi sumber daya terukur;
- distribusi Windows dapat direproduksi.

Lihat `docs/POST_REA_TECH_REVIEW.md` dan `docs/UPGRADE_POLICY.md`.
