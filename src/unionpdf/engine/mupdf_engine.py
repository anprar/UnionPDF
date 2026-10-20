"""Implementasi engine PDF berbasis MuPDF (PyMuPDF).

Catatan versi (lihat docs/REA_LIMITATIONS.md L-08):
  - API widget form adalah ``Page.add_widget`` (bukan ``insert_widget``).
  - API ukuran font widget adalah ``Widget.text_fontsize``.

Thread safety: objek ``pymupdf.Document`` TIDAK thread-safe. Instans engine
diciarkan per-thread; pemanggil bertanggung jawab untuk tidak memakai satu
handle dari dua thread sekaligus.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from unionpdf.domain.document import PageOperation, PageOperationKind
from unionpdf.domain.errors import (
    DocumentError,
    PermissionDeniedError,
    VerificationError,
)
from unionpdf.engine.protocol import (
    RenderedPage,
    SearchHit,
    VerificationResult,
    WriteReport,
)

MIN_ZOOM = 0.1
MAX_ZOOM = 10.0


class MupdfDocumentEngine:
    """Adapter MuPDF untuk :class:`unionpdf.engine.protocol.DocumentEngine`."""

    name = "mupdf"

    def __init__(self) -> None:
        self._version = pymupdf.__version__

    # ------------------------------------------------------------------ open
    def open(self, path: Path) -> pymupdf.Document:
        path = Path(path)
        if not path.exists():
            raise DocumentError(f"Berkas tidak ditemukan: {path}")
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001
            raise DocumentError(f"Gagal membuka dokumen: {exc}") from exc

        if doc.needs_pass:
            # Prompt password ditangani lapisan UI, bukan engine.
            raise PermissionDeniedError(
                "Dokumen dilindungi password. Gunakan fitur buka dengan password."
            )
        if doc.page_count == 0:
            doc.close()
            raise DocumentError("Dokumen tidak memiliki halaman.")
        return doc

    def close(self, handle: object) -> None:
        if isinstance(handle, pymupdf.Document):
            try:
                handle.close()
            except Exception:  # noqa: BLE001, S110
                pass

    # ------------------------------------------------------------------ info
    def page_count(self, handle: object) -> int:
        self._require(handle)
        return handle.page_count

    def document_info(self, handle: object) -> dict[str, object]:
        self._require(handle)
        meta = handle.metadata or {}
        has_text = False
        for index in range(min(handle.page_count, 3)):
            if handle[index].get_text("text").strip():
                has_text = True
                break
        return {
            "page_count": handle.page_count,
            "title": meta.get("title") or "",
            "author": meta.get("author") or "",
            "producer": meta.get("producer") or "",
            "creator": meta.get("creator") or "",
            "subject": meta.get("subject") or "",
            "keywords": meta.get("keywords") or "",
            "encrypted": bool(handle.is_encrypted),
            "has_text_layer": has_text,
            "engine_version": self._version,
        }

    # --------------------------------------------------------------- rendering
    def render_page(self, handle: object, index: int, zoom: float) -> RenderedPage:
        self._require(handle)
        if not 0 <= index < handle.page_count:
            raise IndexError(f"indeks halaman di luar jangkauan: {index}")
        zoom = max(MIN_ZOOM, min(MAX_ZOOM, float(zoom)))
        page = handle[index]
        matrix = pymupdf.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        return RenderedPage(
            png_bytes=pixmap.tobytes("png"),
            width_px=pixmap.width,
            height_px=pixmap.height,
            width_pt=float(page.rect.width),
            height_pt=float(page.rect.height),
        )

    # ------------------------------------------------------------------- text
    def extract_text(self, handle: object, index: int) -> str:
        self._require(handle)
        if not 0 <= index < handle.page_count:
            raise IndexError(f"indeks halaman di luar jangkauan: {index}")
        return handle[index].get_text("text")

    def search(self, handle: object, query: str) -> list[SearchHit]:
        self._require(handle)
        if not query.strip():
            return []
        hits: list[SearchHit] = []
        for index in range(handle.page_count):
            for rect in handle[index].search_for(query):
                hits.append(
                    SearchHit(
                        page_index=index,
                        rect=(rect.x0, rect.y0, rect.x1, rect.y1),
                    )
                )
        return hits

    # ------------------------------------------------------------- operations
    def apply_page_operations(
        self, handle: object, operations: list[PageOperation]
    ) -> pymupdf.Document:
        """Terapkan operasi pada salinan dokumen, kembalikan handle baru."""
        self._require(handle)
        result = pymupdf.open()
        try:
            for operation in operations:
                self._apply_single(result, handle, operation)
            if result.page_count == 0:
                raise VerificationError("Operasi menghasilkan dokumen tanpa halaman.")
        except Exception:
            result.close()
            raise
        return result

    def _apply_single(
        self,
        target: pymupdf.Document,
        source: pymupdf.Document,
        operation: PageOperation,
    ) -> None:
        """Terapkan satu operasi.

        Semantik:
          ROTATE   -> semua halaman dipertahankan, halaman terpilih dirotasi.
          DELETE   -> halaman terpilih dibuang, sisanya dipertahankan.
          DUPLICATE-> semua halaman dipertahankan + salinan halaman terpilih.
          EXTRACT  -> hanya halaman terpilih yang dipertahankan.
          REORDER  -> semua halaman dipertahankan dengan urutan baru.

        Dokumen ``source`` tidak pernah dimutasi; rotasi diterapkan pada
        dokumen hasil (``target``).
        """
        kind = operation.kind
        source_count = source.page_count

        if kind is PageOperationKind.ROTATE:
            target.insert_pdf(source)
            for index in operation.page_indices:
                if 0 <= index < target.page_count:
                    page = target[index]
                    page.set_rotation((page.rotation + operation.rotation_delta) % 360)

        elif kind is PageOperationKind.DELETE:
            removed = set(operation.page_indices)
            for index in range(source_count):
                if index not in removed:
                    target.insert_pdf(source, from_page=index, to_page=index)

        elif kind is PageOperationKind.DUPLICATE:
            target.insert_pdf(source)
            for index in operation.page_indices:
                if 0 <= index < source_count:
                    target.insert_pdf(source, from_page=index, to_page=index)

        elif kind is PageOperationKind.EXTRACT:
            for index in operation.page_indices:
                if 0 <= index < source_count:
                    target.insert_pdf(source, from_page=index, to_page=index)

        elif kind is PageOperationKind.REORDER:
            order = operation.destination_order or operation.page_indices
            for index in order:
                if 0 <= index < source_count:
                    target.insert_pdf(source, from_page=index, to_page=index)

        else:  # pragma: no cover - enum tertutup
            raise ValueError(f"Operasi halaman tidak dikenal: {kind}")

    def merge(self, handles: list[object]) -> pymupdf.Document:
        self._require(handles[0] if handles else None)
        merged = pymupdf.open()
        try:
            for handle in handles:
                self._require(handle)
                merged.insert_pdf(handle)
        except Exception:
            merged.close()
            raise
        return merged

    # ------------------------------------------------------------------ write
    def write(
        self,
        handle: object,
        destination: Path,
        *,
        expected_pages: int | None = None,
        garbage: int = 3,
        deflate: bool = True,
    ) -> WriteReport:
        """Tulis dokumen ke disk, lalu verifikasi hasilnya dengan membuka ulang."""
        self._require(handle)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            handle.save(str(destination), garbage=garbage, deflate=deflate)
        except PermissionError as exc:
            raise PermissionDeniedError(
                f"Tidak ada izin menulis ke {destination}: {exc}"
            ) from exc
        except OSError as exc:
            raise PermissionDeniedError(f"Gagal menulis {destination}: {exc}") from exc

        verification = self._verify(destination, expected_pages)
        return WriteReport(
            destination=destination,
            page_count=verification.page_count_actual,
            bytes_written=destination.stat().st_size,
            verification=verification,
        )

    def _verify(self, path: Path, expected_pages: int | None) -> VerificationResult:
        try:
            reopened = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001
            return VerificationResult(
                page_count_expected=expected_pages or 0,
                page_count_actual=0,
                passed=False,
                notes=[f"Output tidak bisa dibuka ulang: {exc}"],
            )
        try:
            actual = reopened.page_count
            expected = expected_pages if expected_pages is not None else actual
            first_text = reopened[0].get_text("text").strip()[:120] if actual else ""
            passed = actual == expected
            notes = [] if passed else [f"Jumlah halaman tidak sesuai: {actual} != {expected}"]
            return VerificationResult(
                page_count_expected=expected,
                page_count_actual=actual,
                first_page_text=first_text,
                passed=passed,
                notes=notes,
            )
        finally:
            reopened.close()

    # ------------------------------------------------------------------ misc
    @staticmethod
    def _require(handle: object) -> None:
        if not isinstance(handle, pymupdf.Document):
            raise TypeError("handle bukan dokumen MuPDF")
