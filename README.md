# 🎥 YouTube Downloader Pro

A modern, feature-rich GUI application for downloading YouTube videos and playlists with an intuitive interface built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ Features

### 🎯 Core Functionality
- **Single Video & Playlist Downloads** - Download individual videos or entire playlists
- **Dynamic Quality Selection** - Automatically detects available qualities (Best Quality, 1080p, 720p, Data Saving, etc.)
- **Smart Format Detection** - Shows only available formats for each video
- **Enhanced Progress Tracking** - Real-time progress with speed, ETA, and fragment support
- **Advanced Playlist Selector** - Search, filter, and select specific videos from playlists

### 🎨 User Experience
- **Modern Dark Theme** - Professional interface with intuitive controls
- **Native Window Controls** - Full minimize/maximize/close functionality
- **Comprehensive Keyboard Shortcuts** - Efficient workflow with hotkeys
- **Real-time URL Validation** - Instant feedback for valid/invalid URLs
- **Smart Reset System** - Fresh start every launch for consistent experience

## 💻 Installation

### Prerequisites
- Python 3.8 or higher
- Internet connection

### ⚡ Super Simple Setup

**Everything installs automatically - just run the app!**

```bash
# Clone the repository
git clone https://github.com/yourusername/youtube-downloader-pro.git
cd youtube-downloader-pro

# Run the app (installs everything automatically on first run)
python youtube_downloader.py
```

**That's it!** The app will automatically:
- Create virtual environment
- Install Python dependencies  
- Download and setup FFmpeg
- Start the application

### 🔧 Manual Setup (If Needed)

**If you prefer manual control:**

```bash
# Create virtual environment manually
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run setup manually
python setup.py

# Start the app
python youtube_downloader.py
```

### 🎬 FFmpeg Integration

**✨ FFmpeg installs automatically on first run!** (Windows)

- **Windows**: FFmpeg downloads automatically when you first run the app
- **macOS/Linux**: Manual installation required (see below)

**Manual FFmpeg Installation (if needed):**

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg   # CentOS/RHEL
```

**Benefits of FFmpeg:**
- Enables highest quality video+audio downloads
- Without FFmpeg: App works great but downloads audio-only for some videos

## 🎥 Usage

### Quick Start
1. **Launch**: `python youtube_downloader.py`
2. **Paste URL**: Any YouTube video or playlist URL
3. **Analyze**: Click "Analyze" to detect available qualities
4. **Select Quality**: Choose from "Best Quality", specific resolutions, or "Data Saving"
5. **Download**: Click "Download" to start

### Playlist Features
- **Enable "Download entire playlist"** for full playlist downloads
- **Use "Show Playlist"** for advanced selection with search and filtering
- **Set ranges** (From: 5, To: 15) to download specific video ranges

### ⌨️ Keyboard Shortcuts
- **F5** - Analyze URL | **F9** - Download | **F10** - Stop
- **Ctrl+V** - Paste URL | **Ctrl+R** - Reset all options  
- **F1** - Help | **Alt+O** - Open download folder

## 📸 Screenshots

*Coming soon - screenshots of the modern dark theme interface*

## 🔧 Technical Details

### Dependencies
- **yt-dlp** - Core YouTube downloading functionality
- **tkinter** - GUI framework (included with Python)
- **threading** - Background operations for responsive UI

### Key Features
- **Dynamic Quality Detection** - Shows actual available resolutions
- **HLS Fragment Support** - Handles modern YouTube streaming formats
- **Multi-level Error Recovery** - Fallback strategies for reliable downloads
- **Thread-safe UI** - Responsive interface during downloads

## 🚀 What's New

- **Enhanced Progress Tracking** - Now supports HLS fragment downloads
- **Dynamic Quality Options** - Shows actual available resolutions per video
- **Advanced Playlist Selector** - Search, filter, and bulk select videos
- **User-Friendly Quality Names** - "Best Quality" and "Data Saving" options
- **Fresh Start Experience** - Clean reset every app launch

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation

## 📜 License

MIT License - see LICENSE file for details

## ⚠️ Disclaimer

This tool is for personal use only. Please respect YouTube's Terms of Service and copyright laws. The developers are not responsible for any misuse of this software.
