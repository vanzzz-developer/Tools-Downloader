import re
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QComboBox, QGroupBox, QButtonGroup, QRadioButton, QCheckBox,
    QTabWidget, QWidget, QDialogButtonBox, QFileDialog, QMessageBox
)
from src.theme import T, STYLE, TextIconButton

class SettingsDialog(QDialog):
    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setStyleSheet(STYLE)
        self.cfg = dict(cfg)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        tabs = QTabWidget()
        lay.addWidget(tabs)

        w = QWidget()
        wl = QVBoxLayout(w)
        wl.setSpacing(10)
        g1 = QGroupBox("DOWNLOAD SETTINGS")
        g1l = QVBoxLayout(g1)
        g1l.setSpacing(8)
        fr = QHBoxLayout()
        self.le_dir = QLineEdit(self.cfg["save_dir"])
        self.le_dir.setReadOnly(True)
        b = TextIconButton("Browse", "folder", obj="btn_ghost", icon_color=T['text_secondary'])
        b.setFixedHeight(32)
        b.clicked.connect(self._pick_dir)
        fr.addWidget(QLabel("Save folder:"))
        fr.addWidget(self.le_dir, 1)
        fr.addWidget(b)
        g1l.addLayout(fr)

        tr = QHBoxLayout()
        self.sp_threads = QSpinBox()
        self.sp_threads.setRange(1, 16)
        self.sp_threads.setValue(self.cfg["max_threads"])
        self.sp_threads.setFixedWidth(70)
        tr.addWidget(QLabel("Max threads:"))
        tr.addWidget(self.sp_threads)
        tr.addStretch()
        g1l.addLayout(tr)

        rr = QHBoxLayout()
        self.le_rate = QLineEdit(self.cfg.get("rate_limit", ""))
        self.le_rate.setPlaceholderText("e.g. 2M  (empty = unlimited)")
        rr.addWidget(QLabel("Rate limit:"))
        rr.addWidget(self.le_rate, 1)
        g1l.addLayout(rr)
        wl.addWidget(g1)

        g2 = QGroupBox("FORMAT & QUALITY")
        g2l = QVBoxLayout(g2)
        g2l.setSpacing(8)
        fqr = QHBoxLayout()
        fqr.setSpacing(12)
        self.cb_fmt = QComboBox()
        self.cb_fmt.addItems(["MP4", "MKV", "WEBM", "MP3", "M4A"])
        self.cb_fmt.setCurrentText(self.cfg["default_format"])
        self.cb_q = QComboBox()
        self.cb_q.addItems(["Best", "4K", "2K", "1080", "720", "480", "360"])
        self.cb_q.setCurrentText(self.cfg["default_quality"])
        fqr.addWidget(QLabel("Format:"))
        fqr.addWidget(self.cb_fmt)
        fqr.addWidget(QLabel("Quality:"))
        fqr.addWidget(self.cb_q)
        fqr.addStretch()
        self.cb_fmt.currentIndexChanged.connect(
            lambda _: self.cb_q.setEnabled(self.cb_fmt.currentText() not in ("MP3", "M4A"))
        )
        self.cb_q.setEnabled(self.cfg["default_format"] not in ("MP3", "M4A"))
        g2l.addLayout(fqr)
        wl.addWidget(g2)
        wl.addStretch()
        tabs.addTab(w, "  General  ")

        w2 = QWidget()
        w2l = QVBoxLayout(w2)
        w2l.setSpacing(10)
        g3 = QGroupBox("FILENAME TEMPLATE")
        g3l = QVBoxLayout(g3)
        g3l.setSpacing(6)
        self._name_grp = QButtonGroup(self)
        self.rb_title = QRadioButton("Title  (e.g. My Video.mp4)")
        self.rb_tid   = QRadioButton("Title + ID  (e.g. My Video [abc123].mp4)")
        self.rb_id    = QRadioButton("ID only  (e.g. abc123.mp4)")
        self._name_grp.addButton(self.rb_title, 0)
        self._name_grp.addButton(self.rb_tid,   1)
        self._name_grp.addButton(self.rb_id,    2)
        m = self.cfg.get("save_name_mode", "title")
        self.rb_title.setChecked(m == "title")
        self.rb_tid.setChecked(m == "title_id")
        self.rb_id.setChecked(m == "id")
        if not any(r.isChecked() for r in (self.rb_title, self.rb_tid, self.rb_id)):
            self.rb_title.setChecked(True)
        for c in (self.rb_title, self.rb_tid, self.rb_id):
            g3l.addWidget(c)
        w2l.addWidget(g3)

        g4 = QGroupBox("EXTRA FILES")
        g4l = QVBoxLayout(g4)
        g4l.setSpacing(6)
        self.chk_thumb  = QCheckBox("Download Thumbnail")
        self.chk_desc   = QCheckBox("Write Description")
        self.chk_subs   = QCheckBox("Download Subtitles")
        self.chk_esub   = QCheckBox("Embed Subtitles in file")
        self.chk_ethumb = QCheckBox("Embed Thumbnail in file")
        self.chk_info   = QCheckBox("Write .info.json")
        for c, k in (
            (self.chk_thumb, "thumbnail"), (self.chk_desc, "description"),
            (self.chk_subs, "subtitles"), (self.chk_esub, "embed_subs"),
            (self.chk_ethumb, "embed_thumb"), (self.chk_info, "write_info_json")
        ):
            c.setChecked(self.cfg.get(k, False))
            g4l.addWidget(c)
        sr = QHBoxLayout()
        self.le_slang = QLineEdit(self.cfg.get("subtitle_lang", "en"))
        self.le_slang.setFixedWidth(80)
        sr.addWidget(QLabel("Subtitle language:"))
        sr.addWidget(self.le_slang)
        sr.addStretch()
        g4l.addLayout(sr)
        w2l.addWidget(g4)
        w2l.addStretch()
        tabs.addTab(w2, "  Metadata  ")

        w3 = QWidget()
        w3l = QVBoxLayout(w3)
        w3l.setSpacing(10)
        g5 = QGroupBox("PROXY")
        g5l = QVBoxLayout(g5)
        self.le_proxy = QLineEdit(self.cfg.get("proxy", ""))
        self.le_proxy.setPlaceholderText("http://user:pass@host:port  or  socks5://...")
        g5l.addWidget(self.le_proxy)
        w3l.addWidget(g5)

        g_cookie = QGroupBox("COOKIES FILE (OPTIONAL)")
        g_cookiel = QVBoxLayout(g_cookie)
        cr = QHBoxLayout()
        self.le_cookie = QLineEdit(self.cfg.get("cookie_file", ""))
        self.le_cookie.setPlaceholderText("Path to cookies.txt (for age-gated or private videos)")
        b_ck = TextIconButton("Browse", "folder", obj="btn_ghost", icon_color=T['text_secondary'])
        b_ck.setFixedHeight(30)
        b_ck.clicked.connect(self._pick_cookie)
        cr.addWidget(self.le_cookie, 1)
        cr.addWidget(b_ck)
        g_cookiel.addLayout(cr)
        w3l.addWidget(g_cookie)

        g6 = QGroupBox("ADVANCED")
        g6l = QVBoxLayout(g6)
        g6l.setSpacing(6)
        self.chk_noplst  = QCheckBox("Single video only — skip playlist (download only the linked video)")
        self.chk_sponsor = QCheckBox("SponsorBlock — skip sponsor segments")
        self.chk_noplst.setChecked(self.cfg.get("no_playlist", False))
        self.chk_sponsor.setChecked(self.cfg.get("sponsorblock", False))
        for c in (self.chk_noplst, self.chk_sponsor):
            g6l.addWidget(c)
        w3l.addWidget(g6)
        w3l.addStretch()
        tabs.addTab(w3, "  Network  ")

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        ok_btn = bb.button(QDialogButtonBox.StandardButton.Ok)
        ca_btn = bb.button(QDialogButtonBox.StandardButton.Cancel)
        ok_btn.setObjectName("btn_primary")
        ca_btn.setObjectName("btn_ghost")
        ok_btn.setFixedHeight(34)
        ca_btn.setFixedHeight(34)
        bb.accepted.connect(self._accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Choose folder", self.cfg["save_dir"])
        if d:
            self.cfg["save_dir"] = d
            self.le_dir.setText(d)

    def _pick_cookie(self):
        f, _ = QFileDialog.getOpenFileName(self, "Choose cookies.txt", str(Path.home()), "Cookies (*.txt);;All files (*)")
        if f:
            self.le_cookie.setText(f)

    def _accept(self):
        rate_raw = self.le_rate.text().strip()
        if rate_raw:
            if not re.match(r'^\d+(\.\d+)?[KMGkmg]?$', rate_raw):
                QMessageBox.warning(
                    self, "Invalid Rate Limit",
                    "Rate limit must be a number optionally followed by K, M, or G.\n"
                    "Examples: 500K  2M  1.5G"
                )
                return
        if self.rb_tid.isChecked():
            name_mode = "title_id"
        elif self.rb_id.isChecked():
            name_mode = "id"
        else:
            name_mode = "title"

        self.cfg.update({
            "save_dir": self.le_dir.text(),
            "max_threads": self.sp_threads.value(),
            "default_format": self.cb_fmt.currentText(),
            "default_quality": self.cb_q.currentText(),
            "rate_limit": self.le_rate.text().strip(),
            "save_name_mode": name_mode,
            "thumbnail": self.chk_thumb.isChecked(),
            "description": self.chk_desc.isChecked(),
            "subtitles": self.chk_subs.isChecked(),
            "embed_subs": self.chk_esub.isChecked(),
            "embed_thumb": self.chk_ethumb.isChecked(),
            "write_info_json": self.chk_info.isChecked(),
            "subtitle_lang": self.le_slang.text().strip() or "en",
            "proxy": self.le_proxy.text().strip(),
            "cookie_file": self.le_cookie.text().strip(),
            "no_playlist": self.chk_noplst.isChecked(),
            "sponsorblock": self.chk_sponsor.isChecked(),
        })
        self.accept()

    def get_settings(self):
        return self.cfg

