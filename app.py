import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 ---
st.set_page_config(
    page_title="全能影片下載器 V7.0",
    page_icon="⬇️",
    layout="centered"
)

# --- 常數設定 ---
CONFIG_FILE = "api_key_config.json"
TEMP_DIR = "mobile_downloads"
IG_COOKIE_FILE = os.path.join(TEMP_DIR, "ig_cookies.txt")
FB_COOKIE_FILE = os.path.join(TEMP_DIR, "fb_cookies.txt")

# --- 初始化 Session State ---
if 'downloaded_file' not in st.session_state:
    st.session_state['downloaded_file'] = None
if 'file_name' not in st.session_state:
    st.session_state['file_name'] = None

# --- 工具函式 ---
def safe_clean_temp_dir():
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)
        return
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        if filename.endswith(".mp4") or filename.endswith(".webm"):
            try: os.remove(file_path)
            except: pass

# --- API Key 管理 ---
def load_api_key():
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("api_key", "")
        except: return ""
    return ""

def save_api_key_to_file(key):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_key": key}, f)
        st.toast("✅ Key 已暫存", icon="💾")
    except Exception as e:
        st.error(f"儲存失敗: {e}")

if 'user_api_key' not in st.session_state:
    st.session_state['user_api_key'] = load_api_key()

# --- 下載核心函式 (強制修正邏輯移入此處) ---
def download_video(url):
    safe_clean_temp_dir()
    
    # 🔥 V7.0 雙重保險：不管外面有沒有改，這裡強制再改一次 🔥
    if "threads.com" in url:
        url = url.replace("threads.com", "threads.net")
        print(f"Inside downloader: Auto-corrected to {url}")

    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 使用電腦版 User-Agent 以匹配電腦版 Cookies
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    # 智慧 Cookies
    cookie_to_use = None
    url_lower = url.lower()
    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        if os.path.exists(FB_COOKIE_FILE): cookie_to_use = FB_COOKIE_FILE
    elif "instagram.com" in url_lower or "threads.net" in url_lower:
        if os.path.exists(IG_COOKIE_FILE): cookie_to_use = IG_COOKIE_FILE
    
    if cookie_to_use: ydl_opts['cookiefile'] = cookie_to_use

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 這裡顯示實際下載的 URL，方便除錯
            st.toast(f"正在嘗試下載：{url}", icon="🕵️")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video'), cookie_to_use
    except Exception as e:
        return None, str(e), cookie_to_use

# --- 主程式介面 ---
def main():
    st.title("⬇️ 全能影片下載器 V7.0")
    st.caption("雙重防呆 + 環境診斷版")

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

    with st.sidebar:
        st.header("⚙️ 設定")
        if "GEMINI_API_KEY" in st.secrets:
            st.success("🔒 已使用雲端 Secrets Key")
            st.session_state['user_api_key'] = st.secrets["GEMINI_API_KEY"]
        else:
            api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state['user_api_key'])
            if st.button("💾 暫存 Key"): save_api_key_to_file(api_key_input)
        
        st.divider()
        st.header("🍪 雙平台解鎖")
        
        st.caption("📱 **Instagram / Threads**")
        ig_file = st.file_uploader("上傳 IG cookies.txt", type=["txt"], key="ig_uploader")
        if ig_file:
            with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
            st.success("✅ IG Cookies 已更新")
            
        st.caption("📘 **Facebook**")
        fb_file = st.file_uploader("上傳 FB cookies.txt", type=["txt"], key="fb_uploader")
        if fb_file:
            with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
            st.success("✅ FB Cookies 已更新")
            
        st.divider()
        st.caption("環境狀態：")
        st.markdown(f"🟢 IG 驗證檔：{'**已就緒**' if os.path.exists(IG_COOKIE_FILE) else '未上傳'}")
        st.markdown(f"🟢 FB 驗證檔：{'**已就緒**' if os.path.exists(FB_COOKIE_FILE) else '未上傳'}")
        
        # 顯示 yt-dlp 版本，確認 requirements.txt 是否生效
        try:
            version = yt_dlp.version.__version__
            st.caption(f"Engine Ver: {version}")
        except:
            st.caption("Engine Ver: Unknown")

    st.divider()
    
    # 這裡只負責接收輸入，不負責修正，修正交給下載核心
    input_url = st.text_input("貼上影片連結", placeholder="請貼上網址...")
    
    # 介面顯示修正提示
    if input_url and "threads.com" in input_url:
        st.info(f"🔧 偵測到 threads.com，系統將在下載時自動修正為 .net")

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not input_url:
            st.warning("請先輸入網址")
        else:
            with st.status(f"🚀 啟動下載引擎...", expanded=True) as status:
                # 直接傳入原始網址，讓 download_video 內部去改
                file_path, result_msg, used_cookie = download_video(input_url)
                
                if file_path and os.path.exists(file_path):
                    status.write("✅ 下載成功！")
                    if used_cookie: status.write(f"ℹ️ 使用驗證檔：{'IG' if 'ig' in used_cookie else 'FB'}")
                    
                    st.session_state['downloaded_file'] = file_path
                    safe_title = "".join([c for c in str(result_msg) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    if not safe_title: safe_title = "video_download"
                    st.session_state['file_name'] = f"{safe_title}.mp4"
                    status.update(label="完成！", state="complete")
                else:
                    status.update(label="下載失敗", state="error")
                    st.error(f"❌ 錯誤訊息: {result_msg}")
                    
                    err_str = str(result_msg).lower()
                    if "unsupported url" in err_str:
                         st.error("💡 嚴重錯誤：網址無法識別。請確認 requirements.txt 內的 yt-dlp 已更新到最新版。")
                    elif "login required" in err_str:
                        st.warning("💡 需要登入：網址正確，但被 IG 擋住了。請重新上傳 Cookies (需用電腦版 Chrome 下載，且不可登出)。")

    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        with open(st.session_state['downloaded_file'], "rb") as file:
            st.download_button(
                label="📥 儲存影片到手機",
                data=file,
                file_name=st.session_state['file_name'],
                mime="video/mp4",
                use_container_width=True,
                type="primary"
            )

if __name__ == "__main__":
    main()
