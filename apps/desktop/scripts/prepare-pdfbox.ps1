# Menyiapkan worker PDFBox untuk development UnionPDF (lokal-proyek, tanpa admin).
# Sumber JAR: salinan terverifikasi di experiments/restart/deps/pdfbox/jars
# (Maven Central; SHA-1 + tanda tangan GPG diverifikasi — experiments/restart/deps/PROVENANCE.md §7).
# Output: src-tauri/worker/{unionpdf-worker.jar, lib/*.jar} (gitignored).
# Butuh JDK 8+ (javac). Ini kebutuhan BUILD; runtime distribusi dibahas terpisah (JRE belum ditentukan).
param([string]$Jdk = "")
$ErrorActionPreference = "Stop"

$Pinned = [ordered]@{
    "pdfbox-3.0.8.jar"          = "97647cfbde61ebcfc06b4cf8c9b0ffcaaee073396eceb4a7f6836a9b9128903c"
    "fontbox-3.0.8.jar"         = "a1915c24e3edbe0ecec93896dfbf6d41427810b663ade97bd4e8bae86ec3fdab"
    "pdfbox-io-3.0.8.jar"       = "36a0e04001010b4c764857817412b96339930b19755e728959805cc0352061b2"
    "commons-logging-1.4.0.jar" = "d175dbd751dd782a63bde28c7a039520e971f25e84b79c19b8435edc3603e0dc"
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$Src     = Join-Path $AppRoot "..\..\experiments\restart\deps\pdfbox\jars"
$Out     = Join-Path $AppRoot "src-tauri\worker"
$Lib     = Join-Path $Out "lib"
$Build   = Join-Path $AppRoot "worker-pdfbox\build"

if (-not $Jdk) {
    $javac = Get-Command javac -ErrorAction SilentlyContinue
    if ($javac) { $Jdk = Split-Path -Parent $javac.Source }
    elseif (Test-Path "C:\Program Files\Zulu\zulu-8\bin\javac.exe") { $Jdk = "C:\Program Files\Zulu\zulu-8\bin" }
    else { throw "javac tidak ditemukan; berikan -Jdk <folder bin JDK>" }
}

New-Item -ItemType Directory -Force $Lib, $Build | Out-Null
foreach ($name in $Pinned.Keys) {
    $from = Join-Path $Src $name
    if (-not (Test-Path $from)) { throw "JAR tidak ada: $from (jalankan ulang spike G-4 / unduh sesuai PROVENANCE §7)" }
    $h = (Get-FileHash $from -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $Pinned[$name]) { throw "SHA-256 tidak cocok untuk $name ($h)" }
    Copy-Item $from (Join-Path $Lib $name) -Force
}

Get-ChildItem $Build -Recurse -File | Remove-Item
$sources = Get-ChildItem (Join-Path $AppRoot "worker-pdfbox\src") -Recurse -Filter *.java | ForEach-Object { $_.FullName }
& (Join-Path $Jdk "javac.exe") -encoding UTF-8 -Xlint:-options -source 8 -target 8 -cp "$Lib\*" -d $Build @sources
if ($LASTEXITCODE -ne 0) { throw "kompilasi worker gagal" }

$manifest = Join-Path $Build "MANIFEST.MF"
$cp = ($Pinned.Keys | ForEach-Object { "lib/$_" }) -join " "
[IO.File]::WriteAllText($manifest, "Main-Class: org.unionpdf.worker.Main`r`nClass-Path: $cp`r`n`r`n", [Text.UTF8Encoding]::new($false))
& (Join-Path $Jdk "jar.exe") cfm (Join-Path $Out "unionpdf-worker.jar") $manifest -C $Build org
if ($LASTEXITCODE -ne 0) { throw "pembuatan JAR gagal" }
Write-Output "Siap: $Out\unionpdf-worker.jar (+ $($Pinned.Count) JAR di lib\)"
