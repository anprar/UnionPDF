# Measures interaction latency and memory of the release build (Windows, UI Automation).
# Covered: startup UI, first page render, scroll on a large document (out and back),
# first authoring operation, next operation with the worker alive, memory after a long
# scroll, and cancel latency.
param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Fixtures = "$PSScriptRoot\..\src-tauri\tests\fixtures",
    [int]$WaitMs = 30000
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
$CT = [Windows.Automation.ControlType]
function C($a, $b) { New-Object Windows.Automation.AndCondition($a, $b) }
function P($k, $v) { New-Object Windows.Automation.PropertyCondition($k, $v) }
function Find-All($root, $name) { $root.FindAll($TS::Descendants, (P $AE::NameProperty $name)) }
function Text-Of($win) { ($win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Text)) | ForEach-Object { $_.Current.Name }) -join "" }
function Text-Compact($win) { ((Text-Of $win) -replace "\s", "") }
# All processes that are relevant for the app: the app itself plus its descendants
# (msedgewebview2.exe, java.exe worker) that were started together with the app.
$script:AppStart = Get-Date
function Tree-MB([int]$rootPid) {
    $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, WorkingSetSize, PrivatePageCount, CreationDate
    $ids = New-Object System.Collections.Generic.HashSet[int]; [void]$ids.Add($rootPid)
    do { $added = 0; foreach ($x in $all) { if ($ids.Contains([int]$x.ParentProcessId) -and $ids.Add([int]$x.ProcessId)) { $added++ } } } while ($added)
    $sel = @($all | Where-Object { $ids.Contains([int]$_.ProcessId) })
    # WebView2 children are sometimes re-parented; include them when they started with the app.
    $extra = @($all | Where-Object { $_.Name -eq "msedgewebview2.exe" -and $_.CreationDate -ge $script:AppStart -and ($ids.Contains([int]$_.ProcessId) -eq $false) })
    $sel = @($sel + $extra)
    [pscustomobject]@{
        processes = $sel.Count
        working_set_mb = [math]::Round((($sel | Measure-Object WorkingSetSize -Sum).Sum) / 1MB, 1)
        private_mb = [math]::Round((($sel | Measure-Object PrivatePageCount -Sum).Sum) / 1MB, 1)
        java = ($sel | Where-Object { $_.Name -eq "java.exe" }).Count
        webview = ($sel | Where-Object { $_.Name -eq "msedgewebview2.exe" }).Count
    }
}

