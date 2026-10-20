# ROADMAP.md — Milestone M0–M12

Roadmap **boleh direvisi** berdasarkan bukti. Setiap perubahan urutan harus
dicatat di `CHANGELOG.md` dengan alasannya.

Status milestone:

| Milestone | Nama | Status | Keterangan |
|---|---|---|---|
| **M0** | Foundation | **SELESAI (sebagian)** | Docs, analisis, gate teknologi, spike, ADR, skeleton, vertical slice M1. Sisa: packaging (B-03), spike edit teks (B-04). |
| M1 | Viewer | **BERJALAN** | Open/render/zoom/navigasi/thumbnail/cari/selesai. Sisa: info dokumen, salin teks, render async. |
| M2 | Page Operations | TODO | Engine sudah siap; UI belum. |
| M3 | Create & Augment | TODO | |
| M4 | Annotations & Forms | TODO | API engine terverifikasi. |
| M5 | OCR | TODO | Windows OCR terverifikasi. |
| M6 | Optimization & Batch | TODO | |
| M7 | Security | TODO | Enkripsi & redaksi terverifikasi di engine. |
| M8 | Advanced Editing | **DEFER** | B-04. |
| M9 | Conversion | TODO | Office↔PDF ditunda (U-05). |
| M10 | Signatures | TODO | Kriptografis ditunda (U-06). |
| M11 | Modern Workflows | TODO | |
| M12 | Release Hardening | TODO | |

---

## M0 — Foundation ✅ (sebagian)
- [x] Dokumentasi kontinuitas lengkap
- [x] Verifikasi lingkungan
- [x] Analisis referensi (inventaris + dokumentasi)
- [x] Review teknologi pasca-REA (gate)
- [x] Technical spike S1–S12
- [x] ADR-001 stack baseline
- [x] Skeleton aplikasi
- [x] Vertical slice M1 berjalan
- [ ] Build one-dir + ukur ukuran (B-03)
- [ ] Spike edit teks existing (B-04)
- [ ] Inisialisasi git (perlu izin)

## M1 — Viewer
- [x] Open + error handling
- [x] Render, zoom, fit width/fit page
- [x] Navigasi halaman
- [x] Thumbnail
- [x] Search + lompat ke hasil
- [ ] Panel informasi dokumen
- [ ] Seleksi & salin teks
- [ ] Render asynchron (worker thread)
- [ ] Riwayat halaman
- [ ] Checklist manual DPI/keyboard

## M2 — Page Operations
- [ ] UI: putar, hapus, duplikat, susun ulang
- [ ] UI: gabung beberapa dokumen
- [ ] UI: pisah / ekstrak
- [ ] Simpan sebagai + verifikasi output
- [ ] Undo/redo

## M3 — Create & Augment
- [ ] Tambah teks overlay (label jujur)
- [ ] Tambah gambar
- [ ] Watermark
- [ ] Header/footer + nomor halaman
- [ ] Halaman kosong, page range
- [ ] Gambar → PDF

## M4 — Annotations & Forms
- [ ] Highlight, underline, strikeout
- [ ] Note/komentar + panel komentar
- [ ] Bentuk dasar
- [ ] Isi form (AcroForm) + simpan
- [ ] Flatten anotasi/form

## M5 — OCR
- [ ] Adapter OCR (Windows OCR)
- [ ] Dialog: rentang halaman + bahasa
- [ ] Prompt OCR otomatis untuk dokumen scan
- [ ] Lapisan teks tak terlihat + label "bukan teks editable"
- [ ] Preferensi OCR (bahasa, kualitas)
- [ ] Tesseract sebagai opsi lanjut

## M6 — Optimization & Batch
- [ ] Preset kompresi (3) + opsi custom
- [ ] Resample gambar
- [ ] Hapus objek tak terpakai (default noninvasif)
- [ ] Pratinjau delta sebelum apply
- [ ] Antrean batch + progress + cancel + retry

## M7 — Security
- [ ] Enkripsi AES-256 (UI)
- [ ] Permission settings
- [ ] Redaksi aman (+ verifikasi channel metadata)
- [ ] Sanitasi metadata

## M8 — Advanced Editing ⚠️ DEFER
- [ ] **Spike** content-stream surgery (B-04) ← prasyarat
- [ ] Edit teks existing + reflow (hanya bila spike berhasil)
- [ ] Ganti gambar
- [ ] Penanganan font tertanam

## M9 — Conversion
- [ ] PDF → PNG/JPEG/TIFF (terverifikasi, tinggal UI)
- [ ] PDF → teks
- [ ] Office → PDF (DEFER — U-05)
- [ ] PDF → Office (DEFER)
- [ ] Laporan keterbatasan konversi

## M10 — Signatures
- [ ] Gambar tanda tangan + placement
- [ ] Stempel tanda tangan
- [ ] Tanda tangan kriptografis (DEFER — U-06)
- [ ] Peringatan dampak pengeditan pada dokumen bertanda tangan

## M11 — Modern Workflows
- [ ] Command palette
- [ ] Preset workflow
- [ ] Batch resumable
- [ ] Document preflight
- [ ] Ekspor pintar dengan trade-off dijelaskan
- [ ] Ringkasan perubahan
- [ ] CLI

## M12 — Release Hardening
- [ ] Packaging & ukuran terukur
- [ ] Uji mesin bersih
- [ ] Install/uninstall
- [ ] Notices & license bundle
- [ ] User guide
- [ ] Release notes & known limitations
- [ ] Code signing (opsional)
- [ ] AI opsional (opt-in) — hanya bila layak
