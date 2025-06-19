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
        return "Unknown Error", "Check the logs for more details."

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
            "",
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Batch Download")
        batch_urls = st.text_area(
            "Multiple URLs (one per line):",
            height=150,
            help="Enter multiple URLs for batch downloading"
        )
        
        if batch_urls:
            urls_list = [url.strip() for url in batch_urls.split('\n') if url.strip()]
            st.info(f"Found {len(urls_list)} URLs")
            
            if st.button("🚀 Start Batch Download"):
                st.info("Batch download feature coming soon!")
    
    with col2:
        st.markdown("#### 📁 Custom Settings")
        
        custom_format = st.text_input(
            "Custom Format String:",
            help="Advanced yt-dlp format selector"
        )
        
        filename_template = st.text_input(
            "Filename Template:",
            value="%(title)s.%(ext)s",
            help="Customize output filename"
        )
        
        st.markdown("#### 🌐 Network Settings")
        
        use_proxy = st.checkbox("Use Proxy")
        if use_proxy:
            proxy_url = st.text_input("Proxy URL:", placeholder="http://proxy:port")
        
        rate_limit = st.slider("Rate Limit (KB/s)", 0, 10000, 0, help="0 = no limit")

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
        for recent_url in recent_urls[:3]:
            if st.button(f"🔗 {recent_url[:20]}...", use_container_width=True):
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
with st.expander("List of Supported Platforms"):
    st.markdown("""

Below is a list of all extractors that are currently included with yt-dlp.
If a site is not listed here, it might still be supported by yt-dlp's embed extraction or generic extractor.
Not all sites listed here are guaranteed to work; websites are constantly changing and sometimes this breaks yt-dlp's support for them.
The only reliable way to check if a site is supported is to try it.

 - **10play**: [*10play*](## "netrc machine")
 - **10play:season**
 - **17live**
 - **17live:clip**
 - **17live:vod**
 - **1News**: 1news.co.nz article videos
 - **1tv**: Первый канал
 - **20min**
 - **23video**
 - **247sports**: (**Currently broken**)
 - **24tv.ua**
 - **3qsdn**: 3Q SDN
 - **3sat**
 - **4tube**
 - **56.com**
 - **6play**
 - **7plus**
 - **8tracks**
 - **9c9media**
 - **9gag**: 9GAG
 - **9News**
 - **9now.com.au**
 - **abc.net.au**
 - **abc.net.au:iview**
 - **abc.net.au:​iview:showseries**
 - **abcnews**
 - **abcnews:video**
 - **abcotvs**: ABC Owned Television Stations
 - **abcotvs:clips**
 - **AbemaTV**: [*abematv*](## "netrc machine")
 - **AbemaTVTitle**: [*abematv*](## "netrc machine")
 - **AcademicEarth:Course**
 - **acast**
 - **acast:channel**
 - **AcFunBangumi**
 - **AcFunVideo**
 - **ADN**: [*animationdigitalnetwork*](## "netrc machine") Animation Digital Network
 - **ADNSeason**: [*animationdigitalnetwork*](## "netrc machine") Animation Digital Network
 - **AdobeConnect**
 - **adobetv**
 - **adobetv:channel**
 - **adobetv:embed**
 - **adobetv:show**
 - **adobetv:video**
 - **AdultSwim**
 - **aenetworks**: A+E Networks: A&E, Lifetime, History.com, FYI Network and History Vault
 - **aenetworks:collection**
 - **aenetworks:show**
 - **AeonCo**
 - **AirTV**
 - **AitubeKZVideo**
 - **AliExpressLive**
 - **AlJazeera**
 - **Allocine**
 - **Allstar**
 - **AllstarProfile**
 - **AlphaPorno**
 - **Alsace20TV**
 - **Alsace20TVEmbed**
 - **altcensored**
 - **altcensored:channel**
 - **Alura**: [*alura*](## "netrc machine")
 - **AluraCourse**: [*aluracourse*](## "netrc machine")
 - **AmadeusTV**
 - **Amara**
 - **AmazonMiniTV**
 - **amazonminitv:season**: Amazon MiniTV Season, "minitv:season:" prefix
 - **amazonminitv:series**: Amazon MiniTV Series, "minitv:series:" prefix
 - **AmazonReviews**
 - **AmazonStore**
 - **AMCNetworks**
 - **AmericasTestKitchen**
 - **AmericasTestKitchenSeason**
 - **AmHistoryChannel**
 - **AnchorFMEpisode**
 - **anderetijden**: npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl
 - **Angel**
 - **AnimalPlanet**
 - **ant1newsgr:article**: ant1news.gr articles
 - **ant1newsgr:embed**: ant1news.gr embedded videos
 - **antenna:watch**: antenna.gr and ant1news.gr videos
 - **Anvato**
 - **aol.com**: Yahoo screen and movies (**Currently broken**)
 - **APA**
 - **Aparat**
 - **AppleConnect**
 - **AppleDaily**: 臺灣蘋果日報
 - **ApplePodcasts**
 - **appletrailers**
 - **appletrailers:section**
 - **archive.org**: archive.org video and audio
 - **ArcPublishing**
 - **ARD**
 - **ARDMediathek**
 - **ARDMediathekCollection**
 - **Arkena**
 - **Art19**
 - **Art19Show**
 - **arte.sky.it**
 - **ArteTV**
 - **ArteTVCategory**
 - **ArteTVEmbed**
 - **ArteTVPlaylist**
 - **asobichannel**: ASOBI CHANNEL
 - **asobichannel:tag**: ASOBI CHANNEL
 - **AsobiStage**: ASOBISTAGE (アソビステージ)
 - **AtresPlayer**: [*atresplayer*](## "netrc machine")
 - **AtScaleConfEvent**
 - **ATVAt**
 - **AudiMedia**
 - **AudioBoom**
 - **Audiodraft:custom**
 - **Audiodraft:generic**
 - **audiomack**
 - **audiomack:album**
 - **Audius**: Audius.co
 - **audius:artist**: Audius.co profile/artist pages
 - **audius:playlist**: Audius.co playlists
 - **audius:track**: Audius track ID or API link. Prepend with "audius:"
 - **AWAAN**
 - **awaan:live**
 - **awaan:season**
 - **awaan:video**
 - **axs.tv**
 - **AZMedien**: AZ Medien videos
 - **BaiduVideo**: 百度视频
 - **BanBye**
 - **BanByeChannel**
 - **bandaichannel**
 - **Bandcamp**
 - **Bandcamp:album**
 - **Bandcamp:user**
 - **Bandcamp:weekly**
 - **Bandlab**
 - **BandlabPlaylist**
 - **BannedVideo**
 - **bbc**: [*bbc*](## "netrc machine") BBC
 - **bbc.co.uk**: [*bbc*](## "netrc machine") BBC iPlayer
 - **bbc.co.uk:article**: BBC articles
 - **bbc.co.uk:​iplayer:episodes**
 - **bbc.co.uk:​iplayer:group**
 - **bbc.co.uk:playlist**
 - **BBVTV**: [*bbvtv*](## "netrc machine")
 - **BBVTVLive**: [*bbvtv*](## "netrc machine")
 - **BBVTVRecordings**: [*bbvtv*](## "netrc machine")
 - **BeaconTv**
 - **BeatBumpPlaylist**
 - **BeatBumpVideo**
 - **Beatport**
 - **Beeg**
 - **BehindKink**: (**Currently broken**)
 - **Bellator**
 - **BellMedia**
 - **BerufeTV**
 - **Bet**: (**Currently broken**)
 - **bfi:player**: (**Currently broken**)
 - **bfmtv**
 - **bfmtv:article**
 - **bfmtv:live**
 - **bibeltv:live**: BibelTV live program
 - **bibeltv:series**: BibelTV series playlist
 - **bibeltv:video**: BibelTV single video
 - **Bigflix**
 - **Bigo**
 - **Bild**: Bild.de
 - **BiliBili**
 - **Bilibili category extractor**
 - **BilibiliAudio**
 - **BilibiliAudioAlbum**
 - **BiliBiliBangumi**
 - **BiliBiliBangumiMedia**
 - **BiliBiliBangumiSeason**
 - **BilibiliCheese**
 - **BilibiliCheeseSeason**
 - **BilibiliCollectionList**
 - **BiliBiliDynamic**
 - **BilibiliFavoritesList**
 - **BiliBiliPlayer**
 - **BilibiliPlaylist**
 - **BiliBiliSearch**: Bilibili video search; "bilisearch:" prefix
 - **BilibiliSeriesList**
 - **BilibiliSpaceAudio**
 - **BilibiliSpaceVideo**
 - **BilibiliWatchlater**
 - **BiliIntl**: [*biliintl*](## "netrc machine")
 - **biliIntl:series**: [*biliintl*](## "netrc machine")
 - **BiliLive**
 - **BioBioChileTV**
 - **Biography**
 - **BitChute**
 - **BitChuteChannel**
 - **BlackboardCollaborate**
 - **BleacherReport**: (**Currently broken**)
 - **BleacherReportCMS**: (**Currently broken**)
 - **blerp**
 - **blogger.com**
 - **Bloomberg**
 - **Bluesky**
 - **BokeCC**: CC视频
 - **BongaCams**
 - **Boosty**
 - **BostonGlobe**
 - **Box**
 - **BoxCastVideo**
 - **Bpb**: Bundeszentrale für politische Bildung
 - **BR**: Bayerischer Rundfunk (**Currently broken**)
 - **BrainPOP**: [*brainpop*](## "netrc machine")
 - **BrainPOPELL**: [*brainpop*](## "netrc machine")
 - **BrainPOPEsp**: [*brainpop*](## "netrc machine") BrainPOP Español
 - **BrainPOPFr**: [*brainpop*](## "netrc machine") BrainPOP Français
 - **BrainPOPIl**: [*brainpop*](## "netrc machine") BrainPOP Hebrew
 - **BrainPOPJr**: [*brainpop*](## "netrc machine")
 - **BravoTV**
 - **BreitBart**
 - **brightcove:legacy**
 - **brightcove:new**
 - **Brilliantpala:Classes**: [*brilliantpala*](## "netrc machine") VoD on classes.brilliantpala.org
 - **Brilliantpala:Elearn**: [*brilliantpala*](## "netrc machine") VoD on elearn.brilliantpala.org
 - **bt:article**: Bergens Tidende Articles
 - **bt:vestlendingen**: Bergens Tidende - Vestlendingen
 - **Bundesliga**
 - **Bundestag**
 - **BunnyCdn**
 - **BusinessInsider**
 - **BuzzFeed**
 - **BYUtv**: (**Currently broken**)
 - **CaffeineTV**
 - **Callin**
 - **Caltrans**
 - **CAM4**
 - **Camdemy**
 - **CamdemyFolder**
 - **CamFMEpisode**
 - **CamFMShow**
 - **CamModels**
 - **Camsoda**
 - **CamtasiaEmbed**
 - **Canal1**
 - **CanalAlpha**
 - **canalc2.tv**
 - **Canalplus**: mycanal.fr and piwiplus.fr
 - **Canalsurmas**
 - **CaracolTvPlay**: [*caracoltv-play*](## "netrc machine")
 - **cbc.ca**
 - **cbc.ca:player**
 - **cbc.ca:​player:playlist**
 - **CBS**: (**Currently broken**)
 - **CBSLocal**
 - **CBSLocalArticle**
 - **CBSLocalLive**
 - **cbsnews**: CBS News
 - **cbsnews:embed**
 - **cbsnews:live**: CBS News Livestream
 - **cbsnews:livevideo**: CBS News Live Videos
 - **cbssports**: (**Currently broken**)
 - **cbssports:embed**: (**Currently broken**)
 - **CCMA**: 3Cat, TV3 and Catalunya Ràdio
 - **CCTV**: 央视网
 - **CDA**: [*cdapl*](## "netrc machine")
 - **CDAFolder**
 - **Cellebrite**
 - **CeskaTelevize**
 - **CGTN**
 - **CharlieRose**
 - **Chaturbate**
 - **Chilloutzone**
 - **chzzk:live**
 - **chzzk:video**
 - **cielotv.it**
 - **Cinemax**: (**Currently broken**)
 - **CinetecaMilano**
 - **Cineverse**
 - **CineverseDetails**
 - **CiscoLiveSearch**
 - **CiscoLiveSession**
 - **ciscowebex**: Cisco Webex
 - **CJSW**
 - **Clipchamp**
 - **Clippit**
 - **ClipRs**: (**Currently broken**)
 - **ClipYouEmbed**
 - **CloserToTruth**: (**Currently broken**)
 - **CloudflareStream**
 - **CloudyCDN**
 - **Clubic**: (**Currently broken**)
 - **Clyp**
 - **cmt.com**: (**Currently broken**)
 - **CNBCVideo**
 - **CNN**
 - **CNNIndonesia**
 - **ComedyCentral**
 - **ComedyCentralTV**
 - **ConanClassic**: (**Currently broken**)
 - **CondeNast**: Condé Nast media group: Allure, Architectural Digest, Ars Technica, Bon Appétit, Brides, Condé Nast, Condé Nast Traveler, Details, Epicurious, GQ, Glamour, Golf Digest, SELF, Teen Vogue, The New Yorker, Vanity Fair, Vogue, W Magazine, WIRED
 - **CONtv**
 - **CookingChannel**
 - **Corus**
 - **Coub**
 - **CozyTV**
 - **cp24**
 - **cpac**
 - **cpac:playlist**
 - **Cracked**
 - **Crackle**
 - **Craftsy**
 - **CrooksAndLiars**
 - **CrowdBunker**
 - **CrowdBunkerChannel**
 - **Crtvg**
 - **CSpan**: C-SPAN
 - **CSpanCongress**
 - **CtsNews**: 華視新聞
 - **CTV**
 - **CTVNews**
 - **cu.ntv.co.jp**: 日テレ無料TADA!
 - **CultureUnplugged**
 - **curiositystream**: [*curiositystream*](## "netrc machine")
 - **curiositystream:collections**: [*curiositystream*](## "netrc machine")
 - **curiositystream:series**: [*curiositystream*](## "netrc machine")
 - **cwtv**
 - **cwtv:movie**
 - **Cybrary**: [*cybrary*](## "netrc machine")
 - **CybraryCourse**: [*cybrary*](## "netrc machine")
 - **DacastPlaylist**
 - **DacastVOD**
 - **DagelijkseKost**: dagelijksekost.een.be
 - **DailyMail**
 - **dailymotion**: [*dailymotion*](## "netrc machine")
 - **dailymotion:playlist**: [*dailymotion*](## "netrc machine")
 - **dailymotion:search**: [*dailymotion*](## "netrc machine")
 - **dailymotion:user**: [*dailymotion*](## "netrc machine")
 - **DailyWire**
 - **DailyWirePodcast**
 - **damtomo:record**
 - **damtomo:video**
 - **dangalplay**: [*dangalplay*](## "netrc machine")
 - **dangalplay:season**: [*dangalplay*](## "netrc machine")
 - **daum.net**
 - **daum.net:clip**
 - **daum.net:playlist**
 - **daum.net:user**
 - **daystar:clip**
 - **DBTV**
 - **DctpTv**
 - **democracynow**
 - **DestinationAmerica**
 - **DetikEmbed**
 - **DeuxM**
 - **DeuxMNews**
 - **DHM**: Filmarchiv - Deutsches Historisches Museum (**Currently broken**)
 - **DigitalConcertHall**: [*digitalconcerthall*](## "netrc machine") DigitalConcertHall extractor
 - **DigitallySpeaking**
 - **Digiteka**
 - **Digiview**
 - **DiscogsReleasePlaylist**
 - **DiscoveryLife**
 - **DiscoveryNetworksDe**
 - **DiscoveryPlus**
 - **DiscoveryPlusIndia**
 - **DiscoveryPlusIndiaShow**
 - **DiscoveryPlusItaly**
 - **DiscoveryPlusItalyShow**
 - **Disney**
 - **dlf**
 - **dlf:corpus**: DLF Multi-feed Archives
 - **dlive:stream**
 - **dlive:vod**
 - **Douyin**
 - **DouyuShow**
 - **DouyuTV**: 斗鱼直播
 - **DPlay**
 - **DRBonanza**
 - **Drooble**
 - **Dropbox**
 - **Dropout**: [*dropout*](## "netrc machine")
 - **DropoutSeason**
 - **DrTalks**
 - **DrTuber**
 - **drtv**
 - **drtv:live**
 - **drtv:season**
 - **drtv:series**
 - **DTube**: (**Currently broken**)
 - **duboku**: www.duboku.io
 - **duboku:list**: www.duboku.io entire series
 - **Dumpert**
 - **Duoplay**
 - **dvtv**: http://video.aktualne.cz/
 - **dw**: (**Currently broken**)
 - **dw:article**: (**Currently broken**)
 - **dzen.ru**: Дзен (dzen) formerly Яндекс.Дзен (Yandex Zen)
 - **dzen.ru:channel**
 - **EaglePlatform**
 - **EbaumsWorld**
 - **Ebay**
 - **egghead:course**: egghead.io course
 - **egghead:lesson**: egghead.io lesson
 - **eggs:artist**
 - **eggs:single**
 - **EinsUndEinsTV**: [*1und1tv*](## "netrc machine")
 - **EinsUndEinsTVLive**: [*1und1tv*](## "netrc machine")
 - **EinsUndEinsTVRecordings**: [*1und1tv*](## "netrc machine")
 - **eitb.tv**
 - **ElementorEmbed**
 - **Elonet**
 - **ElPais**: El País
 - **ElTreceTV**: El Trece TV (Argentina)
 - **Embedly**
 - **EMPFlix**
 - **Epicon**
 - **EpiconSeries**
 - **EpidemicSound**
 - **eplus**: [*eplus*](## "netrc machine") e+ (イープラス)
 - **Epoch**
 - **Eporner**
 - **Erocast**
 - **EroProfile**: [*eroprofile*](## "netrc machine")
 - **EroProfile:album**
 - **ERRJupiter**
 - **ertflix**: ERTFLIX videos
 - **ertflix:codename**: ERTFLIX videos by codename
 - **ertwebtv:embed**: ert.gr webtv embedded videos
 - **ESPN**
 - **ESPNArticle**
 - **ESPNCricInfo**
 - **EttuTv**
 - **Europa**: (**Currently broken**)
 - **EuroParlWebstream**
 - **EuropeanTour**
 - **Eurosport**
 - **EUScreen**
 - **EWETV**: [*ewetv*](## "netrc machine")
 - **EWETVLive**: [*ewetv*](## "netrc machine")
 - **EWETVRecordings**: [*ewetv*](## "netrc machine")
 - **Expressen**
 - **EyedoTV**
 - **facebook**: [*facebook*](## "netrc machine")
 - **facebook:ads**
 - **facebook:reel**
 - **FacebookPluginsVideo**
 - **fancode:live**: [*fancode*](## "netrc machine") (**Currently broken**)
 - **fancode:vod**: [*fancode*](## "netrc machine") (**Currently broken**)
 - **Fathom**
 - **faz.net**
 - **fc2**: [*fc2*](## "netrc machine")
 - **fc2:embed**
 - **fc2:live**
 - **Fczenit**
 - **Fifa**
 - **filmon**
 - **filmon:channel**
 - **Filmweb**
 - **FiveThirtyEight**
 - **FiveTV**
 - **FlexTV**
 - **Flickr**
 - **Floatplane**
 - **FloatplaneChannel**
 - **Folketinget**: Folketinget (ft.dk; Danish parliament)
 - **FoodNetwork**
 - **FootyRoom**
 - **Formula1**
 - **FOX**
 - **FOX9**
 - **FOX9News**
 - **foxnews**: Fox News and Fox Business Video
 - **foxnews:article**
 - **FoxNewsVideo**
 - **FoxSports**
 - **fptplay**: fptplay.vn
 - **FrancaisFacile**
 - **FranceCulture**
 - **FranceInter**
 - **francetv**
 - **francetv:site**
 - **francetvinfo.fr**
 - **Freesound**
 - **freespeech.org**
 - **freetv:series**
 - **FreeTvMovies**
 - **FrontendMasters**: [*frontendmasters*](## "netrc machine")
 - **FrontendMastersCourse**: [*frontendmasters*](## "netrc machine")
 - **FrontendMastersLesson**: [*frontendmasters*](## "netrc machine")
 - **FujiTVFODPlus7**
 - **Funk**
 - **Funker530**
 - **Fux**
 - **FuyinTV**
 - **Gab**
 - **GabTV**
 - **Gaia**: [*gaia*](## "netrc machine")
 - **GameDevTVDashboard**: [*gamedevtv*](## "netrc machine")
 - **GameJolt**
 - **GameJoltCommunity**
 - **GameJoltGame**
 - **GameJoltGameSoundtrack**
 - **GameJoltSearch**
 - **GameJoltUser**
 - **GameSpot**
 - **GameStar**
 - **Gaskrank**
 - **Gazeta**: (**Currently broken**)
 - **GBNews**: GB News clips, features and live streams
 - **GDCVault**: [*gdcvault*](## "netrc machine") (**Currently broken**)
 - **GediDigital**
 - **gem.cbc.ca**: [*cbcgem*](## "netrc machine")
 - **gem.cbc.ca:live**
 - **gem.cbc.ca:playlist**: [*cbcgem*](## "netrc machine")
 - **Genius**
 - **GeniusLyrics**
 - **Germanupa**: germanupa.de
 - **GetCourseRu**: [*getcourseru*](## "netrc machine")
 - **GetCourseRuPlayer**
 - **Gettr**
 - **GettrStreaming**
 - **GiantBomb**
 - **GlattvisionTV**: [*glattvisiontv*](## "netrc machine")
 - **GlattvisionTVLive**: [*glattvisiontv*](## "netrc machine")
 - **GlattvisionTVRecordings**: [*glattvisiontv*](## "netrc machine")
 - **Glide**: Glide mobile video messages (glide.me)
 - **GlobalPlayerAudio**
 - **GlobalPlayerAudioEpisode**
 - **GlobalPlayerLive**
 - **GlobalPlayerLivePlaylist**
 - **GlobalPlayerVideo**
 - **Globo**: [*globo*](## "netrc machine")
 - **GloboArticle**
 - **glomex**: Glomex videos
 - **glomex:embed**: Glomex embedded videos
 - **GMANetworkVideo**
 - **Go**
 - **GoDiscovery**
 - **GodResource**
 - **GodTube**: (**Currently broken**)
 - **Gofile**
 - **Golem**
 - **goodgame:stream**
 - **google:podcasts**
 - **google:​podcasts:feed**
 - **GoogleDrive**
 - **GoogleDrive:Folder**
 - **GoPlay**: [*goplay*](## "netrc machine")
 - **GoPro**
 - **Goshgay**
 - **GoToStage**
 - **GPUTechConf**
 - **Graspop**
 - **Gronkh**
 - **gronkh:feed**
 - **gronkh:vods**
 - **Groupon**
 - **Harpodeon**
 - **hbo**
 - **HearThisAt**
 - **Heise**
 - **HellPorno**
 - **hetklokhuis**
 - **hgtv.com:show**
 - **HGTVDe**
 - **HGTVUsa**
 - **HiDive**: [*hidive*](## "netrc machine")
 - **HistoricFilms**
 - **history:player**
 - **history:topic**: History.com Topic
 - **HitRecord**
 - **hketv**: 香港教育局教育電視 (HKETV) Educational Television, Hong Kong Educational Bureau
 - **HollywoodReporter**
 - **HollywoodReporterPlaylist**
 - **Holodex**
 - **HotNewHipHop**: (**Currently broken**)
 - **hotstar**
 - **hotstar:playlist**
 - **hotstar:season**
 - **hotstar:series**
 - **hrfernsehen**
 - **HRTi**: [*hrti*](## "netrc machine")
 - **HRTiPlaylist**: [*hrti*](## "netrc machine")
 - **HSEProduct**
 - **HSEShow**
 - **html5**
 - **Huajiao**: 花椒直播
 - **HuffPost**: Huffington Post
 - **Hungama**
 - **HungamaAlbumPlaylist**
 - **HungamaSong**
 - **huya:live**: huya.com
 - **huya:video**: 虎牙视频
 - **Hypem**
 - **Hytale**
 - **Icareus**
 - **IdolPlus**
 - **iflix:episode**
 - **IflixSeries**
 - **ign.com**
 - **IGNArticle**
 - **IGNVideo**
 - **iheartradio**
 - **iheartradio:podcast**
 - **IlPost**
 - **Iltalehti**
 - **imdb**: Internet Movie Database trailers
 - **imdb:list**: Internet Movie Database lists
 - **Imgur**
 - **imgur:album**
 - **imgur:gallery**
 - **Ina**
 - **Inc**
 - **IndavideoEmbed**
 - **InfoQ**
 - **Instagram**
 - **instagram:story**
 - **instagram:tag**: Instagram hashtag search URLs
 - **instagram:user**: Instagram user profile (**Currently broken**)
 - **InstagramIOS**: IOS instagram:// URL
 - **Internazionale**
 - **InternetVideoArchive**
 - **InvestigationDiscovery**
 - **IPrima**: [*iprima*](## "netrc machine")
 - **IPrimaCNN**
 - **iq.com**: International version of iQiyi
 - **iq.com:album**
 - **iqiyi**: [*iqiyi*](## "netrc machine") 爱奇艺
 - **IslamChannel**
 - **IslamChannelSeries**
 - **IsraelNationalNews**
 - **ITProTV**
 - **ITProTVCourse**
 - **ITV**
 - **ITVBTCC**
 - **ivi**: ivi.ru
 - **ivi:compilation**: ivi.ru compilations
 - **ivideon**: Ivideon TV
 - **Ivoox**
 - **IVXPlayer**
 - **iwara**: [*iwara*](## "netrc machine")
 - **iwara:playlist**: [*iwara*](## "netrc machine")
 - **iwara:user**: [*iwara*](## "netrc machine")
 - **Ixigua**
 - **Izlesene**
 - **Jamendo**
 - **JamendoAlbum**
 - **JeuxVideo**: (**Currently broken**)
 - **jiocinema**: [*jiocinema*](## "netrc machine")
 - **jiocinema:series**: [*jiocinema*](## "netrc machine")
 - **jiosaavn:album**
 - **jiosaavn:artist**
 - **jiosaavn:playlist**
 - **jiosaavn:show**
 - **jiosaavn:​show:playlist**
 - **jiosaavn:song**
 - **Joj**
 - **JoqrAg**: 超!A&G+ 文化放送 (f.k.a. AGQR) Nippon Cultural Broadcasting, Inc. (JOQR)
 - **Jove**
 - **JStream**
 - **JTBC**: jtbc.co.kr
 - **JTBC:program**
 - **JWPlatform**
 - **Kakao**
 - **Kaltura**
 - **KankaNews**: (**Currently broken**)
 - **Karaoketv**
 - **Katsomo**: (**Currently broken**)
 - **KelbyOne**: (**Currently broken**)
 - **Kenh14Playlist**
 - **Kenh14Video**
 - **khanacademy**
 - **khanacademy:unit**
 - **kick:clips**
 - **kick:live**
 - **kick:vod**
 - **Kicker**
 - **KickStarter**
 - **Kika**: KiKA.de
 - **KikaPlaylist**
 - **kinja:embed**
 - **KinoPoisk**
 - **Kommunetv**
 - **KompasVideo**
 - **Koo**: (**Currently broken**)
 - **KrasView**: Красвью (**Currently broken**)
 - **KTH**
 - **Ku6**
 - **KukuluLive**
 - **kuwo:album**: 酷我音乐 - 专辑 (**Currently broken**)
 - **kuwo:category**: 酷我音乐 - 分类 (**Currently broken**)
 - **kuwo:chart**: 酷我音乐 - 排行榜 (**Currently broken**)
 - **kuwo:mv**: 酷我音乐 - MV (**Currently broken**)
 - **kuwo:singer**: 酷我音乐 - 歌手 (**Currently broken**)
 - **kuwo:song**: 酷我音乐 (**Currently broken**)
 - **la7.it**
 - **la7.it:​pod:episode**
 - **la7.it:podcast**
 - **laracasts**
 - **laracasts:series**
 - **LastFM**
 - **LastFMPlaylist**
 - **LastFMUser**
 - **LaXarxaMes**: [*laxarxames*](## "netrc machine")
 - **lbry**: odysee.com
 - **lbry:channel**: odysee.com channels
 - **lbry:playlist**: odysee.com playlists
 - **LCI**
 - **Lcp**
 - **LcpPlay**
 - **Le**: 乐视网
 - **LearningOnScreen**
 - **Lecture2Go**: (**Currently broken**)
 - **Lecturio**: [*lecturio*](## "netrc machine")
 - **LecturioCourse**: [*lecturio*](## "netrc machine")
 - **LecturioDeCourse**: [*lecturio*](## "netrc machine")
 - **LeFigaroVideoEmbed**
 - **LeFigaroVideoSection**
 - **LEGO**
 - **Lemonde**
 - **Lenta**: (**Currently broken**)
 - **LePlaylist**
 - **LetvCloud**: 乐视云
 - **Libsyn**
 - **life**: Life.ru
 - **life:embed**
 - **likee**
 - **likee:user**
 - **limelight**
 - **limelight:channel**
 - **limelight:channel_list**
 - **LinkedIn**: [*linkedin*](## "netrc machine")
 - **linkedin:events**: [*linkedin*](## "netrc machine")
 - **linkedin:learning**: [*linkedin*](## "netrc machine")
 - **linkedin:​learning:course**: [*linkedin*](## "netrc machine")
 - **Liputan6**
 - **ListenNotes**
 - **LiTV**
 - **LiveJournal**
 - **livestream**
 - **livestream:original**
 - **Livestreamfails**
 - **Lnk**
 - **loc**: Library of Congress
 - **Loco**
 - **loom**
 - **loom:folder**
 - **LoveHomePorn**
 - **LRTRadio**
 - **LRTStream**
 - **LRTVOD**
 - **LSMLREmbed**
 - **LSMLTVEmbed**
 - **LSMReplay**
 - **Lumni**
 - **lynda**: [*lynda*](## "netrc machine") lynda.com videos
 - **lynda:course**: [*lynda*](## "netrc machine") lynda.com online courses
 - **maariv.co.il**
 - **MagellanTV**
 - **MagentaMusik**
 - **mailru**: Видео@Mail.Ru
 - **mailru:music**: Музыка@Mail.Ru
 - **mailru:​music:search**: Музыка@Mail.Ru
 - **MainStreaming**: MainStreaming Player
 - **mangomolo:live**
 - **mangomolo:video**
 - **MangoTV**: 芒果TV
 - **ManotoTV**: Manoto TV (Episode)
 - **ManotoTVLive**: Manoto TV (Live)
 - **ManotoTVShow**: Manoto TV (Show)
 - **ManyVids**
 - **MaoriTV**
 - **Markiza**: (**Currently broken**)
 - **MarkizaPage**: (**Currently broken**)
 - **massengeschmack.tv**
 - **Masters**
 - **MatchTV**
 - **MBN**: mbn.co.kr (매일방송)
 - **MDR**: MDR.DE
 - **MedalTV**
 - **media.ccc.de**
 - **media.ccc.de:lists**
 - **Mediaite**
 - **MediaKlikk**
 - **Medialaan**
 - **Mediaset**
 - **MediasetShow**
 - **Mediasite**
 - **MediasiteCatalog**
 - **MediasiteNamedCatalog**
 - **MediaStream**
 - **MediaWorksNZVOD**
 - **Medici**
 - **megaphone.fm**: megaphone.fm embedded players
 - **megatvcom**: megatv.com videos
 - **megatvcom:embed**: megatv.com embedded videos
 - **Meipai**: 美拍
 - **MelonVOD**
 - **Metacritic**
 - **mewatch**
 - **MicrosoftBuild**
 - **MicrosoftEmbed**
 - **MicrosoftLearnEpisode**
 - **MicrosoftLearnPlaylist**
 - **MicrosoftLearnSession**
 - **MicrosoftMedius**
 - **microsoftstream**: Microsoft Stream
 - **minds**
 - **minds:channel**
 - **minds:group**
 - **Minoto**
 - **mirrativ**
 - **mirrativ:user**
 - **MirrorCoUK**
 - **MiTele**: mitele.es
 - **mixch**
 - **mixch:archive**
 - **mixch:movie**
 - **mixcloud**
 - **mixcloud:playlist**
 - **mixcloud:user**
 - **MLB**
 - **MLBArticle**
 - **MLBTV**: [*mlb*](## "netrc machine")
 - **MLBVideo**
 - **MLSSoccer**
 - **MNetTV**: [*mnettv*](## "netrc machine")
 - **MNetTVLive**: [*mnettv*](## "netrc machine")
 - **MNetTVRecordings**: [*mnettv*](## "netrc machine")
 - **MochaVideo**
 - **Mojevideo**: mojevideo.sk
 - **Mojvideo**
 - **Monstercat**
 - **MonsterSirenHypergryphMusic**
 - **Motherless**
 - **MotherlessGallery**
 - **MotherlessGroup**
 - **MotherlessUploader**
 - **Motorsport**: motorsport.com (**Currently broken**)
 - **MovieFap**
 - **moviepilot**: Moviepilot trailer
 - **MoviewPlay**
 - **Moviezine**
 - **MovingImage**
 - **MSN**
 - **mtg**: MTG services
 - **mtv**
 - **mtv.de**: (**Currently broken**)
 - **mtv.it**
 - **mtv.it:programma**
 - **mtv:video**
 - **mtvjapan**
 - **mtvservices:embedded**
 - **MTVUutisetArticle**: (**Currently broken**)
 - **MuenchenTV**: münchen.tv (**Currently broken**)
 - **MujRozhlas**
 - **Murrtube**
 - **MurrtubeUser**: Murrtube user profile (**Currently broken**)
 - **MuseAI**
 - **MuseScore**
 - **MusicdexAlbum**
 - **MusicdexArtist**
 - **MusicdexPlaylist**
 - **MusicdexSong**
 - **Mx3**
 - **Mx3Neo**
 - **Mx3Volksmusik**
 - **Mxplayer**
 - **MxplayerShow**
 - **MySpace**
 - **MySpace:album**
 - **MySpass**
 - **MyVideoGe**
 - **MyVidster**
 - **Mzaalo**
 - **n-tv.de**
 - **N1Info:article**
 - **N1InfoAsset**
 - **Nate**
 - **NateProgram**
 - **natgeo:video**
 - **NationalGeographicTV**
 - **Naver**
 - **Naver:live**
 - **navernow**
 - **nba**: (**Currently broken**)
 - **nba:channel**: (**Currently broken**)
 - **nba:embed**: (**Currently broken**)
 - **nba:watch**: (**Currently broken**)
 - **nba:​watch:collection**: (**Currently broken**)
 - **nba:​watch:embed**: (**Currently broken**)
 - **NBC**
 - **NBCNews**
 - **nbcolympics**
 - **nbcolympics:stream**: (**Currently broken**)
 - **NBCSports**: (**Currently broken**)
 - **NBCSportsStream**: (**Currently broken**)
 - **NBCSportsVPlayer**: (**Currently broken**)
 - **NBCStations**
 - **ndr**: NDR.de - Norddeutscher Rundfunk
 - **ndr:embed**
 - **ndr:​embed:base**
 - **NDTV**: (**Currently broken**)
 - **nebula:channel**: [*watchnebula*](## "netrc machine")
 - **nebula:media**: [*watchnebula*](## "netrc machine")
 - **nebula:subscriptions**: [*watchnebula*](## "netrc machine")
 - **nebula:video**: [*watchnebula*](## "netrc machine")
 - **NekoHacker**
 - **NerdCubedFeed**
 - **Nest**
 - **NestClip**
 - **netease:album**: 网易云音乐 - 专辑
 - **netease:djradio**: 网易云音乐 - 电台
 - **netease:mv**: 网易云音乐 - MV
 - **netease:playlist**: 网易云音乐 - 歌单
 - **netease:program**: 网易云音乐 - 电台节目
 - **netease:singer**: 网易云音乐 - 歌手
 - **netease:song**: 网易云音乐
 - **NetPlusTV**: [*netplus*](## "netrc machine")
 - **NetPlusTVLive**: [*netplus*](## "netrc machine")
 - **NetPlusTVRecordings**: [*netplus*](## "netrc machine")
 - **Netverse**
 - **NetversePlaylist**
 - **NetverseSearch**: "netsearch:" prefix
 - **Netzkino**: (**Currently broken**)
 - **Newgrounds**: [*newgrounds*](## "netrc machine")
 - **Newgrounds:playlist**
 - **Newgrounds:user**
 - **NewsPicks**
 - **Newsy**
 - **NextMedia**: 蘋果日報
 - **NextMediaActionNews**: 蘋果日報 - 動新聞
 - **NextTV**: 壹電視 (**Currently broken**)
 - **Nexx**
 - **NexxEmbed**
 - **nfb**: nfb.ca and onf.ca films and episodes
 - **nfb:series**: nfb.ca and onf.ca series
 - **NFHSNetwork**
 - **nfl.com**
 - **nfl.com:article**
 - **nfl.com:​plus:episode**
 - **nfl.com:​plus:replay**
 - **NhkForSchoolBangumi**
 - **NhkForSchoolProgramList**
 - **NhkForSchoolSubject**: Portal page for each school subjects, like Japanese (kokugo, 国語) or math (sansuu/suugaku or 算数・数学)
 - **NhkRadioNewsPage**
 - **NhkRadiru**: NHK らじる (Radiru/Rajiru)
 - **NhkRadiruLive**
 - **NhkVod**
 - **NhkVodProgram**
 - **nhl.com**
 - **nick.com**
 - **nick.de**
 - **nickelodeon:br**
 - **nickelodeonru**
 - **niconico**: [*niconico*](## "netrc machine") ニコニコ動画
 - **niconico:history**: NicoNico user history or likes. Requires cookies.
 - **niconico:live**: [*niconico*](## "netrc machine") ニコニコ生放送
 - **niconico:playlist**
 - **niconico:series**
 - **niconico:tag**: NicoNico video tag URLs
 - **NiconicoChannelPlus**: ニコニコチャンネルプラス
 - **NiconicoChannelPlus:​channel:lives**: ニコニコチャンネルプラス - チャンネル - ライブリスト. nicochannel.jp/channel/lives
 - **NiconicoChannelPlus:​channel:videos**: ニコニコチャンネルプラス - チャンネル - 動画リスト. nicochannel.jp/channel/videos
 - **NiconicoUser**
 - **nicovideo:search**: Nico video search; "nicosearch:" prefix
 - **nicovideo:​search:date**: Nico video search, newest first; "nicosearchdate:" prefix
 - **nicovideo:search_url**: Nico video search URLs
 - **NinaProtocol**
 - **Nintendo**
 - **Nitter**
 - **njoy**: N-JOY
 - **njoy:embed**
 - **NobelPrize**
 - **NoicePodcast**
 - **NonkTube**
 - **NoodleMagazine**
 - **Noovo**
 - **NOSNLArticle**
 - **Nova**: TN.cz, Prásk.tv, Nova.cz, Novaplus.cz, FANDA.tv, Krásná.cz and Doma.cz
 - **NovaEmbed**
 - **NovaPlay**
 - **nowness**
 - **nowness:playlist**
 - **nowness:series**
 - **Noz**: (**Currently broken**)
 - **npo**: npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl
 - **npo.nl:live**
 - **npo.nl:radio**
 - **npo.nl:​radio:fragment**
 - **Npr**
 - **NRK**
 - **NRKPlaylist**
 - **NRKRadioPodkast**
 - **NRKSkole**: NRK Skole
 - **NRKTV**: NRK TV and NRK Radio
 - **NRKTVDirekte**: NRK TV Direkte and NRK Radio Direkte
 - **NRKTVEpisode**
 - **NRKTVEpisodes**
 - **NRKTVSeason**
 - **NRKTVSeries**
 - **NRLTV**: (**Currently broken**)
 - **nts.live**
 - **ntv.ru**
 - **NubilesPorn**: [*nubiles-porn*](## "netrc machine")
 - **nuum:live**
 - **nuum:media**
 - **nuum:tab**
 - **Nuvid**
 - **NYTimes**
 - **NYTimesArticle**
 - **NYTimesCookingGuide**
 - **NYTimesCookingRecipe**
 - **nzherald**
 - **NZOnScreen**
 - **NZZ**
 - **ocw.mit.edu**
 - **Odnoklassniki**
 - **OfTV**
 - **OfTVPlaylist**
 - **OktoberfestTV**
 - **OlympicsReplay**
 - **on24**: ON24
 - **OnDemandChinaEpisode**
 - **OnDemandKorea**
 - **OnDemandKoreaProgram**
 - **OneFootball**
 - **OnePlacePodcast**
 - **onet.pl**
 - **onet.tv**
 - **onet.tv:channel**
 - **OnetMVP**
 - **OnionStudios**
 - **Opencast**
 - **OpencastPlaylist**
 - **openrec**
 - **openrec:capture**
 - **openrec:movie**
 - **OraTV**
 - **orf:​fm4:story**: fm4.orf.at stories
 - **orf:iptv**: iptv.ORF.at
 - **orf:on**
 - **orf:podcast**
 - **orf:radio**
 - **OsnatelTV**: [*osnateltv*](## "netrc machine")
 - **OsnatelTVLive**: [*osnateltv*](## "netrc machine")
 - **OsnatelTVRecordings**: [*osnateltv*](## "netrc machine")
 - **OutsideTV**
 - **OwnCloud**
 - **PacktPub**: [*packtpub*](## "netrc machine")
 - **PacktPubCourse**
 - **PalcoMP3:artist**
 - **PalcoMP3:song**
 - **PalcoMP3:video**
 - **Panopto**
 - **PanoptoList**
 - **PanoptoPlaylist**
 - **ParamountNetwork**
 - **ParamountPlus**
 - **ParamountPlusSeries**
 - **ParamountPressExpress**
 - **Parler**: Posts on parler.com
 - **parliamentlive.tv**: UK parliament videos
 - **Parlview**: (**Currently broken**)
 - **parti:livestream**
 - **parti:video**
 - **patreon**
 - **patreon:campaign**
 - **pbs**: Public Broadcasting Service (PBS) and member stations: PBS: Public Broadcasting Service, APT - Alabama Public Television (WBIQ), GPB/Georgia Public Broadcasting (WGTV), Mississippi Public Broadcasting (WMPN), Nashville Public Television (WNPT), WFSU-TV (WFSU), WSRE (WSRE), WTCI (WTCI), WPBA/Channel 30 (WPBA), Alaska Public Media (KAKM), Arizona PBS (KAET), KNME-TV/Channel 5 (KNME), Vegas PBS (KLVX), AETN/ARKANSAS ETV NETWORK (KETS), KET (WKLE), WKNO/Channel 10 (WKNO), LPB/LOUISIANA PUBLIC BROADCASTING (WLPB), OETA (KETA), Ozarks Public Television (KOZK), WSIU Public Broadcasting (WSIU), KEET TV (KEET), KIXE/Channel 9 (KIXE), KPBS San Diego (KPBS), KQED (KQED), KVIE Public Television (KVIE), PBS SoCal/KOCE (KOCE), ValleyPBS (KVPT), CONNECTICUT PUBLIC TELEVISION (WEDH), KNPB Channel 5 (KNPB), SOPTV (KSYS), Rocky Mountain PBS (KRMA), KENW-TV3 (KENW), KUED Channel 7 (KUED), Wyoming PBS (KCWC), Colorado Public Television / KBDI 12 (KBDI), KBYU-TV (KBYU), Thirteen/WNET New York (WNET), WGBH/Channel 2 (WGBH), WGBY (WGBY), NJTV Public Media NJ (WNJT), WLIW21 (WLIW), mpt/Maryland Public Television (WMPB), WETA Television and Radio (WETA), WHYY (WHYY), PBS 39 (WLVT), WVPT - Your Source for PBS and More! (WVPT), Howard University Television (WHUT), WEDU PBS (WEDU), WGCU Public Media (WGCU), WPBT2 (WPBT), WUCF TV (WUCF), WUFT/Channel 5 (WUFT), WXEL/Channel 42 (WXEL), WLRN/Channel 17 (WLRN), WUSF Public Broadcasting (WUSF), ETV (WRLK), UNC-TV (WUNC), PBS Hawaii - Oceanic Cable Channel 10 (KHET), Idaho Public Television (KAID), KSPS (KSPS), OPB (KOPB), KWSU/Channel 10 & KTNW/Channel 31 (KWSU), WILL-TV (WILL), Network Knowledge - WSEC/Springfield (WSEC), WTTW11 (WTTW), Iowa Public Television/IPTV (KDIN), Nine Network (KETC), PBS39 Fort Wayne (WFWA), WFYI Indianapolis (WFYI), Milwaukee Public Television (WMVS), WNIN (WNIN), WNIT Public Television (WNIT), WPT (WPNE), WVUT/Channel 22 (WVUT), WEIU/Channel 51 (WEIU), WQPT-TV (WQPT), WYCC PBS Chicago (WYCC), WIPB-TV (WIPB), WTIU (WTIU), CET  (WCET), ThinkTVNetwork (WPTD), WBGU-TV (WBGU), WGVU TV (WGVU), NET1 (KUON), Pioneer Public Television (KWCM), SDPB Television (KUSD), TPT (KTCA), KSMQ (KSMQ), KPTS/Channel 8 (KPTS), KTWU/Channel 11 (KTWU), East Tennessee PBS (WSJK), WCTE-TV (WCTE), WLJT, Channel 11 (WLJT), WOSU TV (WOSU), WOUB/WOUC (WOUB), WVPB (WVPB), WKYU-PBS (WKYU), KERA 13 (KERA), MPBN (WCBB), Mountain Lake PBS (WCFE), NHPTV (WENH), Vermont PBS (WETK), witf (WITF), WQED Multimedia (WQED), WMHT Educational Telecommunications (WMHT), Q-TV (WDCQ), WTVS Detroit Public TV (WTVS), CMU Public Television (WCMU), WKAR-TV (WKAR), WNMU-TV Public TV 13 (WNMU), WDSE - WRPT (WDSE), WGTE TV (WGTE), Lakeland Public Television (KAWE), KMOS-TV - Channels 6.1, 6.2 and 6.3 (KMOS), MontanaPBS (KUSM), KRWG/Channel 22 (KRWG), KACV (KACV), KCOS/Channel 13 (KCOS), WCNY/Channel 24 (WCNY), WNED (WNED), WPBS (WPBS), WSKG Public TV (WSKG), WXXI (WXXI), WPSU (WPSU), WVIA Public Media Studios (WVIA), WTVI (WTVI), Western Reserve PBS (WNEO), WVIZ/PBS ideastream (WVIZ), KCTS 9 (KCTS), Basin PBS (KPBT), KUHT / Channel 8 (KUHT), KLRN (KLRN), KLRU (KLRU), WTJX Channel 12 (WTJX), WCVE PBS (WCVE), KBTC Public Television (KBTC)
 - **PBSKids**
 - **PearVideo**
 - **PeekVids**
 - **peer.tv**
 - **PeerTube**
 - **PeerTube:Playlist**
 - **peloton**: [*peloton*](## "netrc machine")
 - **peloton:live**: Peloton Live
 - **PerformGroup**
 - **periscope**: Periscope
 - **periscope:user**: Periscope user videos
 - **PGATour**
 - **PhilharmonieDeParis**: Philharmonie de Paris
 - **phoenix.de**
 - **Photobucket**
 - **PiaLive**
 - **Piapro**: [*piapro*](## "netrc machine")
 - **picarto**
 - **picarto:vod**
 - **Piksel**
 - **Pinkbike**
 - **Pinterest**
 - **PinterestCollection**
 - **PiramideTV**
 - **PiramideTVChannel**
 - **pixiv:sketch**
 - **pixiv:​sketch:user**
 - **Pladform**
 - **PlanetMarathi**
 - **Platzi**: [*platzi*](## "netrc machine")
 - **PlatziCourse**: [*platzi*](## "netrc machine")
 - **player.sky.it**
 - **playeur**
 - **PlayPlusTV**: [*playplustv*](## "netrc machine")
 - **PlaySuisse**: [*playsuisse*](## "netrc machine")
 - **Playtvak**: Playtvak.cz, iDNES.cz and Lidovky.cz
 - **PlayVids**
 - **Playwire**
 - **pluralsight**: [*pluralsight*](## "netrc machine")
 - **pluralsight:course**
 - **PlutoTV**: (**Currently broken**)
 - **PlVideo**: Платформа
 - **PodbayFM**
 - **PodbayFMChannel**
 - **Podchaser**
 - **podomatic**: (**Currently broken**)
 - **PokerGo**: [*pokergo*](## "netrc machine")
 - **PokerGoCollection**: [*pokergo*](## "netrc machine")
 - **PolsatGo**
 - **PolskieRadio**
 - **polskieradio:audition**
 - **polskieradio:category**
 - **polskieradio:legacy**
 - **polskieradio:player**
 - **polskieradio:podcast**
 - **polskieradio:​podcast:list**
 - **Popcorntimes**
 - **PopcornTV**
 - **Pornbox**
 - **PornerBros**
 - **PornFlip**
 - **PornHub**: [*pornhub*](## "netrc machine") PornHub and Thumbzilla
 - **PornHubPagedVideoList**: [*pornhub*](## "netrc machine")
 - **PornHubPlaylist**: [*pornhub*](## "netrc machine")
 - **PornHubUser**: [*pornhub*](## "netrc machine")
 - **PornHubUserVideosUpload**: [*pornhub*](## "netrc machine")
 - **Pornotube**
 - **PornoVoisines**: (**Currently broken**)
 - **PornoXO**: (**Currently broken**)
 - **PornTop**
 - **PornTube**
 - **Pr0gramm**
 - **PrankCast**
 - **PrankCastPost**
 - **PremiershipRugby**
 - **PressTV**
 - **ProjectVeritas**: (**Currently broken**)
 - **prosiebensat1**: ProSiebenSat.1 Digital
 - **PRXAccount**
 - **PRXSeries**
 - **prxseries:search**: PRX Series Search; "prxseries:" prefix
 - **prxstories:search**: PRX Stories Search; "prxstories:" prefix
 - **PRXStory**
 - **puhutv**
 - **puhutv:serie**
 - **Puls4**
 - **Pyvideo**
 - **QDance**: [*qdance*](## "netrc machine")
 - **QingTing**
 - **qqmusic**: QQ音乐
 - **qqmusic:album**: QQ音乐 - 专辑
 - **qqmusic:mv**: QQ音乐 - MV
 - **qqmusic:playlist**: QQ音乐 - 歌单
 - **qqmusic:singer**: QQ音乐 - 歌手
 - **qqmusic:toplist**: QQ音乐 - 排行榜
 - **QuantumTV**: [*quantumtv*](## "netrc machine")
 - **QuantumTVLive**: [*quantumtv*](## "netrc machine")
 - **QuantumTVRecordings**: [*quantumtv*](## "netrc machine")
 - **R7**: (**Currently broken**)
 - **R7Article**: (**Currently broken**)
 - **Radiko**
 - **RadikoRadio**
 - **radio.de**: (**Currently broken**)
 - **Radio1Be**
 - **radiocanada**
 - **radiocanada:audiovideo**
 - **RadioComercial**
 - **RadioComercialPlaylist**
 - **radiofrance**
 - **RadioFranceLive**
 - **RadioFrancePodcast**
 - **RadioFranceProfile**
 - **RadioFranceProgramSchedule**
 - **RadioJavan**: (**Currently broken**)
 - **radiokapital**
 - **radiokapital:show**
 - **RadioRadicale**
 - **RadioZetPodcast**
 - **radlive**
 - **radlive:channel**
 - **radlive:season**
 - **Rai**
 - **RaiCultura**
 - **RaiNews**
 - **RaiPlay**
 - **RaiPlayLive**
 - **RaiPlayPlaylist**
 - **RaiPlaySound**
 - **RaiPlaySoundLive**
 - **RaiPlaySoundPlaylist**
 - **RaiSudtirol**
 - **RayWenderlich**
 - **RayWenderlichCourse**
 - **RbgTum**
 - **RbgTumCourse**
 - **RbgTumNewCourse**
 - **RCS**
 - **RCSEmbeds**
 - **RCSVarious**
 - **RCTIPlus**
 - **RCTIPlusSeries**
 - **RCTIPlusTV**
 - **RDS**: RDS.ca (**Currently broken**)
 - **RedBull**
 - **RedBullEmbed**
 - **RedBullTV**
 - **RedBullTVRrnContent**
 - **redcdnlivx**
 - **Reddit**: [*reddit*](## "netrc machine")
 - **RedGifs**
 - **RedGifsSearch**: Redgifs search
 - **RedGifsUser**: Redgifs user
 - **RedTube**
 - **RENTV**: (**Currently broken**)
 - **RENTVArticle**: (**Currently broken**)
 - **Restudy**: (**Currently broken**)
 - **Reuters**: (**Currently broken**)
 - **ReverbNation**
 - **RheinMainTV**
 - **RideHome**
 - **RinseFM**
 - **RinseFMArtistPlaylist**
 - **RMCDecouverte**
 - **RockstarGames**: (**Currently broken**)
 - **Rokfin**: [*rokfin*](## "netrc machine")
 - **rokfin:channel**: Rokfin Channels
 - **rokfin:search**: Rokfin Search; "rkfnsearch:" prefix
 - **rokfin:stack**: Rokfin Stacks
 - **RoosterTeeth**: [*roosterteeth*](## "netrc machine")
 - **RoosterTeethSeries**: [*roosterteeth*](## "netrc machine")
 - **RottenTomatoes**
 - **RoyaLive**
 - **Rozhlas**
 - **RozhlasVltava**
 - **RTBF**: [*rtbf*](## "netrc machine") (**Currently broken**)
 - **RTDocumentry**
 - **RTDocumentryPlaylist**
 - **rte**: Raidió Teilifís Éireann TV
 - **rte:radio**: Raidió Teilifís Éireann radio
 - **rtl.lu:article**
 - **rtl.lu:tele-vod**
 - **rtl.nl**: rtl.nl and rtlxl.nl
 - **rtl2**
 - **RTLLuLive**
 - **RTLLuRadio**
 - **RTNews**
 - **RTP**
 - **RTRFM**
 - **RTS**: RTS.ch (**Currently broken**)
 - **RTVCKaltura**
 - **RTVCPlay**
 - **RTVCPlayEmbed**
 - **rtve.es:alacarta**: RTVE a la carta and Play
 - **rtve.es:audio**: RTVE audio
 - **rtve.es:live**: RTVE.es live streams
 - **rtve.es:television**
 - **rtvslo.si**
 - **rtvslo.si:show**
 - **RudoVideo**
 - **Rule34Video**
 - **Rumble**
 - **RumbleChannel**
 - **RumbleEmbed**
 - **Ruptly**
 - **rutube**: Rutube videos
 - **rutube:channel**: Rutube channel
 - **rutube:embed**: Rutube embedded videos
 - **rutube:movie**: Rutube movies
 - **rutube:person**: Rutube person videos
 - **rutube:playlist**: Rutube playlists
 - **rutube:tags**: Rutube tags
 - **RUTV**: RUTV.RU
 - **Ruutu**
 - **Ruv**
 - **ruv.is:spila**
 - **S4C**
 - **S4CSeries**
 - **safari**: [*safari*](## "netrc machine") safaribooksonline.com online video
 - **safari:api**: [*safari*](## "netrc machine")
 - **safari:course**: [*safari*](## "netrc machine") safaribooksonline.com online courses
 - **Saitosan**: (**Currently broken**)
 - **SAKTV**: [*saktv*](## "netrc machine")
 - **SAKTVLive**: [*saktv*](## "netrc machine")
 - **SAKTVRecordings**: [*saktv*](## "netrc machine")
 - **SaltTV**: [*salttv*](## "netrc machine")
 - **SaltTVLive**: [*salttv*](## "netrc machine")
 - **SaltTVRecordings**: [*salttv*](## "netrc machine")
 - **SampleFocus**
 - **Sangiin**: 参議院インターネット審議中継 (archive)
 - **Sapo**: SAPO Vídeos
 - **SBS**: sbs.com.au
 - **sbs.co.kr**
 - **sbs.co.kr:allvod_program**
 - **sbs.co.kr:programs_vod**
 - **schooltv**
 - **ScienceChannel**
 - **screen.yahoo:search**: Yahoo screen search; "yvsearch:" prefix
 - **Screen9**
 - **Screencast**
 - **Screencastify**
 - **ScreencastOMatic**
 - **ScreenRec**
 - **ScrippsNetworks**
 - **scrippsnetworks:watch**
 - **Scrolller**
 - **SCTE**: [*scte*](## "netrc machine") (**Currently broken**)
 - **SCTECourse**: [*scte*](## "netrc machine") (**Currently broken**)
 - **sejm**
 - **Sen**
 - **SenalColombiaLive**: (**Currently broken**)
 - **senate.gov**
 - **senate.gov:isvp**
 - **SendtoNews**: (**Currently broken**)
 - **Servus**
 - **Sexu**: (**Currently broken**)
 - **SeznamZpravy**
 - **SeznamZpravyArticle**
 - **Shahid**: [*shahid*](## "netrc machine")
 - **ShahidShow**
 - **SharePoint**
 - **ShareVideosEmbed**
 - **ShemarooMe**
 - **ShowRoomLive**
 - **ShugiinItvLive**: 衆議院インターネット審議中継
 - **ShugiinItvLiveRoom**: 衆議院インターネット審議中継 (中継)
 - **ShugiinItvVod**: 衆議院インターネット審議中継 (ビデオライブラリ)
 - **SibnetEmbed**
 - **simplecast**
 - **simplecast:episode**
 - **simplecast:podcast**
 - **Sina**
 - **Skeb**
 - **sky.it**
 - **sky:news**
 - **sky:​news:story**
 - **sky:sports**
 - **sky:​sports:news**
 - **SkylineWebcams**: (**Currently broken**)
 - **skynewsarabia:article**: (**Currently broken**)
 - **skynewsarabia:video**: (**Currently broken**)
 - **SkyNewsAU**
 - **Slideshare**
 - **SlidesLive**
 - **Slutload**
 - **Smotrim**
 - **SnapchatSpotlight**
 - **Snotr**
 - **SoftWhiteUnderbelly**: [*softwhiteunderbelly*](## "netrc machine")
 - **Sohu**
 - **SohuV**
 - **SonyLIV**: [*sonyliv*](## "netrc machine")
 - **SonyLIVSeries**
 - **soop**: [*afreecatv*](## "netrc machine") sooplive.co.kr
 - **soop:catchstory**: [*afreecatv*](## "netrc machine") sooplive.co.kr catch story
 - **soop:live**: [*afreecatv*](## "netrc machine") sooplive.co.kr livestreams
 - **soop:user**: [*afreecatv*](## "netrc machine")
 - **soundcloud**: [*soundcloud*](## "netrc machine")
 - **soundcloud:playlist**: [*soundcloud*](## "netrc machine")
 - **soundcloud:related**: [*soundcloud*](## "netrc machine")
 - **soundcloud:search**: [*soundcloud*](## "netrc machine") Soundcloud search; "scsearch:" prefix
 - **soundcloud:set**: [*soundcloud*](## "netrc machine")
 - **soundcloud:trackstation**: [*soundcloud*](## "netrc machine")
 - **soundcloud:user**: [*soundcloud*](## "netrc machine")
 - **soundcloud:​user:permalink**: [*soundcloud*](## "netrc machine")
 - **SoundcloudEmbed**
 - **soundgasm**
 - **soundgasm:profile**
 - **southpark.cc.com**
 - **southpark.cc.com:español**
 - **southpark.de**
 - **southpark.lat**
 - **southpark.nl**
 - **southparkstudios.dk**
 - **SovietsCloset**
 - **SovietsClosetPlaylist**
 - **SpankBang**
 - **SpankBangPlaylist**
 - **Spiegel**
 - **Sport5**
 - **SportBox**
 - **SportDeutschland**
 - **spotify**: Spotify episodes (**Currently broken**)
 - **spotify:show**: Spotify shows (**Currently broken**)
 - **Spreaker**
 - **SpreakerShow**
 - **SpringboardPlatform**
 - **SproutVideo**
 - **sr:mediathek**: Saarländischer Rundfunk
 - **SRGSSR**
 - **SRGSSRPlay**: srf.ch, rts.ch, rsi.ch, rtr.ch and swissinfo.ch play sites
 - **StacommuLive**: [*stacommu*](## "netrc machine")
 - **StacommuVOD**: [*stacommu*](## "netrc machine")
 - **StagePlusVODConcert**: [*stageplus*](## "netrc machine")
 - **stanfordoc**: Stanford Open ClassRoom
 - **startrek**: STAR TREK
 - **startv**
 - **Steam**
 - **SteamCommunityBroadcast**
 - **Stitcher**
 - **StitcherShow**
 - **StoryFire**
 - **StoryFireSeries**
 - **StoryFireUser**
 - **Streaks**
 - **Streamable**
 - **StreamCZ**
 - **StreetVoice**
 - **StretchInternet**
 - **Stripchat**
 - **stv:player**
 - **stvr**: Slovak Television and Radio (formerly RTVS)
 - **Subsplash**
 - **subsplash:playlist**
 - **Substack**
 - **SunPorno**
 - **sverigesradio:episode**
 - **sverigesradio:publication**
 - **svt:page**
 - **svt:play**: SVT Play and Öppet arkiv
 - **svt:​play:series**
 - **SwearnetEpisode**
 - **Syfy**
 - **SYVDK**
 - **SztvHu**
 - **t-online.de**: (**Currently broken**)
 - **Tagesschau**: (**Currently broken**)
 - **TapTapApp**
 - **TapTapAppIntl**
 - **TapTapMoment**
 - **TapTapPostIntl**
 - **Tass**: (**Currently broken**)
 - **TBS**
 - **TBSJPEpisode**
 - **TBSJPPlaylist**
 - **TBSJPProgram**
 - **Teachable**: [*teachable*](## "netrc machine") (**Currently broken**)
 - **TeachableCourse**: [*teachable*](## "netrc machine")
 - **teachertube**: teachertube.com videos (**Currently broken**)
 - **teachertube:​user:collection**: teachertube.com user and collection videos (**Currently broken**)
 - **TeachingChannel**: (**Currently broken**)
 - **Teamcoco**
 - **TeamTreeHouse**: [*teamtreehouse*](## "netrc machine")
 - **techtv.mit.edu**
 - **TedEmbed**
 - **TedPlaylist**
 - **TedSeries**
 - **TedTalk**
 - **Tele13**
 - **Tele5**
 - **TeleBruxelles**
 - **TelecaribePlay**
 - **Telecinco**: telecinco.es, cuatro.com and mediaset.es
 - **Telegraaf**
 - **telegram:embed**
 - **TeleMB**: (**Currently broken**)
 - **Telemundo**: (**Currently broken**)
 - **TeleQuebec**
 - **TeleQuebecEmission**
 - **TeleQuebecLive**
 - **TeleQuebecSquat**
 - **TeleQuebecVideo**
 - **TeleTask**: (**Currently broken**)
 - **Telewebion**: (**Currently broken**)
 - **Tempo**
 - **TennisTV**: [*tennistv*](## "netrc machine")
 - **TF1**
 - **TFO**
 - **theatercomplextown:ppv**: [*theatercomplextown*](## "netrc machine")
 - **theatercomplextown:vod**: [*theatercomplextown*](## "netrc machine")
 - **TheGuardianPodcast**
 - **TheGuardianPodcastPlaylist**
 - **TheHoleTv**
 - **TheIntercept**
 - **ThePlatform**
 - **ThePlatformFeed**
 - **TheStar**
 - **TheSun**
 - **TheWeatherChannel**
 - **ThisAmericanLife**
 - **ThisOldHouse**: [*thisoldhouse*](## "netrc machine")
 - **ThisVid**
 - **ThisVidMember**
 - **ThisVidPlaylist**
 - **ThreeSpeak**
 - **ThreeSpeakUser**
 - **TikTok**
 - **tiktok:collection**
 - **tiktok:effect**: (**Currently broken**)
 - **tiktok:live**
 - **tiktok:sound**: (**Currently broken**)
 - **tiktok:tag**: (**Currently broken**)
 - **tiktok:user**
 - **TLC**
 - **TMZ**
 - **TNAFlix**
 - **TNAFlixNetworkEmbed**
 - **toggle**
 - **toggo**
 - **tokfm:audition**
 - **tokfm:podcast**
 - **ToonGoggles**
 - **tou.tv**: [*toutv*](## "netrc machine")
 - **toutiao**: 今日头条
 - **Toypics**: Toypics video (**Currently broken**)
 - **ToypicsUser**: Toypics user profile (**Currently broken**)
 - **TrailerAddict**: (**Currently broken**)
 - **TravelChannel**
 - **Triller**: [*triller*](## "netrc machine")
 - **TrillerShort**
 - **TrillerUser**: [*triller*](## "netrc machine")
 - **Trovo**
 - **TrovoChannelClip**: All Clips of a trovo.live channel; "trovoclip:" prefix
 - **TrovoChannelVod**: All VODs of a trovo.live channel; "trovovod:" prefix
 - **TrovoVod**
 - **TrtCocukVideo**
 - **TrtWorld**
 - **TrueID**
 - **TruNews**
 - **Truth**
 - **TruTV**
 - **Tube8**: (**Currently broken**)
 - **TubeTuGraz**: [*tubetugraz*](## "netrc machine") tube.tugraz.at
 - **TubeTuGrazSeries**: [*tubetugraz*](## "netrc machine")
 - **tubitv**: [*tubitv*](## "netrc machine")
 - **tubitv:series**
 - **Tumblr**: [*tumblr*](## "netrc machine")
 - **TuneInPodcast**
 - **TuneInPodcastEpisode**
 - **TuneInStation**
 - **tv.dfb.de**
 - **TV2**
 - **TV2Article**
 - **TV2DK**
 - **TV2DKBornholmPlay**
 - **tv2play.hu**
 - **tv2playseries.hu**
 - **TV4**: tv4.se and tv4play.se
 - **TV5MONDE**
 - **tv5unis**
 - **tv5unis:video**
 - **tv8.it**
 - **tv8.it:live**: TV8 Live
 - **tv8.it:playlist**: TV8 Playlist
 - **TVANouvelles**
 - **TVANouvellesArticle**
 - **tvaplus**: TVA+
 - **TVC**
 - **TVCArticle**
 - **TVer**
 - **tvigle**: Интернет-телевидение Tvigle.ru
 - **TVIPlayer**
 - **tvland.com**
 - **TVN24**: (**Currently broken**)
 - **TVNoe**: (**Currently broken**)
 - **tvopengr:embed**: tvopen.gr embedded videos
 - **tvopengr:watch**: tvopen.gr (and ethnos.gr) videos
 - **tvp**: Telewizja Polska
 - **tvp:embed**: Telewizja Polska
 - **tvp:stream**
 - **tvp:vod**
 - **tvp:​vod:series**
 - **TVPlayer**
 - **TVPlayHome**
 - **tvw**
 - **tvw:tvchannels**
 - **Tweakers**
 - **TwitCasting**
 - **TwitCastingLive**
 - **TwitCastingUser**
 - **twitch:clips**: [*twitch*](## "netrc machine")
 - **twitch:stream**: [*twitch*](## "netrc machine")
 - **twitch:vod**: [*twitch*](## "netrc machine")
 - **TwitchCollection**: [*twitch*](## "netrc machine")
 - **TwitchVideos**: [*twitch*](## "netrc machine")
 - **TwitchVideosClips**: [*twitch*](## "netrc machine")
 - **TwitchVideosCollections**: [*twitch*](## "netrc machine")
 - **twitter**: [*twitter*](## "netrc machine")
 - **twitter:amplify**: [*twitter*](## "netrc machine")
 - **twitter:broadcast**: [*twitter*](## "netrc machine")
 - **twitter:card**
 - **twitter:shortener**: [*twitter*](## "netrc machine")
 - **twitter:spaces**: [*twitter*](## "netrc machine")
 - **Txxx**
 - **udemy**: [*udemy*](## "netrc machine")
 - **udemy:course**: [*udemy*](## "netrc machine")
 - **UDNEmbed**: 聯合影音
 - **UFCArabia**: [*ufcarabia*](## "netrc machine")
 - **UFCTV**: [*ufctv*](## "netrc machine")
 - **ukcolumn**: (**Currently broken**)
 - **UKTVPlay**
 - **UlizaPlayer**
 - **UlizaPortal**: ulizaportal.jp
 - **umg:de**: Universal Music Deutschland
 - **Unistra**
 - **Unity**: (**Currently broken**)
 - **uol.com.br**
 - **uplynk**
 - **uplynk:preplay**
 - **Urort**: NRK P3 Urørt (**Currently broken**)
 - **URPlay**
 - **USANetwork**
 - **USAToday**
 - **ustream**
 - **ustream:channel**
 - **ustudio**
 - **ustudio:embed**
 - **Varzesh3**: (**Currently broken**)
 - **Vbox7**
 - **Veo**
 - **Vesti**: Вести.Ru (**Currently broken**)
 - **Vevo**
 - **VevoPlaylist**
 - **VGTV**: VGTV, BTTV, FTV, Aftenposten and Aftonbladet
 - **vh1.com**
 - **vhx:embed**: [*vimeo*](## "netrc machine")
 - **vice**: (**Currently broken**)
 - **vice:article**: (**Currently broken**)
 - **vice:show**: (**Currently broken**)
 - **Viddler**
 - **Videa**
 - **video.arnes.si**: Arnes Video
 - **video.google:search**: Google Video search; "gvsearch:" prefix
 - **video.sky.it**
 - **video.sky.it:live**
 - **VideoDetective**
 - **videofy.me**: (**Currently broken**)
 - **VideoKen**
 - **VideoKenCategory**
 - **VideoKenPlayer**
 - **VideoKenPlaylist**
 - **VideoKenTopic**
 - **videomore**
 - **videomore:season**
 - **videomore:video**
 - **VideoPress**
 - **Vidflex**
 - **Vidio**: [*vidio*](## "netrc machine")
 - **VidioLive**: [*vidio*](## "netrc machine")
 - **VidioPremier**: [*vidio*](## "netrc machine")
 - **VidLii**
 - **Vidly**
 - **vids.io**
 - **Vidyard**
 - **viewlift**
 - **viewlift:embed**
 - **Viidea**
 - **vimeo**: [*vimeo*](## "netrc machine")
 - **vimeo:album**: [*vimeo*](## "netrc machine")
 - **vimeo:channel**: [*vimeo*](## "netrc machine")
 - **vimeo:event**: [*vimeo*](## "netrc machine")
 - **vimeo:group**: [*vimeo*](## "netrc machine")
 - **vimeo:likes**: [*vimeo*](## "netrc machine") Vimeo user likes
 - **vimeo:ondemand**: [*vimeo*](## "netrc machine")
 - **vimeo:pro**: [*vimeo*](## "netrc machine")
 - **vimeo:review**: [*vimeo*](## "netrc machine") Review pages on vimeo
 - **vimeo:user**: [*vimeo*](## "netrc machine")
 - **vimeo:watchlater**: [*vimeo*](## "netrc machine") Vimeo watch later list, ":vimeowatchlater" keyword (requires authentication)
 - **Vimm:recording**
 - **Vimm:stream**
 - **ViMP**
 - **ViMP:Playlist**
 - **Viously**
 - **Viqeo**: (**Currently broken**)
 - **Viu**
 - **viu:ott**: [*viu*](## "netrc machine")
 - **viu:playlist**
 - **ViuOTTIndonesia**
 - **vk**: [*vk*](## "netrc machine") VK
 - **vk:uservideos**: [*vk*](## "netrc machine") VK - User's Videos
 - **vk:wallpost**: [*vk*](## "netrc machine")
 - **VKPlay**
 - **VKPlayLive**
 - **vm.tiktok**
 - **Vocaroo**
 - **VODPl**
 - **VODPlatform**
 - **voicy**: (**Currently broken**)
 - **voicy:channel**: (**Currently broken**)
 - **VolejTV**
 - **VoxMedia**
 - **VoxMediaVolume**
 - **vpro**: npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl
 - **vqq:series**
 - **vqq:video**
 - **vrsquare**: VR SQUARE
 - **vrsquare:channel**
 - **vrsquare:search**
 - **vrsquare:section**
 - **VRT**: VRT NWS, Flanders News, Flandern Info and Sporza
 - **vrtmax**: [*vrtnu*](## "netrc machine") VRT MAX (formerly VRT NU)
 - **VTM**: (**Currently broken**)
 - **VTV**
 - **VTVGo**
 - **VTXTV**: [*vtxtv*](## "netrc machine")
 - **VTXTVLive**: [*vtxtv*](## "netrc machine")
 - **VTXTVRecordings**: [*vtxtv*](## "netrc machine")
 - **VuClip**
 - **VVVVID**
 - **VVVVIDShow**
 - **Walla**
 - **WalyTV**: [*walytv*](## "netrc machine")
 - **WalyTVLive**: [*walytv*](## "netrc machine")
 - **WalyTVRecordings**: [*walytv*](## "netrc machine")
 - **washingtonpost**
 - **washingtonpost:article**
 - **wat.tv**
 - **WatchESPN**
 - **WDR**
 - **wdr:mobile**: (**Currently broken**)
 - **WDRElefant**
 - **WDRPage**
 - **web.archive:youtube**: web.archive.org saved youtube videos, "ytarchive:" prefix
 - **Webcamerapl**
 - **Webcaster**
 - **WebcasterFeed**
 - **WebOfStories**
 - **WebOfStoriesPlaylist**
 - **Weibo**
 - **WeiboUser**
 - **WeiboVideo**
 - **WeiqiTV**: WQTV (**Currently broken**)
 - **wetv:episode**
 - **WeTvSeries**
 - **Weverse**: [*weverse*](## "netrc machine")
 - **WeverseLive**: [*weverse*](## "netrc machine")
 - **WeverseLiveTab**: [*weverse*](## "netrc machine")
 - **WeverseMedia**: [*weverse*](## "netrc machine")
 - **WeverseMediaTab**: [*weverse*](## "netrc machine")
 - **WeverseMoment**: [*weverse*](## "netrc machine")
 - **WeVidi**
 - **Weyyak**
 - **whowatch**
 - **Whyp**
 - **wikimedia.org**
 - **Wimbledon**
 - **WimTV**
 - **WinSportsVideo**
 - **Wistia**
 - **WistiaChannel**
 - **WistiaPlaylist**
 - **wnl**: npo.nl, ntr.nl, omroepwnl.nl, zapp.nl and npo3.nl
 - **wordpress:mb.miniAudioPlayer**
 - **wordpress:playlist**
 - **WorldStarHipHop**
 - **wppilot**
 - **wppilot:channels**
 - **WrestleUniversePPV**: [*wrestleuniverse*](## "netrc machine")
 - **WrestleUniverseVOD**: [*wrestleuniverse*](## "netrc machine")
 - **WSJ**: Wall Street Journal
 - **WSJArticle**
 - **WWE**
 - **wyborcza:video**
 - **WyborczaPodcast**
 - **wykop:dig**
 - **wykop:​dig:comment**
 - **wykop:post**
 - **wykop:​post:comment**
 - **Xanimu**
 - **XboxClips**
 - **XHamster**
 - **XHamsterEmbed**
 - **XHamsterUser**
 - **XiaoHongShu**: 小红书
 - **ximalaya**: 喜马拉雅FM
 - **ximalaya:album**: 喜马拉雅FM 专辑
 - **Xinpianchang**: 新片场
 - **XMinus**: (**Currently broken**)
 - **XNXX**
 - **Xstream**
 - **XVideos**
 - **xvideos:quickies**
 - **XXXYMovies**
 - **Yahoo**: Yahoo screen and movies
 - **yahoo:japannews**: Yahoo! Japan News
 - **YandexDisk**
 - **yandexmusic:album**: Яндекс.Музыка - Альбом
 - **yandexmusic:​artist:albums**: Яндекс.Музыка - Артист - Альбомы
 - **yandexmusic:​artist:tracks**: Яндекс.Музыка - Артист - Треки
 - **yandexmusic:playlist**: Яндекс.Музыка - Плейлист
 - **yandexmusic:track**: Яндекс.Музыка - Трек
 - **YandexVideo**
 - **YandexVideoPreview**
 - **YapFiles**: (**Currently broken**)
 - **Yappy**: (**Currently broken**)
 - **YappyProfile**
 - **YleAreena**
 - **YouJizz**
 - **youku**: 优酷
 - **youku:show**
 - **YouNowChannel**
 - **YouNowLive**
 - **YouNowMoment**
 - **YouPorn**
 - **YouPornCategory**: YouPorn category, with sorting, filtering and pagination
 - **YouPornChannel**: YouPorn channel, with sorting and pagination
 - **YouPornCollection**: YouPorn collection (user playlist), with sorting and pagination
 - **YouPornStar**: YouPorn Pornstar, with description, sorting and pagination
 - **YouPornTag**: YouPorn tag (porntags), with sorting, filtering and pagination
 - **YouPornVideos**: YouPorn video (browse) playlists, with sorting, filtering and pagination
 - **youtube**: [*youtube*](## "netrc machine") YouTube
 - **youtube:clip**: [*youtube*](## "netrc machine")
 - **youtube:favorites**: [*youtube*](## "netrc machine") YouTube liked videos; ":ytfav" keyword (requires cookies)
 - **youtube:history**: [*youtube*](## "netrc machine") Youtube watch history; ":ythis" keyword (requires cookies)
 - **youtube:​music:search_url**: [*youtube*](## "netrc machine") YouTube music search URLs with selectable sections, e.g. #songs
 - **youtube:notif**: [*youtube*](## "netrc machine") YouTube notifications; ":ytnotif" keyword (requires cookies)
 - **youtube:playlist**: [*youtube*](## "netrc machine") YouTube playlists
 - **youtube:recommended**: [*youtube*](## "netrc machine") YouTube recommended videos; ":ytrec" keyword
 - **youtube:search**: [*youtube*](## "netrc machine") YouTube search; "ytsearch:" prefix
 - **youtube:​search:date**: [*youtube*](## "netrc machine") YouTube search, newest videos first; "ytsearchdate:" prefix
 - **youtube:search_url**: [*youtube*](## "netrc machine") YouTube search URLs with sorting and filter support
 - **youtube:​shorts:pivot:audio**: [*youtube*](## "netrc machine") YouTube Shorts audio pivot (Shorts using audio of a given video)
 - **youtube:subscriptions**: [*youtube*](## "netrc machine") YouTube subscriptions feed; ":ytsubs" keyword (requires cookies)
 - **youtube:tab**: [*youtube*](## "netrc machine") YouTube Tabs
 - **youtube:user**: [*youtube*](## "netrc machine") YouTube user videos; "ytuser:" prefix
 - **youtube:watchlater**: [*youtube*](## "netrc machine") Youtube watch later list; ":ytwatchlater" keyword (requires cookies)
 - **YoutubeLivestreamEmbed**: [*youtube*](## "netrc machine") YouTube livestream embeds
 - **YoutubeYtBe**: [*youtube*](## "netrc machine") youtu.be
 - **Zaiko**
 - **ZaikoETicket**
 - **Zapiks**
 - **Zattoo**: [*zattoo*](## "netrc machine")
 - **ZattooLive**: [*zattoo*](## "netrc machine")
 - **ZattooMovies**: [*zattoo*](## "netrc machine")
 - **ZattooRecordings**: [*zattoo*](## "netrc machine")
 - **zdf**
 - **zdf:channel**
 - **Zee5**: [*zee5*](## "netrc machine")
 - **zee5:series**
 - **ZeeNews**: (**Currently broken**)
 - **ZenPorn**
 - **ZetlandDKArticle**
 - **Zhihu**
 - **zingmp3**: zingmp3.vn
 - **zingmp3:album**
 - **zingmp3:chart-home**
 - **zingmp3:chart-music-video**
 - **zingmp3:hub**
 - **zingmp3:liveradio**
 - **zingmp3:podcast**
 - **zingmp3:podcast-episode**
 - **zingmp3:user**
 - **zingmp3:week-chart**
 - **zoom**
 - **Zype**
 - **generic**: Generic downloader that works on some sites
    """)

# --- Version information ---
st.markdown("""
<div style="position: fixed; bottom: 10px; left: 10px; background: rgba(0, 0, 0, 0.7); padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; color: #888;">
    v2.0.0 | Enhanced UI
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
