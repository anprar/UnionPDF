# ADR-003 — Runtime Java bundel (jlink) & paket mandiri UnionPDF

- Status: **Accepted** (keputusan pengguna 2026-10-22: "Saya memilih bundling runtime Java khusus UnionPDF")
- Tanggal: 2026-10-22
- Rujukan: `docs/decisions/ADR-002-restart-foundation.md`, `apps/desktop/scripts/prepare-java-runtime.ps1`,
  `apps/desktop/scripts/package-standalone.ps1`, `apps/desktop/scripts/test-bundled-jre.ps1`
- Supersedes: Draft B-RT1 di `docs/BLOCKERS.md` (runtime Java) — status blockir ditutup.

## Konteks

Worker authoring PDFBox membutuhkan Java. Alternatif yang sempat dipertimbangkan:
- `UNIONPDF_JAVA` / `JAVA_HOME` / `PATH` — bergantung pada instalasi pengguna, tidak boleh
  diasumsikan ada ("Jangan mistakenly menganggap komputer pengguna memiliki JDK terpasang").
- Membawa JRE utuh (~280 MB) melampaui anggaran ukuran installer core ≤ 250 MB (A-2).
- Bekerja dengan user lain → tidak boleh, dan tidak ada hak admin.

## Keputusan

**Runtime image Java 17 LTS (Eclipse Temurin 17.0.20.1) yang dipangkas dengan `jlink`**,
dibuat di workspace dan disertakan dalam paket.

| Aspek | Nilai |
|---|---|
| Distributor | Eclipse Temurin (Adoptium), `api.adoptium.net` |
| Versi | 17.0.20.1 (LTS) |
| Zip yang diunduh | 182,0 MB, SHA-256 `e53a79c3c3d86865bd7e787903884331068e71321714ffd44f145785affc7cb0` |
| Lisensi | GPLv2+Classpath Exception (Teks lisensi & sumber dari vendor; dicatat di `NOTICE-THIRD-PARTY.md`) |
| Modul runtime | java.base, java.desktop, java.logging, java.xml, java.security.jgss, jdk.crypto.ec, jdk.crypto.cryptoki, java.sql, java.naming, java.management, jdk.unsupported, java.instrument, jdk.zipfs, jdk.localedata |
| Ukuran runtime image | **53,1 MB** (`jlink --strip-debug --no-header-files --no-man-pages --compress=2`) |
| Analisis dependency | `jdeps --print-module-deps --ignore-missing-deps --class-path lib` → java.base, java.desktop, java.logging (+ daftar konservatif di atas) |

Analisis statis **tidak** dianggap cukup: `scripts/test-bundled-jre.ps1` menjalankan seluruh
operasi worker (inspect, extract, merge, fill_form, add_annotations) dengan runtime terpotong dan
memverifikasi hasilnya dengan PyMuPDF — mencakup font, imaging, XML, dan kriptografi.

## Packaging

| Artefak | Ukuran | Isi |
|---|---|---|
| Paket portabel (`dist-package/UnionPDF-0.1.0/`) | 74,6 MB | exe 10,9 MB · pdfium.dll 6,9 MB · worker (jar + lib 3,7 MB + jre 53,1 MB) · lisensi · NOTICE · README |
| ZIP portabel | 48,0 MB | zip yang sama |
| Installer NSIS | 43,2 MB | `target/release/bundle/nsis/UnionPDF_0.1.0_x64-setup.exe` (perUser, tanpa code signing) |

Runtime Java **tidak lagi** diambil dari `JAVA_HOME`/`PATH` pada build release: `worker::discover`
memakai `<worker>/jre/bin/java.exe` lebih dulu, dan fallback ke Java eksternal hanya di build debug
atau bila `UNIONPDF_ALLOW_EXTERNAL_JAVA=1` disetel eksplisit.

## Konsekuensi

- Positif: pengguna cukup klik exe; authoring (anotasi, form, extract/merge terstruktur) bekerja
  tanpa memasang apa pun; ukuran sesuai anggaran.
- Negatif: runtime image harus dibangun ulang bila modul PDFBox berubah (build script mengulang
  analisis jdeps); obligation lisensi GPLv2+CE untuk runtime (bukan untuk kode UnionPDF).
- Tidak berubah: lisensi proyek UnionPDF tidak diubah; tidak ada engine AGPL; tidak ada
  instalasi global.

## Uji

- `scripts/test-bundled-jre.ps1` — semua operasi worker dengan runtime bundel → PASS.
- `scripts/test-no-external-java.ps1` — aplikasi memakai runtime bundel tanpa `JAVA_HOME`/PATH Java → PASS.
- `scripts/test-package.ps1` — paket pada path ber-spasi + Unicode, folder instalasi tidak writable
  (ACL deny-write), tanpa Java eksternal, tanpa berkas sementara di folder instalasi → PASS.
- Clean-install dari installer NSIS → **NOT_RUN** (menjalankan installer di luar izin; checklist
  ada di `apps/desktop/MANUAL_TEST.md` M-13…M-15).

## Review

Tinjau ulang bila: modul PDFBox berubah, anggaran ukuran berubah, atau runtime image gagal
mencukupi dependency baru.
