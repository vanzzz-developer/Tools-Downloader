from pathlib import Path
from PySide6.QtCore import QThread, Signal
from src.config import _log
from src.utils import _apply_runtime_paths, _validate_proxy, _clean_err_msg

class PlaylistExpandWorker(QThread):
    """
    Background thread: fetches playlist metadata with yt-dlp and emits
    each individual video entry so the main thread can enqueue them one-by-one.
    """
    playlist_found  = Signal(str, int)
    video_found     = Signal(int, int, str, str)
    finished        = Signal(bool, str)

    def __init__(self, url: str, cfg: dict):
        super().__init__()
        self.url  = url
        self.cfg  = cfg
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            import yt_dlp
        except ImportError:
            self.finished.emit(False, "yt-dlp not installed")
            return

        opts = {
            "quiet":          True,
            "no_warnings":    True,
            "extract_flat":   "in_playlist",
            "noplaylist":     False,
            "socket_timeout": 30,
            "retries":        10,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "mweb"]
                }
            },
        }

        _apply_runtime_paths(opts)
        if self.cfg.get("cookie_file") and Path(self.cfg["cookie_file"]).exists():
            opts["cookiefile"] = str(Path(self.cfg["cookie_file"]).resolve())
        if self.cfg.get("proxy"):
            safe_proxy = _validate_proxy(str(self.cfg["proxy"]))
            if safe_proxy:
                opts["proxy"] = safe_proxy

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if self._cancel:
                self.finished.emit(False, "Cancelled")
                return

            if info is None:
                self.finished.emit(False, "Could not fetch URL info")
                return

            entries = info.get("entries")
            if entries is not None:
                pl_title = info.get("title") or "Playlist"
                est_total = info.get("playlist_count") or 0
                self.playlist_found.emit(pl_title, est_total)

                idx = 0
                for entry in entries:
                    if self._cancel:
                        self.finished.emit(False, "Cancelled")
                        return
                    if not entry:
                        continue
                    idx += 1
                    vid_url = (entry.get("webpage_url")
                               or entry.get("url")
                               or (f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get("id") else ""))
                    if not vid_url:
                        continue
                    vid_title = entry.get("title") or entry.get("id") or vid_url
                    total_reported = max(est_total, idx)
                    self.video_found.emit(idx, total_reported, vid_url, vid_title)

                self.finished.emit(True, "")
            else:
                vid_title = info.get("title") or self.url
                self.playlist_found.emit("", 1)
                self.video_found.emit(1, 1, self.url, vid_title)
                self.finished.emit(True, "")

        except Exception as e:
            msg = str(e)
            if "cancel" in msg.lower():
                self.finished.emit(False, "Cancelled")
            else:
                _log.error("PlaylistExpand url=%s error=%s", self.url, msg)
                clean = _clean_err_msg(msg)
                self.finished.emit(False, clean)

