# RS-00 — Review dependency & provenance PDFium (hasil)

| Field | Nilai |
|---|---|
| Spike | RS-00 (persetujuan A-6) |
| Sesi | `2026-10-21T1114+0700` |
| Verdict | **GO untuk dipakai di spike** — distributor pihak ketiga, **bukan build resmi Google** |
| Tidak berarti | PDFium disetujui sebagai engine produksi; biner ini disetujui untuk distribusi |

## 1. Versi yang ditetapkan sebelum unduh

| Komponen | Versi | Alasan pemilihan |
|---|---|---|
| Crate `pdfium-render` | **0.9.4** (rilis stabil terbaru di crates.io, tidak di-yank) | Wrapper Rust yang ditinjau di `POST_ALL_REFERENCES_TECH_REVIEW.md` §2.2 |
| Biner PDFium | **`chromium/7881`** ("PDFium 151.0.7881.0"), aset `pdfium-win-x64.tgz` (varian tanpa V8/XFA) | Fitur default `pdfium_latest` di `pdfium-render 0.9.4` = `pdfium_7881` → binding API cocok dengan build |
| Platform | Windows x64 | Mesin spike |

Rilis distributor terbaru saat review adalah `chromium/8111` (2026-10-19). Ia **tidak**
dipakai karena binding `pdfium-render 0.9.4` diikat ke API 7881. Trade-off: perbaikan
upstream setelah 7881 tidak termasuk. Untuk produksi, pemilihan versi harus ditinjau ulang.

## 2. Crate `pdfium-render`

| Item | Nilai | Sumber |
|---|---|---|
| Lisensi | `MIT OR Apache-2.0` | crates.io API, `Cargo.toml` |
| Checksum crates.io (`.crate`) | `8948a803616a9e936b15a6637af2cd48c5fb8ae0fcdeb3c32eac3a540e255a19` | crates.io API |
| Dipublikasikan | 2026-09-06T14:41:29Z | crates.io API |
| Repository | <https://github.com/ajrcarey/pdfium-render> | crates.io API |
| `rust_version` crate | 1.61 (dengan fitur `image` 0.25: 1.80.1 menurut README) | crates.io, README |
| Toolchain lokal | rustc/cargo 1.98.0 (tidak di-upgrade) | `rustc --version` |
| Dependency normal (non-WASM) | bitflags, bytemuck, bytes, chrono, itertools, libloading, log, maybe-owned, once_cell, utf16string, vecmath; opsional: image, windows | crates.io API |

Lisensi dependency transitif dicatat dari `Cargo.lock` di `results/RS-00.md` setelah
resolusi.

## 3. Biner PDFium — provenance

| Item | Nilai | Sumber / metode |
|---|---|---|
| Upstream | PDFium (`pdfium.googlesource.com/pdfium`), branch `chromium/7881` | Isi rilis |
| Pembangun/distributor | `bblanchon/pdfium-binaries` (komunitas; README: *"isn't affiliated with Google or Foxit"*) | README |
| Rilis | tag `chromium/7881`, dipublikasikan 2026-06-08T17:07:25Z oleh `github-actions[bot]` | GitHub API |
| Commit resep build | `867b3ecc32163d715e84708c51fae5f031254985` (= target tag `chromium/7881`) | GitHub API + atestasi |
| Aset | `pdfium-win-x64.tgz`, 3.733.154 byte | GitHub API, unduhan |
| Digest yang dipublikasikan GitHub | `sha256:73cc0de638ac2095e7445bf56a38200a5b7c7ca0e9f4ba144598f2457377ac08` | GitHub API |
| SHA-256 unduhan lokal | sama persis | `Get-FileHash` |
| Atestasi | 2: in-toto *release* v0.2 dan **SLSA provenance v1** | GitHub attestations API |
| Verifikasi kriptografis | `gh attestation verify … --repo bblanchon/pdfium-binaries` → **exit 0**, 1 hasil terverifikasi | gh 2.89.0 |
| Identitas penandatangan | issuer `https://token.actions.githubusercontent.com`; SAN `…/bblanchon/pdfium-binaries/.github/workflows/build-all.yml@refs/heads/master`; trigger `workflow_dispatch` | sertifikat Sigstore |
| Run build | <https://github.com/bblanchon/pdfium-binaries/actions/runs/27143496415/attempts/1> | atestasi |
| Transparency log | 1 timestamp terverifikasi | `gh attestation verify --format json` |
| `pdfium.dll` | 7.211.520 byte, SHA-256 `79d4676b656cfb1abcea88f9ade3b4b0826c5200382db5f4ec72a636c598c118`, FileVersion 151.0.7881.0 | lokal |
| Authenticode DLL | **NotSigned** | `Get-AuthenticodeSignature` |
| Resource versi DLL | `CompanyName "Google Inc."` berasal dari **template distributor** (`patches/win/resources.rc`); `FileDescription "PDFium (compiled by github.com/bblanchon)"` — **bukan** bukti build/tanda tangan Google | isi template pada commit build |

### Konfigurasi build (`args.gn` dalam paket)

`is_component_build=false`, `is_debug=false`, `pdf_enable_v8=false`, `pdf_enable_xfa=false`,
`pdf_is_standalone=true`, `pdf_use_partition_alloc=false`, `target_cpu="x64"`,
`target_os="win"`, `treat_warnings_as_errors=false`.

### Patch yang diterapkan (Windows, build shared, tanpa V8)

| Patch | Isi | Dampak pada logika PDF |
|---|---|---|
| `patches/shared_library.patch` | `component("pdfium")` → `shared_library`; tambah `resources.rc`; `FPDF_EXPORT` selalu `__declspec(dllexport)` | Tidak ada — build/ekspor simbol |
| `patches/public_headers.patch` | Path `#include` relatif di `public/cpp/*` | Tidak ada — header |
| `patches/win/build.patch` | Pemanggilan `rc.exe` di toolchain | Tidak ada — toolchain |
| `patches/win/resources.rc` | Resource versi Windows | Tidak ada — metadata |

