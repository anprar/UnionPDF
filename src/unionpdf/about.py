"""Metadata proyek UnionPDF.

Pusat untuk informasi yang harus konsisten di seluruh aplikasi: nama,
versi, lisensi, dan **tautan source**.

Kewajiban AGPL-3.0: pengguna harus dapat memperoleh Corresponding Source.
Karena UnionPDF adalah aplikasi desktop (bukan layanan jaringan), kewajiban
ini dipenuhi dengan menyediakan tautan repository publik di dialog "Tentang"
dan di halaman About.
"""

from __future__ import annotations

from unionpdf import __version__

APP_NAME = "UnionPDF"
APP_ID = "UnionPDF"
ORGANIZATION_NAME = "UnionPDF"

LICENSE_SPDX = "AGPL-3.0-only"
LICENSE_NAME = "GNU Affero General Public License v3.0 or later"

#: Repository publik UnionPDF — inilah "source offer" yang diwajibkan AGPL.
SOURCE_URL = "https://github.com/anprar/UnionPDF"
HOMEPAGE_URL = SOURCE_URL
ISSUES_URL = f"{SOURCE_URL}/issues"

COPYRIGHT = "Copyright (C) 2026 UnionPDF Contributors"

#: Ringkasan singkat yang tampil di About & di metadata paket.
SUMMARY = (
    "Aplikasi PDF gratis untuk Windows. Offline, tanpa watermark, "
    "tanpa telemetri."
)

__all__ = [
    "APP_ID",
    "APP_NAME",
    "COPYRIGHT",
    "HOMEPAGE_URL",
    "ISSUES_URL",
    "LICENSE_NAME",
    "LICENSE_SPDX",
    "ORGANIZATION_NAME",
    "SOURCE_URL",
    "SUMMARY",
    "__version__",
]
