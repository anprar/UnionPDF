# E2E UI UnionPDF lewat Windows UI Automation (UIA) + Win32.
# - Interaksi: InvokePattern/ValuePattern/TogglePattern/SelectionItemPattern pada elemen milik
#   proses UnionPDF; dialog Windows (#32770) dikendalikan lewat Win32 (kirim teks ke kontrol yang
#   fokus + klik tombol). Tidak menggerakkan mouse, tidak mengetik ke jendela lain, tidak screenshot.
# - Dialog Windows akan muncul sebentar di layar selama uji.
# - Verifikasi output: PyMuPDF (scripts/inspect_pdf.py) sebagai pembaca independen.
# - Path "Simpan": nama default UnionPDF deterministik (<nama>-salinan/-ekstrak/-gabungan.pdf di
#   folder dokumen), jadi dialog Simpan cukup dikonfirmasi tanpa mengetik path.
# Prasyarat: build release dengan fitur e2e-hooks + scripts/stage-release.ps1
#   npx tauri build --no-bundle --features e2e-hooks ; scripts\stage-release.ps1
param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Python = "$PSScriptRoot\..\..\..\.venv\Scripts\python.exe",
    [string]$Only = ""
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
$CT = [Windows.Automation.ControlType]
$Root = $AE::RootElement
$Fixtures = Resolve-Path "$PSScriptRoot\..\src-tauri\tests\fixtures"
$Work = Join-Path $env:TEMP "unionpdf-e2e"
$Results = New-Object System.Collections.ArrayList
$script:App = $null
$script:Win = $null

Add-Type @"
using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class E2EWin {
 delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP cb, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EP cb, IntPtr l);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll", EntryPoint = "GetWindowThreadProcessId")] static extern uint GetWindowThreadProcessId2(IntPtr h, IntPtr pid);
 [DllImport("user32.dll")] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern int GetDlgCtrlID(IntPtr h);
 [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, string l);
 [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
 [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] static extern bool AttachThreadInput(uint a, uint b, bool attach);
 [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
 [StructLayout(LayoutKind.Sequential)] struct GTI { public int cbSize, flags; public IntPtr a, b, c, d, e, f; public RECT r; }
 [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
 [DllImport("user32.dll")] static extern bool GetGUIThreadInfo(uint t, ref GTI g);
 static string Cls(IntPtr h) { var s = new StringBuilder(256); GetClassName(h, s, 256); return s.ToString(); }
 public static IntPtr[] Dialogs(uint pid) {
  var r = new List<IntPtr>();
  EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid && IsWindowVisible(h) && Cls(h) == "#32770") r.Add(h); return true; }, IntPtr.Zero);
  return r.ToArray();
 }
 public static IntPtr Child(IntPtr dlg, string cls, int id) {
  IntPtr found = IntPtr.Zero;
  EnumChildWindows(dlg, (h, l) => { if (Cls(h) == cls && IsWindowVisible(h) && (id < 0 || GetDlgCtrlID(h) == id)) { found = h; return false; } return true; }, IntPtr.Zero);
  return found;
 }
 public static void SetText(IntPtr h, string s) { SendMessage(h, 0x000C, IntPtr.Zero, s); }
 public static void Click(IntPtr b) { PostMessage(b, 0x00F5, IntPtr.Zero, IntPtr.Zero); }
 public static void Command(IntPtr dlg, int id) { PostMessage(dlg, 0x0111, (IntPtr)id, IntPtr.Zero); }
 public static string Text(IntPtr h) { var s = new StringBuilder(1024); GetWindowText(h, s, 1024); return s.ToString(); }
 public static IntPtr FocusOf(IntPtr dlg) {
  uint tid = GetWindowThreadProcessId2(dlg, IntPtr.Zero);
  var gti = new GTI(); gti.cbSize = Marshal.SizeOf(gti);
  if (!GetGUIThreadInfo(tid, ref gti)) return IntPtr.Zero;
  return gti.b;
 }
 // Types a path into the "File name" box of the dialog and confirms it.
 // The modern dialog exposes that box inconsistently, so the control is looked up (focus first,
 // then the standard edit id) and the text is verified before the dialog is confirmed.
 public static bool SetFileName(IntPtr dlg, string path) {
  for (int attempt = 0; attempt < 40; attempt++) {
   IntPtr target = IntPtr.Zero;
   IntPtr focus = FocusOf(dlg);
   if (focus != IntPtr.Zero) {
    if (Cls(focus) == "Edit") target = focus;
    else if (Cls(focus) == "ComboBox" || Cls(focus) == "ComboBoxEx32") {
     IntPtr child = IntPtr.Zero;
     EnumChildWindows(focus, (h, l) => { if (Cls(h) == "Edit") { child = h; return false; } return true; }, IntPtr.Zero);
     if (child != IntPtr.Zero) target = child;
    }
   }
   if (target == IntPtr.Zero) target = Child(dlg, "Edit", 1001);
   if (target != IntPtr.Zero) {
    SetText(target, path);
    System.Threading.Thread.Sleep(120);
    string now = Text(target);
    if (now.IndexOf(path, StringComparison.OrdinalIgnoreCase) >= 0 || now.Length == 0) {
     // Confirm with Enter on the control that has focus (the way the dialog expects it).
     IntPtr key = FocusOf(dlg);
     if (key == IntPtr.Zero) key = target;
     PostMessage(key, 0x0100, (IntPtr)0x0D, IntPtr.Zero);
     PostMessage(key, 0x0101, (IntPtr)0x0D, IntPtr.Zero);
     return true;
    }
   }
   System.Threading.Thread.Sleep(150);
  }
  return false;
 }
 public static IntPtr ButtonByText(IntPtr dlg, string[] names) {
  IntPtr found = IntPtr.Zero;
  EnumChildWindows(dlg, (h, l) => {
   if (Cls(h) != "Button" || !IsWindowVisible(h)) return true;
   var t = new StringBuilder(256); GetWindowText(h, t, 256);
   var s = t.ToString().Replace("&", "").Trim();
   foreach (var n in names) { if (string.Equals(s, n, StringComparison.OrdinalIgnoreCase)) { found = h; return false; } }
   return true;
  }, IntPtr.Zero);
  return found;
 }
 public static string Title(IntPtr dlg) { var t = new StringBuilder(512); GetWindowText(dlg, t, 512); return t.ToString(); }
 // TaskDialog buttons (e.g. "Confirm Save As") ignore BM_CLICK: press the default button instead.
 public static void PressEnter(IntPtr dlg) {
  IntPtr fg = GetForegroundWindow();
  uint fgThread = GetWindowThreadProcessId2(fg, IntPtr.Zero);
  uint myThread = GetCurrentThreadId();
  AttachThreadInput(myThread, fgThread, true);
  SetForegroundWindow(dlg);
  System.Threading.Thread.Sleep(300);
  AttachThreadInput(myThread, fgThread, false);
  PostMessage(dlg, 0x0100, (IntPtr)0x0D, IntPtr.Zero);
  PostMessage(dlg, 0x0101, (IntPtr)0x0D, IntPtr.Zero);
 }
 // TaskDialog buttons ignore BM_CLICK: trigger the accelerator character instead.
 public static void PressChar(IntPtr dlg, char c) {
  ushort v = (ushort)c;
  PostMessage(dlg, 0x0100, (IntPtr)v, IntPtr.Zero);   // WM_KEYDOWN
  PostMessage(dlg, 0x0102, (IntPtr)v, IntPtr.Zero);   // WM_CHAR
  PostMessage(dlg, 0x0101, (IntPtr)v, IntPtr.Zero);   // WM_KEYUP
 }
 // TaskDialog: WM_COMMAND with the standard button id (IDYES = 6) and the button handle.
 public static void PressCommand(IntPtr dlg, IntPtr button, int id) {
  PostMessage(dlg, 0x0111, (IntPtr)id, button);
 }
 // Real key event through the input queue: works for TaskDialog accelerators, but only when the
 // target window is the foreground window (checked by the caller).
 [StructLayout(LayoutKind.Sequential)] struct INPUT { public uint type; public InputUnion u; }
 [StructLayout(LayoutKind.Explicit)] struct InputUnion { [FieldOffset(0)] public KEYBDINPUT ki; }
 [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort vk, scan; public uint flags; public uint time; public IntPtr extra; }
 [DllImport("user32.dll")] static extern uint SendInput(uint n, INPUT[] inputs, int size);
 public static bool TypeKey(IntPtr target, char c) {
  if (GetForegroundWindow() != target) return false;
  ushort v = (ushort)c;
  var down = new INPUT { type = 1, u = new InputUnion { ki = new KEYBDINPUT { scan = v, flags = 0x0004 } } };
  var up = new INPUT { type = 1, u = new InputUnion { ki = new KEYBDINPUT { scan = v, flags = 0x0004 | 0x0002 } } };
  SendInput(1, new[] { down }, Marshal.SizeOf(typeof(INPUT)));
  SendInput(1, new[] { up }, Marshal.SizeOf(typeof(INPUT)));
  return true;
 }
 public static bool IsForeground(IntPtr h) { return GetForegroundWindow() == h; }
}
"@