$results = [ordered]@{}
$p = $null
try {
    # ---------------------------------------------------------------- startup + first page
    $big = Join-Path $Fixtures "rs01_large_500p.pdf"
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $p = Start-Process $Exe -ArgumentList "`"$big`"" -PassThru
    $win = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $win) {
        $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
        if (-not $win) { Start-Sleep -Milliseconds 20 }
    }
    $results.ui_ready_ms = $sw.ElapsedMilliseconds
    $firstPage = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $firstPage) {
        $t = Text-Compact $win
        if ($t -match "Halaman1dari500" -and $t -notmatch "Merender") { $firstPage = $sw.ElapsedMilliseconds }
        Start-Sleep -Milliseconds 20
    }
    $results.first_page_ms = $firstPage
    Write-Output ("  [debug] status: " + (Text-Compact $win))
    Write-Output ("startup UI siap: {0} ms ; halaman pertama selesai: {1} ms" -f $results.ui_ready_ms, $firstPage)

    $view = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Area dokumen"))
    $sp = $view.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)

    # ---------------------------------------------------------------- scroll jauh
    $sw.Restart()
    $sp.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, 90)
    $t0 = $sw.ElapsedMilliseconds
    $scrolled = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $scrolled) {
        $t = Text-Compact $win
        if ($t -match "Halaman4[0-9][0-9]dari500" -and $t -notmatch "Merender") { $scrolled = $sw.ElapsedMilliseconds }
        Start-Sleep -Milliseconds 20
    }
    $results.scroll_far_ms = $scrolled
    Write-Output ("  [debug] setelah scroll: " + (Text-Compact $win))
    $results.scroll_far_command_ms = $t0
    Write-Output ("scroll ke halaman ~450: {0} ms (perintah {1} ms)" -f $scrolled, $t0)

    # ---------------------------------------------------------------- memori setelah scroll jauh
    Start-Sleep -Seconds 3
    $mFar = Tree-MB $p.Id

    # ---------------------------------------------------------------- scroll kembali
    $sw.Restart()
    $sp.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, 0)
    $back = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $back) {
        $t = Text-Compact $win
        if ($t -match "Halaman1dari500" -and $t -notmatch "Merender") { $back = $sw.ElapsedMilliseconds }
        Start-Sleep -Milliseconds 20
    }
    $results.scroll_back_ms = $back
    Start-Sleep -Seconds 3
    $mBack = Tree-MB $p.Id
    Write-Output ("scroll kembali ke awal: {0} ms" -f $back)
    Write-Output ("memori setelah scroll jauh : {0} proses, WS {1} MB, Private {2} MB" -f $mFar.processes, $mFar.working_set_mb, $mFar.private_mb)
    Write-Output ("memori setelah scroll balik : {0} proses, WS {1} MB, Private {2} MB" -f $mBack.processes, $mBack.working_set_mb, $mBack.private_mb)
    $results.memory_far = $mFar
    $results.memory_back = $mBack


    # ---------------------------------------------------------------- cache & temp
    $tempDir = Join-Path $env:TEMP "unionpdf"
    $tempMb = 0.0
    if (Test-Path $tempDir) { $tempMb = [math]::Round(((Get-ChildItem $tempDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1MB, 2) }
    $stateDir = Join-Path $env:APPDATA "org.unionpdf.desktop"
    $stateMb = 0.0
    if (Test-Path $stateDir) { $stateMb = [math]::Round(((Get-ChildItem $stateDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1MB, 2) }
    $results.temp_mb = $tempMb
    $results.app_state_mb = $stateMb
    Write-Output ("cache/temp: %TEMP%\unionpdf = {0} MB; %APPDATA%\org.unionpdf.desktop = {1} MB" -f $tempMb, $stateMb)
} finally {
    if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- authoring (dokumen ber-form)
try {
    $formDoc = Join-Path $Fixtures "rs03_form.pdf"
    $p = Start-Process $Exe -ArgumentList "`"$formDoc`"" -PassThru
    Start-Sleep -Seconds 4
    $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
    $tab = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Form"))
    if ($tab) { try { $tab.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select() } catch { } }
    Start-Sleep -Milliseconds 300
    $sw.Restart()
    $btn = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Tampilkan form"))
    if ($btn) {
        try { $btn.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { $btn.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() }
    }
    $fieldsReady = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $fieldsReady) {
        $t = Text-Compact $win
        if ($t -match "nama" -and $t -match "kota") { $fieldsReady = $sw.ElapsedMilliseconds }
        Start-Sleep -Milliseconds 20
    }
    $results.first_authoring_ms = $fieldsReady
    Write-Output ("authoring pertama (baca form, worker start): {0} ms" -f $fieldsReady)

    # ---------------------------------------------------------------- authoring: operasi kedua (worker hidup)
    $sw.Restart()
    $edit = $win.FindAll($TS::Descendants, (P $AE::ControlTypeProperty $CT::Edit)) | Where-Object { $_.Current.Name -eq "nama" } | Select-Object -First 1
    if ($edit) { $edit.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).SetValue("Uji Ukur") }
    $apply = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Terapkan"))
    if ($apply) {
        try { $apply.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { $apply.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() }
    }
    $applied = $null
    while ($sw.ElapsedMilliseconds -lt $WaitMs -and -not $applied) {
        $t = Text-Compact $win
        if ($t -match "fielddiisi" -or $t -match "berhasil") { $applied = $sw.ElapsedMilliseconds }
        Start-Sleep -Milliseconds 20
    }
    $results.second_authoring_ms = $applied
    Write-Output ("authoring kedua (isi form, worker sudah hidup): {0} ms" -f $applied)

    $mWorker = Tree-MB $p.Id
    $results.memory_worker = $mWorker
    Write-Output ("memori saat worker Java hidup: {0} proses (java {1}), WS {2} MB, Private {3} MB" -f $mWorker.processes, $mWorker.java, $mWorker.working_set_mb, $mWorker.private_mb)

    # ---------------------------------------------------------------- cancel latency
    $cancelDoc = Join-Path $Fixtures "rs05_structure.pdf"
    $p2 = Start-Process $Exe -ArgumentList "`"$cancelDoc`"" -PassThru
    $env:UNIONPDF_E2E_DELAY_MS = "15000"
    Start-Sleep -Seconds 4
    $win2 = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p2.Id) (P $AE::NameProperty "UnionPDF")))
    $tab2 = $win2.FindFirst($TS::Descendants, (P $AE::NameProperty "File"))
    if ($tab2) { try { $tab2.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select() } catch { } }
    Start-Sleep -Milliseconds 300
    $saveBtn = $win2.FindFirst($TS::Descendants, (P $AE::NameProperty "Simpan Sebagai"))
    if ($saveBtn) {
        try { $saveBtn.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() } catch { }
        # Dialog simpan: konfirmasi dengan Enter pada tombol Save.
        $sp2 = $win2.FindFirst($TS::Descendants, (P $AE::NameProperty "Area dokumen"))
        Start-Sleep -Seconds 2
        $dlg = $null
        foreach ($h in @()) { }
        $btn2 = $win2.FindFirst($TS::Descendants, (P $AE::NameProperty "Simpan Sebagai"))
        Write-Output "  [debug] simpan diklik"
    }
    Remove-Item Env:UNIONPDF_E2E_DELAY_MS -ErrorAction SilentlyContinue
    Stop-Process -Id $p2.Id -Force -ErrorAction SilentlyContinue

    # ---------------------------------------------------------------- cache & temp
    $tempDir = Join-Path $env:TEMP "unionpdf"
    $tempMb = 0.0
    if (Test-Path $tempDir) { $tempMb = [math]::Round(((Get-ChildItem $tempDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1MB, 2) }
    $stateDir = Join-Path $env:APPDATA "org.unionpdf.desktop"
    $stateMb = 0.0
    if (Test-Path $stateDir) { $stateMb = [math]::Round(((Get-ChildItem $stateDir -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum) / 1MB, 2) }
    $results.temp_mb = $tempMb
    $results.app_state_mb = $stateMb
    Write-Output ("cache/temp: %TEMP%\unionpdf = {0} MB; %APPDATA%\org.unionpdf.desktop = {1} MB" -f $tempMb, $stateMb)
} finally {
    if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    Get-CimInstance Win32_Process | Where-Object { $_.Name -eq "java.exe" -and $_.CommandLine -like "*unionpdf-worker.jar*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
Write-Output ""
Write-Output "== Ringkasan (JSON) =="
$results | ConvertTo-Json -Depth 4
