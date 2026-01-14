import streamlit as st
import subprocess
import os
import tempfile
import json
import re
import shutil
import yt_dlp
import requests
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import platform
import sys
import zipfile
import stat
import tarfile
import threading

# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Maximum file size (in bytes) that can be safely loaded into memory for download
# Files larger than this will show a warning and require manual retrieval
MAX_SAFE_FILE_SIZE_MB = 100
MAX_SAFE_FILE_SIZE_BYTES = MAX_SAFE_FILE_SIZE_MB * 1024 * 1024

# FFmpeg status tracking
_ffmpeg_status = {"checked": False, "available": False, "message": ""}


def check_ffmpeg_availability():
    """Check if ffmpeg is available without blocking startup."""
    global _ffmpeg_status
    if _ffmpeg_status["checked"]:
        return _ffmpeg_status["available"]

    _ffmpeg_status["checked"] = True
    if shutil.which("ffmpeg"):
        _ffmpeg_status["available"] = True
        _ffmpeg_status["message"] = "FFmpeg found in PATH"
    else:
        _ffmpeg_status["available"] = False
        _ffmpeg_status["message"] = "FFmpeg not found. Some features may be limited."

    return _ffmpeg_status["available"]


def get_ffmpeg_status():
    """Get the current ffmpeg status message."""
    check_ffmpeg_availability()
    return _ffmpeg_status


# Check ffmpeg availability (non-blocking)
check_ffmpeg_availability()

def cleanup_temp_dir_robust(temp_dir):
    if not temp_dir or not os.path.exists(temp_dir):
        return True
    try:
        shutil.rmtree(temp_dir, ignore_errors=False)
        return True
    except PermissionError:
        st.warning(f"Permission error while cleaning up {temp_dir}. Some files may remain.")
        return False
    except OSError as e:
        st.error(f"Failed to clean up {temp_dir}: {str(e)}")
        return False
    except Exception as e:
        st.error(f"Unexpected error cleaning up {temp_dir}: {str(e)}")
        return False


def is_file_safe_for_memory(file_size):
    """Check if a file is small enough to safely load into memory."""
    return file_size <= MAX_SAFE_FILE_SIZE_BYTES


def serve_file_safely(file_path, filename, file_size, button_key, container=None):
    """
    Serve a file for download, with size-based safety checks.

    For files under MAX_SAFE_FILE_SIZE_MB: Use st.download_button (loads into memory)
    For larger files: Show warning and file path for manual retrieval

    Returns True if file was served, False if too large.
    """
    target = container if container else st
    size_mb = file_size / (1024 * 1024)

    if is_file_safe_for_memory(file_size):
        # Safe to load into memory
        with open(file_path, "rb") as f:
            target.download_button(
                label=f"Download {filename} ({size_mb:.1f} MB)",
                data=f.read(),
                file_name=filename,
                mime="application/octet-stream",
                key=button_key,
                use_container_width=True
            )
        return True
    else:
        # File too large - show warning instead of loading into memory
        target.warning(
            f"**{filename}** ({size_mb:.1f} MB) exceeds the {MAX_SAFE_FILE_SIZE_MB}MB limit "
            f"for browser downloads. Large files may cause memory issues."
        )
        target.info(f"📂 **File saved to:** `{file_path}`")
        target.markdown(
            f"💡 **Tip:** Access the file directly from the server's temp directory, "
            f"or reduce the video quality to get smaller files."
        )
        return False


def create_yt_dlp_progress_hook(progress_bar, status_text=None):
    """
    Create a progress hook for yt-dlp that updates a Streamlit progress bar.

    This replaces the need to parse stdout with regex.
    """
    def progress_hook(d):
        if d['status'] == 'downloading':
            # Calculate progress
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                progress = downloaded / total
                progress_bar.progress(min(progress, 1.0))

            if status_text:
                speed = d.get('speed')
                if speed:
                    speed_str = f"{speed / 1024 / 1024:.1f} MB/s"
                else:
                    speed_str = "calculating..."
                eta = d.get('eta')
                eta_str = f"{eta}s" if eta else "unknown"
                status_text.text(f"Speed: {speed_str} | ETA: {eta_str}")

        elif d['status'] == 'finished':
            progress_bar.progress(1.0)
            if status_text:
                status_text.text("Download complete, processing...")

    return progress_hook


