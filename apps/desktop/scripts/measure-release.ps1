# Measurement of the local release build of UnionPDF (not an installer).
# Method:
#  - Startup: Stopwatch from Start-Process until (a) UI Automation sees the "Buka" button (UI ready)
#    and, when a PDF is given, (b) the status bar shows "Halaman 1 dari N" and the "Merender" hint
#    is gone (first page rendered). Repeated -Runs times; per-run, median, min, max reported.
#  - Memory: process tree = the app process plus all descendants (msedgewebview2.exe, java.exe when
#    the worker runs), from Win32_Process (WorkingSetSize, PrivatePageCount), sampled after 3 s idle.
#    -WithWorker opens the form panel (starts the PDFBox worker) before sampling.
#  - Sizes: split into the application, the components shipped next to it, and external runtimes.
param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Pdf = "",
    [int]$Runs = 5,
    [switch]$WithWorker
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
$CT = [Windows.Automation.ControlType]
function PCond($k, $v) { New-Object Windows.Automation.PropertyCondition($k, $v) }

function Tree([int]$rootPid) {
    $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, WorkingSetSize, PrivatePageCount
    $ids = New-Object System.Collections.Generic.HashSet[int]
    [void]$ids.Add($rootPid)
    do {
        $added = 0
        foreach ($p in $all) { if ($ids.Contains([int]$p.ParentProcessId) -and $ids.Add([int]$p.ProcessId)) { $added++ } }
    } while ($added)
    $all | Where-Object { $ids.Contains([int]$_.ProcessId) }
}
function MB($b) { [math]::Round($b / 1MB, 1) }

$times = @()
$mem = $null
for ($r = 1; $r -le $Runs; $r++) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = if ($Pdf) { Start-Process $Exe -ArgumentList "`"$Pdf`"" -PassThru } else { Start-Process $Exe -PassThru }
    try {
        $win = $null
        $uiReady = $null
        $rendered = $null
        while ($sw.ElapsedMilliseconds -lt 30000) {
            if (-not $win) {
                $win = $AE::RootElement.FindFirst($TS::Children, (New-Object Windows.Automation.AndCondition((PCond $AE::ProcessIdProperty $p.Id), (PCond $AE::NameProperty "UnionPDF"))))
            }
            if ($win -and -not $uiReady -and $win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Buka"))) {
                $uiReady = $sw.ElapsedMilliseconds
                if (-not $Pdf) { break }
            }
            if ($uiReady -and $Pdf) {
                $t = (($win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join "") -replace "\s", ""
                if ($t -match "Halaman1dari\d+" -and -not $t.Contains("Merender")) { $rendered = $sw.ElapsedMilliseconds; break }
            }
            Start-Sleep -Milliseconds 20
        }
        $times += [pscustomobject]@{ run = $r; ui_ready_ms = $uiReady; first_page_ms = $rendered }
        if ($r -eq $Runs) {
            if ($WithWorker) {
                $b = $win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Isi Form"))
                if ($b) {
                    try { $b.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { try { $b.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() } catch { } }
                    Start-Sleep 5
                }
            }
            Start-Sleep 3
            $mem = Tree $p.Id
        }
    } finally {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep 1
    }
}

"== Startup (ms) =="
$times | Format-Table -AutoSize | Out-String -Width 200
foreach ($k in "ui_ready_ms", "first_page_ms") {
    $v = @($times | ForEach-Object { $_.$k } | Where-Object { $_ } | Sort-Object)
    if ($v.Count) {
        "{0}: median={1} min={2} max={3} (n={4})" -f $k, $v[[int][math]::Floor(($v.Count - 1) / 2)], $v[0], $v[-1], $v.Count
    } else {
        "{0}: NOT_MEASURED" -f $k
    }
}
"== Process tree (last run, after idle) =="
$mem | Sort-Object Name | ForEach-Object { "{0,-24} pid={1,-6} WS={2,7} MB  Private={3,7} MB" -f $_.Name, $_.ProcessId, (MB $_.WorkingSetSize), (MB ($_.PrivatePageCount)) }
"TOTAL: {0} processes, WorkingSet sum={1} MB, Private sum={2} MB (WorkingSet shares pages between processes, so the sum is an upper bound)" -f @($mem).Count, (MB ($mem | Measure-Object WorkingSetSize -Sum).Sum), (MB ($mem | Measure-Object PrivatePageCount -Sum).Sum)

"== Sizes on disk =="
$rel = Split-Path $Exe
"app      unionpdf-desktop.exe  : {0} MB" -f (MB (Get-Item $Exe).Length)
if (Test-Path "$rel\pdfium.dll") { "shipped  pdfium.dll            : {0} MB" -f (MB (Get-Item "$rel\pdfium.dll").Length) }
if (Test-Path "$rel\worker") { "shipped  worker PDFBox (jar+lib): {0} MB" -f (MB (Get-ChildItem "$rel\worker" -Recurse -File | Measure-Object Length -Sum).Sum) }
$java = (Get-Command java -ErrorAction SilentlyContinue).Source
if ($java) {
    $home_ = Split-Path (Split-Path $java)
    $size = (Get-ChildItem $home_ -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
    "external Java (dev only, $home_): {0} MB - NOT shipped with the app" -f (MB $size)
}
$wv = Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" -ErrorAction SilentlyContinue
"OS       WebView2 Runtime      : version {0} (OS component, not counted)" -f $(if ($wv) { $wv.pv } else { "not found in registry" })
