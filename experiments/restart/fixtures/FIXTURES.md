# Manifest fixture sintetis (spike restart)

| Field | Nilai |
|---|---|
| Generator | `fixtures/generate_fixtures.py` |
| Engine generator | PyMuPDF 1.27.2.2 (`.venv`) — **bukan** engine yang diuji (PDFium) |
| Sumber isi | Seluruhnya sintetis (teks, gradien piksel buatan) |
| Lisensi | Fixture dibuat proyek; tidak memuat dokumen pihak ketiga |
| Pengecualian | `rs01_unicode_arabic.pdf` menanamkan font sistem `C:\Windows\Fonts\arial.ttf` → **tidak boleh di-commit/didistribusikan**; seluruh `fixtures/generated/` di-gitignore |
| Dibuat | 2026-10-21, sesi `2026-10-21T1114+0700` |

## File (hash run ini)

PyMuPDF menyimpan dengan `no_new_id=True` dan metadata tanggal tetap; reproduksibilitas
byte-per-byte antar-run **belum** diverifikasi.

| File | Byte | Halaman | SHA-256 |
|---|---:|---:|---|
| `rs01_images.pdf` | 85.015 | 1 | `29282151f341e09c59b6e2f6a872a96b8316b66db9241fdecf8d2799c172cd7a` |
| `rs01_large_500p.pdf` | 163.639 | 500 | `9921537a9acc9d84b385d7fdb6f6d7ad78c0c0682e2bec3ca110418e70900e15` |
| `rs01_latin.pdf` | 2.102 | 2 | `24c9d12f87f84a0f0604a6d039e2aaafef8f978ef46225c77b67e8506f370ab0` |
| `rs01_mixed_sizes.pdf` | 2.062 | 4 | `83acf9a349dc7a7d2c8f40c9db9274589a7ab65efe8ea8e06cdef1647262bdf3` |
| `rs01_unicode_arabic.pdf` | 586.356 | 1 | `c04e8f7921beca4018798e452adae9302679fb92d28d1f4768412e8fca8c05a7` |
| `rs02_annot_base.pdf` | 2.018 | 2 | `e5301d3a70c89b2276a8a6d48fdeb71e100450340742b8770175bebe857b4ee7` |
| `rs03_form.pdf` | 4.034 | 1 | `0c8e98abc6244f99302141d151741f60563f6c0dc22426415e070ea8cfd698ab` |
| `rs05_merge_source.pdf` | 1.347 | 2 | `e9342e4bf0a3bc3f880e2b2ddb8d8f91607872bc8e3fbe4c220e66dbf0cba2dd` |
| `rs05_structure.pdf` | 4.588 | 6 | `adb50d4b6075cf55d5bfd0b6b5011ee2b3254f6a80bc90a6254f749d5577d352` |

## v2 (2026-10-21) — fixture diperbaiki + fixture redaksi

| File | Byte | Halaman | SHA-256 |
|---|---:|---:|---|
| `rs01_latin.pdf` | 587.126 | 2 | `1d0ec805d40972650096ca94457ffbda7b424a61f7511ee86612b8a1481a4976` |
| `rs01_unicode_arabic.pdf` | 586.515 | 1 | `166cb1486dd8e8969484f6812613ce4cfa5238c04253db1e23705c5bff72cd07` |
| `rs03_form.pdf` | 4.138 | 1 | `b2880b40615005d108603e4ef7c880ca8b9896eb9fd3f4e1312d92ccfe10a512` |
| `rs07_redact.pdf` | 35.066 | 1 | `4fd69d77af718bb481198446a8b962228cab18fe41b5588356b6e277fdc76e75` |

File lain tidak berubah dari v1. Perbaikan: `Œ` via font TrueType; Arab via `insert_htmlbox`
(HarfBuzz, `dir="rtl"`); radio = satu field grup `pilihan` (`/Parent` + `/Kids`, on-state A/B).
`rs01_latin.pdf` kini juga menanamkan Arial → **tidak boleh di-commit**. Spasi pada teks TrueType
diekstrak sebagai U+00A0 oleh kedua pembaca; perbandingan teks memakai NFKC.

## Cacat fixture v1 (sudah diperbaiki di v2)

| Fixture | Cacat | Bukti | Dampak |
|---|---|---|---|
| `rs01_latin.pdf` | `Œ` (U+0152) ditulis generator sebagai glyph `·` (U+00B7) dengan font base-14 `helv` | Render PDFium menampilkan `·uvre`; PyMuPDF juga mengekstrak `·` | Baris itu tidak dapat menguji engine |
| `rs01_unicode_arabic.pdf` | Teks Arab disisipkan urutan logis kiri→kanan **tanpa** shaping/bidi; spasi dipetakan ke U+00A0 oleh ToUnicode generator | PyMuPDF & PDFium sama-sama membalik kata dan mengembalikan U+00A0 | Uji RTL/Unicode **tidak valid** |
| `rs03_form.pdf` | Dua radio button adalah dua field terpisah bernama sama `pilihan` (tanpa `/Parent`, bukan grup) | Objek mentah: `Parent=null` untuk keduanya | Uji radio terkontaminasi cacat fixture |
