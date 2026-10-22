# Hasil spike terbatas — RS-00, RS-01, bagian PDFium RS-02/RS-03/RS-05

| Field | Nilai |
|---|---|
| Persetujuan | A-6, A-7 (2026-10-21) |
| Sesi | `2026-10-21T1114+0700` |
| Engine | PDFium `chromium/7881` (biner `bblanchon/pdfium-binaries`) via `pdfium-render 0.9.4` |
| Pembaca independen | PyMuPDF 1.27.2.2 + Pillow 12.3.0 (`.venv`, sudah terpasang) |
| Status stack | **BELUM DISETUJUI** — hasil ini **tidak** mengesahkan PDFium sebagai engine lengkap |

Bukti terlacak: `results/evidence/*.json`, `deps/PROVENANCE.md`, `fixtures/FIXTURES.md`.
Bukti mentah (PDF/PNG output, tidak dilacak): `raw/`.

## 1. Dependency & provenance aktual

| Komponen | Versi | Lisensi | Sumber / verifikasi |
|---|---|---|---|
| PDFium (biner) | 151.0.7881.0 (`chromium/7881`), `pdfium-win-x64.tgz` 3.733.154 B, `pdfium.dll` 7.211.520 B | BSD-3 + pustaka pihak ketiga permisif (`licenses/` di paket) | GitHub release `bblanchon/pdfium-binaries`; digest cocok; `gh attestation verify` lulus (SLSA provenance v1, workflow `build-all.yml`, commit `867b3ecc`, run `27143496415`). DLL **tidak** bertanda tangan Authenticode. Rincian: `deps/PROVENANCE.md` |
| `pdfium-render` | 0.9.4 (dipin `=0.9.4`) | MIT OR Apache-2.0 | crates.io, checksum `8948a803…` |
| `image` | 0.25.10 (fitur `png`) | MIT OR Apache-2.0 | crates.io via `Cargo.lock` |
| `serde_json` | 1.0.154 | MIT OR Apache-2.0 | crates.io |
| Transitif (39 paket, target `x86_64-pc-windows-msvc`) | lihat `evidence/Cargo.lock.snapshot` | MIT/Apache (dominan), Unlicense OR MIT, BSD-3 OR Apache, Zlib, ISC (`libloading`), 0BSD | `cargo metadata --filter-platform x86_64-pc-windows-msvc` |

Semua instalasi lokal-proyek: `CARGO_HOME=experiments/restart/.cargo-home`; toolchain Rust
1.98.0 apa adanya; tidak ada instalasi global/admin.

## 2. Command & environment

| Item | Nilai |
|---|---|
| OS | Windows 11 Pro 10.0.26300 (build 26300) |
| CPU / RAM | Intel Core i5-10400 @ 2.90 GHz, 6 core / 12 thread; 15,9 GB |
| Rust | rustc 1.98.0, cargo 1.98.0 |
| Python | 3.13.9 (`.venv`), PyMuPDF 1.27.2.2, Pillow 12.3.0 |
| Java (untuk rencana PDFBox) | Zulu 8 JDK 1.8.0_345 (`javac` tersedia) — **tidak dipakai** pada spike ini |

```powershell
cd D:\dokumentasi\Project\UnionPDF\experiments\restart
..\..\.venv\Scripts\python.exe fixtures\generate_fixtures.py             # exit 0
$env:CARGO_HOME = "$PWD\.cargo-home"
cargo build --release --manifest-path pdfium-spike\Cargo.toml          # exit 0
.\pdfium-spike\target\release\pdfium-spike.exe all                      # exit 0, wall 766 ms
..\..\.venv\Scripts\python.exe verify\verify_independent.py             # exit 0
```

## 3. PASS / FAIL / NOT_RUN

Kriteria ditetapkan di `README.md` sebelum verifikasi independen dijalankan.

