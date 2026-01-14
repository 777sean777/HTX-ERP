import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# --- 憲法神聖科目定義 (V2026.01.14-FINAL-V13) ---
# 這些科目名稱必須與 SQL 裡的 cost_item 完全一致
HOLY_SUBJECTS = {
    "一、訂單總額": ["1.0 訂單總額 (PO Amount)"],
    "二、總收入 (Revenue)": [
        "2.1 產品銷售收入", "2.1 服務收入", "2.1 補助金收入",
        "2.2 其他收入"
    ],
    "三、變動費用 (Variable Costs)": [
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
    """產生從開案日開始的 36 個月列表"""
    # 預設從專案開案日開始，若無則從 2026-01-01
    base = pd.to_datetime(start_date) if start_date else datetime(2026, 1, 1)
    # 強制設為該月 1 號
    base = base.replace(day=1)
    
    month_cols = []
    for i in range(months):
        curr = base + pd.DateOffset(months=i)
        month_cols.append(curr.strftime("%Y-%m-%d"))
    return month_cols

def show(supabase):
    st.markdown('<p class="main-header">📅 專案展開 (36個月預算矩陣)</p>', unsafe_allow_html=True)

    # --- 1. 選擇專案 ---
    # 從資料庫抓取專案清單
    try:
        res = supabase.table("projects").select("project_code, project_name, start_date").execute()
        projects = {f"{r['project_code']} | {r['project_name']}": r for r in res.data}
    except:
        st.error("無法讀取專案列表")
        return

    if not projects:
        st.info("尚無專案，請先至「專案身分建檔」建立。")
        return

    target_label = st.selectbox("📂 選擇專案進行預算規劃", list(projects.keys()))
    target_proj = projects[target_label]
    p_code = target_proj["project_code"]
    
    # --- 2. 產生時間軸 ---
    # 依據憲法：橫向 36 個月
    month_cols = get_month_list(target_proj["start_date"])
    
    st.caption(f"專案代碼: {p_code} | 預算區間: {month_cols[0]} ~ {month_cols[-1]}")

    # --- 3. 讀取現有數據 (Plan & Real) ---
    # 這裡我們需要把資料庫的「長表」轉成「寬表」
    try:
        data_res = supabase.table("project_matrix").select("*").eq("project_code", p_code).execute()
        df_db = pd.DataFrame(data_res.data)
    except:
        df_db = pd.DataFrame()

    # --- 4. 渲染矩陣介面 ---
    # 為了不讓畫面太亂，我們用 Tabs 分類大項
    tab_rev, tab_cost, tab_profit = st.tabs(["💰 收入規劃", "📉 變動費用", "📊 毛利試算"])

    # === Helper: 建立編輯表格 ===
    def render_matrix_editor(category_name, items):
        # 準備空的 DataFrame 結構
        # Index: 科目, Columns: 36個月
        editor_data = []
        
        for item in items:
            row_plan = {"科目": f"{item} (Plan)"}
            # row_real = {"科目": f"{item} (Real)"} # Real 是唯讀，我們晚點再處理顯示
            
            for m in month_cols:
                # 嘗試從 DB 找值
                val = 0.0
                if not df_db.empty:
                    # 篩選條件：科目 & 月份
                    match = df_db[
                        (df_db["cost_item"] == item) & 
                        (df_db["year_month"] == m)
                    ]
                    if not match.empty:
                        val = float(match.iloc[0]["plan_amount"])
                
                row_plan[m] = val
            
            editor_data.append(row_plan)
        
        df_editor = pd.DataFrame(editor_data).set_index("科目")
        
        # 顯示可編輯表格
        st.markdown(f"#### {category_name}")
        edited = st.data_editor(
            df_editor,
            use_container_width=True,
            height=300,
            # 凍結第一欄(科目)
            frozen_columns=1 
        )
        return edited

    # --- Tab 1: 收入 ---
    with tab_rev:
        st.info("💡 提示：在此輸入 **預算 (Plan)** 金額。實際 (Real) 將由訂單模組自動帶入 (目前為空)。")
        df_rev_new = render_matrix_editor("二、總收入", HOLY_SUBJECTS["二、總收入 (Revenue)"])

    # --- Tab 2: 費用 ---
    with tab_cost:
        st.info("💡 提示：輸入各項變動費用預算。")
        df_cost_new = render_matrix_editor("三、變動費用", HOLY_SUBJECTS["三、變動費用 (Variable Costs)"])

    # --- 5. 存檔邏輯 ---
    if st.button("💾 儲存預算規劃 (Save Plan)"):
        # 我們要把 DataFrame 轉回資料庫格式 (Upsert)
        upsert_list = []
        
        def process_df(df_input):
            # df_input index 是 "科目 (Plan)", columns 是月份字串
            for idx, row in df_input.iterrows():
                # 還原科目名稱 (去掉 " (Plan)")
                clean_item = idx.replace(" (Plan)", "")
                
                for m_col in month_cols:
                    amount = row[m_col]
                    # 只有大於 0 或原本有值才存 (節省空間)
                    # 這裡為了簡化，直接 Upsert
                    if amount is not None:
                         upsert_list.append({
                            "project_code": p_code,
                            "year_month": m_col,
                            "cost_item": clean_item,
                            "plan_amount": float(amount)
                            # real_amount 不動，Supabase 會保留原值 (若用 stored procedure) 
                            # 但標準 upsert 會覆蓋，所以嚴謹做法是先讀再寫，或 SQL Handle
                            # 為了 MVP，我們先假設 Real 目前是 0，之後開發 PO 模組時再加強
                        })

        process_df(df_rev_new)
        process_df(df_cost_new)

        if upsert_list:
            try:
                # 批次寫入 (注意：Supabase 批次有限制，若 36*20=720 筆可能要分批)
                # 這裡先簡單做
                chunk_size = 100
                for i in range(0, len(upsert_list), chunk_size):
                    chunk = upsert_list[i:i + chunk_size]
                    supabase.table("project_matrix").upsert(
                        chunk, on_conflict="project_code, year_month, cost_item"
                    ).execute()
                
                st.success("✅ 預算已成功寫入資料庫！")
                st.rerun()
            except Exception as e:
                st.error(f"存檔失敗: {e}")
        else:
            st.warning("沒有資料需要儲存")
