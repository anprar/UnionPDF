"""Pengaturan aplikasi yang disimpan lokal.

Disimpan sebagai JSON di ``%LOCALAPPDATA%/UnionPDF/settings.json``.
Tidak ada telemetry, tidak ada panggilan jaringan.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    """Preferensi pengguna. Tidak pernah berisi credential."""

    last_open_directory: str = ""
    remember_window_geometry: bool = True
    default_zoom: float = 1.0
    show_thumbnails: bool = True
    language: str = "id"

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)


def settings_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "UnionPDF" / "settings.json"


class SettingsStore:
    """Baca/tulis pengaturan; kegagalan membaca tidak boleh menggagalkan aplikasi."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else settings_path()
        self._settings = AppSettings()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def load(self) -> AppSettings:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                known = {f for f in AppSettings.__dataclass_fields__}
                for key, value in data.items():
                    if key in known:
                        setattr(self._settings, key, value)
        except (OSError, ValueError, TypeError):
            # Pengaturan rusak -> pakai default, jangan gagalkan start.
            self._settings = AppSettings()
        return self._settings

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(self._settings.to_json(), encoding="utf-8")
        except OSError:
            pass
