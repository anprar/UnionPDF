"""Titik masuk aplikasi UnionPDF."""

from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from unionpdf import __version__
from unionpdf.ui.main_window import MainWindow
from unionpdf.ui.theme import QSS


def build_application(argv: list[str] | None = None) -> QApplication:
    """Buat QApplication dengan tema UnionPDF."""
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("UnionPDF")
    app.setApplicationDisplayName("UnionPDF")
    app.setOrganizationName("UnionPDF")
    app.setApplicationVersion(__version__)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    return app


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="unionpdf", description="UnionPDF — editor PDF gratis")
    parser.add_argument(
        "--file",
        default="",
        help="Dokumen PDF yang dibuka saat start.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    args = parse_args(raw)

    app = build_application([sys.argv[0], *raw])
    window = MainWindow()

    if args.file:
        from pathlib import Path

        try:
            window._load(Path(args.file))
        except Exception as exc:  # noqa: BLE001
            print(f"Gagal membuka {args.file}: {exc}", file=sys.stderr)

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
