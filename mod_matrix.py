import streamlit as st
import pandas as pd
from datetime import datetime

# --- 憲法神聖科目定義 (V2026.01.14-FINAL-COMPLETE) ---
HOLY_SUBJECTS = {
    "一、訂單": ["1.0 訂單總額 (PO Amount)"],
    "二、總收入": [
        "2.1 產品銷售收入", "2.1 服務收入", "2.1 補助金收入", "2.2 其他收入"
    ],
    "三、變動費用": [
        "3.1 原料採購成本", "3.1 輔料採購成本", "3.1 機械結構件採購", "3.1 電控零件採購", "3.1 耗材成本",
        "3.2 直接人工成本",
        "3.3 委外加工費用", "3.3 打樣及設計費", "3.3 運輸與倉儲",
        "3.4 剩餘材料轉入庫存", # 貸方項
        "3.5 新布料開發與打樣", "3.5 測試材料費",
        "3.6 工廠水電", "3.6 工廠租金",
        "3.7 廣告宣傳費", "3.7 差旅費"
    ]
}

def get_month_list(start_date, months=36):
    try:
        base = pd.to_datetime(start_date) if start_date else datetime(2026, 1, 1)
        base = base.replace(day=1)
        month_cols = []
        for i in range(months):
            curr = base + pd.DateOffset(months=i)
            month_cols.append(curr.strftime("%Y-%m-%d"))
        return month_cols
    except Exception as e:
        return []

def show(supabase):
    st.markdown('<p class="main-header">📅 專案展開 (36個月預算矩陣)</p>', unsafe_allow_html=True)

    # --- 1. 選擇專案 ---
    try:
        res = supabase.table("projects").select("project_code, project_name, start_date").execute()
        projects = {f"{r['project_code']} | {r['project_name']}": r for r in res.data}
    except:
        st.error("讀取專案列表失敗，請確認資料庫連線。")
        return

    if not projects:
        st.info("尚無專案，請先建檔。")
        return

    target_label = st.selectbox("📂 選擇專案", list(projects.keys()))
    target_proj = projects[target_label]
    p_code = target_proj["project_code"]
    month_cols = get_month_list(target_proj["start_date"])
    if not month_cols: return 

    st.caption(f"Code: {p_code} | Range: {month_cols[0]} ~ {month_cols[-1]}")

    # --- 2. 讀取現有數據 ---
    try:
        data_res = supabase.table("project_matrix").select("*").eq("project_code", p_code).execute()
        df_db = pd.DataFrame(data_res.data)
    except:
        df_db = pd.DataFrame()

    if df_db.empty:
        df_db = pd.DataFrame(columns=["project_code", "year_month", "cost_item",