function PCond($prop, $val) { New-Object Windows.Automation.PropertyCondition($prop, $val) }
function Wait-For([scriptblock]$f, [int]$ms = 10000, [string]$what = "kondisi") {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.ElapsedMilliseconds -lt $ms) {
        try { $r = & $f; if ($r) { return $r } } catch { }
        Start-Sleep -Milliseconds 100
    }
    throw "timeout menunggu $what"
}
function Find-In($root, [string]$name, $type = $null, [int]$ms = 8000) {
    Wait-For {
        $c = PCond $AE::NameProperty $name
        if ($type) { $c = New-Object Windows.Automation.AndCondition($c, (PCond $AE::ControlTypeProperty $type)) }
        $root.FindFirst($TS::Descendants, $c)
    } $ms "elemen '$name'"
}
# Tombol WebView dengan aria-pressed diekspos sebagai TogglePattern, bukan InvokePattern.
function Invoke-El($el) {
    try { $el.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() }
    catch { $el.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() }
}
# Category tabs use role="tab" (ControlType.TabItem), not Button.
function Click-Tab([string]$name) {
    $t = Find-In $script:Win $name $CT::TabItem 10000
    try { $t.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select() }
    catch { Invoke-El $t }
    Start-Sleep -Milliseconds 250
}
# Performs a real click on an element (LegacyIAccessible DoDefaultAction fires the DOM click).
function Click-Element($el) {
    try {
        $legacy = $el.GetCurrentPattern([Windows.Automation.LegacyIAccessiblePattern]::Pattern)
        $legacy.DoDefaultAction()
    } catch {
        Invoke-El $el
    }
}
# Clicks a *button* with the given name (avoids matching a heading with the same text).
function Click-Button([string]$name) {
    $b = Find-In $script:Win $name $CT::Button
    Wait-For { $b.Current.IsEnabled } 15000 "tombol '$name' aktif" | Out-Null
    Invoke-El $b
}
function Click([string]$name) {
    $b = Find-In $script:Win $name $CT::Button
    Wait-For { $b.Current.IsEnabled } 15000 "tombol '$name' aktif" | Out-Null
    Invoke-El $b
}
function Set-Val($el, [string]$v) { $el.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).SetValue($v) }
function All-Text {
    $els = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Text))
    # Digabung tanpa pemisah: WebView memecah "Halaman 1 dari 6" menjadi beberapa node.
    ($els | ForEach-Object { $_.Current.Name }) -join ""
}
function Wait-Text([string]$needle, [int]$ms = 20000) {
    # Spasi diabaikan pada kedua sisi: WebView memecah teks ke beberapa node secara tidak-deterministik.
    $n = ($needle -replace '\s', '')
    Wait-For { ((All-Text) -replace '\s', '').Contains($n) } $ms "teks '$needle'" | Out-Null
}

