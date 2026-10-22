# PROJECT_STATE.md — Status Saat Ini

> Status **saat ini**, bukan riwayat lengkap. Riwayat ada di `SESSION_LOG.md`.

| Field | Nilai |
|---|---|
| Tanggal | 2026-10-22 |
| Waktu | 14:15 WIB (UTC+7) |
| Zona waktu | Asia/Bangkok / SE Asia Standard Time |
| Session ID | `2026-10-22T1400+0700` (pembersihan ruang kerja 11,76 GB; checkpoint akhir + commit & push) |
| Fase aktif | **M1 — viewer & authoring dasar berjalan**; scope **reading tools, compact toolbar, bookmark, split, dan konversi** Priority A–F baru diimplementasikan (bukan "scope selesai"); sisanya: Office conversion, DPI 125–200 %, clean-install, seret mouse |
| Milestone aktif | M1 (lihat `docs/ROADMAP.md`) |
| Task aktif | UPDF-048 (vertical slice) **REVIEW → sebagian DONE**; UPDF-049 (worker PDFBox) **DONE**; UPDF-050/051/052 tersisa (outline re-order, bidi RTL, redaksi) |
| Git repo | **`github.com/anprar/UnionPDF`** (public, branch `main`) — HEAD lokal `2a1718a` (**ahead 1, tidak di-push**); remote masih `d01cd16` |
| Working tree | Tidak bersih — **tanpa commit (G-2)**: `apps/desktop/` (baru), `experiments/restart/`, `docs/sessions/2026-10-22T0900+0700.md` |
| Stack | **Fondasi disetujui (ADR-002)**: Tauri 2.12.4 · React 19.3.1 + TS 7.0.2 + Vite 8.3.4 · Rust 1.98 · **PDFium 151.0.7881.0** (renderer) · **PDFBox 3.0.8** (authoring, worker Java) · JSON/config tanpa database. Implementasi lama (Python/PySide6/PyMuPDF) = benchmark, tidak disentuh |
| Lisensi proyek | `LICENSE` = **AGPL-3.0** (tidak diubah, tidak diratifikasi ulang). Lisensi baru untuk PDFBox/BC (Apache-2.0 / MIT-style) **dibaca** pada provenance, **belum** diratifikasi ke LICENSE/NOTICE (perlu persetujuan terpisah) |
| Review pasca-REA | `docs/POST_ALL_REFERENCES_TECH_REVIEW.md` (DRAFT) · `docs/STACK_EVALUATION.md` §10 |

---

## Status persetujuan (controlled restart)

**Tetap berlaku:** cleanup aplikasi lama **BELUM DISETUJUI** · `LICENSE`/`NOTICE` **tidak diubah** ·
**tidak ada commit/push/publikasi** (G-2) · tidak ada instalasi global/admin · MuPDF **tidak**
dipakai sebagai dependency aplikasi (redaksi ditunda) · tidak ada engine redaksi custom.

Keputusan pengguna 2026-10-21 (sesi `2026-10-21T1215+0700`): G-1 disetujui · G-2 tanpa commit ·
G-3/G-4 disetujui · G-5 tunda · G-6 tunda · G-7 disetujui terbatas · **fondasi disetujui**
(Tauri 2 + React/TS/Vite + Rust + PDFium renderer + JSON; PDFBox boleh dipakai sebagai authoring
awal bila terbukti layak) · redaksi ditunda.

Menunggu persetujuan: `docs/BLOCKERS.md` **B-RT1** (runtime Java untuk distribusi worker).

---

## Pembersihan ruang kerja (2026-10-22)

Workspace 12,70 GB → **0,94 GB** (11,76 GB artefak build yang bisa direproduksi ulang dihapus:
`target/`, cache cargo, `node_modules`, JDK toolchain, runtime jlink di luar paket, target spike).
Deliverable tetap utuh di `apps/desktop/dist-package/` (paket mandiri 75,2 MB + installer NSIS 43,3 MB)
dan sudah diverifikasi jalan dari sana. Rincian: `docs/sessions/2026-10-22T1400+0700.md`.

---

## Status implementasi (dipisah agar tidak tercampur)

