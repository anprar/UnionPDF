# REQUIREMENTS.md — Kebutuhan UnionPDF

**Status:** DRAFT v1
Kebutuhan diturunkan dari `docs/FEATURE_MATRIX.md` (97 fitur) dan
`docs/REA_FINDINGS.md`.

Format: `UPDF-R-nnn` · Tipe: `F` (fungsional) / `N` (non-fungsional) ·
Prioritas: `MUST` / `SHOULD` / `COULD`.

---

## 1. Kebutuhan fungsional

### Viewer
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F01 | Membuka berkas PDF (termasuk yang rusak/terenkripsi, dengan pesan jelas) | MUST | M1 | DONE |
| UPDF-R-F02 | Merender halaman dengan zoom, fit width, fit page | MUST | M1 | DONE |
| UPDF-R-F03 | Menavigasi halaman (tombol, keyboard, thumbnail) | MUST | M1 | DONE |
| UPDF-R-F04 | Menampilkan thumbnail halaman | MUST | M1 | DONE |
| UPDF-R-F05 | Mencari teks dan melompat ke hasil | MUST | M1 | DONE |
| UPDF-R-F06 | Menampilkan informasi dokumen (judul, penulis, producer, terenkripsi?) | SHOULD | M1 | TODO |
| UPDF-R-F07 | Menyeleksi dan menyalin teks | SHOULD | M1 | TODO |
| UPDF-R-F08 | Membuka dokumen terakhir & terakhir dibuka | COULD | M11 | TODO |

### Operasi halaman
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F10 | Menggabungkan beberapa PDF | MUST | M2 | Engine DONE, UI TODO |
| UPDF-R-F11 | Memecah / mengekstrak halaman | MUST | M2 | idem |
| UPDF-R-F12 | Menghapus halaman | MUST | M2 | idem |
| UPDF-R-F13 | Memutar halaman | MUST | M2 | idem |
| UPDF-R-F14 | Menyalin halaman (duplicate) | MUST | M2 | idem |
| UPDF-R-F15 | Menyusun ulang halaman | MUST | M2 | idem |
| UPDF-R-F16 | Menyisipkan halaman | SHOULD | M3 | TODO |
| UPDF-R-F17 | Menyimpan sebagai dengan verifikasi output | MUST | M2 | Engine DONE, UI TODO |
| UPDF-R-F18 | Undo / redo | SHOULD | M2 | TODO |

### Create & augment
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F20 | Menambah teks overlay | MUST | M3 | TODO |
| UPDF-R-F21 | Menambah gambar | MUST | M3 | TODO |
| UPDF-R-F22 | Menambah watermark | SHOULD | M3 | TODO |
| UPDF-R-F23 | Header/footer & nomor halaman | SHOULD | M3 | TODO |
| UPDF-R-F24 | Halaman kosong & rentang halaman | SHOULD | M3 | TODO |
| UPDF-R-F25 | Konversi gambar → PDF | SHOULD | M3 | TODO |

### Anotasi & form
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F30 | Highlight, underline, strikeout | MUST | M4 | TODO |
| UPDF-R-F31 | Note/komentar | MUST | M4 | TODO |
| UPDF-R-F32 | Bentuk dasar | SHOULD | M4 | TODO |
| UPDF-R-F33 | Mengisi form AcroForm & menyimpan | MUST | M4 | TODO |
| UPDF-R-F34 | Flatten anotasi/form | COULD | M4 | TODO |

### OCR
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F40 | OCR lokal → PDF searchable | MUST | M5 | TODO (engine terverifikasi) |
| UPDF-R-F41 | Prompt OCR otomatis untuk dokumen tanpa text layer | SHOULD | M5 | TODO |
| UPDF-R-F42 | Pemilihan bahasa OCR | MUST | M5 | TODO (B-05) |
| UPDF-R-F43 | Rentang halaman & progress/cancel OCR | MUST | M5 | TODO |