| Test ID | Spike | Uji | Hasil | Bukti |
|---|---|---|---|---|
| RS00-T1 | RS-00 | Versi crate & biner ditetapkan sebelum unduh | **PASS** | `deps/PROVENANCE.md` §1 |
| RS00-T2 | RS-00 | Digest unduhan = digest yang dipublikasikan | **PASS** | SHA-256 `73cc0de6…` |
| RS00-T3 | RS-00 | Verifikasi atestasi kriptografis | **PASS** | `gh attestation verify` exit 0, 1 hasil, 1 timestamp tlog |
| RS00-T4 | RS-00 | Patch yang diterapkan tidak mengubah logika PDF | **PASS** | 4 patch build/ekspor saja; identik di tag & commit build |
| RS00-T5 | RS-00 | Lisensi & notices tersedia, tanpa copyleft/komersial | **PASS** (penilaian non-hukum) | `licenses/` 15 file |
| RS01-T1 | RS-01 | Semua halaman 5 fixture dirender (skala 1,0) | **PASS** — 508/508 halaman, 0 error | `evidence/rs01_result_pdfium.json` |
| RS01-T2 | RS-01 | Render cocok dengan PyMuPDF (MAD ≤ 10) | **PASS** — 11/11 halaman, MAD 0,051–0,306 | `evidence/verify_independent.json` |
| RS01-T3 | RS-01 | Zoom 0,5/1/2/4× dan thumbnail lebar 160 px | **PASS** | dimensi bitmap sesuai skala |
| RS01-T4 | RS-01 | Ekstraksi teks fixture Latin = ground truth | **FAIL — penyebab fixture**: 1 baris (`Œ`) tidak cocok; glyph di file memang `·` (render & PyMuPDF sama). Baris lain (ASCII, é ï ç Å ö ß) cocok | FIXTURES.md |
| RS01-T5 | RS-01 | Unicode/Arab | **NOT_RUN (fixture tidak valid)** — tanpa shaping/bidi; spasi → U+00A0 di kedua engine | FIXTURES.md |
| RS01-T6 | RS-01 | Pencarian token di halaman yang benar | **PASS** | ditemukan di halaman indeks 1 |
| RS01-T7 | RS-01 | Pembatalan request render usang (antar-request, lintas thread) | **PASS** — 60 antre, sinyal setelah 5 selesai → 6 dirender, 54 dibuang, latensi 1,05 ms | evidence rs01 `cancel` |
| RS01-T8 | RS-01 | Pembatalan di tengah render satu halaman (progressive) | **NOT_RUN** | — |
| RS02-T1 | RS-02 | Membuat 10 subtipe (8 lewat wrapper, circle & ink lewat FFI mentah) tanpa error | **PASS** | evidence rs02 |
| RS02-T2 | RS-02 | Save As → dibuka ulang PDFium: subtipe, contents, warna, attachment points sama | **PASS** — 10/10 | evidence rs02 `reopened_by_pdfium` |
| RS02-T3 | RS-02 | Anotasi ada di file menurut pembaca independen (parsing `/Annots` mentah) | **PASS** — 10/10, subtipe benar | verify `annotations_raw` |
| RS02-T4 | RS-02 | Dapat dimuat API anotasi pembaca independen | **FAIL** — 0/10: PDFium menulis anotasi sebagai **objek langsung** di `/Annots` | verify `pymupdf_annot_api_load` |
| RS02-T5 | RS-02 | Appearance stream (`/AP`) ditulis | **FAIL** — 0/10 | verify `has_AP` |
| RS02-T6 | RS-02 | Terlihat di render kedua engine (≥ 1 % piksel berubah di area) | **FAIL sebagian** — 5/10 PASS (text, freetext, square, circle, ink); highlight, underline, strikeout, squiggly, stamp **tidak dirender PDFium sendiri** (PyMuPDF menampilkannya karena mensintesis appearance) | verify `visibility` |
| RS03-T1 | RS-03 | Field teks: nilai tersimpan | **PASS** — `/V` benar, dibaca ulang PDFium | evidence rs03, verify `raw_widgets` |
| RS03-T2 | RS-03 | Field teks: appearance diperbarui | **FAIL** — AP lama tidak memuat nilai baru; `NeedAppearances` tidak diset | verify |
| RS03-T3 | RS-03 | Checkbox lewat `set_checked(true)` | **FAIL** — wrapper menulis `/AS` & `/V` sebagai **string** `(/Yes)`; PyMuPDF gagal memuat halaman (`key is not a name`) | verify; source `checkbox.rs` |
| RS03-T4 | RS-03 | Radio lewat `set_checked()` | **FAIL** — tidak berefek (`/AS /Off`), padahal melapor sukses; getter melaporkan kedua radio tercentang. Terkontaminasi cacat fixture (radio bukan grup) | verify; source `radio.rs` |
| RS03-T5 | RS-03 | Combo box | **NOT_RUN** — wrapper tidak menyediakan setter | evidence rs03 |
| RS03-T6 | RS-03 | Jalur form-fill native PDFium (`FORM_*`) | **NOT_RUN** | — |
| RS05-T1 | RS-05 | Jumlah, urutan, rotasi halaman benar; output dibuka tanpa repair/warning (9 operasi) | **PASS** — 9/9 | verify `rs05` |
| RS05-T2 | RS-05 | Struktur in-place (rotate, delete, reorder, insert, merge-append): bookmark, link, anotasi, field tetap valid | **PASS** — 5/5 | verify `in_scope_structure` |
| RS05-T3 | RS-05 | Struktur pada impor ke dokumen baru (merge-new, extract, split) | **Diamati** (di luar scope go/no-go): outline **hilang**; link tersalin tetapi `/A <</S/GoTo>>` **tanpa tujuan**; widget tersalin tanpa `/AcroForm` (bukan field); anotasi teks tersalin | verify + objek mentah |
| — | — | Input fixture tidak berubah (SHA-256) | **PASS** — 9/9 | verify `inputs` |

