# CLEANUP_PLAN.md — Rencana Pengamanan & Cleanup (Proposal)

| Field | Nilai |
|---|---|
| Status | **PROPOSAL — BELUM DISETUJUI** |
| Sesi | `2026-10-21T1057+0700` |
| Jadwal | Pengamanan (Fase 1) kapan saja setelah disetujui; arsip & cleanup (Fase 2–3) **hanya setelah keputusan baseline dan spike P0** |
| Dieksekusi | **Tidak ada.** Tidak satu file pun dipindah, disalin, atau dihapus |

Semua perintah di dokumen ini adalah **rancangan**. Sebelum eksekusi, path wajib dicek
ulang terhadap kondisi workspace saat itu.

---

## 1. Prinsip

1. Implementasi lama (`src/`, `tests/`, `spikes/`) **dipertahankan** sampai baseline
   dipilih dan spike kandidat selesai — ia benchmark dan fallback.
2. Arsipkan dulu, jangan hapus permanen. Hapus sumber hanya setelah salinan
   terverifikasi (jumlah file + SHA-256).
3. Tidak ada wildcard luas, tidak ada `git add -A` / `git add .`, tidak ada
   `git reset --hard`, `git clean -fd`, penghapusan `.git`, atau penghapusan cache global.
4. Korpus `docs/research/` dan snapshot REA **tidak pernah** diunggah, termasuk ke
   layanan backup daring, tanpa izin eksplisit terpisah.
5. Setiap fase butuh persetujuan sendiri.

---

## 2. Fase

### Fase 0 — sekarang
Tidak ada tindakan.

### Fase 1 — Pengamanan 13 file yang belum di-commit (butuh persetujuan C-1)

> **Status 2026-10-21:** opsi 1a **dilaksanakan** atas persetujuan A-5 — commit lokal
> `2a1718a` (24 file: 13 file pra-restart + dokumen audit/review/koreksi yang disetujui),
> stage per file, tidak di-push. Opsi 1b (backup independen) **belum** — lokasi belum dipilih
> pengguna; commit lokal **bukan** backup independen.

**Prasyarat sebelum commit apa pun:**

| # | Prasyarat | Alasan | Butuh izin tulis |
|---|---|---|---|
| 1 | ~~Samarkan project token PostHog pihak ketiga di `docs/ANALYSIS_STIRLING_PDF.md`~~ — **selesai** 2026-10-21 (A-3); sidik SHA-256 dicatat. Klasifikasi: project token (boleh publik menurut dok resmi PostHog), bukan personal API key | Commit menyimpan isi selamanya di histori | — |
| 2 | ~~Perlakuan path lokal~~ — **selesai**: disamarkan menjadi `<USERPROFILE>` (A-3) | Data lingkungan pribadi | — |
| 3 | ~~Perbaiki defek `docs/TASKS.md`~~ — **selesai** (A-4) | Hindari mengabadikan defek | — |

**Opsi 1a — commit lokal per-file (tanpa push).** Rancangan perintah, satu path per
baris, tanpa wildcard:

```powershell
# BELUM DIJALANKAN — rancangan
git add -- "docs/HANDOFF.md"
git add -- "docs/PROJECT_STATE.md"
git add -- "docs/SESSION_LOG.md"
git add -- "docs/TASKS.md"
git add -- "docs/ANALYSIS_NITRO14.md"
git add -- "docs/ANALYSIS_STIRLING_PDF.md"
git add -- "docs/ANALYSIS_PDFGEAR.md"
git add -- "docs/sessions/2026-10-21T0851+0700.md"
git add -- "docs/sessions/2026-10-21T0932+0700.md"
git add -- "docs/sessions/2026-10-21T1000+0700.md"
git add -- "scripts/verify_analysis_corpus.py"
git add -- "scripts/verify_stirling_artifact.py"
git add -- "scripts/verify_pdfgear_artifact.py"
git diff --cached --stat        # ditinjau sebelum commit
# commit hanya bila disetujui; push TIDAK termasuk
```

Dokumen yang dibuat/diubah pada sesi `2026-10-21T1057+0700` (`RESTART_AUDIT.md`,
`CLEANUP_PLAN.md`, `POST_ALL_REFERENCES_TECH_REVIEW.md`, `STACK_EVALUATION.md`,
`FEATURE_MATRIX.md`, `TECH_SPIKES.md`, `PROJECT_STATE.md`, `HANDOFF.md`, session log
baru) **tidak** termasuk 13 file di atas dan butuh daftar commit tersendiri.

**Opsi 1b — backup independen (tanpa commit).** Salin 13 file + 3 snapshot REA ke lokasi
**di luar disk kerja** yang dipilih pengguna (disk lain/media eksternal), dengan manifest
SHA-256. Lokasi belum ditentukan → butuh keputusan pengguna. Opsi 1a dan 1b dapat
digabung.

