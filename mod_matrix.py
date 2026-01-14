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
        df_db = pd.DataFrame(columns=["project_code", "year_month", "cost_item", "plan_amount"])

    # --- 3. 準備渲染函數 (含自動加總邏輯) ---
    def render_section(title, items, key_prefix):
        editor_data = []
        for item in items:
            row_plan = {"科目": f"{item}"}
            for m in month_cols:
                val = 0.0
                if not df_db.empty:
                    try:
                        match = df_db[(df_db["cost_item"] == item) & (df_db["year_month"] == m)]
                        if not match.empty:
                            val = float(match.iloc[0]["plan_amount"])
                    except: pass
                row_plan[m] = val
            editor_data.append(row_plan)
        
        # 轉成 DataFrame
        df_editor = pd.DataFrame(editor_data).set_index("科目")
        
        st.markdown(f"#### {title}")
        
        # ★★★ 這裡把 frozen_columns=1 加回來了！ ★★★
        # 感謝你升級了 requirements.txt
        edited_df = st.data_editor(
            df_editor,
            use_container_width=True,
            height=250,
            key=f"ed_{key_prefix}",
            frozen_columns=1 
        )
        
        # 自動計算總計 (Sum Column)
        total_series = edited_df.sum(axis=0)
        df_total = pd.DataFrame(total_series).T
        df_total.index = ["∑ 總計 (Total)"]
        
        # 顯示總計
        st.dataframe(df_total.style.format("{:,.0f}").background_gradient(cmap="Oranges", axis=1), use_container_width=True)
        
        return edited_df, total_series

    # --- 4. 介面 Tabs (憲法 4-2 完整結構) ---
    tab_order, tab_rev, tab_cost, tab_profit = st.tabs(["📝 訂單", "💰 收入", "📉 費用", "📊 毛利 (Profit)"])

    # === Tab 1: 訂單 ===
    with tab_order:
        st.info("輸入預計接單金額 (PO Amount)")
        df_order, sum_order = render_section("一、訂單總額", HOLY_SUBJECTS["一、訂單"], "order")

    # === Tab 2: 收入 ===
    with tab_rev:
        st.info("輸入各項收入預算 (Revenue)")
        df_rev, sum_rev = render_section("二、總收入", HOLY_SUBJECTS["二、總收入"], "rev")

    # === Tab 3: 費用 ===
    with tab_cost:
        st.info("輸入變動費用預算 (Variable Costs)")
        df_cost, sum_cost = render_section("三、變動費用", HOLY_SUBJECTS["三、變動費用"], "cost")

    # === Tab 4: 毛利試算 (即時運算核心) ===
    with tab_profit:
        st.subheader("📊 專案邊際毛利試算")
        st.caption("依據輸入數據即時計算 (無須存檔即可預覽)")
        
        # 計算 毛利 = 收入 - 費用
        # 注意：這裡的運算是 Series 對 Series 的運算，會自動對齊月份
        gross_profit = sum_rev - sum_cost
        
        # 計算 毛利率
        def safe_div(x, y):
            return (x / y * 100) if y != 0 else 0.0
        
        margin_rate = []
        for m in month_cols:
            r = sum_rev.get(m, 0)
            c = sum_cost.get(m, 0)
            p = r - c
            rate = safe_div(p, r)
            margin_rate.append(rate)
            
        profit_data = {
            "1. 總收入": sum_rev,
            "2. 變動費用": sum_cost,
            "3. 邊際毛利": gross_profit,
            "4. 毛利率 (%)": margin_rate
        }
        
        df_profit = pd.DataFrame(profit_data).T 
        
        # 顯示金額表
        st.markdown("#### 💵 金額預測")
        df_amount = df_profit.iloc[0:3] 
        st.dataframe(df_amount.style.format("{:,.0f}").background_gradient(cmap="Greens", subset=pd.IndexSlice["3. 邊際毛利", :], axis=1), use_container_width=True)

        # 顯示比率表
        st.markdown("#### 📉 毛利率趨勢 (%)")
        df_rate = df_profit.iloc[3:4] 
        st.dataframe(df_rate.style.format("{:.1f}%").background_gradient(cmap="YlOrRd", axis=1), use_container_width=True)

    # --- 5. 存檔邏輯 ---
    st.divider()
    if st.button("💾 儲存所有預算規劃", type="primary"):
        upsert_list = []
        
        def process_save(df_input):
            for idx, row in df_input.iterrows():
                clean_item = idx 
                for m_col in month_cols:
                    amount = row[m_col]
                    if amount is not None: 
                         upsert_list.append({
                            "project_code": p_code,
                            "year_month": m_col,
                            "cost_item": clean_item,
                            "plan_amount": float(amount)
                        })
        
        process_save(df_order)
        process_save(df_rev)
        process_save(df_cost)

        if upsert_list:
            try:
                # 簡單分批
                chunk_size = 100
                progress_text = "存檔中，請稍候..."
                my_bar = st.progress(0, text=progress_text)
                
                total_chunks = len(upsert_list) // chunk_size + 1
                for i in range(0, len(upsert_list), chunk_size):
                    chunk = upsert_list[i:i + chunk_size]
                    supabase.table("project_matrix").upsert(
                        chunk, on_conflict="project_code, year_month, cost_item"
                    ).execute()
                    my_bar.progress((i // chunk_size + 1) / total_chunks)
                
                my_bar.empty()
                st.success("✅ 預算規劃已完整儲存！")
                st.rerun()
            except Exception as e: # 這裡就是之前報錯的地方，現在冒號有了！
                st.error(f"存檔失敗: {e}")
