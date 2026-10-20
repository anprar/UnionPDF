<#
.SYNOPSIS
  Jalankan UnionPDF.

.PARAMETER File
  Buka dokumen PDF tertentu saat start.

.PARAMETER Offscreen
  Jalankan tanpa jendela (untuk smoke test otomatis).
#>
[CmdletBinding()]
param(
    [string]$File,
    [switch]$Offscreen
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    throw "Virtual environment belum ada. Jalankan .\scripts\setup.ps1 lebih dulu."
}

$env:PYTHONPATH = Join-Path $root 'src'
if ($Offscreen) { $env:QT_QPA_PLATFORM = 'offscreen' }

$argsList = @('-m', 'unionpdf.app')
if ($File) { $argsList += '--file'; $argsList += $File }

& $py @argsList
exit $LASTEXITCODE
