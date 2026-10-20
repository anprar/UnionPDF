# MODERNIZATION_PLAN.md — Apa yang UnionPDF Buat Lebih Baik

**Status:** DRAFT v1
Tidak menyalin aplikasi referensi. Memperbaiki kelemahannya.

---

## 1. Prinsip modernisasi

| Prinsip | Wujud konkret |
|---|---|
| Stabil > terbaru | Versi di-pin; hindari beta/nightly (`docs/UPGRADE_POLICY.md`) |
| UI responsif | Operasi berat di luar thread UI + progress + cancel (spike S9) |
| Privacy by default | Tanpa telemetry, tanpa unggah dokumen, tanpa AI wajib |
| Engine dapat diganti | Interface `DocumentEngine` + adapter OCR |
| Distribution reproducible | Skrip build & test yang sama untuk semua orang |
| Kebenaran di atas marching | Redaksi diverifikasi lewat ekstraksi ulang |
| Jujur soal batas | Tombol mati dihindari; status fitur eksplisit |

## 2. Modernisasi spesifik

### 2.1 Ukuran & kecepatan
Aplikasi referensi memuat UI berbasis CEF: `libcef.dll` 212 MB +
`mozjs-102.dll` 27 MB. UnionPDF memakai shell Qt tanpa browser engine →
payload jauh lebih kecil dan start lebih cepat.

**Ukuran akhir: `NOT_MEASURED`** (B-03) — harus diukur, bukan diklaim.

### 2.2 Telemetri
Aplikasi referensi menyertakan BugSplat (`BugSplat64.dll`, `BugSplatHD64.exe`,
`BugSplatRc64.dll`) + `mip_ClientTelemetry.dll` → crash reporting aktif default.
UnionPDF: **tidak ada telemetry sama sekali**. Laporan bug dilakukan manual
oleh pengguna.

### 2.3 Redaksi yang dapat dibuktikan
Sebagian besar editor menampilkan kotak hitam. UnionPDF menetapkan
**acceptance criterion**: setelah redaksi, teks target **tidak dapat
diekstrak ulang** (spike S5: `secret_still_extractable: false`). Konten
metadata/thumbnail diuji terpisah (L-07).

UI juga membedakan secara eksplisit:
- **Redaksi aman** — isi dihapus, dapat dibuktikan.
- **Tanda hitam visual** — hanya menutupi, isi masih di dalam berkas.

### 2.4 Optimasi yang tidak merusak
Default **noninvasif**: hapus hanya objek yang benar-benar tidak terpakai.
Aksi destruktif (hapus bookmark, hapus attachment) harus dicentang eksplisit.
Pratinjau delta ("Show Details") sebelum menerapkan.

### 2.5 OCR tanpa drama dependensi
OCR lokal memakai API Windows bawaan → **tanpa unduhan model, tanpa biner
tambahan, offline**. Jalur Tesseract tersedia sebagai opsi lanjut.
UI menyatakan dengan jelas: hasil OCR adalah **lapisan teks tak terlihat**,
bukan teks yang bisa diedit.

### 2.6 Kepribadian vendor
Tidak ada integrasi yang mengunci pengguna ke vendor tertentu: tanpa Office
add-in, tanpa DMS vendor, tanpa layanan tanda tangan cloud, tanpa labeling
MIP. Semuanya **dapat ditambahkan** lewat batas modul, tetapi **tidak
mewati** arsitektur.

### 2.7 Otomatisasi
- Batch queue yang bisa di-resume.
- Preset workflow.
- Command palette.
- CLI (dimulai M11).

### 2.8 Aksesibilitas
Target: navigasi keyboard penuh, label aksesibilitas, kontras, DPI 100–200 %.
(Qt ada di belakang WPF pada aksesibilitas — dicatat jujur di
`STACK_EVALUATION.md` K11.)

### 2.9 AI — opsional dan jujur
| Aturan | Wujud |
|---|---|
| Tidak jadi syarat fungsi inti | Semua fitur inti jalan tanpa AI |
| Opt-in | Sakelar eksplisit per fitur |
| Jelaskan data yang dikirim | Dialog persetujuan menyebut data & tujuan |
| Jangan unggah otomatis | Tidak ada unggah tanpa aksi pengguna |
| Jangan simpan credential di log | — |
| Ada cara manual yang setara | Ringkasan/ekstraksi bisa dilakukan manual |

### 2.10 Transparansi format
Tiap fitur yang punya pasangan mirip diberi label berbeda agar tidak menyesatkan:

| Fitur | Label yang dipakai |
|---|---|
| Tambah teks | "Teks overlay (di atas isi asli)" |
| Edit teks | "Edit teks asli" — **belum tersedia** |
| OCR | "PDF searchable (teks tidak bisa diedit)" |
| Redaksi | "Redaksi (isi dihapus)" vs "Tanda hitam" |
| Tanda tangan | "Gambar tanda tangan" vs "Tanda tangan digital" |
| Kompresi | "Lossless" vs "Lossy" |

## 3. Yang **tidak** dimodernisasi (sengaja)

| Area | Alasan |
|---|---|
| Tidak ada langganan | Prinsip produk |
| Tidak ada watermark | Prinsip produk |
| Tidak ada AI bawaan di tombol utama | Privasi & offline |
| Tidak ada sinkronisasi cloud otomatis | Privasi |
| Tidak ada editor PDF berbasis browser | CEF terlalu berat; shell native lebih ringan |
