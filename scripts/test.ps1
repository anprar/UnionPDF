<#
.SYNOPSIS
  Jalankan test suite UnionPDF.

.PARAMETER Verbose
  Tampilkan detail tiap test.
#>
[CmdletBinding()]
param(
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    throw "Virtual environment belum ada. Jalankan .\scripts\setup.ps1 lebih dulu."
}

$env:PYTHONPATH = Join-Path $root 'src'
$env:QT_QPA_PLATFORM = 'offscreen'

$argsList = @('-m', 'pytest', 'tests', '-q', '--maxfail=1')
if ($Verbose) { $argsList = @('-m', 'pytest', 'tests', '-v') }

Push-Location $root
try {
    & $py @argsList
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $code
