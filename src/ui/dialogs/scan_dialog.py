from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
from src.theme import T, STYLE, make_icon_pixmap, TextIconButton

class ScanDialog(QDialog):
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setFixedSize(380, 190)
        self.setStyleSheet(STYLE)
        self._anim = 0
        self._build()
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
        self._t.start(20)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        card = QFrame()
        card.setObjectName("panel")
        bg = T['bg_raised']
        card.setStyleSheet(
            f"QFrame#panel {{ background: {bg}; border: 1px solid {T['blue_600']}; border-radius: 10px; }}"
            f"QLabel {{ background: {bg}; }}"
        )
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        outer.addWidget(card)

        tr = QHBoxLayout()
        tr.setSpacing(10)
        ico_lbl = QLabel()
        ico_lbl.setPixmap(make_icon_pixmap("scan", T['blue_400'], 20))
        ico_lbl.setStyleSheet(f"background: {bg};")
        tr.addWidget(ico_lbl)

        title = QLabel("Scanning Links")
        title.setStyleSheet(f"color:#ffffff; font-size:15px; font-weight:700; background:{bg};")
        tr.addWidget(title)
        tr.addStretch()
        lay.addLayout(tr)

        self.lbl_url = QLabel("Initialising...")
        self.lbl_url.setStyleSheet(f"color:{T['blue_400']}; font-size:11px; font-weight:600; background:{bg};")
        self.lbl_url.setWordWrap(True)
        lay.addWidget(self.lbl_url)

        self.lbl_count = QLabel("0 / 0")
        self.lbl_count.setStyleSheet(f"color:#ffffff; font-size:11px; background:{bg};")
        lay.addWidget(self.lbl_count)

        self.bar = QProgressBar()
        self.bar.setObjectName("scan_bar")
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        lay.addWidget(self.bar)

        br = QHBoxLayout()
        hint = QLabel("Click Stop to cancel")
        hint.setStyleSheet(f"color:#ffffff; font-size:10px; background:{bg};")
        br.addWidget(hint)
        br.addStretch()

        btn = TextIconButton("Stop", "square", obj="btn_danger", icon_color="#fff", icon_size=12)
        btn.setFixedHeight(30)
        btn.setFixedWidth(90)
        btn.clicked.connect(self._stop)
        br.addWidget(btn)
        lay.addLayout(br)

    def set_progress(self, url: str, idx: int, total: int):
        short = url[:55] + "…" if len(url) > 55 else url
        self.lbl_url.setText(f"Processing:  {short}")
        self.lbl_count.setText(f"{idx} / {total}")
        if total > 0:
            self.bar.setRange(0, total)
            self.bar.setValue(idx)

    def _tick(self):
        if self.bar.maximum() == 100:
            self._anim = (self._anim + 2) % 108
            v = self._anim if self._anim <= 100 else 200 - self._anim
            self.bar.setValue(int(v))

    def _stop(self):
        self._t.stop()
        self.cancelled.emit()
        self.close()

    def finish(self):
        self._t.stop()
        self.bar.setRange(0, 100)
        self.bar.setValue(100)
        QTimer.singleShot(400, self.close)

