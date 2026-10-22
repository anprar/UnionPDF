# Strategi WebView2 (Windows)

UnionPDF memakai **Microsoft Edge WebView2 Runtime** (Chromium) sebagai mesin web — ini
persyaratan Tauri 2 di Windows.

## Keputusan: runtime evergreen (bukan dibundel)

| Aspek | Keputusan | Alasan |
|---|---|---|
| Mode instalasi | `downloadBootstrapper` (lihat `tauri.conf.json` → `bundle.webviewInstallMode`) | WebView2 Runtime sudah terpasang di Windows 10/11 (Edge / Office / Teams) → sebagian besar mesin tidak perlu mengunduh apa pun |
|[Kebutuhan internet saat instalasi] | **Tidak** untuk mesin yang sudah punya WebView2 Runtime. Diperlukan **hanya** bila runtime belum ada (bootstrapper ±1,8 MB diunduh lalu) | Menghindari ukuran installer membengkak |
| Ukuran runtime | ±130–180 MB, diinstal sekali oleh Microsoft, **tidak** ikut dalam paket UnionPDF (paket 74,6 MB) | Runtime adalah komponen sistem, bukan milik UnionPDF |
| Digunakan bersama | **Ya** — satu runtime dipakai bersama oleh Edge, Office, Teams, dan UnionPDF; diperbarui otomatis oleh Microsoft | Tidak ada duplikasi; tetap mutakhir |
| Opsi fully offline (bila dibutuhkan) | `embedBootstrapper` (+±1,8 MB di installer, runtime tetap diunduh) atau `offlineInstaller` (+±127 MB, tanpa internet sama sekali) | Dipilih hanya bila target lingkungan tanpa internet; menambah ukuran installer |
| Opsi fixed runtime | Tidak dipakai: runtime fixed membekukan versi WebView2 (±180 MB, tidak dipakai bersama, tidak update otomatis) | Biaya ukuran dan tidak dapat menerima perbaikan keamanan WebView2 |

## Consequences

- **Mesin tanpa WebView2** (mis. Windows Server Core, Windows 10 LTSC yang bersih): instalasi akan
  mengunduh bootstrapper ±1,8 MB. Untuk lingkungan tanpa internet, bundel harus dibangun ulang
  dengan `webviewInstallMode.type = "offlineInstaller"`.
- **Ukuran installer UnionPDF** tidak berubah karena WebView2 (43,2 MB NSIS; paket portabel 74,6 MB).
- Pemeriksaan: `Get-ItemProperty HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}`
  (versi terpasang: 155.0.4283.62 pada mesin uji).
