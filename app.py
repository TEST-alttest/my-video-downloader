import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 ---
st.set_page_config(
    page_title="全能影片下載器 V4.2",
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
    """只清理舊的影片檔，保留 Cookies 檔案"""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)
        return

    # 刪除舊的 mp4/webm 檔案，但不要刪除 txt (Cookies)
    for filename in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, filename)
        if filename.endswith(".mp4") or filename.endswith(".webm"):
            try:
                os.remove(file_path)
            except:
                pass

# --- API Key 管理 ---
def load_saved_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data.get("api_key", "")
        except:
            return ""
    return ""

def save_api_key_to_file(key):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api_key": key}, f)
        st.toast("✅ API Key 已儲存！", icon="💾")
    except Exception as e:
        st.error(f"儲存失敗: {e}")

def remove_saved_api_key():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    st.toast("🗑️ API Key 已移除。", icon="❌")

if 'user_api_key' not in st.session_state:
    st.session_state['user_api_key'] = load_saved_api_key()

# --- 下載核心函式 ---
def download_video(url):
    """下載影片並智慧選擇 Cookies"""
    safe_clean_temp_dir()
    
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 偽裝成 iPhone
    user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'

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

    # --- 智慧 Cookies 判斷 ---
    cookie_to_use = None
    url_lower = url.lower()

    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        if os.path.exists(FB_COOKIE_FILE):
            cookie_to_use = FB_COOKIE_FILE
    elif "instagram.com" in url_lower or "threads.net" in url_lower:
        if os.path.exists(IG_COOKIE_FILE):
            cookie_to_use = IG_COOKIE_FILE
    
    if cookie_to_use:
        ydl_opts['cookiefile'] = cookie_to_use

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video'), cookie_to_use
    except Exception as e:
        return None, str(e), cookie_to_use

# --- 主程式介面 ---
def main():
    st.title("⬇️ 全能影片下載器 V4.2")
    st.caption("FB / IG / YT / Threads (簡潔版)")

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR, exist_ok=True)

    # --- 側邊欄 ---
    with st.sidebar:
        st.header("⚙️ API 設定")
        api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state['user_api_key'])
        if st.button("💾 儲存 Key"): save_api_key_to_file(api_key_input)
        
        st.divider()

        st.header("🍪 雙平台解鎖")
        st.info("若下載失敗 (Login required)，請上傳 Cookies。")
        
        st.caption("📱 **Instagram / Threads**")
        ig_file = st.file_uploader("上傳 IG cookies.txt", type=["txt"], key="ig_uploader")
        if ig_file:
            with open(IG_COOKIE_FILE, "wb") as f:
                f.write(ig_file.getbuffer())
            st.success("✅ IG Cookies 已更新")
            
        st.caption("📘 **Facebook**")
        fb_file = st.file_uploader("上傳 FB cookies.txt", type=["txt"], key="fb_uploader")
        if fb_file:
            with open(FB_COOKIE_FILE, "wb") as f:
                f.write(fb_file.getbuffer())
            st.success("✅ FB Cookies 已更新")

        st.divider()
        st.caption("目前狀態：")
        if os.path.exists(IG_COOKIE_FILE): st.markdown("🟢 IG 驗證檔：**已就緒**")
        else: st.markdown("🔴 IG 驗證檔：未上傳")
        
        if os.path.exists(FB_COOKIE_FILE): st.markdown("🟢 FB 驗證檔：**已就緒**")
        else: st.markdown("🔴 FB 驗證檔：未上傳")

    # --- 主要下載區 ---
    st.divider()
    url = st.text_input("貼上影片連結", placeholder="FB, IG, Threads, YouTube...")

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not url:
            st.warning("請先輸入網址")
        else:
            with st.status("🚀 處理中...", expanded=True) as status:
                file_path, result_msg, used_cookie = download_video(url)
                
                if file_path and os.path.exists(file_path):
                    status.write("✅ 下載成功！")
                    if used_cookie:
                        if "ig_cookies" in used_cookie: status.write("ℹ️ 已使用 IG 驗證檔")
                        if "fb_cookies" in used_cookie: status.write("ℹ️ 已使用 FB 驗證檔")
                    
                    st.session_state['downloaded_file'] = file_path
                    safe_title = "".join([c for c in str(result_msg) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    if not safe_title: safe_title = "video_download"
                    st.session_state['file_name'] = f"{safe_title}.mp4"
                    status.update(label="完成！", state="complete")
                else:
                    status.update(label="下載失敗", state="error")
                    st.error(f"❌ 錯誤: {result_msg}")
                    err_str = str(result_msg).lower()
                    if "login required" in err_str:
                        st.warning("💡 請檢查左側是否已上傳對應平台的 Cookies。")

    # --- 僅顯示下載按鈕 ---
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
