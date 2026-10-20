import os, tempfile, atexit
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QPushButton
from PySide6.QtSvg import QSvgRenderer

from src.config import APP_FONT_STACK
from src.utils import _app_dir, _dist_dir

T = {
    "bg_base":       "#050d1a",
    "bg_surface":    "#0a1628",
    "bg_raised":     "#0f1f38",
    "bg_hover":      "#162844",
    "bg_active":     "#1c3150",
    "border":        "#1e3a5f",
    "border_focus":  "#2563eb",
    "border_success":"#059669",
    "text_primary":  "#ffffff",
    "text_secondary":"#cbd5e1",
    "text_muted":    "#94a3b8",
    "text_disabled": "#253a52",
    "blue_500":      "#2563eb",
    "blue_600":      "#1d4ed8",
    "blue_700":      "#1e40af",
    "blue_400":      "#60a5fa",
    "green_500":     "#059669",
    "green_600":     "#047857",
    "green_700":     "#065f46",
    "green_400":     "#34d399",
    "amber_500":     "#f59e0b",
    "amber_600":     "#d97706",
    "amber_400":     "#fbbf24",
    "red_500":       "#f87171",
    "red_600":       "#ef4444",
    "red_700":       "#dc2626",
    "slate_600":     "#2a4a6a",
    "slate_700":     "#1e3a52",
    "slate_800":     "#0d1f33",
    "_dark": True,
    "_btn_primary_text": "#ffffff",
    "_btn_success_text": "#ffffff",
    "_icon": ("bg1","#0f1f38","bg2","#050d1a","arr1","#60a5fa","arr2","#1d4ed8","border","#2563eb","tray","#60a5fa","dot","#34d399"),
}

_ICONS = {
    "download":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "clipboard":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2" width="6" height="4" rx="1"/><path d="M17 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>',
    "x":           '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "folder_open": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/><line x1="12" y1="11" x2="12" y2="17"/><line x1="9" y1="14" x2="15" y2="14"/></svg>',
    "folder":      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    "play":        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    "square":      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>',
    "scan":        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>',
    "zap":         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "trash":       '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    "check_circle":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "rotate_cw":   '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>',
    "settings":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "history":     '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="12 8 12 12 14 14"/><path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5"/></svg>',
    "link":        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "cpu":         '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
    "upload":      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "list":        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
    "activity":    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "info":        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
}

@lru_cache(maxsize=256)
def make_icon_pixmap(name: str, color: str = "#cbd5e1", size: int = 16) -> QPixmap:
    svg_src = _ICONS.get(name, _ICONS["download"])
    colored = svg_src.replace('stroke="currentColor"', f'stroke="{color}"')
    colored = colored.replace('fill="currentColor"', f'fill="{color}"')
    data = QByteArray(colored.encode())
    renderer = QSvgRenderer(data)
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(p)
    p.end()
    return pix

def icon(name: str, color: str = "#cbd5e1", size: int = 15):
    return QIcon(make_icon_pixmap(name, color, size))

def _build_icon_svg(td: dict) -> str:
    ic = {td["_icon"][i]: td["_icon"][i+1] for i in range(0, len(td["_icon"]), 2)}
    dot = f'<circle cx="52" cy="12" r="5" fill="{ic["dot"]}" opacity="0.85"/>' if ic.get("dot") else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg_g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{ic["bg1"]}"/>
      <stop offset="1" stop-color="{ic["bg2"]}"/>
    </linearGradient>
    <linearGradient id="arr_g" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{ic["arr1"]}"/>
      <stop offset="1" stop-color="{ic["arr2"]}"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="62" height="62" rx="14" fill="url(#bg_g)"/>
  <rect x="1.5" y="1.5" width="61" height="61" rx="13.5" fill="none" stroke="{ic["border"]}" stroke-width="1.5" opacity="0.8"/>
  <rect x="28.5" y="9" width="7" height="28" rx="3.5" fill="url(#arr_g)"/>
  <path d="M16 34 L32 50 L48 34 L41 34 L32 43 L23 34 Z" fill="url(#arr_g)"/>
  <rect x="13" y="54" width="38" height="5" rx="2.5" fill="{ic["tray"]}" opacity="0.9"/>
  {dot}
