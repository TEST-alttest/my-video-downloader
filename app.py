import streamlit as st
import yt_dlp
import os
import shutil
import json
import time

# --- 頁面設定 (手機優化) ---
st.set_page_config(
    page_title="影片下載器 (Mobile)",
    page_icon="⬇️",
    layout="centered"  # 手機上 centered 比較好看
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
            print(f"清理失敗: {e}")
    os.makedirs(TEMP_DIR, exist_ok=True)

# --- API Key 管理函式 (保留您的要求) ---
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
    """下載影片並回傳路徑"""
    safe_clean_temp_dir()
    
    # 手機版輸出檔名簡化，方便辨識
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        # 偽裝 User-Agent 避免 IG/Threads 阻擋
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, info.get('title', 'video')
    except Exception as e:
        st.error(f"❌ 下載錯誤: {str(e)}")
        return None, None

# --- 主程式介面 ---

def main():
    st.title("⬇️ 全能影片下載器")
    st.caption("支援 YT Shorts / IG Reels / Threads")

    # --- 側邊欄：API Key 設定 (保留功能) ---
    with st.sidebar:
        st.header("⚙️ 設定")
        st.info("此處僅供儲存 API Key，下載功能不需要 Key 即可運作。")
        
        api_key_input = st.text_input(
            "Gemini API Key", 
            type="password", 
            value=st.session_state['user_api_key'],
            key="api_key_widget"
        )
        
        if api_key_input != st.session_state['user_api_key']:
            st.session_state['user_api_key'] = api_key_input

        col_save, col_clear = st.columns(2)
        with col_save:
            if st.button("💾 儲存 Key", use_container_width=True):
                save_api_key_to_file(api_key_input)
        with col_clear:
            if st.button("❌ 清除 Key", use_container_width=True):
                remove_saved_api_key()
                st.session_state['user_api_key'] = ""
                st.rerun()

    # --- 主要下載區 ---
    st.divider()
    
    url = st.text_input("貼上影片連結", placeholder="https://...")

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not url:
            st.warning("請先輸入網址")
        else:
            with st.status("🚀 正在處理中...", expanded=True) as status:
                status.write("正在連接伺服器...")
                file_path, title = download_video(url)
                
                if file_path and os.path.exists(file_path):
                    status.write("✅ 下載成功！準備檔案中...")
                    st.session_state['downloaded_file'] = file_path
                    # 處理檔名，移除不合法字元
                    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).strip()
                    st.session_state['file_name'] = f"{safe_title}.mp4"
                    status.update(label="完成！請點擊下方按鈕儲存", state="complete")
                else:
                    status.update(label="失敗", state="error")

    # --- 顯示下載按鈕 ---
    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        st.success("影片已準備好！")
        
        # 讀取檔案以供下載
        with open(st.session_state['downloaded_file'], "rb") as file:
            btn = st.download_button(
                label="📥 儲存影片到手機",
                data=file,
                file_name=st.session_state['file_name'],
                mime="video/mp4",
                use_container_width=True,
                type="primary"
            )
            
        if btn:
            st.toast("開始下載...", icon="📂")

if __name__ == "__main__":
    main()