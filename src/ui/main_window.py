import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QCursor, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QComboBox, QButtonGroup, QRadioButton,
    QCheckBox, QLineEdit, QStatusBar, QMessageBox, QFileDialog,
    QMenu, QApplication, QDialog
)

from src.config import APP_NAME, APP_AUTHOR, APP_VER, APP_FONT_STACK, _log
from src.utils import _is_valid_url, _ensure_save_dir
from src.storage import load_settings, save_settings, append_history
from src.theme import T, STYLE, make_app_icon, make_icon_pixmap, icon, TextIconButton
from src.ui.delegates import ProgressDelegate, PROG_ROLE
from src.ui.dialogs import ScanDialog, SettingsDialog, HistoryDialog
from src.workers import DLTask, DLWorker, PlaylistExpandWorker, _UpdateThread


class URLDropTextEdit(QTextEdit):
    """TextEdit that accepts dragged and dropped .txt files or URL links."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            lines = []
            for u in event.mimeData().urls():
                if u.isLocalFile():
                    path = u.toLocalFile()
                    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
                        try:
                            with open(path, encoding=enc, errors="replace") as f:
                                lines.extend([l.strip().strip("<>\"'") for l in f if _is_valid_url(l.strip().strip("<>\"'"))])
                            break
                        except Exception:
                            continue
                else:
                    url_str = u.toString().strip().strip("<>\"'")
                    if _is_valid_url(url_str):
                        lines.append(url_str)
            if lines:
                cur = self.toPlainText().strip()
                self.setPlainText((cur + "\n" + "\n".join(lines)).strip())
                event.acceptProposedAction()
                return
        super().dropEvent(event)


class MiniDownload(QMainWindow):
    C_NUM, C_NAME, C_BAR, C_SPEED, C_SIZE, C_ETA, C_STATUS, C_URL = range(8)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{APP_VER}  |  By {APP_AUTHOR}")
        self.setWindowIcon(make_app_icon())
        self.setMinimumSize(920, 660)
        self.resize(1040, 740)
        self.setStyleSheet(STYLE)
        self.cfg       = load_settings()
        self._tasks:   dict[str, DLTask]   = {}
        self._workers: dict[str, DLWorker] = {}
        self._pending: list[str]           = []
        self._uid_map: dict[str, int]      = {}
        self._row_uid: dict[int, str]      = {}
        self._yt_dlp_ready = False
        self._updating_ytdlp = False
        self._ctr = 0
        self._done_n = 0
        self._fail_n = 0
        self._scan_dlg = None
        self._expand_workers: list = []
        self._remove_on_finish: set[str] = set()
        # Scan state — initialized here to avoid AttributeError on early cancel
        self._scan_queue: list = []
        self._scan_stop = False
        self._scan_total = 0
        self._scan_done = 0
        self._scan_added = 0
        self._build()
        self._check_dep()
        self._sync_ui_from_cfg()
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._tick_status)
        self._status_timer.start(1000)

    def _build(self):
        mb = self.menuBar()
        m_app = mb.addMenu("Application")
        a_pref = QAction("  Preferences", self)
        a_pref.setShortcut("Ctrl+,")
        a_pref.triggered.connect(self._open_settings)
        m_app.addAction(a_pref)
        m_app.addSeparator()
        a_quit = QAction("  Exit", self)
        a_quit.setShortcut("Ctrl+Q")
        a_quit.triggered.connect(self.close)
        m_app.addAction(a_quit)

        m_tools = mb.addMenu("Tools")
        a_hist = QAction("  Download History", self)
        a_hist.triggered.connect(self._open_history)
        m_tools.addAction(a_hist)
        self.a_update_ytdlp = QAction("  Update yt-dlp", self)
        self.a_update_ytdlp.triggered.connect(self._update_ytdlp)
        m_tools.addAction(self.a_update_ytdlp)
        a_open = QAction("  Open Save Folder", self)
        a_open.triggered.connect(self._open_folder)
        m_tools.addAction(a_open)

        m_help = mb.addMenu("Help")
        a_about = QAction("  About", self)
        a_about.triggered.connect(
            lambda: QMessageBox.information(
                self, "About",
                f"<b>{APP_NAME} {APP_VER}</b><br>By {APP_AUTHOR}<br><br>Multithreaded Video Downloader<br>"
                "Powered by <b>yt-dlp</b> and <b>PySide6</b><br>Supports 1,000+ sites"
            )
        )
        m_help.addAction(a_about)

        cw = QWidget()
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(8)
        cl.addWidget(self._build_url_panel())
        cl.addWidget(self._build_options_panel())
        cl.addWidget(self._build_queue_panel(), 1)
        cl.addWidget(self._build_toolbar())
        cl.addWidget(self._build_action_bar())
        root.addWidget(content, 1)

        self.sb = QStatusBar()
        self.setStatusBar(self.sb)
        self.sb_msg = QLabel("Ready")
        self.sb_msg.setStyleSheet(
            f"color:#ffffff; background:transparent;"
            f" font-size:11px; font-family:{APP_FONT_STACK}; padding:0 4px;"
        )
        self.sb.addWidget(self.sb_msg, 1)

        self._stats_w = QWidget()
        stats_w = self._stats_w
        stats_w.setStyleSheet("background:transparent;")
        stats_w.setMinimumWidth(320)
        stats_l = QHBoxLayout(stats_w)
        stats_l.setContentsMargins(0, 0, 12, 0)
        stats_l.setSpacing(20)

        def _stat(prefix, color):
            lbl = QLabel(f"{prefix}: 0")
            lbl.setStyleSheet(
                f"color:{color}; background:transparent;"
                f" font-size:11px; font-weight:700;"
                f" font-family:{APP_FONT_STACK}; padding:0 6px;"
            )
            lbl.setMinimumWidth(70)
            return lbl

        self._sb_queue  = _stat("Queue",  T['text_secondary'])
        self._sb_active = _stat("Active", T['blue_400'])
        self._sb_done   = _stat("Done",   T['green_400'])
        self._sb_fail   = _stat("Failed", T['red_500'])
        for l in (self._sb_queue, self._sb_active, self._sb_done, self._sb_fail):
            stats_l.addWidget(l)
        self.sb.addPermanentWidget(stats_w)

    def _build_url_panel(self):
        frame = QFrame()
        frame.setObjectName("panel")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)
        hr = QHBoxLayout()
        sec_ico = QLabel()
        sec_ico.setPixmap(make_icon_pixmap("link", T['text_muted'], 12))
        sec_lbl = QLabel("ADD VIDEO LINKS")
        sec_lbl.setObjectName("sec_lbl")
        hint = QLabel("One URL per line  ·  YouTube  TikTok  Instagram  Twitter  1,000+ sites")
        hint.setStyleSheet("color:#ffffff; font-size:10px;")
        hr.addWidget(sec_ico)
        hr.addSpacing(5)
        hr.addWidget(sec_lbl)
        hr.addSpacing(10)
        hr.addWidget(hint)
        hr.addStretch()
        self.lbl_url_count = QLabel("")
        self.lbl_url_count.setStyleSheet(
            f"color:{T['blue_400']}; font-size:11px; font-weight:700; background:{T['bg_surface']}; font-family:{APP_FONT_STACK};"
        )
        hr.addWidget(self.lbl_url_count)
        lay.addLayout(hr)
        self.url_area = URLDropTextEdit()
        self.url_area.setObjectName("url_area")
        self.url_area.setPlaceholderText(
            "https://www.youtube.com/watch?v=…\nhttps://www.tiktok.com/@user/video/…\nhttps://vimeo.com/…"
        )
        self.url_area.setFixedHeight(82)
        self.url_area.textChanged.connect(self._update_url_count)
        lay.addWidget(self.url_area)
        br = QHBoxLayout()
        br.setSpacing(6)
        self.btn_paste    = TextIconButton("Paste",     "clipboard", obj="btn_warning",        icon_color="#0f1117", icon_size=13)
        self.btn_clear    = TextIconButton("Clear",     "x",         obj="btn_danger_outline",  icon_color="#ffffff", icon_size=13)
        self.btn_loadfile = TextIconButton("Load File", "upload",    obj="btn_purple",          icon_color="#ffffff", icon_size=13)
        for b, fn in (
            (self.btn_paste, self._paste),
            (self.btn_clear, self.url_area.clear),
            (self.btn_loadfile, self._load_file)
        ):
            b.setFixedHeight(30)
            b.clicked.connect(fn)
            br.addWidget(b)
        br.addStretch()
        lay.addLayout(br)
        return frame

    def _build_options_panel(self):
        frame = QFrame()
        frame.setObjectName("panel")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(20)
        left = QVBoxLayout()
        left.setSpacing(8)
        lh = QHBoxLayout()
        lh_ico = QLabel()
        lh_ico.setPixmap(make_icon_pixmap("cpu", T['text_muted'], 12))
        lh_lbl = QLabel("OUTPUT SETTINGS")
        lh_lbl.setObjectName("sec_lbl")
        lh.addWidget(lh_ico)
        lh.addSpacing(5)
        lh.addWidget(lh_lbl)
        lh.addStretch()
        left.addLayout(lh)
        snr = QHBoxLayout()
        snr.setSpacing(12)
        snl = QLabel("Save name:")
        snl.setStyleSheet("color:#ffffff; font-size:11px;")
        snr.addWidget(snl)
        self._sn_grp    = QButtonGroup(self)
        self.chk_sn_t   = QRadioButton("Title")
        self.chk_sn_tid = QRadioButton("Title + ID")
        self.chk_sn_id  = QRadioButton("ID only")
        self._sn_grp.addButton(self.chk_sn_t,   0)
        self._sn_grp.addButton(self.chk_sn_tid, 1)
        self._sn_grp.addButton(self.chk_sn_id,  2)
        self.chk_sn_t.setChecked(True)
        for c in (self.chk_sn_t, self.chk_sn_tid, self.chk_sn_id):
            snr.addWidget(c)
        snr.addStretch()
        left.addLayout(snr)
        exr = QHBoxLayout()
        exr.setSpacing(12)
        exl = QLabel("Extras:")
        exl.setStyleSheet("color:#ffffff; font-size:11px;")
        exr.addWidget(exl)
        self.chk_thumb = QCheckBox("Thumbnail")
        self.chk_desc  = QCheckBox("Description")
        self.chk_subs  = QCheckBox("Subtitles")
        for c in (self.chk_thumb, self.chk_desc, self.chk_subs):
            exr.addWidget(c)
        exr.addStretch()
        left.addLayout(exr)
        fqr = QHBoxLayout()
        fqr.setSpacing(10)
        fl = QLabel("Format:")
        fl.setStyleSheet("color:#ffffff; font-size:11px;")
        self.cb_fmt = QComboBox()
        self.cb_fmt.addItems(["MP4", "MKV", "WEBM", "MP3", "M4A"])
        self.cb_fmt.setFixedHeight(30)
        ql = QLabel("Quality:")
        ql.setStyleSheet("color:#ffffff; font-size:11px;")
        self.cb_q = QComboBox()
        self.cb_q.addItems(["Best", "4K", "2K", "1080", "720", "480", "360"])
        self.cb_q.setFixedHeight(30)
        fqr.addWidget(fl)
        fqr.addWidget(self.cb_fmt)
        fqr.addSpacing(6)
        fqr.addWidget(ql)
        fqr.addWidget(self.cb_q)
        fqr.addStretch()
        self.cb_fmt.currentIndexChanged.connect(self._on_fmt_changed)
        self.cb_q.currentIndexChanged.connect(
            lambda _: self.cfg.update({"default_quality": self.cb_q.currentText()})
        )
        left.addLayout(fqr)
        lay.addLayout(left, 2)
        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        lay.addWidget(div)
        right = QVBoxLayout()
        right.setSpacing(8)
        rh = QHBoxLayout()
        rh_ico = QLabel()
        rh_ico.setPixmap(make_icon_pixmap("folder", T['text_muted'], 12))
        rh_lbl = QLabel("SAVE LOCATION")
        rh_lbl.setObjectName("sec_lbl")
        rh.addWidget(rh_ico)
        rh.addSpacing(5)
        rh.addWidget(rh_lbl)
        rh.addStretch()
        right.addLayout(rh)
        self.le_folder = QLineEdit(self.cfg["save_dir"])
        self.le_folder.setReadOnly(True)
        self.le_folder.setFixedHeight(30)
        right.addWidget(self.le_folder)
        dbr = QHBoxLayout()
        dbr.setSpacing(6)
        self.btn_chg = TextIconButton("Change Folder", "folder_open", obj="btn_warning", icon_color="#0f1117", icon_size=13)
        self.btn_opn = TextIconButton("Open Folder",   "folder_open", obj="btn_teal",    icon_color="#ffffff",  icon_size=13)
        self.btn_chg.setFixedHeight(30)
        self.btn_opn.setFixedHeight(30)
        self.btn_chg.clicked.connect(self._pick_dir)
        self.btn_opn.clicked.connect(self._open_folder)
        dbr.addWidget(self.btn_chg)
        dbr.addWidget(self.btn_opn)
        right.addLayout(dbr)
        lay.addLayout(right, 2)
        return frame

    def _build_queue_panel(self):
        frame = QFrame()
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        hr = QHBoxLayout()
        hr.setContentsMargins(2, 0, 2, 0)
        qh_ico = QLabel()
        qh_ico.setPixmap(make_icon_pixmap("list", T['text_muted'], 12))
        self.lbl_q = QLabel("DOWNLOAD QUEUE")
        self.lbl_q.setObjectName("sec_lbl")
        self.lbl_q_count = QLabel("0 items")
        self.lbl_q_count.setStyleSheet("color:#ffffff; font-size:11px;")
        hr.addWidget(qh_ico)
        hr.addSpacing(5)
        hr.addWidget(self.lbl_q)
        hr.addStretch()
        hr.addWidget(self.lbl_q_count)
        lay.addLayout(hr)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["#", "File Name", "Progress", "Speed", "Size", "ETA", "Status", "URL"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(self.C_NAME, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(self.C_URL,  QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(self.C_NUM,    36)
        self.table.setColumnWidth(self.C_BAR,   130)
        self.table.setColumnWidth(self.C_SPEED,  80)
        self.table.setColumnWidth(self.C_SIZE,   74)
        self.table.setColumnWidth(self.C_ETA,    50)
        self.table.setColumnWidth(self.C_STATUS, 125)

        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._ctx_menu)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.setItemDelegateForColumn(self.C_BAR, ProgressDelegate(self.table))
        self.table.verticalHeader().setDefaultSectionSize(32)
        lay.addWidget(self.table, 1)
        return frame

    def _build_toolbar(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 2, 0, 2)
        lay.setSpacing(6)
        self.btn_del   = TextIconButton("Delete Selected", "trash",        obj="btn_ghost", icon_color=T['red_500'],        icon_size=13)
        self.btn_clra  = TextIconButton("Clear All",       "x",            obj="btn_ghost", icon_color=T['text_secondary'], icon_size=13)
        self.btn_clrd  = TextIconButton("Clear Done",      "check_circle", obj="btn_ghost", icon_color=T['green_400'],      icon_size=13)
        self.btn_retry = TextIconButton("Retry Failed",    "rotate_cw",    obj="btn_ghost", icon_color=T['amber_400'],      icon_size=13)
        _ss = lambda clr: (
            f"QPushButton {{ color:{clr}; background:{T['bg_raised']}; border:1px solid {T['border']};"
            f" border-radius:5px; font-size:12px; font-weight:600; padding:5px 14px; }}"
        )
        self.btn_del.setStyleSheet(_ss(T['red_500']))
        self.btn_clrd.setStyleSheet(_ss(T['green_400']))
        self.btn_retry.setStyleSheet(_ss(T['amber_400']))
        for b, fn in (
            (self.btn_del,   self._delete_selected),
            (self.btn_clra,  self._clear_all),
            (self.btn_clrd,  self._clear_done),
            (self.btn_retry, self._retry_all)
        ):
            b.setFixedHeight(28)
            b.clicked.connect(fn)
            lay.addWidget(b)
        lay.addStretch()
        tl = QLabel("Threads")
        tl.setStyleSheet("color:#ffffff; font-size:11px;")
        self.sp_threads = QComboBox()
        self.sp_threads.addItems([str(i) for i in range(1, 17)])
        cur_t = str(self.cfg.get("max_threads", 4))
        idx = self.sp_threads.findText(cur_t)
        self.sp_threads.setCurrentIndex(idx if idx >= 0 else 3)
        self.sp_threads.setFixedWidth(68)
        self.sp_threads.setFixedHeight(28)
        self.sp_threads.currentTextChanged.connect(lambda v: self.cfg.update({"max_threads": int(v)}))
        lay.addWidget(tl)
        lay.addWidget(self.sp_threads)
        return w

    def _build_action_bar(self):
        w = QWidget()
        w.setStyleSheet(f"background:{T['bg_surface']}; border-top:1px solid {T['border']};")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(6)
        self.btn_scan   = TextIconButton("Scan Link",  "scan",      obj="btn_amber_outline", icon_color=T['amber_400'], icon_size=14)
        self.btn_noscrp = TextIconButton("No Scrap",   "zap",       obj="btn_amber_outline", icon_color=T['amber_400'], icon_size=14)
        self.btn_dl     = TextIconButton("Download",   "download",  obj="btn_success",       icon_color="#fff",         icon_size=14)
        self.btn_stop   = TextIconButton("Stop",       "square",    obj="btn_danger",        icon_color="#fff",         icon_size=14)
        self.btn_update = TextIconButton("Update API", "rotate_cw", obj="btn_primary",       icon_color="#fff",         icon_size=14)
        self.btn_scan.setToolTip("Scan URLs — expand playlists into individual videos  [Ctrl+Shift+S]")
        self.btn_noscrp.setToolTip("Add URLs directly to queue without scanning  [Ctrl+Shift+A]")
        self.btn_dl.setToolTip("Start downloading all queued items  [Ctrl+D]")
        self.btn_stop.setToolTip("Stop all active downloads  [Ctrl+.]")
        self.btn_update.setToolTip("Update yt-dlp to latest version")
        self.btn_scan.setShortcut("Ctrl+Shift+S")
        self.btn_noscrp.setShortcut("Ctrl+Shift+A")
        self.btn_dl.setShortcut("Ctrl+D")
        self.btn_stop.setShortcut("Ctrl+.")
        for b in (self.btn_scan, self.btn_noscrp, self.btn_dl, self.btn_stop, self.btn_update):
            b.setFixedHeight(38)
            lay.addWidget(b, 1)
        self.btn_scan.clicked.connect(self._scan_links)
        self.btn_noscrp.clicked.connect(self._add_direct)
        self.btn_dl.clicked.connect(self._download_all)
        self.btn_stop.clicked.connect(self._stop_all)
        self.btn_update.clicked.connect(self._update_ytdlp)
        return w

    def _on_fmt_changed(self):
        fmt = self.cb_fmt.currentText()
        self.cfg["default_format"] = fmt
        is_audio = fmt in ("MP3", "M4A")
        self.cb_q.setEnabled(not is_audio)

    def _check_dep(self):
        try:
            import yt_dlp
            ver = getattr(yt_dlp.version, '__version__', None) or "unknown"
            self._set_status(f"yt-dlp ready ✓  (v{ver})")
            self._yt_dlp_ready = True
        except ImportError:
            self._set_status("⚠  yt-dlp not installed — click Update API to install")
            self._yt_dlp_ready = False
        self._sync_action_state()

    def _sync_ui_from_cfg(self):
        self.le_folder.setText(self.cfg["save_dir"])
        self.cb_fmt.setCurrentText(self.cfg["default_format"])
        self.cb_q.setCurrentText(self.cfg["default_quality"])
        self.chk_thumb.setChecked(self.cfg.get("thumbnail", False))
        self.chk_desc.setChecked(self.cfg.get("description", False))
        self.chk_subs.setChecked(self.cfg.get("subtitles", False))
        idx = self.sp_threads.findText(str(self.cfg.get("max_threads", 4)))
        self.sp_threads.setCurrentIndex(idx if idx >= 0 else 3)
        m = self.cfg.get("save_name_mode", "title")
        self.chk_sn_t.setChecked(m == "title")
        self.chk_sn_tid.setChecked(m == "title_id")
        self.chk_sn_id.setChecked(m == "id")
        if not any(r.isChecked() for r in (self.chk_sn_t, self.chk_sn_tid, self.chk_sn_id)):
            self.chk_sn_t.setChecked(True)
        self.cb_q.setEnabled(self.cb_fmt.currentText() not in ("MP3", "M4A"))

    def _read_ui_cfg(self) -> dict:
        """Sync the current UI control values into self.cfg and return it."""
        self.cfg["default_format"]  = self.cb_fmt.currentText()
        self.cfg["default_quality"] = self.cb_q.currentText()
        self.cfg["max_threads"]     = int(self.sp_threads.currentText())
        self.cfg["thumbnail"]       = self.chk_thumb.isChecked()
        self.cfg["description"]     = self.chk_desc.isChecked()
        self.cfg["subtitles"]       = self.chk_subs.isChecked()
        if self.chk_sn_tid.isChecked():
            self.cfg["save_name_mode"] = "title_id"
        elif self.chk_sn_id.isChecked():
            self.cfg["save_name_mode"] = "id"
        else:
            self.cfg["save_name_mode"] = "title"
        return self.cfg

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Choose Save Folder", self.cfg.get("save_dir", ""))
        if d:
            self.cfg["save_dir"] = d
            self.le_folder.setText(d)
            save_settings(self.cfg)
            self._set_status(f"Save folder changed: {d}")

    def _open_folder(self):
        p = self.cfg.get("save_dir", str(Path.home() / "Downloads"))
        try:
            folder = _ensure_save_dir(p)
            folder_str = str(folder)
            if sys.platform == "win32":
                os.startfile(folder_str)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder_str])
            else:
                subprocess.Popen(["xdg-open", folder_str])
            self._set_status(f"Opened folder: {folder_str}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{e}")

    def _get_urls(self):
        seen = set()
        result = []
        for l in self.url_area.toPlainText().splitlines():
            url = l.strip().strip("<>\"'")
            if _is_valid_url(url) and url not in seen:
                seen.add(url)
                result.append(url)
        return result

    def _update_url_count(self):
        n = len(self._get_urls())
        self.lbl_url_count.setText(f"{n} URL{'s' if n != 1 else ''}" if n else "")

    def _set_status(self, msg):
        self.sb_msg.setText(msg)

    def _tick_status(self):
        self._sb_queue.setText(f"Queue: {len(self._pending)}")
        self._sb_active.setText(f"Active: {len(self._workers)}")
        self._sb_done.setText(f"Done: {self._done_n}")
        self._sb_fail.setText(f"Failed: {self._fail_n}")
        self._sync_action_state()

    def _downloads_active(self) -> bool:
        return bool(self._workers)

    def _block_if_downloading(self, action: str) -> bool:
        if not self._downloads_active():
            return False
        self._set_status(f"Stop active download(s) before {action}")
        self._sync_action_state()
        return True

    def _block_if_queue_action_locked(self, action: str) -> bool:
        if self._block_if_downloading(action):
            return True
        if self._updating_ytdlp:
            self._set_status(f"Wait for yt-dlp update to finish before {action}")
            self._sync_action_state()
            return True
        if not self._yt_dlp_ready:
            self._set_status("yt-dlp is not ready; click Update API first")
            self._sync_action_state()
            return True
        return False

    def _sync_action_state(self):
        if not hasattr(self, "btn_scan"):
            return
        downloads_active = self._downloads_active()
        has_pending = bool(self._pending)
        can_queue_action = self._yt_dlp_ready and not downloads_active and not self._updating_ytdlp
        can_download = can_queue_action and has_pending
        can_update = not downloads_active and not self._updating_ytdlp
        self.btn_scan.setEnabled(can_queue_action)
        self.btn_noscrp.setEnabled(can_queue_action)
        self.btn_dl.setEnabled(can_download)
        self.btn_update.setEnabled(can_update)
        self.btn_stop.setEnabled(downloads_active)
        if hasattr(self, "a_update_ytdlp"):
            self.a_update_ytdlp.setEnabled(can_update)

    def _paste(self):
        txt = QApplication.clipboard().text().strip()
        if not txt:
            self._set_status("Clipboard is empty")
            return
        cur_lines = [l for l in self.url_area.toPlainText().splitlines() if l.strip()]
        new_lines = [l.strip() for l in txt.splitlines() if l.strip()]
        existing = set(cur_lines)
        added = [l for l in new_lines if l not in existing]
        all_lines = cur_lines + added
        self.url_area.setPlainText("\n".join(all_lines))
        self._set_status(f"Pasted {len(added)} new URL(s) from clipboard" if added else "URLs already in list")

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load URL list", str(Path.home()), "Text files (*.txt);;All files (*)")
        if not path:
            return
        lines = []
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                with open(path, encoding=enc, errors="replace") as f:
                    lines = [l.strip() for l in f if _is_valid_url(l.strip())]
                break
            except (OSError, UnicodeDecodeError):
                continue
        if not lines:
            self._set_status("No valid URLs found in file")
            return
        cur = self.url_area.toPlainText().strip()
        self.url_area.setPlainText((cur + "\n" + "\n".join(lines)).strip())
        self._set_status(f"Loaded {len(lines)} URLs from {Path(path).name}")

    def _open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_cfg = dlg.get_settings()
            self.cfg.update(new_cfg)   # update IN-PLACE so live DLTask references stay valid
            save_settings(self.cfg)
            self._sync_ui_from_cfg()
            self._set_status("Settings saved")

    def _open_history(self):
        dlg = HistoryDialog(self)
        def _on_redownload(url):
            if _is_valid_url(url):
                cur = self.url_area.toPlainText().strip()
                if cur:
                    urls = [u.strip() for u in cur.splitlines() if u.strip()]
                    if url not in urls:
                        self.url_area.setPlainText(cur + "\n" + url)
                else:
                    self.url_area.setPlainText(url)
                self._set_status("URL loaded from history")
                dlg.close()
        dlg.redownload.connect(_on_redownload)
        dlg.exec()

    def _update_ytdlp(self):
        if self._block_if_downloading("updating yt-dlp"):
            return
        if self._updating_ytdlp:
            self._set_status("yt-dlp update is already running")
            return
        self._updating_ytdlp = True
        self._sync_action_state()
        self._set_status("Updating yt-dlp…")

        def _on_done(ok, msg):
            self._updating_ytdlp = False
            if ok:
                self._yt_dlp_ready = True
                self._set_status(msg or "yt-dlp updated successfully")
            else:
                self._set_status(f"Update failed: {msg}")
            self._sync_action_state()
            QTimer.singleShot(0, lambda: setattr(self, "_update_thread", None))

        self._update_thread = _UpdateThread()
        self._update_thread.done.connect(_on_done)
        self._update_thread.start()

    def _scan_links(self):
        if self._block_if_queue_action_locked("scanning links"):
            return
        urls = self._get_urls()
        if not urls:
            self._set_status("No URLs to scan")
            return
        if self.cfg.get("no_playlist"):
            self._add_direct()
            self._set_status("Playlist scanning is disabled; added direct URL(s)")
            return

        if hasattr(self, "_scan_timer"):
            self._scan_timer.stop()
        if self._scan_dlg:
            self._scan_dlg.close()
            self._scan_dlg = None

        for w in list(self._expand_workers):
            w.cancel()
        for w in list(self._expand_workers):
            w.wait(2000)
        self._expand_workers = [w for w in self._expand_workers if w.isRunning()]
        if self._expand_workers:
            self._set_status("Previous scan is still stopping; try again shortly")
            return

        self._scan_queue   = list(urls)
        self._scan_stop    = False
        self._scan_total   = len(urls)
        self._scan_done    = 0
        self._scan_added   = 0

        self._scan_dlg = ScanDialog(self)
        self._scan_dlg.cancelled.connect(self._scan_cancel)
        gp = self.geometry()
        self._scan_dlg.move(gp.x() + (gp.width() - 380) // 2,
                            gp.y() + (gp.height() - 190) // 2)
        self._scan_dlg.show()
        self._scan_dlg.set_progress("Starting…", 0, self._scan_total)

        self._scan_next_url()

    def _scan_next_url(self):
        if self._scan_stop or not self._scan_queue:
            self._scan_finish()
            return

        url = self._scan_queue.pop(0)
        self._scan_done += 1

        if self._scan_dlg:
            self._scan_dlg.set_progress(url, self._scan_done, self._scan_total)

        worker = PlaylistExpandWorker(url, {"proxy": self.cfg.get("proxy", "")})
        worker.playlist_found.connect(self._on_expand_playlist_found,
                                      Qt.ConnectionType.QueuedConnection)
        worker.video_found.connect(self._on_expand_video_found,
                                   Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(
            lambda ok, msg, w=worker: self._on_expand_finished(ok, msg, w),
            Qt.ConnectionType.QueuedConnection
        )
        self._expand_workers.append(worker)
        worker.start()

    def _on_expand_playlist_found(self, pl_title: str, total: int):
        if self._scan_dlg and pl_title:
            self._scan_dlg.lbl_url.setText(f"Playlist: {pl_title[:50]}  ({total} videos)")
            self._scan_dlg.lbl_count.setText(f"{self._scan_done} / {self._scan_total} URLs  •  expanding…")

    def _on_expand_video_found(self, idx: int, total: int, vid_url: str, vid_title: str):
        if self._scan_stop:
            return
        if self._scan_dlg:
            self._scan_dlg.set_progress(vid_url, idx, total)
        self._enqueue(vid_url, prefill_title=vid_title)
        self._scan_added += 1
        self._update_q_label()

    def _on_expand_finished(self, ok: bool, msg: str, worker=None):
        if worker in self._expand_workers:
            self._expand_workers.remove(worker)
        if worker:
            worker.deleteLater()
        if not ok and not self._scan_stop:
            self._set_status(f"Scan error: {msg}")
            _log.warning("Expand finished with error: %s", msg)
        if not self._scan_stop:
            self._scan_next_url()

    def _scan_cancel(self):
        self._scan_stop = True
        for w in list(self._expand_workers):
            w.cancel()
        for w in list(self._expand_workers):
            w.wait(500)
        self._expand_workers = [w for w in self._expand_workers if w.isRunning()]
        if hasattr(self, "_scan_timer"):
            self._scan_timer.stop()
        self._scan_finish()

    def _scan_finish(self):
        if self._scan_dlg:
            if not self._scan_stop:
                self._scan_dlg.finish()
            else:
                self._scan_dlg.close()
            dlg = self._scan_dlg
            self._scan_dlg = None
            QTimer.singleShot(500, dlg.deleteLater)
        self._update_q_label()
        if self._scan_stop:
            self._set_status(f"Scan stopped — {self._scan_added} video(s) added")
        else:
            self._set_status(f"Scan complete — {self._scan_added} video(s) added to queue")

    def _add_direct(self):
        if self._block_if_queue_action_locked("adding URLs without scan"):
            return
        urls = self._get_urls()
        if not urls:
            self._set_status("No URLs to add")
            return
        for url in urls:
            self._enqueue(url)
        self._update_q_label()
        self._set_status(f"Added {len(urls)} URL(s) to queue")

    def _new_uid(self):
        self._ctr += 1
        return f"dl_{self._ctr:05d}"

    def _enqueue(self, url, force=False, prefill_title: str = ""):
        if not force:
            for uid, task in list(self._tasks.items()):
                if task.url == url and (uid in self._pending or uid in self._workers):
                    return
        uid = self._new_uid()
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 32)

        def _it(txt, align=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, clr=T['text_secondary']):
            i = QTableWidgetItem(txt)
            i.setTextAlignment(align)
            i.setForeground(QColor(clr))
            return i

        C = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        display_name = prefill_title[:80] if prefill_title else (url[:60] + "…" if len(url) > 60 else url)
        num_item = _it(str(row + 1), C, T['text_muted'])
        num_item.setData(Qt.ItemDataRole.UserRole, uid)
        self.table.setItem(row, self.C_NUM,    num_item)
        self.table.setItem(row, self.C_NAME,   _it(display_name, clr=T['text_primary'] if prefill_title else T['text_secondary']))
        pi = QTableWidgetItem()
        pi.setData(PROG_ROLE, (0.0, "waiting"))
        self.table.setItem(row, self.C_BAR, pi)
        for col, txt in ((self.C_SPEED, "—"), (self.C_SIZE, "—"), (self.C_ETA, "—")):
            self.table.setItem(row, col, _it(txt, C, T['text_muted']))
        self.table.setItem(row, self.C_STATUS, _it("Waiting", C, T['text_secondary']))
        self.table.setItem(row, self.C_URL,    _it(url, clr=T['text_muted']))
        task = DLTask(uid, url, self.cfg)
        task.sig.progress.connect(self._on_progress, Qt.ConnectionType.QueuedConnection)
        task.sig.finished.connect(self._on_finished, Qt.ConnectionType.QueuedConnection)
        task.sig.title.connect(self._on_title, Qt.ConnectionType.QueuedConnection)
        self._tasks[uid] = task
        self._uid_map[uid] = row
        self._row_uid[row] = uid
        self._pending.append(uid)
        self._update_q_label()

    def _update_q_label(self):
        n = self.table.rowCount()
        self.lbl_q_count.setText(f"{n} item{'s' if n != 1 else ''}")
        self._sync_action_state()

    def _ctx_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        uid = self._row_uid.get(row)
        task = self._tasks.get(uid) if uid else None
        has_file = bool(task and getattr(task, "filepath", None) and Path(task.filepath).exists())
        file_path = task.filepath if has_file else None

        m = QMenu(self)
        m.setStyleSheet(STYLE)

        # Contextual actions for completed downloads with valid local files
        if has_file:
            a_play = QAction(icon("play", T['green_400']), "  Play File", self)
            a_play.triggered.connect(lambda: self._open_file(file_path))
            m.addAction(a_play)

            a_show = QAction(icon("folder_open", T['blue_400']), "  Show in Folder", self)
            a_show.triggered.connect(lambda: self._show_in_folder(file_path))
            m.addAction(a_show)
            m.addSeparator()

        for label, fn, ico_n in [
            ("Start",    lambda u=uid: self._start_worker(u) if u and u in self._pending and u in self._tasks else None, "play"),
            ("Stop",     lambda u=uid: self._tasks[u].cancel() if u and u in self._tasks and u in self._workers else None, "square"),
            ("Retry",    lambda u=uid: self._retry_uid(u) if u else None, "rotate_cw"),
            (None, None, None),
            ("Copy URL", lambda r=row: QApplication.clipboard().setText(
                self.table.item(r, self.C_URL).text() if self.table.item(r, self.C_URL) else ""), "link"),
            ("Remove",   lambda u=uid: self._remove_uid(u) if u else None, "trash"),
        ]:
            if label is None:
                m.addSeparator()
                continue
            a = QAction(icon(ico_n), f"  {label}", self)
            a.triggered.connect(fn)
            m.addAction(a)
        m.exec(QCursor.pos())

    def _on_cell_double_clicked(self, row, column):
        uid = self._row_uid.get(row)
        if not uid or uid not in self._tasks:
            return
        task = self._tasks[uid]
        it_st = self.table.item(row, self.C_STATUS)
        status_text = it_st.text() if it_st else ""
        if status_text == "Complete":
            if getattr(task, "filepath", None) and Path(task.filepath).exists():
                self._open_file(task.filepath)
            else:
                self._open_folder()
        elif status_text in ("Failed", "Network Timeout", "403: Forbidden", "Stopped") or "Error" in status_text:
            self._retry_uid(uid)

    def _open_file(self, filepath: str):
        try:
            p = str(Path(filepath).resolve())
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])
            self._set_status(f"Opening: {Path(p).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{e}")

    def _show_in_folder(self, filepath: str):
        try:
            p = str(Path(filepath).resolve())
            if sys.platform == "win32":
                subprocess.Popen(["explorer", f"/select,{p}"])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", p])
            else:
                subprocess.Popen(["xdg-open", str(Path(p).parent)])
            self._set_status(f"Showing in folder: {Path(p).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not show file in folder:\n{e}")

    def _download_all(self):
        if self._block_if_queue_action_locked("downloading"):
            return
        if not self._pending:
            self._set_status("Nothing pending to download")
            return
        max_t = int(self.sp_threads.currentText())
        slots = max(0, max_t - len(self._workers))
        if slots == 0:
            self._set_status(f"All {max_t} thread(s) busy — {len(self._pending)} queued")
            return
        started = 0
        to_start = list(self._pending[:slots])
        for uid in to_start:
            self._start_worker(uid)
            started += 1
        self._set_status(f"Started {started} download(s)  [{max_t} threads, {len(self._pending)} pending]")

    def _start_worker(self, uid):
        if uid not in self._tasks:
            return
        if uid in self._workers:
            return
        self._read_ui_cfg()
        self._tasks[uid].cfg = dict(self.cfg)
        if uid in self._pending:
            self._pending.remove(uid)
        w = DLWorker(self._tasks[uid])
        w.finished.connect(lambda checked=False, u=uid: self._thread_done(u))
        self._workers[uid] = w
        w.start()
        self._set_cell_clr(uid, self.C_STATUS, "Downloading", T['blue_400'])
        self._set_prog(uid, 0.0, "running")
        self._sync_action_state()

    def _thread_done(self, uid):
        worker = self._workers.pop(uid, None)
        if worker:
            worker.deleteLater()
        if uid in self._remove_on_finish:
            self._remove_finished_uid(uid)
        threads_text = self.sp_threads.currentText()
        max_t = int(threads_text) if threads_text.isdigit() else self.cfg.get("max_threads", 4)
        while len(self._workers) < max_t and self._pending:
            next_uid = self._pending[0]
            if next_uid in self._tasks:
                self._start_worker(next_uid)
            else:
                self._pending.pop(0)
        self._sync_action_state()

    def closeEvent(self, event):
        if self._workers:
            reply = QMessageBox.question(
                self, "Exit",
                f"{len(self._workers)} download(s) still in progress.\nExit and cancel them?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if hasattr(self, "_status_timer"):
            self._status_timer.stop()
        for w in list(self._expand_workers):
            w.cancel()
        for w in list(self._expand_workers):
            w.wait(1000)
        for t in self._tasks.values():
            t.cancel()
        self._pending.clear()
        for w in list(self._workers.values()):
            w.wait(1000)
        for uid, w in list(self._workers.items()):
            if not w.isRunning():
                self._workers.pop(uid, None)
                w.deleteLater()
        if hasattr(self, "_update_thread") and self._update_thread and self._update_thread.isRunning():
            self._update_thread.wait(1000)
        self._read_ui_cfg()
        save_settings(self.cfg)
        event.accept()

    def _stop_all(self):
        for uid, t in self._tasks.items():
            t.cancel()
            if uid in self._pending:
                self._set_cell_clr(uid, self.C_STATUS, "Stopped", T['text_secondary'])
                row = self._uid_map.get(uid, -1)
                self._set_prog(uid, self._get_prog(row) if row >= 0 else 0.0, "stopped")
        self._pending.clear()
        self._set_status(f"Stop signal sent to {len(self._workers)} active download(s)")
        self._sync_action_state()

    def _retry_uid(self, uid):
        if uid not in self._tasks:
            return
        if uid in self._workers:
            self._set_status("Cannot retry a download that is currently running")
            return
        if uid in self._remove_on_finish:
            self._set_status("That item is still stopping; retry after it exits")
            return
        self._tasks[uid].reset()
        if uid not in self._pending:
            self._pending.append(uid)
        self._set_cell_clr(uid, self.C_STATUS, "Waiting", T['text_secondary'])
        self._set_prog(uid, 0.0, "waiting")
        threads_text = self.sp_threads.currentText()
        max_t = int(threads_text) if threads_text.isdigit() else self.cfg.get("max_threads", 4)
        if len(self._workers) < max_t:
            self._start_worker(uid)

    def _retry_all(self):
        ids = [
            u for u in self._tasks
            if u not in self._workers and u not in self._pending
            and self._uid_map.get(u, -1) >= 0
        ]
        for uid in ids:
            self._retry_uid(uid)
        if ids:
            self._set_status(f"Retrying {len(ids)} failed download(s)")

    def _on_progress(self, uid, pct, speed, size, eta):
        self._set_prog(uid, pct, "running")
        self._set_cell_clr(uid, self.C_SPEED,  speed, T['blue_400'])
        self._set_cell_clr(uid, self.C_SIZE,   size,  T['text_secondary'])
        self._set_cell_clr(uid, self.C_ETA,    eta,   T['text_muted'])
        self._set_cell_clr(uid, self.C_STATUS, f"{pct:.0f}%", T['blue_400'])

    def _on_finished(self, uid, ok, msg, size):
        if uid in self._pending:
            self._pending.remove(uid)
        row = self._uid_map.get(uid, -1)
        if row < 0:
            return
        if uid in self._remove_on_finish:
            self._set_cell_clr(uid, self.C_STATUS, "Stopped", T['text_secondary'])
            self._set_prog(uid, self._get_prog(row), "stopped")
            return
        if ok:
            clr = T['green_400']
            state = "done"
            self._done_n += 1
        else:
            clr   = T['text_secondary'] if msg == "Stopped" else T['red_500']
            state = "stopped" if msg == "Stopped" else "error"
            if state == "error":
                self._fail_n += 1
        self._set_prog(uid, 100.0 if ok else self._get_prog(row), state)
        self._set_cell_clr(uid, self.C_STATUS, msg[:22], clr)
        if not ok and 0 <= row < self.table.rowCount():
            it_st = self.table.item(row, self.C_STATUS)
            if it_st:
                it_st.setToolTip(f"{msg}\n(Tip: Preferences -> Network -> Cookies File)")
        self._set_cell_clr(uid, self.C_SPEED,  "—", T['text_muted'])
        self._set_cell_clr(uid, self.C_ETA,    "—", T['text_muted'])
        if size != "—":
            self._set_cell_clr(uid, self.C_SIZE, size, clr)
        ni = self.table.item(row, self.C_NAME)
        ui = self.table.item(row, self.C_URL)
        fmt = self._tasks[uid].cfg.get("default_format", "") if uid in self._tasks else self.cb_fmt.currentText()
        real_title = ni.text() if ni else ""
        append_history({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "title": real_title,
            "url": ui.text() if ui else "",
            "fmt": fmt,
            "size": size,
            "ok": ok
        })
        self.sb_msg.setText(f"{'Done' if ok else 'Failed'}: {real_title[:60]}")

    def _on_title(self, uid, title):
        self._set_cell_clr(uid, self.C_NAME, title, T['text_primary'])

    def _set_cell_clr(self, uid, col, txt, clr):
        row = self._uid_map.get(uid, -1)
        if row < 0 or row >= self.table.rowCount():
            return
        it = self.table.item(row, col)
        if it is None:
            it = QTableWidgetItem()
            self.table.setItem(row, col, it)
        it.setText(txt)
        it.setForeground(QColor(clr))

    def _set_prog(self, uid, pct, state):
        row = self._uid_map.get(uid, -1)
        if row < 0 or row >= self.table.rowCount():
            return
        it = self.table.item(row, self.C_BAR)
        if not it:
            it = QTableWidgetItem()
            self.table.setItem(row, self.C_BAR, it)
        it.setData(PROG_ROLE, (pct, state))
        rect = self.table.visualRect(self.table.model().index(row, self.C_BAR))
        self.table.viewport().update(rect)

    def _get_prog(self, row):
        if row < 0 or row >= self.table.rowCount():
            return 0.0
        it = self.table.item(row, self.C_BAR)
        if it:
            d = it.data(PROG_ROLE)
            if d and isinstance(d, (tuple, list)):
                return d[0]
        return 0.0

    def _remove_uid(self, uid):
        if not uid:
            return
        if uid in self._workers:
            self._tasks[uid].cancel()
            self._remove_on_finish.add(uid)
            self._set_cell_clr(uid, self.C_STATUS, "Stopping", T['text_secondary'])
            self._set_status("Download is stopping; it will be removed when the worker exits")
            return
        if uid in self._tasks:
            self._tasks[uid].cancel()
        row = self._uid_map.pop(uid, -1)
        self._tasks.pop(uid, None)
        self._workers.pop(uid, None)
        self._row_uid.pop(row, None)
        self._remove_on_finish.discard(uid)
        if uid in self._pending:
            self._pending.remove(uid)
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
        self._rebuild_maps()
        self._update_q_label()

    def _delete_selected(self):
        rows = sorted({i.row() for i in self.table.selectedItems()}, reverse=True)
        for row in rows:
            uid = self._row_uid.get(row)
            if uid:
                if uid in self._workers:
                    self._tasks[uid].cancel()
                    self._remove_on_finish.add(uid)
                    self._set_cell_clr(uid, self.C_STATUS, "Stopping", T['text_secondary'])
                    continue
                if uid in self._tasks:
                    self._tasks[uid].cancel()
                self._tasks.pop(uid, None)
                self._workers.pop(uid, None)
                self._uid_map.pop(uid, None)
                self._remove_on_finish.discard(uid)
                if uid in self._pending:
                    self._pending.remove(uid)
            self._row_uid.pop(row, None)
            if row < self.table.rowCount():
                self.table.removeRow(row)
        self._rebuild_maps()
        self._update_q_label()

    def _clear_all(self):
        if self._workers:
            reply = QMessageBox.question(
                self, "Clear All",
                f"{len(self._workers)} download(s) still active.\nStop and clear everything?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        for t in self._tasks.values():
            t.cancel()
        active = set(self._workers)
        for uid in active:
            self._remove_on_finish.add(uid)
            self._set_cell_clr(uid, self.C_STATUS, "Stopping", T['text_secondary'])
        self._pending.clear()
        remove_uids = [uid for uid in list(self._tasks) if uid not in active]
        rows_to_remove = sorted(
            [self._uid_map.get(uid, -1) for uid in remove_uids if self._uid_map.get(uid, -1) >= 0],
            reverse=True
        )
        for uid in remove_uids:
            self._tasks.pop(uid, None)
            row = self._uid_map.pop(uid, -1)
            self._row_uid.pop(row, None)
            self._remove_on_finish.discard(uid)
        for row in rows_to_remove:
            if row < self.table.rowCount():
                self.table.removeRow(row)
        self._rebuild_maps()
        self._done_n = 0
        self._fail_n = 0
        self._update_q_label()
        self._set_status("Queue cleared")

    def _clear_done(self):
        done_uids = []
        for uid, row in list(self._uid_map.items()):
            if uid not in self._workers and uid not in self._pending:
                it_st = self.table.item(row, self.C_STATUS)
                if it_st and it_st.text() == "Complete":
                    done_uids.append(uid)
        if not done_uids:
            self._set_status("No completed downloads to clear")
            return
        rows_to_remove = sorted(
            [self._uid_map[uid] for uid in done_uids if self._uid_map.get(uid, -1) >= 0],
            reverse=True
        )
        for uid in done_uids:
            self._tasks.pop(uid, None)
            row = self._uid_map.pop(uid, -1)
            self._row_uid.pop(row, None)
            self._remove_on_finish.discard(uid)
        for row in rows_to_remove:
            if row < self.table.rowCount():
                self.table.removeRow(row)
        self._rebuild_maps()
        self._update_q_label()
        self._set_status(f"Cleared {len(done_uids)} completed download(s)")

    def _rebuild_maps(self):
        self._uid_map.clear()
        self._row_uid.clear()
        for r in range(self.table.rowCount()):
            num_item = self.table.item(r, self.C_NUM)
            if num_item:
                uid = num_item.data(Qt.ItemDataRole.UserRole)
                if uid:
                    self._uid_map[uid] = r
                    self._row_uid[r] = uid
                num_item.setText(str(r + 1))

    def _remove_finished_uid(self, uid):
        if uid in self._workers:
            return
        row = self._uid_map.pop(uid, -1)
        self._tasks.pop(uid, None)
        self._row_uid.pop(row, None)
        self._remove_on_finish.discard(uid)
        if uid in self._pending:
            self._pending.remove(uid)
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
        self._rebuild_maps()
        self._update_q_label()

