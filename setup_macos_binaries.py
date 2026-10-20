"""
Tools Downloader - macOS FFmpeg & yt-dlp Auto-Downloader
Downloads native static binaries for Apple Silicon (M1/M2/M3/M4) and Intel Mac.
"""
import sys
import os
import platform
import gzip
import shutil
import urllib.request
from pathlib import Path

def setup_macos_binaries(target_dir: Path = None):
    root = Path(__file__).resolve().parent
    bin_dir = target_dir or (root / "bin" / "macos")
    bin_dir.mkdir(parents=True, exist_ok=True)

    is_arm = platform.machine() in ("arm64", "aarch64")
    arch_name = "arm64" if is_arm else "x64"

    print(f"========================================================")
    print(f"  Downloading FFmpeg & yt-dlp for macOS ({arch_name})")
    print(f"========================================================")

    ffmpeg_url = f"https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffmpeg-darwin-{arch_name}.gz"
    ffprobe_url = f"https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffprobe-darwin-{arch_name}.gz"
    ytdlp_url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"

    headers = {"User-Agent": "Mozilla/5.0"}

    def _download_and_extract_gz(url: str, dest_path: Path):
        print(f"-> Downloading {dest_path.name}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            compressed = resp.read()
            decompressed = gzip.decompress(compressed)
            dest_path.write_bytes(decompressed)
        dest_path.chmod(0o755)
        print(f"   Saved {dest_path.name} ({len(decompressed):,} bytes)")

    def _download_binary(url: str, dest_path: Path):
        print(f"-> Downloading {dest_path.name}...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            dest_path.write_bytes(data)
        dest_path.chmod(0o755)
        print(f"   Saved {dest_path.name} ({len(data):,} bytes)")

    # Download ffmpeg, ffprobe, and yt-dlp
    _download_and_extract_gz(ffmpeg_url, bin_dir / "ffmpeg")
    _download_and_extract_gz(ffprobe_url, bin_dir / "ffprobe")
    _download_binary(ytdlp_url, bin_dir / "yt-dlp")

    # Mirror into root/bin for direct fallback
    alt_bin = root / "bin"
    if alt_bin.exists():
        for name in ("ffmpeg", "ffprobe", "yt-dlp"):
            src = bin_dir / name
            if src.exists():
                try:
                    shutil.copy2(src, alt_bin / name)
                    (alt_bin / name).chmod(0o755)
                except Exception:
                    pass

    print(f"\n[SUCCESS] macOS binaries are ready in: {bin_dir}")

if __name__ == "__main__":
    setup_macos_binaries()

