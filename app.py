import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 (手機優化) ---
st.set_page_config(
    page_title="全能影片下載器 V3",
    page_icon="⬇️",
    layout="centered"
)

# --- 常數設定 ---
CONFIG_FILE = "api_key_config.json"
TEMP_DIR = "mobile_downloads"

# --- 初始化 Session State ---
if 'downloaded_file' not in st.session_state:
    st.session_state['downloaded_file'] = None
if 'file_name' not in st.session_state:
    st.session_state['file_name'] = None

# --- 工具函式 ---
def safe_clean_temp_dir():
    """清理暫存資料夾"""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            pass
    os.makedirs(TEMP_DIR, exist_ok=True)

# --- API Key 管理函式 ---
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
def download_video(url, cookie_path=None):
    """下載影片並回傳路徑 (支援 FB/IG/YT/Threads)"""
    safe_clean_temp_dir()
    
    timestamp = int(time.time())
    # 設定通用輸出檔名
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 偽裝成 iPhone (有助於 FB/IG 手機版連結解析)
    user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # 嘗試下載最佳畫質
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    # 掛載 Cookies (解決 FB/IG 登入限制)
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        return None, str(e)

# --- 主程式介面 ---
def main():
    st.title("⬇️ 全能影片下載器 V3")
    st.caption("支援：Facebook / YouTube / Instagram / Threads")

    # --- 側邊欄：設定與 Cookies ---
    with st.sidebar:
        st.header("⚙️ 設定")
        
        # 1. API Key
        api_key_input = st.text_input(
            "Gemini API Key", 
            type="password", 
            value=st.session_state['user_api_key'],
            key="api_key_widget"
        )
        if api_key_input != st.session_state['user_api_key']:
            st.session_state['user_api_key'] = api_key_input
            
        c1, c2 = st.columns(2)
        if c1.button("💾 存 Key"): save_api_key_to_file(api_key_input)
        if c2.button("❌ 刪 Key"): 
            remove_saved_api_key()
            st.session_state['user_api_key'] = ""
            st.rerun()

        st.divider()

        # 2. Cookies 上傳 (防擋神器)
        st.subheader("🍪 萬能解鎖 (Cookies)")
        st.info("若 FB/IG 下載失敗 (顯示 Login required)，請在此上傳 cookies.txt")
        uploaded_cookies = st.file_uploader("上傳 cookies.txt", type=["txt"])
        
    # --- 處理 Cookies ---
    cookie_temp_path = None
    if uploaded_cookies:
        safe_clean_temp_dir() # 清理舊檔
        cookie_temp_path = os.path.join(TEMP_DIR, "cookies.txt")
        with open(cookie_temp_path, "wb") as f:
            f.write(uploaded_cookies.getbuffer())
        st.sidebar.success("✅ Cookies 已掛載！")

    # --- 主要下載區 ---
    st.divider()
    url = st.text_input("貼上影片連結", placeholder="支援 FB, IG, YT, Threads...")

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not url:
            st.warning("請先輸入網址")
        else:
            with st.status("🚀 正在處理中 (雲端主機連線中)...", expanded=True) as status:
                
                file_path, result_msg = download_video(url, cookie_temp_path)
                
                if file_path and os.path.exists(file_path):
                    status.write("✅ 下載成功！")
                    st.session_state['downloaded_file'] = file_path
                    
                    # 檔名淨化
                    safe_title = "".join([c for c in str(result_msg) if c.isalpha() or c.isdigit() or c==' ']).strip()
                    if not safe_title: safe_title = "download_video"
                    st.session_state['file_name'] = f"{safe_title}.mp4"
                    
                    status.update(label="完成！請點擊下方按鈕儲存", state="complete")
                else:
                    status.update(label="下載失敗", state="error")
                    st.error(f"❌ 錯誤: {result_msg}")
                    # 針對常見錯誤給提示
                    err_str = str(result_msg).lower()
                    if "login required" in err_str or "sign in" in err_str:
                        st.warning("💡 **需要登入**：請使用側邊欄的 Cookies 功能上傳檔案來解決。")
                    elif "facebook" in err_str and "content is not available" in err_str:
                        st.warning("💡 **FB 私人影片**：這部影片可能是設為好友限動或私人社團，無法公開下載。")

    # --- 下載按鈕 ---
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