### Fase 2 — Arsip implementasi lama (butuh persetujuan C-2; hanya setelah keputusan baseline + spike P0)

Bila baseline C dipilih, sebagian kode Python lama mungkin dipakai ulang sebagai worker;
pada kasus itu daftar target ditinjau ulang.

| Target (relatif ke workspace) | Isi terverifikasi 2026-10-21 | Tracked | Aksi usulan |
|---|---|---|---|
| `src/` | 40 file, 156 KB (20 modul `.py` + cache) | ya (commit `336538a`) | arsip → hapus sumber setelah verifikasi |
| `tests/` | 12 file, 130 KB | ya | idem |
| `spikes/*.py` | 5 skrip | ya | idem |
| `spikes/out/` | hasil JSON/PNG/PDF S1–S12 (**bukti benchmark**) | tidak (gitignored) | **arsip**, bukan hapus |
| `spikes/fixtures/` | 4 fixture sintetis | tidak (gitignored) | arsip |
| `requirements.txt`, `requirements-dev.txt`, `pytest.ini` | konfigurasi stack lama | ya | arsip → hapus sumber |
| `scripts/smoke_app.py`, `scripts/run.ps1`, `scripts/setup.ps1`, `scripts/test.ps1`, `scripts/run_spikes.ps1` | runner stack lama | ya | arsip → hapus sumber |

Tetap di tempat: `scripts/verify_*.py`, `scripts/lint.py`, `scripts/repair_docs.py`,
5 skrip ekstraksi REA, seluruh `docs/`, `LICENSE`, `NOTICE`, `AGENTS.md`, `README.md`.

Lokasi arsip usulan: `_archive/restart-<timestamp>/previous-application/` +
`manifest.json` + `checksums.json`. Penambahan `_archive/` ke `.gitignore` adalah
perubahan file tersendiri yang butuh izin.

**Prosedur (rancangan, belum dijalankan):**

```powershell
# 1) Prapemeriksaan
git status --short -- src tests spikes scripts requirements.txt requirements-dev.txt pytest.ini
Get-ChildItem src,tests,spikes -Recurse -Force -Attributes ReparsePoint   # harus kosong
# 2) Salin dengan struktur relatif; robocopy /XJ = jangan ikuti junction
robocopy src "_archive\restart-<ts>\previous-application\src" /E /COPY:DAT /XJ
# (ulangi per target eksplisit; tidak memakai wildcard pada akar workspace)
# 3) Manifest & verifikasi: jumlah file dan SHA-256 sumber == salinan
# 4) Hanya bila langkah 3 lulus: hapus sumber per target eksplisit
# 5) Verifikasi pasca: dokumen analisis, skrip verifikasi, docs/research masih ada
```

**Rollback:** salin balik dari arsip, atau pulihkan file tracked dari histori Git dengan
perintah restore non-destruktif per path.

### Fase 3 — Cache (butuh persetujuan C-3)

| Target | Aksi usulan |
|---|---|
| `.pytest_cache/` | Hapus (regenerable) — setelah Fase 2 |
| `__pycache__/` di bawah target yang diarsip | Ikut arsip atau dikecualikan dengan alasan tercatat |
| `.venv/` (≈771 MB) | **Pertahankan** sampai stack diputuskan; masih dipakai skrip verifikasi REA dan benchmark |

---

## 3. Arsip lokal vs backup independen

| Aspek | Arsip lokal (`_archive/` di workspace) | Backup independen |
|---|---|---|
| Lokasi | Disk & folder yang sama | Disk/perangkat lain yang dipilih pengguna |
| Melindungi dari | Salah hapus, perubahan struktur | Kerusakan disk, kehilangan mesin, kerusakan workspace |
| Tidak melindungi dari | Kerusakan disk / kehilangan mesin | — |
| Histori Git sebagai pengganti | Hanya untuk file **tracked** dan hanya di mesin ini sampai di-push | — |
| Status | Usulan, belum dibuat | Lokasi belum ditentukan |

Catatan: `docs/research/` (korpus) dan snapshot REA di
`<USERPROFILE>\AppData\Local\Temp\opencode\` **tidak** tercakup histori Git. Snapshot di
folder temp berisiko terhapus oleh pembersihan sistem; perlindungannya hanya lewat
arsip lokal atau backup independen yang disetujui — tidak lewat unggahan.

---

## 4. Keputusan yang dibutuhkan

| ID | Pertanyaan |
|---|---|
| C-1 | Fase 1: opsi 1a, 1b, keduanya, atau tidak sekarang? (termasuk izin memperbaiki 3 prasyarat) |
| C-1b | Bila 1b: lokasi backup independen? |
| C-2 | Fase 2: setujui daftar target **setelah** keputusan baseline? |
| C-3 | Fase 3: setujui penghapusan `.pytest_cache/`? |