Semua file di atas identik antara ref tag `chromium/7881` dan commit `867b3ecc` (dibandingkan
via SHA blob GitHub).

## 4. Lisensi & third-party notices (isi paket)

`LICENSE` paket = MIT (skrip/paket distributor, © Benoit Blanchon). Folder `licenses/`
berisi lisensi pustaka yang ter-link menurut `steps/08-licenses.sh`:

pdfium (BSD-3-Clause), abseil (Apache-2.0), agg23, fast_float (MIT), freetype (FreeType
License/FTL), icu (lisensi ICU/Unicode), lcms, libjpeg_turbo (IJG + BSD), libopenjpeg,
libpng, libtiff, llvm-libc, simdutf, zlib.

Penilaian: semuanya permisif; **kewajiban notice** harus dipenuhi bila kelak
didistribusikan (FTL memuat klausul kredit dokumentasi). Tidak ditemukan lisensi copyleft
atau komersial pada paket varian non-V8 ini. Penilaian lisensi rinci per pustaka
**belum** dilakukan (teks dibaca sekilas, tidak dianalisis hukum).

## 5. Keterbatasan

- Atestasi membuktikan artefak dibangun oleh workflow repo distributor; **tidak**
  membuktikan bahwa workflow/toolchain itu sendiri bebas masalah, dan tidak setara dengan
  build reproduksi sendiri.
- DLL tidak bertanda tangan Authenticode; distribusi produksi butuh keputusan signing.
- Versi 7881 lebih lama dari rilis distributor terbaru.

## 7. RS-00-B — PDFBox 3.0.8 & Bouncy Castle 1.84 (G-4, 2026-10-21)

Sumber: Maven Central (`repo1.maven.org/maven2`). Versi PDFBox = rilis terbaru 3.0.x saat review;
versi `commons-logging` (1.4.0) dan Bouncy Castle (1.84) **diambil dari POM `pdfbox-parent-3.0.8`**
(bukan versi terbaru BC 1.86), agar sesuai versi yang dideklarasikan PDFBox.

| Artefak | Byte | SHA-256 (lokal) | `.sha1` Maven | Tanda tangan `.asc` | Penandatangan (sidik kunci) |
|---|---:|---|---|---|---|
| `pdfbox-3.0.8.jar` | 2.070.583 | `97647cfb…9128903c` | cocok | **GOODSIG/VALIDSIG** | Andreas Lehmkuehler (CODE SIGNING KEY) `A602970FE1BF5C9C8A9491B97A3C9FE21DFDBF44` |
| `fontbox-3.0.8.jar` | 1.647.000 | `a1915c24…6ec3fdab` | cocok | **GOODSIG/VALIDSIG** | idem |
| `pdfbox-io-3.0.8.jar` | 51.906 | `36a0e040…352061b2` | cocok | **GOODSIG/VALIDSIG** | idem |
| `commons-logging-1.4.0.jar` | 75.828 | `d175dbd7…3603e0dc` | cocok | **GOODSIG/VALIDSIG** | Gary Gregory `F4DD59C90148BDC52BEB90A4530AA5F25C25011F` |
| `bcprov-jdk18on-1.84.jar` | 8.919.063 | `64d6c5a6…1858b2731` | cocok | **GOODSIG/VALIDSIG** | The Legion of the Bouncy Castle Inc. (Maven Repository Artifact Signer) `7B121B76A7ED6CE6E60AD51784E913A8E3A748C0` |
| `bcpkix-jdk18on-1.84.jar` | 1.165.716 | `c87f16ed…7ec7ec1bb` | cocok | **GOODSIG/VALIDSIG** | idem |
| `bcutil-jdk18on-1.84.jar` | 707.499 | `b374e169…45f7619a` | cocok | **GOODSIG/VALIDSIG** | idem |

Metode & batas kepercayaan:
- gpg 2 (bawaan Git for Windows, `C:\Program Files\Git\usr\bin\gpg.exe`) dengan **keyring
  lokal-proyek** (`deps/pdfbox/gnupg/`, gitignored); tidak ada keyring global yang diubah.
- Kunci Apache diambil dari `https://downloads.apache.org/pdfbox/KEYS` dan
  `https://downloads.apache.org/commons/KEYS`; kunci BC dari
  `https://downloads.bouncycastle.org/java/bc_maven_public_key.asc` (ditautkan halaman unduhan
  resmi `bouncycastle.org/download/bouncy-castle-java/`).
- Status gpg: `TRUST_UNDEFINED` — kunci **tidak** disertifikasi web-of-trust. Identitas
  penandatangan hanya berjangkar pada file kunci dari situs resmi proyek via HTTPS. Klaim yang
  sah: "tanda tangan valid terhadap kunci yang dipublikasikan situs resmi proyek"; **bukan**
  rantai kepercayaan penuh.
- Lisensi: PDFBox, fontbox, pdfbox-io, commons-logging = Apache-2.0 (deklarasi POM/proyek
  Apache); Bouncy Castle = lisensi MIT-style Bouncy Castle (teks lisensi **belum** dibaca
  langsung pada sesi ini).
- Runtime: Zulu 8 JDK 1.8.0_345 (sudah terpasang); PDFBox 3.0 minimum Java 8.

## 6. Lokasi lokal (tidak dilacak Git)

- Arsip: `experiments/restart/deps/download/pdfium-win-x64.tgz`
- Ekstraksi: `experiments/restart/deps/pdfium/chromium-7881/`
