"""Spike 05 - Kesiapan desktop: Qt shell offscreen, DPI, font, dan packaging.

Output: spikes/out/spike_05_packaging.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

OUT = Path(__file__).parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

results: dict = {"spike": "05_packaging"}


def probe_qt() -> dict:
    """Satu QApplication untuk seluruh proses (Qt hanya mengizinkan satu instance)."""
    from PySide6.QtCore import Qt, qVersion
    from PySide6.QtWidgets import QApplication, QLabel

    out = {
        "qt_version": qVersion(),
        "pyside_version": None,
        "high_dpi_policy_available": hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"),
    }
    try:
        import PySide6

        out["pyside_version"] = PySide6.__version__
    except Exception:  # noqa: BLE001
        pass

    app = QApplication(sys.argv)
    out["app_ok"] = True
    screen = app.primaryScreen()
    if screen is not None:
        out["primary_screen_dpr"] = screen.devicePixelRatio()
        out["logical_dpi"] = screen.logicalDotsPerInch()
        out["available_geometry"] = {
            "w": screen.availableGeometry().width(),
            "h": screen.availableGeometry().height(),
        }

    label = QLabel("UnionPDF")
    label.resize(120, 40)
    label.show()
    app.processEvents()
    size = label.size()
    out["widget_created"] = True
    out["widget_size"] = [size.width(), size.height()]
    out["qss_supported"] = True
    del label
    return out


def probe_pyinstaller() -> dict:
    exe = shutil.which("pyinstaller")
    out = {"on_path": bool(exe), "path": exe}
    if not exe:
        try:
            r = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                               capture_output=True, text=True, timeout=60)
            out["module_version"] = r.stdout.strip() or r.stderr.strip()[:120]
        except Exception as exc:  # noqa: BLE001
            out["error"] = str(exc)
    else:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60)
        out["version"] = r.stdout.strip()
    out["note"] = "PyInstaller belum diinstal pada venv UnionPDF; build/pyinstaller butuh paket terpisah."
    return out


def probe_native_deps() -> dict:
    """Cek ukuran dependensi native yang akan ikut terbawa saat packaging."""
    import pymupdf

    base = Path(pymupdf.__file__).parent
    total = 0
    biggest = []
    for p in base.rglob("*"):
        if p.is_file():
            size = p.stat().st_size
            total += size
            biggest.append((size, str(p.relative_to(base))))
    biggest.sort(reverse=True)
    return {
        "pymupdf_package_mb": round(total / 1024 / 1024, 2),
        "largest_files": [{"name": n, "mb": round(s / 1024 / 1024, 2)} for s, n in biggest[:6]],
    }


def main() -> int:
    results["qt"] = probe_qt()
    results["pyinstaller"] = probe_pyinstaller()
    results["native_deps"] = probe_native_deps()
    (OUT / "spike_05_packaging.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
