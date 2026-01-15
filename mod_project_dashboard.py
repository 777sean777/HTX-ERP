import streamlit as st
import pandas as pd

def show(supabase):
    st.markdown('<p class="main-header">📊 經營決策看板 (Project Dashboard)</p>', unsafe_allow_html=True)
    st.caption("全公司專案戰情室 | 預算 (Plan) vs 實際 (Real) 即時監控")

    # --- 1. 讀取資料 (一次撈出所有專案與矩陣數據) ---
    try:
        # 抓專案清單
        res_proj = supabase.table("projects").select("project_code, project_name, pm_owner, start_date, end_date, partners(name)").execute()
        df_proj = pd.DataFrame(res_proj.data)
        
        # 抓矩陣數據 (只抓有數值的)
        # 注意：這裡我們把 Plan 和 Real 都抓出來
        res_matrix = supabase.table("project_matrix").select("project_code, cost_item, plan_amount, real_amount").execute()
        df_matrix = pd.DataFrame(res_matrix.data)

    except Exception as e:
        st.error(f"資料讀取失敗: {e}")
        return

    if df_proj.empty:
        st.info("目前無專案資料。")
        return

    # --- 2. 數據清洗與彙總 (Aggregation) ---
    # 目標：算出每個專案的 總收入、總成本、毛利
    
    dashboard_data = []

    for _, proj in df_proj.iterrows():
        p_code = proj['project_code']
        p_name = proj['project_name']
        cust_name = proj['partners']['name'] if proj['partners'] else "未知"
        
        # 篩選該專案的矩陣資料
        if not df_matrix.empty:
            mask = df_matrix['project_code'] == p_code
            my_data = df_matrix[mask]
        else:
            my_data = pd.DataFrame()

        # 初始化數值
        plan_rev = 0.0
        plan_cost = 0.0
        real_rev = 0.0
        real_cost = 0.0

        if not my_data.empty:
            # 依據憲法科目編號邏輯分類
            # 2.x 開頭 = 收入
            # 3.x 開頭 = 費用
            
            # --- Plan 計算 ---
            plan_rev = my_data[my_data['cost_item'].str.startswith("2.", na=False)]['plan_amount'].sum()
            plan_cost = my_data[my_data['cost_item'].str.startswith("3.", na=False)]['plan_amount'].sum()
            
            # --- Real 計算 (未來 SO/PO 寫入後會自動生效) ---
            real_rev = my_data[my_data['cost_item'].str.startswith("2.", na=False)]['real_amount'].sum()
            real_cost = my_data[my_data['cost_item'].str.startswith("3.", na=False)]['real_amount'].sum()

        # 毛利計算
        plan_profit = plan_rev - plan_cost
        plan_margin = (plan_profit / plan_rev * 100) if plan_rev != 0 else 0.0
        
        real_profit = real_rev - real_cost
        real_margin = (real_profit / real_rev * 100) if real_rev != 0 else 0.0

        dashboard_data.append({
            "專案代碼": p_code,
            "專案名稱": p_name,
            "客戶": cust_name,
            "預算總收入": plan_rev,
            "預算總成本": plan_cost,
            "預算毛利 $": plan_profit,
            "預算毛利率 %": plan_margin,
            "實際總收入": real_rev,
            "實際總成本": real_cost,
            "實際毛利 $": real_profit,
            "實際毛利率 %": real_margin,
            "達成率 (Rev)": (real_rev / plan_rev * 100) if plan_rev != 0 else 0.0
        })

    df_dash = pd.DataFrame(dashboard_data)

    # --- 3. 頂部 KPI 卡片 (全公司加總) ---
    st.markdown("### 🏢 全公司匯總 (Company Overview)")
    
    total_plan_rev = df_dash['預算總收入'].sum()
    total_plan_cost = df_dash['預算總成本'].sum()
    total_plan_profit = total_plan_rev - total_plan_cost
    avg_plan_margin = (total_plan_profit / total_plan_rev * 100) if total_plan_rev != 0 else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("全案預算總營收", f"${total_plan_rev:,.0f}")
    k2.metric("全案預算總成本", f"${total_plan_cost:,.0f}")
    k3.metric("全案潛在毛利", f"${total_plan_profit:,.0f}")
    k4.metric("平均預算毛利率", f"{avg_plan_margin:.1f}%")
    
    st.divider()

    # --- 4. 專案詳細列表 (互動式表格) ---
    st.markdown("### 📋 專案詳細列表")
    
    # 這裡我們只顯示 Plan 欄位，等有 Real 數據時再顯示 Real
    # 或者我們可以並列顯示
    
    # 格式化顯示
    st.dataframe(
        df_dash,
        column_config={
            "專案代碼": st.column_config.TextColumn("專案代碼", width="medium"),
            "預算總收入": st.column_config.NumberColumn("預算營收", format="$%d"),
            "預算總成本": st.column_config.NumberColumn("預算成本", format="$%d"),
            "預算毛利 $": st.column_config.NumberColumn("預算毛利", format="$%d"),
            "預算毛利率 %": st.column_config.NumberColumn("預算毛利 %", format="%.1f%%"),
            "實際總收入": st.column_config.NumberColumn("實際營收", format="$%d"), # 目前是 0
            "實際總成本": st.column_config.NumberColumn("實際成本", format="$%d"), # 目前是 0
            "達成率 (Rev)": st.column_config.ProgressColumn("營收達成率", format="%.1f%%", min_value=0, max_value=100),
        },
        use_container_width=True,
        hide_index=True
    )

    # --- 5. 圖表分析 (憲法 10-3 樞紐分析的前身) ---
    st.divider()
    st.markdown("### 📈 營收貢獻度分析")
    
    if not df_dash.empty and total_plan_rev > 0:
        # 簡單的長條圖：各專案預算營收
        st.bar_chart(
            df_dash.set_index("專案代碼")[["預算總收入", "預算毛利 $"]],
            color=["#FF4B4B", "#00CC96"] # 紅色營收，綠色毛利
        )
    else:
        st.caption("尚無足夠數據生成圖表")
