# ASSUMPTIONS.md — Asumsi yang Belum Diverifikasi

**Status:** aktif
Setiap asumsi harus: bisa dibuktikan salah, punya cara pembuktian, dan punya
dampak bila salah.

| ID | Asumsi | Dampak bila salah | Cara pembuktian | Status |
|---|---|---|---|---|
| A-01 | Kebanyakan pengguna UnionPDF berada di Windows 10/11 x64 | Runtime & packaging salah | Statistik unduhan (nanti) | UNVERIFIED |
| A-02 | `Windows.Media.Ocr` tersedia di Windows 10 1809+ | Jalur OCR utama hilang | Cek build minimum saat packaging | UNVERIFIED |
| A-03 | Bahasa OCR yang dibutuhkan pengguna =~ Indonesia + Inggris | Kurang relevan bila hanya Latin | Survei / log OCR lokal (tanpa isi dokumen) | UNVERIFIED |
| A-04 | Dokumen kerja pengguna umumnya < 500 halaman | Target performa salah | Benchmark sintetik 1k–10k halaman | UNVERIFIED |
| A-05 | MuPDF cukup untuk redaksi aman di semua channel (metadata, thumbnail, XMP) | **Klaim keamanan M7 overstated** | Uji channel pada spikedocs ber-metadata (L-07) | UNVERIFIED |
| A-06 | Model bisnis open-source + binary gratis sesuai harapan | Distribusi berubah | Keputusan pengguna (B-01) | UNVERIFIED |
| A-07 | Interaksi mouse/keyboard standar Windows cukup (tanpa sentuh) | UX untuk tablet kurang | Uji manual | UNVERIFIED |
| A-08 | Kita boleh mendistribusikan ulang komponen LGPL/AGPL dengan kewajiban source offer | Blokir distribusi | Audit `LICENSE_REVIEW.md` §5 | UNVERIFIED |
| A-09 | Parser PDF MuPDF menangani dokumen "kussex" (PDF 1.7, XFA, malformed) cukup baik | Error saat membuka file user | Corpus uji legal (nanti) | UNVERIFIED |
| A-10 | Bitset 64-bit hanya (tidak perlu 32-bit) | distributing lebih sederhana | Konfirmasi pengguna | UNVERIFIED |

**Aturan:** jangan menulis asumsi sebagai fakta. Jika sebuah asumsi Used to
justify a decision, decision tersebut harus ditandai sebagai "berdasarkan
asumsi" di ADR terkait.