| Aspect | Status | Bukti |
|---|---|---|
| **Engine dipilih** | PDFium (renderer) · PDFBox 3.0.8 (authoring awal) | `docs/decisions/ADR-002-restart-foundation.md` |
| **Engine terintegrasi** | PDFium in-process (render, rotasi, Save As, extract/merge fallback) · **PDFBox worker Java terhubung** (IPC JSON-lines over stdio) dan dipakai aplikasi untuk extract/merge/form/anotasi | `apps/desktop/src-tauri/src/{engine,worker,ops}.rs` |
| **Fitur backend teruji** | **26/26** `cargo test` (unit + integrasi PDFium nyata + worker PDFBox nyata + text span + penempatan anotasi per halaman + outline + pencarian + konversi PNG/TXT) | `apps/desktop/src-tauri/src/ops.rs` |
| **Fitur UI teruji** | **39 PASS + 1 NOT_RUN** (40 kasus) (E2E UI 37 kasus: dialog, putar+simpan, ekstrak berkonfirmasi, gabung (dialog daftar), batal job, form, dirty-state, continuous scroll, fit/sidebar, ganti dokumen saat render, halaman berotasi, fokus keyboard, label aksesibel, toolbar sempit, lapisan teks, **toolbar collapse/expand, panel kanan, pencarian, auto-scroll, bookmark, split, konversi**) | `apps/desktop/scripts/ui-e2e.ps1`, `docs/sessions/2026-10-22T1900+0700.md` |
| **Lapisan teks** | **Terbukti**: text run per halaman dari engine (ruang tampilan, rotasi & crop box dihormati) → teks dapat dipilih/disalin | `text_spans` + `TextLayer.tsx`; UI-26 |
| **Belum diverifikasi** | Anotasi yang digambar dengan mouse · prompt timpa Windows · High-DPI 125/150/200 % · multi-monitor · clean-install installer · redaksi (ditunda) | `apps/desktop/MANUAL_TEST.md` M-01…M-24 |

### Yang benar-benar berjalan sekarang

- Viewer: buka (dialog/argumen CLI), render, navigasi, zoom ±/Lebar/Halaman, thumbnail lazy, pesan error spesifik.
- Operasi halaman: Putar (in-memory → Simpan Sebagai), Simpan Sebagai (atomik, verifikasi output, input tak pernah ditimpa), Ekstrak, Gabung.
- **Integritas struktur**: extract memangkas bookmark/link/field yang menunjuk halaman terhapus; merge mengganti nama field bentrok (`nama` → `nama_2`); sebelum eksekusi UI menampilkan pratinjau dampaknya dan meminta konfirmasi.
- Authoring (PDFBox worker): isi form (teks, checkbox, radio, combo) dan anotasi (sorot, garis bawah, catatan, teks bebas) dengan appearance; perubahan menambah revisi dokumen dan renderer dimuat ulang.
- Batal job, error berkas terkunci, konfirmasi perubahan belum disimpan saat mengganti dokumen/menutup jendela.

### Pengukuran build release lokal (2026-10-22)

| Metrik | Nilai | Cara ukur |
|---|---|---|
| Ukuran aplikasi | exe 10,9 MB · pdfium.dll 6,9 MB · worker 3,7 MB (total dibawa ≈ 21,5 MB) | `scripts/measure-release.ps1` |
| Startup | UI siap median **481 ms** (n=5); halaman pertama selesai dirender median **677 ms** | Stopwatch + UI Automation |
| Memori | process tree 7 proses (1 app + 6 WebView2): WorkingSet jumlah 401 MB (batas atas, halaman berbagi), Private total **178,7 MB** | `Win32_Process` setelah idle |
| Runtime eksternal | Java 278 MB (**tidak dibawa**, dev saja) · WebView2 155.0.4283.62 (komponen OS, tidak dihitung) | registry + disk |
| Installer | **belum ada** (`bundle.active=false`); yang ada hanya build release lokal + staging | — |

---

## Hasil spike & pembandingan (2026-10-21)

Ringkasan: `experiments/restart/results/SUMMARY.md` §9 (tabel per engine + klasifikasi kegagalan) ·
provenance: `experiments/restart/deps/PROVENANCE.md` §1–7 (PDFium, PDFBox, Bouncy Castle) ·
fixture: `experiments/restart/fixtures/FIXTURES.md` v2.

| Test | PDFium | MuPDF | PDFBox |
|---|---|---|---|
| RS-02 anotasi (AP + terlihat di 2 engine) | 0/10 | 14/14 | 13/14 |
| RS-03 isi form (7 pemeriksaan) | 1/7 | 7/7 | 7/7 |
| RS-04 buat field | tanpa API | PASS | PASS |
| RS-05 merge | PASS | PASS | PASS |
| RS-05 extract (struktur) | hilang | PASS | perlu pemangkasan outline |
| RS-07 redaksi | tanpa API | PASS (nilai field lama masih ada di AP) | tanpa API |
| RS-08 signature | baca saja | API level rendah (tak diuji) | bukti minimal, sertifikat uji self-signed |

## Blocker & yang tertunda

- ~~B-RT1~~ runtime Java untuk distribusi → **selesai**: runtime image Temurin 17 (jlink) 53,1 MB
  dibundel (ADR-003). Fallback Java eksternal hanya di build debug.
- **Redaksi** ditunda (instruksi pengguna): fixture `rs07_redact.pdf` + temuan "nilai field lama
  masih ada di appearance stream" tetap sebagai test gagal yang harus diselesaikan sebelum klaim
  *secure redaction*.
- **Teks RTL** dari PDFium masih urutan visual (reordering bidi belum ada).
- **Installer** NSIS sudah dibangun (43,2 MB) tetapi **belum dijalankan** (di luar izin instalasi);
  strategi WebView2: memakai runtime WebView2 yang sudah ada di OS (bukan dibundel) — perlu
 internet hanya bila OS belum memilikinya.
