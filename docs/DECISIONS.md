# DECISIONS.md — Indeks Keputusan Arsitektur

Format: ADR (Architecture Decision Record) di `docs/decisions/`.

| ID | Judul | Status | Tanggal | Berkas |
|---|---|---|---|---|
| ADR-001 | Stack baseline UnionPDF | **Accepted** (dengan syarat) | 2026-10-20 | [ADR-001-stack-baseline.md](decisions/ADR-001-stack-baseline.md) |
| ADR-002 | Fondasi controlled restart (Tauri 2 + React/TS + Rust, PDFium renderer, PDFBox authoring awal) | **Accepted** (fondasi; redaksi terbuka) | 2026-10-21 | [ADR-002-restart-foundation.md](decisions/ADR-002-restart-foundation.md) |
| ADR-003 | Runtime Java bundel (jlink) & paket mandiri | **Accepted** | 2026-10-22 | [ADR-003-java-runtime-and-packaging.md](decisions/ADR-003-java-runtime-and-packaging.md) |

---

## Format penulisan ADR

```markdown
# ADR-xxx — Judul

- Status: Proposed | Accepted | Superseded by ADR-xxx
- Tanggal:
- Hormat: (tautan dokumen lain)

## Konteks
## Kandidat yang dinilai
## Keputusan
## Alasan
## Konsekuensi (Positif / Negatif / Yang tidak berubah)
## Implikasi
## Rute cadangan
## Review
```

---

## Pemicu peninjauan ulang keputusan

- Fitur wajib ternyata tidak dapat dipenuhi.
- Risiko integritas dokumen.
- Masalah performa besar.
- Kegagalan packaging.
- Dependency tidak terawat.
- Konflik lisensi.
- Batasan keamanan.
- Biaya baru yang tidak sesuai tujuan.

**Jangan** mengganti seluruh stack bila cukup mengganti adapter atau engine
tertentu. Spesifikasi rendah: perubahan engine → ADR baru (bukan edit diam-diam
atas ADR-001).
