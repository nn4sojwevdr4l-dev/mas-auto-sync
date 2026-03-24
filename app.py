import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- 1. 基礎設定 ---
st.set_page_config(page_title="MAS 雲端掃描器", layout="centered")

# 自動對準你的 GitHub 路徑
GITHUB_REPO = "nn4sojwevdr4l-dev/mas-auto-sync" 
DATA_FOLDER = "MAS_Full_Directory_Latest"

# 讀取 Secrets (請確保 Streamlit 後台只填：GITHUB_TOKEN = "xxx")
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("❌ 未偵測到 GITHUB_TOKEN，請在 Streamlit Secrets 設定。")

st.title("📱 MAS 金融自動監控")

# --- 2. 自動執行爬蟲邏輯 (請確保這裡有你的爬蟲代碼) ---
def auto_scan():
    st.info("📡 正在掃描網站資料...")
    # 這裡放你原本的爬蟲 code
    # ...
    st.success("✅ 掃描完成！")

# 進入網頁就自動跑
auto_scan()

# --- 3. 顯示 GitHub 資料夾內的檔案 ---
if os.path.exists(DATA_FOLDER):
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(('.csv', '.xlsx'))]
    if files:
        selected = st.selectbox("📂 選擇雲端檔案：", files)
        df = pd.read_csv(os.path.join(DATA_FOLDER, selected))
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("資料夾內尚無檔案。")
else:
    st.error(f"❌ 找不到資料夾：{DATA_FOLDER}")
