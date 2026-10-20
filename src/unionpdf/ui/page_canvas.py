"""Kanvas tampilan halaman PDF.

Render dilakukan on-demand untuk halaman yang terlihat, dengan cache pixmap
berdasarkan (indeks halaman, tingkat zoom). Render ~34 ms/halaman pada MuPDF
(spike S1), sehingga rendering sinkron di thread UI masih dapat diterima pada
M1; pemindahan ke worker thread direncanakan pada M6 saat halaman penuh.
"""

from __future__ import annotations

from collections import OrderedDict

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

from unionpdf.application.session import EditSession
from unionpdf.ui.theme import COLORS

PAGE_GAP = 16
MARGIN = 12
MAX_CACHE_ITEMS = 24


class RenderCache:
    """Cache LRU pixmap halaman, dikunci per (halaman, zoom)."""

    def __init__(self, max_items: int = MAX_CACHE_ITEMS) -> None:
        self._items: OrderedDict[tuple[int, int], QPixmap] = OrderedDict()
        self._max_items = max_items

    @staticmethod
    def _bucket(zoom: float) -> int:
        return max(1, round(zoom * 20))

    def get(self, page_index: int, zoom: float) -> QPixmap | None:
        key = (page_index, self._bucket(zoom))
        pixmap = self._items.get(key)
        if pixmap is not None:
            self._items.move_to_end(key)
        return pixmap

    def put(self, page_index: int, zoom: float, pixmap: QPixmap) -> None:
        key = (page_index, self._bucket(zoom))
        self._items[key] = pixmap
        self._items.move_to_end(key)
        while len(self._items) > self._max_items:
            self._items.popitem(last=False)

    def clear(self) -> None:
        self._items.clear()


class PageCanvas(QGraphicsView):
    """Tampilan dokumen: halaman berurutan vertikal, dapat di-zoom."""

    page_changed = Signal(int)
    zoom_changed = Signal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(COLORS["canvas"]))
        self.setFrameShape(QGraphicsView.NoFrame)

        self._session: EditSession | None = None
        self._cache = RenderCache()
        self._zoom = 1.0
        self._current_page = 0
        self._page_items: list[QGraphicsPixmapItem] = []
        self._page_rects: list[QRectF] = []
        self._rendering = False

    # ------------------------------------------------------------------ state
    @property
    def session(self) -> EditSession | None:
        return self._session

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def current_page(self) -> int:
        return self._current_page

    def set_document(self, session: EditSession | None) -> None:
        self._session = session
        self._cache.clear()
        self._page_items.clear()
        self._page_rects.clear()
        self._scene.clear()
        self._current_page = 0
        if session is not None:
            self._rebuild_scene()
        self.viewport().update()

    # ----------------------------------------------------------------- layout
    def _rebuild_scene(self) -> None:
        if self._session is None:
            return
        count = self._session.document.page_count
        y = MARGIN
        for index in range(count):
            item = QGraphicsPixmapItem()
            item.setTransformationMode(Qt.SmoothTransformation)
            self._scene.addItem(item)
            self._page_items.append(item)
            self._page_rects.append(QRectF(0, y, 10, 10))
            y += 10 + PAGE_GAP
        self._layout_pages()

    def _layout_pages(self) -> None:
        if self._session is None:
            return
        zoom = self._zoom
        y = MARGIN
        for index, item in enumerate(self._page_items):
            pixmap = self._render_page(index)
            if pixmap is None:
                item.setPixmap(QPixmap())
                item.setPos(0, y)
                y += 120 + PAGE_GAP
                continue
            scaled_w = pixmap.width() * zoom
            scaled_h = pixmap.height() * zoom
            item.setPixmap(pixmap)
            item.setTransform(item.transform().scale(zoom, zoom))
            item.setPos(0, y)
            self._page_rects[index] = QRectF(0, y, scaled_w, scaled_h)
            y += scaled_h + PAGE_GAP
        total_height = y
        self._scene.setSceneRect(QRectF(0, 0, self.viewport().width(), total_height))

    def _render_page(self, index: int) -> QPixmap | None:
        if self._session is None:
            return None
        cached = self._cache.get(index, self._zoom)
        if cached is not None:
            return cached
        try:
            rendered = self._session.render_page(index, 1.0)
        except Exception:  # noqa: BLE001
            return None
        image = QImage.fromData(rendered.png_bytes, "PNG")
        if image.isNull():
            return None
        pixmap = QPixmap.fromImage(image)
        self._cache.put(index, self._zoom, pixmap)
        return pixmap

    # ------------------------------------------------------------------- zoom
    def set_zoom(self, zoom: float, *, anchor_top: bool = False) -> None:
        zoom = max(0.1, min(10.0, float(zoom)))
        if abs(zoom - self._zoom) < 1e-6:
            return
        self._zoom = zoom
        self._layout_pages()
        self.zoom_changed.emit(self._zoom)
        if anchor_top:
            self.verticalScrollBar().setValue(0)

    def zoom_in(self) -> None:
        self.set_zoom(self._zoom * 1.25)

    def zoom_out(self) -> None:
        self.set_zoom(self._zoom / 1.25)

    def fit_width(self) -> None:
        if self._session is None or not self._page_rects:
            return
        available = self.viewport().width() - 2 * MARGIN
        page_width_pt = self._page_rects[0].width()
        if page_width_pt <= 0:
            return
        self.set_zoom(max(0.1, min(10.0, available / page_width_pt)))

    def fit_page(self) -> None:
        if self._session is None or not self._page_rects:
            return
        available_w = self.viewport().width() - 2 * MARGIN
        available_h = self.viewport().height() - 2 * MARGIN
        rect = self._page_rects[0]
        if rect.width() <= 0 or rect.height() <= 0:
            return
        zoom = min(available_w / rect.width(), available_h / rect.height())
        self.set_zoom(max(0.1, min(10.0, zoom)))

    # ------------------------------------------------------------- navigation
    def go_to_page(self, index: int) -> None:
        if self._session is None or not self._page_rects:
            return
        index = max(0, min(index, len(self._page_rects) - 1))
        self._current_page = index
        rect = self._page_rects[index]
        self.centerOn(rect.center())
        self.page_changed.emit(index)

    def go_to_next_page(self) -> None:
        self.go_to_page(self._current_page + 1)

    def go_to_previous_page(self) -> None:
        self.go_to_page(self._current_page - 1)

    def refresh(self) -> None:
        self._cache.clear()
        self._layout_pages()

    # --------------------------------------------------------------- painting
    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # noqa: N802
        painter.fillRect(rect, QColor(COLORS["canvas"]))
        if self._session is None:
            return
        # Garis pemisah tipis antar halaman agar doc terlihat "diatas meja".
        pen = QPen(QColor(COLORS["border"]))
        pen.setWidthF(0.5)
        painter.setPen(pen)
        for index, item in enumerate(self._page_items):
            if not item.pixmap():
                continue
            width = item.pixmap().width() * self._zoom
            height = item.pixmap().height() * self._zoom
            rect_page = QRectF(item.pos().x(), item.pos().y(), width, height)
            if rect_page.bottom() < rect.top() or rect_page.top() > rect.bottom():
                continue
            painter.setBrush(QColor(COLORS["paper"]))
            painter.drawRect(rect_page)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect_page)
