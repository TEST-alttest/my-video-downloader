import streamlit as st
import yt_dlp
import os
import time
import json

st.set_page_config(page_title="全能下載器 V20.0", page_icon="🦄", layout="centered")

# --- 核心除錯顯示 ---
st.title("🦄 全能下載器 V20.0")

# 獲取引擎版本
try:
    ver = yt_dlp.version.__version__
except:
    ver = "未知"

# 判斷版本是否合格 (2024.11.04 以後才支援 Threads 較好)
if ver.startswith("2024") or ver.startswith("2025"):
    st.success(f"✅ 下載引擎版本正常：{ver}")
else:
    st.error(f"❌ 下載引擎版本過舊：{ver}")
    st.info("請務必去 GitHub 修改 requirements.txt 為：\n`yt-dlp>=2024.11.04`")

# --- 常數與設定 ---
CONFIG_FILE = "api_key_config.json"
TEMP_DIR = "mobile_downloads"
IG_COOKIE_FILE = os.path.join(TEMP_DIR, "ig_cookies.txt")
FB_COOKIE_FILE = os.path.join(TEMP_DIR, "fb_cookies.txt")

if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

# --- 側邊欄 ---
with st.sidebar:
    st.header("設定")
    if "GEMINI_API_KEY" in st.secrets: st.success("🔒 雲端 Key 使用中")
    
    st.divider()
    ig_file = st.file_uploader("IG Cookies", type=["txt"])
    if ig_file:
        with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
        st.success("IG Cookies 更新")
        
    fb_file = st.file_uploader("FB Cookies", type=["txt"])
    if fb_file:
        with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
        st.success("FB Cookies 更新")

# --- 下載邏輯 ---
def download_video(url, use_cookies=True):
    # 簡易版下載邏輯，專注於成功率
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'}
    }
    
    # 掛載 Cookies
    if use_cookies:
        if "threads" in url or "instagram" in url:
            if os.path.exists(IG_COOKIE_FILE): ydl_opts['cookiefile'] = IG_COOKIE_FILE
        elif "facebook" in url or "fb.watch" in url:
            if os.path.exists(FB_COOKIE_FILE): ydl_opts['cookiefile'] = FB_COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'video'), None
    except Exception as e:
        return None, None, str(e)

# --- 主畫面 ---
raw_url = st.text_input("貼上影片連結")
if st.button("解析並下載", type="primary", use_container_width=True):
    if not raw_url:
        st.warning("請輸入網址")
    else:
        # 自動修正網址
        real_url = raw_url.strip()
        if "threads.com" in real_url: real_url = real_url.replace("threads.com", "threads.net")
        if "threads.net" in real_url and "?" in real_url: real_url = real_url.split("?")[0]
        
        st.caption(f"目標網址: {real_url}")
        
        with st.status("執行中...", expanded=True) as status:
            path, title, err = download_video(real_url)
            
            if path and os.path.exists(path):
                status.write("✅ 成功！")
                st.session_state['file_path'] = path
                status.update(label="完成", state="complete")
            else:
                status.update(label="失敗", state="error")
                st.error("下載失敗")
                st.code(err)

if 'file_path' in st.session_state and st.session_state['file_path'] and os.path.exists(st.session_state['file_path']):
    with open(st.session_state['file_path'], "rb") as f:
        st.download_button("📥 儲存影片", f, file_name="video.mp4", mime="video/mp4", use_container_width=True, type="primary")
