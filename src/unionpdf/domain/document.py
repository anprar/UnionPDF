"""Model domain murni — tidak boleh knowing PySide6 maupun MuPDF."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True, slots=True)
class PageRef:
    """Referensi satu halaman dalam dokumen (indeks 0-based)."""

    index: int

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("index halaman tidak boleh negatif")


@dataclass(frozen=True, slots=True)
class PageRange:
    """Rentang halaman 1-based inklusif, dapat di-open ended."""

    start: int
    end: int | None = None

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("start harus >= 1")
        if self.end is not None and self.end < self.start:
            raise ValueError("end harus >= start")

    def indices(self, page_count: int) -> list[int]:
        """Ubah menjadi daftar indeks 0-based yang valid."""
        if page_count <= 0:
            return []
        end = self.end if self.end is not None else page_count
        end = min(end, page_count)
        return list(range(self.start - 1, end))


class PageOperationKind(str, Enum):
    ROTATE = "rotate"
    DELETE = "delete"
    DUPLICATE = "duplicate"
    REORDER = "reorder"
    EXTRACT = "extract"


@dataclass(frozen=True, slots=True)
class PageOperation:
    """Satu operasi pada sekumpulan halaman."""

    kind: PageOperationKind
    page_indices: tuple[int, ...]
    rotation_delta: int = 0
    destination_order: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.kind is PageOperationKind.ROTATE and self.rotation_delta % 360 == 0:
            raise ValueError("rotasi harus kelipatan 90 yang tidak nol")


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    """Metadata ringkas dokumen untuk UI."""

    path: str
    page_count: int
    title: str = ""
    author: str = ""
    producer: str = ""
    encrypted: bool = False
    has_text_layer: bool = False


@dataclass(slots=True)
class Document:
    """Dokumen terbuka pada level domain.

    Objek ini **tidak** menyimpan handle engine; engine state dikelola terpisah
    oleh :class:`unionpdf.application.session.EditSession`. Pemisahan ini
    menjaga domain tetap murni dan bisa diuji tanpa MuPDF.
    """

    info: DocumentInfo
    _pages: list[PageRef] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self._pages)

    @property
    def pages(self) -> tuple[PageRef, ...]:
        return tuple(self._pages)

    def page_at(self, index: int) -> PageRef:
        if not 0 <= index < len(self._pages):
            raise IndexError(f"indeks halaman di luar jangkauan: {index}")
        return self._pages[index]
