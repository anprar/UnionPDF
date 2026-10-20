"""Exception bertipe untuk seluruh lapisan UnionPDF."""

from __future__ import annotations


class UnionPdfError(Exception):
    """Basis seluruh error aplikasi."""


class DocumentError(UnionPdfError):
    """Dokumen tidak bisa dibuka atau rusak."""


class EngineError(UnionPdfError):
    """Kegagalan pada lapisan engine PDF."""


class PermissionDeniedError(UnionPdfError):
    """File terkunci atau tidak ada izin tulis."""


class DiskFullError(UnionPdfError):
    """Ruang disk tidak cukup."""


class OperationCancelled(UnionPdfError):
    """Pekerjaan dibatalkan oleh pengguna."""


class VerificationError(UnionPdfError):
    """Output hasil operasi tidak memenuhi verifikasi yang diharapkan."""
