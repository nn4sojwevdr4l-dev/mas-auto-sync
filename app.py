import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import math
import time
import random
import base64
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. 基礎配置 ---
st.set_page_config(page_title="MAS 金融自動同步", layout="centered")
BASE_URL = "https://eservices.mas.gov.sg"
LIST_API = "https://eservices.mas.gov.sg/fid/custom/resultpartial"
TARGET_FILE = "MAS_Full_Directory_Latest.xlsx"
REPO_PATH = "nn4sojwevdr4l-dev/mas-auto-sync"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://eservices.mas.gov.sg/fid"
}

sectors_map = {
    "Banking": ["Local Bank", "Qualifying Full Bank", "Full Bank", "Wholesale Bank", "Merchant Bank", "Finance Company", "Representative Office (Banking)", "Financial Holding Company (Banking)", "SGS Primary Dealer"],
    "Capital Markets": ["Capital Markets Services Licensee", "Approved CIS Trustee", "Exempt Capital Markets Services Entity", "Licensed Trust Company", "Exempt Trust Company", "Approved Exchange", "Approved Holding Company", "Approved Clearing House", "Recognised Market Operator", "Recognised Clearing House", "Licensed Trade Repository", "Central Depository System"],
    "Financial Advisory": ["Licensed Financial Adviser", "Exempt Financial Adviser"],
    "Insurance": ["Direct Insurer (Life)", "Direct Insurer (General)", "Direct Insurer (Composite)", "Reinsurer (Life)", "Reinsurer (General)", "Reinsurer (Composite)", "Captive Insurer (Life)", "Captive Insurer (General)", "Captive Insurer (Composite)", "Lloyd's Asia Scheme", "Authorised Reinsurer (General)", "Authorised Reinsurer (Life)", "Authorised Reinsurer (Composite)", "Registered Insurance Broker", "Exempt Insurance Broker", "Representative Office (Insurance)", "Financial Holding Company (Insurance)", "Approved Insurance Broker"],
    "Payments": ["Credit and Charge Card Licensee", "Money-changing Licensee", "Standard Payment Institution", "Major Payment Institution", "Designated Payment System Operator", "Designated Payment System Settlement Institution", "Licensed Credit Bureau"]
}

# --- 2. 工具函數：同步回 GitHub ---
def push_to_github(df, filename):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        url = f"https://api.github.com/repos/{REPO_PATH}/contents/{filename}"
        auth_headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

        # 獲取檔案 SHA
        r = requests.get(url, headers=auth_headers)
        sha = r.json().get('sha') if r.status_code == 200 else None

        # 轉換為 Excel 二進位
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        content = base64.b64encode(output.getvalue()).decode('utf-8')

        payload = {
            "message": f"📱 Mobile Auto-Sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content
        }
        if sha: payload["sha"] = sha

        res = requests.put(url, headers=auth_headers, json=payload)
        return res.status_code in [200, 201]
    except Exception as e:
        st.error(f"GitHub 同步錯誤: {e}")
        return False

# --- 3. 爬蟲核心 (你的 MAS 邏輯) ---
def fetch_detail(href, s_str, c_str):
    try:
        res = requests.get(BASE_URL + href, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        name = soup.select_one("h1, h2").text.strip() if soup.select_one("h1, h2") else "N/A"
        tags = ", ".join(sorted([x.text.strip() for x in soup.select(".category li")]))
        phone = soup.select_one('a[href^="tel:"]').text.strip() if soup.select_one('a[href^="tel:"]') else ""
        address = ""
        for row in soup.select(".info tr"):
            label, value = row.find("th"), row.find("td")
            if label and value and "address" in label.get_text().lower():
                address = value.get_text(separator=" ", strip=True)
        return {"公司名稱": name, "所屬大類": s_str, "所屬細項": c_str, "標籤": tags, "電話": phone, "地址": address, "連結": BASE_URL + href}
    except: return None

def run_crawler():
    unique_links = {}
    session = requests.Session()
    session.get(f"{BASE_URL}/fid", headers=headers)
    
    prog_text = st.empty()
    bar = st.progress(0)
    
    # 掃描列表
    steps = sum(len(c) for c in sectors_map.values())
    cur = 0
    for s, cats in sectors_map.items():
        for c in cats:
            cur += 1
            prog_text.text(f"🔍 掃描: {s} > {c}")
            bar.progress(cur / steps)
            try:
                r = session.post(LIST_API, headers=headers, data={"sector": s, "category": c, "page": 1})
                soup = BeautifulSoup(r.text, "html.parser")
                hits = int(soup.select_one(".box-wrapper").get("data-hit", 0))
                for p in range(1, math.ceil(hits / 10) + 1):
                    p_r = session.post(LIST_API, headers=headers, data={"sector": s, "category": c, "page": p})
                    p_s = BeautifulSoup(p_r.text, "html.parser")
                    for item in p_s.select(".inner"):
                        lk = item.select_one("a[href*='/fid/institution/detail/']")
                        if lk:
                            h = lk["href"]
                            if h not in unique_links: unique_links[h] = {"s": {s}, "c": {c}}
                            else: 
                                unique_links[h]["s"].add(s)
                                unique_links[h]["c"].add(c)
            except: pass

    # 詳情抓取
    results = []
    prog_text.text(f"🚀 抓取詳情 ({len(unique_links)} 筆)...")
    with ThreadPoolExecutor(max_workers=10) as exe:
        tasks = [exe.submit(fetch_detail, h, ", ".join(sorted(list(i["s"]))), ", ".join(sorted(list(i["c"])))) for h, i in unique_links.items()]
        for t in as_completed(tasks):
            if t.result(): results.append(t.result())
    return pd.DataFrame(results).fillna("")

# --- 4. 主程式介面 ---
st.title("📱 MAS 金融監控中心")

if st.button("🚀 開始即時掃描並同步 GitHub", use_container_width=True):
    new_df = run_crawler()
    
    if os.path.exists(TARGET_FILE):
        old_df = pd.read_excel(TARGET_FILE).fillna("")
        # 比對新增
        new_items = new_df[~new_df['連結'].isin(old_df['連結'])]
        
        if not new_items.empty:
            st.error(f"🚨 偵測到 {len(new_items)} 筆新資料！")
            st.dataframe(new_items, use_container_width=True)
        else:
            st.success("✅ 與現有資料庫一致，無新公司。")
    
    # 無論有無新資料，都執行同步以確保 GitHub 最新
    with st.spinner("💾 正在將最新結果同步回 GitHub..."):
        if push_to_github(new_df, TARGET_FILE):
            st.toast("GitHub 更新成功！", icon="✅")
        else:
            st.error("GitHub 更新失敗，請檢查 Token 或 Repo 路徑。")

st.divider()
if os.path.exists(TARGET_FILE):
    df_view = pd.read_excel(TARGET_FILE)
    st.metric("資料總量", f"{len(df_view)} 筆")
    q = st.text_input("🔍 搜尋現有資料")
    if q: df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)]
    st.dataframe(df_view.head(30), use_container_width=True)
