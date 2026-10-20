import unittest
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set off-screen Qt platform for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"


from PySide6.QtWidgets import QApplication

# Ensure single QApplication instance
_app = QApplication.instance() or QApplication(sys.argv)

from src.config import (
    APP_NAME, APP_AUTHOR, APP_VER, DEFAULT_SETTINGS, _QUAL_H
)
from src.utils import (
    _is_valid_url, _validate_proxy, _validate_save_dir,
    _ensure_save_dir, _clean_err_msg, _bundled_binary, _yt_dlp_exe
)
from src.storage import (
    load_settings, save_settings, load_history, append_history, clear_history
)
from src.theme import (
    T, STYLE, make_icon_pixmap, icon, make_app_icon, TextIconButton
)
from src.workers import (
    DLSignals, DLTask, DLWorker, PlaylistExpandWorker, _UpdateThread
)
from src.ui import (
    ProgressDelegate, ScanDialog, SettingsDialog, HistoryDialog, MiniDownload
)


class TestUtils(unittest.TestCase):
    def test_valid_urls(self):
        self.assertTrue(_is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(_is_valid_url("http://example.com/video.mp4"))
        self.assertFalse(_is_valid_url("ftp://example.com/video.mp4"))
        self.assertFalse(_is_valid_url("not a url"))
        self.assertFalse(_is_valid_url(""))
        self.assertFalse(_is_valid_url("https://"))

    def test_proxy_validation(self):
        self.assertEqual(_validate_proxy("http://127.0.0.1:8080"), "http://127.0.0.1:8080")
        self.assertEqual(_validate_proxy("socks5://user:pass@10.0.0.1:1080"), "socks5://user:pass@10.0.0.1:1080")
        self.assertEqual(_validate_proxy("invalid://proxy"), "")
        self.assertEqual(_validate_proxy(""), "")

    def test_clean_err_msg(self):
        # ANSI stripping and friendly labels
        ansi_err = "\x1b[0;31mERROR: [youtube] Sign in to confirm you're not a bot\x1b[0m"
        self.assertEqual(_clean_err_msg(ansi_err), "Bot Check (Sign In)")

        err_429 = "ERROR: HTTP Error 429: Too Many Requests"
        self.assertEqual(_clean_err_msg(err_429), "429: Rate Limited")

        err_priv = "ERROR: [youtube] Private video"
        self.assertEqual(_clean_err_msg(err_priv), "Private Video")

        err_generic = "ERROR: Some unknown failure happened"
        self.assertTrue(len(_clean_err_msg(err_generic)) <= 28)

    def test_bundled_binaries(self):
        # Binaries were placed in bin/
        ffmpeg = _bundled_binary("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        self.assertIsNotNone(ffmpeg)
        self.assertTrue(ffmpeg.exists())

        ytdlp = _yt_dlp_exe()
        self.assertIsNotNone(ytdlp)
        self.assertTrue(ytdlp.exists())


class TestStorage(unittest.TestCase):
    def test_settings_load_save(self):
        s = load_settings()
        self.assertIn("save_dir", s)
        self.assertIn("max_threads", s)
        self.assertIn("default_format", s)

    def test_history_operations(self):
        clear_history()
        self.assertEqual(load_history(), [])

        entry = {
            "date": "2026-10-20 05:00",
            "title": "Test Video",
            "url": "https://example.com/test",
            "fmt": "MP4",
            "size": "10 MB",
            "ok": True
        }
        append_history(entry)
        hist = load_history()
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["title"], "Test Video")

        clear_history()
        self.assertEqual(load_history(), [])


class TestTheme(unittest.TestCase):
    def test_theme_palette(self):
        self.assertIn("bg_base", T)
        self.assertIn("blue_500", T)
        self.assertTrue(len(STYLE) > 100)

    def test_icons(self):
        pix = make_icon_pixmap("download", "#ffffff", 16)
        self.assertFalse(pix.isNull())
        ic = icon("play")
        self.assertFalse(ic.isNull())
        app_ic = make_app_icon()
        self.assertFalse(app_ic.isNull())


class TestWorkersAndTasks(unittest.TestCase):
    def test_task_init(self):
        cfg = dict(DEFAULT_SETTINGS)
        task = DLTask("dl_00001", "https://example.com/test", cfg)
        self.assertEqual(task.uid, "dl_00001")
        self.assertFalse(task._cancel)
        task.cancel()
        self.assertTrue(task._cancel)
        task.reset()
        self.assertFalse(task._cancel)

    def test_fmt_eta(self):
        self.assertEqual(DLTask._fmt_eta(0), "—")
        self.assertEqual(DLTask._fmt_eta(45), "45s")
        self.assertEqual(DLTask._fmt_eta(125), "2m 5s")
        self.assertEqual(DLTask._fmt_eta(3665), "1h 1m")

    def test_playlist_worker_init(self):
        w = PlaylistExpandWorker("https://example.com/playlist", {})
        self.assertFalse(w._cancel)
        w.cancel()
        self.assertTrue(w._cancel)


class TestUIComponents(unittest.TestCase):
    def test_dialogs(self):
        scan = ScanDialog()
        self.assertEqual(scan.windowTitle(), "")
        scan.close()
        scan.deleteLater()

        cfg = dict(DEFAULT_SETTINGS)
        settings = SettingsDialog(cfg)
        self.assertEqual(settings.windowTitle(), "Settings")
        settings.close()
        settings.deleteLater()

        history = HistoryDialog()
        self.assertEqual(history.windowTitle(), "Download History")
        # Test history search filter
        history.le_search.setText("non_existent_query_xyz")
        # All rows should be hidden
        for r in range(history.tb.rowCount()):
            self.assertTrue(history.tb.isRowHidden(r))
        history.le_search.setText("")
        for r in range(history.tb.rowCount()):
            self.assertFalse(history.tb.isRowHidden(r))
        history.close()
        history.deleteLater()
        _app.processEvents()

    def test_main_window(self):
        win = MiniDownload()
        self.assertIn(APP_NAME, win.windowTitle())
        self.assertEqual(win.table.rowCount(), 0)

        # Enqueue item
        win._enqueue("https://www.youtube.com/watch?v=dQw4w9WgXcQ", prefill_title="Rick Astley")
        self.assertEqual(win.table.rowCount(), 1)
        self.assertEqual(len(win._pending), 1)

        # Check UID mapping
        uid = win._row_uid.get(0)
        self.assertIsNotNone(uid)
        self.assertEqual(win._uid_map.get(uid), 0)

        # Test _clear_done preserves non-complete rows
        # Item 0 is in 'Waiting' state, not 'Complete'
        win._pending.clear()  # simulate finished/stopped
        win._clear_done()
        # Item should NOT be deleted because status is Waiting, not Complete
        self.assertEqual(win.table.rowCount(), 1)

        # Mark item as Complete
        win.table.item(0, win.C_STATUS).setText("Complete")
        win._clear_done()
        # Now it should be cleared!
        self.assertEqual(win.table.rowCount(), 0)

        # Clear queue
        win._clear_all()
        self.assertEqual(win.table.rowCount(), 0)
        self.assertEqual(len(win._pending), 0)

        win.close()
        win.deleteLater()
        _app.processEvents()


if __name__ == "__main__":
    unittest.main(exit=False)
    _app.processEvents()

