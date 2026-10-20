#!/usr/bin/env bash
# ==============================================================================
# Tools Downloader - macOS FFmpeg & yt-dlp Auto-Downloader
# Downloads native static binaries for Apple Silicon (M1/M2/M3/M4) and Intel Mac
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$SCRIPT_DIR/bin/macos"
mkdir -p "$BIN_DIR"

ARCH=$(uname -m)
echo "========================================================"
echo "    Downloading FFmpeg & yt-dlp for macOS ($ARCH)"
echo "========================================================"

if [ "$ARCH" = "arm64" ]; then
    FFMPEG_URL="https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffmpeg-darwin-arm64.gz"
    FFPROBE_URL="https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffprobe-darwin-arm64.gz"
else
    FFMPEG_URL="https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffmpeg-darwin-x64.gz"
    FFPROBE_URL="https://github.com/eugeneware/ffmpeg-static/releases/download/b6.1.1/ffprobe-darwin-x64.gz"
fi

YTDLP_URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"

# 1. Download & Decompress ffmpeg
echo "-> Downloading FFmpeg..."
curl -L -s "$FFMPEG_URL" | gzip -d > "$BIN_DIR/ffmpeg"
chmod +x "$BIN_DIR/ffmpeg"

# 2. Download & Decompress ffprobe
echo "-> Downloading FFprobe..."
curl -L -s "$FFPROBE_URL" | gzip -d > "$BIN_DIR/ffprobe"
chmod +x "$BIN_DIR/ffprobe"

# 3. Download Universal yt-dlp
echo "-> Downloading yt-dlp..."
curl -L -s -o "$BIN_DIR/yt-dlp" "$YTDLP_URL"
chmod +x "$BIN_DIR/yt-dlp"

# Copy to bin/ as fallback
cp -f "$BIN_DIR/ffmpeg" "$SCRIPT_DIR/bin/ffmpeg" 2>/dev/null || true
cp -f "$BIN_DIR/ffprobe" "$SCRIPT_DIR/bin/ffprobe" 2>/dev/null || true
cp -f "$BIN_DIR/yt-dlp" "$SCRIPT_DIR/bin/yt-dlp" 2>/dev/null || true

echo ""
echo "========================================================"
echo "[SUCCESS] macOS Binaries installed in $BIN_DIR:"
ls -lh "$BIN_DIR"
echo "========================================================"

