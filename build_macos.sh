#!/usr/bin/env bash
# Tools Downloader - macOS Application Builder (.app)
set -e

echo "========================================================"
echo "        Building Tools Downloader for macOS"
echo "========================================================"

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install requirements
pip install -r requirements.txt

# Clean previous build artifacts
rm -rf build/ "dist/Tools Downloader.app"

# Check for Homebrew FFmpeg
if command -v ffmpeg &> /dev/null; then
    echo "[INFO] System FFmpeg detected at: $(which ffmpeg)"
else
    echo "[WARNING] FFmpeg not found in PATH! You can install it via: brew install ffmpeg"
fi

# Build arguments for macOS App bundle
ARGS=(
    --noconsole
    --windowed
    --clean
    --noconfirm
    --name "Tools Downloader"
    --icon "assets/icon.png"
    --add-data "assets/icon.png:assets"
    --hidden-import "yt_dlp"
    --collect-all "yt_dlp"
)

# Include bin directory if binaries are provided
if [ -d "bin" ]; then
    ARGS+=(--add-data "bin:bin")
fi

echo "Running PyInstaller for macOS..."
pyinstaller "${ARGS[@]}" main.py

echo ""
echo "========================================================"
echo "[SUCCESS] Build Complete!"
echo "Application bundle created at: dist/Tools Downloader.app"
echo "========================================================"
