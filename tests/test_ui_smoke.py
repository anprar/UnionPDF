"""Smoke test UI (offscreen).

Cakupan: aplikasi bisa dibuat, jendela bisa dibangun, dokumen bisa dimuat ke
UI, thumbnail & kanvas terisi. Interaksi visual penuh tetap NOT_RUN (manual).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtCore import QSize  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from unionpdf.ui.main_window import MainWindow  # noqa: E402


@pytest.fixture(scope="module")
def app() -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing  # type: ignore[return-value]
    application = QApplication([])
    application.setStyle("Fusion")
    return application


@pytest.fixture
def window(app: QApplication) -> MainWindow:
    win = MainWindow()
    yield win
    win.close()


class TestMainWindow:
    def test_window_constructs(self, window: MainWindow) -> None:
        assert window.windowTitle() == "UnionPDF"
        assert window.canvas is not None
        assert window.thumbnails is not None

    def test_actions_disabled_without_document(self, window: MainWindow) -> None:
        assert not window._actions["save_as"].isEnabled()
        assert not window._actions["fit_width"].isEnabled()
        assert window._actions["open"].isEnabled()

    def test_load_document_populates_ui(
        self, window: MainWindow, simple_pdf: Path
    ) -> None:
        window._load(simple_pdf)
        assert window._session is not None
        assert window.canvas.session is not None
        assert window.thumbnails.count() == 5
        assert "5 halaman" in window._doc_label.text()

    def test_canvas_renders_pages(
        self, window: MainWindow, simple_pdf: Path
    ) -> None:
        window._load(simple_pdf)
        assert window.canvas._page_items
        assert window.canvas._page_rects[0].width() > 0

    def test_zoom_changes_scale(self, window: MainWindow, simple_pdf: Path) -> None:
        window._load(simple_pdf)
        before = window.canvas.zoom
        window.canvas.zoom_in()
        assert window.canvas.zoom > before

    def test_fit_width_sets_zoom(self, window: MainWindow, simple_pdf: Path) -> None:
        window._load(simple_pdf)
        window.canvas.fit_width()
        assert 0.1 <= window.canvas.zoom <= 10.0

    def test_search_updates_status(self, window: MainWindow, simple_pdf: Path) -> None:
        window._load(simple_pdf)
        window._search_box.setText("Halaman")
        window._run_search()
        assert "5 hasil" in window._search_label.text()

    def test_close_document_clears_state(self, window: MainWindow, simple_pdf: Path) -> None:
        window._load(simple_pdf)
        window.close_document()
        assert window._session is None
        assert window.thumbnails.count() == 0
        assert window.windowTitle() == "UnionPDF"
