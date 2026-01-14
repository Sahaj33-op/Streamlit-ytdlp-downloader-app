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

This is a single-file Streamlit application (`app.py`) that provides a web GUI for yt-dlp video downloading.

### Core Structure

The app is organized into 5 Streamlit tabs:
- **Download (tab1):** URL input, video info display, download options, and download execution
- **Advanced (tab2):** Batch download with parallel processing, network/proxy settings, custom format options
- **Monitor (tab3):** System metrics (CPU, memory, disk, network speed)
- **History (tab4):** Download history with session persistence via `st.session_state`
- **System (tab5):** Dependency status and installation instructions

### Key Functions

- `check_ffmpeg_availability()` - Non-blocking check for ffmpeg in PATH (fails gracefully if missing)
- `serve_file_safely()` - File serving with size-based safety checks to prevent memory exhaustion
- `create_yt_dlp_progress_hook()` - Progress hook for yt-dlp Python API (replaces regex parsing)
- `download_with_ytdlp_api()` - Download using yt-dlp Python API instead of subprocess
- `check_dependencies()` - Cached function that verifies yt-dlp/ffmpeg/ffprobe availability
- `validate_url()` - URL format validation using urlparse
- `categorize_error()` - Maps yt-dlp errors to user-friendly messages with solutions
- `cleanup_temp_files()` - Removes temporary directories prefixed with `ytdlp_`

### State Management

Uses `st.session_state` for:
- `video_info` - Fetched video metadata from yt-dlp
- `is_playlist_url` - Boolean flag for playlist detection
- `download_history` - List of download records
- `downloading` - Active download flag
- `batch_*` - Batch download state (temp_dir, urls_list, settings, trigger)
- `is_mobile` - Mobile layout toggle

### Download Flow

1. User enters URL and clicks "Fetch Info"
2. yt-dlp extracts metadata without downloading (`skip_download=True`)
3. User selects options (type, quality, format, subtitles, etc.)
4. Download executes via yt-dlp Python API with progress hooks
5. Files are saved to temp directory, then served via `st.download_button` (with size limits)
6. Temp directory cleaned up after download or on session cleanup

### Styling

Custom CSS is injected via `st.markdown(unsafe_allow_html=True)` providing:
- Dark gradient theme with glassmorphism effects
- Mobile-responsive breakpoints at 1200px, 768px, 480px, 360px
- Accessibility features (prefers-reduced-motion)

## Known Limitations

### Memory Constraints
- **File size limit:** Files over 100MB cannot be served via `st.download_button` due to memory constraints
- The `MAX_SAFE_FILE_SIZE_MB` constant (default: 100) controls this limit
- Large files show a warning with the temp file path for manual retrieval
- Adjust this limit based on available server memory

### Scalability
- Single-user design: Heavy downloads will impact responsiveness
- No job queue: Downloads execute immediately, no rate limiting
- Session-based state: Cannot scale horizontally without sticky sessions

### FFmpeg Dependency
- FFmpeg is required for audio extraction and metadata embedding
- App checks for ffmpeg non-blocking at startup but continues without it
- Audio-only downloads and metadata features are disabled if ffmpeg is missing

## Deployment

- **Streamlit Cloud:** Uses `packages.txt` for apt packages (ffmpeg) and `requirements.txt` for Python packages
- **Dev Container:** Configured in `.devcontainer/devcontainer.json` with Python 3.11, auto-installs deps, and starts the server on port 8501
- **Memory:** Allocate at least 512MB RAM; 1GB+ recommended for concurrent users
