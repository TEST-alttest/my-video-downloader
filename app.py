import streamlit as st
import os
import shutil
import time
import subprocess
import glob

# --- 頁面設定 ---
st.set_page_config(page_title="全能下載器 V25.0", page_icon="🦄", layout="centered")

# --- 常數設定 ---
TEMP_DIR = "mobile_downloads"
IG_COOKIE_FILE = os.path.join(TEMP_DIR, "ig_cookies.txt")
FB_COOKIE_FILE = os.path.join(TEMP_DIR, "fb_cookies.txt")

# 確保目錄存在
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

# --- 工具函式 ---
def safe_clean_temp_dir():
    # 清空舊影片
    for f in os.listdir(TEMP_DIR):
        if f.endswith(".mp4") or f.endswith(".webm") or f.endswith(".mkv"):
            try: os.remove(os.path.join(TEMP_DIR, f))
            except: pass

def download_video_cli(url, use_cookies=True):
    safe_clean_temp_dir()
    
    # 1. 網址修正
    final_url = url.strip()
    if "threads.com" in final_url: final_url = final_url.replace("threads.com", "threads.net")
    if "threads.net" in final_url and "?" in final_url: final_url = final_url.split("?")[0]

    # 2. 建構暴力指令 (CLI Command)
    # 這是直接對系統下令，不經過 Python 函式庫
    output_template = f"{TEMP_DIR}/video_%(timestamp)s.%(ext)s"
    
    command = [
        "yt-dlp",                      # 呼叫主程式
        final_url,                     # 網址
        "-o", output_template,         # 輸出路徑
        "--no-playlist",               # 不要下載播放清單
        "--force-overwrites",          # 強制覆蓋
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]

    # 3. 掛載 Cookies
    if use_cookies:
        if "instagram.com" in final_url or "threads.net" in final_url:
            if os.path.exists(IG_COOKIE_FILE):
                command.extend(["--cookies", IG_COOKIE_FILE])
        elif "facebook.com" in final_url or "fb.watch" in final_url:
            if os.path.exists(FB_COOKIE_FILE):
                command.extend(["--cookies", FB_COOKIE_FILE])

    # 4. 執行指令並捕獲輸出
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

# --- 主介面 ---
st.title("🦄 全能下載器 V25.0")
st.caption("CLI 暴力模式 (繞過 Python 邏輯)")

# 側邊欄
with st.sidebar:
    st.header("🍪 憑證管理")
    ig_file = st.file_uploader("上傳 IG Cookies", type=["txt"])
    if ig_file:
        with open(IG_COOKIE_FILE, "wb") as f: f.write(ig_file.getbuffer())
        st.success("IG 憑證更新！")
        
    fb_file = st.file_uploader("上傳 FB Cookies", type=["txt"])
    if fb_file:
        with open(FB_COOKIE_FILE, "wb") as f: f.write(fb_file.getbuffer())
        st.success("FB 憑證更新！")

    if os.path.exists(IG_COOKIE_FILE): st.markdown("✅ **IG 憑證已就緒**")

# 主畫面
raw_url = st.text_input("貼上影片連結")
use_cookies = st.checkbox("🍪 掛載憑證下載 (必選)", value=True)

if st.button("🚀 暴力下載", type="primary", use_container_width=True):
    if not raw_url:
        st.warning("請先貼上網址")
    else:
        with st.status("正在執行系統指令...", expanded=True) as status:
            success, stdout, stderr = download_video_cli(raw_url, use_cookies)
            
            # 檢查檔案是否真的產生了
            downloaded_files = glob.glob(f"{TEMP_DIR}/*.mp4") + glob.glob(f"{TEMP_DIR}/*.webm") + glob.glob(f"{TEMP_DIR}/*.mkv")
            
            if success and downloaded_files:
                final_file = downloaded_files[0]
                status.write("✅ 下載成功！")
                status.update(label="完成", state="complete")
                
                with open(final_file, "rb") as f:
                    st.download_button(
                        label="📥 儲存影片到手機",
                        data=f,
                        file_name="video.mp4",
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary"
                    )
            else:
                status.update(label="失敗", state="error")
                st.error("❌ 下載失敗")
                # 顯示底層錯誤訊息，這會告訴我們真正的死因
                with st.expander("查看底層日誌 (Log)"):
                    st.code(stderr, language="text")
                    st.divider()
                    st.code(stdout, language="text")
