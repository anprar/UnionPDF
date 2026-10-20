"""Panel thumbnail halaman."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from unionpdf.application.session import EditSession
from unionpdf.ui.theme import COLORS

THUMBNAIL_WIDTH = 128
THUMBNAIL_HEIGHT = 176


class ThumbnailPane(QListWidget):
    """Daftar thumbnail halaman; klik untuk pindah ke halaman."""

    page_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session: EditSession | None = None
        self.setIconSize(QSize(THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
        self.setUniformItemSizes(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setSpacing(2)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.currentItemChanged.connect(self._on_current_changed)

    def set_document(self, session: EditSession | None) -> None:
        self._session = session
        self.clear()
        if session is None:
            return
        count = session.document.page_count
        for index in range(count):
            item = QListWidgetItem()
            item.setData(Qt.UserRole, index)
            item.setText(f"  {index + 1}")
            item.setToolTip(f"Halaman {index + 1}")
            self.addItem(item)
        self._populate_thumbnails()
        if self.count():
            self.setCurrentRow(0)

    def _populate_thumbnails(self) -> None:
        if self._session is None:
            return
        for index in range(self.count()):
            item = self.item(index)
            if item is None:
                continue
            pixmap = self._render_thumbnail(index)
            if pixmap is not None:
                item.setIcon(QPixmap(pixmap))

    def _render_thumbnail(self, index: int) -> QPixmap | None:
        if self._session is None:
            return None
        try:
            rendered = self._session.render_page(index, 0.35)
        except Exception:  # noqa: BLE001
            return None
        image = QImage.fromData(rendered.png_bytes, "PNG")
        if image.isNull():
            return None
        pixmap = QPixmap.fromImage(image)
        return pixmap.scaled(
            THUMBNAIL_WIDTH,
            THUMBNAIL_HEIGHT,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

    def refresh_thumbnails(self) -> None:
        self._populate_thumbnails()

    def select_page(self, index: int) -> None:
        if 0 <= index < self.count():
            self.setCurrentRow(index)

    def _on_current_changed(self, current: QListWidgetItem | None, _previous=None) -> None:
        if current is None:
            return
        index = current.data(Qt.UserRole)
        if isinstance(index, int):
            self.page_selected.emit(index)
