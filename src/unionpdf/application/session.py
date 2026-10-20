"""Sesi edit: pemilik handle dokumen dan-paper cleanly.

Sesi ini berada di atas engine, di bawah UI. Semua operasi yang mengubah
dokumen harus melalui sini supaya ada satu tempat untuk undo/redo nanti.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from unionpdf.domain.document import Document, DocumentInfo, PageRef
from unionpdf.domain.errors import DocumentError
from unionpdf.engine.protocol import DocumentEngine, RenderedPage, SearchHit


class EditSession:
    """Satu dokumen terbuka."""

    def __init__(self, engine: DocumentEngine, path: Path) -> None:
        self._engine = engine
        self._path = Path(path)
        self._handle: Any = None
        self._document: Document | None = None
        self._dirty = False
        self._undo_stack: list[Any] = []
        self._redo_stack: list[Any] = []

    # ------------------------------------------------------------- lifecycle
    def open(self) -> Document:
        handle = self._engine.open(self._path)
        self._handle = handle
        info = self._engine.document_info(handle)
        page_count = int(info.get("page_count", 0))
        document = Document(
            info=DocumentInfo(
                path=str(self._path),
                page_count=page_count,
                title=str(info.get("title", "")),
                author=str(info.get("author", "")),
                producer=str(info.get("producer", "")),
                encrypted=bool(info.get("encrypted", False)),
                has_text_layer=bool(info.get("has_text_layer", False)),
            )
        )
        document._pages = [PageRef(i) for i in range(page_count)]
        self._document = document
        return document

    def close(self) -> None:
        if self._handle is not None:
            self._engine.close(self._handle)
            self._handle = None
        self._document = None
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._dirty = False

    # -------------------------------------------------------------- accessors
    @property
    def document(self) -> Document:
        if self._document is None:
            raise DocumentError("Tidak ada dokumen terbuka.")
        return self._document

    @property
    def path(self) -> Path:
        return self._path

    @property
    def handle(self) -> Any:
        if self._handle is None:
            raise DocumentError("Tidak ada dokumen terbuka.")
        return self._handle

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    # ------------------------------------------------------------- operations
    def render_page(self, index: int, zoom: float) -> RenderedPage:
        return self._engine.render_page(self.handle, index, zoom)

    def extract_text(self, index: int) -> str:
        return self._engine.extract_text(self.handle, index)

    def search(self, query: str) -> list[SearchHit]:
        return self._engine.search(self.handle, query)

    def mark_dirty(self) -> None:
        self._dirty = True

    def mark_clean(self) -> None:
        self._dirty = False

    def push_undo(self, snapshot: Any) -> None:
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()
        self._dirty = True

    def pop_undo(self) -> Any | None:
        if not self._undo_stack:
            return None
        item = self._undo_stack.pop()
        self._redo_stack.append(item)
        return item

    def pop_redo(self) -> Any | None:
        if not self._redo_stack:
            return None
        item = self._redo_stack.pop()
        self._undo_stack.append(item)
        return item
