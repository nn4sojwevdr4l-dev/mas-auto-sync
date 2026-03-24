import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="MAS 金融自動監控", layout="centered")

# GitHub 上的舊資料路徑
DATA_FILE = "MAS_Full_Directory_Latest/master_data.csv"

st.title("📱 MAS 自動掃描系統")

# --- 1. 自動爬蟲功能 (請在此處替換成你實際的爬蟲邏輯) ---
def fetch_latest_data():
    # 範例：假設你要爬某個金融網站
    # url = "https://example-finance-site.com"
    # r = requests.get(url)
    # ... 你的爬蟲代碼 ...
    
    # 這裡先模擬一份爬到的新資料 (示範用)
    new_raw_data = pd.DataFrame({
        'ID': ['A001', 'A002', 'A003'], 
        '名稱': ['範例標的1', '範例標的2', '新標的X'],
        '價格': [100, 200, 300]
    })
    return new_raw_data

# --- 2. 執行自動掃描 ---
st.subheader("🔍 正在執行即時掃描...")

with st.spinner("📡 正在抓取網站最新數據..."):
    latest_df = fetch_latest_data() # 執行爬蟲
    
    # 讀取 GitHub 上的舊資料做比對
    if os.path.exists(DATA_FILE):
        old_df = pd.read_csv(DATA_FILE)
        
        # --- 比對邏輯：找出不在舊資料裡的新 ID ---
        # 假設關鍵字欄位是 'ID'
        new_items = latest_df[~latest_df['ID'].isin(old_df['ID'])]
        
        if not new_items.empty:
            # 🚨 關鍵提示：發現更動！
            st.error(f"🚨 偵測到更動！發現 {len(new_items)} 筆新資料")
            st.toast(f"發現 {len(new_items)} 筆新資料！", icon='🚨')
            
            st.write("✨ **新發現內容：**")
            st.dataframe(new_items, use_container_width=True)
            
            # 合併並更新 (這部分會更新在 Streamlit 運行環境中)
            updated_df = pd.concat([old_df, new_items], ignore_index=True)
            # 如果需要存檔，這裡可以加更新 GitHub 的代碼
        else:
            st.success("✅ 掃描完成：目前與雲端資料一致，暫無更動。")
    else:
        st.warning(f"⚠️ 找不到舊資料檔 ({DATA_FILE})，已將本次掃描視為初始版本。")
        latest_df.to_csv(DATA_FILE, index=False)

# --- 3. 手機操作介面 ---
st.divider()
st.write("📊 **目前雲端總覽：**")
if os.path.exists(DATA_FILE):
    master = pd.read_csv(DATA_FILE)
    st.metric("資料庫總數", f"{len(master)} 筆")
    st.dataframe(master.head(20), use_container_width=True)

# 下載按鈕 (手機存檔用)
st.download_button(
    label="📥 下載最新報表",
    data=pd.read_csv(DATA_FILE).to_csv(index=False).encode('utf-8-sig'),
    file_name=f"MAS_Report_{datetime.now().strftime('%m%d')}.csv",
    use_container_width=True
)

st.caption("Live-Scanning Mode | Mobile Optimized")
