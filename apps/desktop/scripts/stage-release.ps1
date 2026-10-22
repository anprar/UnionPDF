# Menempatkan komponen runtime di samping exe release lokal (BUKAN installer):
#   target/release/pdfium.dll        (dari src-tauri/pdfium/bin, SHA-256 diperiksa)
#   target/release/worker/...        (dari src-tauri/worker: unionpdf-worker.jar + lib/)
# Java runtime TIDAK disertakan: worker memakai UNIONPDF_JAVA / JAVA_HOME / PATH.
$ErrorActionPreference = "Stop"
$AppRoot = Split-Path -Parent $PSScriptRoot
$Release = Join-Path $AppRoot "src-tauri\target\release"
$DllSha256 = "79d4676b656cfb1abcea88f9ade3b4b0826c5200382db5f4ec72a636c598c118"

if (-not (Test-Path (Join-Path $Release "unionpdf-desktop.exe"))) { throw "Build release belum ada (npx tauri build --no-bundle)" }
$dll = Join-Path $AppRoot "src-tauri\pdfium\bin\pdfium.dll"
if ((Get-FileHash $dll -Algorithm SHA256).Hash.ToLower() -ne $DllSha256) { throw "pdfium.dll tidak cocok; jalankan prepare-pdfium.ps1" }
Copy-Item $dll $Release -Force
$worker = Join-Path $AppRoot "src-tauri\worker"
if (Test-Path (Join-Path $worker "unionpdf-worker.jar")) {
    Copy-Item $worker $Release -Recurse -Force
    Write-Output "Worker PDFBox disalin ke $Release\worker"
} else {
    Write-Warning "Worker PDFBox belum dibangun (prepare-pdfbox.ps1): fitur authoring tidak akan tersedia"
}
Write-Output "Siap: $Release\unionpdf-desktop.exe"