### Optimasi, keamanan, konversi
| ID | Kebutuhan | Prioritas | Milestone | Status |
|---|---|---|---|---|
| UPDF-R-F50 | Preset kompresi + opsi custom | MUST | M6 | TODO |
| UPDF-R-F51 | Pratinjau perubahan sebelum optimasi | MUST | M6 | TODO |
| UPDF-R-F52 | Antrean batch dengan progress, cancel, retry | MUST | M6 | TODO |
| UPDF-R-F53 | Enkripsi password (AES-256) | MUST | M7 | Engine DONE, UI TODO |
| UPDF-R-F54 | Permission settings | SHOULD | M7 | TODO |
| UPDF-R-F55 | Redaksi yang **terbukti** menghapus isi | MUST | M7 | Engine DONE (S5), UI TODO |
| UPDF-R-F56 | Sanitasi metadata | SHOULD | M7 | TODO |
| UPDF-R-F57 | PDF → gambar & PDF → teks | SHOULD | M9 | TODO |
| UPDF-R-F58 | Tanda tangan gambar | SHOULD | M10 | TODO |
| UPDF-R-F59 | Tanda tangan kriptografis | COULD | M10 | DEFER (U-06) |

## 2. Kebutuhan non-fungsional

| ID | Kebutuhan | Target | Cara ukur | Status |
|---|---|---|---|---|
| UPDF-R-N01 | Render halaman | ≤ 100 ms/halaman @144 DPI | Spike + benchmark | TERPENCAPAI (33,87 ms) |
| UPDF-R-N02 | Buka dokumen 500 halaman | ≤ 250 ms | Spike | TERPENCAPAI (11,69 ms) |
| UPDF-R-N03 | UI tidak membeku saat operasi panjang | Event loop tetap responsif | Spike S9 | TERPENCAPAI (661 tick/detik) |
| UPDF-R-N04 | Setiap operasi lama punya progress + cancel | 100% | Uji manual | TODO |
| UPDF-R-N05 | Penulisan atomik | 100% operasi tulis | `tests/test_infrastructure.py` | DONE |
| UPDF-R-N06 | Output diverifikasi | 100% operasi tulis | `tests/test_engine.py` | DONE |
| UPDF-R-N07 | Input tidak pernah ditimpa tanpa konfirmasi | 100% | Uji manual | TODO |
| UPDF-R-N08 | Tidak ada telemetry | 0 panggilan jaringan | Audit deps + review | TERPENCAPAI (by design) |
| UPDF-R-N09 | Didukung DPI 100–200 % | Sesuai | Uji manual | TODO |
| UPDF-R-N10 | Ukuran distribusi | **NOT_MEASURED** — butuh angka dari pengguna (B-03) | Build one-dir | TODO |
| UPDF-R-N11 | Dependency di-pin & dapat diuji | 100% | `requirements*.txt` | DONE |
| UPDF-R-N12 | Engine dapat diganti | 1 interface | `engine/protocol.py` | DONE |
| UPDF-R-N13 | Dokumen besar (>5.000 hlm) | **UNKNOWN** | Benchmark | TODO (U-04) |
| UPDF-R-N14 | Waktu start aplikasi | **NOT_MEASURED** | Timing | TODO |
| UPDF-R-N15 | Using RAM saat viewer terbuka | **NOT_MEASURED** | Profiling | TODO |

## 3. Kebutuhan non-goal (tegas)

| ID | Bukan kebutuhan |
|---|---|
| UPDF-R-X01 | Dukungan XFA form |
| UPDF-R-X02 | Integrasi DMS vendor (iManage, SharePoint) |
| UPDF-R-X03 | Tanda tangan berbasis cloud |
| UPDF-R-X04 | Ekstensi Microsoft Office |
| UPDF-R-X05 | Sensitivity labeling (MIP) |
| UPDF-R-X06 | Editor PDF berbasis CEF/Chromium |
