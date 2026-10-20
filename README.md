<div align="center">

# ⚡ Tools Downloader

**Modern, blazing-fast, and self-contained Video & Audio Downloader for Windows & macOS**  
*Built with Python 3, PySide6 (Qt6), yt-dlp, and FFmpeg*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![FFmpeg](https://img.shields.io/badge/Media-FFmpeg%20Bundled-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Windows](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![macOS](https://img.shields.io/badge/Platform-macOS%2012%2B-000000?style=for-the-badge&logo=apple&logoColor=white)](https://www.apple.com/macos)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

[English](#-key-features) • [ភាសាខ្មែរ (Khmer Overview)](#-សេចក្ដីសង្ខេបជាភាសាខ្មែរ) • [Windows Setup](#-getting-started-windows) • [macOS Setup](#-getting-started-macos) • [Building](#-building-standalone-executables)

</div>

---

## 🌟 Key Features

- **🎬 Ultra High-Definition Video:**
  - Download resolutions up to **8K, 4K, 2K, 1080p Full HD**, 720p, 480p, 360p.
  - Smart container merge: Guarantees compatible **MP4 (H.264/AAC)** format for seamless playback on any device, Mac QuickTime, TV, or video editing software (Final Cut Pro, Premiere Pro, DaVinci Resolve, CapCut).

- **🎵 True Studio Audio Extraction:**
  - Converts online media to high-fidelity **MP3 at true 320 kbps (CBR)**.
  - Also supports **M4A, WAV, FLAC, and OPUS**.

- **📋 Multi-Link & Batch Downloads:**
  - Paste dozens or hundreds of URLs at once.
  - **Drag-and-Drop:** Simply drag and drop any `.txt` file containing URLs directly onto the input box.

- **📑 Smart Playlist & Channel Scanner:**
  - Automatically detects YouTube / Facebook / TikTok playlists and channels.
  - Interactive popup modal allowing you to select/deselect specific videos before downloading.

- **⚡ Blazing Fast & Multi-Threaded:**
  - Download up to 10 files simultaneously with multi-threading.
  - Integrated speed limiter to preserve your bandwidth when needed.
  - Real-time download progress, live speed (MB/s), and friendly ETA (`3m 15s`).

- **📦 Native & Self-Contained:**
  - **Windows:** Bundled `.exe` and Inno Setup installer embedding FFmpeg, FFprobe, FFplay, and yt-dlp.
  - **macOS:** Native `.app` bundle, automatic Homebrew FFmpeg detection (`/opt/homebrew/bin` & `/usr/local/bin`).

- **🎨 Modern Fluent UI:**
  - Sleek Dark / Light theme with smooth animations and intuitive controls.
  - Media Action Buttons: "Play File" (with default media player or built-in previewer) and "Open Folder".
  - Searchable History Dialog with instant keyword filtering.
  - One-click `yt-dlp` update checker inside the Settings dialog.

---

## 🌐 Supported Platforms

Tools Downloader leverages the comprehensive extractor network of `yt-dlp`, supporting **1,000+ websites** including:

| Platform | Supported Content |
| :--- | :--- |
| **YouTube** | Videos, Shorts, Playlists, Channels, Live Streams |
| **Facebook** | Public & Private Videos, Watch, Reels |
| **TikTok** | HD Videos (watermark-free), Original Audio |
| **Instagram** | Reels, Posts, Stories |
| **Twitter / X** | Video Clips, GIFs |
| **Others** | Vimeo, Dailymotion, SoundCloud, Bilibili, Twitch, Reddit, etc. |

---

## 🇰🇭 សេចក្ដីសង្ខេបជាភាសាខ្មែរ

**Tools Downloader** គឺជាកម្មវិធីទាញយក Video និង Audio ដ៏ទំនើប លឿន និងងាយស្រួលប្រើប្រាស់បំផុតសម្រាប់ប្រព័ន្ធប្រតិបត្តិការ **Windows និង macOS**៖
* **ទាញយកកម្រិតច្បាស់ខ្ពស់:** គាំទ្រដល់កម្រិត 4K, 2K, 1080p Full HD (MP4 H.264) និងបម្លែងសំឡេងជា MP3 កម្រិតច្បាស់ 320 kbps។
* **ទាញយកម្តងបានច្រើន:** អាច Copy links ជាច្រើនដាក់ចូល ឬ Drag-and-drop file `.txt` ចូល App ផ្ទាល់។
* **ស្កេន Playlist & Channel:** អាចជ្រើសរើសវីដេអូណាមួយដែលចង់បាន ឬមិនចង់បានពីក្នុង Playlist មុនពេលទាញយក។
* **គាំទ្រទាំងស្រុងលើ Windows & Mac:** គាំទ្រទាំងលើ Windows 10/11 និង macOS (Apple Silicon M1/M2/M3/M4 & Intel) ដោយមានប្រព័ន្ធស្វែងរក FFmpeg ស្វ័យប្រវត្តិតាមរយៈ Homebrew។

---

## 📂 Project Architecture

```plaintext
Tools Downloader/
├── assets/                  # Icons and application branding
│   ├── icon.ico             # Windows executable icon
│   └── icon.png             # macOS / Linux & UI icons
├── bin/                     # Embedded native binaries (ignored from git)
│   ├── ffmpeg.exe           # FFmpeg multimedia processor (Windows)
│   ├── ffprobe.exe          # Media stream analyzer (Windows)
│   ├── ffplay.exe           # Integrated lightweight media previewer
│   └── yt-dlp.exe           # CLI binary for standalone updates
├── src/                     # Core application source code
│   ├── ui/                  # Qt6 UI Components
│   │   ├── dialogs/         # History, Settings, and Playlist Scanner dialogs
│   │   ├── delegates.py     # Custom TableView item delegates & action buttons
│   │   └── main_window.py   # Primary application window (with macOS/Windows handlers)
│   ├── workers/             # Multi-threaded QThread background workers
│   │   ├── download_worker.py # yt-dlp download & post-processing logic
│   │   ├── playlist_scanner.py# Fast metadata and playlist extraction
│   │   └── signals.py       # Thread-safe Qt signals
│   ├── app.py               # Application bootstrap & lifecycle
│   ├── config.py            # Global constants, presets & macOS/Windows font stack
│   ├── storage.py           # SQLite / JSON download history persistence
│   ├── theme.py             # Dark & Light stylesheet engine
│   └── utils.py             # Formatter, runtime path resolver (macOS Homebrew & Windows)
├── tests/                   # Automated unit and integration tests
│   └── test_downloader.py   # Test suite for downloader, formatters & options
├── .gitignore               # Clean git rules (excludes large binaries & build files)
├── Build App.bat            # One-click Windows batch script to build .exe
├── Build Installer.bat      # One-click Windows Inno Setup installer generator
├── build_macos.sh           # One-click macOS build script to create .app bundle
├── Push to GitHub.bat       # Instant push helper script
├── Tools Downloader.spec    # PyInstaller configuration with embedded assets
├── installer.iss            # Inno Setup Windows installer configuration
├── main.py                  # Application entry point
├── requirements.txt         # Python package dependencies
└── README.md                # Project documentation
```

---

## 🚀 Getting Started (Windows)

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10+**

### Installation
```bash
git clone https://github.com/vanzzz-developer/Tools-Downloader.git
cd Tools-Downloader
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 🍏 Getting Started (macOS)

### Prerequisites
- **macOS 12.0+ (Monterey, Ventura, Sonoma, Sequoia)**
- Supports both **Apple Silicon (M1/M2/M3/M4)** and **Intel**
- **Python 3.10+** (Install via Homebrew: `brew install python`)
- **FFmpeg** (Install via Homebrew: `brew install ffmpeg`)

### Installation
```bash
git clone https://github.com/vanzzz-developer/Tools-Downloader.git
cd Tools-Downloader

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download native FFmpeg & yt-dlp binaries for macOS
python3 setup_macos_binaries.py

# Run application
python3 main.py
```

---

## 🛠️ Building Standalone Executables

### 🪟 Windows (.exe)
```bash
# Method 1: Double-click Build App.bat
# Method 2: Manual command
pyinstaller "Tools Downloader.spec" --noconfirm
```
Output: `dist/Tools Downloader.exe`

### 📦 Windows Setup Installer (.exe)
Double-click `Build Installer.bat` or compile with Inno Setup.  
Output: `dist/Tools_Downloader_Setup_v1.0.exe`

### 🍏 macOS (.app Bundle)
Run the automated build script:
```bash
chmod +x build_macos.sh
./build_macos.sh
```
Output: `dist/Tools Downloader.app`

---

## 🧪 Running Tests

To verify all components and formatting helpers across Windows and macOS:

```bash
python -m unittest discover tests
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is created for educational and personal archiving purposes only. Please respect the terms of service of the websites you download from and only download content you have the right to access.
