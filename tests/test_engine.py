"""Test integrasi engine PDF (MuPDF)."""

from __future__ import annotations

from pathlib import Path

import pytest

from unionpdf.domain.document import PageOperation, PageOperationKind
from unionpdf.domain.errors import DocumentError, PermissionDeniedError
from unionpdf.engine.mupdf_engine import MupdfDocumentEngine


@pytest.fixture
def engine() -> MupdfDocumentEngine:
    return MupdfDocumentEngine()


class TestOpen:
    def test_open_valid_document(self, engine: MupdfDocumentEngine, simple_pdf: Path) -> None:
        handle = engine.open(simple_pdf)
        try:
            assert engine.page_count(handle) == 5
        finally:
            engine.close(handle)

    def test_open_missing_file_raises(self, engine: MupdfDocumentEngine, tmp_path: Path) -> None:
        with pytest.raises(DocumentError):
            engine.open(tmp_path / "tidak_ada.pdf")

    def test_open_corrupt_file_raises(self, engine: MupdfDocumentEngine, corrupt_pdf: Path) -> None:
        with pytest.raises(DocumentError):
            engine.open(corrupt_pdf)

    def test_open_encrypted_raises_permission_error(
        self, engine: MupdfDocumentEngine, encrypted_pdf: Path
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            engine.open(encrypted_pdf)

    def test_document_info(self, engine: MupdfDocumentEngine, simple_pdf: Path) -> None:
        handle = engine.open(simple_pdf)
        try:
            info = engine.document_info(handle)
            assert info["page_count"] == 5
            assert info["has_text_layer"] is True
            assert info["engine_version"]
        finally:
            engine.close(handle)


class TestRender:
    def test_render_returns_expected_geometry(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            page = engine.render_page(handle, 0, 1.0)
            assert page.width_px > 0 and page.height_px > 0
            assert page.png_bytes.startswith(b"\x89PNG")
            # 1.0 zoom -> pixel ≈ point (72 dpi)
            assert abs(page.width_px - page.width_pt) <= 2
        finally:
            engine.close(handle)

    def test_render_scales_with_zoom(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            small = engine.render_page(handle, 0, 0.5)
            large = engine.render_page(handle, 0, 2.0)
            assert large.width_px == pytest.approx(small.width_px * 4, rel=0.05)
        finally:
            engine.close(handle)

    def test_render_out_of_range_raises(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            with pytest.raises(IndexError):
                engine.render_page(handle, 99, 1.0)
        finally:
            engine.close(handle)


class TestTextAndSearch:
    def test_extract_text_contains_content(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            text = engine.extract_text(handle, 0)
            assert "Halaman 1" in text
        finally:
            engine.close(handle)

    def test_search_finds_hits(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            hits = engine.search(handle, "Halaman")
            assert len(hits) == 5
            assert {h.page_index for h in hits} == {0, 1, 2, 3, 4}
        finally:
            engine.close(handle)

    def test_search_empty_query_returns_nothing(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            assert engine.search(handle, "   ") == []
        finally:
            engine.close(handle)


class TestPageOperations:
    def test_rotate_preserves_page_count(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            result = engine.apply_page_operations(
                handle,
                [
                    PageOperation(
                        kind=PageOperationKind.ROTATE, page_indices=(0, 1), rotation_delta=90
                    )
                ],
            )
            try:
                assert result.page_count == 5
                assert result[0].rotation == 90
            finally:
                engine.close(result)
        finally:
            engine.close(handle)

    def test_delete_removes_pages(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            result = engine.apply_page_operations(
                handle,
                [PageOperation(kind=PageOperationKind.DELETE, page_indices=(0, 2))],
            )
            try:
                assert result.page_count == 3
                text = result[0].get_text("text")
                assert "Halaman 2" in text
            finally:
                engine.close(result)
        finally:
            engine.close(handle)

    def test_extract_keeps_only_selected(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            result = engine.apply_page_operations(
                handle,
                [PageOperation(kind=PageOperationKind.EXTRACT, page_indices=(1, 3))],
            )
            try:
                assert result.page_count == 2
                assert "Halaman 2" in result[0].get_text("text")
                assert "Halaman 4" in result[1].get_text("text")
            finally:
                engine.close(result)
        finally:
            engine.close(handle)

    def test_duplicate_increases_count(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            result = engine.apply_page_operations(
                handle,
                [PageOperation(kind=PageOperationKind.DUPLICATE, page_indices=(0,))],
            )
            try:
                assert result.page_count == 6
            finally:
                engine.close(result)
        finally:
            engine.close(handle)

    def test_rotate_does_not_mutate_source(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        """Operasi harus bekerja pada salinan, bukan mengubah dokumen sumber."""
        handle = engine.open(simple_pdf)
        try:
            engine.apply_page_operations(
                handle,
                [PageOperation(kind=PageOperationKind.ROTATE, page_indices=(0,), rotation_delta=90)],
            )
            assert handle[0].rotation == 0
        finally:
            engine.close(handle)

    def test_reorder_changes_page_sequence(
        self, engine: MupdfDocumentEngine, simple_pdf: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            result = engine.apply_page_operations(
                handle,
                [
                    PageOperation(
                        kind=PageOperationKind.REORDER,
                        page_indices=(3, 0, 1, 2, 4),
                        destination_order=(3, 0, 1, 2, 4),
                    )
                ],
            )
            try:
                assert result.page_count == 5
                assert "Halaman 4" in result[0].get_text("text")
                assert "Halaman 1" in result[1].get_text("text")
            finally:
                engine.close(result)
        finally:
            engine.close(handle)

    def test_merge_combines_documents(
        self, engine: MupdfDocumentEngine, simple_pdf: Path, single_page_pdf: Path
    ) -> None:
        first = engine.open(simple_pdf)
        second = engine.open(single_page_pdf)
        try:
            merged = engine.merge([first, second])
            try:
                assert merged.page_count == 6
            finally:
                engine.close(merged)
        finally:
            engine.close(first)
            engine.close(second)


class TestWrite:
    def test_write_and_verify(
        self, engine: MupdfDocumentEngine, simple_pdf: Path, tmp_path: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            target = tmp_path / "out.pdf"
            report = engine.write(handle, target, expected_pages=5)
            assert target.exists()
            assert report.page_count == 5
            assert report.verification.passed
            assert report.bytes_written > 0
        finally:
            engine.close(handle)

    def test_verification_detects_mismatch(
        self, engine: MupdfDocumentEngine, simple_pdf: Path, tmp_path: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            report = engine.write(handle, tmp_path / "out.pdf", expected_pages=99)
            assert not report.verification.passed
            assert report.verification.notes
        finally:
            engine.close(handle)

    def test_write_creates_parent_directory(
        self, engine: MupdfDocumentEngine, simple_pdf: Path, tmp_path: Path
    ) -> None:
        handle = engine.open(simple_pdf)
        try:
            target = tmp_path / "nested" / "deep" / "out.pdf"
            engine.write(handle, target)
            assert target.exists()
        finally:
            engine.close(handle)
