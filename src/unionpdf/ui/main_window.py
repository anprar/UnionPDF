"""Jendela utama UnionPDF.

M1 vertical slice: buka dokumen, lihat halaman (kanvas + thumbnail), zoom,
navigasi halaman, cari teks, simpan sebagai.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QWidget,
)

from unionpdf import __version__
from unionpdf.application.session import EditSession
from unionpdf.domain.errors import UnionPdfError
from unionpdf.engine.mupdf_engine import MupdfDocumentEngine
from unionpdf.ui.page_canvas import PageCanvas
from unionpdf.ui.thumbnail_pane import ThumbnailPane


class MainWindow(QMainWindow):
    """Jendela aplikasi utama."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UnionPDF")
        self.resize(1280, 820)

        self._engine = MupdfDocumentEngine()
        self._session: EditSession | None = None

        self._build_ui()
        self._build_actions()
        self._update_ui_state()

    # --------------------------------------------------------------- UI build
    def _build_ui(self) -> None:
        self.thumbnails = ThumbnailPane()
        self.canvas = PageCanvas()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.thumbnails)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 1060])
        self.setCentralWidget(splitter)

        self.thumbnails.page_selected.connect(self.canvas.go_to_page)
        self.canvas.page_changed.connect(self._on_page_changed)

        self._page_label = QLabel("Halaman - / -")
        self._zoom_label = QLabel("100%")
        self._doc_label = QLabel("Tidak ada dokumen")
        self._search_label = QLabel("")

        status = self.statusBar()
        status.addWidget(self._doc_label, 1)
        status.addPermanentWidget(self._search_label)
        status.addPermanentWidget(self._page_label)
        status.addPermanentWidget(self._zoom_label)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Cari teks…  (Ctrl+F)")
        self._search_box.setMaximumWidth(320)
        self._search_box.returnPressed.connect(self._run_search)

        toolbar = QToolBar("Utama")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        self.toolbar = toolbar

        self._zoom_combo = None  # diisi di _build_actions

    def _build_actions(self) -> None:
        # --- File -----------------------------------------------------------
        open_act = QAction("Buka…", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self.open_document)
        self.addAction(open_act)

        close_act = QAction("Tutup Dokumen", self)
        close_act.setShortcut(QKeySequence.Close)
        close_act.triggered.connect(self.close_document)
        self.addAction(close_act)

        save_as_act = QAction("Simpan Sebagai…", self)
        save_as_act.setShortcut(QKeySequence.SaveAs)
        save_as_act.triggered.connect(self.save_document_as)
        self.addAction(save_as_act)

        exit_act = QAction("Keluar", self)
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.triggered.connect(self.close)
        self.addAction(exit_act)

        file_menu = self.menuBar().addMenu("&Berkas")
        file_menu.addAction(open_act)
        file_menu.addAction(close_act)
        file_menu.addSeparator()
        file_menu.addAction(save_as_act)
        file_menu.addSeparator()
        file_menu.addAction(exit_act)

        # --- Tampilan --------------------------------------------------------
        zoom_in_act = QAction("Perbesar", self)
        zoom_in_act.setShortcut(QKeySequence.ZoomIn)
        zoom_in_act.triggered.connect(self.canvas.zoom_in)
        self.addAction(zoom_in_act)

        zoom_out_act = QAction("Perkecil", self)
        zoom_out_act.setShortcut(QKeySequence.ZoomOut)
        zoom_out_act.triggered.connect(self.canvas.zoom_out)
        self.addAction(zoom_out_act)

        fit_width_act = QAction("Sesuaikan Lebar", self)
        fit_width_act.setShortcut(QKeySequence("Ctrl+0"))
        fit_width_act.triggered.connect(self.canvas.fit_width)
        self.addAction(fit_width_act)

        fit_page_act = QAction("Sesuaikan Halaman", self)
        fit_page_act.setShortcut(QKeySequence("Ctrl+1"))
        fit_page_act.triggered.connect(self.canvas.fit_page)
        self.addAction(fit_page_act)

        view_menu = self.menuBar().addMenu("&Tampilan")
        view_menu.addAction(zoom_in_act)
        view_menu.addAction(zoom_out_act)
        view_menu.addSeparator()
        view_menu.addAction(fit_width_act)
        view_menu.addAction(fit_page_act)

        # --- ToolBar ---------------------------------------------------------
        self.toolbar.addAction(open_act)
        self.toolbar.addSeparator()
        self.toolbar.addAction(zoom_out_act)
        self.toolbar.addAction(zoom_in_act)
        self.toolbar.addAction(fit_width_act)
        self.toolbar.addAction(fit_page_act)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self._search_box)

        # --- Bantuan ---------------------------------------------------------
        about_act = QAction("Tentang UnionPDF", self)
        about_act.triggered.connect(self._show_about)
        help_menu = self.menuBar().addMenu("&Bantuan")
        help_menu.addAction(about_act)

        self._actions = {
            "open": open_act,
            "close": close_act,
            "save_as": save_as_act,
            "zoom_in": zoom_in_act,
            "zoom_out": zoom_out_act,
            "fit_width": fit_width_act,
            "fit_page": fit_page_act,
        }

    # --------------------------------------------------------------- actions
    def open_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Buka Dokumen PDF", "", "Dokumen PDF (*.pdf);;Semua berkas (*)"
        )
        if not path:
            return
        try:
            self._load(Path(path))
        except UnionPdfError as exc:
            QMessageBox.warning(self, "Gagal membuka", str(exc))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Kesalahan", f"Terjadi kesalahan tak terduga:\n{exc}")

    def _load(self, path: Path) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

        session = EditSession(self._engine, path)
        document = session.open()
        self._session = session

        self.canvas.set_document(session)
        self.thumbnails.set_document(session)
        self.canvas.fit_width()

        info = document.info
        title = info.title or path.name
        self.setWindowTitle(f"{title} — UnionPDF")
        self._doc_label.setText(f"{path.name}  ·  {info.page_count} halaman")
        self._update_ui_state()

    def close_document(self) -> None:
        if self._session is None:
            return
        self._session.close()
        self._session = None
        self.canvas.set_document(None)
        self.thumbnails.set_document(None)
        self.setWindowTitle("UnionPDF")
        self._doc_label.setText("Tidak ada dokumen")
        self._update_ui_state()

    def save_document_as(self) -> None:
        if self._session is None:
            return
        suggested = str(self._session.path.with_name(f"{self._session.path.stem}_edited.pdf"))
        path, _ = QFileDialog.getSaveFileName(
            self, "Simpan Sebagai", suggested, "Dokumen PDF (*.pdf)"
        )
        if not path:
            return
        try:
            report = self._engine.write(
                self._session.handle,
                Path(path),
                expected_pages=self._session.document.page_count,
            )
        except UnionPdfError as exc:
            QMessageBox.warning(self, "Gagal menyimpan", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Kesalahan", f"Terjadi kesalahan tak terduga:\n{exc}")
            return

        if not report.verification.passed:
            QMessageBox.warning(
                self,
                "Verifikasi gagal",
                "Berkas tersimpan, tetapi hasil verifikasi tidak sesuai:\n"
                + "\n".join(report.verification.notes),
            )
            return
        QMessageBox.information(
            self,
            "Tersimpan",
            f"Dokumen tersimpan:\n{report.destination}\n"
            f"Halaman: {report.page_count}\n"
            f"Ukuran: {report.bytes_written / 1024:.1f} KB",
        )

    def _run_search(self) -> None:
        if self._session is None:
            return
        query = self._search_box.text().strip()
        if not query:
            self._search_label.setText("")
            return
        hits = self._session.search(query)
        self._search_label.setText(f"{len(hits)} hasil untuk “{query}”")
        if hits:
            self.canvas.go_to_page(hits[0].page_index)
            self.thumbnails.select_page(hits[0].page_index)

    def _on_page_changed(self, index: int) -> None:
        if self._session is None:
            return
        total = self._session.document.page_count
        self._page_label.setText(f"Halaman {index + 1} / {total}")

    def _update_ui_state(self) -> None:
        has_document = self._session is not None
        for key in ("close", "save_as", "zoom_in", "zoom_out", "fit_width", "fit_page"):
            self._actions[key].setEnabled(has_document)
        self._page_label.setText("Halaman - / -" if not has_document else self._page_label.text())
        if not has_document:
            self._zoom_label.setText("100%")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "Tentang UnionPDF",
            f"<b>UnionPDF</b> {__version__}<br><br>"
            "Aplikasi PDF gratis, offline, tanpa watermark.<br>"
            "Lisensi: AGPL-3.0.<br><br>"
            f"Engine PDF: {self._engine.name} {getattr(self._engine, '_version', '')}",
        )

    # -------------------------------------------------------------- shortcuts
    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        ctrl = event.modifiers() & Qt.ControlModifier
        if ctrl and key == Qt.Key_F:
            self._search_box.setFocus()
            self._search_box.selectAll()
            return
        if key in (Qt.Key_PageDown,):
            self.canvas.go_to_next_page()
            return
        if key in (Qt.Key_PageUp,):
            self.canvas.go_to_previous_page()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._session is not None:
            self._session.close()
            self._session = None
        super().closeEvent(event)
