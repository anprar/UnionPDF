"""Fixture pytest untuk UnionPDF.

Semua dokumen PDF yang dipakai adalah **sintetis** — dibuat di sini, bukan
diunduh dan tidak berisi data pengguna. Lihat docs/TEST_PLAN.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pymupdf
import pytest

# Pastikan paket sumber dapat diimpor meski pytest dijalankan dari root.
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# UI test berjalan tanpa display.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _build_pdf(path: Path, pages: int = 5, secret: str | None = None) -> Path:
    doc = pymupdf.open()
    sizes = [(595, 842), (842, 595), (612, 792)]
    for index in range(pages):
        width, height = sizes[index % len(sizes)]
        page = doc.new_page(width=width, height=height)
        page.insert_text((72, 90), f"Halaman {index + 1}", fontsize=18, fontname="helv")
        page.insert_text(
            (72, 130),
            "Teks publik yang harus tetap ada setelah operasi.",
            fontsize=11,
            fontname="helv",
        )
        if secret and index == 0:
            page.insert_text((72, 300), secret, fontsize=12, fontname="helv")
    doc.save(path)
    doc.close()
    return path


@pytest.fixture(scope="session")
def fixture_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("unionpdf_fixtures")


@pytest.fixture
def simple_pdf(fixture_dir: Path) -> Path:
    """PDF 5 halaman dengan text layer, ukuran halaman campuran."""
    return _build_pdf(fixture_dir / "simple.pdf", pages=5)


@pytest.fixture
def single_page_pdf(fixture_dir: Path) -> Path:
    return _build_pdf(fixture_dir / "single.pdf", pages=1)


@pytest.fixture
def secret_pdf(fixture_dir: Path) -> Path:
    """PDF berisi satu string rahasia di halaman pertama."""
    return _build_pdf(fixture_dir / "secret.pdf", pages=2, secret="RAHASIA-12345")


@pytest.fixture
def large_pdf(fixture_dir: Path) -> Path:
    """PDF 120 halaman untuk uji performa ringan."""
    return _build_pdf(fixture_dir / "large.pdf", pages=120)


@pytest.fixture
def encrypted_pdf(fixture_dir: Path) -> Path:
    """PDF terenkripsi AES-256 dengan password pengguna 'user123'."""
    source = _build_pdf(fixture_dir / "enc_src.pdf", pages=2)
    doc = pymupdf.open(source)
    target = fixture_dir / "encrypted.pdf"
    doc.save(
        str(target),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner456",
        user_pw="user123",
    )
    doc.close()
    return target


@pytest.fixture
def corrupt_pdf(fixture_dir: Path) -> Path:
    """Berkas yang bukan PDF valid."""
    path = fixture_dir / "corrupt.pdf"
    path.write_bytes(b"%PDF-1.7\nthis is not a real pdf body\n")
    return path
