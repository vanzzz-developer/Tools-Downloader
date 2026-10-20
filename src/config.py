import logging as _logging
from pathlib import Path

APP_NAME        = "Tools Downloader"
APP_AUTHOR      = "VannSoThunh"
APP_VER         = "1.0.0"
APP_VER_TUPLE   = tuple(int(x) for x in APP_VER.split("."))
APP_FONT_FAMILY = "Noto Sans Khmer"
APP_FONT_STACK  = f"'{APP_FONT_FAMILY}', 'Khmer Sangam MN', 'Khmer MN', 'Khmer UI', 'Leelawadee UI', 'Segoe UI', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"

HISTORY_FILE    = Path.home() / ".mini_dl_history.json"
SETTINGS_FILE   = Path.home() / ".mini_dl_settings.json"
LOG_FILE        = Path.home() / ".mini_dl.log"

_log = _logging.getLogger("tools_downloader")
_log.setLevel(_logging.DEBUG)
if not _log.handlers:
    _log_handler = _logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    _log_handler.setFormatter(_logging.Formatter(
        "%(asctime)s [%(levelname)s] %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"))
    _log.addHandler(_log_handler)

DEFAULT_SETTINGS = {
    "save_dir": str(Path.home() / "Downloads"),
    "max_threads": 4,
    "default_format": "MP4",
    "default_quality": "Best",
    "save_name_mode": "title",
    "thumbnail": False, "description": False,
    "subtitles": False, "subtitle_lang": "en",
    "embed_subs": False, "embed_thumb": False,
    "write_info_json": False,
    "proxy": "", "rate_limit": "",
    "cookie_file": "",
    "no_playlist": False, "sponsorblock": False,
}

# Quality label -> max pixel height for WEBM format selector
_QUAL_H = {
    "Best": 9999, "4K": 2160, "2K": 1440, "1080": 1080,
    "720": 720, "480": 480, "360": 360
}

