# Builds a self-contained Java runtime for the UnionPDF PDFBox worker (no external Java needed).
#
# Steps:
#   1. A JDK 17 LTS (Temurin) is downloaded into .toolchain/ (workspace only, no global install).
#   2. jdeps analyses the worker jar and the PDFBox jars for the required JDK modules.
#   3. jlink creates a trimmed runtime image in src-tauri/worker/jre.
#   4. The worker is started with that runtime to prove the image is sufficient.
#
# Result: src-tauri/worker/jre (gitignored) - shipped with the package.
param(
    [switch]$SkipDownload,
    [switch]$KeepDebugInfo
)
$ErrorActionPreference = "Stop"

$AppRoot = Split-Path -Parent $PSScriptRoot
$Toolchain = Join-Path $AppRoot ".toolchain"
$Zip = Join-Path $Toolchain "temurin17.zip"
$JdkDir = Join-Path $Toolchain "jdk17"
$Worker = Join-Path $AppRoot "src-tauri\worker"
$Jre = Join-Path $Worker "jre"
$Url = "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"

function Say($m) { Write-Output "[prepare-java] $m" }

# ---------------------------------------------------------------- 1. toolchain
if (-not $SkipDownload -and -not (Test-Path $Zip)) {
    New-Item -ItemType Directory -Force $Toolchain | Out-Null
    Say "mengunduh Temurin JDK 17 (LTS) ke workspace..."
    curl.exe -sSL --max-time 1800 -o $Zip $Url
    if ($LASTEXITCODE -ne 0) { throw "gagal mengunduh JDK (curl exit $LASTEXITCODE)" }
}
if (-not (Test-Path $Zip)) { throw "JDK zip tidak ditemukan: $Zip" }
Say ("JDK zip: {0:N1} MB, sha256 {1}" -f ((Get-Item $Zip).Length / 1MB), (Get-FileHash $Zip -Algorithm SHA256).Hash.ToLower())

if (-not (Test-Path $JdkDir)) {
    Say "mengekstrak JDK..."
    $tmp = Join-Path $Toolchain "jdk-extract"
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $tmp | Out-Null
    Expand-Archive -Path $Zip -DestinationPath $tmp -Force
    $root = Get-ChildItem $tmp -Directory | Select-Object -First 1
    Move-Item $root.FullName $JdkDir
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
$jlink = Join-Path $JdkDir "bin\jlink.exe"
$jdeps = Join-Path $JdkDir "bin\jdeps.exe"
if (-not (Test-Path $jlink)) { throw "jlink tidak ditemukan di $jlink" }
$javaVersion = "unknown"
$prevPref = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $javaVersion = ((& (Join-Path $JdkDir "bin\java.exe") -version 2>&1) | Out-String).Trim().Split("`n")[0]
} finally { $ErrorActionPreference = $prevPref }
Say ("JDK: {0} ({1})" -f $javaVersion.Trim(), $JdkDir)

# ---------------------------------------------------------------- 2. module analysis
$jars = @()
$jars += (Join-Path $Worker "unionpdf-worker.jar")
$libJars = @(Get-ChildItem (Join-Path $Worker "lib") -Filter *.jar -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
$jars += $libJars
if (-not (Test-Path $jars[0])) { throw "worker jar belum ada: $($jars[0]) (jalankan prepare-pdfbox.ps1)" }
$libCp = (Join-Path $Worker "lib")
Say "menganalisis dependency modul dengan jdeps (classpath: $libCp)..."
$depsOut = @()
$prevPref2 = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $depsOut = @(& $jdeps --print-module-deps --ignore-missing-deps --multi-release 17 --class-path $libCp $jars 2>&1)
} finally { $ErrorActionPreference = $prevPref2 }
$depsOut | Where-Object { $_ -match "not found" } | Select-Object -First 3 | ForEach-Object { Say "jdeps: $_" }
$moduleLine = ($depsOut | Where-Object { ($_ -is [string]) -and ($_ -match "^[a-z][\w\.]*(,[a-z][\w\.]*)*$") -and ($_ -notmatch "not found") } | Select-Object -Last 1)
if (-not $moduleLine) {
    Say "jdeps tidak menghasilkan daftar modul; memakai daftar konservatif."
    $moduleLine = "java.base,java.desktop,java.logging,java.xml"
}
$staticModules = ($moduleLine -split ",") | Sort-Object -Unique
Say "modul statis: $($staticModules -join ',')"

# Modul yang selalu dibutuhkan worker (font, imaging, XML, kriptografi, logging).
$extra = @("java.base", "java.desktop", "java.logging", "java.xml", "java.security.jgss", "jdk.crypto.ec", "jdk.crypto.cryptoki", "java.sql", "java.naming", "java.management", "jdk.unsupported", "java.instrument", "jdk.zipfs", "jdk.localedata")
$modules = @()
foreach ($m in ($staticModules + $extra)) {
    if ($m -and ($modules -notcontains $m)) { $modules += $m }
}
# Buang modul yang tidak ada di JDK ini.
$prevPref3 = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $available = @((& (Join-Path $JdkDir "bin\java.exe") --list-modules 2>$null) | ForEach-Object { (($_ -split "@")[0]).Trim() } | Where-Object { $_ })
} finally { $ErrorActionPreference = $prevPref3 }
Say ("modul tersedia di JDK: {0}" -f $available.Count)
$modules = @($modules | Where-Object { $available -contains $_ })
if ($modules.Count -eq 0) { throw "tidak ada modul yang bisa dipakai" }
Say "modul untuk runtime: $($modules -join ',')"

# ---------------------------------------------------------------- 3. jlink
Remove-Item $Jre -Recurse -Force -ErrorAction SilentlyContinue
$jlinkArgs = @("--add-modules", ($modules -join ","), "--output", $Jre, "--strip-debug", "--no-header-files", "--no-man-pages", "--compress=2")
if (-not $KeepDebugInfo) { }
Say "jlink membuat runtime image..."
& $jlink @jlinkArgs
if ($LASTEXITCODE -ne 0) { throw "jlink gagal (exit $LASTEXITCODE)" }
$size = (Get-ChildItem $Jre -Recurse -File | Measure-Object Length -Sum).Sum
Say ("runtime image: {0:N1} MB di {1}" -f ($size / 1MB), $Jre)

# ---------------------------------------------------------------- 4. smoke test
$javaExe = Join-Path $Jre "bin\java.exe"
if (-not (Test-Path $javaExe)) { throw "java.exe tidak ada di runtime image" }
$req = '{"id":"1","op":"ping"}' + "`n" + '{"id":"2","op":"shutdown"}'
$out = $req | & $javaExe "-Dfile.encoding=UTF-8" "-Djava.awt.headless=true" -jar (Join-Path $Worker "unionpdf-worker.jar") 2>&1
Say "smoke test worker dengan runtime bawaan:"
$out | ForEach-Object { Say "  $_" }
if (($out -join "`n") -notmatch '"type":"ready"') { throw "worker tidak berjalan dengan runtime bawaan" }
Say "OK: worker berjalan dengan runtime Java bawaan (tanpa Java eksternal)."
