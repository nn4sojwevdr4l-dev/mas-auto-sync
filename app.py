import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- 1. 基礎設定 ---
st.set_page_config(page_title="MAS 金融自動掃描", layout="centered")

# 你的 GitHub 檔案名稱
TARGET_FILE = "MAS_Full_Directory_Latest.xlsx"

# 自定義手機樣式
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📱 MAS 雲端自動中心")

# --- 2. 爬蟲功能 (請確保這裡回傳的 DataFrame 欄位包含「公司名稱」) ---
def fetch_latest_data():
    with st.spinner("📡 正在掃描網站數據..."):
        try:
            # --- 這裡請放入你原本的爬蟲代碼 ---
            # 範例模擬爬回來的資料：
            new_data = pd.DataFrame({
                '公司名稱': ['範例公司A', '範例公司B', '新出現的某某公司'], # 欄位名要跟 Excel 對齊
                '所屬大類': ['類別1', '類別2', '類別3'],
                '連結': ['http://...', 'http://...', 'http://...']
            })
            return new_data
        except Exception as e:
            st.error(f"爬蟲執行失敗: {e}")
            return None

# --- 3. 執行自動比對 ---
if os.path.exists(TARGET_FILE):
    # 讀取 Excel
    old_df = pd.read_excel(TARGET_FILE)
    
    # 執行爬蟲
    latest_df = fetch_latest_data()
    
    if latest_df is not None:
        # 使用你截圖中的「公司名稱」作為比對基準
        check_col = '公司名稱'
        
        if check_col in old_df.columns:
            # 找出最新爬到、但在舊 Excel 裡沒出現過的公司
            new_items = latest_df[~latest_df[check_col].isin(old_df[check_col])]
            
            if not new_items.empty:
                st.error(f"🚨 偵測到更動！發現 {len(new_items)} 筆新資料")
                st.toast(f"發現 {len(new_items)} 筆新公司！", icon='🚨')
                st.write("✨ **新資料預覽：**")
                st.dataframe(new_items, use_container_width=True)
            else:
                st.success("✅ 掃描完成：目前資料與 Excel 一致，暫無更動。")
        else:
            st.warning(f"⚠️ 欄位比對失敗：Excel 內找不到「{check_col}」欄位。")
            st.write("目前的 Excel 欄位有：", old_df.columns.tolist())

    # --- 4. 手機顯示介面 ---
    st.divider()
    st.subheader("📊 雲端資料總覽")
    st.metric("目前資料總數", f"{len(old_df)} 筆")
    
    # 搜尋功能 (適合手機輸入)
    search = st.text_input("🔍 搜尋公司名稱/地址")
    if search:
        display_df = old_df[old_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    else:
        display_df = old_df.head(20) # 預設顯示前 20 筆
        
    st.dataframe(display_df, use_container_width=True)

else:
    st.error(f"❌ 找不到檔案：{TARGET_FILE}")
    st.info("請檢查 GitHub 上是否有這個 Excel 檔。")

st.caption(f"Last Scan: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
