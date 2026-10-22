# Menyiapkan pdfium.dll untuk development UnionPDF (lokal-proyek, tanpa admin).
# Biner: bblanchon/pdfium-binaries tag chromium/7881 (distributor pihak ketiga, BUKAN build Google).
# Provenance & verifikasi: experiments/restart/deps/PROVENANCE.md
$ErrorActionPreference = "Stop"

$TagUrl     = "https://github.com/bblanchon/pdfium-binaries/releases/download/chromium/7881/pdfium-win-x64.tgz"
$TgzSha256  = "73cc0de638ac2095e7445bf56a38200a5b7c7ca0e9f4ba144598f2457377ac08"
$DllSha256  = "79d4676b656cfb1abcea88f9ade3b4b0826c5200382db5f4ec72a636c598c118"

$AppRoot  = Split-Path -Parent $PSScriptRoot
$Target   = Join-Path $AppRoot "src-tauri\pdfium"
$Verified = Join-Path $AppRoot "..\..\experiments\restart\deps\pdfium\chromium-7881"

function Test-Dll($path) {
    (Test-Path $path) -and ((Get-FileHash $path -Algorithm SHA256).Hash.ToLower() -eq $DllSha256)
}

if (Test-Dll (Join-Path $Target "bin\pdfium.dll")) {
    Write-Output "pdfium.dll sudah ada dan SHA-256 cocok: $Target\bin\pdfium.dll"
    exit 0
}

New-Item -ItemType Directory -Force $Target | Out-Null
if (Test-Dll (Join-Path $Verified "bin\pdfium.dll")) {
    Copy-Item (Join-Path $Verified "*") $Target -Recurse -Force
    Write-Output "Disalin dari salinan terverifikasi spike: $Verified"
} else {
    $tmp = Join-Path $env:TEMP "unionpdf-pdfium-win-x64.tgz"
    Invoke-WebRequest -UseBasicParsing -Uri $TagUrl -OutFile $tmp
    $h = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $TgzSha256) { Remove-Item $tmp; throw "Digest arsip tidak cocok ($h); dibatalkan." }
    if (Get-Command gh -ErrorAction SilentlyContinue) {
        gh attestation verify $tmp --repo bblanchon/pdfium-binaries | Out-Null
        if ($LASTEXITCODE -ne 0) { Remove-Item $tmp; throw "Verifikasi atestasi gagal; dibatalkan." }
    } else {
        Write-Warning "gh tidak tersedia: atestasi SLSA tidak diverifikasi (hanya digest)."
    }
    tar -xzf $tmp -C $Target
    Remove-Item $tmp
}

if (-not (Test-Dll (Join-Path $Target "bin\pdfium.dll"))) { throw "pdfium.dll tidak cocok setelah penyiapan." }
Write-Output "Siap: $Target\bin\pdfium.dll (lisensi pihak ketiga di $Target\licenses)"
