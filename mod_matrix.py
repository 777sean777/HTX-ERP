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

    # --- 3. 準備渲染函數 (新版邏輯) ---
    def render_section(title, items, key_prefix):
        editor_data = []
        for item in items:
            row_plan = {"科目": f"{item}"}
            # 填入月份數據
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
        
        # 建立 DataFrame
        df_editor = pd.DataFrame(editor_data).set_index("科目")
        
        # [新增邏輯] 計算橫向總計 (Row Sum)
        # axis=1 代表橫向相加
        df_editor.insert(0, "∑ 總計 (Total)", df_editor.sum(axis=1))
        
        st.markdown(f"#### {title}")
        
        # 顯示編輯器
        # 注意：我們將 "∑ 總計 (Total)" 設為 disabled，防止用戶手動改總數
        try:
            edited_df = st.data_editor(
                df_editor,
                use_container_width=True,
                height=250,
                key=f"ed_{key_prefix}",
                disabled=["∑ 總計 (Total)"], # 鎖定總計欄
                frozen_columns=2 # 凍結 科目 + 總計，方便查看
            )
        except TypeError:
            # 舊版兼容
            edited_df = st.data_editor(
                df_editor,
                use_container_width=True,
                height=250,
                key=f"ed_{key_prefix}",
                disabled=["∑ 總計 (Total)"]
            )
        
        # [修改邏輯] 不再顯示每個月的垂直加總，只顯示該大項的「總金額」
        # 計算該大項的總和 (Grand Total of this Category)
        category_total = edited_df["∑ 總計 (Total)"].sum()
        
        # 用 Metric 大字顯示，清楚明瞭
        st.metric(label=f"{title} - 全案總計", value=f"${category_total:,.0f}")
        
        return edited_df, category_total

    # --- 4. 介面 Tabs ---
    tab_order, tab_rev, tab_cost, tab_profit = st.tabs(["📝 訂單", "💰 收入", "📉 費用", "📊 全案損益總結"])

    # === Tab 1: 訂單 ===
    with tab_order:
        st.info("輸入預計接單金額")
        df_order, total_order_val = render_section("一、訂單總額", HOLY_SUBJECTS["一、訂單"], "order")

    # === Tab 2: 收入 ===
    with tab_rev:
        st.info("輸入收入預算")
        df_rev, total_rev_val = render_section("二、總收入", HOLY_SUBJECTS["二、總收入"], "rev")

    # === Tab 3: 費用 ===
    with tab_cost:
        st.info("輸入變動費用預算")
        df_cost, total_cost_val = render_section("三、變動費用", HOLY_SUBJECTS["三、變動費用"], "cost")

    # === Tab 4: 全案損益總結 (新版) ===
    with tab_profit:
        st.subheader("📊 專案全案損益預估 (Project Summary)")
        st.caption("彙整上方輸入之所有數據，計算全案最終效益。")
        
        # 計算核心指標
        gross_profit = total_rev_val - total_cost_val
        margin_rate = (gross_profit / total_rev_val * 100) if total_rev_val != 0 else 0.0

        # 建立總結表格 (Simple Table)
        summary_data = {
            "項目": [
                "1. 全案預估總訂單 (Total Order)",
                "2. 全案預估總收入 (Total Revenue)",
                "3. 全案預估總變動費用 (Total Variable Cost)",
                "4. 全案預估邊際毛利 (Gross Profit)",
                "5. 全案預估邊際毛利率 (Gross Margin %)"
            ],
            "金額 / 數值": [
                total_order_val,
                total_rev_val,
                total_cost_val,
                gross_profit,
                margin_rate # 這裡先存數值，顯示時再格式化
            ]
        }
        
        df_sum = pd.DataFrame(summary_data)
        
        # 視覺化顯示
        # 針對每一列做不同的格式處理比較麻煩，我們直接用 st.metric 排版比較漂亮
        
        c1, c2, c3 = st.columns(3)
        c1.metric("預估總收入", f"${total_rev_val:,.0f}")
        c2.metric("預估總費用", f"${total_cost_val:,.0f}", delta_color="inverse") # 費用通常不顯示 delta
        c3.metric("預估總毛利", f"${gross_profit:,.0f}", 
                  delta=f"{margin_rate:.1f}%", delta_color="normal")

        st.divider()
        st.markdown("#### 📑 詳細損益表")
        
        # 手動格式化表格顯示
        display_df = df_sum.copy()
        display_df["金額 / 數值"] = display_df.apply(
            lambda x: f"{x['金額 / 數值']:.1f}%" if "率" in x["項目"] else f"${x['金額 / 數值']:,.0f}", 
            axis=1
        )
        st.dataframe(display_df, use_container_width=True, hide_index=True)


    # --- 5. 存檔邏輯 (自動過濾總計欄) ---
    st.divider()
    if st.button("💾 儲存所有預算規劃", type="primary"):
        upsert_list = []
        
        def process_save(df_input):
            for idx, row in df_input.iterrows():
                clean_item = idx 
                for m_col in month_cols:
                    # ★★★ 關鍵：只存月份欄位，跳過 "∑ 總計 (Total)" ★★★
                    if m_col in row: 
                        amount = row[m_col]
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
