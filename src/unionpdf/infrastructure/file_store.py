"""Penyimpanan berkas dengan penulisan atomik.

Aturan (docs/ARCHITECTURE.md §2.4):
  1. Tulis ke file sementara di direktori yang sama dengan tujuan.
  2. Tutup & flush handle.
  3. Verifikasi output (buka ulang, cek isi).
  4. ``os.replace`` -> final (atomik di NTFS bila volume sama).
  5. Hapus file sementara bila langkah 1-3 gagal.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

from unionpdf.domain.errors import (
    DiskFullError,
    PermissionDeniedError,
    VerificationError,
)

VERIFY = Callable[[Path], None]


def atomic_write(
    destination: Path,
    writer: Callable[[Path], None],
    *,
    verifier: VERIFY | None = None,
) -> Path:
    """Tulis ``destination`` via file sementara, verifikasi, lalu finalisasi.

    ``writer`` menerima path file sementara dan harus menulis di sana.
    ``verifier`` menerima path final dan harus melempar exception bila output
    tidak valid.
    """
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    handle, temp_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.unionpdf-", suffix=".tmp", dir=str(destination.parent)
    )
    os.close(handle)
    temp_path = Path(temp_name)

    try:
        writer(temp_path)
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise VerificationError(f"Tidak ada data yang ditulis ke {temp_path}")
        if verifier is not None:
            verifier(temp_path)
        os.replace(temp_path, destination)
    except PermissionError as exc:
        temp_path.unlink(missing_ok=True)
        raise PermissionDeniedError(
            f"Tidak ada izin menulis ke {destination}: {exc}"
        ) from exc
    except OSError as exc:
        temp_path.unlink(missing_ok=True)
        if getattr(exc, "errno", None) in (28, 39):  # ENOSPC, EDQUOT
            raise DiskFullError(f"Ruang disk tidak cukup untuk {destination}") from exc
        raise
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return destination


class FileStore:
    """Wrapper tipis untuk operasi berkas tingkat aplikasi."""

    @staticmethod
    def ensure_parent(path: Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def unique_path(directory: Path, stem: str, suffix: str = ".pdf") -> Path:
        """Buat nama berkas unik di ``directory`` tanpa menimpa berkas lain."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        candidate = directory / f"{stem}{suffix}"
        counter = 1
        while candidate.exists():
            candidate = directory / f"{stem} ({counter}){suffix}"
            counter += 1
        return candidate
