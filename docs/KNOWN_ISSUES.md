# KNOWN_ISSUES.md — Bugs & Keterbatasan yang Diketahui

**Status:** aktif
Setiap entri harus bisa direproduksi.

| ID | Severity | Deskripsi | Reproduksi | Status | RenSAS | Task |
|---|---|---|---|---|---|---|
| KI-01 | Tinggi | Rotasi pada dokumen yang halamannya sudah punya rotasi non-90 bisa menghasilkan hasil tak terduga | `PageOperation(ROTATE, delta=90)` pada halaman ber-rotasi 270 | Terbuka | — | UPDF-204 |
| KI-02 | Sedang | Render halaman dilakukan sinkron di thread UI → dokumen sangat besar bisa menyentuh UI sebentar | Buka PDF 1.000+ halaman | Terbuka | Render asynchron | UPDF-109 |
| KI-03 | Sedang | `RenderCache` memakai bucketing zoom (1/20) → zoom halus di antara bucket memakai pixmap tertua | Set zoom 1,03 lalu 1,04 | Terbuka | Cache per-zoom eksak atau re-render | UPDF-109 |
| KI-04 | Sedang | Kolom thumbnail tidak menampilkan nomor halaman dengan benar saat item terpilih (ikon menutupi teks) | Buka dokumen, pilih thumbnail | Terbuka | Ganti layout item | UPDF-104 |
| KI-05 | Sedang | Jalur `Save As` UI belum memakai `atomic_write` → file sementara tidak dibersihkan bila gagal | Simpan ke direktori tanpa izin tulis | Terbuka | Pakai `atomic_write` | UPDF-012 |
| KI-06 | Rendah | `WARN`/log aplikasi belum ada; error hanya tampil di dialog | — | Terbuka | Tambah logger tanpa isi dokumen | UPDF-013 |
| KI-07 | Rendah | Tidak ada undo/redo | — | Terbuka | `EditSession.push_undo` sudah disiapkan | UPDF-204 |
| KI-08 | Rendah | Teks di dalam `RichText` annotation tidak diedit | — | Terbuka | DEFER | — |
| KI-09 | Rendah | Tampilan thumbnail halaman berganti ukuran tidak di-refresh otomatis | Resize window | Terbuka | QEvent.Resize handler | UPDF-104 |

---

## Keterbatasan yang diketahui dan diterima (bukan bug)

| ID | Keterbatasan | Alasan | Dampak |
|---|---|---|---|
| KL-01 | Edit teks existing dengan reflow tidak tersedia | Content-stream surgery belum dibuktikan (B-04) | Fitur M8 di-DEFER; UnionPDF menyediakan overlay + redaksi-reinsert yang **berlabel jujur** |
| KL-02 | Bahasa OCR tidak bisa dideteksi otomatis | Binding WinRT 3.2.1 tidak mengekspos API (B-05) | User memilih bahasa; daftar statis sebagai bantuan |
| KL-03 | Tidak ada PDF/A | Butuh validator; risiko kepatuhan tinggi | Ditunda ke M12 |
| KL-04 | Tidak ada tanda tangan kriptografis | pyHanko belum dievaluasi | Ditunda ke M10 |
| KL-05 | XFA form tidak didukung | Kompleksitas sangat tinggi | Ditolak |
| KL-06 | Tidak ada editor PDF berbasis browser (CEF) | Terlalu berat; shell native lebih ringan | — |
