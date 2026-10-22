# Uji: aplikasi UnionPDF harus memakai runtime Java BUNDLE, bukan Java eksternal.
# Environment proses uji dibersihkan (JAVA_HOME dihapus, PATH tanpa Java) - hanya untuk
# proses anak, bukan mengubah PATH/JAVA_HOME global.
param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Python = "$PSScriptRoot\..\..\..\.venv\Scripts\python.exe"
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
$CT = [Windows.Automation.ControlType]
function C($a, $b) { New-Object Windows.Automation.AndCondition($a, $b) }
function P($k, $v) { New-Object Windows.Automation.PropertyCondition($k, $v) }

$fx = Resolve-Path "$PSScriptRoot\..\src-tauri\tests\fixtures\rs03_form.pdf"
$work = Join-Path $env:TEMP "unionpdf-nojava"
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $work | Out-Null
$out = Join-Path $work "hasil.pdf"

# --- environment bersih untuk proses anak ---
$savedJavaHome = $env:JAVA_HOME
$savedPath = $env:PATH
try {
    Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue
    $javaDirs = @($savedPath -split ";" | Where-Object { $_ -and (Test-Path (Join-Path $_ "java.exe")) })
    $env:PATH = (($savedPath -split ";" | Where-Object { $_ -and ($javaDirs -notcontains $_) }) -join ";")
    Write-Output ("PATH ohne Java: {0} folder Java dihapus dari PATH" -f $javaDirs.Count)

    $p = Start-Process $Exe -ArgumentList "`"$fx`"" -PassThru
    try {
        Start-Sleep -Seconds 6
        $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
        if (-not $win) { throw "jendela UnionPDF tidak ditemukan" }
        $text = ($win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join ""
        # Status bar: "Anotasi & form aktif" = worker PDFBox (runtime bundel) siap.
        if ($text -notmatch "Anotasi & form aktif") { throw "worker authoring tidak terdeteksi: $text" }

        # Bukalah panel form -> worker harus start (java.exe dari runtime bundel).
        $tab = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Form"))
        if ($tab) {
            try { $tab.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select() } catch { }
            Start-Sleep -Milliseconds 400
        }
        $btn = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Tampilkan form"))
        if ($btn) {
            try { $btn.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { $btn.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() }
        }
        Start-Sleep -Seconds 6
        $text = ($win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join ""
        foreach ($f in @("nama", "setuju", "pilihan", "kota")) {
            if ($text -notmatch $f) { throw "field '$f' tidak terbaca - worker mungkin gagal start: $text" }
        }
        # Proses java harus berasal dari runtime bundel.
        $javaProcs = Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" }
        if (-not $javaProcs) { throw "proses java worker tidak terlihat" }
        foreach ($jp in $javaProcs) {
            if ($jp.CommandLine -notmatch "jre\\bin\\java" -and $jp.ExecutablePath -notmatch "jre") {
                throw "worker memakai Java eksternal: $($jp.ExecutablePath)"
            }
        }
        Write-Output ("OK: worker berjalan dengan runtime bundel ({0}); tanpa Java eksternal." -f $javaProcs[0].ExecutablePath)
        Write-Output "  field form terbaca: nama, setuju, pilihan, kota"
    } finally {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    }
} finally {
    if ($savedJavaHome) { $env:JAVA_HOME = $savedJavaHome } else { Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue }
    $env:PATH = $savedPath
}
