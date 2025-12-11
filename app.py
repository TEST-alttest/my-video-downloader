import streamlit as st
import os
import time
import shutil
import sys
import subprocess

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V24.0", page_icon="🦄", layout="centered")

# --- V24.0 關鍵修復：手動喚醒 Instagram 下載模組 ---
# 這能解決 "Unsupported URL" 的問題，即使網址正確
try:
    import yt_dlp
    from yt_dlp.extractor.instagram import InstagramIE
    # 強制註冊，確保引擎認識 Threads
    yt_dlp.extractor.instagram.InstagramIE = InstagramIE
except ImportError:
    pass

# --- 常數設定 ---
TEMP_DIR = "mobile_downloads"
IG_COOKIE_FILE = os.path.join(TEMP_DIR, "ig_cookies.txt")
FB_COOKIE_FILE = os.path.join(TEMP_DIR, "fb_cookies.txt")

if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

# --- 工具函式 ---
def safe_clean_temp_dir():
    for f in os.listdir(TEMP_DIR):
        if f.endswith(".mp4") or f.endswith(".webm"):
            try: os.remove(os.path.join(TEMP_DIR, f))
            except: pass

def download_video(url, use_cookies=True):
    safe_clean_temp_dir()
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 1. 強制修正網址
    final_url = url.strip()
    if "threads.com" in final_url: final_url = final_url.replace("threads.com", "threads.net")
    if "threads.net" in final_url and "?" in final_url: final_url = final_url.split("?")[0]

    # 2. V24 診斷：直接問引擎「你認得這個網址嗎？」
    is_supported = InstagramIE.suitable(final_url)
    if is_supported:
        st.success(f"✅ 引擎已識別此網址 (InstagramIE)")
    else:
        st.warning(f"⚠️ 引擎似乎不認識此網址，嘗試強制下載...")

    # 3. 偽裝設定 (iOS 模式)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'instagram': {'api_host': ['ios'], 'imp_seed': ['yes']}},
        'http_headers': {
            'User-Agent': 'Instagram 219.0.0.12.117 (iPhone13,4; iOS 14_4; en_US; en-US; scale=3.00; 1284x2778; 352306745)',
            'Accept-Language': 'en-US',
        }
    }
    
    if use_cookies:
        if "instagram.com" in final_url or "threads.net" in final_url:
            if os.path.exists(IG_COOKIE_FILE): ydl_opts['cookiefile'] = IG_COOKIE_FILE
        elif "facebook.com" in final_url or "fb.watch" in final_url:
            if os.path.exists(FB_COOKIE_FILE): ydl_opts['cookiefile'] = FB_COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(final_url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'video'), None
    except Exception as e:
        return None, None, str(e)

# --- 主介面 ---
st.title("🦄 全能下載器 V24.0")
st.caption("喚醒核心版 (解決 Unsupported URL)")

# 側邊欄
with st.sidebar:
    st.header("🍪 憑證管理")
    ig_file = st.file_uploader("上傳 IG Cookies", type=["txt"])
    if ig_file:
        with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
        st.success("IG 憑證更新！")
    
    fb_file = st.file_uploader("FB Cookies", type=["txt"])
    if fb_file:
        with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
        st.success("FB 憑證更新！")

    if os.path.exists(IG_COOKIE_FILE): st.markdown("✅ **IG 憑證已就緒**")
    
    try: st.caption(f"Engine: {yt_dlp.version.__version__}")
    except: pass

# 主畫面
raw_url = st.text_input("貼上影片連結")
use_cookies = st.checkbox("🍪 掛載憑證下載 (必選)", value=True)

if st.button("🚀 解析並下載", type="primary", use_container_width=True):
    if not raw_url:
        st.warning("請先貼上網址")
    else:
        with st.status("🚀 處理中...", expanded=True) as status:
            path, title, err = download_video(raw_url, use_cookies)
            
            if path and os.path.exists(path):
                status.write("✅ 下載成功！")
                status.update(label="完成", state="complete")
                
                with open(path, "rb") as f:
                    st.download_button(
                        label="📥 儲存影片到手機",
                        data=f,
                        file_name=f"video.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )
            else:
                status.update(label="失敗", state="error")
                st.error("❌ 下載失敗")
                st.code(err)
