import streamlit as st
import pandas as pd
from datetime import datetime

# --- 憲法神聖科目定義 ---
HOLY_SUBJECTS = {
    "一、訂單": ["1.0 訂單總額 (PO Amount)"],
    "二、總收入": [
        "2.1 產品銷售收入", "2.1 服務收入", "2.1 補助金收入", "2.2 其他收入"
    ],
    "三、變動費用": [
        "3.1 原料採購成本", "3.1 輔料採購成本", "3.1 機械結構件採購", "3.1 電控零件採購", "3.1 耗材成本",
        "3.2 直接人工成本",
        "3.3 委外加工費用", "3.3 打樣及設計費", "3.3 運輸與倉儲",
        "3.4 剩餘材料轉入庫存",
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
        st.error(f"日期計算錯誤: {e}")
        return []

def show(supabase):
    st.markdown('<p class="main-header">📅 專案展開 (36個月預算矩陣)</p>', unsafe_allow_html=True)

    # --- 1. 選擇專案 ---
    try:
        res = supabase.table("projects").select("project_code, project_name, start_date").execute()
        projects = {f"{r['project_code']} | {r['project_name']}": r for r in res.data}
    except Exception as e:
        st.error(f"讀取專案列表失敗: {e}")
        return

    if not projects:
        st.info("尚無專案，請先至「專案身分建檔」建立。")
        return

    target_label = st.selectbox("📂 選擇專案進行預算規劃", list(projects.keys()))
    target_proj = projects[target_label]
    p_code = target_proj["project_code"]
    
    # --- 2. 產生時間軸 ---
    month_cols = get_month_list(target_proj["start_date"])
    if not month_cols: return # 防呆

    st.caption(f"專案代碼: {p_code} | 預算區間: {month_cols[0]} ~ {month_cols[-1]}")

    # --- 3. 讀取現有數據 (Plan & Real) ---
    try:
        data_res = supabase.table("project_matrix").select("*").eq("project_code", p_code).execute()
        df_db = pd.DataFrame(data_res.data)
    except Exception as e:
        # 如果表不存在或讀取失敗，建立空表結構，避免 KeyError
        df_db = pd.DataFrame(columns=["project_code", "year_month", "cost_item", "plan_amount"])
        if st.session_state.get("dev_mode"):
            st.warning(f"資料庫讀取異常 (可能是初次建立): {e}")

    # ★★★ 防彈衣：確保 DataFrame 有欄位，即使它是空的 ★★★
    if df_db.empty:
        df_db = pd.DataFrame(columns=["project_code", "year_month", "cost_item", "plan_amount"])

    # --- 4. 渲染矩陣介面 ---
    tab_rev, tab_cost, tab_profit = st.tabs(["💰 收入規劃", "📉 變動費用", "📊 毛利試算"])

    # Helper function
    def render_matrix_editor(category_name, items):
        editor_data = []
        for item in items:
            row_plan = {"科目": f"{item} (Plan)"}
            for m in month_cols:
                val = 0.0
                # 只有當資料庫有資料時才去篩選
                if not df_db.empty:
                    # 注意：這裡需確保 cost_item 欄位存在
                    try:
                        match = df_db[
                            (df_db["cost_item"] == item) & 
                            (df_db["year_month"] == m)
                        ]
                        if not match.empty:
                            val = float(match.iloc[0]["plan_amount"])
                    except:
                        pass # 欄位對不上就跳過，保持 0.0
                
                row_plan[m] = val
            editor_data.append(row_plan)
        
        df_editor = pd.DataFrame(editor_data).set_index("科目")
        
        st.markdown(f"#### {category_name}")
        # 使用 key 避免元件重繪衝突
        edited = st.data_editor(
            df_editor,
            use_container_width=True,
            height=300,
            frozen_columns=1,
            key=f"editor_{category_name}" 
        )
        return edited

    with tab_rev:
        st.info("💡 提示：輸入預算 (Plan)。")
        df_rev_new = render_matrix_editor("二、總收入", HOLY_SUBJECTS["二、總收入"])

    with tab_cost:
        st.info("💡 提示：輸入變動費用預算。")
        df_cost_new = render_matrix_editor("三、變動費用", HOLY_SUBJECTS["三、變動費用"])

    # --- 5. 存檔邏輯 ---
    if st.button("💾 儲存預算規劃"):
        upsert_list = []
        
        def process_df(df_input):
            for idx, row in df_input.iterrows():
                clean_item = idx.replace(" (Plan)", "")
                for m_col in month_cols:
                    amount = row[m_col]
                    if amount is not None: # 存 0 也是一種數據
                         upsert_list.append({
                            "project_code": p_code,
                            "year_month": m_col,
                            "cost_item": clean_item,
                            "plan_amount": float(amount)
                        })

        process_df(df_rev_new)
        process_df(df_cost_new)

        if upsert_list:
            try:
                # 簡單分批寫入
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
