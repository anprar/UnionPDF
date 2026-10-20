<#
.SYNOPSIS
  Jalankan seluruh technical spike dan simpan hasil JSON.

.DESCRIPTION
  Spike berada di folder spikes/ dan TERPISAH dari kode produksi.
  Hasil ditulis ke spikes/out/*.json lalu diringkas ke docs/test-runs/.
#>
[CmdletBinding()]
param(
    [string]$Only = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    throw "Virtual environment belum ada. Jalankan .\scripts\setup.ps1 lebih dulu."
}

$env:PYTHONPATH = Join-Path $root 'src'
$env:PYTHONIOENCODING = 'utf-8'

$spikes = Get-ChildItem (Join-Path $root 'spikes') -Filter 'spike_*.py' | Sort-Object Name
if ($Only) {
    $spikes = $spikes | Where-Object { $_.Name -like "*$Only*" }
}

$failed = @()
foreach ($spike in $spikes) {
    Write-Host "==> $($spike.Name)" -ForegroundColor Cyan
    Push-Location $root
    try {
        & $py $spike.FullName | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    GAGAL (exit $LASTEXITCODE)" -ForegroundColor Red
            $failed += $spike.Name
        } else {
            Write-Host "    OK" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Spike gagal: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "Semua spike selesai. Hasil: spikes\out\*.json" -ForegroundColor Green
exit 0
