from pathlib import Path
from PySide6.QtCore import QThread
from src.config import _log, _QUAL_H
from src.utils import _ensure_save_dir, _apply_runtime_paths, _validate_proxy, _clean_err_msg
from src.workers.signals import DLSignals

class DLTask:
    RES = {
        "Best": "bestvideo+bestaudio/best",
        "4K":   "bestvideo[height<=2160]+bestaudio/best[height<=2160]/best",
        "2K":   "bestvideo[height<=1440]+bestaudio/best[height<=1440]/best",
        "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "720":  "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "480":  "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        "360":  "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
        "MP3":  "bestaudio/best",
        "M4A":  "bestaudio[ext=m4a]/bestaudio/best",
    }

    def __init__(self, uid, url, cfg_ref: dict):
        """
        cfg_ref must be the LIVE cfg dict from MiniDownload so that any
        format/quality changes made after enqueue are picked up at download time.
        """
        self.uid = uid
        self.url = url
        self.cfg = cfg_ref   # live reference, NOT a copy
        self._cancel = False
        self.sig = DLSignals()
        self._sz = "—"
        self._title_emitted = False
        self.filepath: str | None = None

    def cancel(self):
        self._cancel = True

    def reset(self):
        self._cancel = False
        self._sz = "—"
        self._title_emitted = False
        self.filepath = None

    @staticmethod
    def _fmtsz(b):
        if not b:
            return "—"
        if b >= 1 << 30:
            return f"{b/1073741824:.2f} GB"
        if b >= 1 << 20:
            return f"{b/1048576:.1f} MB"
        return f"{b/1024:.0f} KB"

    @staticmethod
    def _fmt_eta(eta):
        if not eta or eta <= 0:
            return "—"
        s = int(eta)
        if s >= 3600:
            return f"{s // 3600}h {(s % 3600) // 60}m"
        if s >= 60:
            return f"{s // 60}m {s % 60}s"
        return f"{s}s"

    def _hook(self, d):
        if self._cancel:
            raise Exception("__cancel__")
        if not self._title_emitted:
            t = (d.get("info_dict") or {}).get("title")
            if t:
                self._title_emitted = True
                self.sig.title.emit(self.uid, t[:90])
        if d["status"] == "downloading":
            tot = d.get("total_bytes") or d.get("total_bytes_estimate")
            dl  = d.get("downloaded_bytes", 0)
            spd = d.get("speed") or 0
            eta = d.get("eta") or 0
            self._sz = self._fmtsz(tot) if tot else (self._fmtsz(dl) if dl else "—")
            pct = min(100.0, max(0.0, (dl / tot * 100))) if tot else 0.0
            self.sig.progress.emit(
                self.uid, pct,
                f"{spd/1048576:.2f} MB/s" if spd else "—",
                self._sz,
                self._fmt_eta(eta)
            )
        elif d["status"] == "finished":
            self.sig.progress.emit(self.uid, 100.0, "—", self._sz, "—")

    def run(self):
        try:
            import yt_dlp
        except ImportError:
            self.sig.finished.emit(self.uid, False, "yt-dlp not installed", "—")
            return

        cfg   = self.cfg
        fmt   = cfg.get("default_format", "MP4")
        qual  = cfg.get("default_quality", "Best")
        audio = fmt in ("MP3", "M4A")
        nm    = cfg.get("save_name_mode", "title")

        name_tmpl = {
            "title_id": "%(title)s [%(id)s].%(ext)s",
            "id":       "%(id)s.%(ext)s",
        }.get(nm, "%(title)s.%(ext)s")

        try:
            save_dir = _ensure_save_dir(cfg.get("save_dir", str(Path.home() / "Downloads")))
        except OSError as e:
            self.sig.finished.emit(self.uid, False, f"Save folder error: {e}", "—")
            return

        outtmpl = str(save_dir / name_tmpl)

        opts = {
            "outtmpl":             outtmpl,
            "progress_hooks":      [self._hook],
            "quiet":               True,
            "no_warnings":         True,
            "noprogress":          True,
            "noplaylist":          True,
            "socket_timeout":      30,
            "retries":             10,
            "fragment_retries":    10,
            "file_access_retries": 5,
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android", "mweb"]
                }
            },
        }

        _apply_runtime_paths(opts)

        if cfg.get("cookie_file") and Path(cfg["cookie_file"]).exists():
            opts["cookiefile"] = str(Path(cfg["cookie_file"]).resolve())

        if audio:
            opts["format"] = self.RES.get(fmt, self.RES["MP3"])
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt.lower(),
                "preferredquality": "320"
            }]
        else:
            opts["format"] = self.RES.get(qual, self.RES["Best"])
            if fmt == "MP4":
                opts["merge_output_format"] = "mp4"
            elif fmt == "MKV":
                opts["merge_output_format"] = "mkv"
            elif fmt == "WEBM":
                opts["format"] = (
                    f"bestvideo[ext=webm][height<={_QUAL_H.get(qual,9999)}]+bestaudio[ext=webm]"
                    f"/bestvideo[height<={_QUAL_H.get(qual,9999)}]+bestaudio/best"
                )
                opts["merge_output_format"] = "webm"

        if cfg.get("thumbnail"):       opts["writethumbnail"]   = True
        if cfg.get("description"):     opts["writedescription"] = True
        if cfg.get("write_info_json"): opts["writeinfojson"]    = True
        if cfg.get("subtitles"):
            opts.update(writesubtitles=True, writeautomaticsub=True,
                        subtitleslangs=[cfg.get("subtitle_lang", "en")])
        if cfg.get("embed_subs"):  opts["embedsubtitles"]  = True
        if cfg.get("embed_thumb"): opts["embedthumbnail"]  = True
        if cfg.get("proxy"):
            safe_proxy = _validate_proxy(cfg["proxy"])
            if safe_proxy:
                opts["proxy"] = safe_proxy
        if cfg.get("rate_limit"):
            rl = cfg["rate_limit"].strip().upper()
            try:
                if rl.endswith("K"):   opts["ratelimit"] = int(float(rl[:-1]) * 1024)
                elif rl.endswith("M"): opts["ratelimit"] = int(float(rl[:-1]) * 1024 * 1024)
                elif rl.endswith("G"): opts["ratelimit"] = int(float(rl[:-1]) * 1024 * 1024 * 1024)
                else:                  opts["ratelimit"] = int(float(rl))
            except ValueError:
                pass
        if cfg.get("sponsorblock"):
            opts["postprocessors"] = opts.get("postprocessors", []) + [
                {"key": "SponsorBlock", "categories": ["sponsor"]}]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                if self._cancel:
                    raise Exception("__cancel__")
                if info and not self._title_emitted:
                    self._title_emitted = True
                    self.sig.title.emit(self.uid, (info.get("title") or self.url)[:90])

                # Capture actual output file path
                filepath = None
                if info:
                    req = info.get("requested_downloads")
                    if req and isinstance(req, list) and req[0].get("filepath"):
                        filepath = req[0]["filepath"]
                    if not filepath and info.get("_filename"):
                        filepath = info["_filename"]
                    if not filepath:
                        try:
                            filepath = ydl.prepare_filename(info)
                        except Exception:
                            pass
                self.filepath = str(filepath) if filepath else None

            self.sig.finished.emit(self.uid, True, "Complete", self._sz)

        except Exception as e:
            msg = str(e)
            if "__cancel__" in msg:
                self.sig.finished.emit(self.uid, False, "Stopped", "—")
            else:
                _log.error("DLTask uid=%s url=%s error=%s", self.uid, self.url, msg)
                clean = _clean_err_msg(msg)
                self.sig.finished.emit(self.uid, False, clean, "—")


class DLWorker(QThread):
    def __init__(self, task: DLTask):
        super().__init__()
        self.task = task

    def run(self):
        self.task.run()

