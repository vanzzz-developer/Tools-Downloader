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
    ProgressDelegate, ScanDialog, SettingsDialog, HistoryDialog, PlaylistSelectDialog, MiniDownload
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

    def test_audio_settings_validation(self):
        save_settings({"default_format": "WAV"})
        self.assertEqual(load_settings()["default_format"], "WAV")
        save_settings({"default_format": "FLAC"})
        self.assertEqual(load_settings()["default_format"], "FLAC")
        save_settings(dict(DEFAULT_SETTINGS))

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

    def test_audio_formats_and_hls_progress(self):
        self.assertIn("WAV", DLTask.RES)
        self.assertIn("FLAC", DLTask.RES)
        self.assertEqual(DLTask.RES["WAV"], "bestaudio/best")
        self.assertEqual(DLTask.RES["FLAC"], "bestaudio/best")

        # Test HLS progress calculation via _hook
        cfg = dict(DEFAULT_SETTINGS)
        task = DLTask("dl_hls", "https://example.com/stream", cfg)
        progress_captured = []
        task.sig.progress.connect(lambda uid, pct, spd, eta, sz: progress_captured.append((pct, spd, eta, sz)))

        # When total_bytes is None, uses fragment_index / fragment_count
        hls_hook_data = {
            "status": "downloading",
            "downloaded_bytes": 1024 * 1024,
            "total_bytes": None,
            "fragment_index": 5,
            "fragment_count": 10,
            "speed": 1024 * 500,
            "eta": 30,
        }
        task._hook(hls_hook_data)
        self.assertTrue(len(progress_captured) > 0)
        self.assertEqual(progress_captured[-1][0], 50)  # 5 / 10 = 50%


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

        # PlaylistSelectDialog
        videos = [("https://example.com/v1", "Song 1"), ("https://example.com/v2", "Song 2")]
        pl_dlg = PlaylistSelectDialog("Test Album", videos)
        self.assertEqual(len(pl_dlg.selected_items), 2)
        pl_dlg._deselect_all()
        self.assertEqual(len(pl_dlg.selected_items), 0)
        pl_dlg._select_all()
        self.assertEqual(len(pl_dlg.selected_items), 2)
        pl_dlg.close()
        pl_dlg.deleteLater()

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

        # Test clear failed and dynamic status counters
        win._enqueue("https://example.com/v1", prefill_title="V1")
        win._enqueue("https://example.com/v2", prefill_title="V2")
        win._enqueue("https://example.com/v3", prefill_title="V3")
        win._pending.clear()

        win.table.item(0, win.C_STATUS).setText("Complete")
        win.table.item(1, win.C_STATUS).setText("Failed")
        win.table.item(2, win.C_STATUS).setText("Waiting")
        win._update_status_counters()

        self.assertEqual(win._sb_done.text(), "Done: 1")
        self.assertEqual(win._sb_fail.text(), "Failed: 1")

        # Test _clear_failed removes failed row
        win._clear_failed()
        self.assertEqual(win.table.rowCount(), 2)
        self.assertEqual(win._sb_fail.text(), "Failed: 0")

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

