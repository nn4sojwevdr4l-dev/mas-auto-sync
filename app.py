import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import math
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. 基礎配置 ---
st.set_page_config(page_title="MAS 金融監控系統", layout="centered")
BASE_URL = "https://eservices.mas.gov.sg"
LIST_API = "https://eservices.mas.gov.sg/fid/custom/resultpartial"
TARGET_FILE = "MAS_Full_Directory_Latest.xlsx"

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

# --- 2. 爬蟲核心函數 ---
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

def run_mas_crawler():
    unique_links = {}
    session = requests.Session()
    session.get(f"{BASE_URL}/fid", headers=headers)
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 掃描列表
    total_steps = sum(len(cats) for cats in sectors_map.values())
    current_step = 0
    
    for sector, categories in sectors_map.items():
        for category in categories:
            current_step += 1
            status_text.text(f"🔍 正在掃描目錄: {sector} - {category}")
            progress_bar.progress(current_step / total_steps)
            payload = {"sector": sector, "category": category, "page": 1}
            try:
                res = session.post(LIST_API, headers=headers, data=payload, timeout=20)
                soup = BeautifulSoup(res.text, "html.parser")
                total_hits = int(soup.select_one(".box-wrapper").get("data-hit", 0))
                for page in range(1, math.ceil(total_hits / 10) + 1):
                    payload["page"] = page
                    p_res = session.post(LIST_API, headers=headers, data=payload)
                    p_soup = BeautifulSoup(p_res.text, "html.parser")
                    for item in p_soup.select(".inner"):
                        link_tag = item.select_one("a[href*='/fid/institution/detail/']")
                        if link_tag:
                            href = link_tag["href"]
                            if href not in unique_links:
                                unique_links[href] = {"sectors": {sector}, "categories": {category}}
                            else:
                                unique_links[href]["sectors"].add(sector)
                                unique_links[href]["categories"].add(category)
            except: pass

    # 抓取詳情
    all_data = []
    status_text.text(f"🚀 正在抓取詳細資料 (共 {len(unique_links)} 筆)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_detail, h, ", ".join(sorted(list(info["sectors"]))), ", ".join(sorted(list(info["categories"])))) for h, info in unique_links.items()]
        for future in as_completed(futures):
            res = future.result()
            if res: all_data.append(res)
            
    return pd.DataFrame(all_data).fillna("")

# --- 3. Streamlit UI 介面 ---
st.title("📱 MAS 金融雲端監控")

if st.button("🚀 開始執行即時掃描比對", use_container_width=True):
    new_df = run_mas_crawler()
    
    if os.path.exists(TARGET_FILE):
        old_df = pd.read_excel(TARGET_FILE).fillna("")
        
        # 以「連結」作為唯一識別
        old_df_idx = old_df.set_index("連結")
        new_df_idx = new_df.set_index("連結")

        # 找出新增項目
        added_idx = new_df_idx.index.difference(old_df_idx.index)
        added_df = new_df_idx.loc[added_idx].reset_index()

        if not added_df.empty:
            st.error(f"🚨 發現 {len(added_df)} 筆新公司！")
            st.dataframe(added_df, use_container_width=True)
            
            # 提供下載
            csv = added_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 下載新發現清單", data=csv, file_name="New_MAS_Entities.csv", use_container_width=True)
        else:
            st.success("✅ 掃描完成：目前與 Excel 資料一致，無新增項目。")
    else:
        st.warning("⚠️ 找不到舊資料檔，已將本次結果存為初始版本。")
        new_df.to_excel(TARGET_FILE, index=False)

# --- 4. 檢視現有資料 ---
st.divider()
st.subheader("📊 現有資料庫查詢")
if os.path.exists(TARGET_FILE):
    master_df = pd.read_excel(TARGET_FILE)
    st.metric("資料總筆數", f"{len(master_df)} 筆")
    search = st.text_input("🔍 搜尋公司名稱/地址")
    if search:
        master_df = master_df[master_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    st.dataframe(master_df.head(50), use_container_width=True)
else:
    st.info("尚未建立資料庫，請點擊上方按鈕開始掃描。")
