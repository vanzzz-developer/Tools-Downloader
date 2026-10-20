import sys
from PySide6.QtCore import QThread, Signal
from src.utils import _yt_dlp_exe, _run_hidden_subprocess

class _UpdateThread(QThread):
    done = Signal(bool, str)

    def run(self):
        if getattr(sys, "frozen", False):
            exe = _yt_dlp_exe()
            if not exe:
                self.done.emit(False, "yt-dlp.exe not found beside the app")
                return
            try:
                r = _run_hidden_subprocess(
                    [str(exe), "-U"],
                    cwd=str(exe.parent),
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                output = (r.stdout or r.stderr or "").strip()
                last_line = output.splitlines()[-1] if output.splitlines() else ""
                if r.returncode == 0:
                    self.done.emit(True, last_line or "yt-dlp.exe updated successfully")
                else:
                    self.done.emit(False, (last_line or f"yt-dlp.exe exited with code {r.returncode}")[:120])
            except Exception as e:
                self.done.emit(False, str(e)[:120])
            return

        try:
            r = _run_hidden_subprocess(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if r.returncode == 0:
                try:
                    import importlib, yt_dlp
                    importlib.invalidate_caches()
                    importlib.reload(yt_dlp)
                except Exception:
                    pass
                self.done.emit(True, "yt-dlp updated successfully")
            else:
                output = (r.stderr or r.stdout or "").strip()
                last_line = output.splitlines()[-1] if output.splitlines() else ""
                self.done.emit(False, (last_line or "pip update failed")[:120])
        except Exception as e:
            self.done.emit(False, str(e)[:120])

