"""Test infrastruktur: penulisan atomik dan pengaturan."""

from __future__ import annotations

from pathlib import Path

import pytest

from unionpdf.domain.errors import VerificationError
from unionpdf.infrastructure.file_store import FileStore, atomic_write
from unionpdf.infrastructure.settings import SettingsStore


class TestAtomicWrite:
    def test_writes_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"

        def writer(path: Path) -> None:
            path.write_text("halo", encoding="utf-8")

        atomic_write(target, writer)
        assert target.read_text(encoding="utf-8") == "halo"

    def test_no_temp_file_left_behind(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"
        atomic_write(target, lambda p: p.write_text("x", encoding="utf-8"))
        leftovers = [p for p in tmp_path.iterdir() if p.name != "out.txt"]
        assert leftovers == []

    def test_failed_writer_leaves_no_temp_and_no_target(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"

        def writer(path: Path) -> None:
            path.write_text("partial", encoding="utf-8")
            raise RuntimeError("gagal di tengah")

        with pytest.raises(RuntimeError):
            atomic_write(target, writer)

        assert not target.exists()
        assert [p for p in tmp_path.iterdir() if p.name != "out.txt"] == []

    def test_verifier_failure_blocks_finalisation(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"

        def verifier(path: Path) -> None:
            raise VerificationError("isi tidak sesuai")

        with pytest.raises(VerificationError):
            atomic_write(target, lambda p: p.write_text("x", encoding="utf-8"), verifier=verifier)

        assert not target.exists()

    def test_empty_output_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "out.txt"
        with pytest.raises(VerificationError):
            atomic_write(target, lambda p: None)
        assert not target.exists()

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "out.txt"
        atomic_write(target, lambda p: p.write_text("x", encoding="utf-8"))
        assert target.exists()


class TestFileStore:
    def test_unique_path_avoids_overwrite(self, tmp_path: Path) -> None:
        first = FileStore.unique_path(tmp_path, "dokumen")
        first.write_bytes(b"x")
        second = FileStore.unique_path(tmp_path, "dokumen")
        assert second != first
        assert second.exists() is False


class TestSettings:
    def test_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        store = SettingsStore(path)
        store.settings.default_zoom = 1.5
        store.save()

        reloaded = SettingsStore(path).load()
        assert reloaded.default_zoom == 1.5

    def test_corrupt_settings_fall_back_to_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text("{bukan json", encoding="utf-8")
        settings = SettingsStore(path).load()
        assert settings.default_zoom == 1.0

    def test_unknown_keys_ignored(self, tmp_path: Path) -> None:
        path = tmp_path / "settings.json"
        path.write_text('{"default_zoom": 2.0, "asing": 1}', encoding="utf-8")
        settings = SettingsStore(path).load()
        assert settings.default_zoom == 2.0
        assert not hasattr(settings, "asing")
