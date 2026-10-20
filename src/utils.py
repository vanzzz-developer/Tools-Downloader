import sys, os, re, subprocess
from pathlib import Path
from urllib.parse import urlparse

def _is_valid_url(url: str) -> bool:
    """Accept only http/https URLs with a valid netloc (max 2048 chars)."""
    try:
        r = urlparse(url)
        return r.scheme in ("http", "https") and bool(r.netloc) and len(url) <= 2048
    except Exception:
        return False

def _validate_proxy(proxy: str) -> str:
    """Only allow http/https/socks4/socks5 proxy schemes."""
    p = proxy.strip()
    if not p:
        return ""
    if re.match(r'^(https?|socks[45](h?)?)://', p, re.IGNORECASE):
        return p
    return ""

def _validate_save_dir(path_str: str) -> str:
    """Resolve and validate save directory. Returns cleaned path or Downloads fallback."""
    try:
        p = Path(path_str).resolve()
        if len(p.parts) < 2:
            raise ValueError("Path too shallow")
        return str(p)
    except Exception:
        return str(Path.home() / "Downloads")

def _ensure_save_dir(path_str: str) -> Path:
    path = Path(path_str).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def _clean_err_msg(msg: str) -> str:
    """Strip ANSI codes and format friendly short messages for GUI status."""
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', msg)
    clean = re.sub(r'^ERROR:\s*(\[.*?\])?\s*([a-zA-Z0-9_-]+:\s*)?', '', clean).strip()
    low = clean.lower()
    if "sign in to confirm you" in low or "sign in to confirm" in low:
        return "Bot Check (Sign In)"
    if "http error 429" in low or "too many requests" in low:
        return "429: Rate Limited"
    if "timed out" in low or "timeout" in low:
        return "Network Timeout"
    if "403" in clean or "forbidden" in low or "unable to download video data" in low:
        return "403: Forbidden"
    if "connection reset" in low or "connection aborted" in low:
        return "Connection Reset"
    if "private video" in low:
        return "Private Video"
    if "video unavailable" in low or "this video is not available" in low:
        return "Video Unavailable"
    if "members-only" in low or "join this channel" in low:
        return "Members-Only Video"
    return clean[:24] or "Failed"


def _run_hidden_subprocess(cmd, **kwargs):
    """Run subprocess on Windows without flashing a black console window."""
    if sys.platform == "win32":
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
    return subprocess.run(cmd, **kwargs)

def _app_dir() -> Path:
    """Return the directory that contains bundled runtime files in PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent

def _dist_dir() -> Path:
    """Return the executable folder for side-by-side files in frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _first_existing_path(*paths: Path) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None

def _bundled_binary(name: str) -> Path | None:
    root = Path(__file__).resolve().parent.parent
    candidates = [
        _dist_dir() / "bin" / name,
        _dist_dir() / name,
        _app_dir() / "bin" / name,
        _app_dir() / name,
        root / "bin" / name,
        root / name,
    ]
    # Check macOS Homebrew / system paths
    import shutil
    which_path = shutil.which(name)
    if which_path:
        candidates.append(Path(which_path))
    if sys.platform == "darwin":
        candidates.extend([
            Path("/opt/homebrew/bin") / name,
            Path("/usr/local/bin") / name,
        ])
    return _first_existing_path(*candidates)

def _yt_dlp_exe() -> Path | None:
    exe_name = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
    # Check side-by-side with app executable first (persistent across runs)
    for p in (_dist_dir() / "bin" / exe_name, _dist_dir() / exe_name):
        if p.exists():
            return p
    # Look in bundled files (_MEIPASS)
    bundled = _bundled_binary(exe_name)
    if bundled and bundled.exists():
        if getattr(sys, "frozen", False):
            try:
                import shutil
                target = _dist_dir() / exe_name
                shutil.copy2(bundled, target)
                return target
            except Exception:
                pass
        return bundled
    return None

def _apply_runtime_paths(opts: dict):
    ffmpeg = _bundled_binary("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    if ffmpeg:
        opts["ffmpeg_location"] = str(ffmpeg.parent)

def _atomic_write(path: Path, text: str):
    """Write to a temp file then rename — prevents corruption on crash."""
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(text, "utf-8")
        tmp.replace(path)
    except OSError:
        pass