## 4. Bukti & keterbatasan

- Struktur divalidasi dengan PyMuPDF (`is_repaired`, warning MuPDF) — **bukan** `qpdf --check`
  (QPDF tidak dipasang).
- Satu pembaca independen saja (PyMuPDF). Perilaku pada Acrobat/Chrome/viewer lain **tidak diuji**.
- Pengukuran waktu adalah satu run pada fixture sintetis kecil; bukan benchmark.
- Akses binding mentah memakai dua `bind_to_library` sebelum `Pdfium::new` (trait accessor
  `pub(crate)` di 0.9.4, berbeda dengan catatan README 0.9.2).

## 5. Pengukuran yang benar-benar dilakukan

| Pengukuran | Nilai | Catatan |
|---|---:|---|
| Bind + init PDFium | 5,93 ms | dalam proses spike |
| Muat fixture + render halaman pertama ×1,5 | 7,01 ms | setelah library ter-init; **bukan** waktu startup aplikasi |
| Render 500 halaman ×1,0 (teks sederhana) | 253,98 ms total | ≈ 0,51 ms/halaman, satu run |
| Zoom ×4 halaman 0 | 5,68–16,13 ms | 2380×3368 px |
| Thumbnail lebar 160 px | 0,14–1,61 ms | |
| Latensi pembatalan antar-request | 1,05 ms | |
| Working set setelah init | 9.039.872 B | |
| Peak working set seluruh run | 47.042.560 B | termasuk bitmap ×4 |
| Peak private bytes | 38.584.320 B | |
| Wall time `pdfium-spike all` | 766 ms | |
| Ukuran unduhan PDFium | 3.733.154 B | arsip `.tgz` |
| Ukuran terpasang PDFium | 7.211.520 B | `pdfium.dll` |
| Ukuran exe spike (release) | 1.981.440 B | memuat `pdfium.dll` dinamis |

Kategori A-2 untuk distribusi UnionPDF: ukuran installer/terpasang aplikasi, runtime eksternal
(mis. WebView2), komponen OS, dan waktu startup aplikasi = **NOT_MEASURED** (belum ada shell/paket).
Dependensi DLL sistem `pdfium.dll` **belum diperiksa**.

## 6. Gap authoring yang masih terbuka (PDFium)

| # | Gap | Status |
|---|---|---|
| G-A1 | Anotasi baru tanpa `/AP` dan sebagai objek langsung → interoperabilitas buruk; PDFium sendiri tidak menampilkan markup/stamp tanpa AP | Jalur perbaikan **UNPROVEN**: AP kustom via `FPDFAnnot_SetAP`; tidak ditemukan API PDFium untuk menulis anotasi sebagai objek tidak langsung |
| G-A2 | Circle & InkList hanya lewat FFI mentah (wrapper tidak membungkus) | Bisa, tapi butuh kode `unsafe` + workaround binding |
| G-A3 | Setter form wrapper cacat (checkbox `/AS` string, radio no-op, getter radio salah, tanpa setter choice); AP teks tidak diperbarui | Jalur native `FORM_*` **NOT_RUN** |
| G-A4 | Pembuatan field form baru | **NOT_RUN** (RS-04 belum disetujui); review API: tidak ada API publik |
| G-A5 | Impor halaman ke dokumen baru membuang outline, tujuan link, dan `/AcroForm` | Butuh penanganan kustom atau engine lain untuk merge/extract/split yang mempertahankan struktur |
| G-A6 | Redaksi, enkripsi tulis, signature | Tidak diuji (di luar persetujuan); review API: tidak ada di PDFium |
| G-A7 | Unicode/RTL | Fixture harus diperbaiki sebelum dapat dinilai |

