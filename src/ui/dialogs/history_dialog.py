from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QLabel
)
from src.storage import load_history, clear_history
from src.utils import _is_valid_url
from src.theme import T, STYLE, TextIconButton, make_icon_pixmap

class HistoryDialog(QDialog):
    redownload = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.resize(840, 520)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # Search filter bar
        sr = QHBoxLayout()
        sr.setSpacing(8)
        search_ico = QLabel()
        search_ico.setPixmap(make_icon_pixmap("scan", T['text_muted'], 14))
        sr.addWidget(search_ico)
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("Search history by title, format, or URL...")
        self.le_search.setClearButtonEnabled(True)
        self.le_search.setFixedHeight(30)
        self.le_search.textChanged.connect(self._filter_history)
        sr.addWidget(self.le_search, 1)
        lay.addLayout(sr)

        self.tb = QTableWidget(0, 5)
        self.tb.setHorizontalHeaderLabels(["Date", "Title", "Format", "Size", "URL"])
        self.tb.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tb.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tb.setColumnWidth(0, 130)
        self.tb.setColumnWidth(2, 65)
        self.tb.setColumnWidth(3, 78)
        self.tb.verticalHeader().setVisible(False)
        self.tb.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tb.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tb.setAlternatingRowColors(True)
        self.tb.cellDoubleClicked.connect(lambda r, c: self._redl())
        lay.addWidget(self.tb, 1)

        for h in load_history():
            r = self.tb.rowCount()
            self.tb.insertRow(r)
            for c, key in enumerate(["date", "title", "fmt", "size", "url"]):
                it = QTableWidgetItem(str(h.get(key, "—")))
                it.setForeground(QColor(T['green_400'] if h.get("ok") else T['red_500']))
                self.tb.setItem(r, c, it)

        br = QHBoxLayout()
        br.setSpacing(8)
        b_dl = TextIconButton("Re-download", "download", obj="btn_success", icon_color="#fff")
        b_cl = TextIconButton("Clear History", "trash",  obj="btn_danger",  icon_color="#fff")
        b_cx = TextIconButton("Close",         "x",      obj="btn_ghost",   icon_color=T['text_secondary'])
        for b in (b_dl, b_cl, b_cx):
            b.setFixedHeight(34)

        b_dl.clicked.connect(self._redl)

        def _on_clear_clicked():
            clear_history()
            self.tb.setRowCount(0)

        b_cl.clicked.connect(_on_clear_clicked)
        b_cx.clicked.connect(self.close)

        br.addWidget(b_dl)
        br.addWidget(b_cl)
        br.addStretch()
        br.addWidget(b_cx)
        lay.addLayout(br)

    def _filter_history(self, text: str):
        q = text.strip().lower()
        for r in range(self.tb.rowCount()):
            if not q:
                self.tb.setRowHidden(r, False)
                continue
            title_it = self.tb.item(r, 1)
            fmt_it   = self.tb.item(r, 2)
            url_it   = self.tb.item(r, 4)
            t = (title_it.text() if title_it else "").lower()
            f = (fmt_it.text() if fmt_it else "").lower()
            u = (url_it.text() if url_it else "").lower()
            match = q in t or q in f or q in u
            self.tb.setRowHidden(r, not match)

    def _redl(self):
        row = self.tb.currentRow()
        if row >= 0:
            it = self.tb.item(row, 4)
            if it and _is_valid_url(it.text().strip()):
                self.redownload.emit(it.text().strip())

