# START_HERE.md — Peta Dokumen & Urutan Baca

**Selamat datang di UnionPDF.** Baca file ini dulu.

---

## 1. Ringkasan proyek

UnionPDF adalah aplikasi **desktop Windows** untuk pengolahan PDF: melihat,
mengedit, menganotasi, mengisi form, mengoptimasi, dan menandatangani dokumen
PDF.

- **Gratis**, tanpa paywall untuk fitur yang sudah diimplementasikan
- **Tanpa watermark** pada hasil ekspor
- **Offline-first** — pemrosesan lokal, tidak ada unggah dokumen
- **Implementasi independen** — tidak memakai engine atau aset aplikasi referensi

Aplikasi referensi: **Nitro PDF Pro 14.41.0.15** (read-only, di
`C:\Program Files\Nitro\PDF Pro\14`). Dipakai sebagai sumber **kebutuhan**,
bukan sebagai dependency.

**Stack:** Python 3.13 · PySide6 6.11 · MuPDF 1.27 (PyMuPDF) · Windows OCR.
Keputusan: `docs/decisions/ADR-001-stack-baseline.md`.

---

## 2. Peta dokumen

### Orientasi
| Dokumen | Isi |
|---|---|
| `AGENTS.md` | Instruksi permanen agent (baca **pertama**) |
| `docs/PROJECT_STATE.md` | Status **saat ini** (bukan riwayat) |
| `docs/HANDOFF.md` | Posisi kerja untuk sesi berikutnya |
| `docs/TASKS.md` | Backlog `UPDF-xxx` |
| `docs/SESSION_LOG.md` | Indeks sesi |
| `docs/COMMAND_LOG.md` | Indeks perintah |
| `docs/DECISIONS.md` | Indeks ADR |

### Produk & kebutuhan
| Dokumen | Isi |
|---|---|
| `docs/PRODUCT_VISION.md` | Untuk siapa, prinsip produk, batas |
| `docs/REQUIREMENTS.md` | Kebutuhan fungsional & non-fungsional |
| `docs/FEATURE_MATRIX.md` | 97 fitur: referensi → keputusan UnionPDF |
| `docs/MODERNIZATION_PLAN.md` | Apa yang UnionPDF buat lebih baik |

### Analisis referensi
| Dokumen | Isi |
|---|---|
| `docs/REA_FINDINGS.md` | Temuan analisis aplikasi referensi |
| `docs/REA_LIMITATIONS.md` | **Apa yang tidak boleh disimpulkan** |
| `docs/EVIDENCE_INDEX.md` | Indeks bukti `E-0xx` … `E-3xx` |

### Teknologi
| Dokumen | Isi |
|---|---|
| `docs/POST_REA_TECH_REVIEW.md` | **Gate** review teknologi pasca-REA |
| `docs/STACK_EVALUATION.md` | Perbandingan 4 kandidat berbobot |
| `docs/TECH_SPIKES.md` | Hasil spike S1–S12 (terukur) |
| `docs/ARCHITECTURE.md` | Lapisan, kontrak, struktur direktori |
| `docs/DEPENDENCIES.md` | Dependency + versi + lisensi |
| `docs/LICENSE_REVIEW.md` | Audit lisensi (AGPL-3.0) |
| `docs/UPGRADE_POLICY.md` | Cara menaikkan dependency |

### Operasional
| Dokumen | Isi |
|---|---|
| `docs/BUILD_AND_RUN.md` | Setup, run, test |
| `docs/PACKAGING.md` | Rencana build EXE |
| `docs/TEST_PLAN.md` | Cakupan & fixture |
| `docs/TEST_RESULTS.md` | Hasil uji terakhir |
| `docs/SECURITY.md` | Prinsip keamanan dokumen |
| `docs/KNOWN_ISSUES.md` | Bugs & keterbatasan yang diketahui |
| `docs/BLOCKERS.md` | Yang butuh keputusan pengguna |
| `docs/ASSUMPTIONS.md` | Asumsi yang belum diverifikasi |
| `docs/ROADMAP.md` | Milestone M0–M12 |
| `docs/CHANGELOG.md` | Riwayat perubahan |

---

## 3. Urutan baca sesi baru

1. `AGENTS.md`
2. `docs/START_HERE.md` (file ini)
3. `docs/PROJECT_STATE.md`
4. `docs/HANDOFF.md`
5. `docs/TASKS.md` → task berstatus `IN_PROGRESS`
6. `docs/BLOCKERS.md`
7. `docs/DECISIONS.md` + ADR terkait
8. `docs/sessions/<terbaru>.md` bila perlu detail

---

## 4. Checkpoint terakhir

| Item | Nilai |
|---|---|
| Sesi | `2026-10-20T1700+0700` (lanjutan dari `2026-10-20T1624+0700`) |
| Fase | M0 — Foundation · Fase A (analisis referensi) **v2 selesai** |
| Milestone aktif | M0 |
| Task aktif | `UPDF-012` (Save As → atomic write) |
| Stack | **Diputuskan & dikonfirmasi v2** (ADR-001, skor 463/500) |
| Lisensi proyek | **AGPL-3.0** — open source (`LICENSE` + `NOTICE`) |
| Analisis referensi | 14.452 string UI · 783 kontrol ribbon · 10.284 identifier fitur |
| Test | 55 pytest PASS · smoke app 9/9 PASS · lint 0 temuan |
| Blocker aktif | B-03 (ukuran) · B-04 (edit teks) · B-05 (bahasa OCR) |

---

## 5. Perintah penting

```powershell
.\scripts\setup.ps1      # buat venv + pasang dependensi
.\scripts\run.ps1        # jalankan aplikasi
.\scripts\test.ps1       # jalankan test suite
.\scripts\run_spikes.ps1 # jalankan technical spike
.\scripts\smoke_app.py   # verifikasi aplikasi jalan
.\.venv\Scripts\python.exe scripts\lint.py   # linter workspace
```

---

## 6. Aturan singkat

- Bahasa dokumen: **Indonesia**. Bahasa kode: **Inggris**.
- **Jangan** kunci stack lagi tanpa ADR baru.
- **Jangan** tandai task `DONE` hanya karena kodenya ada.
- **Jangan** mengubah `NOT_RUN` menjadi `PASS`.
- Operation panjang harus di luar thread UI, dengan progress + cancel.
- Kalau tidak yakin, tulis `UNKNOWN` / `NOT_MEASURED` — jangan mengarang.
