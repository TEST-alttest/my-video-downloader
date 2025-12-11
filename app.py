import streamlit as st
import os
import shutil
import json
import time
import subprocess
import sys

# --- V17.0: 強制依賴檢查 ---
def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
    except:
        pass

if 'dep_installed' not in st.session_state:
    install_dependencies()
    st.session_state['dep_installed'] = True

import yt_dlp

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V17.0", page_icon="🦄", layout="centered")

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

# --- 🔥 V17.0 核心黑科技：餅乾魔改函式 🔥 ---
def patch_cookies_for_threads(cookie_path):
    """
    讀取 IG 餅乾，將 instagram.com 的權限複製一份給 threads.net
    """
    try:
        with open(cookie_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        has_threads = False
        
        for line in lines:
            new_lines.append(line)
            # 檢查是否已經有 threads 權限
            if ".threads.net" in line:
                has_threads = True
            
            # 如果這行是 instagram 的權限，就複製一份改給 threads
            if ".instagram.com" in line:
                # 把 .instagram.com 替換成 .threads.net
                new_line = line.replace(".instagram.com", ".threads.net")
                new_lines.append(new_line)
        
        # 寫回檔案
        with open(cookie_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        return True
    except Exception as e:
        print(f"Cookie patch failed: {e}")
        return False

# --- 下載核心 ---
def download_video(raw_url, use_cookies=True):
    safe_clean_temp_dir()
    timestamp = int(time.time())
    output_path = f"{TEMP_DIR}/video_{timestamp}.%(ext)s"
    
    # 1. 網址修正
    final_url = raw_url.strip()
    if "threads.com" in final_url:
        final_url = final_url.replace("threads.com", "threads.net")
    if "threads.net" in final_url and "?" in final_url:
        final_url = final_url.split("?")[0]

    st.write(f"⚙️ 鎖定網址: {final_url}")
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    cookie_to_use = None
    if use_cookies:
        if "instagram.com" in final_url.lower() or "threads.net" in final_url.lower():
            if os.path.exists(IG_COOKIE_FILE): 
                # 🔥 下載前先執行魔改 🔥
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
    st.title("🦄 全能下載器 V17.0")
    st.caption("餅乾魔改版 (IG/Threads 權限通吃)")

    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR, exist_ok=True)

    with st.sidebar:
        st.header("⚙️ 設定")
        if "GEMINI_API_KEY" in st.secrets: st.success("🔒 雲端 Key 使用中")
        else:
            k = st.text_input("API Key", type="password", value=st.session_state['user_api_key'])
            if st.button("💾"): save_api_key(k)
        
        st.divider()
        ig_file = st.file_uploader("IG Cookies (Threads 通用)", type=["txt"], key="ig_uploader")
        if ig_file is not None:
            with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
            # 上傳後馬上執行一次魔改，確保權限正確
            if patch_cookies_for_threads(IG_COOKIE_FILE):
                st.success("✅ IG Cookies 更新並擴充 Threads 權限！")
            else:
                st.success("✅ IG Cookies 更新成功")

        fb_file = st.file_uploader("FB Cookies", type=["txt"], key="fb_uploader")
        if fb_file is not None:
            with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
            st.success("✅ FB Cookies 更新成功")
            
        if os.path.exists(IG_COOKIE_FILE): st.caption("✅ IG 憑證: OK")
        
        try:
            ver = yt_dlp.version.__version__
            st.info(f"Engine Ver: {ver}")
        except: pass

    st.divider()
    
    input_url = st.text_input("貼上影片連結")
    use_cookies_toggle = st.checkbox("🍪 掛載 Cookies (強烈建議勾選)", value=True)

    if st.button("🔍 解析並下載", type="primary", use_container_width=True):
        if not input_url:
            st.warning("請輸入網址")
        else:
            with st.status("🚀 啟動 V17 引擎 (自動適配權限)...", expanded=True) as status:
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
                    with st.expander("查看詳細錯誤"):
                        st.code(err_msg, language="text")

    if st.session_state['downloaded_file'] and os.path.exists(st.session_state['downloaded_file']):
        with open(st.session_state['downloaded_file'], "rb") as f:
            st.download_button("📥 儲存影片", f, file_name=st.session_state['file_name'], mime="video/mp4", use_container_width=True, type="primary")

if __name__ == "__main__":
    main()
