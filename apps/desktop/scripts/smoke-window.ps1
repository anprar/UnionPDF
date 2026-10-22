# Smoke test visual: jalankan exe UnionPDF (opsional dengan PDF), tunggu, tangkap HANYA jendela
# UnionPDF (PrintWindow, bukan seluruh layar) ke PNG, lalu tutup aplikasi.
param(
    [string]$Exe = "$PSScriptRoot\..\src-tauri\target\debug\unionpdf-desktop.exe",
    [string]$Pdf = "",
    [string]$Out = "$env:TEMP\unionpdf-smoke.png",
    [int]$WaitSeconds = 6
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Text; using System.Runtime.InteropServices;
public class UnionPdfWin {
 public delegate bool EP(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] public static extern bool EnumWindows(EP cb, IntPtr l);
 [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
 public struct R { public int L, T, Rr, B; }
 public static IntPtr Find(uint pid) {
  IntPtr found = IntPtr.Zero;
  EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); var t = new StringBuilder(256); GetWindowText(h, t, 256);
   if (p == pid && IsWindowVisible(h) && t.ToString() == "UnionPDF") { found = h; return false; } return true; }, IntPtr.Zero);
  return found;
 }
}
'@
$argsList = @()
if ($Pdf) { $argsList += "`"$Pdf`"" }
$p = if ($argsList) { Start-Process -FilePath $Exe -ArgumentList $argsList -PassThru } else { Start-Process -FilePath $Exe -PassThru }
try {
    Start-Sleep -Seconds $WaitSeconds
    $h = [UnionPdfWin]::Find([uint32]$p.Id)
    if ($h -eq [IntPtr]::Zero) { throw "Jendela UnionPDF tidak ditemukan" }
    $r = New-Object UnionPdfWin+R
    [UnionPdfWin]::GetWindowRect($h, [ref]$r) | Out-Null
    $bmp = New-Object Drawing.Bitmap ($r.Rr - $r.L), ($r.B - $r.T)
    $g = [Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [UnionPdfWin]::PrintWindow($h, $hdc, 2) | Out-Null
    $g.ReleaseHdc($hdc)
    $bmp.Save($Out)
    $p.Refresh()
    Write-Output ("OK alive={0} working_set_mb={1} out={2}" -f (-not $p.HasExited), [math]::Round($p.WorkingSet64 / 1MB, 1), $Out)
} finally {
    Get-Process -Id $p.Id -ErrorAction SilentlyContinue | Stop-Process
}
