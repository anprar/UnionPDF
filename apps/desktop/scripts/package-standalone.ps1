# Assembles a self-contained UnionPDF package (no developer toolchain required).
#
# Contents:
#   unionpdf-desktop.exe        application
#   pdfium.dll                  PDF renderer (third party, licenses included)
#   worker/                     PDFBox worker: jar, libs and the bundled Java runtime
#   licenses/                   third-party license texts
#   NOTICE-THIRD-PARTY.md       components, versions, licenses, sources
#   README.txt                  how to run
#
# The package is portable: it only needs a writable TEMP folder and a WebView2 runtime.
param(
    [string]$Version = "0.1.0",
    [string]$OutDir = "$PSScriptRoot\..\dist-package",
    [switch]$SkipZip
)
$ErrorActionPreference = "Stop"
$AppRoot = Split-Path -Parent $PSScriptRoot
$Release = Join-Path $AppRoot "src-tauri\target\release"
$Stage = Join-Path $OutDir "UnionPDF-$Version"

if (-not (Test-Path (Join-Path $Release "unionpdf-desktop.exe"))) { throw "build release belum ada (npx tauri build --no-bundle)" }
foreach ($need in @("pdfium.dll", "worker\unionpdf-worker.jar", "worker\jre\bin\java.exe")) {
    if (-not (Test-Path (Join-Path $Release $need))) { throw "komponen paket tidak ada: $need (jalankan prepare-pdfium.ps1 / prepare-pdfbox.ps1 / prepare-java-runtime.ps1)" }
}

Write-Output "[package] menyusun $Stage"
Remove-Item $Stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Stage | Out-Null
Copy-Item (Join-Path $Release "unionpdf-desktop.exe") $Stage
Copy-Item (Join-Path $Release "pdfium.dll") $Stage
Copy-Item (Join-Path $Release "worker") $Stage -Recurse
if (Test-Path (Join-Path $Release "licenses")) { Copy-Item (Join-Path $Release "licenses") $Stage -Recurse } else { New-Item -ItemType Directory -Force (Join-Path $Stage "licenses") | Out-Null }
Copy-Item (Join-Path $AppRoot "src-tauri\pdfium\licenses\*") (Join-Path $Stage "licenses") -Force -ErrorAction SilentlyContinue

$notice = @"
UnionPDF - komponen pihak ketiga
================================

Aplikasi: UnionPDF 0.1.0 (desktop Windows, Tauri 2 + React/TypeScript + Rust).
Lisensi proyek UnionPDF: lihat LICENSE di repositori (belum diratifikasi ulang; tidak diubah
dalam siklus restart ini).

| Komponen | Versi | Lisensi | Sumber |
|---|---|---|---|
| PDFium (libpdfium) | chromium/7881 (151.0.7881.0) | BSD-3-Clause + lisensi masing-masing dependensi (lihat licenses/) | bblanchon/pdfium-binaries (distributor pihak ketiga, bukan build Google); SHA-256 dll 79d4676b656cfb1abcea88f9ade3b4b0826c5200382db5f4ec72a636c598c118 |
| Apache PDFBox + FontBox + PDFBox IO | 3.0.8 | Apache-2.0 | Maven Central; SHA-1 & tanda tangan GPG terverifikasi (experiments/restart/deps/PROVENANCE.md) |
| Apache Commons Logging | 1.4.0 | Apache-2.0 | Maven Central; SHA-1 & tanda tangan GPG terverifikasi |
| Eclipse Temurin JDK (runtime image, dikustom dengan jlink) | 17.0.20.1 | GPLv2+Classpath Exception | api.adoptium.net; zip SHA-256 e53a79c3c3d86865bd7e787903884331068e71321714ffd44f145785affc7cb0 |

Runtime Java dibundel berisi modul: java.base, java.desktop, java.logging, java.xml,
java.security.jgss, jdk.crypto.ec, jdk.crypto.cryptoki, java.sql, java.naming,
java.management, jdk.unsupported, java.instrument, jdk.zipfs, jdk.localedata.

PDFium dan PDFBox tidak berada di bawah lisensi AGPL; proyek UnionPDF tidak memuat engine AGPL.
Font yang disertakan runtime Temurin mengikuti lisensi font masing-masing (bagian dari
Temurin GPLv2+CE).

Dokumentasi lisensi lengkap: folder licenses/ dan repositori proyek.
"@
$notice = $notice -replace "tidakurrences", "tidak"
Set-Content -Path (Join-Path $Stage "NOTICE-THIRD-PARTY.md") -Value $notice -Encoding UTF8

$readme = @"
UnionPDF 0.1.0 - paket mandiri (portable)
==========================================

Cara menjalankan
---------------
  1. Buka folder ini.
  2. Klik dua kali unionpdf-desktop.exe.

Tidak perlu memasang Node.js, Rust, JDK, atau toolchain lain. Aplikasi memakai runtime Java
yang sudah disertakan di folder worker\jre.

Kebutuhan sistem
----------------
  - Windows 10/11 x64.
  - Microsoft Edge WebView2 Runtime (biasanya sudah terpasang di Windows 10/11).
    Jika belum, pasang WebView2 Runtime dari Microsoft (gratis, unduhan ~130 MB).
  - Folder TEMP yang bisa ditulis (dipakai untuk berkas sementara saat memproses PDF).

Folder yang ditulis aplikasi
-----------------------------
  - %TEMP%\unionpdf\  berkas sementara selama operasi dokumen (dibersihkan otomatis).
  - %APPDATA%\org.unionpdf.desktop\  state aplikasi Tauri.
  Tidak ada data yang dikirim keluar dari komputer.
"@
Set-Content -Path (Join-Path $Stage "README.txt") -Value $readme -Encoding UTF8

$files = Get-ChildItem $Stage -Recurse -File
$size = ($files | Measure-Object Length -Sum).Sum
Write-Output ("[package] isi: {0} file, {1:N1} MB" -f $files.Count, ($size / 1MB))
$groups = $files | Group-Object { if ($_.FullName -like "*worker\jre\*") { "runtime Java (jre)" } elseif ($_.FullName -like "*worker\lib\*") { "worker libs" } elseif ($_.FullName -like "*licenses\*") { "lisensi" } else { "aplikasi & lain" } }
foreach ($g in $groups) { Write-Output ("  {0,-22} {1,4} file {2,8:N1} MB" -f $g.Name, $g.Count, (($g.Group | Measure-Object Length -Sum).Sum / 1MB)) }

if (-not $SkipZip) {
    $zip = Join-Path $OutDir "UnionPDF-$Version-portable.zip"
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path $Stage -DestinationPath $zip -CompressionLevel Optimal
    Write-Output ("[package] zip: {0} ({1:N1} MB)" -f $zip, ((Get-Item $zip).Length / 1MB))
}
Write-Output "[package] selesai: $Stage"
