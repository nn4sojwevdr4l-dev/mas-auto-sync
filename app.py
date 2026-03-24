import streamlit as st
import pandas as pd
import base64
import requests
from datetime import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="MAS 雲端掃描器", layout="centered")

# GitHub 設定 (請填入你的資訊)
GITHUB_REPO = "你的帳號/你的倉庫名"
FILE_PATH = "MAS_Full_Directory_Latest.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

# --- 自定義手機樣式 (CSS) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 18px !important;
        border-radius: 10px;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 功能函數：從 GitHub 讀取與更新 ---
def get_github_file():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8-sig')
        return pd.read_csv(pd.compat.StringIO(content)), r.json()['sha']
    return None, None

def update_github_file(df, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content = df.to_csv(index=False).encode('utf-8-sig')
    data = {
        "message": f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(content).decode('utf-8'),
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=data)
    return r.status_code == 200

# --- 主介面 ---
st.title("📱 MAS 雲端同步系統")

# 1. 檢查目前雲端版本
with st.status("📡 正在連線雲端資料庫...", expanded=False):
    master_df, current_sha = get_github_file()
    if master_df is not None:
        st.write(f"當前資料庫筆數: {len(master_df)}")
    else:
        st.error("無法取得雲端檔案，請檢查 Repo 設定。")

# 2. 上傳原始資料
st.subheader("📤 上傳原始資料")
uploaded_file = st.file_uploader("點擊選擇或拖入檔案", type=['csv', 'xlsx'])

if uploaded_file and master_df is not None:
    # 針對手機的大型按鈕
    if st.button("🚀 開始比對並同步雲端"):
        try:
            # 讀取上傳資料
            if uploaded_file.name.endswith('.csv'):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file)

            # --- 比對邏輯 (這裡依據你的需求自定義) ---
            # 範例：找出 raw_df 裡不在 master_df 的新內容
            new_data = raw_df[~raw_df['ID'].isin(master_df['ID'])] # 假設關鍵欄位叫 ID
            
            if not new_data.empty:
                # 合併新舊資料
                updated_master = pd.concat([master_df, new_data], ignore_index=True)
                
                # 3. 更新回 GitHub
                with st.spinner("💾 正在同步至 GitHub..."):
                    success = update_github_file(updated_master, current_sha)
                
                if success:
                    st.success(f"✅ 同步成功！新增 {len(new_data)} 筆資料。")
                    st.metric("資料庫總數", len(updated_master))
                    
                    # 下載報表供手機儲存
                    csv_report = new_data.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 下載本次更動報表",
                        data=csv_report,
                        file_name=f"update_report_{datetime.now().strftime('%m%d')}.csv",
                        use_container_width=True
                    )
                else:
                    st.error("GitHub 同步失敗，請檢查權限。")
            else:
                st.info("查無更動，雲端資料庫已是最新狀態。")
                
        except Exception as e:
            st.error(f"錯誤: {e}")

st.divider()
st.caption("Designed for Mobile Access | Auto-Sync Enabled")