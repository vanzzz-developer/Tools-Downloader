from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
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
        title.setStyleSheet(f"color:{T['text_primary']}; font-size:15px; font-weight:700; background:{bg};")
        tr.addWidget(title)
        tr.addStretch()
        lay.addLayout(tr)

        self.lbl_url = QLabel("Initialising...")
        self.lbl_url.setStyleSheet(f"color:{T['blue_400']}; font-size:11px; font-weight:600; background:{bg};")
        self.lbl_url.setWordWrap(True)
        lay.addWidget(self.lbl_url)

        self.lbl_count = QLabel("0 / 0")
        self.lbl_count.setStyleSheet(f"color:{T['text_secondary']}; font-size:11px; background:{bg};")
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
        hint.setStyleSheet(f"color:{T['text_muted']}; font-size:10px; background:{bg};")
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


class PlaylistSelectDialog(QDialog):
    """Interactive modal allowing users to select/deselect videos from a playlist before enqueuing."""
    def __init__(self, pl_title: str, items: list[tuple[str, str]], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Playlist Videos")
        self.resize(760, 480)
        self.setStyleSheet(STYLE)
        self.pl_title = pl_title or "Playlist"
        self.raw_items = items  # list of (url, title)
        self._build()

    @property
    def selected_items(self) -> list[tuple[str, str]]:
        if hasattr(self, "_checks") and self._checks:
            return [self.raw_items[i] for i, c in enumerate(self._checks) if c.isChecked()]
        return []

    def _build(self):
        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # Header info
        hr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(make_icon_pixmap("list", T['blue_400'], 18))
        hr.addWidget(ico)
        lbl_t = QLabel(f"Playlist: {self.pl_title}")
        lbl_t.setStyleSheet(f"font-size:14px; font-weight:700; color:{T['text_primary']};")
        hr.addWidget(lbl_t, 1)
        self.lbl_stats = QLabel(f"Selected: {len(self.raw_items)} / {len(self.raw_items)}")
        self.lbl_stats.setStyleSheet(f"color:{T['blue_400']}; font-weight:600; font-size:12px;")
        hr.addWidget(self.lbl_stats)
        lay.addLayout(hr)

        # Quick action buttons row
        ar = QHBoxLayout()
        ar.setSpacing(8)
        b_all = TextIconButton("Select All", "check_circle", obj="btn_ghost", icon_color=T['green_400'])
        b_none = TextIconButton("Deselect All", "x", obj="btn_ghost", icon_color=T['red_500'])
        b_all.setFixedHeight(28)
        b_none.setFixedHeight(28)
        b_all.clicked.connect(self._select_all)
        b_none.clicked.connect(self._deselect_all)
        ar.addWidget(b_all)
        ar.addWidget(b_none)
        ar.addStretch()
        lay.addLayout(ar)

        # Table
        self.tb = QTableWidget(len(self.raw_items), 3)
        self.tb.setHorizontalHeaderLabels(["", "Title", "URL"])
        self.tb.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tb.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tb.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tb.setColumnWidth(0, 36)
        self.tb.verticalHeader().setVisible(False)
        self.tb.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tb.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tb.setAlternatingRowColors(True)

        self._checks = []
        for r, (url, title) in enumerate(self.raw_items):
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(self._update_stats)
            self._checks.append(chk)
            self.tb.setCellWidget(r, 0, chk)

            it_t = QTableWidgetItem(title)
            it_t.setForeground(QColor(T['text_primary']))
            self.tb.setItem(r, 1, it_t)

            it_u = QTableWidgetItem(url)
            it_u.setForeground(QColor(T['text_secondary']))
            self.tb.setItem(r, 2, it_u)

        lay.addWidget(self.tb, 1)

        # Bottom buttons
        br = QHBoxLayout()
        br.setSpacing(10)
        self.b_add = TextIconButton("Add Selected to Queue", "download", obj="btn_primary", icon_color="#fff")
        self.b_add.setFixedHeight(34)
        self.b_add.clicked.connect(self._accept_selection)

        b_cancel = TextIconButton("Cancel", "x", obj="btn_ghost", icon_color=T['text_secondary'])
        b_cancel.setFixedHeight(34)
        b_cancel.clicked.connect(self.reject)

        br.addStretch()
        br.addWidget(b_cancel)
        br.addWidget(self.b_add)
        lay.addLayout(br)

    def _select_all(self):
        for c in self._checks:
            c.setChecked(True)
        self._update_stats()

    def _deselect_all(self):
        for c in self._checks:
            c.setChecked(False)
        self._update_stats()

    def _update_stats(self):
        sel = sum(1 for c in self._checks if c.isChecked())
        self.lbl_stats.setText(f"Selected: {sel} / {len(self._checks)}")
        self.b_add.setEnabled(sel > 0)

    def _accept_selection(self):
        self.accept()


