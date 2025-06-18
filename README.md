# 🎬 YT-DLP Downloader (Streamlit App)

```
                                
                                ██╗░░░██╗████████╗░░░░░░██████╗░██╗░░░░░██████╗░
                                ╚██╗░██╔╝╚══██╔══╝░░░░░░██╔══██╗██║░░░░░██╔══██╗
                                ░╚████╔╝░░░░██║░░░█████╗██║░░██║██║░░░░░██████╔╝
                                ░░╚██╔╝░░░░░██║░░░╚════╝██║░░██║██║░░░░░██╔═══╝░
                                ░░░██║░░░░░░██║░░░░░░░░░██████╔╝███████╗██║░░░░░
                                ░░░╚═╝░░░░░░╚═╝░░░░░░░░░╚═════╝░╚══════╝╚═╝░░░░░
            
                             YT-DLP GUI Downloader powered by Streamlit – by Sahaj33
```

> Download videos & audio from YouTube with style and advanced options.

<p align="center">
  <a href="https://github.com/Sahaj33-op/YT-DLP-Downloader">
    <img src="https://img.shields.io/badge/Streamlit-Deploy-red?logo=streamlit" alt="Streamlit Badge">
  </a>
  <a href="https://www.python.org">
    <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  </a>
  <img src="https://img.shields.io/badge/License-MIT-brightgreen" alt="MIT License">
</p>


An advanced, beautifully designed Streamlit web app for downloading videos and audio using `yt-dlp`. Supports downloading single videos, playlists, and batch URLs with additional options like subtitle downloads, audio format selection, metadata embedding, and more.

---

## 🚀 Features

- 🎥 **Download Types**: Video+Audio, Audio-only, or Video-only
- 🧠 **Smart URL Detection**: Detects video vs playlist automatically
- 🎚 **Custom Quality**: Choose from Best, 1080p, 720p, 480p, etc.
- 🎵 **Audio Format Selector**: mp3, aac, m4a, opus, flac
- 📝 **Download Subtitles**, Thumbnails, Add Metadata
- 📦 **Batch Download** (Coming Soon)
- 📚 **Download History** with session persistence
- 📊 **System Monitor**: Memory, disk, network speed
- ⚙️ **Advanced Options**: Proxy, filename templates, custom format
- ✨ **Beautiful Dark UI** with custom CSS

---

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/yt-dlp-streamlit.git
cd yt-dlp-streamlit
```

### 2. Create a virtual environment (optional)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Make sure `yt-dlp`, `ffmpeg`, and `ffprobe` are installed and available in your system PATH.

#### Install yt-dlp

```bash
pip install yt-dlp
```

#### Install FFmpeg

- **Windows**:  
  ```bash
  winget install FFmpeg
  ```
- **Linux**:  
  ```bash
  sudo apt install ffmpeg
  ```
- **macOS**:  
  ```bash
  brew install ffmpeg
  ```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

---

## 💻 Tech Stack

- Streamlit
- yt-dlp
- FFmpeg
- Python standard libraries

---

## 👨‍💻 Author

**[Sahaj33](https://linktr.ee/sahaj33)**  
Made with ❤️ using Python and Streamlit.

---

## 📃 License

This project is licensed under the MIT License.
