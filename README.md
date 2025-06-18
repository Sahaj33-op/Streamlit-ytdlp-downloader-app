# 🎬 YT-DLP Downloader – Streamlit Web App

```
              ██╗░░░██╗████████╗  ██████╗░██████╗░██╗░░░░░██████╗░
              ██║░░░██║╚══██╔══╝  ██╔══██╗██╔══██╗██║░░░░░██╔══██╗
              ██║░░░██║░░░██║░░░  ██████╦╝██████╔╝██║░░░░░██████╦╝
              ██║░░░██║░░░██║░░░  ██╔══██╗██╔═══╝░██║░░░░░██╔══██╗
              ╚██████╔╝░░░██║░░░  ██████╦╝██║░░░░░███████╗██████╦╝
               ╚═════╝░░░░╚═╝░░░  ╚═════╝░╚═╝░░░░░╚══════╝╚═════╝░

               YT-DLP GUI Downloader powered by Streamlit – by Sahaj33
```

> Download videos & audio from YouTube and other platforms with style and advanced options.

<p align="center">
  <a href="https://github.com/Sahaj33-op/YT-DLP-Downloader">
    <img src="https://img.shields.io/badge/Streamlit-Deploy-red?logo=streamlit" alt="Streamlit Badge">
  </a>
  <a href="https://www.python.org">
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  </a>
  <img src="https://img.shields.io/badge/License-MIT-brightgreen" alt="MIT License">
</p>

---

## ✨ Key Features

| Feature                   | Description                                                             |
|---------------------------|-------------------------------------------------------------------------|
| 📥 Video & Audio Download | Supports full video+audio, audio-only, or video-only options            |
| 🎚 Format & Quality       | Choose from 1080p, 720p, or best available formats                      |
| 📄 Subtitles & Metadata   | Option to download subs, thumbnails, and embed metadata (ffmpeg needed) |
| 📁 Playlist Support       | Select specific video range in playlists                                |
| 🛠 Custom Settings        | Advanced format strings, proxy config, rate limit, filename templates   |
| 📊 System Monitor         | View memory usage, free disk space, and test download speed             |
| 📜 Download History       | Tracks previous downloads with status and titles                        |
| 🌐 Streamlit Interface    | Fully featured dark UI with tabs and floating buttons                   |

---

## 📂 Project Structure

```
YT-DLP-Downloader/
├── app.py               # Streamlit application
├── requirements.txt     # Dependencies
├── README.md            # You’re reading it!
└── .gitignore           # Clean repository
```

---

## 🚀 Quickstart

### 🔧 Setup

```bash
git clone https://github.com/Sahaj33-op/YT-DLP-Downloader
cd YT-DLP-Downloader
pip install -r requirements.txt
```

Install [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [ffmpeg](https://ffmpeg.org):

```bash
pip install yt-dlp
# and install ffmpeg using your system package manager
```

---

### ▶️ Launch the App

```bash
streamlit run app.py
```

Open in your browser: [http://localhost:8501](http://localhost:8501)

---

## 🧠 System Requirements

- Python 3.10+
- yt-dlp
- ffmpeg + ffprobe (for advanced features)
- Streamlit

---

## 🎨 UI Showcase

| Home Tab | Video Info | Monitor |
|----------|------------|---------|
| ![](https://via.placeholder.com/400x200?text=YT-DLP+Home) | ![](https://via.placeholder.com/400x200?text=Video+Info) | ![](https://via.placeholder.com/400x200?text=System+Monitor) |

---

## 🧠 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Streamlit](https://streamlit.io)
- [FFmpeg](https://ffmpeg.org)
- Built with ❤️ by [Sahaj33](https://linktr.ee/sahaj33)

---

## 📜 License

MIT License – See [LICENSE](LICENSE) for details.