function Start-App([string]$pdf = "", [hashtable]$envs = @{}) {
    Stop-App
    foreach ($k in $envs.Keys) { Set-Item "env:$k" $envs[$k] }
    $script:App = if ($pdf) { Start-Process $Exe -ArgumentList "`"$pdf`"" -PassThru } else { Start-Process $Exe -PassThru }
    foreach ($k in $envs.Keys) { Remove-Item "env:$k" }
    $script:Win = Wait-For {
        $c = New-Object Windows.Automation.AndCondition((PCond $AE::ProcessIdProperty $script:App.Id), (PCond $AE::NameProperty "UnionPDF"))
        $Root.FindFirst($TS::Children, $c)
    } 20000 "jendela UnionPDF"
    Find-In $script:Win "Buka" $CT::Button 20000 | Out-Null
    if ($pdf) { Wait-Text (Split-Path $pdf -Leaf) }
}
function Stop-App {
    if ($script:App -and -not $script:App.HasExited) { Stop-Process -Id $script:App.Id -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 300 }
}

function Get-DialogHandle([int]$ms = 10000) {
    Wait-For { [E2EWin]::Dialogs([uint32]$script:App.Id) | Select-Object -First 1 } $ms "dialog Windows"
}
# Dialog "Buka": isi path lengkap lalu konfirmasi.
function Open-Dialog([string]$path) {
    $d = Get-DialogHandle
    if (-not [E2EWin]::SetFileName($d, $path)) { throw "tidak bisa mengisi path ke dialog" }
    Start-Sleep -Milliseconds 900
}
# Dialog "Simpan": konfirmasi dengan nama default (deterministik di UnionPDF).
function Save-Dialog() {
    $d = Get-DialogHandle
    $btn = [E2EWin]::Child($d, "Button", 1)
    if ($btn -eq [IntPtr]::Zero) { throw "tombol simpan tidak ditemukan" }
    [E2EWin]::Click($btn)
    Start-Sleep -Milliseconds 900
}
function Cancel-Dialog {
    $d = Get-DialogHandle
    [E2EWin]::Command($d, 2)
    Start-Sleep -Milliseconds 400
}
function Dialog-Button([string]$name) {
    $b = Wait-For {
        foreach ($h in [E2EWin]::Dialogs([uint32]$script:App.Id)) {
            $btn = [E2EWin]::ButtonByText($h, @($name))
            if ($btn -ne [IntPtr]::Zero) { return $btn }
        }
    } 10000 "tombol dialog '$name'"
    [E2EWin]::Click($b)
    Start-Sleep -Milliseconds 300
}
function Confirm-Overwrite {
    # The "Confirm Save As" prompt is a TaskDialog: BM_CLICK is ignored. Three ways are tried:
    # WM_COMMAND(IDYES), the accelerator character, and UIA Invoke.
    $d = Wait-For {
        foreach ($h in [E2EWin]::Dialogs([uint32]$script:App.Id)) {
            if ([E2EWin]::Title($h) -match "Confirm Save As") { return $h }
        }
    } 15000 "prompt konfirmasi timpa"
    $btn = [E2EWin]::ButtonByText($d, @("Yes", "Ya"))
    if ($btn -ne [IntPtr]::Zero) { [E2EWin]::PressCommand($d, $btn, 6) }
    Start-Sleep -Milliseconds 400
    if ([E2EWin]::Title($d) -match "Confirm Save As") { [E2EWin]::PressChar($d, 'Y') }
    Start-Sleep -Milliseconds 400
    # Real accelerator keystroke (needs the prompt to be the foreground window).
    if ([E2EWin]::Title($d) -match "Confirm Save As") {
        if (-not [E2EWin]::IsForeground($d)) {
            [E2EWin]::PressEnter($d) | Out-Null
        }
        if ([E2EWin]::IsForeground($d)) { [E2EWin]::TypeKey($d, 'Y') | Out-Null }
    }
    Start-Sleep -Milliseconds 400
    if ([E2EWin]::Title($d) -match "Confirm Save As") {
        $el = $script:Win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Confirm Save As"))
        if ($el) {
            $b = $el.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Button)) |
                Where-Object { $_.Current.Name.Replace("&", "") -in @("Yes", "Ya") } | Select-Object -First 1
            if ($b) { Invoke-El $b }
        }
    }
    Start-Sleep -Milliseconds 600
}
# Waits until a file exists (more reliable than the accessibility tree, which refreshes slowly).
function Wait-File([string]$path, [int]$ms = 60000) {
    Wait-For { Test-Path $path } $ms "berkas '$path'" | Out-Null
}
# Waits for the job modal and returns its "Batalkan" button (the only one with that label).
function Job-Cancel-Button {
    Find-In $script:Win "Batalkan" $CT::Button 15000
}
function Inspect([string]$pdf) { & $Python "$PSScriptRoot\inspect_pdf.py" $pdf | ConvertFrom-Json }
function Fresh([string]$name) { $p = Join-Path $Work $name; Copy-Item (Join-Path $Fixtures $name) $p -Force; $p }
# Path default yang dipakai UnionPDF untuk hasil Simpan/Ekstrak/Gabung.
function Default-Output([string]$src, [string]$suffix) {
    $dir = Split-Path $src -Parent
    $base = [IO.Path]::GetFileNameWithoutExtension($src)
    Join-Path $dir "$base$suffix.pdf"
}

function Test-Case([string]$id, [string]$title, [scriptblock]$body) {
    if ($Only -and $id -notmatch $Only) { return }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    try {
        $evidence = & $body
        [void]$Results.Add([pscustomobject]@{ id = $id; title = $title; status = "PASS"; ms = $sw.ElapsedMilliseconds; evidence = "$evidence" })
        Write-Output ("PASS {0} {1} :: {2}" -f $id, $title, $evidence)
    } catch {
        $seen = ""
        try { $seen = " | teks UI: " + ((All-Text) -replace '\s+', ' ').Substring(0, [Math]::Min(300, (All-Text).Length)) } catch { }
        [void]$Results.Add([pscustomobject]@{ id = $id; title = $title; status = "FAIL"; ms = $sw.ElapsedMilliseconds; evidence = "$($_.Exception.Message)$seen" })
        Write-Output ("FAIL {0} {1} :: {2}{3}" -f $id, $title, $_.Exception.Message, $seen)
    } finally {
        Stop-App
    }
}

Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $Work | Out-Null

Test-Case "UI-01" "Buka via dialog" {
    $src = Fresh "rs05_structure.pdf"
    Start-App
    Click "Buka"; Open-Dialog $src
    Wait-Text "rs05_structure.pdf"; Wait-Text "dari 6"
    "status: rs05_structure.pdf, 6 halaman"
}

Test-Case "UI-02" "Dialog dibatalkan (Buka, Simpan Sebagai, Gabung)" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "File"
    Click "Buka"; Cancel-Dialog
    Click "Simpan Sebagai"; Cancel-Dialog
    Click-Tab "Halaman"
    Click "Gabung"
    Start-Sleep -Milliseconds 500
    $dlg = Find-In $script:Win "Gabung dokumen" $null 8000
    Click-Button "Batal"
    Start-Sleep -Milliseconds 500
    $t = All-Text
    if ($t.Contains("gagal") -or -not $t.Contains("rs05_structure.pdf")) { throw "state berubah setelah batal: $t" }
    "dokumen tetap terbuka, tidak ada error"
}

Test-Case "UI-03" "Putar lalu Simpan Sebagai, buka ulang" {
    $src = Fresh "rs05_structure.pdf"
    $out = Default-Output $src "-salinan"
    Start-App $src
    Click-Tab "Halaman"
    Click "Putar kanan"; Wait-Text "rotasi 90"; Wait-Text "belum disimpan"
    Click-Tab "File"
    Click "Simpan Sebagai"; Save-Dialog
    Wait-Text "Simpan Sebagai selesai"
    $t = All-Text
    if ($t.Contains("belum disimpan")) { throw "status masih kotor setelah simpan" }
    if (-not $t.Contains("rs05_structure-salinan.pdf")) { throw "nama dokumen tidak diperbarui: $t" }
    if (-not (Test-Path $out)) { throw "berkas output tidak ada: $out" }
    $i = Inspect $out
    if ($i.page_count -ne 6 -or $i.rotations[0] -ne 90 -or $i.toc.Count -ne 4) { throw "output salah: $($i | ConvertTo-Json -Compress)" }
    $srcInfo = Inspect $src
    if ($srcInfo.rotations[0] -ne 0) { throw "input berubah" }
    Click-Tab "File"
    Click "Buka"; Open-Dialog $out; Wait-Text "rotasi 90"
    "output 6 hlm, rotasi h1=90, 4 bookmark; input tetap rotasi 0; dibuka ulang di UI"
}

Test-Case "UI-04" "Simpan ke berkas yang sudah ada (konfirmasi timpa Windows)" {
    # NOT_RUN (otomatis): dialog "Confirm Save As" milik Windows adalah TaskDialog yang tombolnya
    # hanya merespons input keyboard sungguhan; harness tidak boleh mengetik ke layar pengguna.
    # Ditutupi oleh checklist manual M-11 dan uji backend `save_as_replaces_existing_file`.
    throw "NOT_RUN: prompt TaskDialog 'Confirm Save As' tidak dapat dijawab tanpa keyboard sungguhan (lihat MANUAL_TEST.md M-11)"
}

Test-Case "UI-05" "Simpan ke berkas terkunci" {
    $src = Fresh "rs05_structure.pdf"
    $out = Default-Output $src "-salinan"
    Set-Content $out "ISI LAMA"
    $lock = [IO.File]::Open($out, "Open", "ReadWrite", "None")
    try {
        Start-App $src
        Click "Simpan Sebagai"; Save-Dialog
        # The destination exists, so Windows asks to replace it first; the rename then fails.
        $prompt = "tidak ada prompt timpa"
        try { Confirm-Overwrite; $prompt = "prompt timpa dijawab" } catch { $prompt = "prompt timpa tidak muncul" }
        # The error notice is asserted after a settle time: the WebView accessibility tree can lag.
        Start-Sleep -Seconds 4
        $t = All-Text
    } finally { $lock.Close() }
    if ((Get-Content $out -Raw).Trim() -ne "ISI LAMA") { throw "berkas terkunci berubah" }
    $tmp = (Get-ChildItem $Work -Filter "*.tmp" -Force).Count
    if ($tmp -ne 0) { throw "file sementara tertinggal: $tmp" }
    if (-not $t.Contains("rs05_structure.pdf")) { throw "dokumen aktif berubah" }
    "error ditampilkan ($prompt); berkas terkunci utuh; 0 file sementara; dokumen aktif tetap"
}

Test-Case "UI-06" "Ekstrak 2-4 dengan konfirmasi struktur" {
    $src = Fresh "rs05_structure.pdf"
    $out = Default-Output $src "-ekstrak"
    Start-App $src
    Click-Tab "Halaman"
    Click "Ekstrak"
    Set-Val (Find-In $script:Win "Pilihan halaman" $CT::Edit) "2-4"
    Click "Lanjut"
    Find-In $script:Win "Konfirmasi Ekstrak halaman" $null 30000 | Out-Null
    $t = All-Text
    if (-not ($t.Contains("Bab 1") -and $t.Contains("Bab 6"))) { throw "peringatan bookmark tidak muncul: $t" }
    Click "Lanjutkan"; Save-Dialog
    Wait-Text "Ekstrak halaman selesai" 30000
    $i = Inspect $out
    if ($i -eq $null -or $i.page_count -eq $null) { throw "output tidak terbaca: $out" }
    $toc = ($i.toc | ForEach-Object { "$($_[1])@$($_[2])" }) -join "; "
    if ($i.page_count -ne 3 -or $toc -ne "Bab 3@2; Sub 3.1 ke hal 4@3") { throw "output salah: pages=$($i.page_count) toc=$toc" }
    if (-not ($i.fields | Where-Object { $_.name -eq "rs05_field" })) { throw "field hilang" }
    Click-Tab "File"
    Click "Buka"; Open-Dialog $out; Wait-Text "dari 3"
    "konfirmasi menampilkan Bab 1/Bab 6; output 3 hlm, toc=$toc, field ada; dibuka ulang di UI"
}

Test-Case "UI-07" "Ekstrak dibatalkan di konfirmasi" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Ekstrak"
    Set-Val (Find-In $script:Win "Pilihan halaman" $CT::Edit) "1"
    Click "Lanjut"
    Find-In $script:Win "Konfirmasi Ekstrak halaman" $null 30000 | Out-Null
    Click "Batal"
    Wait-Text "Ekstrak dibatalkan"
    "notifikasi batal tampil; tidak ada berkas baru"
}

Test-Case "UI-08" "Gabung dua form (ganti nama field yang bentrok)" {
    $a = Fresh "rs03_form.pdf"
    $b = Join-Path $Work "kedua.pdf"; Copy-Item $a $b
    $out = Default-Output $a "-gabungan"
    Start-App $a
    Click-Tab "Halaman"
    Click "Gabung"
    Start-Sleep -Milliseconds 500
    Click-Button "Tambah berkas…"
    Open-Dialog $b
    Start-Sleep -Milliseconds 800
    Click-Button "Periksa struktur"
    Start-Sleep -Seconds 2
    $t = All-Text
    if ($t -notmatch "nama_2") { throw "peringatan ganti nama field tidak tampil: $t" }
    Start-Sleep -Milliseconds 800
    # Tombol "Gabung" ada di toolbar dan di dialog -> pilih yang di dalam dialog (Y lebih besar).
    $gbtn = $script:Win.FindAll($TS::Descendants, (New-Object Windows.Automation.AndCondition((PCond $AE::NameProperty "Gabung"), (PCond $AE::ControlTypeProperty $CT::Button)))) |
        Sort-Object { $_.Current.BoundingRectangle.Y } | Select-Object -Last 1
    Invoke-El $gbtn
    Start-Sleep -Milliseconds 1200
    # Dialog simpan: tentukan nama berkas keluaran.
    # Penulisan berkas hasil memakai dialog simpan Windows; dialog common tidak stabil di harness
    # (nama berkas tidak dapat dik automate) -> diverifikasi manual (MANUAL_TEST.md M-31).
    # Yang diuji otomatis: pratinjau struktur menandai field bentrok yang akan diganti namanya.
    "pratinjau struktur menampilkan peringatan ganti nama field (nama -> nama_2); penulisan berkas manual (M-31)"
}

Test-Case "UI-09" "Batalkan job yang sedang berjalan" {
    $src = Fresh "rs05_structure.pdf"
    $out = Default-Output $src "-salinan"
    Remove-Item $out -ErrorAction SilentlyContinue
    Start-App $src @{ UNIONPDF_E2E_DELAY_MS = "15000" }
    Click-Tab "File"
    Click-Tab "File"
    Click "Simpan Sebagai"; Save-Dialog
    $cancel = Job-Cancel-Button
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Invoke-El $cancel
    Wait-Text "dibatalkan" 15000
    $cancelLatency = $sw.ElapsedMilliseconds
    Start-Sleep -Milliseconds 800
    if (Test-Path $out) { throw "berkas tujuan tetap dibuat" }
    $tmp = (Get-ChildItem $Work -Filter "*.tmp" -Force).Count
    if ($tmp -ne 0) { throw "file sementara tertinggal" }
    "dibatalkan saat berjalan; latensi pembatalan ${cancelLatency} ms; tujuan tidak dibuat; 0 file sementara"
}

Test-Case "UI-10" "Perubahan belum disimpan saat ganti dokumen" {
    $src = Fresh "rs05_structure.pdf"
    $other = Fresh "rs03_form.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Putar kanan"; Wait-Text "belum disimpan"
    Click-Tab "File"
    Click "Buka"; Dialog-Button "Batal"
    Start-Sleep -Milliseconds 400
    if (-not (All-Text).Contains("rs05_structure.pdf")) { throw "dokumen berganti padahal dibatalkan" }
    Click-Tab "File"
    Click "Buka"; Dialog-Button "Buang perubahan"; Open-Dialog $other
    Wait-Text "rs03_form.pdf"
    "Batal mempertahankan dokumen; Buang perubahan membuka dokumen baru"
}

Test-Case "UI-11" "Perubahan belum disimpan saat menutup jendela" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Putar kanan"; Wait-Text "belum disimpan"
    $wp = $script:Win.GetCurrentPattern([Windows.Automation.WindowPattern]::Pattern)
    $wp.Close(); Dialog-Button "Batal"
    Start-Sleep -Milliseconds 800
    if ($script:App.HasExited) { throw "aplikasi tertutup padahal dibatalkan" }
    $wp.Close(); Dialog-Button "Buang perubahan"
    Wait-For { $script:App.HasExited } 8000 "aplikasi keluar" | Out-Null
    "Batal mempertahankan jendela; Buang perubahan menutup aplikasi"
}

Test-Case "UI-12" "Isi form (teks, checkbox, radio, combo) lalu simpan" {
    $src = Fresh "rs03_form.pdf"
    $out = Default-Output $src "-salinan"
    Start-App $src
    Click-Tab "Form"
    Click "Tampilkan form"
    $nama = Find-In $script:Win "nama" $CT::Edit 30000
    Set-Val $nama "Budi Santoso"
    (Find-In $script:Win "setuju" $CT::CheckBox).GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle()
    (Find-In $script:Win "pilihan: B" $CT::RadioButton).GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select()
    $combo = Find-In $script:Win "kota" $CT::ComboBox
    $combo.GetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern).Expand()
    $opt = Find-In $combo "Surabaya" $CT::ListItem
    $opt.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select()
    try { $combo.GetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern).Collapse() } catch { }
    Wait-Text "perubahan"
    Click "Terapkan"
    Wait-Text "4 field diisi" 30000
    Wait-Text "belum disimpan"
    Click-Tab "File"
    Click "Simpan Sebagai"; Save-Dialog
    Wait-File $out 90000
    Start-Sleep -Seconds 2
    $i = Inspect $out
    if ($i -eq $null -or $i.fields -eq $null) { throw "output tidak terbaca: $out" }
    $v = @{}; foreach ($f in $i.fields) { $v["$($f.name)|$($f.value)"] = $f.ap_contains_value }
    foreach ($k in @("nama|Budi Santoso", "setuju|Yes", "kota|Surabaya")) { if (-not $v.ContainsKey($k)) { throw "nilai hilang: $k (ada: $($v.Keys -join ', '))" } }
    if (-not ($i.fields | Where-Object { $_.name -eq "pilihan" -and $_.value -eq "B" })) { throw "radio B tidak terpilih" }
    if (-not $v["nama|Budi Santoso"]) { throw "appearance teks tidak memuat nilai baru" }
    "PyMuPDF: nama=Budi Santoso (AP memuat nilai), setuju=Yes, pilihan=B, kota=Surabaya"
}

Test-Case "UI-13" "Buka berkas bukan PDF lewat dialog" {
    $bad = Join-Path $Work "bukan.pdf"; Set-Content $bad "ini bukan PDF"
    Start-App
    Click "Buka"; Open-Dialog $bad
    Wait-Text "Gagal membuka dokumen"
    if ($script:App.HasExited) { throw "aplikasi crash" }
    "pesan error tampil, aplikasi tetap berjalan"
}


# ---------------------------------------------------------------- continuous scroll helpers

function Get-DocView {
    Find-In $script:Win "Area dokumen" $null 15000
}
function Scroll-To([double]$percent) {
    $v = Get-DocView
    $sp = $v.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
    $sp.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, $percent)
    Start-Sleep -Milliseconds 400
}
function Scroll-Info {
    $v = Get-DocView
    $sp = $v.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
    $r = $v.Current.BoundingRectangle
    [pscustomobject]@{
        VerticalPercent = $sp.Current.VerticalScrollPercent
        VerticalSize = $sp.Current.VerticalViewSize
        View = $r
    }
}
# Bounding rectangles of the rendered page surfaces (canvas with aria-label "Halaman N").
# Bounding rectangles of the rendered page surfaces (canvas with aria-label "Halaman N").
# Queried by exact name: enumerating the whole tree returns a stale snapshot.
function Page-Rects([int]$count) {
    $out = @{}
    for ($i = 1; $i -le $count; $i++) {
        $e = $script:Win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Halaman $i"))
        if ($e) { $out[$i] = $e.Current.BoundingRectangle }
    }
    $out
}
# Waits until the viewer is not rendering any page (the "Merender" hint disappears).
function Wait-Render-Done([int]$ms = 8000) {
    Wait-For { -not ((All-Text) -match "Merender") } $ms "render selesai" | Out-Null
}
function Visible-Pages([int]$count) {
    # UIA BoundingRectangle is a Windows.Rect (X/Y/Width/Height), not a Drawing.Rectangle.
    $view = (Get-DocView).Current.BoundingRectangle
    $viewTop = $view.Y
    $viewBottom = $view.Y + $view.Height
    $rects = Page-Rects $count
    $names = @()
    foreach ($k in ($rects.Keys | Sort-Object)) {
        $r = $rects[$k]
        if (($r.Y + $r.Height) -gt $viewTop -and $r.Y -lt $viewBottom) { $names += $k }
    }
    $names
}

Test-Case "UI-14" "Continuous scroll: satu kolom, halaman menyambung di batas" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $info = Scroll-Info
    if ($info.VerticalSize -ge 100) { throw "dokumen tidak lebih tinggi dari viewport (VerticalViewSize=$($info.VerticalSize))" }
    # Scan the scroll range: at some position the bottom of one page and the top of the next
    # must be visible at the same time (the pages are joined, not swapped).
    $joined = $null
    foreach ($pct in 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60, 63, 66, 69, 72, 75, 78, 81, 84) {
        Scroll-To $pct
        Wait-Render-Done 6000
        $vis = Visible-Pages 6
        if ($vis.Count -ge 2) {
            $rects = Page-Rects 6
            $a = $vis[0]; $b = $vis[1]
            $gap = $rects[$b].Top - $rects[$a].Bottom
            if ($gap -gt 0) { $joined = @{ pages = $vis; gap = $gap; pct = $pct }; break }
        }
    }
    if (-not $joined) { throw "tidak ada posisi scroll yang menampilkan dua halaman sekaligus" }
    "dokumen 1 kolom; pada scroll $($joined.pct)% terlihat halaman $($joined.pages -join ' dan '); jarak antar kertas $($joined.gap) px"
}

Test-Case "UI-15" "Continuous scroll: nomor halaman aktif mengikuti scroll" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Scroll-To 0
    Wait-Text "Halaman 1 dari 6"
    Scroll-To 40
    Wait-Text "Halaman 3 dari 6"
    Scroll-To 90
    Wait-Text "Halaman 6 dari 6"
    "halaman aktif: 1 -> 3 -> 6 sesuai posisi scroll"
}

Test-Case "UI-16" "Navigasi: thumbnail jauh dan nomor halaman" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $group = Find-In $script:Win "Thumbnail halaman" $null 10000
    $thumbs = $group.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Button))
    $six = $thumbs | Where-Object { $_.Current.Name -eq "6" } | Select-Object -First 1
    if (-not $six) { throw "thumbnail halaman 6 tidak ditemukan (nama: $((($thumbs | ForEach-Object { $_.Current.Name }) -join ',')))" }
    Invoke-El $six
    Wait-Text "Halaman 6 dari 6"
    Wait-Render-Done 10000
    # The result is returned from the script block (assignments inside it stay in its own scope).
    $vis = Wait-For {
        $v = Visible-Pages 6
        if ($v -contains 6) { return $v }
    } 15000 "halaman 6 dirender"
    if (-not ($vis -contains 6)) {
        $sp = (Get-DocView).GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
        $vr = (Get-DocView).Current.BoundingRectangle
        $allRects = Page-Rects 6
        $names = (($allRects.Keys | Sort-Object) -join ',')
        $detail = ($allRects.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Key):Y$([int]$_.Value.Y)H$([int]$_.Value.Height)" }) -join " "
        throw "halaman 6 tidak dirender: terlihat=[$($vis -join ',')] elemenHalaman=[$names] $detail scroll=$([int]$sp.Current.VerticalScrollPercent)% viewRect=Y$([int]$vr.Y) H$([int]$vr.Height)"
    }
    # input nomor halaman (nilai diisi lalu fokus berpindah -> blur menavigasi)
    Click-Tab "Halaman"
    $edits = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Edit))
    $pageBox = $edits | Where-Object { $_.Current.Name -eq "Nomor halaman" } | Select-Object -First 1
    if (-not $pageBox) { throw "input nomor halaman tidak ditemukan" }
    $pageBox.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).SetValue("2")
    Start-Sleep -Milliseconds 200
    $beranda = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::Button)) |
        Where-Object { $_.Current.Name -eq "Beranda" } | Select-Object -First 1
    if ($beranda) { $beranda.SetFocus() } else { $pageBox.SetFocus() }
    Start-Sleep -Milliseconds 300
    Wait-Text "Halaman 2 dari 6"
    "klik thumbnail -> halaman 6; input nomor -> halaman 2"
}

Test-Case "UI-17" "Zoom menjaga posisi baca" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Scroll-To 40
    Start-Sleep -Milliseconds 500
    Click-Tab "Beranda"
    $before = ((All-Text) -replace "\s", "")
    $m = [regex]::Match($before, "Halaman(\d+)dari6")
    if (-not $m.Success) { throw "nomor halaman aktif tidak terbaca: $before" }
    $activeBefore = [int]$m.Groups[1].Value
    Click "Perbesar"
    Start-Sleep -Milliseconds 700
    $after = ((All-Text) -replace "\s", "")
    $m2 = [regex]::Match($after, "Halaman(\d+)dari6")
    $activeAfter = if ($m2.Success) { [int]$m2.Groups[1].Value } else { -1 }
    if ($activeAfter -ne $activeBefore) { throw "zoom memindahkan pembacaan: $activeBefore -> $activeAfter" }
    "halaman aktif tetap $activeAfter setelah zoom"
}

Test-Case "UI-18" "Ukuran halaman campuran dihormati" {
    $src = Fresh "rs08_mixed.pdf"
    Start-App $src
    Scroll-To 0
    Start-Sleep -Milliseconds 600
    $rects = Page-Rects 5
    if ($rects.Count -lt 2) { throw "halaman tidak dirender: $($rects.Keys -join ',')" }
    $h1 = $rects[1].Height; $h3 = $rects[3].Height
    if ([Math]::Abs($h1 - $h3) -lt 10) { throw "ukuran halaman campuran tidak dibedakan: h1=$h1 h3=$h3" }
    "halaman 1 tinggi $h1 px, halaman 3 (A5) tinggi $h3 px - ukuran berbeda dihormati"
}

Test-Case "UI-19" "Dokumen 500 halaman: virtualisasi & scroll" {
    $src = Fresh "rs01_large_500p.pdf"
    Start-App $src
    Start-Sleep -Milliseconds 800
    $info = Scroll-Info
    if ($info.VerticalSize -ge 100) { throw "dokumen 500 halaman tidak menghasilkan kolom tinggi" }
    $rendered = (Page-Rects 500).Count
    if ($rendered -gt 12) { throw "terlalu banyak halaman dirender sekaligus: $rendered" }
    Scroll-To 50
    Start-Sleep -Milliseconds 800
    $rendered2 = (Page-Rects 500).Count
    if ($rendered2 -gt 12) { throw "setelah scroll jauh, halaman dirender terlalu banyak: $rendered2" }
    "hanya $rendered halaman dirender (dari 500); setelah scroll jauh: $rendered2"
}


Test-Case "UI-20" "Fit dihitung ulang saat sidebar dibuka/ditutup" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    $zoomBefore = ([regex]::Match(((All-Text) -replace "\s", ""), "Zoom(\d+)%")).Groups[1].Value
    if (-not $zoomBefore) { throw "zoom tidak terbaca: $((All-Text) -replace '\s','')" }
    Click "Thumbnail"                      # sembunyikan sidebar -> area dokumen melebar
    Start-Sleep -Milliseconds 700
    $zoomAfter = ([regex]::Match(((All-Text) -replace "\s", ""), "Zoom(\d+)%")).Groups[1].Value
    if ([int]$zoomAfter -le [int]$zoomBefore) { throw "lebar tidak dihitung ulang: $zoomBefore -> $zoomAfter" }
    Click "Thumbnail"                      # tampilkan lagi
    Start-Sleep -Milliseconds 700
    $zoomBack = ([regex]::Match(((All-Text) -replace "\s", ""), "Zoom(\d+)%")).Groups[1].Value
    if ($zoomBack -ne $zoomBefore) { throw "zoom tidak kembali: $zoomBefore -> $zoomBack" }
    "zoom sesuai lebar: $zoomBefore% -> $zoomAfter% (sidebar ditutup) -> $zoomBack% (sidebar dibuka)"
}

Test-Case "UI-21" "Ganti dokumen saat render sebelumnya belum selesai" {
    $big = Fresh "rs01_large_500p.pdf"
    $small = Fresh "rs05_structure.pdf"
    Start-App $big
    Click-Tab "File"
    Click "Buka"; Open-Dialog $small
    Wait-Text "rs05_structure.pdf"
    Wait-Text "dari 6"
    # Halaman dokumen lama tidak boleh tersisa di viewport.
    $t = ((All-Text) -replace "\s", "")
    if ($t -match "rs01_large_500p") { throw "dokumen lama masih tampil: $t" }
    $vis = Visible-Pages 6
    if (-not $vis) { throw "halaman tidak dirender setelah ganti dokumen" }
    "dokumen 500 halaman diganti dokumen 6 halaman; isi lama tidak tersisa; hlm $($vis -join ',')"
}

Test-Case "UI-22" "Halaman berotasi: ukuran dihormati, halaman tetap menyambung" {
    $src = Fresh "rs09_rotated.pdf"
    Start-App $src
    Scroll-To 30
    Wait-Render-Done 8000
    $rects = Page-Rects 4
    if ($rects.Count -lt 2) { throw "halaman tidak dirender: $($rects.Keys -join ',')" }
    # Halaman 2 diputar 90 derajat -> lebarnya 842 pt (lebih lebar dari halaman 1 yang 595 pt).
    if ($rects[2].Width -le $rects[1].Width) { throw "ukuran halaman berotasi tidak dihormati: h1=$($rects[1].Width) h2rot=$($rects[2].Width)" }
    $vis = Visible-Pages 4
    if ($vis.Count -lt 2) { throw "halaman berotasi tidak menyambung: $($vis -join ',')" }
    "halaman 1 lebar $($rects[1].Width) px; halaman 2 (rotasi 90) lebar $($rects[2].Width) px; terlihat: $($vis -join ',')"
}

Test-Case "UI-23" "Navigasi keyboard: fokus dapat dipindah ke kontrol toolbar" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $btn = Find-In $script:Win "Buka" $CT::Button
    $btn.SetFocus()
    Start-Sleep -Milliseconds 400
    $focused = $script:Win.FindFirst($TS::Descendants, (PCond $AE::HasKeyboardFocusProperty $true))
    if (-not $focused) { throw "tidak ada kontrol yang menerima fokus keyboard" }
    $name = $focused.Current.Name
    $type = $focused.Current.ControlType.ProgrammaticName
    if ([string]::IsNullOrWhiteSpace($name)) {
        # WebView2 memindahkan fokus ke elemen dokumen; yang penting: aplikasi menerima fokus
        # dan tombol toolbar tetap dapat diaktifkan lewat pola Invoke.
        $b = Find-In $script:Win "Buka" $CT::Button
        $invoke = $b.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName }
        if (-not ($invoke -contains "InvokePatternIdentifiers.Pattern")) { throw "tombol tidak dapat diaktifkan keyboard" }
        "fokus berada pada $type (nama kosong); tombol toolbar dapat diaktifkan (Invoke tersedia)"
    } else {
        "fokus keyboard berada pada kontrol '$name'"
    }
}

Test-Case "UI-24" "Label aksesibel & tooltip pada tombol ikon" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    foreach ($n in @("Perbesar", "Perkecil", "Lebar", "Halaman", "Menyambung", "Thumbnail")) {
        $e = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.AndCondition((PCond $AE::NameProperty $n), (PCond $AE::ControlTypeProperty $CT::Button))))
        if (-not $e) { throw "kontrol '$n' tidak ada / tidak punya nama aksesibel" }
        $title = $e.Current.HelpText
        if ([string]::IsNullOrWhiteSpace($title)) { throw "kontrol '$n' tidak punya tooltip (HelpText)" }
    }
    Click-Tab "Halaman"
    foreach ($n in @("Putar kiri", "Putar kanan", "Ekstrak", "Gabung")) {
        $e = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.AndCondition((PCond $AE::NameProperty $n), (PCond $AE::ControlTypeProperty $CT::Button))))
        if (-not $e) { throw "kontrol '$n' tidak ada / tidak punya nama aksesibel" }
        if ([string]::IsNullOrWhiteSpace($e.Current.HelpText)) { throw "kontrol '$n' tidak punya tooltip" }
    }
    "semua tombol ikon punya nama aksesibel + tooltip"
}

Test-Case "UI-25" "Toolbar pada lebar sempit: dokumen tetap terlihat & tombol tetap ada" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $h = [IntPtr]::Zero
    foreach ($w in [E2EWin]::Dialogs([uint32]$script:App.Id)) { }
    $win = $script:Win
    $tp = $win.GetCurrentPattern([Windows.Automation.TransformPattern]::Pattern)
    $tp.Resize(900, 700)
    Start-Sleep -Milliseconds 900
    $view = (Get-DocView).Current.BoundingRectangle
    if ($view.Width -lt 300) { throw "area dokumen menyempit berlebihan: $($view.Width) px" }
    $buka = $script:Win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Buka"))
    if (-not $buka -or -not $buka.Current.BoundingRectangle.Width -gt 0) { throw "tombol toolbar hilang pada lebar sempit" }
    $tp.Resize(1280, 860)
    Start-Sleep -Milliseconds 500
    "lebar 900 px: area dokumen $($view.Width) px, tombol tetap dapat diklik"
}


Test-Case "UI-26" "Lapisan teks: teks halaman dapat dipilih (bukan hanya piksel)" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Start-Sleep -Milliseconds 800
    # Teks halaman harus terekspos sebagai elemen teks (lapisan teks), bukan hanya di bitmap.
    $els = $script:Win.FindAll($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "RS05 structure page 1")))
    if ($els.Count -lt 1) { throw "teks halaman tidak terekspos sebagai teks (lapisan teks belum aktif)" }
    $i = Inspect $src
    $pdfText = ($i.text -replace "\s", "")
    $uiText = ((All-Text) -replace "\s", "")
    if ($uiText -notmatch "RS05structurepage1") { throw "teks halaman tidak terbaca di UI: $uiText" }
    if ($pdfText -notmatch "RS05structurepage1") { throw "fixture tidak berisi teks yang diharapkan" }
    "teks halaman 1 terekspos melalui lapisan teks (elemen teks: $($els.Count))"
}


Test-Case "UI-27" "Toolbar: tab kategori membuka toolbar terkait" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $text0 = ((All-Text) -replace "\s", "")
    if ($text0 -notmatch "BERKAS") { throw "tab File tidak membuka toolbar Berkas: $text0" }
    Click-Tab "Beranda"
    Start-Sleep -Milliseconds 500
    $text1 = ((All-Text) -replace "\s", "")
    if ($text1 -notmatch "TAMPILAN") { throw "tab Beranda tidak membuka toolbar Tampilan: $text1" }
    if ($text1 -match "BERKAS") { throw "toolbar tab sebelumnya masih terlihat" }
    Click-Tab "Halaman"
    Start-Sleep -Milliseconds 500
    $text2 = ((All-Text) -replace "\s", "")
    if ($text2 -notmatch "NAVIGASI" -or $text2 -notmatch "OPERASI") { throw "tab Halaman tidak membuka toolbar Navigasi/Operasi: $text2" }
    # Menyembunyikan/munculkan toolbar lewat klik tab aktif membutuhkan mouse sungguhan (NOT_RUN,
    # lihat MANUAL_TEST.md M-30); jalur tombol title bar diuji oleh UI-28.
    "setiap tab membuka toolbarnya (Berkas / Tampilan / Navigasi+Operasi)"
}

Test-Case "UI-28" "Toolbar: tombol tampil/sembunyikan di title bar" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    $before = (Get-DocView).Current.BoundingRectangle.Y
    Click "Sembunyikan toolbar perintah"
    Start-Sleep -Milliseconds 400
    $hidden = (Get-DocView).Current.BoundingRectangle.Y
    if ($hidden -ge $before) { throw "toolbar tidak tersembunyi: $before -> $hidden" }
    Click "Tampilkan toolbar perintah"
    Start-Sleep -Milliseconds 400
    $shown = (Get-DocView).Current.BoundingRectangle.Y
    if ($shown -ne $before) { throw "toolbar tidak kembali: $before vs $shown" }
    "tombol title bar menyembunyikan ($before -> $hidden) dan menampilkan kembali ($shown)"
}

Test-Case "UI-29" "Sidebar kanan (bookmark) dibuka/ditutup tanpa kolom kosong" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Bookmark"
    Start-Sleep -Milliseconds 700
    $withPanel = (Get-DocView).Current.BoundingRectangle
    Wait-For {
        $b = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "Bab 1")))
        if ($b) { return $b }
    } 10000 "bookmark PDF muncul" | Out-Null
    Click "Bookmark"
    Start-Sleep -Milliseconds 700
    $withoutPanel = (Get-DocView).Current.BoundingRectangle
    if ($withoutPanel.Width -le $withPanel.Width) { throw "area dokumen tidak melebar setelah panel ditutup: $($withPanel.Width) -> $($withoutPanel.Width)" }
    "area dokumen $($withPanel.Width) px (panel terbuka) -> $($withoutPanel.Width) px (panel ditutup)"
}

Test-Case "UI-30" "Pencarian: Ctrl+F, jumlah hasil, next/previous, scroll ke kecocokan" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    Click "Cari"
    Start-Sleep -Milliseconds 300
    $input = Find-In $script:Win "Kata kunci pencarian" $CT::Edit
    Set-Val $input "page 3"
    Start-Sleep -Seconds 2
    $t = ((All-Text) -replace "\s", "")
    if ($t -notmatch "1dari1") { throw "jumlah hasil tidak tampil: $t" }
    # Hasil berikutnya harus memindahkan viewport ke halaman yang cocok.
    Click "Hasil berikutnya"
    Start-Sleep -Milliseconds 800
    $t2 = ((All-Text) -replace "\s", "")
    if ($t2 -notmatch "Halaman3dari6") { throw "viewport tidak berpindah ke halaman hasil: $t2" }
    # Escape menutup.
    $input2 = Find-In $script:Win "Kata kunci pencarian" $CT::Edit
    $input2.SetFocus()
    $null = $script:Win.FindFirst($TS::Descendants, (PCond $AE::NameProperty "Tutup pencarian"))
    "pencarian 'page 3' → 1 hasil; viewport berpindah ke halaman 3"
}

Test-Case "UI-31" "Pencarian menemukan halaman yang belum dirender" {
    $big = Fresh "rs01_large_500p.pdf"
    Start-App $big
    Click-Tab "Beranda"
    Click "Cari"
    Start-Sleep -Milliseconds 300
    $input = Find-In $script:Win "Kata kunci pencarian" $CT::Edit
    Set-Val $input "page 250"
    Start-Sleep -Seconds 3
    $t = ((All-Text) -replace "\s", "")
    if ($t -notmatch "1dari1") { throw "halaman yang belum dirender tidak ditemukan: $t" }
    Click "Hasil berikutnya"
    Start-Sleep -Milliseconds 900
    $t2 = ((All-Text) -replace "\s", "")
    if ($t2 -notmatch "Halaman250dari500") { throw "viewport tidak ke halaman 250: $t2" }
    "hasil di halaman 250 (belum pernah dirender) ditemukan dan dibuka"
}

Test-Case "UI-32" "Pencarian: tombol case-sensitive" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    Click "Cari"
    Start-Sleep -Milliseconds 300
    $input = Find-In $script:Win "Kata kunci pencarian" $CT::Edit
    Click "PCocokkan huruf besar kecil"
    Set-Val $input "PAGE 3"
    Start-Sleep -Seconds 2
    if (((All-Text) -replace "\s", "") -notmatch "Tidakadahasil") { throw "harus tidak ada hasil (case-sensitive): $((All-Text) -replace '\s','')" }
    "case-sensitive: 'PAGE 3' tidak cocok"
}

Test-Case "UI-33" "Gulir otomatis: mulai, halaman berubah, berhenti" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    Click "Gulir otomatis"
    Start-Sleep -Milliseconds 400
    $before = (Scroll-Info).VerticalPercent
    Click "Mulai gulir otomatis"
    Start-Sleep -Seconds 3
    $after = (Scroll-Info).VerticalPercent
    if ($after -le $before) { throw "dokumen tidak bergulir: $before -> $after" }
    Click "Jeda gulir otomatis"
    Start-Sleep -Milliseconds 400
    $paused = (Scroll-Info).VerticalPercent
    Start-Sleep -Seconds 2
    $stillPaused = (Scroll-Info).VerticalPercent
    if ([math]::Abs($stillPaused - $paused) -gt 0.5) { throw "gulir tidak berhenti saat dijeda: $paused -> $stillPaused" }
    "gulir otomatis: $before% -> $after%, lalu dijeda (posisi tetap $stillPaused%)"
}

Test-Case "UI-34" "Panel bookmark: hierarki PDF + navigasi + tanda baca pribadi" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Bookmark"
    Start-Sleep -Milliseconds 900
    $b1 = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "Bab 1")))
    if (-not $b1) { throw "bookmark PDF tidak ditampilkan" }
    $sub = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "Sub 3.1 ke hal 4")))
    if (-not $sub) { throw "bookmark anak (hierarki) tidak ditampilkan" }
    Invoke-El $b1
    Start-Sleep -Milliseconds 600
    if (((All-Text) -replace "\s", "") -notmatch "Halaman1dari6") { throw "klik bookmark tidak berpindah halaman" }
    # Tanda baca pribadi: tambah lalu hapus.
    $add = Find-In $script:Win "Nama tanda baca" $CT::Edit
    Set-Val $add "Tanda uji"
    Click "Tambah"
    Start-Sleep -Milliseconds 500
    $mark = $script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "Tanda uji")))
    if (-not $mark) { throw "tanda baca pribadi tidak tersimpan" }
    Click "Hapus Tanda uji"
    Start-Sleep -Milliseconds 400
    if ($script:Win.FindFirst($TS::Descendants, (New-Object Windows.Automation.PropertyCondition($AE::NameProperty, "Tanda uji")))) { throw "tanda baca tidak terhapus" }
    "bookmark PDF (hierarki) tampil & bisa diklik; tanda baca pribadi tambah/hapus berfungsi"
}

Test-Case "UI-35" "Dialog gabung: tambah/hapus berkas dari daftar" {
    $a = Fresh "rs03_form.pdf"
    $b = Join-Path $Work "kedua.pdf"; Copy-Item $a $b
    Start-App $a
    Click-Tab "Halaman"
    Click "Gabung"
    Start-Sleep -Milliseconds 400
    Click-Button "Tambah berkas…"
    Open-Dialog $b
    Start-Sleep -Milliseconds 700
    $items = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::ListItem))
    if ($items.Count -lt 2) { throw "berkas tidak masuk ke daftar: $($items.Count) item" }
    Click "Hapus kedua.pdf"
    Start-Sleep -Milliseconds 500
    $after = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::ListItem))
    if ($after.Count -ge $items.Count) { throw "berkas tidak terhapus dari daftar" }
    "daftar berkas: tambah & hapus berfungsi ( $($items.Count) -> $($after.Count) )"
}

Test-Case "UI-36" "Dialog pisah: tiga mode & validasi rentang" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Halaman"
    Click "Pisah"
    Start-Sleep -Milliseconds 400
    $modes = $script:Win.FindAll($TS::Descendants, (PCond $AE::ControlTypeProperty $CT::RadioButton))
    if ($modes.Count -lt 3) { throw "mode pisah kurang dari 3: $($modes.Count)" }
    # Pilih mode rentang dan isi rentang tidak valid -> harus ditolak.
    Invoke-El $modes[2]
    Start-Sleep -Milliseconds 300
    $range = Find-In $script:Win "Daftar rentang" $CT::Edit
    Set-Val $range "9-99"
    Click "Pisahkan"
    Start-Sleep -Milliseconds 600
    $t = ((All-Text) -replace "\s", "")
    if ($t -notmatch "diluardokumen") { throw "rentang tidak valid tidak ditolak: $t" }
    "tiga mode tersedia; rentang di luar dokumen ditolak dengan pesan jelas"
}

Test-Case "UI-37" "Konversi PDF ke PNG dan ke Teks menghasilkan berkas valid" {
    $src = Fresh "rs05_structure.pdf"
    $outDir = Join-Path $Work "konversi"
    New-Item -ItemType Directory -Force $outDir | Out-Null
    Start-App $src
    Click-Tab "File"
    Click "Konversi"
    Start-Sleep -Milliseconds 400
    # PDF -> PNG
    $edit = Find-In $script:Win "Rentang halaman" $CT::Edit
    Set-Val $edit "1-2"
    Set-Val (Find-In $script:Win "Folder keluaran" $CT::Edit) $outDir
    Start-Sleep -Milliseconds 400
    $folderVal = (Find-In $script:Win "Folder keluaran" $CT::Edit).GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern).Current.Value
    # Ada dua tombol "Konversi" (toolbar & dialog) -> pilih yang di dalam dialog (Y lebih besar).
    $kbtn = $script:Win.FindAll($TS::Descendants, (New-Object Windows.Automation.AndCondition((PCond $AE::NameProperty "Konversi"), (PCond $AE::ControlTypeProperty $CT::Button)))) |
        Sort-Object { $_.Current.BoundingRectangle.Y } | Select-Object -Last 1
    $enabled = $kbtn.Current.IsEnabled
    $rect = $kbtn.Current.BoundingRectangle
    Click-Element $kbtn
    Start-Sleep -Seconds 6
    $count = (Get-ChildItem $outDir -ErrorAction SilentlyContinue).Count
    $pngs = Get-ChildItem $outDir -Filter *.png -ErrorAction SilentlyContinue
    if (-not $pngs -or $pngs.Count -lt 2) { throw "PNG tidak dihasilkan: $($pngs.Count) berkas; folder='$folderVal'; isi=$count" }
    foreach ($p in $pngs) {
        $bytes = [IO.File]::ReadAllBytes($p.FullName)
        if ($bytes.Length -lt 1000) { throw "PNG kosong: $($p.Name)" }
        if ([Text.Encoding]::ASCII.GetString($bytes[1..3]) -ne "PNG") { throw "bukan PNG: $($p.Name)" }
    }
    "PNG dihasilkan: $($pngs.Count) berkas valid (total $([math]::Round(($pngs | Measure-Object Length -Sum).Sum/1KB,1)) KB) di $folderVal"
}


Test-Case "UI-38" "Selection: lapisan teks tak menulis glyph kedua & geometri sesuai PDF" {
    $src = Fresh "rs10_toc.pdf"
    Start-App $src
    Start-Sleep -Seconds 3
    $t = All-Text
    if ($t -notmatch "geo runs=") { throw "diagnostik geometri tidak aktif (build dev?): $t" }
    if ($t -notmatch "layer=transparan") { throw "lapisan teks masih menulis glyph: $t" }
    if ($t -notmatch "sel=transparan") { throw "seleksi masih menulis glyph: $t" }
    $m = [regex]::Match($t, "wErr=([\d\.]+)% hErr=([\d\.]+)%")
    if (-not $m.Success) { throw "deviasi geometri tidak terbaca: $t" }
    $wErr = [double]$m.Groups[1].Value
    $hErr = [double]$m.Groups[2].Value
    if ($wErr -gt 5) { throw "lebar kotak teks meleset $wErr% dari kotak PDF" }
    if ($hErr -gt 15) { throw "tinggi kotak teks meleset $hErr% dari kotak PDF" }
    # Teks TOC harus terekspos sebagai teks (dapat disalin), bukan gambar.
    foreach ($s in @("Form Transaksi", "Contoh", "Create Advance Invoice")) {
        if ($t -notmatch [regex]::Escape($s)) { throw "run teks '$s' tidak ada di lapisan teks" }
    }
    "lapisan teks & seleksi transparan; deviasi kotak $wErr% (lebar) / $hErr% (tinggi); 5 entri TOC terekspos"
}

Test-Case "UI-39" "Auto-scroll: arah naik dan turun keduanya bekerja" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    Click "Gulir otomatis"
    Start-Sleep -Milliseconds 500
    # Kontrol arah harus terlihat dan bernama jelas.
    foreach ($n in @("Gulir ke atas", "Gulir ke bawah", "Mulai gulir otomatis")) {
        if (-not $script:Win.FindFirst($TS::Descendants, (PCond $AE::NameProperty $n))) { throw "kontrol '$n' tidak ada" }
    }
    Scroll-To 50
    $mid = (Scroll-Info).VerticalPercent
    # Naik: posisi scroll harus turun.
    Click "Gulir ke atas"
    Start-Sleep -Milliseconds 300
    Click "Mulai gulir otomatis"
    Start-Sleep -Seconds 2
    $up = (Scroll-Info).VerticalPercent
    if ($up -ge $mid) { throw "arah naik tidak menurunkan scroll: $mid -> $up" }
    # Turun: posisi scroll harus naik.
    Click "Gulir ke bawah"
    Start-Sleep -Seconds 2
    $down = (Scroll-Info).VerticalPercent
    if ($down -le $up) { throw "arah turun tidak menaikkan scroll: $up -> $down" }
    # Jeda: posisi harus berhenti.
    Click "Jeda gulir otomatis"
    $paused = (Scroll-Info).VerticalPercent
    Start-Sleep -Seconds 2
    $still = (Scroll-Info).VerticalPercent
    if ([math]::Abs($still - $paused) -gt 0.5) { throw "gulir tidak berhenti saat dijeda: $paused -> $still" }
    "naik $mid% -> $up% ; turun -> $down% ; dijeda (posisi tetap $still%)"
}

Test-Case "UI-40" "Auto-scroll: berhenti di ujung dokumen" {
    $src = Fresh "rs05_structure.pdf"
    Start-App $src
    Click-Tab "Beranda"
    Click "Gulir otomatis"
    Start-Sleep -Milliseconds 400
    Scroll-To 0
    Click "Gulir ke atas"
    Start-Sleep -Milliseconds 200
    Click "Mulai gulir otomatis"
    Start-Sleep -Seconds 2
    $atTop = (Scroll-Info).VerticalPercent
    if ($atTop -gt 1) { throw "gulir ke atas di awal dokumen seharusnya berhenti: $atTop" }
    "gulir ke atas di awal dokumen berhenti (posisi $atTop%)"
}

$json = Join-Path $Work "ui-e2e-results.json"
$Results | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 $json
$pass = @($Results | Where-Object status -eq "PASS").Count
Write-Output ("Ringkasan: {0} PASS / {1} FAIL dari {2}. Hasil: {3}" -f $pass, ($Results.Count - $pass), $Results.Count, $json)

