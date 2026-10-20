import json
import threading as _threading
from src.config import SETTINGS_FILE, HISTORY_FILE, DEFAULT_SETTINGS
from src.utils import _validate_save_dir, _validate_proxy, _atomic_write

def load_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    if SETTINGS_FILE.exists():
        try:
            loaded = json.loads(SETTINGS_FILE.read_text("utf-8"))
            for k in DEFAULT_SETTINGS:
                if k in loaded:
                    s[k] = loaded[k]
            s["save_dir"] = _validate_save_dir(s["save_dir"])
            try:
                s["max_threads"] = max(1, min(16, int(s.get("max_threads", 4))))
            except (TypeError, ValueError):
                s["max_threads"] = DEFAULT_SETTINGS["max_threads"]
            if s.get("default_format") not in ("MP4", "MKV", "WEBM", "MP3", "M4A"):
                s["default_format"] = DEFAULT_SETTINGS["default_format"]
            if s.get("default_quality") not in ("Best", "4K", "2K", "1080", "720", "480", "360"):
                s["default_quality"] = DEFAULT_SETTINGS["default_quality"]
            if s.get("save_name_mode") not in ("title", "title_id", "id"):
                s["save_name_mode"] = DEFAULT_SETTINGS["save_name_mode"]
            for k in ("thumbnail", "description", "subtitles", "embed_subs",
                      "embed_thumb", "write_info_json", "no_playlist", "sponsorblock"):
                s[k] = bool(s.get(k, DEFAULT_SETTINGS[k]))
            s["proxy"] = _validate_proxy(str(s.get("proxy", "")))
            s["rate_limit"] = str(s.get("rate_limit", "")).strip()
            s["cookie_file"] = str(s.get("cookie_file", "")).strip()
            s["subtitle_lang"] = str(s.get("subtitle_lang", "en")).strip() or "en"
        except (json.JSONDecodeError, OSError):
            pass
    return s

def save_settings(s: dict):
    safe = {k: s[k] for k in DEFAULT_SETTINGS if k in s}
    _atomic_write(SETTINGS_FILE, json.dumps(safe, indent=2))

_history_cache: list | None = None
_history_lock  = _threading.Lock()

def load_history() -> list:
    global _history_cache
    with _history_lock:
        if _history_cache is not None:
            return list(_history_cache)
        if HISTORY_FILE.exists():
            try:
                _history_cache = json.loads(HISTORY_FILE.read_text("utf-8"))
                if not isinstance(_history_cache, list):
                    _history_cache = []
                return list(_history_cache)
            except (json.JSONDecodeError, OSError):
                pass
        _history_cache = []
        return []

def append_history(entry: dict):
    global _history_cache
    with _history_lock:
        if _history_cache is None:
            if HISTORY_FILE.exists():
                try:
                    loaded = json.loads(HISTORY_FILE.read_text("utf-8"))
                    _history_cache = loaded if isinstance(loaded, list) else []
                except (json.JSONDecodeError, OSError):
                    _history_cache = []
            else:
                _history_cache = []
        h = list(_history_cache)
        h.insert(0, entry)
        h = h[:500]
        _history_cache = h
    _atomic_write(HISTORY_FILE, json.dumps(h, indent=2))

def clear_history():
    global _history_cache
    with _history_lock:
        _history_cache = []
        try:
            HISTORY_FILE.unlink(missing_ok=True)
        except OSError:
            pass

