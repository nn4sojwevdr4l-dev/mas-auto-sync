import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="MAS 金融掃描器", layout="centered")

# 你的 GitHub 檔案路徑 (現在是對應到 Excel 檔案)
TARGET_FILE = "MAS_Full_Directory_Latest.xlsx"

st.title("📱 MAS 自動掃描系統")

# --- 1. 自動爬蟲功能 ---
def fetch_latest_data():
    st.info("📡 正在抓取網站最新數據...")
    # 這裡請放你原本的爬蟲代碼
    # 範例模擬爬到的新資料：
    try:
        # 假設你的爬蟲邏輯在這裡...
        new_data = pd.DataFrame({
            'ID': ['A001', 'A002', 'X999'], # 假設 X999 是新出現的
            '名稱': ['標的1', '標的2', '新標的'],
            '狀態': ['穩定', '波動', '新偵測']
        })
        return new_data
    except Exception as e:
        st.error(f"爬蟲執行出錯: {e}")
        return None

# --- 2. 執行自動掃描與比對 ---
if os.path.exists(TARGET_FILE):
    # 讀取 GitHub 上的 Excel 舊資料
    old_df = pd.read_excel(TARGET_FILE)
    
    # 執行爬蟲抓取最新內容
    latest_df = fetch_latest_data()
    
    if latest_df is not None:
        # 比對邏輯：找出 latest_df 裡不在 old_df 的資料 (以 'ID' 欄位為準)
        # 請確認你的 Excel 裡有沒有 'ID' 這一欄，沒有的話請換成正確的欄位名
        new_items = latest_df[~latest_df['ID'].isin(old_df['ID'])]
        
        if not new_items.empty:
            # 🚨 發現更動！發出提示
            st.error(f"🚨 偵測到更動！發現 {len(new_items)} 筆新資料")
            st.toast("發現新資料！", icon='🚨')
            st.write("✨ **新發現內容：**")
            st.dataframe(new_items, use_container_width=True)
        else:
            st.success("✅ 掃描完成：目前資料與 Excel 一致，暫無更動。")

    # --- 3. 手機顯示介面 ---
    st.divider()
    st.subheader("📊 雲端資料庫總覽")
    st.metric("目前總筆數", len(old_df))
    
    # 搜尋功能
    search = st.text_input("🔍 快速搜尋 (代碼/名稱)")
    if search:
        display_df = old_df[old_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    else:
        display_df = old_df.head(20)
        
    st.dataframe(display_df, use_container_width=True)

else:
    st.error(f"❌ 找不到檔案：{TARGET_FILE}")
    st.info("請確認你的 GitHub 根目錄下確實有這個 Excel 檔。")

st.caption("Auto-Scan Mode | Database: MAS_Full_Directory_Latest.xlsx")
