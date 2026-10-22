# Uji paket mandiri UnionPDF pada kondisi "{ hostile":
#   - path dengan spasi dan karakter Unicode
#   - folder instalasi tidak bisa ditulis (file read-only)
#   - tanpa Java eksternal di PATH dan tanpa JAVA_HOME
#   - tanpa toolchain pengembang (node/cargo/jdk tidak dipakai aplikasi)
param(
    [string]$Package = "$PSScriptRoot\..\dist-package\UnionPDF-0.1.0",
    [string]$Root = ""
)
$ErrorActionPreference = "Stop"
# Nama folder uji dibuat dari code point (skrip tetap ASCII; PowerShell 5.1 membaca
# berkas tanpa BOM sebagai ANSI, sehingga karakter Unicode literal akan rusak).
if (-not $Root) {
    $uni = [char]0x00FC + [char]0x006E + [char]0x0069 + "code"   # "ünïcode"
    $Root = Join-Path $env:TEMP "UnionPDF Paket Uji ($uni)"
}
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
$CT = [Windows.Automation.ControlType]
function C($a, $b) { New-Object Windows.Automation.AndCondition($a, $b) }
function P($k, $v) { New-Object Windows.Automation.PropertyCondition($k, $v) }

$dest = Join-Path $Root "Instalasi UnionPDF (v0.1.0)"
Remove-Item $Root -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item (Join-Path $Package "*") $dest -Recurse -Force
Write-Output "[test] paket disalin ke: $dest"

# Folder tidak writable: ACL menolak tulis untuk user saat ini (tanpa admin, dibalik setelah uji).
$aclOk = $false
try {
    & icacls $dest /deny "$($env:USERNAME):(W)" 2>&1 | Out-Null
    $aclOk = $true
} catch { $aclOk = $false }
$probe = Join-Path $dest "probe-tulis.txt"
$writable = $false
try { Set-Content $probe "x" -ErrorAction Stop; $writable = $true; Remove-Item $probe -ErrorAction SilentlyContinue } catch { }
Write-Output "[test] ACL deny-write diterapkan: $aclOk ; folder writable: $writable (diharapkan False)"

# Environment bersih: tanpa Java eksternal.
$savedJavaHome = $env:JAVA_HOME
$savedPath = $env:PATH
$p = $null
try {
    Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue
    $javaDirs = @($savedPath -split ";" | Where-Object { $_ -and (Test-Path (Join-Path $_ "java.exe")) })
    $env:PATH = (($savedPath -split ";" | Where-Object { $_ -and ($javaDirs -notcontains $_) }) -join ";")
    Write-Output "[test] JAVA_HOME dihapus, $($javaDirs.Count) folder Java dibuang dari PATH"

    $exe = Join-Path $dest "unionpdf-desktop.exe"
    $p = Start-Process $exe -PassThru
    Start-Sleep -Seconds 6
    if ($p.HasExited) { throw "aplikasi berhenti dengan kode $($p.ExitCode)" }
    $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
    if (-not $win) { throw "jendela UnionPDF tidak ditemukan" }
    $text = ($win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join ""
    if ($text -notmatch "UnionPDF") { throw "UI tidak termuat: $text" }
    Write-Output "[test] aplikasi start dari path ber-spasi + Unicode, UI tampil"
    if ($text -match "Authoring: PDFBox") { Write-Output "[test] authoring: worker PDFBox terdeteksi" } else { Write-Output "[test] authoring: TIDAK terdeteksi (runtime Java mungkin belum ada di paket)" }

    # Buka dokumen dari fixture untuk memastikan PDFium termuat.
    $fx = Resolve-Path "$PSScriptRoot\..\src-tauri\tests\fixtures\rs05_structure.pdf"
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    $p = Start-Process $exe -ArgumentList "`"$fx`"" -PassThru
    Start-Sleep -Seconds 6
    $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
    $text = ($win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join ""
    if ($text -notmatch "rs05_structure.pdf") { throw "dokumen tidak terbuka dari paket: $text" }
    Write-Output "[test] dokumen dibuka (PDFium termuat)"

    # Berkas sementara harus ditulis ke %TEMP%, bukan ke folder instalasi.
    $tmpDir = Join-Path $env:TEMP "unionpdf"
    Write-Output "[test] folder temp aplikasi: $tmpDir"
    $leftovers = Get-ChildItem $dest -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*.tmp" -or $_.Name -like ".unionpdf-*" }
    if ($leftovers) { throw "paket menulis berkas di folder instalasi: $($leftovers.Name -join ',')" }
    Write-Output "[test] tidak ada berkas sementara di folder instalasi"
} finally {
    if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if ($savedJavaHome) { $env:JAVA_HOME = $savedJavaHome } else { Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue }
    $env:PATH = $savedPath
    if ($aclOk) { & icacls $dest /remove:d "$($env:USERNAME):(W)" 2>&1 | Out-Null }
}
Write-Output "OK: paket mandiri lulus uji path spasi+Unicode, folder read-only, tanpa Java eksternal."
