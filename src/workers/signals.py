from PySide6.QtCore import QObject, Signal

class DLSignals(QObject):
    progress = Signal(str, float, str, str, str)
    finished = Signal(str, bool, str, str)
    title    = Signal(str, str)

