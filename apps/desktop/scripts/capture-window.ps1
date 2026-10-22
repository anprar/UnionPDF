param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\release\unionpdf-desktop.exe",
    [string]$Pdf = "",
    [string]$Out = "$env:TEMP\unionpdf-window.png",
    [int]$WaitSeconds = 6
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing @"

using System; using System.Text; using System.Collections.Generic; using System.Runtime.InteropServices;
public static class Shot {
 delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EP cb, IntPtr l);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
 [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr h, int cmd);
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
   var hdc = g.GetHdc();
   PrintWindow(h, hdc, 2);
   g.ReleaseHdc(hdc);
   bmp.Save(path);
  }
 }
 public static void Focus(IntPtr h) { SetForegroundWindow(h); }
 public static void Maximize(IntPtr h) { ShowWindow(h, 3); }
}
"@
$p = if ($Pdf) { Start-Process $Exe -ArgumentList "`"$Pdf`"" -PassThru } else { Start-Process $Exe -PassThru }
try {
    Start-Sleep -Seconds $WaitSeconds
    $h = [Shot]::Find([uint32]$p.Id, "UnionPDF")
    if ($h -eq [IntPtr]::Zero) { throw "jendela UnionPDF tidak ditemukan" }
    [Shot]::Focus($h) | Out-Null
    Start-Sleep -Milliseconds 700
    [Shot]::Capture($h, $Out)
    Write-Output "OK -> $Out (hanya jendela UnionPDF)"
} finally {
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
}
