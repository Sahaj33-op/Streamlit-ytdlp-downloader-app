# YT-DLP Downloader

A modern, minimalist web application for downloading videos and audio from 1000+ platforms using yt-dlp.

[![Streamlit](https://img.shields.io/badge/Streamlit-Deploy-red?logo=streamlit)](https://ytdlp-downloader-app-sahaj33.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-brightgreen)](LICENSE)

---

## Features

- **Download Types** — Video+Audio, Audio-only, or Video-only
- **Smart Detection** — Automatically detects videos vs playlists
- **Quality Selection** — Best, 1080p, 720p, 480p, 360p
- **Audio Formats** — mp3, aac, m4a, opus, flac
- **Batch Download** — Download multiple URLs in parallel
- **Additional Options** — Subtitles, thumbnails, metadata embedding
- **Download History** — Session-persistent history
- **System Monitor** — CPU, memory, disk, network metrics
- **Modern Dark UI** — Clean, minimal black design

---

## Installation

### Clone the repository

```bash
git clone https://github.com/Sahaj33-op/Streamlit-ytdlp-downloader-app
cd Streamlit-ytdlp-downloader-app
```

### Create virtual environment (optional)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### System requirements

**yt-dlp** and **FFmpeg** must be installed and available in PATH.

```bash
# yt-dlp
pip install yt-dlp

# FFmpeg
# Windows
winget install FFmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

## Usage

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

**Live Demo:** [ytdlp-downloader-app-sahaj33.streamlit.app](https://ytdlp-downloader-app-sahaj33.streamlit.app/)

---

## Tech Stack

- Streamlit
- yt-dlp (Python API)
- FFmpeg
- Python 3.10+

---

## Architecture

Single-file Streamlit application with:

- **yt-dlp Python API** for downloads (no subprocess)
- **Progress hooks** for real-time progress tracking
- **Memory-safe file serving** with size limits (100MB default)
- **Session state** for history and download management

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.

---

## Author

**[Sahaj33](https://linktr.ee/sahaj33)**

---

## License

MIT License - see [LICENSE](LICENSE) for details.
