# Fixture uji aplikasi

Sintetis, dibuat oleh `experiments/restart/fixtures/generate_fixtures.py` (PyMuPDF), hanya memakai
font base-14 Helvetica **tanpa font tertanam** (diperiksa dengan `get_fonts`). Isi teks buatan sendiri.

| File | SHA-256 | Isi |
|---|---|---|
| `rs05_structure.pdf` | `adb50d4b6075cf55d5bfd0b6b5011ee2b3254f6a80bc90a6254f749d5577d352` | 6 halaman; bookmark Bab 1→h1, Bab 3→h3 (anak: Sub 3.1→h4), Bab 6→h6; link h1→h4; anotasi Text di h2; field teks `rs05_field` di h3 |
| `rs03_form.pdf` | `b2880b40615005d108603e4ef7c880ca8b9896eb9fd3f4e1312d92ccfe10a512` | form v2: teks `nama`, checkbox `setuju`, grup radio `pilihan` (A, B), combo `kota` |
| `rs08_mixed.pdf` | `12f461e9e0a07e1306b4e14889ad63e9fd08b45c93fed9c709bf6c79b13abcbb` | 5 halaman ukuran campuran (A4, Letter, A5, A4, Letter) - untuk uji layout continuous |
