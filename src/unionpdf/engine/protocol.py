"""Kontrak engine PDF.

Seluruh akses ke engine PDF harus lewat interface di modul ini, agar engine
(MuPDF sekarang) dapat diganti tanpa menyentuh domain atau UI.
Lihat docs/ARCHITECTURE.md §2.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from unionpdf.domain.document import PageOperation
from unionpdf.domain.errors import EngineError


@dataclass(frozen=True, slots=True)
class RenderedPage:
    """Hasil render satu halaman."""

    png_bytes: bytes
    width_px: int
    height_px: int
    width_pt: float
    height_pt: float


@dataclass(frozen=True, slots=True)
class SearchHit:
    """Satu hasil pencarian teks."""

    page_index: int
    rect: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Hasil verifikasi output tertulis."""

    page_count_expected: int
    page_count_actual: int
    first_page_text: str = ""
    passed: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class WriteReport:
    """Laporan satu operasi tulis ke disk."""

    destination: Path
    page_count: int
    bytes_written: int
    verification: VerificationResult
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class DocumentEngine(Protocol):
    """Operasi tingkat dokumen yang dibutuhkan UnionPDF."""

    name: str

    def open(self, path: Path) -> object:
        """Buka dokumen dan kembalikan handle opaque milik engine."""

    def close(self, handle: object) -> None:
        """Tutup handle dan lepaskan sumber daya."""

    def page_count(self, handle: object) -> int: ...

    def document_info(self, handle: object) -> dict[str, object]: ...

    def render_page(self, handle: object, index: int, zoom: float) -> RenderedPage: ...

    def extract_text(self, handle: object, index: int) -> str: ...

    def search(self, handle: object, query: str) -> list[SearchHit]: ...

    def apply_page_operations(
        self, handle: object, operations: list[PageOperation]
    ) -> object:
        """Kembalikan handle **baru**; handle lama tidak dimodifikasi."""

    def merge(self, handles: list[object]) -> object: ...

    def write(
        self,
        handle: object,
        destination: Path,
        *,
        expected_pages: int | None = None,
        garbage: int = 3,
        deflate: bool = True,
    ) -> WriteReport: ...


class EngineNotAvailableError(EngineError):
    """Engine tidak tersedia di lingkungan ini."""
