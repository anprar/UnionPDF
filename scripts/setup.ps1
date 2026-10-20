<#
.SYNOPSIS
  Siapkan lingkungan pengembangan UnionPDF (venv lokal + dependensi).

.DESCRIPTION
  Membuat .venv di dalam workspace (bukan instalasi global), memasang
  dependensi runtime dan development sesuai requirements*.txt.

  Tidak menjalankan tindakan administrator dan tidak mengubah PATH sistem.
#>
[CmdletBinding()]
param(
    [switch]$SkipDev
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv'
$py = Join-Path $venv 'Scripts\python.exe'

function Write-Step([string]$Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

Write-Step "Workspace: $root"

if (-not (Test-Path $py)) {
    Write-Step "Membuat virtual environment di .venv"
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Gagal membuat venv (exit $LASTEXITCODE)" }
} else {
    Write-Step "Virtual environment sudah ada"
}

Write-Step "Memutakhirkan pip"
& $py -m pip install --upgrade pip --disable-pip-version-check --quiet

Write-Step "Memasang dependensi runtime"
& $py -m pip install -r (Join-Path $root 'requirements.txt') --disable-pip-version-check
if ($LASTEXITCODE -ne 0) { throw "Gagal memasang dependensi runtime (exit $LASTEXITCODE)" }

if (-not $SkipDev) {
    Write-Step "Memasang dependensi pengembangan"
    & $py -m pip install -r (Join-Path $root 'requirements-dev.txt') --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { throw "Gagal memasang dependensi development (exit $LASTEXITCODE)" }
}

Write-Step "Memverifikasi instalasi"
& $py -c "import pymupdf, PySide6; print('pymupdf', pymupdf.__version__); print('PySide6', PySide6.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Verifikasi gagal (exit $LASTEXITCODE)" }

Write-Host ""
Write-Host "Selesai. Jalankan aplikasi dengan: .\scripts\run.ps1" -ForegroundColor Green
