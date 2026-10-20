"""Token desain & QSS UnionPDF.

Identitas visual UnionPDF berdiri sendiri — bukan turunan UI aplikasi referensi.
Palet: netral gelap + satu aksen, kontras tinggi, target DPIAware.
"""

from __future__ import annotations

# Token warna (dipakai QSS dan kode)
COLORS = {
    "canvas": "#14161a",
    "surface": "#1c1f26",
    "surface_alt": "#232730",
    "border": "#2e3340",
    "ink": "#e6e8ee",
    "ink_muted": "#9aa1b1",
    "accent": "#4c8dff",
    "accent_hover": "#6ba0ff",
    "accent_pressed": "#3a7ae8",
    "danger": "#ff6b6b",
    "success": "#3ecf8e",
    "paper": "#ffffff",
    "paper_shadow": "#0b0d11",
}

QSS = f"""
QWidget {{
    background-color: {COLORS['canvas']};
    color: {COLORS['ink']};
    font-family: "Segoe UI", "Inter", system-ui, sans-serif;
    font-size: 12px;
}}

QMainWindow::separator {{
    background: {COLORS['border']};
    width: 1px;
    height: 1px;
}}

QToolBar {{
    background: {COLORS['surface']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px 6px;
    spacing: 2px;
}}

QToolBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 9px;
    color: {COLORS['ink']};
}}
QToolBar QToolButton:hover {{
    background: {COLORS['surface_alt']};
    border-color: {COLORS['border']};
}}
QToolBar QToolButton:pressed {{
    background: {COLORS['accent_pressed']};
    color: #ffffff;
}}
QToolBar QToolButton:disabled {{
    color: {COLORS['ink_muted']};
}}

QMenuBar {{
    background: {COLORS['surface']};
    border-bottom: 1px solid {COLORS['border']};
}}
QMenuBar::item:selected {{
    background: {COLORS['surface_alt']};
}}
QMenu {{
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 26px 6px 20px;
    border-radius: 5px;
}}
QMenu::item:selected {{
    background: {COLORS['accent']};
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background: {COLORS['border']};
    margin: 4px 8px;
}}

QListWidget {{
    background: {COLORS['surface']};
    border: none;
    outline: none;
}}
QListWidget::item {{
    border-radius: 6px;
    margin: 3px 6px;
    padding: 2px;
}}
QListWidget::item:selected {{
    background: {COLORS['accent']};
}}
QListWidget::item:hover:!selected {{
    background: {COLORS['surface_alt']};
}}

QLineEdit, QSpinBox, QComboBox {{
    background: {COLORS['surface_alt']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: {COLORS['accent']};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {COLORS['accent']};
}}

QStatusBar {{
    background: {COLORS['surface']};
    border-top: 1px solid {COLORS['border']};
    color: {COLORS['ink_muted']};
}}
QStatusBar::item {{ border: none; }}

QGraphicsView {{
    background: {COLORS['canvas']};
    border: none;
}}
"""
