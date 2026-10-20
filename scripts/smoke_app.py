"""Smoke test aplikasi: menjalankan UI sungguhan (offscreen) dan memuat dokumen.

Dipakai sebagai verifikasi "aplikasi benar-benar dapat dijalankan", terpisah
dari test pytest.

Jalankan: .venv\\Scripts\\python.exe scripts\\smoke_app.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pymupdf  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402

from unionpdf.app import build_application  # noqa: E402
from unionpdf.ui.main_window import MainWindow  # noqa: E402


def make_pdf(path: Path, pages: int = 6) -> Path:
    doc = pymupdf.open()
    for index in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 90), f"Smoke test halaman {index + 1}", fontsize=18, fontname="helv")
        page.insert_text((72, 130), "Isi dokumen untuk smoke test UnionPDF.", fontsize=11, fontname="helv")
    doc.save(path)
    doc.close()
    return path


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="unionpdf-smoke-"))
    pdf = make_pdf(tmp / "smoke.pdf")

    app = build_application([sys.argv[0]])
    window = MainWindow()
    window.show()

    errors: list[str] = []
    try:
        window._load(pdf)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"gagal memuat dokumen: {exc}")

    app.processEvents()

    checks = {
        "jendela terlihat": window.isVisible(),
        "dokumen termuat": window._session is not None,
        "jumlah thumbnail": window.thumbnails.count() == 6,
        "kanvas punya item": len(window.canvas._page_items) == 6,
        "lebar halaman > 0": window.canvas._page_rects[0].width() > 0,
        "judul dokumen": "smoke.pdf" in window.windowTitle(),
    }

    window.canvas.zoom_in()
    app.processEvents()
    checks["zoom berfungsi"] = window.canvas.zoom > 1.0

    window.canvas.go_to_page(3)
    app.processEvents()
    checks["navigasi halaman"] = window.canvas.current_page == 3

    window._search_box.setText("halaman")
    window._run_search()
    app.processEvents()
    checks["pencarian"] = "6 hasil" in window._search_label.text()

    report = []
    for name, ok in checks.items():
        report.append(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            errors.append(name)

    print("UnionPDF smoke test")
    print("\n".join(report))
    print(f"\nDokumen uji: {pdf}")

    window.close()
    app.quit()

    if errors:
        print(f"\nGAGAL: {len(errors)} pemeriksaan tidak lolos -> {errors}")
        return 1
    print("\nSemua pemeriksaan lolos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