## 7. Rencana pembandingan PDFBox & MuPDF pada fixture yang sama

1. **Perbaiki fixture** (tanpa butuh instalasi): `Œ` dengan font TrueType yang benar; teks Arab
   ber-shaping/bidi (generator HarfBuzz-capable, mis. `insert_htmlbox` PyMuPDF — perlu
   diverifikasi); radio sebagai grup dengan `/Parent`.
2. **Generator & verifier yang sama** dipakai untuk ketiga engine. Pembaca independen disilang:
   output PDFBox/MuPDF diverifikasi dengan PDFium **dan** PyMuPDF/PDFBox sesuai engine yang diuji.
3. **MuPDF (baseline C):** PyMuPDF 1.27.2.2 sudah ada di `.venv` → spike kapabilitas tanpa
   instalasi baru; integrasi worker Tauri belakangan.
4. **PDFBox (baseline B):** unduh JAR PDFBox 3.0.x (+ `fontbox`, `pdfbox-io`, `commons-logging`;
   Bouncy Castle untuk RS-08) dari Maven Central/Apache dengan verifikasi checksum & tanda tangan
   penerbit; dikompilasi dengan Zulu 8 JDK yang sudah ada (memenuhi minimum Java 8).
5. **Spike yang dibandingkan:** RS-02, RS-03 (termasuk choice & radio grup), RS-04 (field
   authoring), RS-05 (termasuk impor yang mempertahankan outline/link/AcroForm), RS-07 (redaksi
   dengan verifikasi penghapusan), RS-08 (signature dengan validasi independen).
6. Opsional untuk melengkapi baseline A: jalur `FORM_*` native dan AP kustom di PDFium.

## 8. Usulan gate berikutnya (histori)

Keputusan G-1…G-7 diberikan pengguna 2026-10-21; lihat §9.

## 9. Pembandingan engine pada fixture v2 (G-3, G-4) — 2026-10-21

Fixture diperbaiki (`fixtures/FIXTURES.md` v2): `Œ` via TrueType, teks Arab ber-shaping
(`insert_htmlbox`), radio sebagai grup `/Parent`+`/Kids` (A, B), fixture redaksi 8 kanal.
Operasi sama di tiga engine; output diverifikasi oleh PDFium (`pdfium-spike describe`),
PyMuPDF, dan objek mentah. Bukti: `evidence/compare_engines.json`, `evidence/mupdf_result.json`,
`evidence/pdfbox_result.json`.

| Engine | Versi | Sumber |
|---|---|---|
| PDFium | `chromium/7881` + `pdfium-render 0.9.4` | lihat §1 |
| MuPDF | PyMuPDF 1.27.2.2 (sudah ada di `.venv`) | — |
| PDFBox | 3.0.8 + Bouncy Castle 1.84, Java 1.8.0_345 (Zulu 8 lokal) | `deps/PROVENANCE.md` §7 |

### 9.1 Hasil

