# Menyiapkan worker PDFBox untuk development UnionPDF (lokal-proyek, tanpa admin).
# Sumber JAR: Maven Central (sha256 diverifikasi) atau salinan spike yang sudah terverifikasi.
# Output: src-tauri/worker/{unionpdf-worker.jar, lib/*.jar} (gitignored).
# Butuh JDK 8+ (javac). Ini kebutuhan BUILD; runtime distribusi dibahas terpisah (ADR-003).
param([string]$Jdk = "", [switch]$ForceDownload)
$ErrorActionPreference = "Stop"

# name => @{ sha256; url }
$Pinned = [ordered]@{
    "pdfbox-3.0.8.jar"          = @{ sha = "97647cfbde61ebcfc06b4cf8c9b0ffcaaee073396eceb4a7f6836a9b9128903c"; url = "https://repo1.maven.org/maven2/org/apache/pdfbox/pdfbox/3.0.8/pdfbox-3.0.8.jar" }
    "fontbox-3.0.8.jar"         = @{ sha = "a1915c24e3edbe0ecec93896dfbf6d41427810b663ade97bd4e8bae86ec3fdab"; url = "https://repo1.maven.org/maven2/org/apache/pdfbox/fontbox/3.0.8/fontbox-3.0.8.jar" }
    "pdfbox-io-3.0.8.jar"       = @{ sha = "36a0e04001010b4c764857817412b96339930b19755e728959805cc0352061b2"; url = "https://repo1.maven.org/maven2/org/apache/pdfbox/pdfbox-io/3.0.8/pdfbox-io-3.0.8.jar" }
    "commons-logging-1.4.0.jar" = @{ sha = "d175dbd751dd782a63bde28c7a039520e971f25e84b79c19b8435edc3603e0dc"; url = "https://repo1.maven.org/maven2/commons-logging/commons-logging/1.4.0/commons-logging-1.4.0.jar" }
}

$AppRoot = Split-Path -Parent $PSScriptRoot
$Src     = Join-Path $AppRoot "..\..\experiments\restart\deps\pdfbox\jars"
$Out     = Join-Path $AppRoot "src-tauri\worker"
$Lib     = Join-Path $Out "lib"
$Build   = Join-Path $AppRoot "worker-pdfbox\build"
$Cache   = Join-Path $AppRoot ".toolchain\pdfbox-jars"

function Say($m) { Write-Output "[prepare-pdfbox] $m" }

if (-not $Jdk) {
    $javac = Get-Command javac -ErrorAction SilentlyContinue
    if ($javac) { $Jdk = Split-Path -Parent $javac.Source }
    elseif (Test-Path "C:\Program Files\Zulu\zulu-8\bin\javac.exe") { $Jdk = "C:\Program Files\Zulu\zulu-8\bin" }
    else { throw "javac tidak ditemukan; berikan -Jdk <folder bin JDK 8+>" }
}

New-Item -ItemType Directory -Force $Lib, $Build, $Cache | Out-Null

function Resolve-Jar([string]$name) {
    $info = $Pinned[$name]
    $candidates = @((Join-Path $Src $name), (Join-Path $Cache $name))
    if (-not $ForceDownload) {
        foreach ($c in $candidates) {
            if (Test-Path $c) {
                $h = (Get-FileHash $c -Algorithm SHA256).Hash.ToLower()
                if ($h -eq $info.sha) { return $c }
                Say "hash tidak cocok, mengunduh ulang: $name"
            }
        }
    }
    # Unduh dari Maven Central (sumber resmi) lalu verifikasi hash.
    $tmp = Join-Path $Cache "$name.part"
    Say "mengunduh $name dari Maven Central"
    curl.exe -sSfL --max-time 300 -o $tmp $info.url
    if ($LASTEXITCODE -ne 0) { throw "gagal mengunduh $name (curl exit $LASTEXITCODE)" }
    $h = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $info.sha) { Remove-Item $tmp -Force; throw "sha256 $name tidak cocok (dapat $h)" }
    Move-Item $tmp (Join-Path $Cache $name) -Force
    return (Join-Path $Cache $name)
}

foreach ($name in $Pinned.Keys) {
    $jar = Resolve-Jar $name
    Copy-Item $jar (Join-Path $Lib $name) -Force
}

Get-ChildItem $Build -Recurse -File -ErrorAction SilentlyContinue | Remove-Item -Force
$sources = Get-ChildItem (Join-Path $AppRoot "worker-pdfbox\src") -Recurse -Filter *.java | ForEach-Object { $_.FullName }
& (Join-Path $Jdk "javac.exe") -encoding UTF-8 -Xlint:-options -source 8 -target 8 -cp "$Lib\*" -d $Build @sources
if ($LASTEXITCODE -ne 0) { throw "kompilasi worker gagal" }

$manifest = Join-Path $Build "MANIFEST.MF"
$cp = ($Pinned.Keys | ForEach-Object { "lib/$_" }) -join " "
[IO.File]::WriteAllText($manifest, "Main-Class: org.unionpdf.worker.Main`r`nClass-Path: $cp`r`n`r`n", [Text.UTF8Encoding]::new($false))
& (Join-Path $Jdk "jar.exe") cfm (Join-Path $Out "unionpdf-worker.jar") $manifest -C $Build org
if ($LASTEXITCODE -ne 0) { throw "pembuatan JAR gagal" }
Say "siap: $Out\unionpdf-worker.jar (+ $($Pinned.Count) JAR di lib\)"
