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
import threading
import queue
import platform
import sys
import zipfile

import stat, tarfile

def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return  # already available
    # URL to a Linux static build (adjust for your platform)
    url = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-release-amd64-static.tar.xz"
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()

    tmp = tempfile.mkdtemp()
    archive = os.path.join(tmp, "ffmpeg.tar.xz")
    with open(archive, "wb") as f:
        for chunk in r.iter_content(1024*1024):
            f.write(chunk)

    with tarfile.open(archive) as tar:
        # extract only ffmpeg & ffprobe
        members = [m for m in tar.getmembers() if m.name.endswith(("ffmpeg","ffprobe"))]
        tar.extractall(path=tmp, members=members)

    bin_dir = tmp  # binaries live directly under tmp/
    # ensure executable
    for name in ("ffmpeg","ffprobe"):
        path = os.path.join(bin_dir, name)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH","")

# call this at top of app.py
ensure_ffmpeg()

def cleanup_temp_dir_robust(temp_dir):
    """Safely clean up a temporary directory and its contents."""
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


st.set_page_config(
    layout="wide", 
    page_title="YT-DLP Downloader", 
    page_icon="🎬",
    initial_sidebar_state="collapsed"
)

# --- Enhanced Custom CSS ---
st.markdown("""
<style>
    /* Main App Styling */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #ffffff;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Header */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #00d4aa, #00a8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 0 0 20px rgba(0, 212, 170, 0.3);
    }
    
    .sub-header {
        text-align: center;
        color: #a0a0a0;
        font-size: 1.2rem;
        margin-bottom: 3rem;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a1a2e;
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 0px 24px;
        background-color: #2c2c54;
        border-radius: 8px;
        color: #ffffff;
        font-weight: 600;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #40407a;
        border-color: #00d4aa;
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4aa, #00a8ff) !important;
        color: #000000 !important;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(0, 212, 170, 0.4);
    }
    
    /* Card Styling */
    .info-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .status-card {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(0, 168, 255, 0.1));
        border: 1px solid rgba(0, 212, 170, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .error-card {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 69, 69, 0.1));
        border: 1px solid rgba(255, 107, 107, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: #ffffff;
        backdrop-filter: blur(5px);
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus {
        border-color: #00d4aa;
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #00d4aa, #00a8ff);
        color: #000000;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 212, 170, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 212, 170, 0.4);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d4aa, #00a8ff);
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background-color: rgba(0, 212, 170, 0.1);
        border: 1px solid #00d4aa;
        color: #00d4aa;
    }
    
    .stError {
        background-color: rgba(255, 107, 107, 0.1);
        border: 1px solid #ff6b6b;
        color: #ff6b6b;
    }
    
    .stWarning {
        background-color: rgba(255, 206, 84, 0.1);
        border: 1px solid #ffce54;
        color: #ffce54;
    }
    
    .stInfo {
        background-color: rgba(0, 168, 255, 0.1);
        border: 1px solid #00a8ff;
        color: #00a8ff;
    }
    
    /* Quick Action Buttons */
    .quick-action {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action:hover {
        background: rgba(0, 212, 170, 0.2);
        border-color: #00d4aa;
        transform: translateY(-2px);
    }
    
    /* Dependency Status */
    .dep-available {
        background: linear-gradient(135deg, #00d4aa, #26de81);
        color: #000000;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .dep-missing {
        background: linear-gradient(135deg, #ff6b6b, #ff5252);
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Video Info Display */
    .video-info {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .video-title {
        font-size: 1.4rem;
        font-weight: bold;
        color: #00d4aa;
        margin-bottom: 0.5rem;
    }
    
    /* Loading Animation */
    .loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(0, 212, 170, 0.3);
        border-radius: 50%;
        border-top-color: #00d4aa;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# --- Dependency Check Functions ---
@st.cache_data
def check_dependencies():
    """Check if required dependencies are available"""
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
    """Validate if URL is properly formatted"""
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
    """Parse yt-dlp progress line"""
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
    """Categorize common yt-dlp errors"""
    error_lower = error_message.lower()
    
    if 'network' in error_lower or 'connection' in error_lower:
        return "Network Error", "Check your internet connection and try again."
    elif 'private' in error_lower or 'unavailable' in error_lower:
        return "Content Unavailable", "The video may be private, deleted, or geo-restricted."
    elif 'format' in error_lower and 'not available' in error_lower:
        return "Format Error", "Try a different quality setting."
    elif 'ffmpeg' in error_lower:
        return "FFmpeg Error", "FFmpeg is required for this operation."
    else:
        return "Unknown Error", "An unexpected error occurred."

# --- Initialize Session State ---
if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'is_playlist_url' not in st.session_state:
    st.session_state.is_playlist_url = False
if 'download_history' not in st.session_state:
    st.session_state.download_history = []

# --- Header ---
st.markdown('<h1 class="main-header">🎬 YT-DLP Downloader</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Download videos and audio from 1000+ Supoorted Platforms</p>', unsafe_allow_html=True)

# --- Check Dependencies ---
deps = check_dependencies()

# Create main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Download", 
    "⚙️ Advanced", 
    "📊 Monitor", 
    "📚 History", 
    "🔧 System"
])

# --- TAB 1: MAIN DOWNLOAD ---
with tab1:
    # Dependency Status (Compact)
    if not all(deps.values()):
        st.warning("⚠️ Some dependencies are missing. Check the System tab for installation instructions.")

    # URL Input Section
    st.markdown("### 🔗 Enter URL")

    col1, col2 = st.columns([4, 1])
    with col1:
        url = st.text_input(
            "Video URL",
            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            help="Paste any video, playlist, or channel URL from supported platforms",
            label_visibility="collapsed"
        )
    with col2:
        fetch_clicked = st.button("🔍 Fetch Info", use_container_width=True, disabled=not url)

    # URL Validation
    if url:
        is_valid, message = validate_url(url)
        if is_valid:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")

    # Fetch Video Info
    if fetch_clicked and url:
        with st.spinner("Fetching video information..."):
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    st.session_state.video_info = info
                    st.session_state.is_playlist_url = info.get('_type') == 'playlist' or 'entries' in info

                st.success("✅ Information fetched successfully!")
                st.rerun()

            except Exception as e:
                error_type, error_solution = categorize_error(str(e))
                st.error(f"❌ {error_type}: {error_solution}")

    # Display Video Info
    if st.session_state.video_info:
        info = st.session_state.video_info
        
        st.markdown("### 📺 Video Information")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if info.get('thumbnail'):
                st.image(info['thumbnail'], use_container_width=True)
        
        with col2:
            # st.markdown(f'<div class="video-info">', unsafe_allow_html=True) #
            st.markdown(f'<div class="video-title">{info.get("title", "N/A")}</div>', unsafe_allow_html=True)
            
            if st.session_state.is_playlist_url:
                entries_count = len(info.get('entries', []))
                st.markdown(f"**📋 Type:** Playlist ({entries_count:,} videos)")
            else:
                st.markdown(f"**🎥 Type:** Single Video")
                st.markdown(f"**⏱️ Duration:** {info.get('duration_string', 'N/A')}")
                if info.get('view_count'):
                    st.markdown(f"**👀 Views:** {info['view_count']:,}")
            
            st.markdown(f"**👤 Uploader:** {info.get('uploader', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Download Options
        st.markdown("### ⚙️ Download Options")
        
        option_col1, option_col2, option_col3 = st.columns(3)
        
        with option_col1:
            download_type = st.selectbox(
                "Download Type",
                ["Video + Audio", "Audio Only", "Video Only"],
                help="Choose what to download"
            )
        
        with option_col2:
            if download_type != "Audio Only":
                quality = st.selectbox(
                    "Video Quality",
                    ["Best Available", "1080p", "720p", "480p", "360p"],
                    help="Higher quality = larger file size"
                )
            else:
                quality = "Best Available"
        
        with option_col3:
            if download_type == "Audio Only":
                audio_format = st.selectbox(
                    "Audio Format",
                    ["mp3", "aac", "m4a", "opus", "flac"],
                    help="MP3 is most compatible"
                )
            else:
                audio_format = "mp3"
        
        # Additional Options
        with st.expander("➕ Additional Options"):
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
        
        # Download Button
        st.markdown("---")
        
        download_col1, download_col2, download_col3 = st.columns([2, 2, 2])
        
        with download_col2:
            if st.button("🚀 Start Download", type="primary", use_container_width=True):
                if not deps['yt-dlp']:
                    st.error("❌ yt-dlp is required but not installed!")
                else:
                    # Start download process
                    st.session_state.downloading = True
                    st.rerun()
    
    # Download Process
    if st.session_state.get('downloading', False):
        st.markdown("### 📥 Downloading...")

        # Progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.empty()

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="ytdlp_")

        try:
            # Build command
            cmd = ["yt-dlp", "-o", os.path.join(temp_dir, "%(title)s.%(ext)s")]

            # Add format options
            if download_type == "Audio Only":
                cmd.extend(["-x", "--audio-format", audio_format])
            elif download_type == "Video Only":
                cmd.extend(["-f", "bestvideo"])
            else:
                if quality != "Best Available":
                    quality_map = {
                        "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                        "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                        "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                        "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]"
                    }
                    cmd.extend(["-f", quality_map.get(quality, "best")])

            # Add additional options
            if download_subs:
                cmd.extend(["--write-sub", "--sub-langs", "en"])
            if download_thumbnail:
                cmd.append("--write-thumbnail")
            if embed_metadata and deps['ffmpeg']:
                cmd.append("--add-metadata")

            # File size limit
            if max_file_size != "No Limit":
                size_map = {"100MB": "100m", "500MB": "500m", "1GB": "1000m", "2GB": "2000m"}
                cmd.extend(["--max-filesize", size_map[max_file_size]])

            # Playlist options
            if st.session_state.is_playlist_url:
                if playlist_start > 1:
                    cmd.extend(["--playlist-start", str(playlist_start)])
                if playlist_end > 0:
                    cmd.extend(["--playlist-end", str(playlist_end)])

            cmd.append(url)

            # Execute download
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                universal_newlines=True
            )

            logs = []
            current_percent = 0

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break

                if output:
                    line = output.strip()
                    logs.append(line)

                    # Parse progress
                    progress_info = parse_progress(line)
                    if progress_info:
                        if 'percent' in progress_info:
                            current_percent = progress_info['percent']
                            progress_bar.progress(current_percent / 100)

                            status = f"Progress: {current_percent:.1f}%"
                            if 'speed' in progress_info:
                                status += f" | Speed: {progress_info['speed']}"
                            if 'eta' in progress_info:
                                status += f" | ETA: {progress_info['eta']}"

                            status_text.text(status)

                    # Show recent logs
                    recent_logs = logs[-5:] if len(logs) > 5 else logs
                    log_container.text_area("Download Log:", "\n".join(recent_logs), height=100, disabled=True)

            # Check result
            return_code = process.poll()

            if return_code == 0:
                progress_bar.progress(1.0)
                status_text.text("✅ Download completed successfully!")

                # List downloaded files
                downloaded_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        downloaded_files.append((file, file_path, file_size))

                if downloaded_files:
                    st.success(f"🎉 Downloaded {len(downloaded_files)} file(s)!")

                    for filename, file_path, size in downloaded_files:
                        size_mb = size / (1024 * 1024)

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"📁 {filename} ({size_mb:.1f} MB)")
                        with col2:
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    "💾 Download",
                                    data=f.read(),
                                    file_name=filename,
                                    key=f"dl_{filename}"
                                )

                    # Add to history
                    st.session_state.download_history.insert(0, {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "url": url[:50] + "..." if len(url) > 50 else url,
                        "title": st.session_state.video_info.get('title', 'Unknown')[:30] + "...",
                        "files": len(downloaded_files),
                        "status": "Success"
                    })

            else:
                st.error("❌ Download failed!")
                if logs:
                    error_type, error_solution = categorize_error(logs[-1])
                    st.markdown(f"**Error:** {error_type}")
                    st.markdown(f"**Solution:** {error_solution}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

        finally:
            # Cleanup
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

            st.session_state.downloading = False

            if st.button("🔄 Download Another"):
                st.rerun()

# --- TAB 2: ADVANCED OPTIONS ---
with tab2:
    st.markdown("### 🔧 Advanced Settings")

    # --- Automatic Cleanup Logic (Runs on session start/rerun if not active) ---
    if st.session_state.get("batch_temp_dir") and not st.session_state.get("batch_download_trigger", False):
        st.info("Checking for leftover temporary files from a previous session...")
        if cleanup_temp_dir_robust(st.session_state.batch_temp_dir):
            st.session_state.batch_temp_dir = None
            st.success("Cleaned up old temporary files.")
        else:
            st.warning("Could not clean up all old temporary files. Some might remain until the server restarts.")

    col1, col2 = st.columns(2)

    with col2:
        st.markdown("#### 📁 Custom & Post-processing Settings")

        custom_format = st.text_input(
            "Custom Format String (`-f`):",
            help="Advanced yt-dlp format selector (e.g., 'bv*+ba/b'). Overrides quality/format selections."
        )

        filename_template = st.text_input(
            "Filename Template (`-o`):",
            value="%(title)s.%(ext)s",
            help="Customize output filename using yt-dlp's template variables."
        )

        st.checkbox("Embed Subtitles (if available)", key="advanced_embed_subs", value=False)
        st.checkbox("Embed Thumbnail (if available)", key="advanced_embed_thumb", value=False)

        st.markdown("#### 🌐 Network Settings")

        use_proxy = st.checkbox("Use Proxy (`--proxy`)")
        proxy_url = ""
        if use_proxy:
            proxy_url = st.text_input("Proxy URL:", placeholder="http://proxy:port or socks5://user:pass@host:port")

        rate_limit = st.slider("Rate Limit (KB/s) (`--limit-rate`)", 0, 10000, 0, step=100, help="0 = no limit")


    with col1:
        st.markdown("#### 🎯 Batch Download")
        batch_urls = st.text_area(
            "Multiple URLs (one per line):",
            height=200,
            help="Enter multiple URLs for batch downloading. Each URL will be processed sequentially."
        )

        urls_list = [u.strip() for u in batch_urls.split('\n') if u.strip()]

        if urls_list:
            st.info(f"Found {len(urls_list)} URLs for batch download.")

            # Only show button if there are URLs and no download is active
            if not st.session_state.get("batch_download_trigger", False):
                if st.button("🚀 Start Batch Download", key="start_batch_btn"):
                    st.session_state.batch_download_trigger = True
                    st.session_state.batch_urls_list = urls_list
                    # Create a single temporary directory for the entire batch
                    st.session_state.batch_temp_dir = tempfile.mkdtemp(prefix="ytdlp_batch_")
                    st.rerun() # Rerun to trigger the download logic
            else:
                st.info("Batch download in progress...")

            # Run batch download if triggered
            if st.session_state.get("batch_download_trigger", False):
                urls_to_process = st.session_state.get("batch_urls_list", [])
                batch_overall_temp_dir = st.session_state.get("batch_temp_dir")

                total_urls = len(urls_to_process)
                success_count = 0
                fail_count = 0
                batch_logs = []
                batch_downloaded_files_info = [] # Store (title, list of (file, path, size))

                st.markdown("---")
                st.markdown("### 🗂️ Batch Download Progress")

                # Progress bar for overall batch
                progress_text_placeholder = st.empty()
                progress_bar_placeholder = st.progress(0)

                for idx, url in enumerate(urls_to_process, 1):
                    current_progress = (idx - 1) / total_urls
                    progress_bar_placeholder.progress(current_progress)
                    progress_text_placeholder.text(f"Processing URL {idx}/{total_urls}: {url[:70]}...")

                    is_valid, msg = validate_url(url)

                    if not is_valid:
                        st.error(f"❌ Skipping invalid URL [{idx}/{total_urls}]: {url} ({msg})")
                        fail_count += 1
                        st.session_state.download_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": url[:50] + "..." if len(url) > 50 else url,
                            "title": "N/A (Invalid URL)",
                            "files": 0,
                            "status": "Failed"
                        })
                        continue

                    # Build yt-dlp command
                    cmd_list = ["yt-dlp"]

                    # Convert Streamlit options to yt-dlp CLI arguments
                    if custom_format:
                        cmd_list.extend(["-f", custom_format])

                    if use_proxy and proxy_url:
                        cmd_list.extend(["--proxy", proxy_url])

                    if rate_limit > 0:
                        cmd_list.extend(["--limit-rate", f"{rate_limit}K"]) # yt-dlp uses K for KB/s

                    if filename_template:
                        cmd_list.extend(["-o", os.path.join(batch_overall_temp_dir, filename_template)])
                    else:
                        cmd_list.extend(["-o", os.path.join(batch_overall_temp_dir, "%(title)s.%(ext)s")])

                    if st.session_state.advanced_embed_subs:
                        cmd_list.append("--embed-subs")
                    if st.session_state.advanced_embed_thumb:
                        cmd_list.append("--embed-thumbnail")

                    cmd_list.append(url)

                    try:
                        process = subprocess.run(
                            cmd_list,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            timeout=900
                        )
                        output_stdout = process.stdout
                        output_stderr = process.stderr
                        full_output = output_stdout + output_stderr

                        # Attempt to extract title/filename from yt-dlp output
                        title_match = re.search(r'\[download\] Destination:\s*(.+)', full_output)
                        title = title_match.group(1).split(os.sep)[-1] if title_match else url[:60] + "..."

                        if process.returncode == 0:
                            st.success(f"✅ [{idx}/{total_urls}] Downloaded: {title}")
                            success_count += 1
                            st.session_state.download_history.insert(0, {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "url": url[:50] + "..." if len(url) > 50 else url,
                                "title": title,
                                "files": "N/A (Batch)",
                                "status": "Success"
                            })
                        else:
                            error_message = output_stderr if output_stderr else full_output[-500:]
                            st.error(f"❌ [{idx}/{total_urls}] Failed: {title}\n\n```\n{error_message}\n```")
                            fail_count += 1
                            st.session_state.download_history.insert(0, {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "url": url[:50] + "..." if len(url) > 50 else url,
                                "title": title,
                                "files": 0,
                                "status": "Failed"
                            })
                        batch_logs.append(full_output)
                    except subprocess.TimeoutExpired:
                        st.error(f"❌ [{idx}/{total_urls}] Timeout: Download for {url} took too long.")
                        fail_count += 1
                        batch_logs.append(f"Timeout occurred for URL: {url}")
                        st.session_state.download_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": url[:50] + "..." if len(url) > 50 else url,
                            "title": "N/A (Timeout)",
                            "files": 0,
                            "status": "Failed"
                        })
                    except Exception as e:
                        st.error(f"❌ [{idx}/{total_urls}] Error processing {url}: {str(e)}")
                        fail_count += 1
                        batch_logs.append(f"General error for URL {url}: {str(e)}")
                        st.session_state.download_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "url": url[:50] + "..." if len(url) > 50 else url,
                            "title": "N/A (Error)",
                            "files": 0,
                            "status": "Failed"
                        })

                progress_bar_placeholder.progress(1.0)
                progress_text_placeholder.text(f"Batch processing complete! ✅ {success_count} succeeded, ❌ {fail_count} failed out of {total_urls}.")

                # --- Show download buttons for all files from the batch temp dir ---
                downloadable_files_info = []
                if os.path.exists(batch_overall_temp_dir):
                    for root, dirs, files in os.walk(batch_overall_temp_dir):
                        for file_name in files:
                            file_path = os.path.join(root, file_name)
                            try:
                                file_size = os.path.getsize(file_path)
                                downloadable_files_info.append((file_name, file_path, file_size))
                            except OSError:
                                pass

                if downloadable_files_info:
                    st.markdown("### 💾 Download Your Batch Files")
                    for idx, (file, file_path, file_size) in enumerate(downloadable_files_info, 1):
                        size_mb = file_size / (1024 * 1024)
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"💾 Download {file} ({size_mb:.1f} MB)",
                                data=f.read(),
                                file_name=file,
                                key=f"batch_dl_{idx}_{file_path.replace('.', '').replace('/', '').replace('\\', '')}"
                            )
                else:
                    st.info("No files were successfully downloaded in this batch.")


                with st.expander("Show Detailed Batch Logs"):
                    for i, log in enumerate(batch_logs):
                        st.text_area(f"Log for item #{i+1}", log, height=150, key=f"batch_log_{i}")

                # --- Manual Cleanup Button ---
                if st.button("Clean up downloaded files from server", help="This will remove the temporary files from the server after you've downloaded them.", key="cleanup_batch_btn_manual"):
                    if cleanup_temp_dir_robust(batch_overall_temp_dir):
                        st.success("Temporary batch files cleaned up!")
                    else:
                        st.error("Failed to clean up temporary batch files. Please try again or check server logs.")
                    st.session_state.batch_temp_dir = None

                # Reset trigger and URLs list so it doesn't rerun a finished batch
                st.session_state.batch_download_trigger = False
                st.session_state.batch_urls_list = []
    
    

# --- TAB 3: MONITOR ---
with tab3:
    st.markdown("### 📊 System Monitor")
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # CPU usage placeholder
        st.metric("CPU Usage", "Calculating...", help="Current CPU usage")
    
    with col2:
        # Memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            st.metric("Memory Usage", f"{memory.percent:.1f}%", f"{memory.available//1024//1024} MB free")
        except:
            st.metric("Memory Usage", "N/A")
    
    with col3:
        # Disk space
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
        # Network speed test
        if st.button("🌐 Test Speed"):
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
    
    # Active downloads section
    st.markdown("---")
    st.markdown("### 📥 Active Downloads")
    
    if st.session_state.get('downloading', False):
        st.info("🔄 Download in progress...")
    else:
        st.info("No active downloads")

# --- TAB 4: HISTORY ---
with tab4:
    st.markdown("### 📚 Download History")
    
    if st.session_state.download_history:
        # Display history as cards
        for i, entry in enumerate(st.session_state.download_history[:10]):  # Show last 10
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
                        st.markdown(
                            """
                            <style>
                                .centered-success {
                                    text-align: center;
                                    color: #a7d97b; /* Light green from your dark theme */
                                    font-weight: bold;
                                }
                            </style>
                            <p class="centered-success">✅ Success</p>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        # You can also apply centering to the error if you want consistency
                        st.markdown(
                            """
                            <style>
                                .centered-error {
                                    text-align: center;
                                    color: #ff7b72; /* Light red from your dark theme */
                                    font-weight: bold;
                                }
                            </style>
                            <p class="centered-error">❌ Failed</p>
                            """,
                            unsafe_allow_html=True
                        )
                
                if i < len(st.session_state.download_history) - 1:
                    st.divider()
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.download_history = []
            st.success("History cleared!")
            st.rerun()
    
    else:
        st.info("📝 No download history yet. Start downloading to see your history here!")

# --- TAB 5: SYSTEM ---
with tab5:
    st.markdown("### 🔧 System Information")
    
    # Dependency status
    st.markdown("#### 📦 Dependencies")
    
    dep_col1, dep_col2, dep_col3 = st.columns(3)
    
    with dep_col1:
        st.markdown("**yt-dlp**")
        if deps['yt-dlp']:
            st.markdown('<span class="dep-available">✅ Installed</span>', unsafe_allow_html=True)
            st.caption(deps['yt-dlp'][:50] + "...")
        else:
            st.markdown('<span class="dep-missing">❌ Missing</span>', unsafe_allow_html=True)
            st.caption("Required for downloading")
    
    with dep_col2:
        st.markdown("**FFmpeg**")
        if deps['ffmpeg']:
            st.markdown('<span class="dep-available">✅ Installed</span>', unsafe_allow_html=True)
            st.caption("Video processing available")
        else:
            st.markdown('<span class="dep-missing">❌ Missing</span>', unsafe_allow_html=True)
            st.caption("Optional for advanced features")
    
    with dep_col3:
        st.markdown("**FFprobe**")
        if deps['ffprobe']:
            st.markdown('<span class="dep-available">✅ Installed</span>', unsafe_allow_html=True)
            st.caption("Media analysis available")
        else:
            st.markdown('<span class="dep-missing">❌ Missing</span>', unsafe_allow_html=True)
            st.caption("Optional for media info")
    
    # Installation instructions
    if not all(deps.values()):
        st.markdown("---")
        st.markdown("#### 🛠️ Installation Instructions")
        
        system = platform.system().lower()
        
        install_col1, install_col2 = st.columns(2)
        
        with install_col1:
            st.markdown("**Install yt-dlp:**")
            if system == "windows":
                st.code("pip install yt-dlp", language="bash")
                st.markdown("Or download from [GitHub Releases](https://github.com/yt-dlp/yt-dlp/releases)")
            elif system == "darwin":  # macOS
                st.code("pip install yt-dlp\n# or\nbrew install yt-dlp", language="bash")
            else:  # Linux
                st.code("pip install yt-dlp\n# or\nsudo apt install yt-dlp", language="bash")
        
        with install_col2:
            st.markdown("**Install FFmpeg:**")
            if system == "windows":
                st.code("winget install FFmpeg", language="bash")
                st.markdown("Or download from [FFmpeg.org](https://ffmpeg.org/download.html)")
            elif system == "darwin":  # macOS
                st.code("brew install ffmpeg", language="bash")
            else:  # Linux
                st.code("sudo apt install ffmpeg  # Ubuntu/Debian\nsudo dnf install ffmpeg  # Fedora", language="bash")
    
    # System details
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
        
        # Python path
        st.markdown(f"**Python Path:** `{sys.executable[:50]}...`")

# --- Quick Actions Sidebar ---
with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    
    # Quick format presets
    st.markdown("#### 📱 Format Presets")
    
    if st.button("🎵 Audio Only (MP3)", use_container_width=True):
        st.session_state.preset_format = "audio_mp3"
        st.success("Preset: Audio MP3")
    
    if st.button("📺 Best Video", use_container_width=True):
        st.session_state.preset_format = "best_video"
        st.success("Preset: Best Video")
    
    if st.button("💾 720p Video", use_container_width=True):
        st.session_state.preset_format = "720p_video"
        st.success("Preset: 720p Video")
    
    st.markdown("---")
    
    # Recent URLs
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
    
    # Support section
    st.markdown("#### 💡 Support")
    
    st.markdown("""
    **Supported Platforms:**
    - YouTube, YouTube Music
    - Twitch, Twitter/X
    - Instagram, TikTok
    - Facebook, Vimeo
    - And 1000+ more!
    """)
    
    if st.button("📋 View All Platforms", use_container_width=True):
        try:
            result = subprocess.run(['yt-dlp', '--list-extractors'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                extractors = result.stdout.split('\n')[:50]  # Show first 50
                st.info(f"Supports {len(extractors)}+ platforms")
        except:
            st.info("Run `yt-dlp --list-extractors` to see all platforms")

# --- Floating Action Buttons (using containers) ---
if url or st.session_state.get('quick_url'):
    st.markdown("""
    <style>
    .floating-actions {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .floating-btn {
        background: linear-gradient(135deg, #00d4aa, #00a8ff);
        color: #000000;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        font-weight: bold;
        box-shadow: 0 4px 20px rgba(0, 212, 170, 0.4);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .floating-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 170, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Footer with Tips ---
st.markdown("---")

st.markdown("### 💡 Pro Tips:")

# Create columns for better layout
tip_col1, tip_col2, tip_col3 = st.columns(3)

with tip_col1:
    st.markdown("#### 🎯 For Best Results:")
    st.markdown("""
    - Use wired internet for large downloads
    - Test with single videos before downloading playlists  
    - Check available storage space
    """)

with tip_col2:
    st.markdown("#### 🚀 Speed Optimization:")
    st.markdown("""
    - Choose appropriate quality (720p recommended)
    - Close other bandwidth-heavy apps
    - Use audio-only for music
    """)

with tip_col3:
    st.markdown("#### 🛠️ Troubleshooting:")
    st.markdown("""
    - Refresh page if downloads fail
    - Try different quality settings
    - Check URL accessibility in browser
    """)

st.markdown("---")

# Footer with proper Streamlit styling
st.markdown(
    '<div style="text-align: center; padding: 2rem 0; border-top: 1px solid #3d3d5c; margin-top: 3rem;">'
        '<div style="background: linear-gradient(90deg, #00d4aa, #00a8ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">'
        '    Advanced YT-DLP Downloader'
        '</div>'
        
        '<div style="color: #a0a0a0; margin-bottom: 1rem;">'
        '    Powered by <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" style="color: #00a8ff;">yt-dlp</a> | '
        '    Built with <a href="https://streamlit.io" target="_blank" style="color: #00a8ff;">Streamlit</a><br>'
        '    Made by <a href="https://linktr.ee/sahaj33" target="_blank" style="color: #00a8ff;">Sahaj33</a>'
        '</div>'
    '</div>'
    , unsafe_allow_html=True)

# Feature highlights using Streamlit columns instead of raw HTML
feat_col1, feat_col2, feat_col3 = st.columns(3)

with feat_col1:
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; text-align: center; margin: 0.5rem 0;">
        <span style="color: #00d4aa;">🎬</span> 1000+ Supported Sites
    </div>
    """, unsafe_allow_html=True)

with feat_col2:
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; text-align: center; margin: 0.5rem 0;">
        <span style="color: #00a8ff;">⚡</span> High-Speed Downloads
    </div>
    """, unsafe_allow_html=True)

with feat_col3:
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.1); padding: 0.5rem 1rem; border-radius: 20px; text-align: center; margin: 0.5rem 0;">
        <span style="color: #26de81;">🔧</span> Advanced Features
    </div>
    """, unsafe_allow_html=True)


# --- Error Handling for Missing Dependencies ---
def show_dependency_warning():
    """Show warning if critical dependencies are missing"""
    if not deps['yt-dlp']:
        st.error("""
        ❌ **yt-dlp is not installed!**
        
        This app requires yt-dlp to function. Please install it using:
        ```bash
        pip install yt-dlp
        ```
        
        Then refresh this page.
        """)
        st.stop()

# Check dependencies on app load
show_dependency_warning()

# --- Auto-clear temporary files on app restart ---
def cleanup_temp_files():
    """Clean up any leftover temporary files"""
    try:
        temp_base = tempfile.gettempdir()
        for item in os.listdir(temp_base):
            if item.startswith("ytdlp_"):
                item_path = os.path.join(temp_base, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
    except:
        pass

# Run cleanup
cleanup_temp_files()

# --- Session state management for better UX ---
def init_session_state():
    """Initialize session state variables"""
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.download_count = 0
        st.session_state.total_downloaded_size = 0

init_session_state()

# --- Performance monitoring ---
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

# --- Keyboard shortcuts info ---
with st.expander("⌨️ Keyboard Shortcuts"):
    st.markdown("""
    **Available Shortcuts:**
    - `Ctrl + Enter` - Start download (when URL is entered)
    - `Ctrl + Shift + R` - Refresh page
    - `Tab` - Navigate between tabs
    - `Escape` - Close modals/expanders
    
    **Browser Shortcuts:**
    - `Ctrl + S` - Save current page
    - `F5` - Refresh page
    - `F11` - Fullscreen mode
    """)

# --- Keyboard shortcuts info ---
with st.expander("List of 1000+ Supported Platforms"):
    st.markdown("""
https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
    """)

# --- Version information ---
st.markdown("""
<div style="position: fixed; bottom: 10px; left: 10px; background: rgba(0, 0, 0, 0.7); padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; color: #888;">
    v2.5.0 | Enhanced UI
</div>
""", unsafe_allow_html=True)

# --- Advanced JavaScript for better UX ---
st.markdown("""
<script>
// Auto-focus URL input when page loads
document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.querySelector('input[placeholder*="youtube"]');
    if (urlInput) {
        urlInput.focus();
    }
});

// Handle Enter key in URL input
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        const fetchButton = document.querySelector('button:contains("Fetch Info")');
        if (fetchButton) {
            fetchButton.click();
        }
    }
});

// Prevent form submission on Enter in text inputs
document.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
        e.preventDefault();
    }
});
</script>
""", unsafe_allow_html=True)

# --- Mobile responsiveness ---
st.markdown("""
<style>
@media (max-width: 768px) {
    .main-header {
        font-size: 2rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0px 12px !important;
        font-size: 0.9rem !important;
    }
    
    .video-info {
        padding: 1rem !important;
    }
    
    .floating-actions {
        bottom: 80px !important;
        right: 10px !important;
    }
}

@media (max-width: 480px) {
    .main-header {
        font-size: 1.5rem !important;
    }
    
    .sub-header {
        font-size: 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# --- End of application ---
