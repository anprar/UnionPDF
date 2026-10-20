"""Unit test lapisan domain (murni, tanpa engine maupun GUI)."""

from __future__ import annotations

import pytest

from unionpdf.domain.document import (
    Document,
    DocumentInfo,
    PageOperation,
    PageOperationKind,
    PageRange,
    PageRef,
)
from unionpdf.domain.errors import (
    DiskFullError,
    DocumentError,
    OperationCancelled,
    UnionPdfError,
    VerificationError,
)


class TestPageRange:
    def test_open_ended_range(self) -> None:
        assert PageRange(1).indices(5) == [0, 1, 2, 3, 4]

    def test_closed_range_is_inclusive(self) -> None:
        assert PageRange(2, 4).indices(10) == [1, 2, 3]

    def test_range_clipped_to_page_count(self) -> None:
        assert PageRange(3, 99).indices(5) == [2, 3, 4]

    def test_range_beyond_document_is_empty(self) -> None:
        assert PageRange(10, 12).indices(5) == []

    def test_zero_document_yields_empty(self) -> None:
        assert PageRange(1).indices(0) == []

    def test_start_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            PageRange(0)

    def test_end_before_start_rejected(self) -> None:
        with pytest.raises(ValueError):
            PageRange(5, 2)


class TestPageOperation:
    def test_rotation_must_be_nonzero_multiple_of_90(self) -> None:
        with pytest.raises(ValueError):
            PageOperation(kind=PageOperationKind.ROTATE, page_indices=(0,), rotation_delta=0)

    def test_valid_rotation(self) -> None:
        op = PageOperation(
            kind=PageOperationKind.ROTATE, page_indices=(0, 1), rotation_delta=90
        )
        assert op.rotation_delta == 90

    def test_negative_page_index_rejected(self) -> None:
        with pytest.raises(ValueError):
            PageRef(-1)


class TestDocument:
    def test_page_count_reflects_pages(self) -> None:
        doc = Document(info=DocumentInfo(path="x.pdf", page_count=2))
        doc._pages = [PageRef(0), PageRef(1)]
        assert doc.page_count == 2
        assert doc.page_at(1).index == 1

    def test_page_out_of_range_raises(self) -> None:
        doc = Document(info=DocumentInfo(path="x.pdf", page_count=1))
        doc._pages = [PageRef(0)]
        with pytest.raises(IndexError):
            doc.page_at(5)


class TestErrorHierarchy:
    @pytest.mark.parametrize(
        "error_cls",
        [DocumentError, DiskFullError, OperationCancelled, VerificationError],
    )
    def test_all_inherit_base(self, error_cls: type) -> None:
        assert issubclass(error_cls, UnionPdfError)
