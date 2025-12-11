import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V9.0", page_icon="⬇️", layout="centered")

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
def download_video(url, use_cookies=True):
    safe_clean_temp_dir()
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # V9.0: 訪客模式使用更像真實瀏覽器的 User-Agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {'User-Agent': user_agent, 'Accept-Language': 'en-US,en;q=0.9'}
    }

    cookie_to_use = None
    # 只有當 use_cookies 為 True 時才掛載
    if use_cookies:
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
    st.title("⬇️ 全能下載器 V9.0")
    st.caption("訪客模式 + 餅乾診斷")

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

    with st.sidebar:
        st.header("⚙️ 設定")
        if "GEMINI_API_KEY" in st.secrets: st.success("🔒 雲端 Key 使用中")
        else:
            k = st.text_input("API Key", type="password", value=st.session_state['user_api_key'])
            if st.button("💾"): save_api_key(k)
        
        st.divider()
        st.header("🍪 餅乾管理")
        
        # 顯示餅乾診斷資訊
        if os.path.exists(IG_COOKIE_FILE):
            with open(IG_COOKIE_FILE, 'r', errors='ignore') as f:
                first_line = f.readline().strip()
            if "# Netscape" in first_line or len(first_line) > 0:
                st.success(f"IG 檔格式看來正常\n({first_line[:20]}...)")
            else:
                st.error("IG 檔格式可能錯誤 (內容為空或亂碼)")
        
        ig_file = st.file_uploader("IG Cookies", type=["txt"], key="ig_uploader")
        if ig_file is not None:
            with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
            st.rerun()

        fb_file = st.file_uploader("FB Cookies", type=["txt"], key="fb_uploader")
        if fb_file is not None:
            with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
            st.rerun()
        
        try: st.caption(f"Engine: {yt_dlp.version.__version__}")
        except: pass

    st.divider()
    
    # --- 核心邏輯 ---
    raw_url = st.text_input("貼上影片連結")
    
    real_url = raw_url.strip()
    if "threads.com" in real_url:
        real_url = real_url.replace("threads.com", "threads.net")
        st.info(f"🔧 已強制修正為 .net")
    
    # 🔥 V9.0 新功能：訪客模式開關 🔥
    use_cookies_toggle = st.checkbox("🍪 使用 Cookies 下載 (若失敗請取消勾選)", value=True)

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not real_url:
            st.warning("請輸入網址")
        else:
            with st.status("🚀 下載中...", expanded=True) as status:
                # 傳入 use_cookies 參數
                path, msg, cookie = download_video(real_url, use_cookies=use_cookies_toggle)
                
                if path and os.path.exists(path):
                    status.write("✅ 成功！")
                    if cookie: status.write(f"ℹ️ 使用驗證檔：{'IG' if 'ig' in cookie else 'FB'}")
                    else: status.write("ℹ️ 使用訪客模式 (無 Cookies)")
                    
                    st.session_state['downloaded_file'] = path
                    safe_name = "".join([c for c in str(msg) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    st.session_state['file_name'] = f"{safe_name or 'video'}.mp4"
                    status.update(label="完成", state="complete")
                else:
                    status.update(label="失敗", state="error")
                    st.error(f"❌ 錯誤: {msg}")
                    
                    # 智慧提示
                    if "unsupported url" in str(msg).lower():
                        st.warning("💡 提示：你的 Cookies 可能被 IG 阻擋了。請嘗試 **取消勾選** 上方的「使用 Cookies」再試一次。")

    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        with open(st.session_state['downloaded_file'], "rb") as f:
            st.download_button("📥 儲存影片", f, file_name=st.session_state['file_name'], mime="video/mp4", use_container_width=True, type="primary")

if __name__ == "__main__":
    main()
