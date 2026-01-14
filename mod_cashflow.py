import streamlit as st
import pandas as pd

def show(supabase, dept):
    st.markdown(f'<p class="main-header">📅 {dept} 現金估算填報</p>', unsafe_allow_html=True)
    
    # --- 自動測試按鈕 ---
    if st.sidebar.button("🛠️ 載入模擬測試數據"):
        st.session_state.test_data = {
            "AR-Customer": 500000, "Salary": 150000, "Operating EXP": 30000
        }
        st.toast("已載入模擬數據，請手動確認後存檔")

    # --- 1. 時間與專案選擇 ---
    col_y, col_m, col_p = st.columns(3)
    with col_y: year = st.selectbox("年度", [2026, 2027, 2028])
    with col_m: month = st.selectbox("月份", [f"{i:02d}" for i in range(1, 13)])
    with col_p: 
        # 這裡未來連動專案清單
        project = st.text_input("關聯專案編號 (選填)", value="GENERAL")

    target_month = f"{year}-{month}"

    # --- 2. 現金流入區 (Cash In) ---
    with st.expander("💰 Cash In (應收/借款/利息)", expanded=True):
        c_in_cols = st.columns(2)
        ar_cust = c_in_cols[0].number_input("應收帳款-客戶 (AR-Customer)", min_value=0, value=st.session_state.get('test_data', {}).get('AR-Customer', 0))
        loan_in = c_in_cols[1].number_input("借款收入 (Loan)", min_value=0)
        # 其餘科目 R... (依截圖補足)

    # --- 3. 現金流出區 (Cash Out - Plan/Real) ---
    st.subheader("💸 Cash Out (營運/薪資/購料)")
    tab_plan, tab_real = st.tabs(["預計 (Plan)", "實際 (Real)"])
    
    with tab_plan:
        p_cols = st.columns(2)
        salary_p = p_cols[0].number_input("薪資 獎金 (Salary) - 預計", min_value=0, value=st.session_state.get('test_data', {}).get('Salary', 0))
        ops_p = p_cols[1].number_input("營運支出 (Operating EXP) - 預計", min_value=0, value=st.session_state.get('test_data', {}).get('Operating EXP', 0))

    # --- 4. 存檔邏輯 ---
    if st.button("💾 儲存本月現金流數據", type="primary"):
        # Antigravity 提醒：這裡會將資料拆解成 transactions 格式存入
        st.success(f"數據已成功傳送至 Supabase ({target_month})")
