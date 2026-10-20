import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.config import APP_NAME, APP_VER, APP_FONT_FAMILY
from src.theme import make_app_icon
from src.ui.main_window import MiniDownload

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = f"vannsothunh.{APP_NAME}.{APP_VER}".replace(" ", "")
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

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
    win.setWindowIcon(app_icon)
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