</svg>'''

def make_app_icon(td: dict = None):
    root = Path(__file__).resolve().parent.parent
    bases = [root / "assets", root, _app_dir() / "assets", _app_dir(), _dist_dir() / "assets", _dist_dir()]
    for base in bases:
        for name in ("icon.ico", "icon.png"):
            p = base / name
            if p.exists():
                ic = QIcon(str(p))
                if not ic.isNull():
                    return ic
    # Fallback to rendered SVG
    svg_str = _build_icon_svg(td or T)
    app_icon = QIcon()
    for sz in (16, 24, 32, 48, 64, 128, 256):
        data = QByteArray(svg_str.encode())
        renderer = QSvgRenderer(data)
        pix = QPixmap(sz, sz)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(p)
        p.end()
        app_icon.addPixmap(pix)
    return app_icon

_ARROW_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 6"><polyline points="1,1 5,5 9,1" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
_arrow_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
_arrow_file.write(_ARROW_SVG)
_arrow_file.close()
_ARROW_PATH = _arrow_file.name.replace("\\", "/")
atexit.register(lambda: os.unlink(_ARROW_PATH) if os.path.exists(_ARROW_PATH) else None)

def build_style(t: dict, arrow_path: str = "") -> str:
    return f"""
QMainWindow, QWidget {{
    background: {t['bg_base']};
    color: {t['text_primary']};
    font-family: {APP_FONT_STACK};
    font-size: 12px;
}}
QMenuBar {{
    background: {t['bg_surface']};
    color: #ffffff;
    border-bottom: 1px solid {t['border']};
    padding: 1px 4px;
    font-size: 12px;
}}
QMenuBar::item {{ padding: 4px 10px; border-radius: 3px; }}
QMenuBar::item:selected {{ background: {t['bg_raised']}; color: {t['text_primary']}; }}
QMenu {{
    background: {t['bg_raised']};
    border: 1px solid {t['border']};
    color: {t['text_primary']};
    padding: 3px 0;
}}
QMenu::item {{ padding: 5px 28px 5px 12px; font-size: 12px; }}
QMenu::item:selected {{ background: {t['bg_hover']}; color: {t['text_primary']}; }}
QMenu::separator {{ height: 1px; background: {t['border']}; margin: 3px 6px; }}

QLabel#sec_lbl {{
    color: {t['blue_400']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    background: transparent;
}}
QFrame#panel {{
    background: {t['bg_surface']};
    border: 1px solid {t['border']};
    border-left: 3px solid {t['blue_600']};
    border-radius: 6px;
}}
QTextEdit#url_area {{
    background: {t['bg_raised']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    color: {t['text_primary']};
    font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 7px 10px;
    selection-background-color: {t['blue_700']};
}}
QTextEdit#url_area:focus {{ border-color: {t['blue_500']}; }}
QLineEdit {{
    background: {t['bg_raised']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 5px 9px;
    color: {t['text_primary']};
    font-size: 12px;
    selection-background-color: {t['blue_700']};
}}
QLineEdit:focus {{ border-color: {t['blue_500']}; }}
QLineEdit:read-only {{ color: #ffffff; }}

QPushButton {{
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
    padding: 5px 14px;
    border: 1px solid transparent;
    color: {t['text_primary']};
}}
QPushButton#btn_primary {{
    background: {t['blue_600']}; color: #ffffff; border-color: {t['blue_700']};
}}
QPushButton#btn_primary:hover   {{ background: {t['blue_500']}; }}
QPushButton#btn_primary:pressed {{ background: {t['blue_700']}; }}
QPushButton#btn_primary:disabled {{ background: {t['slate_800']}; color: {t['text_disabled']}; border-color: {t['border']}; }}

QPushButton#btn_success {{
    background: {t['green_600']}; color: #ffffff; border-color: {t['green_700']};
}}
QPushButton#btn_success:hover   {{ background: {t['green_500']}; }}
QPushButton#btn_success:pressed {{ background: {t['green_700']}; }}
QPushButton#btn_success:disabled {{ background: {t['slate_800']}; color: {t['text_disabled']}; border-color: {t['border']}; }}

QPushButton#btn_warning {{
    background: {t['amber_600']}; color: #111111; border-color: #92400e;
}}
QPushButton#btn_warning:hover   {{ background: {t['amber_500']}; }}
QPushButton#btn_warning:pressed {{ background: #92400e; color:#fff; }}
QPushButton#btn_warning:disabled {{ background: {t['slate_800']}; color: {t['text_disabled']}; border-color: {t['border']}; }}

QPushButton#btn_danger {{
    background: {t['red_600']}; color: #ffffff; border-color: {t['red_700']};
}}
QPushButton#btn_danger:hover    {{ background: {t['red_500']}; }}
QPushButton#btn_danger:pressed {{ background: {t['red_700']}; }}
QPushButton#btn_danger:disabled {{ background: {t['slate_800']}; color: {t['text_disabled']}; border-color: {t['border']}; }}

QPushButton#btn_teal {{
    background: #0d9488; color: #ffffff; border-color: #0f766e;
}}
QPushButton#btn_teal:hover   {{ background: #14b8a6; }}
QPushButton#btn_teal:pressed {{ background: #0f766e; }}

QPushButton#btn_danger_outline {{
    background: transparent; color: {t['red_500']}; border: 1px solid {t['red_500']};
}}
QPushButton#btn_danger_outline:hover   {{ background: {t['red_700']}20; }}
QPushButton#btn_danger_outline:pressed {{ background: {t['red_700']}; color: #ffffff; border-color: {t['red_700']}; }}

QPushButton#btn_amber_outline {{
    background: transparent; color: {t['amber_400']}; border: 1px solid {t['amber_600']};
}}
QPushButton#btn_amber_outline:hover   {{ background: {t['amber_600']}20; }}
QPushButton#btn_amber_outline:pressed {{ background: #92400e; color: #ffffff; }}

QPushButton#btn_purple {{
    background: #7c3aed; color: #ffffff; border-color: #6d28d9;
}}
QPushButton#btn_purple:hover   {{ background: #8b5cf6; }}
QPushButton#btn_purple:pressed {{ background: #6d28d9; }}

QPushButton#btn_ghost {{
    background: {t['bg_raised']}; color: #ffffff; border-color: {t['border']};
}}
QPushButton#btn_ghost:hover    {{ background: {t['bg_hover']}; }}
QPushButton#btn_ghost:pressed {{ background: {t['bg_active']}; }}
QPushButton#btn_ghost:disabled {{ background: {t['slate_800']}; color: {t['text_disabled']}; border-color: {t['border']}; }}

QPushButton#btn_icon_only {{
    background: transparent; border: none; padding: 4px; border-radius: 4px;
}}
QPushButton#btn_icon_only:pressed {{ background: {t['bg_hover']}; }}

QComboBox {{
    background: {t['bg_raised']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 4px 28px 4px 9px;
    color: {t['text_primary']};
    font-size: 12px;
    min-width: 60px;
}}
QComboBox:disabled {{ color: {t['text_disabled']}; background: {t['slate_800']}; }}
QComboBox::drop-down {{
    border: none;
    width: 20px;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: url("{arrow_path}");
    width: 10px;
    height: 6px;
}}
QComboBox QAbstractItemView {{
    background: {t['bg_raised']};
    border: 1px solid {t['border_focus']};
    selection-background-color: {t['blue_600']};
    selection-color: #ffffff;
    color: {t['text_primary']};
    outline: none;
    padding: 2px 0;
}}
QComboBox QAbstractItemView::item {{ padding: 5px 10px; min-height: 24px; color: {t['text_primary']}; }}
QComboBox QAbstractItemView::item:selected {{ background: {t['blue_600']}; color: #ffffff; }}

QSpinBox {{
    background: {t['bg_raised']};
    border: 1px solid {t['border']};
    border-radius: 4px;
    padding: 4px 7px;
    color: {t['text_primary']};
    font-size: 12px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 0px; height: 0px; border: none; background: transparent;
}}
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 0; height: 0; image: none; border: none;
}}

QTableWidget {{
    background: {t['bg_base']};
    gridline-color: {t['border']};
    border: 1px solid {t['border']};
    color: #ffffff;
    font-size: 12px;
    selection-background-color: {t['bg_hover']};
    selection-color: {t['text_primary']};
    outline: none;
    alternate-background-color: {t['bg_surface']};
}}
QTableWidget::item {{ padding: 0 7px; border: none; }}
QTableWidget::item:selected {{ background: {t['bg_hover']}; color: {t['text_primary']}; }}
QHeaderView::section {{
    background: {t['bg_surface']};
    color: #ffffff;
    border: none;
    border-right: 1px solid {t['border']};
    border-bottom: 2px solid {t['blue_500']};
    padding: 6px 7px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QHeaderView::section:first {{ border-left: none; }}

QProgressBar#scan_bar {{
    background: {t['bg_raised']};
    border: none;
    border-radius: 3px;
    min-height: 6px; max-height: 6px;
}}
QProgressBar#scan_bar::chunk {{
    background: {t['blue_500']};
    border-radius: 3px;
}}

QDialog {{ background: {t['bg_surface']}; border: 1px solid {t['border']}; }}
QTabWidget::pane {{
    background: {t['bg_surface']};
    border: 1px solid {t['border']};
    top: -1px;
}}
QTabBar::tab {{
    background: {t['bg_raised']};
    color: #ffffff;
    padding: 6px 16px;
    border: 1px solid {t['border']};
    border-bottom: none;
    margin-right: 2px;
    font-size: 12px;
    letter-spacing: 0.4px;
}}
QTabBar::tab:selected {{
    background: {t['bg_surface']};
    color: {t['blue_400']};
    border-bottom: 1px solid {t['bg_surface']};
    border-top: 2px solid {t['blue_500']};
}}
QGroupBox {{
    border: 1px solid {t['border']};
    border-left: 2px solid {t['blue_700']};
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 4px;
    color: {t['blue_600']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px; top: -2px;
    padding: 0 5px;
    background: {t['bg_surface']};
    color: {t['blue_400']};
}}

QRadioButton {{
    color: #ffffff;
    background: transparent;
    spacing: 6px;
    font-size: 12px;
}}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    background: {t['bg_raised']};
    border: 1px solid {t['slate_600']};
    border-radius: 7px;
}}
QRadioButton::indicator:checked {{
    background: {t['blue_600']};
    border-color: {t['blue_600']};
}}

QStatusBar {{
    background: {t['bg_base']};
    color: #ffffff;
    border-top: 2px solid {t['blue_600']};
    font-size: 11px;
    font-family: {APP_FONT_STACK};
    min-height: 26px;
    padding: 0 10px;
}}
QStatusBar::item {{ border: none; }}

QScrollBar:vertical {{
    background: {t['bg_raised']}; width: 8px; margin: 0; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {t['slate_600']}; border-radius: 4px; min-height: 28px; margin: 2px;
}}
QScrollBar::handle:vertical:pressed {{ background: {t['blue_600']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; border: none; background: none; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: {t['bg_raised']}; border-radius: 4px; }}
QScrollBar:horizontal {{
    background: {t['bg_raised']}; height: 8px; margin: 0; border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {t['slate_600']}; border-radius: 4px; min-width: 28px; margin: 2px;
}}
QScrollBar::handle:horizontal:pressed {{ background: {t['blue_600']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; border: none; background: none; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: {t['bg_raised']}; border-radius: 4px; }}

QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {t['border']}; }}

QLabel {{ color: #ffffff; background: transparent; }}
QCheckBox {{
    color: #ffffff; background: transparent;
    spacing: 6px; font-size: 12px;
}}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    background: {t['bg_raised']};
    border: 1px solid {t['slate_600']};
    border-radius: 3px;
}}
QCheckBox::indicator:checked {{ background: {t['blue_600']}; border-color: {t['blue_600']}; }}

QFrame#panel QLabel,
QFrame#panel QCheckBox,
QFrame#panel QRadioButton {{ background: {t['bg_surface']}; }}
"""

STYLE = build_style(T, _ARROW_PATH)

def IconButton(icon_name, tooltip="", color=T['text_secondary'], size=15, obj="btn_ghost"):
    btn = QPushButton()
    btn.setIcon(icon(icon_name, color, size))
    btn.setIconSize(QSize(size, size))
    btn.setObjectName(obj)
    btn.setToolTip(tooltip)
    btn.setFixedSize(32, 32)
    return btn

def TextIconButton(text, icon_name, tooltip="", obj="btn_ghost",
                   icon_color=T['text_secondary'], icon_size=14):
    btn = QPushButton(f"  {text}")
    btn.setIcon(icon(icon_name, icon_color, icon_size))
    btn.setIconSize(QSize(icon_size, icon_size))
    btn.setObjectName(obj)
    btn.setToolTip(tooltip)
    return btn

