import streamlit as st
import yt_dlp
import os
import shutil
import json
import time
import subprocess
import sys

# --- V19.0 強制依賴更新 (確保引擎支援 API 模式) ---
if 'dep_installed' not in st.session_state:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except: pass
    st.session_state['dep_installed'] = True

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V19.0", page_icon="🦄", layout="centered")

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

# --- 🔥 V19.0 核心：Cookie 權限修正 + iOS API 模式 🔥 ---
def patch_cookies_for_threads(cookie_path):
    # 確保 Cookie 檔案同時擁有 IG 和 Threads 的權限宣告
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 簡單粗暴：如果裡面沒有 threads.net，就把 instagram.com 全部複製一份改成 threads.net 加上去
        if ".threads.net" not in content and ".instagram.com" in content:
            new_content = content + "\n" + content.replace(".instagram.com", ".threads.net")
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except: return False
    return False

def download_video(raw_url, use_cookies=True):
    safe_clean_temp_dir()
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 1. 強制網址修正
    final_url = raw_url.strip()
    if "threads.com" in final_url: final_url = final_url.replace("threads.com", "threads.net")
    if "threads.net" in final_url and "?" in final_url: final_url = final_url.split("?")[0]

    # 2. V19 關鍵設定：強制使用 iOS API 介面 (徹底避開網頁轉址)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'instagram': {
                'api_host': ['ios'],   # 強制走 iOS API
                'imp_seed': ['yes']
            }
        },
        'http_headers': {
            'User-Agent': 'Instagram 219.0.0.12.117 (iPhone13,4; iOS 14_4; en_US; en-US; scale=3.00; 1284x2778; 352306745)',
            'Accept-Language': 'en-US',
        }
    }

    cookie_to_use = None
    if use_cookies:
        if "instagram.com" in final_url.lower() or "threads.net" in final_url.lower():
            if os.path.exists(IG_COOKIE_FILE):
                patch_cookies_for_threads(IG_COOKIE_FILE)
                cookie_to_use = IG_COOKIE_FILE
        elif "facebook.com" in final_url.lower() or "fb.watch" in final_url.lower():
            if os.path.exists(FB_COOKIE_FILE): cookie_to_use = FB_COOKIE_FILE
        
        if cookie_to_use: ydl_opts['cookiefile'] = cookie_to_use

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(final_url, download=True)
            return ydl.prepare_filename(info), info.get('title', 'video'), cookie_to_use, None
    except Exception as e:
        return None, "下載失敗", cookie_to_use, str(e)

# --- 主介面 ---
def main():
    st.title("🦄 全能下載器 V19.0")
    st.caption("iOS API 強力模式 (防轉址)")

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

    with st.sidebar:
        st.header("⚙️ 設定")
        if "GEMINI_API_KEY" in st.secrets: st.success("🔒 雲端 Key 使用中")
        else:
            k = st.text_input("API Key", type="password", value=st.session_state['user_api_key'])
            if st.button("💾"): save_api_key(k)
        
        st.divider()
        ig_file = st.file_uploader("IG Cookies (通用)", type=["txt"], key="ig_uploader")
        if ig_file is not None:
            with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
            patch_cookies_for_threads(IG_COOKIE_FILE)
            st.success("✅ IG/Threads 憑證已優化")

        fb_file = st.file_uploader("FB Cookies", type=["txt"], key="fb_uploader")
        if fb_file is not None:
            with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
            st.success("✅ FB Cookies 更新成功")
            
        if os.path.exists(IG_COOKIE_FILE): st.caption("✅ IG 憑證: OK")
        
        try: st.caption(f"Engine Ver: {yt_dlp.version.__version__}")
        except: pass

    st.divider()
    
    input_url = st.text_input("貼上影片連結")
    use_cookies_toggle = st.checkbox("🍪 掛載 Cookies (必選)", value=True)

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not input_url:
            st.warning("請輸入網址")
        else:
            with st.status("🚀 正在呼叫 iOS API 下載...", expanded=True) as status:
                path, title, cookie, err_msg = download_video(input_url, use_cookies=use_cookies_toggle)
                
                if path and os.path.exists(path):
                    status.write("✅ 成功！")
                    st.session_state['downloaded_file'] = path
                    safe_name = "".join([c for c in str(title) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    st.session_state['file_name'] = f"{safe_name or 'video'}.mp4"
                    status.update(label="完成", state="complete")
                else:
                    status.update(label="失敗", state="error")
                    st.error("❌ 下載失敗")
                    with st.expander("錯誤詳情"):
                        st.code(err_msg, language="text")

    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        with open(st.session_state['downloaded_file'], "rb") as f:
            st.download_button("📥 儲存影片", f, file_name=st.session_state['file_name'], mime="video/mp4", use_container_width=True, type="primary")

if __name__ == "__main__":
    main()
