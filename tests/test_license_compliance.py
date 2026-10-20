"""Test kewajiban lisensi AGPL-3.0: source offer harus selalu tersedia.

AGPL-3.0 mewajibkan pengguna dapat memperoleh Corresponding Source.
Untuk aplikasi desktop, hal ini dipenuhi dengan tautan repository publik
yang harus tampil di aplikasi dan terdokumentasi.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from unionpdf import about

ROOT = Path(__file__).resolve().parents[1]


class TestProjectMetadata:
    def test_source_url_is_public_github(self) -> None:
        assert about.SOURCE_URL.startswith("https://github.com/")
        assert "anprar" in about.SOURCE_URL

    def test_license_is_agpl(self) -> None:
        assert about.LICENSE_SPDX.startswith("AGPL-3.0")
        assert "Affero" in about.LICENSE_NAME

    def test_license_file_exists_and_is_agpl(self) -> None:
        license_file = ROOT / "LICENSE"
        assert license_file.exists()
        text = license_file.read_text(encoding="utf-8", errors="replace")
        assert "GNU AFFERO GENERAL PUBLIC LICENSE" in text
        assert "Version 3" in text

    def test_notice_file_exists(self) -> None:
        notice = ROOT / "NOTICE"
        assert notice.exists()
        text = notice.read_text(encoding="utf-8", errors="replace")
        assert "AGPL" in text
        assert "MuPDF" in text
        assert "PySide6" in text

    def test_homepage_matches_source(self) -> None:
        assert about.HOMEPAGE_URL == about.SOURCE_URL


class TestSourceOfferIsVisible:
    """Tautan source harus benar-benar muncul di tempat yang dilihat pengguna."""

    def test_about_dialog_mentions_source(self) -> None:
        source = (ROOT / "src" / "unionpdf" / "ui" / "main_window.py").read_text(
            encoding="utf-8"
        )
        assert "about.SOURCE_URL" in source
        assert "LICENSE_SPDX" in source or "LICENSE_NAME" in source

    def test_readme_links_to_repository(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        assert "github.com/anprar/UnionPDF" in readme

    def test_license_review_documents_offer(self) -> None:
        review = (ROOT / "docs" / "LICENSE_REVIEW.md").read_text(encoding="utf-8")
        assert "github.com/anprar/UnionPDF" in review


class TestNoProprietaryAssetsCommitted:
    """Aset proprietary tidak boleh masuk repositori."""

    @pytest.mark.parametrize(
        "relative",
        [
            "docs/research/mui_strings_en-US.json",
            "docs/research/native_feature_ids_v14.json",
            "docs/research/ribbon_controls_v14.json",
            "docs/research/V14_UI_EVIDENCE.md",
        ],
    )
    def test_raw_corpora_is_gitignored(self, relative: str) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        assert relative in gitignore, f"{relative} harus di-gitignore"

    def test_no_nitro_binary_in_repo(self) -> None:
        tracked = [
            p.name
            for p in ROOT.rglob("*")
            if p.is_file()
            and p.suffix.lower() in {".dll", ".exe"}
            and ".venv" not in p.parts
        ]
        assert tracked == [], f"Biner tidak boleh ada di workspace: {tracked}"


class TestRepoUrlIsConsistent:
    def test_url_format(self) -> None:
        assert re.fullmatch(r"https://github\.com/[\w.-]+/[\w.-]+", about.SOURCE_URL)