| Test | PDFium (+wrapper) | MuPDF | PDFBox |
|---|---|---|---|
| RS-02 anotasi: punya `/AP`, objek tidak langsung, terlihat di kedua engine | 0/10 (objek langsung, tanpa AP) | **14/14** | **13/14** — stamp tanpa AP (tidak ada appearance handler) |
| RS-02 subtipe CR-08 (line, polygon, polyline, caret) | tidak dapat dibuat | **4/4** | **4/4** |
| RS-03 isi form: nilai teks, AP teks, checkbox `/AS` name, radio B saja, nilai & AP combo, PyMuPDF dapat memuat halaman | 1/7 | **7/7** | **7/7** |
| RS-04 buat field: dikenali PDFium & PyMuPDF; diisi pembaca lain lalu terbaca PDFium | NOT_RUN (tanpa API; G-5 ditunda) | **PASS** | **PASS** (appearance checkbox dibangun manual) |
| RS-05 merge: urutan, tanpa repair, bookmark, link, field, anotasi | **PASS** (append in-place) | **PASS** | **PASS** (`PDFMergerUtility`) |
| RS-05 extract p2–4 ke dokumen baru | bookmark & field hilang | **PASS** (`insert_pdf` + `set_toc` remap) | `PageExtractor`: bookmark & field hilang |
| RS-05 extract in-place (hapus halaman lain) | (lihat RS-05 delete: struktur utuh) | — | struktur utuh, **tetapi** bookmark ke halaman terhapus tetap ada & menunjuk halaman salah → perlu pemangkasan outline |
| RS-07 redaksi: kanal di dalam area (teks, XObject, teks tersembunyi, anotasi, gambar, vektor) | NOT_RUN (tanpa API) | **PASS** — tidak terdeteksi oleh 2 engine & pemindaian mentah; area gambar/vektor 100 % tertutup | NOT_RUN (tanpa API) |
| RS-07 sanitasi di luar area | — | metadata hilang hanya dengan `scrub()`; `reset_fields` mengosongkan nilai tetapi **teks lama tersisa di appearance stream** | — |
| RS-08 signature | tidak ada API | `pdf_sign_signature` + `PdfPkcs7Signer` di binding level rendah (signer harus disediakan pemanggil) — tidak diuji | **Bukti minimal**: ditandatangani dengan sertifikat uji self-signed; CMS valid terhadap sertifikat tertanam (BC); byte-range menutup file; file diubah 1 bit → terdeteksi; PDFium membaca 1 signature, PyMuPDF `sigflags=3`. **Rantai kepercayaan tidak dinilai; verifikasi kriptografis oleh library yang sama** |
| RS-01 teks Latin (fixture v2) | **PASS** | — | — |
| RS-01 teks Arab (fixture v2) | **FAIL — keterbatasan engine**: PDFium mengembalikan urutan visual (string terbalik) | PASS (urutan logis, NFKC) | — |

### 9.2 Klasifikasi kegagalan

| Kategori | Temuan |
|---|---|
| Kegagalan fixture (sudah diperbaiki) | `Œ` base-14; Arab tanpa shaping; radio bukan grup |
| Kegagalan wrapper (`pdfium-render 0.9.4`) | Setter checkbox menulis `/AS` string; radio no-op; widget anak grup radio berklasifikasi `Unknown` (tidak mewarisi `/FT` dari `/Parent`); tanpa setter choice; **`stroke_color()` menyebabkan access violation pada anotasi Text yang sudah punya `/AP`** (wrapper vs PDFium belum dipisahkan) |
| Keterbatasan engine | PDFium: anotasi baru tanpa AP & objek langsung, tidak merender markup/stamp tanpa AP, tidak membuat field, tidak menulis enkripsi, signature hanya baca, ekstraksi teks RTL urutan visual; PDFBox: tanpa API redaksi, tanpa handler AP stamp, tanpa generator AP checkbox; MuPDF: sanitasi field meninggalkan AP lama |
| Kesalahan implementasi eksperimen (diperbaiki) | Verifier awal crash pada anotasi langsung & halaman tak termuat; `describe` memanggil `stroke_color()` |

### 9.3 Kesimpulan (bukan klaim fitur selesai)

- **PDFium** layak sebagai **renderer** (RS-01, RS-05 in-place) — sesuai keputusan pengguna.
- **PDFBox** memenuhi kebutuhan authoring awal yang diuji (anotasi kecuali stamp, isi form,
  buat field, merge, signature minimal) → dipakai sebagai **pilihan authoring awal**
  (otorisasi pengguna 2026-10-21). Gap: redaksi (tanpa API), AP stamp, pemangkasan outline
  saat extract in-place.
- **MuPDF** paling lengkap pada uji ini (termasuk redaksi), tetapi berlisensi AGPL/komersial;
  pemakaian sebagai dependency aplikasi **butuh keputusan lisensi tersendiri**. Rekomendasi
  provider redaksi: MuPDF sebagai worker opsional **jika** keputusan lisensi diambil;
  alternatif: redaksi kustom di atas PDFBox (risiko tinggi, belum dibuktikan).
