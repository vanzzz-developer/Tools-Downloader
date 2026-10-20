import os, sys, subprocess
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QLabel, QMessageBox
)
from src.storage import load_history, clear_history
from src.utils import _is_valid_url
from src.theme import T, STYLE, TextIconButton, make_icon_pixmap

class HistoryDialog(QDialog):
    redownload = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Download History")
        self.resize(880, 530)
        self.setStyleSheet(STYLE)
        self._history_items = []
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
        self.tb.cellDoubleClicked.connect(lambda r, c: self._on_double_click(r))
        lay.addWidget(self.tb, 1)

        self._history_items = load_history()
        for h in self._history_items:
            r = self.tb.rowCount()
            self.tb.insertRow(r)
            is_ok = bool(h.get("ok"))
            for c, key in enumerate(["date", "title", "fmt", "size", "url"]):
                it = QTableWidgetItem(str(h.get(key, "—")))
                if c == 0:
                    it.setForeground(QColor(T['green_400'] if is_ok else T['red_500']))
                else:
                    it.setForeground(QColor(T['text_primary'] if c == 1 else T['text_secondary']))
                if c == 0:
                    it.setData(Qt.ItemDataRole.UserRole, h)
                self.tb.setItem(r, c, it)

        br = QHBoxLayout()
        br.setSpacing(8)
        self.b_play = TextIconButton("Play File", "play", obj="btn_teal", icon_color="#fff")
        self.b_folder = TextIconButton("Show in Folder", "folder_open", obj="btn_purple", icon_color="#fff")
        self.b_dl = TextIconButton("Re-download", "download", obj="btn_success", icon_color="#fff")
        self.b_cl = TextIconButton("Clear History", "trash",  obj="btn_danger",  icon_color="#fff")
        self.b_cx = TextIconButton("Close", "x", obj="btn_ghost", icon_color=T['text_secondary'])
        for b in (self.b_play, self.b_folder, self.b_dl, self.b_cl, self.b_cx):
            b.setFixedHeight(34)

        self.b_play.clicked.connect(self._play_file)
        self.b_folder.clicked.connect(self._show_folder)
        self.b_dl.clicked.connect(self._redl)

        def _on_clear_clicked():
            clear_history()
            self.tb.setRowCount(0)
            self._history_items.clear()

        self.b_cl.clicked.connect(_on_clear_clicked)
        self.b_cx.clicked.connect(self.close)

        br.addWidget(self.b_play)
        br.addWidget(self.b_folder)
        br.addWidget(self.b_dl)
        br.addWidget(self.b_cl)
        br.addStretch()
        br.addWidget(self.b_cx)
        lay.addLayout(br)

    def _get_selected_entry(self) -> dict | None:
        row = self.tb.currentRow()
        if row >= 0:
            it = self.tb.item(row, 0)
            if it:
                return it.data(Qt.ItemDataRole.UserRole)
        return None

    def _play_file(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        fp = entry.get("filepath")
        if fp and Path(fp).exists():
            try:
                if sys.platform == "win32":
                    os.startfile(fp)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", fp])
                else:
                    subprocess.Popen(["xdg-open", fp])
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not play file:\n{e}")
        else:
            QMessageBox.information(self, "File Not Found", "The downloaded file was moved or deleted.")

    def _show_folder(self):
        entry = self._get_selected_entry()
        if not entry:
            return
        fp = entry.get("filepath")
        folder = str(Path(fp).parent) if fp and Path(fp).parent.exists() else None
        if not folder:
            QMessageBox.information(self, "Folder Not Found", "The target folder does not exist.")
            return
        try:
            if sys.platform == "win32":
                if fp and Path(fp).exists():
                    subprocess.Popen(["explorer", f"/select,{fp}"])
                else:
                    os.startfile(folder)
            elif sys.platform == "darwin":
                if fp and Path(fp).exists():
                    subprocess.Popen(["open", "-R", fp])
                else:
                    subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{e}")

    def _on_double_click(self, row: int):
        it = self.tb.item(row, 0)
        entry = it.data(Qt.ItemDataRole.UserRole) if it else None
        if entry and entry.get("filepath") and Path(entry["filepath"]).exists():
            self._play_file()
        else:
            self._redl()

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

