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
    except:
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
        st.info("尚無專案，請先建檔。")
        return

    target_label = st.selectbox("📂 選擇專案", list(projects.keys()))
    target_proj = projects[target_label]
    p_code = target_proj["project_code"]
    month_cols = get_month_list(target_proj["start_date"])
    
    if not month_cols:
        st.error("日期計算錯誤")
        return 

    st.caption(f"Code: {p_code} | Range: {month_cols[0]} ~ {month_cols[-1]}")

    # --- 2. 讀取現有數據 ---
    try:
        data_res = supabase.table("project_matrix").select("*").eq("project_code", p_code).execute()
        df_db = pd.DataFrame(data_res.data)
    except:
        df_db = pd.DataFrame()

    # 防呆：確保 DataFrame 有欄位 (之前語法錯誤的地方已修正)
    if df_db.empty:
        df_db = pd.DataFrame(columns=["project_code", "year_month", "cost_item", "plan_amount"])

    # --- 3. 準備渲染函數 ---
    def render_section(title, items, key_prefix):
        editor_data = []
        for item in items:
            row_plan = {"科目": f"{item}"}
            for m in month_cols:
                val = 0.0
                if not df_db.empty:
                    try:
                        # 嚴謹的篩選邏輯
                        match = df_db[(df_db["cost_item"] == item) & (df_db["year_month"] == m)]
                        if not match.empty:
                            val = float(match.iloc[0]["plan_amount"])
                    except: pass
                row_plan[m] = val
            editor_data.append(row_plan)
        
        df_editor = pd.DataFrame(editor_data).set_index("科目")
        
        st.markdown(f"#### {title}")
        
        # ★★★ 智慧偵測：如果版本太舊不支援 frozen_columns，就自動拿掉 ★★★
        try:
            edited_df = st.data_editor(
                df_editor,
                use_container_width=True,
                height=250,
                key=f"ed_{key_prefix}",
                frozen_columns=1 
            )
        except TypeError:
            # 降級處理
            if st.session_state.get("dev_mode"):
                st.warning("⚠️ 檢測到 Streamlit 版本較舊，已關閉凍結欄位功能。")
            edited_df = st.data_editor(
                df_editor,
                use_container_width=True,
                height=250,
                key=f"ed_{key_prefix}"
            )
        
        # 自動加總
        total_series = edited_df.sum(axis=0)
        df_total = pd.DataFrame(total_series).T
        df_total.index = ["∑ 總計 (Total)"]
        
        st.dataframe(df_total.style.format("{:,.0f}").background_gradient(cmap="Oranges", axis=1), use_container_width=True)
        
        return edited_df, total_series

    # --- 4. 介面 Tabs ---
    tab_order, tab_rev, tab_cost, tab_profit = st.tabs(["📝 訂單", "💰 收入", "📉 費用", "📊 毛利 (Profit)"])

    with tab_order:
        st.info("輸入預計接單金額")
        df_order, sum_order = render_section("一、訂單總額", HOLY_SUBJECTS["一、訂單"], "order")

    with tab_rev:
        st.info("輸入收入預算")
        df_rev, sum_rev = render_section("二、總收入", HOLY_SUBJECTS["二、總收入"], "rev")

    with tab_cost:
        st.info("輸入變動費用預算")
        df_cost, sum_cost = render_section("三、變動費用", HOLY_SUBJECTS["三、變動費用"], "cost")

    with tab_profit:
        st.subheader("📊 專案邊際毛利試算")
        st.caption("依據輸入數據即時計算 (無須存檔即可預覽)")
        
        # 毛利計算 (Series 運算)
        # 確保 sum_rev 和 sum_cost 都有數據
        gross_profit = sum_rev - sum_cost
        
        # 毛利率計算
        margin_rate = []
        for m in month_cols:
            r = sum_rev.get(m, 0) if not sum_rev.empty else 0
            c = sum_cost.get(m, 0) if not sum_cost.empty else 0
            p = r - c
            rate = (p / r * 100) if r != 0 else 0.0
            margin_rate.append(rate)
            
        profit_data = {
            "1. 總收入": sum_rev,
            "2. 變動費用": sum_cost,
            "3. 邊際毛利": gross_profit,
            "4. 毛利率 (%)": margin_rate
        }
        
        df_profit = pd.DataFrame(profit_data).T 
        
        # 顯示
        st.markdown("#### 💵 金額預測")
        df_amount = df_profit.iloc[0:3] 
        st.dataframe(df_amount.style.format("{:,.0f}").background_gradient(cmap="Greens", subset=pd.IndexSlice["3. 邊際毛利", :], axis=1), use_container_width=True)

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
                    # 存入所有非 None 數值 (包含 0)
                    if pd.notna(amount): 
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
                # 分批寫入 (避免 Payload 太大)
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
            except Exception as e:
                st.error(f"存檔失敗: {e}")
        else:
            st.warning("沒有資料需要儲存")
