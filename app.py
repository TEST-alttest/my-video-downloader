import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V8.1", page_icon="⬇️", layout="centered")

# --- 常數 ---
CONFIG_FILE = "api_key_config.json"
TEMP_DIR = "mobile_downloads"
IG_COOKIE_FILE = os.path.join(TEMP_DIR, "ig_cookies.txt")
FB_COOKIE_FILE = os.path.join(TEMP_DIR, "fb_cookies.txt")

# --- 初始化 ---
if 'downloaded_file' not in st.session_state: st.session_state['downloaded_file'] = None
if 'file_name' not in st.session_state: st.session_state['file_name'] = None

# --- 工具 ---
def safe_clean_temp_dir():
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)
    return
    for f in os.listdir(TEMP_DIR):
        if f.endswith(".mp4") or f.endswith(".webm"):
            try: os.remove(os.path.join(TEMP_DIR, f))
            except: pass

def load_api_key():
    if "GEMINI_API_KEY" in st.secrets: return st.secrets["GEMINI_API_KEY"]
    if os.path.exists(CONFIG_FILE):
        try: return json.load(open(CONFIG_FILE)).get("api_key", "")
        except: return ""
    return ""

def save_api_key(key):
    with open(CONFIG_FILE, "w") as f: json.dump({"api_key": key}, f)
    st.toast("Key 已暫存", icon="💾")

if 'user_api_key' not in st.session_state: st.session_state['user_api_key'] = load_api_key()

# --- 下載核心 ---
def download_video(url):
    safe_clean_temp_dir()
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 偽裝成 Windows 電腦
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': user_agent, 'Accept-Language': 'en-US,en;q=0.9'}
    }

    cookie_to_use = None
    if "facebook.com" in url.lower() or "fb.watch" in url.lower():
        if os.path.exists(FB_COOKIE_FILE): cookie_to_use = FB_COOKIE_FILE
    elif "instagram.com" in url.lower() or "threads.net" in url.lower():
        if os.path.exists(IG_COOKIE_FILE): cookie_to_use = IG_COOKIE_FILE
    
    if cookie_to_use: ydl_opts['cookiefile'] = cookie_to_use

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'video'), cookie_to_use
    except Exception as e:
        return None, str(e), cookie_to_use

# --- 主介面 ---
def main():
    st.title("⬇️ 全能下載器 V8.1")
    st.caption("修復 Cookies 上傳崩潰問題")

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

    with st.sidebar:
        st.header("⚙️ 設定")
        if "GEMINI_API_KEY" in st.secrets: st.success("🔒 雲端 Key 使用中")
        else:
            k = st.text_input("API Key", type="password", value=st.session_state['user_api_key'])
            if st.button("💾"): save_api_key(k)
        
        st.divider()
        st.info("若下載失敗請更新 Cookies")
        
        # 🔥 V8.1 修正：正確處理檔案上傳物件 🔥
        ig_file = st.file_uploader("IG Cookies", type=["txt"], key="ig_uploader")
        if ig_file is not None:
            with open(IG_COOKIE_FILE, "wb") as f: 
                f.write(ig_file.getbuffer())
            st.success("IG Cookies 已更新")

        fb_file = st.file_uploader("FB Cookies", type=["txt"], key="fb_uploader")
        if fb_file is not None:
            with open(FB_COOKIE_FILE, "wb") as f: 
                f.write(fb_file.getbuffer())
            st.success("FB Cookies 已更新")
        
        st.caption(f"IG 檔: {'✅' if os.path.exists(IG_COOKIE_FILE) else '❌'} | FB 檔: {'✅' if os.path.exists(FB_COOKIE_FILE) else '❌'}")
        try: st.caption(f"Engine: {yt_dlp.version.__version__}")
        except: pass

    st.divider()
    
    # --- 核心下載邏輯 ---
    raw_url = st.text_input("貼上影片連結")
    
    real_url = raw_url.strip()
    if "threads.com" in real_url:
        real_url = real_url.replace("threads.com", "threads.net")
        st.info(f"🔧 已強制修正網址為：{real_url}")
    
    if real_url:
        st.code(f"準備下載：{real_url}", language="text")

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not real_url:
            st.warning("請輸入網址")
        else:
            with st.status("🚀 下載中...", expanded=True) as status:
                path, msg, cookie = download_video(real_url)
                
                if path and os.path.exists(path):
                    status.write("✅ 成功！")
                    st.session_state['downloaded_file'] = path
                    safe_name = "".join([c for c in str(msg) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    st.session_state['file_name'] = f"{safe_name or 'video'}.mp4"
                    status.update(label="完成", state="complete")
                else:
                    status.update(label="失敗", state="error")
                    st.error(f"❌ 錯誤: {msg}")
                    if "unsupported url" in str(msg).lower():
                        st.error("💀 嚴重錯誤：請更新 requirements.txt")

    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        with open(st.session_state['downloaded_file'], "rb") as f:
            st.download_button("📥 儲存影片", f, file_name=st.session_state['file_name'], mime="video/mp4", use_container_width=True, type="primary")

if __name__ == "__main__":
    main()
