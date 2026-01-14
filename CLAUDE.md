# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Streamlit app locally
streamlit run app.py

# Run with dev container settings (CORS/XSRF disabled)
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

**System Requirements:** yt-dlp, ffmpeg, and ffprobe must be installed and available in PATH.

## Architecture

Single-file Streamlit application (`app.py`) providing a web GUI for yt-dlp video downloading.

### Core Structure

The app is organized into 5 Streamlit tabs:
- **Download** — URL input, video info display, download options, download execution
- **Batch** — Batch download with parallel processing, network/proxy settings
- **Monitor** — System metrics (CPU, memory, disk, network speed)
- **History** — Download history with session persistence via `st.session_state`
- **System** — Dependency status and installation instructions

### Key Functions

- `check_ffmpeg_availability()` — Non-blocking check for ffmpeg in PATH
- `serve_file_safely()` — File serving with size-based safety checks (prevents OOM)
- `create_yt_dlp_progress_hook()` — Progress hook for yt-dlp Python API
- `download_with_ytdlp_api()` — Download using yt-dlp Python API (not subprocess)
- `check_dependencies()` — Cached function verifying yt-dlp/ffmpeg/ffprobe
- `validate_url()` — URL format validation using urlparse
- `categorize_error()` — Maps yt-dlp errors to user-friendly messages

### State Management

Uses `st.session_state` for:
- `video_info` — Fetched video metadata
- `is_playlist_url` — Playlist detection flag
- `download_history` — List of download records
- `downloading` — Active download flag
- `batch_*` — Batch download state
- `is_mobile` — Mobile layout toggle

### Download Flow

1. User enters URL and clicks "Fetch Info"
2. yt-dlp extracts metadata (`skip_download=True`)
3. User selects options (type, quality, format, subtitles, etc.)
4. Download executes via yt-dlp Python API with progress hooks
5. Files served via `st.download_button` (with size limits)
6. Temp directory cleaned up after download

## UI Design System

### Color Palette
- **Background:** #000000 (pure black)
- **Surface:** #0A0A0A (cards, inputs)
- **Border:** #1A1A1A (subtle borders)
- **Text Primary:** #FFFFFF
- **Text Secondary:** #666666
- **Success:** #22C55E
- **Error:** #EF4444
- **Warning:** #EAB308

### Typography
- **Font:** Inter (Google Fonts)
- **Headers:** 500-600 weight, -0.01em letter-spacing
- **Labels:** 0.8125rem, uppercase, 500 weight
- **Body:** 0.9375rem, 400 weight

### Design Principles
- Minimal, no emojis in UI text
- White primary buttons on black background
- Underline-style tab selection
- Subtle 1px borders
- 8px border radius for cards/inputs
- 6px border radius for buttons

## Known Limitations

### Memory Constraints
- Files over 100MB cannot be served via `st.download_button`
- `MAX_SAFE_FILE_SIZE_MB` constant controls this limit
- Large files show a warning with temp file path

### Scalability
- Single-user design: Heavy downloads impact responsiveness
- No job queue: Downloads execute immediately
- Session-based state: Cannot scale horizontally without sticky sessions

### FFmpeg Dependency
- Required for audio extraction and metadata embedding
- App checks non-blocking at startup, continues without it
- Audio-only downloads disabled if ffmpeg is missing

## Deployment

- **Streamlit Cloud:** Uses `packages.txt` for apt packages (ffmpeg)
- **Dev Container:** Python 3.11, auto-installs deps, port 8501
- **Memory:** Allocate 512MB minimum; 1GB+ recommended
