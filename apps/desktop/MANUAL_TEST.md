# Checklist uji manual UnionPDF

Bagian ini **tidak** diotomatisasi: menggambar anotasi butuh seret mouse, dan harness otomatis tidak
boleh menggerakkan mouse atau memotret desktop. Isi kolom Hasil: PASS / FAIL / NOT_RUN + catatan.

Persiapan (dari `apps/desktop`):
`scripts\prepare-pdfium.ps1`, `scripts\prepare-pdfbox.ps1`, `scripts\prepare-java-runtime.ps1`,
`npx tauri build --no-bundle`, `scripts\stage-release.ps1`, lalu jalankan
`src-tauri\target\release\unionpdf-desktop.exe`.
Fixture: `src-tauri\tests\fixtures\` (rs05_structure, rs03_form, rs08_mixed, rs01_large_500p).

| # | Langkah | Harapan | Hasil |
|---|---|---|---|
| M-01 | Buka dokumen, **gulir** (wheel/touchpad) dari atas ke bawah | Halaman menyambung: bagian bawah halaman N dan atas halaman N+1 terlihat bersamaan; tidak ada lompatan ganti halaman | |
| M-02 | Gulir melewati batas dua halaman slowly | Tidak ada "snapping" atau berhenti di batas; jarak antar kertas tetap seragam | |
| M-03 | Gulir cepat (flick) | Tidak ada halaman kosong/berkabut; render selesai | |
| M-04 | Gulir ke halaman 250 pada dokumen 500 halaman, lalu kembali | Cepat, tidak freeze; thumbnail aktif ikut berubah | |
| M-05 | Klik thumbnail halaman jauh (mis. 6) | Viewport melompat ke halaman itu; nomor halaman status ikut berubah | |
| M-06 | Ketik nomor halaman di kolom status, tekan Enter | Pindah ke halaman tersebut | |
| M-07 | Zoom + / − di tengah dokumen | Posisi baca tetap di halaman yang sama (tidak lompat ke atas) | |
| M-08 | Klik **Lebar**, lalu **Halaman** | Lebar: seluruh lebar halaman muat; Halaman: satu halaman penuh muat | |
| M-09 | Sembunyikan/buka panel thumbnail (tab Beranda) | Lebar/zoom dihitung ulang mengikuti lebar area dokumen | |
| M-10 | Pilih **Satu halaman** di tab Beranda, lalu kembali **Menyambung** | Mode berubah; mode terakhir tersimpan saat aplikasi dibuka lagi | |
| M-11 | Simpan Sebagai ke nama berkas yang **sudah ada** (jawab prompt "Confirm Save As" Windows dengan Ya) | Berkas lama diganti PDF valid; isi lama hilang | |
| M-12 | Anotasi di halaman **kedua** dan halaman jauh: alat Sorot / Garis bawah / Catatan / Teks | Anotasi muncul di halaman yang benar (bukan halaman tetangga); sorot menempel pada teks | |
| M-13 | Seret sorot lintas batas halaman | Gesture dibatalkan (tidak ada anotasi pada dua halaman) | |
| M-14 | Isi form (teks/checkbox/radio/combo), **Simpan Como**, buka lagi | Nilai & tampilan (appearance) tetap benar | |
| M-15 | Putar halaman, Simpan Como, buka lagi | Rotasi tersimpan | |
| M-16 | Ekstrak halaman, periksa bookmark hasil | Bookmark menuju halaman tak diekstrak hilang; field tetap ada | |
| M-17 | DPI 125 %, 150 %, 200 % (jika tersedia) | Teks tajam, toolbar tidak menutupi dokumen, posisi anotasi tepat | |
| M-18 | Pindahkan jendela ke monitor lain (jika tersedia) | Skala & ukuran tetap benar | |
| M-19 | Pasang/­jalankan **installer NSIS** (`target\release\bundle\nsis\UnionPDF_0.1.0_x64-setup.exe`) di mesin bersih | Instalasi berhasil; UnionPDF jalan; authoring (Isi Form) berfungsi **tanpa** Java yang diinstal; uninstall bersih | |
| M-20 | Jalankan paket portabel dari folder **read-only** | Aplikasi tetap jalan; berkas sementara ditulis ke %TEMP% | |
| M-21 | Navigasi keyboard: Tab (fokus toolbar), Ctrl+O, PageUp/PageDown, Ctrl+0, Esc | Fokus terlihat jelas; semua pintasan bekerja | |
| M-22 | Tooltip tiap tombol ikon (hover 1 detik) | Tooltip muncul dan menjelaskan aksi | |
| M-23 | Perkecil jendela sempit (< 900 px) | Toolbar tidak menumpuk menutupi dokumen; tombol tetap dapat diklik | |
| M-24 | Tutup jendela saat ada perubahan belum disimpan | Dialog konfirmasi; "Batal" mempertahankan, "Buang perubahan" menutup | |
| M-25 | Geser mouse di atas teks halaman, lalu salin (Ctrl+C) | Teks yang disalin adalah teks dokumen (bukan nama file) | |
| M-26 | Geser mouse di atas teks dan **sorot** (alat Sorot) | Sorotan menempel tepat pada kata yang disorot (menggunakan lapisan teks) | |
| M-27 | Geser mouse dari satu halaman ke halaman berikutnya saat alat aktif | Gesture dibatalkan; tidak ada anotasi pada dua halaman | |
| M-28 | Klik ganda kata di lapisan teks | Kata terpilih (highlight biru) seperti di pembaca PDF lain | |
| M-29 | Geser mouse menyorot beberapa kata, lalu Ctrl+C, tempel di Notepad | Teks yang ditempel = teks dokumen (bukan nama berkas); coba seleksi yang menyeberangi batas halaman | |
| M-30 | Klik tab kategori yang sedang aktif | Toolbar perintah menyembunyikan/munculkan mengikuti klik | |
| M-31 | Gabung: tambah berkas, atur urutan, klik Gabung, simpan; lalu Pisah (tiap halaman / tiap N / rentang) | Berkas hasil dibuat; bookmark/field tetap utuh; rentang di luar dokumen ditolak | |
| M-32 | Navigasi: tombol halaman pertama/terakhir (belum ada) | Tambah bila dipakai; sementara gunakan Ctrl+Home / End | |
| M-33 | Konversi: PDF→JPEG dan gambar→PDF | Berkas JPEG/PDF terbentuk dan valid | |
| M-34 | Pencarian: Ctrl+F, ketik, Enter/Shift+Enter, Esc, tombol Batalkan untuk pencarian panjang | Jumlah hasil benar; Esc menutup; pencarian panjang dapat dibatalkan | |
| M-35 | Buka `rs10_toc.pdf`; seret mouse menyorot sebagian satu kata pada baris "Form Transaksi" | **Tidak ada tulisan kedua**; hanya satu tulisan yang tampil; highlight tepat di atas teks | |
| M-36 | Sorot satu kalimat penuh, lalu beberapa baris sekaligus | Highlight mengikuti teks yang disorot, tidak bergeser | |
| M-37 | Sorot pada baris dengan dot leader + nomor halaman kanan | Nomor halaman ikut tersorot sesuai posisinya | |
| M-38 | Ulangi sorot pada zoom 75 %, 100 %, 125 %, 150 %, 200 % dan pada "Sesuai lebar" | Highlight tetap menempel pada teks di semua zoom | |
| M-39 | Sorot lalu tekan Ctrl+C, tempel di Notepad | Hasil tempel = teks yang dipilih (bukan teks lain/duplikat) | |
| M-40 | Sorot lalu buka/tutup panel thumbnail; scroll ke halaman lain lalu kembali ke halaman bersorot | Span lama tidak tertinggal; sorotan tetap pada teks yang sama | |
| M-41 | Auto-scroll: pilih "Naik" lalu Mulai (dari tengah dokumen) | Halaman bergerak ke arah awal; tombol status berubah sesuai keadaan | |
| M-42 | Auto-scroll: pilih "Turun" lalu Mulai | Halaman bergerak ke arah akhir | |
| M-43 | Auto-scroll: ganti arah saat berjalan; ubah slider kecepatan; tekan Escape | Tidak lompat halaman; laju berubah (bukan jumlah timer); Escape menghentikan | |
