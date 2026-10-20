import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.config import APP_NAME, APP_VER, APP_FONT_FAMILY
from src.theme import make_app_icon
from src.ui.main_window import MiniDownload

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VER)
    app_icon = make_app_icon()
    app.setWindowIcon(app_icon)
    font = app.font()
    if hasattr(font, "setFamilies"):
        font.setFamilies([APP_FONT_FAMILY, "Khmer UI", "Leelawadee UI", "Segoe UI", "sans-serif"])
    else:
        font.setFamily(APP_FONT_FAMILY)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.NoSubpixelAntialias)
    app.setFont(font)
    win = MiniDownload()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

