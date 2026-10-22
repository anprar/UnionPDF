param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Pdf = "$PSScriptRoot\..\src-tauri\tests\fixtures\rs05_structure.pdf",
    [string]$Out = "$env:TEMP\unionpdf-window.png",
    [double]$ScrollPercent = 15
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing @"
using System; using System.Text; using System.Runtime.InteropServices;
public static class WinCap {
 delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP cb, IntPtr l);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
 [StructLayout(LayoutKind.Sequential)] struct RECT { public int L, T, R, B; }
 static string Cls(IntPtr h) { var s = new StringBuilder(64); GetClassName(h, s, 64); return s.ToString(); }
 public static IntPtr Find(uint pid, string title) {
  IntPtr found = IntPtr.Zero;
  EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); var t = new StringBuilder(128); GetWindowText(h, t, 128);
   if (p == pid && IsWindowVisible(h) && t.ToString() == title) { found = h; return false; } return true; }, IntPtr.Zero);
  return found;
 }
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 public static void Capture(IntPtr h, string path) {
  RECT r; GetWindowRect(h, out r);
  using (var bmp = new System.Drawing.Bitmap(r.R - r.L, r.B - r.T))
  using (var g = System.Drawing.Graphics.FromImage(bmp)) {
   var hdc = g.GetHdc(); PrintWindow(h, hdc, 2); g.ReleaseHdc(hdc); bmp.Save(path);
  }
 }
}
"@
$AE = [Windows.Automation.AutomationElement]
$TS = [Windows.Automation.TreeScope]
function C($a, $b) { New-Object Windows.Automation.AndCondition($a, $b) }
function P($k, $v) { New-Object Windows.Automation.PropertyCondition($k, $v) }
$p = Start-Process $Exe -ArgumentList "`"$Pdf`"" -PassThru
try {
    Start-Sleep -Seconds 5
    $win = $AE::RootElement.FindFirst($TS::Children, (C (P $AE::ProcessIdProperty $p.Id) (P $AE::NameProperty "UnionPDF")))
    if (-not $win) { throw "jendela UnionPDF tidak ditemukan" }
    $view = $win.FindFirst($TS::Descendants, (P $AE::NameProperty "Area dokumen"))
    $sp = $view.GetCurrentPattern([Windows.Automation.ScrollPattern]::Pattern)
    $sp.SetScrollPercent([Windows.Automation.ScrollPattern]::NoScroll, $ScrollPercent)
    Start-Sleep -Seconds 2
    $h = [WinCap]::Find([uint32]$p.Id, "UnionPDF")
    [WinCap]::Capture($h, $Out)
    Write-Output "OK -> $Out (hanya jendela UnionPDF, scroll $ScrollPercent%)"
} finally {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
}
