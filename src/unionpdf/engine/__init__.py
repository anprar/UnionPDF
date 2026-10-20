"""Lapisan engine: akses ke backend PDF di balik interface."""

from __future__ import annotations

from .mupdf_engine import MupdfDocumentEngine
from .protocol import (
    DocumentEngine,
    EngineNotAvailableError,
    RenderedPage,
    SearchHit,
    VerificationResult,
    WriteReport,
)

__all__ = [
    "DocumentEngine",
    "EngineNotAvailableError",
    "MupdfDocumentEngine",
    "RenderedPage",
    "SearchHit",
    "VerificationResult",
    "WriteReport",
]
