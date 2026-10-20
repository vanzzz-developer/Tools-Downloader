<div align="center">

# ⚡ Tools Downloader

**Modern, blazing-fast, and self-contained Video & Audio Downloader for Windows**  
*Built with Python 3, PySide6 (Qt6), yt-dlp, and FFmpeg*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![yt-dlp](https://img.shields.io/badge/Engine-yt--dlp-red?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![FFmpeg](https://img.shields.io/badge/Media-FFmpeg%20Bundled-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

[English](#-key-features) • [ភាសាខ្មែរ (Khmer Overview)](#-សេចក្ដីសង្ខេបជាភាសាខ្មែរ) • [Installation](#-getting-started) • [Building EXE](#-building-standalone-exe)

</div>

---

## 🌟 Key Features

- **🎬 Ultra High-Definition Video:**
  - Download resolutions up to **8K, 4K, 2K, 1080p Full HD**, 720p, 480p, 360p.
  - Smart container merge: Guarantees compatible **MP4 (H.264/AAC)** format for seamless playback on any device, TV, or video editing software (CapCut, Premiere Pro, DaVinci Resolve).

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

- **📦 100% Standalone (Zero Configuration for End-Users):**
  - All critical dependencies (`ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`, and `yt-dlp.exe`) are bundled directly inside the executable.
  - Runs immediately on any clean Windows machine without needing Python, FFmpeg, or command-line tools installed.

- **🎨 Modern Fluent UI:**
  - Sleek Dark / Light theme with smooth animations and intuitive controls.
  - Media Action Buttons: "Play File" (with default media player or built-in ffplay) and "Open Folder".
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

**Tools Downloader** គឺជាកម្មវិធីទាញយក Video និង Audio ដ៏ទំនើប លឿន និងងាយស្រួលប្រើប្រាស់បំផុតសម្រាប់ប្រព័ន្ធប្រតិបត្តិការ Windows៖
* **ទាញយកកម្រិតច្បាស់ខ្ពស់:** គាំទ្រដល់កម្រិត 4K, 2K, 1080p Full HD (MP4 H.264) និងបម្លែងសំឡេងជា MP3 កម្រិតច្បាស់ 320 kbps។
* **ទាញយកម្តងបានច្រើន:** អាច Copy links ជាច្រើនដាក់ចូល ឬ Drag-and-drop file `.txt` ចូល App ផ្ទាល់។
* **ស្កេន Playlist & Channel:** អាចជ្រើសរើសវីដេអូណាមួយដែលចង់បាន ឬមិនចង់បានពីក្នុង Playlist មុនពេលទាញយក។
* **មិនបាច់ Install អ្វីបន្ថែម:** ទាំង FFmpeg និង yt-dlp ត្រូវបានបង្កប់រួចជាស្រេចនៅក្នុង App តែមួយ យកទៅបើកលើកុំព្យូទ័រណាក៏ដើរភ្លាមៗ។

---

## 📂 Project Architecture

```plaintext
Tools Downloader/
├── assets/                  # Icons and application branding
│   ├── icon.ico             # Windows executable icon
│   └── icon.png             # UI and dialog icons
├── bin/                     # Embedded native binaries (ignored from git)
│   ├── ffmpeg.exe           # FFmpeg multimedia processor
│   ├── ffprobe.exe          # Media stream analyzer
│   ├── ffplay.exe           # Integrated lightweight media previewer
│   └── yt-dlp.exe           # CLI binary for standalone updates
├── src/                     # Core application source code
│   ├── ui/                  # Qt6 UI Components
│   │   ├── dialogs/         # History, Settings, and Playlist Scanner dialogs
│   │   ├── delegates.py     # Custom TableView item delegates & action buttons
│   │   └── main_window.py   # Primary application window
│   ├── workers/             # Multi-threaded QThread background workers
│   │   ├── download_worker.py # yt-dlp download & post-processing logic
│   │   ├── playlist_scanner.py# Fast metadata and playlist extraction
│   │   └── signals.py       # Thread-safe Qt signals
│   ├── app.py               # Application bootstrap & lifecycle
│   ├── config.py            # Global constants, presets & settings
│   ├── storage.py           # SQLite / JSON download history persistence
│   ├── theme.py             # Dark & Light stylesheet engine
│   └── utils.py             # Formatter, runtime path resolver & binary locators
├── tests/                   # Automated unit and integration tests
│   └── test_downloader.py   # Test suite for downloader, formatters & options
├── .gitignore               # Clean git rules (excludes large binaries & build files)
├── Build App.bat            # One-click Windows batch script to build .exe
├── Tools Downloader.spec    # PyInstaller configuration with embedded assets
├── main.py                  # Application entry point
├── requirements.txt         # Python package dependencies
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- **Windows 10 / 11** (64-bit recommended)
- **Python 3.10+** (tested on Python 3.13)

### Installation (From Source)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/tools-downloader.git
   cd tools-downloader
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Binaries in `bin/` directory:**
   Place the following Windows executables inside the `bin/` folder:
   - `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` (Download from [gyan.dev FFmpeg Builds](https://www.gyan.dev/ffmpeg/builds/))
   - `yt-dlp.exe` (Download from [yt-dlp Releases](https://github.com/yt-dlp/yt-dlp/releases))

5. **Run the Application:**
   ```bash
   python main.py
   ```

---

## 🛠️ Building Standalone EXE

You can compile the entire application into a single, fully self-contained `.exe` that embeds all Python runtimes, Qt libraries, FFmpeg, and yt-dlp:

### Method 1: One-Click Script
Simply double-click:
```plaintext
Build App.bat
```

### Method 2: Manual Command
```bash
.venv\Scripts\activate
pyinstaller "Tools Downloader.spec" --noconfirm
```

The compiled standalone executable will be located at:
```plaintext
dist/Tools Downloader.exe
```

> **Note:** The resulting `.exe` is completely portable. You can copy it to any Windows PC and run it immediately without installing Python or FFmpeg!

---

## 📦 Building Windows Setup Installer (.exe)

To generate a professional Windows Setup Wizard with Desktop shortcut, Start Menu entry, and full uninstaller:

Simply double-click:
```plaintext
Build Installer.bat
```

The compiled installer wizard will be located at:
```plaintext
dist/Tools_Downloader_Setup_v1.0.exe
```

---

## 🧪 Running Tests

To verify that all components, formatting helpers, and download options are functioning properly:

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
