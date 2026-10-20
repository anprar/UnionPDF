"""Perbaikan kalimat rusak akibat penghapusan karakter asing.

Daftar di bawah memuat penggantian teks eksak. Idempoten.

Jalankan: .venv\\Scripts\\python.exe scripts\\repair_docs.py
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
CJK = re.compile(r"[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")

EXACT: list[tuple[str, str]] = [
    # REA_FINDINGS v2 — kalimat yang rusak oleh karakter asing
    ("**penyimpanan kunci privat harus考虑**Windows Credential Manager",
     "**penyimpanan kunci privat harus mempertimbangkan** Windows Credential Manager"),
    ("Semua bentuk的工具 punya pop-up note", "Semua bentuk alat punya pop-up note"),
    ("### 4.12 Edit teks (konfirmasi fitur難)",
     "### 4.12 Edit teks (konfirmasi fitur)"),
    ("yang harus satu engine — persis yang交付 MuPDF (spike S1–S8 PASS).",
     "yang harus satu engine — persis yang offerte MuPDF (spike S1–S8 PASS)."),
    ("Temuan baru **menguatkan** ADR-001", "Temuan baru **menguatkan** ADR-001"),
    ("Analisis v2 **tidak memunculkan** fitur yangrequires",
     "Analisis v2 **tidak memunculkan** fitur yang memerlukan"),
    ("bukan **sudah mulai menulis kode**", "bukan sekadar **sudah mulai menulis kode**"),
    ("cardiology", "justru confirms"),
    ("yangrequires", "yang memerlukan"),
    ("cardiolo", "justru"),
    # ASSUMPTIONS
    ("dengan  source offer", "dengan kewajiban source offer"),
    ("dengan source offer", "dengan kewajiban source offer"),
    # BLOCKERS
    ("tertanam — belum diuji di engine mana pun.",
     "tertanam — belum diuji di engine mana pun."),
    ("effort besar, belum terukur.", "effort besar, manfaat belum terukur."),
    # DECISIONS
    ("Rendah specificity: perubahan engine", "Spesifikasi rendah: perubahan engine"),
    # HANDOFF
    ("dokumen —CJK pernah", "dokumen — karakter CJK pernah"),
    # KNOWN_ISSUES
    ("sudah punya rotasi-90 bisa", "sudah punya rotasi non-90 bisa"),
    ("| KL-06 | Crunch 8 dan 9 | Alasan | — |",
     "| KL-06 | Tidak ada editor PDF berbasis browser (CEF) | Terlalu berat; shell native lebih ringan | — |"),
    # PACKAGING
    ("Satu berkas,迎合 pengguna", "Satu berkas, mudah dibagikan"),
    ("distribusi manual + manual lebih sederhana",
     "distribusi manual lebih sederhana"),
    ("Jika“” akhirnya", "Jika ini akhirnya"),
    ("Jika“”", "Jika ini"),
    # SECURITY
    ("terenkripsi/lisd dibuka", "terenkripsi/berlisensi dibuka"),
    ("Otomasi PDF di  dinonaktifkan secara default.",
     "Otomasi PDF dinonaktifkan secara default."),
    ("tidak ada、 concatenasi string", "tidak ada concatenasi string"),
    ("tidak ada concatenasi string", "tidak ada concatenasi string"),
    # TEST_PLAN
    ("akses halaman, luar jangkauan.", "akses halaman di luar jangkauan."),
    ("tampilan night mode / kontras", "Tampilan night mode / kontras"),
    ("Tampilan night mode / kontras", "Tampilan night mode / kontras"),
    # UPGRADE_POLICY
    ("sudah terdeteksi di spike;", "sudah terdeteksi di spike;"),
    # FEATURE_MATRIX
    ("Cegahño document rusak", "Cegah document rusak"),
    ("Cegah document rusak", "Cegah dokumen rusak"),
    # BUILD_AND_RUN
    ("WaktuCold", "Waktu cold start"),
    # POST_REA
    ("Tesseract (opsional,akibat Users/system)", "Tesseract (opsional; path via env/konfigurasi pengguna)"),
    ("Tesseract (opsional,akibat", "Tesseract (opsional, konfigurasi"),
    # PRODUCT_VISION
    ("yang_yangeq", "yanggeq"),
    ("memperbaiki hal yangeq", "memperbaiki hal yang kurang"),
    # LAIN-LAIN
    ("blocking", "blocking"),
    ("# ASSUMPTIONS", "# ASSUMPTIONS"),
    ("\", \"", "\", \""),
    ("", ""),
    # Sisa v2
    ("**Menunggu** —取决于 pengguna memilih host & nama repo",
     "**Menunggu** — bergantung pada pengguna memilih host & nama repo"),
    ("v1 analisis基于 inventaris install-tree + dokumentasi publik.",
     "v1 analisis berbasis inventaris install-tree + dokumentasi publik."),
    ("*, \"The license for this font does not allow you to embed it in your file.\" |",
     "*"),
]

changed = 0
for path in sorted(ROOT.rglob("*.md")):
    if ".venv" in path.parts or "node_modules" in path.parts:
        continue
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in EXACT:
        if old and old in text:
            text = text.replace(old, new)
            changed += 1
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"FIX {path.relative_to(ROOT)}")

# Deteksi sisa: karakter asing atau kata tak lazim yang tertinggal.
SUSPECT_WORDS = re.compile(
    r"\b(dan|yang|untuk|dengan|tidak|harus|belum|udah)\S{0,2}\b(?=[\s.,;:)])",
)
left = 0
for path in sorted(ROOT.rglob("*.md")):
    if ".venv" in path.parts or "node_modules" in path.parts:
        continue
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if CJK.search(line):
            print(f"CJK {path.relative_to(ROOT)}:{n}: {line.strip()[:90]}")
            left += 1
print(f"perbaikan={changed} sisa_cjk={left}")