def download_with_ytdlp_api(url, output_dir, options, progress_bar=None, status_text=None):
    """
    Download using yt-dlp Python API instead of subprocess.

    Returns dict with 'success', 'files', 'error' keys.
    """
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title).100s-%(id)s.%(ext)s'),
        'restrictfilenames': True,
        'quiet': True,
        'no_warnings': True,
    }

    # Add progress hook if progress bar provided
    if progress_bar:
        ydl_opts['progress_hooks'] = [create_yt_dlp_progress_hook(progress_bar, status_text)]

    # Apply download type options
    download_type = options.get('download_type', 'Video + Audio')
    quality = options.get('quality', 'Best Available')
    audio_format = options.get('audio_format', 'mp3')

    if download_type == "Audio Only":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
        }]
    elif download_type == "Video Only":
        ydl_opts['format'] = 'bestvideo'
    else:
        # Video + Audio
        if quality != "Best Available":
            quality_map = {
                "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]"
            }
            ydl_opts['format'] = quality_map.get(quality, 'best')
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

    # Additional options
    if options.get('download_subs'):
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = ['en']

    if options.get('download_thumbnail'):
        ydl_opts['writethumbnail'] = True

    if options.get('embed_metadata') and check_ffmpeg_availability():
        ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
        ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

    if options.get('max_file_size') and options['max_file_size'] != "No Limit":
        size_map = {"100MB": 100*1024*1024, "500MB": 500*1024*1024,
                    "1GB": 1000*1024*1024, "2GB": 2000*1024*1024}
        ydl_opts['max_filesize'] = size_map.get(options['max_file_size'])

    # Playlist options
    if options.get('playlist_start', 1) > 1:
        ydl_opts['playliststart'] = options['playlist_start']
    if options.get('playlist_end', 0) > 0:
        ydl_opts['playlistend'] = options['playlist_end']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Collect downloaded files
        files = []
        for root, _, filenames in os.walk(output_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                files.append((filename, file_path, os.path.getsize(file_path)))

        return {'success': True, 'files': files, 'error': None}

    except Exception as e:
        return {'success': False, 'files': [], 'error': str(e)}


st.set_page_config(
    layout="wide",
    page_title="YT-DLP Downloader",
    page_icon="▼",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# MODERN MINIMAL BLACK UI - Clean, Professional Design
# =============================================================================
st.markdown("""
<style>
    /* ========== CSS RESET & BASE ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: #000000;
        color: #E5E5E5;
    }

    /* Hide Streamlit chrome and reduce top padding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Remove default Streamlit top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px !important;
    }

    /* ========== TYPOGRAPHY ========== */
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #FFFFFF;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        margin: 0 auto;
        letter-spacing: -0.02em;
        width: 100%;
        display: block;
    }

    .sub-header {
        text-align: center;
        color: #666666;
        font-size: 1rem;
        font-weight: 400;
        margin: 0 auto 2rem auto;
        padding: 0;
        letter-spacing: 0.01em;
        width: 100%;
        display: block;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 500;
        letter-spacing: -0.01em;
    }

    .video-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 0.75rem;
        line-height: 1.4;
    }

    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        gap: 0;
        border-bottom: 1px solid #1A1A1A;
        padding: 0;
        margin-bottom: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #666666;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
        padding: 1rem 1.5rem;
        font-size: 0.875rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #999999;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid #FFFFFF !important;
    }

    /* ========== FORM ELEMENTS ========== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        background: #0A0A0A !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-size: 0.9375rem;
        padding: 0.75rem 1rem;
        transition: border-color 0.2s ease;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div:focus-within {
        border-color: #333333 !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #444444 !important;
    }

    /* Labels */
    .stTextInput > label,
    .stSelectbox > label,
    .stNumberInput > label,
    .stTextArea > label,
    .stCheckbox > label {
        color: #888888 !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ========== BUTTONS ========== */
    .stButton > button {
        background: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.625rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }

    .stButton > button:hover {
        background: #E5E5E5 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    .stButton > button:active {
        background: #CCCCCC !important;
    }

    /* Secondary/Ghost buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: #555555 !important;
        background: #0A0A0A !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background: #0A0A0A !important;
        color: #FFFFFF !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stDownloadButton > button:hover {
        border-color: #333333 !important;
        background: #111111 !important;
    }

    /* ========== PROGRESS BAR ========== */
    .stProgress > div > div > div > div {
        background: #FFFFFF !important;
        border-radius: 2px;
    }

    .stProgress > div > div > div {
        background: #1A1A1A !important;
    }

    /* ========== ALERTS/STATUS ========== */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        border-radius: 8px !important;
        color: #22C55E !important;
    }

    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-radius: 8px !important;
        color: #EF4444 !important;
    }

    .stWarning {
        background: rgba(234, 179, 8, 0.1) !important;
        border: 1px solid rgba(234, 179, 8, 0.3) !important;
        border-radius: 8px !important;
        color: #EAB308 !important;
    }

    .stInfo {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #999999 !important;
    }

    /* ========== CARDS & CONTAINERS ========== */
    .info-card {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Expander */
    .stExpander {
        background: transparent !important;
        border: 1px solid #1A1A1A !important;
        border-radius: 8px !important;
    }

    .stExpander > div > div > div > div {
        color: #FFFFFF !important;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background: #0A0A0A;
        border: 1px solid #1A1A1A;
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="metric-container"] label {
        color: #666666 !important;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* ========== CHECKBOX & RADIO ========== */
    .stCheckbox > label > div {
        color: #E5E5E5 !important;
    }

    .stCheckbox > label > div[data-checked="true"]::before {
        background: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }

    /* ========== DIVIDER ========== */
    hr {
        border-color: #1A1A1A !important;
        margin: 2rem 0;
    }

    /* ========== SIDEBAR ========== */
    [data-testid="stSidebar"] {
        background: #050505 !important;
        border-right: 1px solid #1A1A1A;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #111111 !important;
        border: 1px solid #1A1A1A !important;
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: #333333 !important;
    }

    /* ========== STATUS BADGES ========== */
    .dep-available {
        background: #0A0A0A;
        color: #22C55E;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .dep-missing {
        background: #0A0A0A;
        color: #EF4444;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* ========== IMAGE/THUMBNAIL ========== */
    .stImage {
        border-radius: 8px;
        overflow: hidden;
    }

    .stImage img {
        border-radius: 8px;
    }

    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0A0A0A;
    }

    ::-webkit-scrollbar-thumb {
        background: #333333;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #444444;
    }

    /* ========== RESPONSIVE ========== */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .main-header {
            font-size: 1.75rem !important;
            padding: 0.5rem 0 0.25rem 0 !important;
        }

        .sub-header {
            font-size: 0.875rem !important;
            margin-bottom: 1.5rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            margin-bottom: 1.5rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem !important;
            font-size: 0.8125rem !important;
        }

        .video-title {
            font-size: 1.1rem !important;
        }
    }

    @media (max-width: 480px) {
        .block-container {
            padding-top: 0.25rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }

        .main-header {
            font-size: 1.5rem !important;
            padding: 0.25rem 0 0.25rem 0 !important;
        }

        .sub-header {
            font-size: 0.8rem !important;
            margin-bottom: 1rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap;
            gap: 0.25rem !important;
            margin-bottom: 1rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            flex: 1 1 auto;
            text-align: center;
            justify-content: center;
            padding: 0.5rem 0.75rem !important;
            font-size: 0.75rem !important;
        }

        h3 {
            font-size: 1.1rem !important;
        }

        .stButton > button {
            padding: 0.5rem 1rem !important;
            font-size: 0.8125rem !important;
        }

        .stDownloadButton > button {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.8125rem !important;
        }
    }

    @media (max-width: 360px) {
        .main-header {
            font-size: 1.25rem !important;
        }

        .sub-header {
            font-size: 0.75rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.5rem !important;
            font-size: 0.7rem !important;
        }
    }

    /* ========== REDUCED MOTION ========== */
    @media (prefers-reduced-motion: reduce) {
        * {
            transition: none !important;
            animation: none !important;
        }
    }

    /* ========== LOADING SPINNER ========== */
    .loading {
        width: 20px;
        height: 20px;
        border: 2px solid #333333;
        border-top-color: #FFFFFF;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* ========== FOOTER ========== */
    .app-footer {
        text-align: center;
        padding: 3rem 0;
        color: #444444;
        font-size: 0.8125rem;
        border-top: 1px solid #1A1A1A;
        margin-top: 4rem;
    }

    .app-footer a {
        color: #666666;
        text-decoration: none;
        transition: color 0.2s ease;
    }

    .app-footer a:hover {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def check_dependencies():
    deps = {
        'yt-dlp': False,
        'ffmpeg': False,
        'ffprobe': False
    }
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            deps['yt-dlp'] = result.stdout.strip()
    except:
        pass
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            deps['ffmpeg'] = result.stdout.split('\n')[0].strip()
    except:
        pass
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            deps['ffprobe'] = result.stdout.split('\n')[0].strip()
    except:
        pass
    return deps

def validate_url(url):
    if not url:
        return False, "URL cannot be empty"
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format. Please include http:// or https://"
        return True, "URL format is valid"
    except:
        return False, "Invalid URL format"

def parse_progress(line):
    progress_info = {}
    progress_match = re.search(r'\[download\]\s+(\d+\.?\d*)%.*?(\d+\.?\d*\w+/s)', line)
    if progress_match:
        progress_info['percent'] = float(progress_match.group(1))
        progress_info['speed'] = progress_match.group(2)
    eta_match = re.search(r'ETA\s+(\d+:\d+)', line)
    if eta_match:
        progress_info['eta'] = eta_match.group(1)
    return progress_info

def categorize_error(error_message):
    error_lower = error_message.lower()
    if 'network' in error_lower or 'connection' in error_lower or 'timeout' in error_lower:
        return "Network Error", "Check your internet connection and try again."
    elif 'login' in error_lower or 'authentication' in error_lower or 'private' in error_lower:
        if 'instagram' in error_lower and 'stories' in error_lower:
            return "Instagram Story Restriction", "Instagram stories often require login. Try a public post or reel."
        return "Authentication Required", "This content requires login, which is disabled. Try a different video."
    elif 'format' in error_lower and 'not available' in error_lower:
        return "Format Error", "Try a different quality setting."
    elif 'ffmpeg' in error_lower:
        return "FFmpeg Error", "FFmpeg is required. Check the System tab to install it."
    elif 'instagram' in error_lower:
        return "Instagram Restriction", "Instagram content may have restrictions. Try a different URL."
    elif 'youtube' in error_lower:
        return "YouTube Restriction", "Some YouTube videos are restricted. Try a different video."
    elif 'unsupported' in error_lower or 'not a valid' in error_lower:
        return "URL Error", "The URL is invalid or from an unsupported site."
    elif 'permission denied' in error_lower or 'cannot write' in error_lower:
        return "Permission Error", "Check write permissions to the output directory."
    elif 'invalid option' in error_lower or 'unknown option' in error_lower:
        return "Configuration Error", "Check the advanced options."
    elif 'live stream' in error_lower or 'cannot download live' in error_lower:
        return "Live Stream Error", "Live streams cannot be downloaded."
    elif 'rate limit' in error_lower or 'too many requests' in error_lower:
        return "Rate Limit Error", "Too many requests. Try again later."
    elif 'video unavailable' in error_lower or 'deleted' in error_lower:
        return "Content Error", "The video is unavailable or deleted."
    elif 'no subtitles' in error_lower or 'subtitles not found' in error_lower:
        return "Subtitle Error", "Subtitles are not available."
    elif 'disk full' in error_lower or 'no space left' in error_lower:
        return "Disk Space Error", "Free up disk space and try again."
    elif 'ssl' in error_lower or 'certificate' in error_lower:
        return "SSL Error", "Update certificates or check network settings."
    elif 'proxy' in error_lower:
        return "Proxy Error", "Check proxy configuration."
    elif 'invalid character' in error_lower or 'filename too long' in error_lower:
        return "Filename Error", "Change the filename template in advanced settings."
    elif 'index out of range' in error_lower or 'invalid playlist index' in error_lower:
        return "Playlist Error", "Check playlist indices."
    elif 'file too large' in error_lower or 'exceeds max size' in error_lower:
        return "File Size Error", "Try lower quality or increase the limit."
    else:
        return "Unknown Error", "An unexpected error occurred."

if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'is_playlist_url' not in st.session_state:
    st.session_state.is_playlist_url = False
if 'download_history' not in st.session_state:
    st.session_state.download_history = []

# Simple mobile detection using user agent
user_agent = st.get_option("server.enableCORS")
is_mobile = st.session_state.get('is_mobile', False)

# Add a hidden component to detect mobile via JavaScript
mobile_detector = st.empty()
mobile_detector.markdown("""
<script>
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                 window.innerWidth <= 768;
if (isMobile) {
    document.body.classList.add('mobile-device');
}
</script>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">YT-DLP Downloader</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Download videos and audio from 1000+ platforms</p>', unsafe_allow_html=True)

deps = check_dependencies()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Download",
    "Batch",
    "Monitor",
    "History",
    "System"
])

with tab1:
    if not all(deps.values()):
        st.warning("Some dependencies are missing. Check the System tab.")
    st.markdown("### Enter URL")
    # Mobile-friendly layout: stack vertically on small screens
    if st.session_state.get('is_mobile', False):
        url = st.text_input(
            "Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any video, playlist, or channel URL",
            label_visibility="collapsed"
        )
        fetch_clicked = st.button("Fetch Info", use_container_width=True, disabled=not url)
    else:
        col1, col2 = st.columns([4, 1])
        with col1:
            url = st.text_input(
                "Video URL",
                placeholder="https://www.youtube.com/watch?v=...",
                help="Paste any video, playlist, or channel URL",
                label_visibility="collapsed"
            )
        with col2:
            fetch_clicked = st.button("Fetch Info", use_container_width=True, disabled=not url)
    if url:
        is_valid, message = validate_url(url)
        if is_valid:
            st.success(f"{message}")
        else:
            st.error(f"{message}")
    if fetch_clicked and url:
        with st.spinner("Fetching video information..."):
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state.video_info = info
                    st.session_state.is_playlist_url = info.get('_type') == 'playlist' or 'entries' in info
                st.success("Information fetched successfully!")
                st.rerun()
            except Exception as e:
                error_type, error_solution = categorize_error(str(e))
                st.error(f"{error_type}: {error_solution}")
    if st.session_state.video_info:
        info = st.session_state.video_info
        st.markdown("### 📺 Video Information")
        # Mobile-friendly video info layout
        if st.session_state.get('is_mobile', False):
            if info.get('thumbnail'):
                st.image(info['thumbnail'], use_container_width=True)
            st.markdown(f'<div class="video-title">{info.get("title", "N/A")}</div>', unsafe_allow_html=True)
            if st.session_state.is_playlist_url:
                entries_count = len(info.get('entries', []))
                st.markdown(f"**Type:** Playlist ({entries_count:,} videos)")
            else:
                st.markdown(f"**Type:** Single Video")
                st.markdown(f"**Duration:** {info.get('duration_string', 'N/A')}")
                if info.get('view_count'):
                    st.markdown(f"**👀 Views:** {info['view_count']:,}")
            st.markdown(f"**👤 Uploader:** {info.get('uploader', 'N/A')}")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                if info.get('thumbnail'):
                    st.image(info['thumbnail'], use_container_width=True)
            with col2:
                st.markdown(f'<div class="video-title">{info.get("title", "N/A")}</div>', unsafe_allow_html=True)
                if st.session_state.is_playlist_url:
                    entries_count = len(info.get('entries', []))
                    st.markdown(f"**Type:** Playlist ({entries_count:,} videos)")
                else:
                    st.markdown(f"**Type:** Single Video")
                    st.markdown(f"**Duration:** {info.get('duration_string', 'N/A')}")
                    if info.get('view_count'):
                        st.markdown(f"**👀 Views:** {info['view_count']:,}")
                st.markdown(f"**👤 Uploader:** {info.get('uploader', 'N/A')}")
        st.markdown("### Download Options")
        # Mobile-friendly download options layout
        if st.session_state.get('is_mobile', False):
            download_type = st.selectbox(
                "Download Type",
                ["Video + Audio", "Audio Only", "Video Only"]
            )
            if download_type != "Audio Only":
                quality = st.selectbox(
                    "Video Quality",
                    ["Best Available", "1080p", "720p", "480p", "360p"]
                )
            else:
                quality = "Best Available"
            if download_type == "Audio Only":
                audio_format = st.selectbox(
                    "Audio Format",
                    ["mp3", "aac", "m4a", "opus", "flac"]
                )
            else:
                audio_format = "mp3"
        else:
            option_col1, option_col2, option_col3 = st.columns(3)
            with option_col1:
                download_type = st.selectbox(
                    "Download Type",
                    ["Video + Audio", "Audio Only", "Video Only"]
                )
            with option_col2:
                if download_type != "Audio Only":
                    quality = st.selectbox(
                        "Video Quality",
                        ["Best Available", "1080p", "720p", "480p", "360p"]
                    )
                else:
                    quality = "Best Available"
            with option_col3:
                if download_type == "Audio Only":
                    audio_format = st.selectbox(
                        "Audio Format",
                        ["mp3", "aac", "m4a", "opus", "flac"]
                    )
                else:
                    audio_format = "mp3"
        with st.expander("➕ Additional Options"):
            # Mobile-friendly additional options layout
            if st.session_state.get('is_mobile', False):
                download_subs = st.checkbox("Download Subtitles")
                download_thumbnail = st.checkbox("Download Thumbnail")
                if st.session_state.is_playlist_url:
                    playlist_start = st.number_input("Start from video #", min_value=1, value=1)
                    playlist_end = st.number_input("End at video # (0 = all)", min_value=0, value=0)
                else:
                    playlist_start = 1
                    playlist_end = 0
                embed_metadata = st.checkbox("Add Metadata", disabled=not deps['ffmpeg'])
                max_file_size = st.selectbox(
                    "Max File Size",
                    ["No Limit", "100MB", "500MB", "1GB", "2GB"]
                )
            else:
                option_col1, option_col2 = st.columns(2)
                with option_col1:
                    download_subs = st.checkbox("Download Subtitles")
                    download_thumbnail = st.checkbox("Download Thumbnail")
                    if st.session_state.is_playlist_url:
                        playlist_start = st.number_input("Start from video #", min_value=1, value=1)
                        playlist_end = st.number_input("End at video # (0 = all)", min_value=0, value=0)
                    else:
                        playlist_start = 1
                        playlist_end = 0
                with option_col2:
                    embed_metadata = st.checkbox("Add Metadata", disabled=not deps['ffmpeg'])
                    max_file_size = st.selectbox(
                        "Max File Size",
                        ["No Limit", "100MB", "500MB", "1GB", "2GB"]
                    )
        st.markdown("---")
        # Mobile-friendly download button layout
        if st.session_state.get('is_mobile', False):
            if st.button("Start Download", type="primary", use_container_width=True):
                if not deps['yt-dlp']:
                    st.error("yt-dlp is required but not installed!")
                else:
                    st.session_state.downloading = True
                    st.rerun()
        else:
            download_col1, download_col2, download_col3 = st.columns([2, 2, 2])
            with download_col2:
                if st.button("Start Download", type="primary", use_container_width=True):
                    if not deps['yt-dlp']:
                        st.error("yt-dlp is required but not installed!")
                    else:
                        st.session_state.downloading = True
                        st.rerun()
    if st.session_state.get('downloading', False):
        st.markdown("### Downloading...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        temp_dir = tempfile.mkdtemp(prefix="ytdlp_")

        try:
            # Build download options for the yt-dlp API
            download_options = {
                'download_type': download_type,
                'quality': quality,
                'audio_format': audio_format,
                'download_subs': download_subs,
                'download_thumbnail': download_thumbnail,
                'embed_metadata': embed_metadata and deps['ffmpeg'],
                'max_file_size': max_file_size,
                'playlist_start': playlist_start if st.session_state.is_playlist_url else 1,
                'playlist_end': playlist_end if st.session_state.is_playlist_url else 0,
            }

            # Use yt-dlp Python API instead of subprocess
            result = download_with_ytdlp_api(
                url=url,
                output_dir=temp_dir,
                options=download_options,
                progress_bar=progress_bar,
                status_text=status_text
            )

            if result['success'] and result['files']:
                downloaded_files = result['files']
                progress_bar.progress(1.0)
                status_text.empty()
                st.success(f"Downloaded {len(downloaded_files)} file(s)!")
                st.markdown("### Download Files")

                # Calculate total size for warnings
                total_size = sum(f[2] for f in downloaded_files)
                large_files_count = sum(1 for f in downloaded_files if f[2] > MAX_SAFE_FILE_SIZE_BYTES)

                if large_files_count > 0:
                    st.warning(
                        f"{large_files_count} file(s) exceed {MAX_SAFE_FILE_SIZE_MB}MB. "
                        f"Large files cannot be downloaded via browser due to memory constraints."
                    )

                for i, (filename, file_path, size) in enumerate(downloaded_files):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Use safe file serving with size checks
                        serve_file_safely(
                            file_path=file_path,
                            filename=filename,
                            file_size=size,
                            button_key=f"download_btn_{i}"
                        )
                    with col2:
                        st.markdown(f"**{size / 1024 / 1024:.1f} MB**")

                st.session_state.download_history.insert(0, {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": url[:50] + "..." if len(url) > 50 else url,
                    "title": st.session_state.video_info.get('title', 'Unknown')[:30] + "...",
                    "files": len(downloaded_files),
                    "status": "Success"
                })
            else:
                st.error("Download failed!")
                if result['error']:
                    error_type, error_solution = categorize_error(result['error'])
                    st.markdown(f"**Error:** {error_type}")
                    st.markdown(f"**Solution:** {error_solution}")

        except Exception as e:
            st.error(f"Error: {str(e)}")
            error_type, error_solution = categorize_error(str(e))
            st.markdown(f"**Error:** {error_type}")
            st.markdown(f"**Solution:** {error_solution}")
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            st.session_state.downloading = False
            if st.button("Download Another"):
                st.rerun()

with tab2:
    st.markdown("### Batch Download & Advanced Settings")
    if st.session_state.get("batch_temp_dir") and not st.session_state.get("batch_download_trigger", False):
        with st.spinner("Cleaning up previous session files..."):
            if cleanup_temp_dir_robust(st.session_state.batch_temp_dir):
                st.session_state.batch_temp_dir = None
                st.success("Cleaned up old temporary files.")
            else:
                st.warning("Could not clean up all old temporary files.")
    st.markdown("## Batch Download")
    st.markdown("Download multiple videos at once with the same settings.")
    col1, col2 = st.columns([2, 1])
    with col1:
        batch_urls = st.text_area(
            "📝 Video URLs (one per line)",
            height=150,
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ\nhttps://www.youtube.com/watch?v=example2"
        )
        urls_list = [u.strip() for u in batch_urls.split('\n') if u.strip()]
        if urls_list:
            st.info(f"{len(urls_list)} URL{'s' if len(urls_list) > 1 else ''} ready for download")
    with col2:
        if urls_list:
            st.markdown("**📊 Quick Preview:**")
            for i, url in enumerate(urls_list[:3], 1):
                domain = url.split('/')[2] if '/' in url else url
                st.text(f"{i}. {domain}")
            if len(urls_list) > 3:
                st.text(f"... and {len(urls_list) - 3} more")
    if urls_list:
        st.markdown("### Batch Download Settings")
        setting_col1, setting_col2, setting_col3 = st.columns(3)
        with setting_col1:
            batch_download_type = st.selectbox(
                "📹 Download Type",
                ["Video + Audio", "Audio Only", "Video Only"]
            )
        with setting_col2:
            if batch_download_type != "Audio Only":
                batch_quality = st.selectbox(
                    "🎯 Video Quality",
                    ["Best Available", "1080p", "720p", "480p", "360p"]
                )
            else:
                batch_quality = "Best Available"
        with setting_col3:
            if batch_download_type == "Audio Only":
                batch_audio_format = st.selectbox(
                    "Audio Format",
                    ["mp3", "aac", "m4a", "opus", "flac"]
                )
            else:
                batch_audio_format = "mp3"
        with st.expander("🔧 Additional Batch Options"):
            batch_col1, batch_col2 = st.columns(2)
            with batch_col1:
                batch_subs = st.checkbox("📝 Download Subtitles")
                batch_thumbnail = st.checkbox("🖼️ Download Thumbnails")
                batch_metadata = st.checkbox("Add Metadata", disabled=not deps.get('ffmpeg', False))
            with batch_col2:
                batch_max_size = st.selectbox(
                    "📏 Max File Size (per file)",
                    ["No Limit", "100MB", "500MB", "1GB", "2GB"]
                )
                batch_timeout = st.slider(
                    "Timeout per URL (minutes)",
                    min_value=5, max_value=30, value=15
                )
                batch_parallel = st.slider(
                    "Parallel Downloads",
                    min_value=1, max_value=10, value=3,
                    help="Number of simultaneous downloads"
                )
    if urls_list and not st.session_state.get("batch_download_trigger", False):
        st.markdown("---")
        estimated_time = len(urls_list) * 2 / (st.session_state.get('batch_parallel', 3) or 3)
        st.info(f"Estimated time: ~{int(estimated_time)} minutes for {len(urls_list)} URL(s)")
        if len(urls_list) > 10:
            st.warning("Large batch detected! Consider reducing parallel downloads if issues occur.")
        start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
        with start_col2:
            if st.button("Start Batch Download", type="primary", use_container_width=True):
                if not deps.get('yt-dlp', False):
                    st.error("yt-dlp is required but not installed!")
                else:
                    st.session_state.batch_download_trigger = True
                    st.session_state.batch_urls_list = urls_list
                    st.session_state.batch_temp_dir = tempfile.mkdtemp(prefix="ytdlp_batch_")
                    st.session_state.batch_settings = {
                        'download_type': batch_download_type,
                        'quality': batch_quality,
                        'audio_format': batch_audio_format,
                        'subs': batch_subs,
                        'thumbnail': batch_thumbnail,
                        'metadata': batch_metadata,
                        'max_size': batch_max_size,
                        'timeout': batch_timeout * 60,
                        'parallel': batch_parallel
                    }
                    st.rerun()
    if st.session_state.get("batch_download_trigger", False):
        urls_to_process = st.session_state.get("batch_urls_list", [])
        batch_temp_dir = st.session_state.get("batch_temp_dir")
        batch_settings = st.session_state.get("batch_settings", {})
        total_urls = len(urls_to_process)
        st.markdown("---")
        st.markdown("## Batch Download in Progress")
        st.markdown(f"Processing {total_urls} URL(s) with {batch_settings.get('parallel', 3)} parallel downloads...")

        # Progress tracking
        progress_container = st.container()
        with progress_container:
            overall_progress = st.progress(0)
            current_status = st.empty()
            results_container = st.container()

        # Function to download a single URL using yt-dlp Python API
        def download_single_url(url, temp_dir, settings, task_id):
            # Create unique subdirectory for each task
            task_temp_dir = os.path.join(temp_dir, f"task_{task_id}")
            os.makedirs(task_temp_dir, exist_ok=True)

            # Build yt-dlp options
            ydl_opts = {
                'outtmpl': os.path.join(task_temp_dir, '%(title).100s-%(id)s.%(ext)s'),
                'restrictfilenames': True,
                'quiet': True,
                'no_warnings': True,
            }

            download_type = settings.get('download_type', 'Video + Audio')
            quality = settings.get('quality', 'Best Available')
            audio_format = settings.get('audio_format', 'mp3')

            if download_type == "Audio Only":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                }]
            elif download_type == "Video Only":
                ydl_opts['format'] = 'bestvideo'
            else:
                if quality != "Best Available":
                    quality_map = {
                        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]"
                    }
                    ydl_opts['format'] = quality_map.get(quality, 'best')
                else:
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'

            if settings.get('subs', False):
                ydl_opts['writesubtitles'] = True
                ydl_opts['subtitleslangs'] = ['en']

            if settings.get('thumbnail', False):
                ydl_opts['writethumbnail'] = True

            if settings.get('metadata', False) and check_ffmpeg_availability():
                ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
                ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

            max_size = settings.get('max_size', 'No Limit')
            if max_size != "No Limit":
                size_map = {"100MB": 100*1024*1024, "500MB": 500*1024*1024,
                            "1GB": 1000*1024*1024, "2GB": 2000*1024*1024}
                ydl_opts['max_filesize'] = size_map.get(max_size)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown') if info else 'Unknown'
                    if len(title) > 50:
                        title = title[:47] + "..."

                # Collect downloaded files
                files = []
                for root, _, filenames in os.walk(task_temp_dir):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        files.append((filename, file_path, os.path.getsize(file_path)))

                return {"url": url, "title": title, "status": "success", "files": files}

            except Exception as e:
                error_type, error_solution = categorize_error(str(e))
                return {"url": url, "title": "Failed", "status": "error", "error": f"{error_type}: {error_solution}"}

        # Process URLs in parallel
        success_count = 0
        fail_count = 0
        skip_count = 0
        all_downloaded_files = []
        results = []

        with ThreadPoolExecutor(max_workers=batch_settings.get('parallel', 3)) as executor:
            future_to_url = {
                executor.submit(download_single_url, url, batch_temp_dir, batch_settings, idx): url
                for idx, url in enumerate(urls_to_process) if validate_url(url)[0]
            }
            for idx, future in enumerate(as_completed(future_to_url), 1):
                result = future.result()
                results.append(result)
                current_progress = idx / total_urls
                overall_progress.progress(current_progress)
                current_status.info(f"Processed {idx}/{total_urls}: {result['url'][:60]}...")
                with results_container:
                    if result['status'] == "success":
                        st.success(f"[{idx}/{total_urls}] {result['title']}")
                        success_count += 1
                        all_downloaded_files.extend(result.get('files', []))
                        st.session_state.download_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": result['url'][:50] + "..." if len(result['url']) > 50 else result['url'],
                            "title": result['title'],
                            "files": len(result.get('files', [])),
                            "status": "Success"
                        })
                    elif result['status'] == "timeout":
                        st.error(f"[{idx}/{total_urls}] Timeout - took longer than {batch_settings.get('timeout', 900)//60} minutes")
                        fail_count += 1
                    else:
                        st.error(f"[{idx}/{total_urls}] {result['title']}: {result.get('error', 'Unknown error')}")
                        fail_count += 1
                        st.session_state.download_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": result['url'][:50] + "..." if len(result['url']) > 50 else result['url'],
                            "title": "Failed",
                            "files": 0,
                            "status": "Failed"
                        })

        # Final results
        overall_progress.progress(1.0)
        if success_count > 0:
            current_status.success(f"Batch Complete! {success_count} succeeded, {fail_count} failed, {skip_count} skipped")
        else:
            current_status.error(f"Batch Complete. No downloads succeeded. {fail_count} failed, {skip_count} skipped")

        # Show downloadable files
        if all_downloaded_files:
            st.markdown("### Download Your Files")
            st.markdown(f"**{len(all_downloaded_files)} file(s) ready for download:**")

            # Warn about large files
            large_files_count = sum(1 for f in all_downloaded_files if f[2] > MAX_SAFE_FILE_SIZE_BYTES)
            if large_files_count > 0:
                st.warning(
                    f"{large_files_count} file(s) exceed {MAX_SAFE_FILE_SIZE_MB}MB. "
                    f"Large files cannot be downloaded via browser due to memory constraints."
                )

            all_downloaded_files.sort(key=lambda x: x[2], reverse=True)
            for idx, (filename, file_path, file_size) in enumerate(all_downloaded_files, 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Use safe file serving with size checks
                    serve_file_safely(
                        file_path=file_path,
                        filename=filename,
                        file_size=file_size,
                        button_key=f"batch_download_{idx}_{hash(file_path)}"
                    )
                with col2:
                    size_mb = file_size / (1024 * 1024)
                    st.markdown(f"**{size_mb:.1f} MB**")
        else:
            st.info("No files were successfully downloaded.")

        # Cleanup option
        st.markdown("---")
        cleanup_col1, cleanup_col2, cleanup_col3 = st.columns([1, 2, 1])
        with cleanup_col2:
            if st.button("Clean Up Server Files", use_container_width=True):
                if cleanup_temp_dir_robust(batch_temp_dir):
                    st.success("Server files cleaned up!")
                    st.session_state.batch_temp_dir = None
                else:
                    st.error("Failed to clean up some files.")
        st.session_state.batch_download_trigger = False
        st.session_state.batch_urls_list = []
    st.markdown("---")
    st.markdown("## 🔧 Advanced Settings")
    with st.expander("Network & Custom Settings"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            st.markdown("**Network Options**")
            use_proxy = st.checkbox("Use Proxy")
            if use_proxy:
                proxy_url = st.text_input("Proxy URL:", placeholder="http://proxy:port")
            else:
                proxy_url = ""
            rate_limit = st.slider("Rate Limit (KB/s)", 0, 10000, 0, step=100)
        with adv_col2:
            st.markdown("**🎛️ Custom Format**")
            custom_format = st.text_input(
                "Custom Format String:",
                placeholder="bv*+ba/b"
            )
            filename_template = st.text_input(
                "Filename Template:",
                value="%(title)s.%(ext)s"
            )
        if custom_format or use_proxy or rate_limit > 0:
            st.info("💡 These settings apply to single downloads.")
    st.session_state.advanced_settings = {
        'custom_format': custom_format,
        'filename_template': filename_template,
        'use_proxy': use_proxy,
        'proxy_url': proxy_url,
        'rate_limit': rate_limit
    }

with tab3:
    st.markdown("### 📊 System Monitor")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("CPU Usage", "Calculating...")
    with col2:
        try:
            import psutil
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent:.1f}%", f"{memory.available//1024//1024} MB free")
        except:
            st.metric("Memory Usage", "N/A")
    with col3:
        if hasattr(shutil, 'disk_usage'):
            try:
                total, used, free = shutil.disk_usage("/")
                free_gb = free // (1024**3)
                st.metric("Free Space", f"{free_gb} GB")
            except:
                st.metric("Free Space", "N/A")
        else:
            st.metric("Free Space", "N/A")
    with col4:
        if st.button("Test Speed"):
            with st.spinner("Testing network speed..."):
                try:
                    start_time = time.time()
                    response = requests.get("https://httpbin.org/bytes/1048576", timeout=30)
                    end_time = time.time()
                    if response.status_code == 200:
                        speed_mbps = (1.0 / (end_time - start_time)) * 8
                        st.metric("Network Speed", f"{speed_mbps:.1f} Mbps")
                    else:
                        st.metric("Network Speed", "Test Failed")
                except:
                    st.metric("Network Speed", "Test Failed")
    st.markdown("---")
    st.markdown("### Active Downloads")
    if st.session_state.get('downloading', False):
        st.info("Download in progress...")
    else:
        st.info("No active downloads")

with tab4:
    st.markdown("### 📚 Download History")
    if st.session_state.download_history:
        for i, entry in enumerate(st.session_state.download_history[:10]):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{entry['title']}**")
                    st.caption(entry['url'])
                with col2:
                    st.write(entry['timestamp'])
                with col3:
                    st.write(f"{entry['files']} files")
                with col4:
                    if entry['status'] == 'Success':
                        st.markdown('<p class="centered-success">Success</p>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p class="centered-error">Failed</p>', unsafe_allow_html=True)
                if i < len(st.session_state.download_history) - 1:
                    st.divider()
        if st.button("🗑️ Clear History"):
            st.session_state.download_history = []
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("📝 No download history yet.")

with tab5:
    st.markdown("### 🔧 System Information")
    st.markdown("#### Dependencies")
    dep_col1, dep_col2, dep_col3 = st.columns(3)
    with dep_col1:
        st.markdown("**yt-dlp**")
        if deps['yt-dlp']:
            st.markdown('<span class="dep-available">Installed</span>', unsafe_allow_html=True)
            st.caption(deps['yt-dlp'][:50] + "...")
        else:
            st.markdown('<span class="dep-missing">Missing</span>', unsafe_allow_html=True)
    with dep_col2:
        st.markdown("**FFmpeg**")
        if deps['ffmpeg']:
            st.markdown('<span class="dep-available">Installed</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="dep-missing">Missing</span>', unsafe_allow_html=True)
    with dep_col3:
        st.markdown("**FFprobe**")
        if deps['ffprobe']:
            st.markdown('<span class="dep-available">Installed</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="dep-missing">Missing</span>', unsafe_allow_html=True)
    if not all(deps.values()):
        st.markdown("---")
        st.markdown("#### 🛠️ Installation Instructions")
        system = platform.system().lower()
        install_col1, install_col2 = st.columns(2)
        with install_col1:
            st.markdown("**Install yt-dlp:**")
            if system == "windows":
                st.code("pip install yt-dlp")
            elif system == "darwin":
                st.code("pip install yt-dlp\n# or\nbrew install yt-dlp")
            else:
                st.code("pip install yt-dlp\n# or\nsudo apt install yt-dlp")
        with install_col2:
            st.markdown("**Install FFmpeg:**")
            if system == "windows":
                st.code("winget install FFmpeg")
            elif system == "darwin":
                st.code("brew install ffmpeg")
            else:
                st.code("sudo apt install ffmpeg")
    st.markdown("---")
    st.markdown("#### 💻 System Details")
    sys_col1, sys_col2 = st.columns(2)
    with sys_col1:
        st.markdown(f"**Platform:** {platform.system()} {platform.release()}")
        st.markdown(f"**Architecture:** {platform.machine()}")
        st.markdown(f"**Python:** {sys.version.split()[0]}")
    with sys_col2:
        st.markdown(f"**Processor:** {platform.processor() or 'Unknown'}")
        st.markdown(f"**Node:** {platform.node()}")

with st.sidebar:
    st.markdown("### Quick Actions")
    st.markdown("#### 📱 Format Presets")
    if st.button("Audio Only (MP3)", use_container_width=True):
        st.session_state.preset_format = "audio_mp3"
        st.success("Preset: Audio MP3")
    if st.button("📺 Best Video", use_container_width=True):
        st.session_state.preset_format = "best_video"
        st.success("Preset: Best Video")
    if st.button("💾 720p Video", use_container_width=True):
        st.session_state.preset_format = "720p_video"
        st.success("Preset: 720p Video")
    st.markdown("---")
    st.markdown("#### 🕒 Recent URLs")
    if st.session_state.download_history:
        recent_urls = list(set([entry['url'] for entry in st.session_state.download_history[:5]]))
        for i, recent_url in enumerate(recent_urls[:3]):
            if st.button(f"🔗 {recent_url[:20]}...", use_container_width=True, key=f"recent_url_btn_{i}_{recent_url}"):
                st.session_state.quick_url = recent_url
                st.success("URL loaded!")
    else:
        st.info("No recent URLs")
    st.markdown("---")
    st.markdown("#### 💡 Support")
    st.markdown("""
    **Supported Platforms:**
    - YouTube, YouTube Music
    - Twitch, Twitter/X
    - Instagram, TikTok
    - Facebook, Vimeo
    - And 1000+ more!
    """)
    if st.button("View All Platforms", use_container_width=True):
        try:
            result = subprocess.run(['yt-dlp', '--list-extractors'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                extractors = result.stdout.split('\n')[:50]
                st.info(f"Supports {len(extractors)}+ platforms")
        except:
            st.info("Run `yt-dlp --list-extractors` to see all platforms")


st.markdown("---")
st.markdown(
    '<div style="text-align: center; padding: 2rem 0; color: #666666; font-size: 0.875rem;">'
        'Powered by <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" style="color: #999999;">yt-dlp</a> · '
        'Built with <a href="https://streamlit.io" target="_blank" style="color: #999999;">Streamlit</a> · '
        'Made by <a href="https://linktr.ee/sahaj33" target="_blank" style="color: #999999;">Sahaj33</a>'
    '</div>',
    unsafe_allow_html=True
)

def show_dependency_warning():
    if not deps['yt-dlp']:
        st.error("""
        **yt-dlp is not installed!**
        Install it using:
        ```bash
        pip install yt-dlp
        ```
        Then refresh this page.
        """)
        st.stop()

show_dependency_warning()

def cleanup_temp_files():
    try:
        temp_base = tempfile.gettempdir()
        for item in os.listdir(temp_base):
            if item.startswith("ytdlp_"):
                item_path = os.path.join(temp_base, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
    except:
        pass

cleanup_temp_files()

def init_session_state():
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.download_count = 0
        st.session_state.total_downloaded_size = 0
    
    # Simple mobile detection based on screen width
    # This is a basic approach - in a real app you'd use proper user agent detection
    if 'is_mobile' not in st.session_state:
        st.session_state.is_mobile = False

init_session_state()

# Mobile detection toggle for testing (hidden in production)
with st.expander("🔧 Developer Options", expanded=False):
    st.session_state.is_mobile = st.checkbox("Force Mobile Layout", value=st.session_state.get('is_mobile', False))

if st.session_state.get('show_performance', False):
    with st.expander("📊 Performance Stats"):
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        with perf_col1:
            st.metric("Downloads Today", st.session_state.download_count)
        with perf_col2:
            size_mb = st.session_state.total_downloaded_size / (1024 * 1024)
            st.metric("Data Downloaded", f"{size_mb:.1f} MB")
        with perf_col3:
            uptime = time.time() - st.session_state.get('start_time', time.time())
            st.metric("Session Time", f"{int(uptime//60)}m {int(uptime%60)}s")

with st.expander("⌨️ Keyboard Shortcuts"):
    st.markdown("""
    **Available Shortcuts:**
    - `Ctrl + Enter` - Start download
    - `Ctrl + Shift + R` - Refresh page
    - `Tab` - Navigate tabs
    - `Escape` - Close modals
    
    **Browser Shortcuts:**
    - `Ctrl + S` - Save page
    - `F5` - Refresh
    - `F11` - Fullscreen
    """)

with st.expander("List of 1000+ Supported Platforms"):
    st.markdown("""
    https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
    """)

st.markdown("""
<div style="position: fixed; bottom: 10px; left: 10px; background: rgba(0, 0, 0, 0.7); padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; color: #888;">
    v2.6.0 | Mobile Responsive
</div>
""", unsafe_allow_html=True)

st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.querySelector('input[placeholder*="youtube"]');
    if (urlInput) urlInput.focus();
    
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                     window.innerWidth <= 768;
    
    // Send mobile detection to Streamlit
    if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: isMobile
        }, '*');
    }
});
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        const fetchButton = document.querySelector('button:contains("Fetch Info")');
        if (fetchButton) fetchButton.click();
    }
});
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        e.preventDefault();
    }
});

// Handle window resize for responsive design
window.addEventListener('resize', function() {
    const isMobile = window.innerWidth <= 768;
    if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: isMobile
        }, '*');
    }
});
</script>
""", unsafe_allow_html=True)


