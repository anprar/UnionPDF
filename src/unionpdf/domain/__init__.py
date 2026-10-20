"""Domain UnionPDF (model murni, tanpa engine maupun GUI)."""

from __future__ import annotations

from .document import (
    Document,
    DocumentInfo,
    PageOperation,
    PageOperationKind,
    PageRange,
    PageRef,
)
from .errors import (
    DiskFullError,
    DocumentError,
    EngineError,
    OperationCancelled,
    PermissionDeniedError,
    UnionPdfError,
    VerificationError,
)

__all__ = [
    "DiskFullError",
    "Document",
    "DocumentError",
    "DocumentInfo",
    "EngineError",
    "OperationCancelled",
    "PageOperation",
    "PageOperationKind",
    "PageRange",
    "PageRef",
    "PermissionDeniedError",
    "UnionPdfError",
    "VerificationError",
]
